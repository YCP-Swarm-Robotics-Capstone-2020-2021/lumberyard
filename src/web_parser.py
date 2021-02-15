# Log parser to create json from a log file

import itertools
import re
import json


# TODO Make script a function that accepts file, file path as a parameter

file_path = "../test_logs/sixrobotlog/LOG_Narwhal_1_12_2020_____13_01_34/LOG_Narwhal_1_12_2020_____13_01_34.alog"
opened_file = open(file_path, "r")


# Parameter is an opened file, rather than a file path
def web_parser(file):
    # Check to see what type of log file this is, and set log_type and robot_id appropriately
    if "LOG_Narwhal" in file.name:
        print("This is a Narwhal log")
        log_type = "Narwhal"
        robot_id = "Narwhal"
    elif "LOG_Dolphin" in file_path:
        print("This is a Dolphin log")
        log_type = "Dolphin"
        # Extract dolphin id
        robot_match = re.search(r'LOG_Dolphin\d+', file.name)
        if robot_match.group(0):
            robot_id = robot_match.group(0)
        else:
            print("Error searching for robot id")
    else:
        print('Log neither Dolphin nor Narwhal')

    # Parse date from file path
    matches = re.findall(r'[0-9]+_[0-9]+_[0-9]+', file.name)
    date_parts = matches[0].split('_')
    time_parts = matches[1].split('_')
    date = '-'.join(date_parts)
    time = ':'.join(time_parts)

    # Which robots are reported as being connected at each timestamp
    connected_robots = dict()

    # Parsed script data
    parsed = {
        "robot_id": robot_id,
        "date": date,
        "time": time,
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
    # print(json.dumps(parsed))
    # Open new json file, write the json contents, and close it
    file = open(file.name + ".json", "w+")
    file.write(json.dumps(parsed))
    file.close()


web_parser(opened_file)
