#!/usr/bin/env python3
import os
import time
from datetime import datetime, timedelta
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('downloaderd.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
mount = True
path = "/gefs/gefs/" if mount else "./gefs/"
whichpath = '/gefs/whichgefs' if mount else 'whichgefs'
statuspath = '/gefs/serverstatus' if mount else 'serverstatus'
refresh_interval = 300  # 5 minutes

def update_status(message):
    """Update the HABSIM status file."""
    try:
        with open(statuspath, "w") as f:
            f.write(message)
    except Exception as e:
        logger.error(f"Failed to update status: {str(e)}")

def get_current_cycle():
    """Get current GEFS cycle from whichgefs file."""
    try:
        with open(whichpath) as f:
            s = f.readline().strip()
        if not s:
            return None
        now = datetime.strptime(s, "%Y%m%d%H")
        return datetime(now.year, now.month, now.day, int(now.hour / 6) * 6)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Error reading whichgefs: {str(e)}")
        return None

def validate_data(timestamp):
    """Check if data files exist and are valid for a given timestamp."""
    base_name = timestamp.strftime("%Y%m%d%H")
    # Check a few key forecast hours
    for hour in [0, 6, 12]:
        forecast = timestamp + timedelta(hours=hour)
        file_path = Path(path) / f"{base_name}_{forecast.strftime('%Y%m%d%H')}_01.npy"
        if not file_path.exists() or file_path.stat().st_size < 1000:
            return False
    return True

def run_downloader():
    """Run the downloader script and handle errors."""
    try:
        logger.info("Starting downloader")
        result = subprocess.run(
            ['python3', 'downloader.py'],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Downloader completed successfully")
        logger.debug(f"Downloader output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Downloader failed with code {e.returncode}")
        logger.error(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Failed to run downloader: {str(e)}")
        return False

def main():
    """Main daemon loop."""
    logger.info("Starting GEFS downloader daemon")
    
    # Ensure directories exist
    os.makedirs(path, exist_ok=True)
    update_status("Initializing. Please check again later.")
    
    while True:
        try:
            # Check current cycle
            current_cycle = get_current_cycle()
            if current_cycle:
                logger.info(f"Current GEFS cycle: {current_cycle}")
            else:
                logger.warning("No current cycle found")

            # Run downloader
            update_status("Data refreshing. Sims may be slower than usual.")
            if run_downloader():
                # Verify new data
                new_cycle = get_current_cycle()
                if new_cycle and validate_data(new_cycle):
                    logger.info(f"Successfully downloaded and verified data for {new_cycle}")
                    update_status("Ready")
                else:
                    logger.error("Data validation failed")
                    update_status("Error: Data validation failed")
            else:
                logger.error("Download process failed")
                update_status("Error: Download failed")

            # Wait before next check
            logger.info(f"Waiting {refresh_interval} seconds before next check")
            time.sleep(refresh_interval)

        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            update_status(f"Error: {str(e)}")
            time.sleep(refresh_interval)

if __name__ == "__main__":
    main()
