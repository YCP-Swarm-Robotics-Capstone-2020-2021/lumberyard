# Log parser for visualization script generation

import itertools
import re

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

        if 'xPos' in items and 'yPos' in items and 'attitude' in items:
            positions[time] = \
                {
                    "xPos": items['xPos'],
                    "yPos": items['yPos'],
                    "attitude": items['attitude'],
                }

# Adjust timestamps so that they all begin at 0
adjusted_positions = {}
time_diff = list(positions.keys())[0]
for time, data in positions.items():
    adjusted_positions[str(round(float(time) - float(time_diff), 3))] = data

for ((k1, v1), (k2, v2)) in zip(positions.items(), adjusted_positions.items()):
    print("{{{}: {}}} - {{{}: {}}}".format(k1, v1, k2, v2))
