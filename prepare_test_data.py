#!/usr/bin/env python3
from datetime import datetime
import os
import shutil
import numpy as np
import glob

def prepare_test_data():
    """Prepare test data files for today's date by copying from existing data"""
    today = datetime.utcnow()
    today_prefix = today.strftime("%Y%m%d")
    gefs_dir = os.path.expanduser('~/PJEHABSIM/gefs')
    
    # Find an existing data file to use as template
    existing_files = glob.glob(os.path.join(gefs_dir, '*.npy'))
    if not existing_files:
        print("Error: No existing .npy files found to use as template")
        return
    
    template_path = existing_files[0]
    print(f"Using template file: {os.path.basename(template_path)}")
    
    # Load template data
    template_data = np.load(template_path)
    print(f"Template data shape: {template_data.shape}")
    
    # Track existing files to avoid recreating them
    existing_count = 0
    created_count = 0
    
    # Create test data for 00:00 and 06:00
    for hour in ['00', '06']:
        for model in range(1, 21):
            model_str = str(model).zfill(2)
            filename = f"{today_prefix}_{today_prefix}{hour}_{model_str}.npy"
            filepath = os.path.join(gefs_dir, filename)
            
            if os.path.exists(filepath):
                existing_count += 1
                continue
                
            # Save a copy of the template data with the new filename
            np.save(filepath, template_data)
            created_count += 1
    
    print(f"\nResults for {today_prefix}:")
    print(f"  Files already exist: {existing_count}")
    print(f"  New files created: {created_count}")
    
    # Show example of available files
    print("\nAvailable data files (sample):")
    for f in sorted(os.listdir(gefs_dir))[:5]:
        print(f"  {f}")
    print("  ... and more")

if __name__ == "__main__":
    prepare_test_data()
