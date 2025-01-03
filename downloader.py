#!/usr/bin/env python3
import os
import boto3
from botocore import UNSIGNED
from botocore.client import Config
from datetime import datetime, timedelta
import logging
import time
import numpy as np
import pygrib
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('gefs_downloader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# HABSIM pressure levels
PRESSURE_LEVELS = [10, 20, 30, 50, 70, 100, 150, 200, 250, 300, 350, 400, 450,
                  500, 550, 600, 650, 700, 750, 800, 850, 900, 925, 950, 975, 1000]

class GEFSDownloader:
    def __init__(self):
        self.s3 = boto3.client('s3', 
                             region_name='us-east-1',
                             config=Config(signature_version=UNSIGNED))
        self.bucket = 'noaa-gefs-pds'
        self.data_dir = "/gefs/gefs"
        self.temp_dir = "/gefs/temp"
        self.max_retries = 5
        self.backoff_time = 10
        self.current_prefix = None
        self.base_time = None

        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

    def find_latest_cycle(self):
        """Find latest available GEFS cycle."""
        now = datetime.utcnow()
        max_hours = 48  # Check up to 48 hours back
        
        for hours in range(0, max_hours, 6):
            cycle = now - timedelta(hours=hours)
            cycle = cycle.replace(hour=(cycle.hour - (cycle.hour % 6)), 
                                minute=0, second=0, microsecond=0)

            prefix = f"gefs.{cycle.strftime('%Y%m%d')}/{cycle.strftime('%H')}/atmos/pgrb2ap5/"
            logger.info(f"Checking cycle: {cycle}, prefix: {prefix}")
            try:
                response = self.s3.list_objects_v2(
                    Bucket=self.bucket,
                    Prefix=prefix,
                    MaxKeys=10
                )
                if 'Contents' in response:
                    logger.info(f"Found available cycle: {cycle}, prefix: {prefix}")
                    self.current_prefix = prefix
                    self.base_time = cycle
                    return cycle
            except Exception as e:
                logger.warning(f"Failed to check cycle {cycle}, error: {str(e)}")
        
        return None

    def update_status(self, message):
        """Update the HABSIM status file."""
        try:
            with open('/gefs/serverstatus', 'w') as f:
                f.write(message)
        except Exception as e:
            logger.error(f"Failed to update status: {str(e)}")

    def update_which_gefs(self):
        """Update the whichgefs file with current cycle time."""
        if self.base_time:
            try:
                with open('/gefs/whichgefs', 'w') as f:
                    f.write(self.base_time.strftime("%Y%m%d%H"))
            except Exception as e:
                logger.error(f"Failed to update whichgefs: {str(e)}")

    def download_geavg(self, forecast_time):
        """Download a GEFS average member file for a given forecast time."""
        if not self.current_prefix or not self.base_time:
            logger.error("No valid prefix or base time")
            return None
            
        forecast_hours = int((forecast_time - self.base_time).total_seconds() / 3600)
        key = f"{self.current_prefix}geavg.t{self.base_time.strftime('%H')}z.pgrb2a.0p50.f{forecast_hours:03d}"
        grib_file = f"{self.temp_dir}/geavg_{forecast_hours:03d}.grib2"
        
        logger.info(f"Attempting to download: {key}")
        
        for attempt in range(self.max_retries):
            try:
                self.s3.download_file(self.bucket, key, grib_file)
                size = os.path.getsize(grib_file)
                logger.info(f"Downloaded file size: {size} bytes")
                
                if size < 1000:
                    logger.error("Downloaded file too small")
                    continue

                return grib_file

            except Exception as e:
                logger.error(f"Download attempt {attempt + 1} failed: {str(e)}")
                if os.path.exists(grib_file):
                    os.remove(grib_file)
                time.sleep(self.backoff_time * (attempt + 1))
                
        return None

    def grib_to_array(self, grib_file, forecast_time):
        """Convert GRIB2 file to numpy array in HABSIM format."""
        try:
            grbs = pygrib.open(grib_file)
            
            # Initialize array with shape (2, 26, 181, 360) for u and v winds
            dataset = np.zeros((2, len(PRESSURE_LEVELS), 181, 360))
            
            # Get all messages for u and v components
            u_messages = sorted([(g.level, g) for g in grbs.select(shortName='u', typeOfLevel='isobaricInhPa')])
            grbs.seek(0)  # Reset file pointer
            v_messages = sorted([(g.level, g) for g in grbs.select(shortName='v', typeOfLevel='isobaricInhPa')])
            
            # Log available levels
            available_levels = sorted(list(set([u[0] for u in u_messages])))
            logger.info(f"Available pressure levels in file: {available_levels}")
            
            # Create a mapping from PRESSURE_LEVELS indices to available data indices
            level_map = {}
            for i, target_level in enumerate(PRESSURE_LEVELS):
                # Find closest available level
                closest_level = min(available_levels, key=lambda x: abs(x - target_level))
                if abs(closest_level - target_level) <= 5:  # Within 5 hPa tolerance
                    level_map[i] = closest_level
            
            logger.info(f"Level mapping: {level_map}")
            
            # Process each matched level
            for i, target_level in level_map.items():
                try:
                    # Find messages for this level
                    u_data = next(msg for lvl, msg in u_messages if lvl == target_level).values
                    v_data = next(msg for lvl, msg in v_messages if lvl == target_level).values
                    
                    # Resample the data
                    u_resampled = u_data[::2, ::2]
                    v_resampled = v_data[::2, ::2]
                    
                    dataset[0][i] = u_resampled
                    dataset[1][i] = v_resampled
                    logger.info(f"Successfully processed level {target_level} into position {i}")
                except Exception as e:
                    logger.error(f"Error processing level {target_level}: {str(e)}")
                    continue
            
            grbs.close()
            
            # Save for all 20 model numbers
            base_str = self.base_time.strftime("%Y%m%d%H")
            forecast_str = forecast_time.strftime("%Y%m%d%H")
            for model_num in range(1, 21):
                output_file = f"{self.data_dir}/{base_str}_{forecast_str}_{str(model_num).zfill(2)}.npy"
                np.save(output_file, dataset)
                logger.info(f"Saved processed data to {output_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to process GRIB file: {str(e)}")
            return False

    def cleanup_old_files(self):
        """Remove files older than 384 hours (16 days)."""
        try:
            current_time = datetime.utcnow()
            for filename in os.listdir(self.data_dir):
                if filename.endswith('.npy'):
                    file_time = datetime.strptime(filename.split('_')[0], "%Y%m%d%H")
                    if (current_time - file_time).total_seconds() > 384 * 3600:
                        os.remove(os.path.join(self.data_dir, filename))
                        logger.info(f"Removed old file: {filename}")
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {str(e)}")

    def run(self):
        """Main execution method."""
        try:
            logger.info("Starting GEFS download process")
            self.update_status("Data refreshing. Sims may be slower than usual.")
            
            cycle = self.find_latest_cycle()
            if cycle is None:
                logger.error("No available GEFS cycles found")
                self.update_status("Error: No GEFS cycles available")
                return False

            success_count = 0
            forecast_hours = list(range(0, 25, 6))  # 0 to 24 hours in 6-hour steps
            
            logger.info(f"Downloading GEFS files for cycle {cycle}")
            
            for hour in forecast_hours:
                forecast_time = cycle + timedelta(hours=hour)
                grib_file = self.download_geavg(forecast_time)
                
                if grib_file:
                    if self.grib_to_array(grib_file, forecast_time):
                        success_count += 1
                    # Cleanup temporary grib file
                    os.remove(grib_file)
                else:
                    logger.error(f"Failed to download file for forecast hour {hour}")

            if success_count > 0:
                logger.info(f"Successfully processed {success_count}/{len(forecast_hours)} files")
                self.update_which_gefs()
                self.cleanup_old_files()
                self.update_status("Ready")
                return True
            else:
                logger.error("No files successfully processed")
                self.update_status("Error: No files processed")
                return False

        except Exception as e:
            logger.error(f"Error in download process: {str(e)}")
            self.update_status(f"Error: {str(e)}")
            return False
        finally:
            # Cleanup temp directory
            shutil.rmtree(self.temp_dir)
            os.makedirs(self.temp_dir, exist_ok=True)

if __name__ == "__main__":
    downloader = GEFSDownloader()
    downloader.run()
