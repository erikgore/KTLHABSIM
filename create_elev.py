import numpy as np

# Creating a smaller test array (still covers the whole world but at lower resolution)
rows = 21600  # 180 degrees * 120 points per degree
cols = 43200  # 360 degrees * 120 points per degree

# Create array with zeros (sea level)
elev_data = np.zeros((rows, cols), dtype=np.float32)

# Add some basic elevation for land masses (very simplified)
# This creates a basic topography where most land is around 100m above sea level
elev_data[8400:13200, :] = 100  # Rough approximation of major land masses

# Save the array
np.save('worldelev.npy', elev_data)
print("Elevation file created successfully!")
