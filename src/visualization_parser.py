# Log parser for visualization script generation

import itertools
import re
import json

file_path = "../test_logs/tworobotlog/LOG_Narwhal_1_12_2020_____12_55_43/LOG_Narwhal_1_12_2020_____12_55_43.alog"
file = open(file_path, "r")

positions = {}

# Iterate through each line of the file, skipping the header
for line in itertools.islice(file, 5, None):
    line = line.rstrip()
    # Each line is composed of <timestamp> <module> <process> <data>
    (time, module, _, data) = line.split(maxsplit=3)

    # We only care about the robot reporting a new position
    if 'Update_Pos' in module:
        # Remove all whitespace from data
        data = re.sub(r'\s+', '', data).split(',')

        items = {}
        for item in data:
            (lhs, rhs) = item.split('=')
            items[lhs] = rhs

        if 'id' in items:
            positions.setdefault(time, set()).add(json.dumps(
                {
                    'id': items['id'],
                    'xPos': float(items.get('xPos') or 0.0),
                    'yPos': float(items.get('yPos') or 0.0),
                    'attitude': float(items.get('attitude') or 270.0),
                    'current_speed': float(items.get('current_speed') or 0.0)
                }
            ))

output = {}
for time, data in positions.items():
    output[time] = list(map(lambda a: json.loads(a), data))

output = {"offset": list(positions.keys())[0], "timestamps": output}

file.close()
file = open(file_path + ".script", "w+")
file.write(json.dumps(output))
file.close()

print(json.dumps(output, indent=4))

""
# Adjust timestamps so that they all begin at 0
# adjusted_positions = {}
# time_diff = list(positions.keys())[0]
# for time, data in positions.items():
#     list_data = []
#     for d in data:
#         list_data.append(json.loads(d))
#     adjusted_positions[str(round(float(time) - float(time_diff), 3))] = list_data
#
# for (a, b) in zip(positions.items(), adjusted_positions.items()):
#     print("{} - {}".format(a, b))
