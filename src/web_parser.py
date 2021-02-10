# Log parser to create json from a log file

import itertools
import re
import json


file_path = "../test_logs/sixrobotlog/LOG_Narwhal_1_12_2020_____13_01_34/LOG_Narwhal_1_12_2020_____13_01_34.alog"
file = open(file_path, "r")

log_type = ''
if "LOG_Narwhal" in file_path:
    print("This is a Narwhal log")
    log_type = "Narwhal"
elif "LOG_Dolphin" in file_path:
    print("This is a Dolphin log")
    log_type = "Dolphin"

# Which robots are reported as being connected at each timestamp
connected_robots = dict()

# Parsed script data
parsed = {
    "date": "date",
    "log_type": log_type,
    "log_content": []
}

for line in itertools.islice(file, 5, None):
    line = line.rstrip()
    # Each line is composed of <timestamp> <module> <process> <data>
    (time, module, process, data) = line.split(maxsplit=3)
    parsed_line = {
        'time': time,
        'module': module,
        'process': process,
        'data': data
    }

    parsed['log_content'].append(parsed_line)



# Close log file
file.close()
# Open new json file, write the json contents, and close it
file = open(file_path + ".json", "w+")
file.write(json.dumps(parsed))
file.close()