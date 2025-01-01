import numpy as np
import os
from datetime import datetime

def create_test_gefs():
    # Create array with shape [2, 26, 181, 360]
    data = np.zeros((2, 26, 181, 360), dtype=np.float32)
    
    # Add some basic wind patterns for visibility
    data[0] += 5.0  # Add slight eastward wind
    data[1] += 2.0  # Add slight northward wind
    
    # Use November 18th, 2024
    base_time = "20241118"
    
    # Ensure gefs directory exists
    os.makedirs('gefs', exist_ok=True)
    
    # Create files for both 00 and 06 hours
    for hour in ["00", "06"]:
        pred_time = f"{base_time}{hour}"  # Using same date for both base and pred
        for model in range(1, 21):
            filename = f"gefs/{base_time}_{pred_time}_{model:02d}.npy"
            np.save(filename, data)
            print(f"Created {filename}")

    # Update whichgefs file
    with open('whichgefs', 'w') as f:
        f.write(base_time)
    print(f"Updated whichgefs to {base_time}")

if __name__ == "__main__":
    create_test_gefs()
