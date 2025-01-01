import os
import numpy as np 
import math
import elev
import bisect
import time
from datetime import datetime, timedelta, timezone
from config import GEFS_DIR, WHICH_GEFS_FILE, MOUNT_ENABLED

EARTH_RADIUS = float(6.371e6)
DATA_STEP = 6 # hrs

GFSHIST = [1, 2, 3, 5, 7, 10, 20, 30, 50, 70,\
          100, 150, 200, 250, 300, 350, 400, 450,\
          500, 550, 600, 650, 700, 750, 800, 850,\
          900, 925, 950, 975, 1000]

GFSHIST_ALT = [45385, 40989, 38417, 35178, 33044, 30782, \
                26386, 23815, 20576, 18442, 16180, 13608, \
                11784, 10363, 9164, 8117, 7186, 6344, 5575, \
                4865, 4206, 3591, 3012, 2466, 1949, 1457, 989, 762, 540, 323, 111]

GFSHIST_ALT_DIFFS = [-4396, -2572, -3239, -2134, -2262, -4396, -2571,\
                 -3239, -2134, -2262, -2572, -1824, -1421, -1199, -1047, -931, \
                 -842, -769, -710, -659, -615, -579, -546, -517, -492, \
                 -468, -227, -222, -217, -212]

GEFS = [10, 20, 30, 50, 70,\
          100, 150, 200, 250, 300, 350, 400, 450,\
          500, 550, 600, 650, 700, 750, 800, 850,\
          900, 925, 950, 975, 1000]

GEFS_ALT = [30782, 26386, 23815, 20576, 18442, \
            16180, 13608, 11784, 10363, 9164, 8117, 7186, 6344, \
            5575, 4865, 4206, 3591, 3012, 2466, 1949, 1457, \
            989, 762, 540, 323, 111]

GEFS_ALT_DIFFS = [-4396, -2571, -3239, -2134, -2262, -2572, -1824, -1421, -1199, \
       -1047,  -931,  -842,  -769,  -710,  -659,  -615,  -579,  -546, \
        -517,  -492,  -468,  -227,  -222,  -217,  -212]

filecache = {}
suffix = ".npy"
currgefs = None  # Will be set by refresh()

def ensure_utc(dt):
    """Ensure datetime object has UTC timezone."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

def check_time_valid(simtime):
    """Check if simulation time is within valid data range."""
    if not currgefs:
        refresh()  # Try to load from file
        if not currgefs:
            return False
    
    # Make sure input time has timezone info
    simtime = ensure_utc(simtime)
    
    # Create timezone-aware current_cycle and end time
    current_cycle = ensure_utc(datetime.strptime(currgefs, "%Y%m%d%H"))
    valid_start = current_cycle
    valid_end = current_cycle + timedelta(hours=384)
    
    print(f"DEBUG: Checking time validity:")
    print(f"DEBUG: Input time: {simtime}")
    print(f"DEBUG: Valid range: {valid_start} to {valid_end}")
    print(f"DEBUG: Is valid: {valid_start <= simtime <= valid_end}")
    
    return valid_start <= simtime <= valid_end

def refresh():
    global currgefs
    try:
        with open(WHICH_GEFS_FILE, 'r') as f:
            s = f.readline().strip()
        if s != currgefs:
            reset()
            currgefs = s
            return True
        return False
    except FileNotFoundError:
        print(f"Warning: Could not open {WHICH_GEFS_FILE}")
        return False

def reset():
    global filecache
    filecache = {}

def get_basetime(simtime):
    """Get base time with timezone consistency."""
    simtime = ensure_utc(simtime)
    base = datetime(simtime.year, simtime.month, simtime.day, 
                   int(math.floor(simtime.hour / 6) * 6),
                   tzinfo=timezone.utc)
    print(f"DEBUG: get_basetime input: {simtime}, output: {base}")
    print(f"DEBUG: Current currgefs value: {currgefs}")
    return base

def get_file(timestamp, model):
    """Get GEFS file with timezone-aware timestamp handling."""
    timestamp = ensure_utc(timestamp)
    print(f"DEBUG: get_file attempt - timestamp: {timestamp}, model: {model}")
    
    if (timestamp, model) not in filecache.keys():
        name = timestamp.strftime("%Y%m%d%H")
        base_date = name[:8]  # Gets YYYYMMDD part
        print(f"DEBUG: Trying to load file for base date: {base_date}, timestamp: {name}")
        
        if timestamp.year < 2019:
            print(f"DEBUG: Loading historical file {name}")
            try:
                filecache[(timestamp, model)] = np.load(os.path.join(GEFS_DIR, name + suffix), "r")
                print(f"DEBUG: Successfully loaded file {name}")
            except FileNotFoundError:
                print(f"DEBUG: Historical file not found")
                return None
        else:
            filename = os.path.join(GEFS_DIR, f"{currgefs}_{name}_{str(model).zfill(2)}{suffix}")
            print(f"DEBUG: Loading GEFS file {filename}")
            try:
                filecache[(timestamp, model)] = np.load(filename, "r")
                print(f"DEBUG: Successfully loaded file {filename}")
            except FileNotFoundError:
                print(f"DEBUG: File not found: {filename}")
                return None
    return filecache[(timestamp,model)]

def get_wind_helper(lat_res, lon_res, level_res, time_res, model, diffs):
    lat_i, lat_f = lat_res
    lon_i, lon_f = lon_res
    level_i, level_f = level_res
    timestamp, time_f = time_res
    
    data1 = get_file(timestamp, model)
    if data1 is None:
        return None, None, None, None
        
    data2 = get_file(timestamp + timedelta(hours=6), model)
    if data2 is None:
        return None, None, None, None

    pressure_filter = np.array([level_f, 1-level_f]).reshape(1,2)
    lat_filter = np.array([lat_f, 1-lat_f]).reshape(1,1,2,1)
    lon_filter = np.array([lon_f, 1-lon_f]).reshape(1,1,1,2)
    
    cube1 = data1[:,level_i:level_i+2,lat_i:lat_i+2, lon_i:lon_i+2]
    cube2 = data2[:,level_i:level_i+2,lat_i:lat_i+2, lon_i:lon_i+2]
    
    line1 = np.sum(cube1 * lat_filter * lon_filter, axis=(2,3))
    line2 = np.sum(cube2 * lat_filter * lon_filter, axis=(2,3))

    line_t = line1 * time_f + line2 * (1-time_f)
    du, dv = np.diff(line_t, axis=1).flatten()
    dh = diffs[level_i]

    u, v = (line_t * pressure_filter).sum(axis=1).flatten()

    return u, v, du/dh, dv/dh

def get_bounds_and_fractions(lat, lon, alt, sim_timestamp, levels):
    sim_timestamp = ensure_utc(sim_timestamp)
    lat_res, lon_res, pressure_res = None, None, None
        
    lat = 90 - lat
    lat_res = (int(math.floor(lat)), 1 - lat % 1)

    lon = lon % 360
    lon_res = (int(math.floor(lon)), 1 - lon % 1)
    
    base_timestamp = get_basetime(sim_timestamp)
    offset = sim_timestamp - base_timestamp
    time_f = 1-float(offset.seconds)/(3600*6)
    time_res = (base_timestamp, time_f)
    
    pressure_res = get_pressure_bound(alt, levels)
    return lat_res, lon_res, pressure_res, time_res

def get_pressure_bound(alt, levels):
    pressure = alt_to_hpa(alt)
    pressure_i = bisect.bisect_left(levels, pressure)
    if pressure_i == len(levels):
        return pressure_i-2, 0
    if pressure_i == 0:
        return 0, 1
    return pressure_i - 1, (levels[pressure_i]-pressure)/float(levels[pressure_i] - levels[pressure_i-1])

def alt_to_hpa(altitude):
    pa_to_hpa = 1.0/100.0
    if altitude < 11000:
        return pa_to_hpa * (1-altitude/44330.7)**5.2558 * 101325
    else:
        return pa_to_hpa * math.exp(altitude / -6341.73) * 128241

def hpa_to_alt(p):
    if p > 226.325:
        return 44330.7 * (1 - (p / 1013.25) ** 0.190266)
    else:
        return -6341.73 * (math.log(p) - 7.1565)

def lin_to_angular_velocities(lat, lon, u, v): 
    dlat = math.degrees(v / EARTH_RADIUS)
    dlon = math.degrees(u / (EARTH_RADIUS * math.cos(math.radians(lat))))
    return dlat, dlon

def get_wind(simtime, lat, lon, alt, model, levels):
    simtime = ensure_utc(simtime)
    # First check if time is valid
    if not check_time_valid(simtime):
        print(f"DEBUG: Time {simtime} outside valid range")
        return "error", "error", "error", "error"

    bounds = get_bounds_and_fractions(lat, lon, alt, simtime, levels)  
    diffs = GEFS_ALT_DIFFS if levels == GEFS else GFSHIST_ALT_DIFFS
    u, v, du, dv = get_wind_helper(*bounds, model, diffs)
    if u is None:
        return "error", "error", "error", "error"
    return u, v, du, dv

def simulate(simtime, lat, lon, rate, step, max_duration, alt, model, coefficient=1, elevation=True):
    print(f"DEBUG: Starting simulation at time {simtime}")
    simtime = ensure_utc(simtime)
    base_time = get_basetime(datetime.strptime(currgefs, "%Y%m%d%H").replace(tzinfo=timezone.utc))
    print(f"DEBUG: Base model time: {base_time}")
    
    # Check simulation time range validity
    if not check_time_valid(simtime):
        print(f"DEBUG: Start time {simtime} outside valid range")
        return "error"

    # Check if end time will be valid
    end = simtime + timedelta(hours=max_duration)
    if not check_time_valid(end):
        print(f"DEBUG: End time {end} outside valid range")
        return "error"

    print(f"DEBUG: Flight time: {simtime}")
    print(f"DEBUG: Flight end time: {end}")
    
    levels = GFSHIST if simtime.year < 2019 else GEFS
    path = list()
    
    while True:
        u, v, du, dv = get_wind(simtime, lat, lon, alt, model, levels)
        if u == "error":
            return "error"
            
        path.append((simtime.timestamp(), lat, lon, alt, u, v, du, dv))
        if simtime >= end or (elevation and elev.getElevation(lat, lon) > alt):
            break
        dlat, dlon = lin_to_angular_velocities(lat, lon, u, v)
        alt = alt + step * rate
        lat = lat + dlat * step * coefficient
        lon = lon + dlon * step * coefficient
        simtime = simtime + timedelta(seconds=step)
    
    return path

def refreshdaemon():
    """Daemon to refresh GEFS data cache."""
    while True:
        if refresh():
            print('Cache reset by daemon.')
        time.sleep(60)

def start_refresh_daemon():
    """Start the refresh daemon if not already running."""
    from threading import Thread
    Thread(target=refreshdaemon).start()

# Force initial load of currgefs on module import
refresh()

# Only start daemon if explicitly requested
if __name__ == "__main__":
    start_refresh_daemon()
