import os
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)
start_time = None
runners = []
times = {}
race_type = None
laps_needed = {
    '100m': 1,
    '400m': 1,
    '800m': 2,
    '1500m': 4,
    '3000m': 8,
    '5000m': 13
}

@app.route('/')
def index():
    return render_template('index.html', runners=runners)

@app.route('/add_runner', methods=['POST'])
def add_runner():
    if len(runners) >= 12:
        return jsonify({"error": "Maximum number of runners reached"}), 400
    name = request.form.get('name')
    if name and len(runners) < 12:
        runners.append(name)
        times[name] = []  # Initialize an empty list for lap times
    return jsonify(runners=runners)

@app.route('/start_timer', methods=['POST'])
def start_timer():
    global start_time, race_type
    start_time = datetime.now()
    race_type = request.form.get('race_type')
    return jsonify(start_time=start_time.isoformat(), runners=runners, race_type=race_type)

@app.route('/record_time', methods=['POST'])
def record_time():
    runner = request.form.get('runner')
    if start_time and runner in runners:
        current_time = datetime.now()
        if times[runner]:
            last_lap_time = times[runner][-1]
            lap_time = (current_time - last_lap_time).total_seconds()
        else:
            lap_time = (current_time - start_time).total_seconds()
        times[runner].append(current_time)
        lap_times = [format_time((times[runner][i] - times[runner][i-1]).total_seconds()) if i > 0 else format_time((times[runner][i] - start_time).total_seconds()) for i in range(len(times[runner]))]
        total_time = format_time(sum([(times[runner][i] - times[runner][i-1]).total_seconds() if i > 0 else (times[runner][i] - start_time).total_seconds() for i in range(len(times[runner]))]))

        if all(len(lap_times) == laps_needed[race_type] for lap_times in times.values()):
            return jsonify(times=sorted_times(), stop_timer=True, message="Race finished")
    return jsonify(times=sorted_times(), stop_timer=False, message="")

@app.route('/reset', methods=['POST'])
def reset():
    global start_time, runners, times, race_type
    start_time = None
    runners = []
    times = {}
    race_type = None
    return jsonify({"status": "reset"})

def format_time(seconds):
    total_seconds = seconds
    minutes, seconds = divmod(total_seconds, 60)
    split_seconds = round(seconds % 1, 2)
    seconds = int(seconds)
    return f"{int(minutes):02d}:{seconds:02d}.{int(split_seconds * 100):02d}"

def sorted_times():
    sorted_dict = {}
    for runner, lap_times in times.items():
        total_time = sum([(lap_times[i] - lap_times[i-1]).total_seconds() if i > 0 else (lap_times[i] - start_time).total_seconds() for i in range(len(lap_times))])
        formatted_lap_times = [format_time((lap_times[i] - lap_times[i-1]).total_seconds()) if i > 0 else format_time((lap_times[i] - start_time).total_seconds()) for i in range(len(lap_times))]
        sorted_dict[runner] = {
            "lap_times": formatted_lap_times,
            "total_time": format_time(total_time)
        }
    # Sort runners by total time
    sorted_dict = dict(sorted(sorted_dict.items(), key=lambda item: sum(map(float, item[1]['total_time'].split(':')))))
    return sorted_dict

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))