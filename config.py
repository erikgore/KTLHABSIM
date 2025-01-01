import os

# Base configuration
MOUNT_ENABLED = True

# Directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GEFS_DIR = '/gefs/gefs' if MOUNT_ENABLED else os.path.join(BASE_DIR, 'gefs')
WHICH_GEFS_FILE = '/gefs/whichgefs' if MOUNT_ENABLED else os.path.join(BASE_DIR, 'whichgefs')
STATUS_FILE = '/gefs/serverstatus' if MOUNT_ENABLED else os.path.join(BASE_DIR, 'serverstatus')
SERVER_STATUS_FILE = STATUS_FILE  # Alias for app.py
ELEVATION_FILE = os.path.join(BASE_DIR, 'worldelev.npy')

# Create directories if they don't exist
os.makedirs(GEFS_DIR, exist_ok=True)
