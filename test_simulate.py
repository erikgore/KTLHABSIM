from datetime import datetime, timezone
import simulate
import os

def test_simulation():
    """Test the simulation with our test data"""
    # First verify GEFS data directory
    gefs_dir = os.path.expanduser('~/PJEHABSIM/gefs/')
    print(f"\nChecking GEFS directory: {gefs_dir}")
    if not os.path.exists(gefs_dir):
        print(f"ERROR: GEFS directory not found at {gefs_dir}")
        return
    
    # List available data files
    print("\nAvailable data files:")
    files = sorted(os.listdir(gefs_dir))
    print("\n".join(files[:5]) + "\n... and more")
    
    # Test parameters
    test_time = datetime(2024, 11, 18, 1, 0).replace(tzinfo=timezone.utc)  # 1:00 UTC
    lat = 37.4275  # Stanford's latitude
    lon = -122.1697  # Stanford's longitude
    rate = 5  # m/s ascent rate
    step = 240  # time step in seconds
    max_duration = 2  # hours
    alt = 0  # starting altitude
    model = 1  # use first model

    print("\nStarting test simulation...")
    print(f"Test time: {test_time}")
    print(f"Location: {lat}, {lon}")
    
    # Test time validation
    print("\nTesting time validation...")
    is_valid = simulate.check_time_valid(test_time)
    print(f"Time validation result: {is_valid}")

    # Test file loading
    print("\nTesting file loading...")
    base_time = simulate.get_basetime(test_time)
    print(f"Base time for simulation: {base_time}")
    data = simulate.get_file(base_time, model)
    print(f"Data loaded: {'Success' if data is not None else 'Failed'}")
    if data is not None:
        print(f"Data shape: {data.shape}")

    # Test full simulation
    print("\nTesting full simulation...")
    path = simulate.simulate(test_time, lat, lon, rate, step, max_duration, alt, model)
    if path == "error":
        print("Simulation failed")
    else:
        print(f"Simulation successful - generated {len(path)} points")
        print("\nFirst point:", path[0])
        print("Last point:", path[-1])

if __name__ == "__main__":
    test_simulation()