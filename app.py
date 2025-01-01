from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import os
from datetime import datetime, timezone
import simulate
from config import GEFS_DIR, SERVER_STATUS_FILE, BASE_DIR
import elev

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():  # pragma: no cover
    return Response(open(os.path.join(BASE_DIR, "interface/home.html")).read(), mimetype="text/html")

@app.route('/paths.js')
def pathsjs():  # pragma: no cover
    return Response(open(os.path.join(BASE_DIR, "interface/paths.js")).read(), mimetype="text/html")

@app.route('/style.js')
def stylejs():  # pragma: no cover
    return Response(open(os.path.join(BASE_DIR, "interface/style.js")).read(), mimetype="text/html")

@app.route('/util.js')
def utiljs():  # pragma: no cover
    return Response(open(os.path.join(BASE_DIR, "interface/util.js")).read(), mimetype="text/html")

@app.route('/which')
def whichgefs():
    return simulate.currgefs

@app.route('/status')
def status():
    try:
        with open(SERVER_STATUS_FILE, 'r') as f:
            return f.readline().strip()
    except FileNotFoundError:
        return "Error: Status file not found"

@app.route('/ls')
def ls():
    try:
        return jsonify(os.listdir(GEFS_DIR))
    except FileNotFoundError:
        return jsonify([])

'''
Returns a json object representing the flight path, given a UTC launch time (yr, mo, day, hr, mn),
a location (lat, lon), a launch elevation (alt), a drift coefficient (coeff),
a maximum duration in hrs (dur), a step interval in seconds (step), and a GEFS model number (model)

Return format is a list of [loc1, loc2 ...] where each loc is a list [lat, lon, altitude, u-wind, v-wind]

u-wind is wind towards the EAST: wind vector in the positive X direction
v-wind is wind towards the NORTH: wind vector in the positve Y direction
'''
@app.route('/singlepredicth')
def singlepredicth():
    args = request.args
    yr, mo, day, hr, mn = int(args['yr']), int(args['mo']), int(args['day']), int(args['hr']), int(args['mn'])
    lat, lon = float(args['lat']), float(args['lon'])
    rate, dur, step = float(args['rate']), float(args['dur']), float(args['step'])
    model = int(args['model'])
    coeff = float(args['coeff'])
    alt = float(args['alt'])
    try:
        path = simulate.simulate(datetime(yr, mo, day, hr, mn).replace(tzinfo=timezone.utc), lat, lon, rate, step, dur, alt, model, coefficient=coeff)
    except Exception as e:
        print(f"Error in simulation: {str(e)}")
        return "error"
    return jsonify(path)

@app.route('/singlepredict')
def singlepredict():
    args = request.args
    timestamp = datetime.utcfromtimestamp(float(args['timestamp'])).replace(tzinfo=timezone.utc)
    lat, lon = float(args['lat']), float(args['lon'])
    rate, dur, step = float(args['rate']), float(args['dur']), float(args['step'])
    model = int(args['model'])
    coeff = float(args['coeff'])
    alt = float(args['alt'])
    try:
        path = simulate.simulate(timestamp, lat, lon, rate, step, dur, alt, model, coefficient=coeff)
    except Exception as e:
        print(f"Error in simulation: {str(e)}")
        return "error"
    return jsonify(path)

def singlezpb(timestamp, lat, lon, alt, equil, eqtime, asc, desc, model):
    try:
        dur = 0 if equil == alt else (equil - alt) / asc / 3600
        rise = simulate.simulate(timestamp, lat, lon, asc, 240, dur, alt, model, elevation=False)
        if len(rise) > 0:
            timestamp, lat, lon, alt, __, __, __, __ = rise[-1]
            timestamp = datetime.utcfromtimestamp(timestamp).replace(tzinfo=timezone.utc)
        
        coast = simulate.simulate(timestamp, lat, lon, 0, 240, eqtime, alt, model)
        if len(coast) > 0:
            timestamp, lat, lon, alt, __, __, __, __ = coast[-1]
            timestamp = datetime.utcfromtimestamp(timestamp).replace(tzinfo=timezone.utc)
        
        dur = (alt) / desc / 3600
        fall = simulate.simulate(timestamp, lat, lon, -desc, 240, dur, alt, model)
        return (rise, coast, fall)
    except Exception as e:
        print(f"Error in ZPB simulation: {str(e)}")
        return "error"

@app.route('/singlezpb')
def singlezpbh():
    args = request.args
    timestamp = datetime.utcfromtimestamp(float(args['timestamp'])).replace(tzinfo=timezone.utc)
    lat, lon = float(args['lat']), float(args['lon'])
    alt = float(args['alt'])
    equil = float(args['equil'])
    eqtime = float(args['eqtime'])
    asc, desc = float(args['asc']), float(args['desc'])
    model = int(args['model'])
    path = singlezpb(timestamp, lat, lon, alt, equil, eqtime, asc, desc, model)
    return jsonify(path)

@app.route('/spaceshot')
def spaceshot():
    args = request.args
    timestamp = datetime.utcfromtimestamp(float(args['timestamp'])).replace(tzinfo=timezone.utc)
    lat, lon = float(args['lat']), float(args['lon'])
    alt = float(args['alt'])
    equil = float(args['equil'])
    eqtime = float(args['eqtime'])
    asc, desc = float(args['asc']), float(args['desc'])
    paths = []
    for model in range(1, 21):
        result = singlezpb(timestamp, lat, lon, alt, equil, eqtime, asc, desc, model)
        if result == "error":
            return jsonify(["error"])
        paths.append(result)
    return jsonify(paths)

@app.route('/elev')
def elevation():
    lat, lon = float(request.args['lat']), float(request.args['lon'])
    return str(elev.getElevation(lat, lon))

@app.route('/windensemble')
def windensemble():
    args = request.args
    lat, lon = float(args['lat']), float(args['lon'])
    alt = float(args['alt'])
    yr, mo, day, hr, mn = int(args['yr']), int(args['mo']), int(args['day']), int(args['hr']), int(args['mn'])
    time = datetime(yr, mo, day, hr, mn).replace(tzinfo=timezone.utc)
    uList = []
    vList = []
    duList = []
    dvList = []

    levels = simulate.GFSHIST if yr < 2019 else simulate.GEFS

    for i in range(1, 21):
        try:
            u, v, du, dv = simulate.get_wind(time, lat, lon, alt, i, levels)
            uList.append(u)
            vList.append(v)
            duList.append(du)
            dvList.append(dv)
        except Exception as e:
            print(f"Error getting wind data for model {i}: {str(e)}")
            return "error"
    
    return jsonify([uList, vList, duList, dvList])

@app.route('/wind')
def wind():
    args = request.args
    lat, lon = float(args['lat']), float(args['lon'])
    model = int(args['model'])
    alt = float(args['alt'])
    yr, mo, day, hr, mn = int(args['yr']), int(args['mo']), int(args['day']), int(args['hr']), int(args['mn'])
    levels = simulate.GFSHIST if yr < 2019 else simulate.GEFS
    time = datetime(yr, mo, day, hr, mn).replace(tzinfo=timezone.utc)
    try:
        u, v, du, dv = simulate.get_wind(time, lat, lon, alt, model, levels)
    except Exception as e:
        print(f"Error getting wind data: {str(e)}")
        return "error"
    return jsonify([u, v, du, dv])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
