import numpy as np
import math
import os
from config import ELEVATION_FILE

resolution = 120  # points per degree

# Load elevation data with error handling
try:
    data = np.load(ELEVATION_FILE, 'r')
    print(f"Successfully loaded elevation data from {ELEVATION_FILE}")
except FileNotFoundError:
    print(f"Warning: Could not find elevation file {ELEVATION_FILE}")
    # Create a small empty dataset as fallback
    data = np.zeros((180 * resolution, 360 * resolution))
except Exception as e:
    print(f"Error loading elevation data: {str(e)}")
    data = np.zeros((180 * resolution, 360 * resolution))

def getElevation(lat, lon):
    """
    Get elevation for a given latitude and longitude.
    Returns elevation in meters, or 0 if coordinates are invalid.
    """
    try:
        x = int(round((lon + 180) * resolution))
        y = int(round((90 - lat) * resolution)) - 1
        return max(0, data[y, x])
    except IndexError:
        print(f"Warning: Coordinates out of range - lat: {lat}, lon: {lon}")
        return 0
    except Exception as e:
        print(f"Error getting elevation: {str(e)}")
        return 0
