import itertools
import re
import json
import sys


# Parameter is the file path of the log
def web_parser(file_path):
    # Open the log file in read mode
    file = open(file_path, 'r')

    # Check to see what type of log file this is, and set log_type and robot_id appropriately
    if "LOG_Narwhal" in file.name:
        print("This is a Narwhal log")
        log_type = "Narwhal"
        device_id = "Narwhal"
    elif "LOG_Dolphin" in file.name:
        print("This is a Dolphin log")
        log_type = "Dolphin"
        # Extract dolphin id
        robot_match = re.search(r'Dolphin\d+', file.name)
        # if robot_match.group(0):
        try:
            device_id = robot_match.group(0)
        except AttributeError:
            print('Error finding robot id from file name')
            sys.exit(1)
    # If the log does not contain dolphin or narwhal exit the parser
    else:
        print('Log neither Dolphin nor Narwhal')
        sys.exit(1)

    # Parse date and time from file path
    # The leading _ differentiates the date and time from robot id
    matches = re.findall(r'_[0-9]+_[0-9]+_[0-9]+', file.name)
    try:
        # Split the date and time from the underscores
        date_parts = matches[0].split('_')
        time_parts = matches[1].split('_')

        # Recreate the date and times with appropriate separator
        date = '-'.join(date_parts[1:])
        time = ':'.join(time_parts[1:])

    # If the splits fail, they will throw an index error, which is caught here
    except IndexError:
        print('Error getting date and time from file name')
        sys.exit(1)

    # Parsed script data
    parsed = {
        "device_id": device_id,
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


def visualization_parser(file_path):
    print("Log file parsed into visualization script")
