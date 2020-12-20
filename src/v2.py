# Log parser for visualization script generation

import itertools
import re
import json

file_path = "../test_logs/tworobotlog/LOG_Narwhal_1_12_2020_____12_55_43/LOG_Narwhal_1_12_2020_____12_55_43.alog"
file = open(file_path, "r")

parsed_log = {}

robots = {}

# Iterate through each line of the file, skipping the header
for line in itertools.islice(file, 5, None):
    line = line.rstrip()
    # Each line is composed of <timestamp> <module> <process> <data>
    (time, module, _, data) = line.split(maxsplit=3)

    # Robot reporting a new position
    if 'Update_Pos' in module:
        # Remove all whitespace from data
        data = re.sub(r'\s+', '', data).split(',')

        # Get key-value pairs from the line of data
        items = {}
        for item in data:
            (lhs, rhs) = item.split('=')
            items[lhs] = rhs

        if 'id' in items:
            robots.setdefault(items['id'], list()).append(
                    {
                        'time': time,
                        'x_pos': round(float(items.get('xPos') or 0.0), 3),
                        'y_pos': round(float(items.get('yPos') or 0.0), 3),
                        'attitude': round(float(items.get('attitude') or 270.0), 3),
                        'current_speed': round(float(items.get('current_speed') or 0.0), 3)
                    }
                )

steps = {}
step_increment = 0.01
step_rounding = 2

largest_step = 0.0
for robot, timestamps in robots.items():
    timestamps.sort(key=lambda t: float(t['time']))

    curr_step = 0.0
    last_step = \
        {
            'id': robot,
            'x_pos': timestamps[0]['x_pos'],
            'y_pos': timestamps[0]['y_pos'],
            'attitude': timestamps[0]['attitude'],
            'current_speed': timestamps[0]['current_speed']
        }

    for i in range(1, len(timestamps)):
        timestamp = timestamps[i]
        rounded_time = round(float(timestamp['time']), 3)
        if rounded_time <= curr_step:
            last_step = \
                {
                    'id': robot,
                    'x_pos': timestamp['x_pos'],
                    'y_pos': timestamp['y_pos'],
                    'attitude': timestamp['attitude'],
                    'current_speed': timestamp['current_speed']
                }

        steps.setdefault(curr_step, list()).append(last_step)
        curr_step = round(curr_step + step_increment, step_rounding)

    if curr_step > largest_step:
        largest_step = curr_step

output = {"step_increment": step_increment, 'step_rounding': step_rounding, 'largest_step': largest_step, 'steps': steps}

file.close()
file = open(file_path + ".script", "w+")
file.write(json.dumps(output))
file.close()

print(json.dumps(output, indent=4))
#print(json.dumps(robots))
