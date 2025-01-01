import numpy as np
import os
from datetime import datetime

def create_test_gefs():
    # Create array with shape [2, 26, 181, 360] as per the data format
    # 2 components (u,v winds), 26 pressure levels, 181 lats, 360 lons
    data = np.zeros((2, 26, 181, 360), dtype=np.float32)
    
    # Add some basic wind patterns
    data[0] += 5.0  # Add slight eastward wind
    data[1] += 2.0  # Add slight northward wind
    
    # Base time is now 20241229
    base_time = "20241229"
    
    # Ensure gefs directory exists
    os.makedirs('gefs', exist_ok=True)
    
    # Create files for both 00 and 06 hours
    for hour in ["00", "06"]:
        pred_time = f"20241229{hour}"
        for model in range(1, 21):
            filename = f"gefs/{base_time}_{pred_time}_{model:02d}.npy"
            np.save(filename, data)
            print(f"Created {filename}")

    # Update whichgefs file
    with open('whichgefs', 'w') as f:
        f.write(base_time)
    print(f"Updated whichgefs to {base_time}")

create_test_gefs()
