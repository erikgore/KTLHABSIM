import numpy as np

# Load and inspect one file
data = np.load('gefs/20241118_2024111800_01.npy')

print("Data shape:", data.shape)
print("\nSample wind values (first few elements):")
print("U wind (east):", data[0,0,0,:10])  # First 10 elements of u wind
print("V wind (north):", data[1,0,0,:10]) # First 10 elements of v wind
