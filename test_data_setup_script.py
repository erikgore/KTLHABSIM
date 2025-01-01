import os
from datetime import datetime, timedelta

def verify_test_files():
    """Verify test data files exist and print missing files."""
    base_time = "2024111800"  # Nov 18, 2024 00:00 UTC
    prediction_times = ["2024111800", "2024111806"]  # 00:00 and 06:00 UTC
    
    required_files = []
    missing_files = []
    
    # Generate list of required files
    for pred_time in prediction_times:
        for model in range(1, 21):  # Models 01-20
            filename = f"{base_time}_{pred_time}_{str(model).zfill(2)}.npy"
            required_files.append(filename)
            
            # Check if file exists in the GEFS directory
            if not os.path.exists(os.path.join('/gefs/gefs', filename)):
                missing_files.append(filename)
    
    print(f"Total required files: {len(required_files)}")
    print(f"Missing files: {len(missing_files)}")
    
    if missing_files:
        print("\nMissing files:")
        for file in missing_files:
            print(file)
    else:
        print("\nAll required files are present!")
    
    return required_files, missing_files

if __name__ == "__main__":
    print("Verifying test data files...")
    verify_test_files()
