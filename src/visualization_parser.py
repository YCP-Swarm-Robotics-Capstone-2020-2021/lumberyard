# Log parser for visualization script generation

import itertools
import re
import json

file = open("../test_logs/onerobotlog/LOG_Dolphin0_23_10_2020_____18_51_42/LOG_Dolphin0_23_10_2020_____18_51_42.alog", "r")

positions = {}

# Iterate through each line of the file, skipping the header
for line in itertools.islice(file, 5, None):
    line = line.rstrip()
    # Each line is composed of <timestamp> <module> <process> <data>
    (time, module, _, data) = line.split(maxsplit=3)

    # We only care about the robot reporting a new position
    if module == 'Update_Pos':
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
                }
            ))

output = {}
for time, data in positions.items():
    output[time] = list(map(lambda a: json.loads(a), data))

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
