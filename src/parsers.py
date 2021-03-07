import itertools
import re
import json
import sys


# Log parser for the web application
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
    # file = open(file.name + ".json", "w+")
    return json.dumps(parsed)



# Log parser for visualization script generation
# Currently, this just parses the Narwhal's log file
def visualization_parser(file_path):
    file = open(file_path, "r")
    # To which decimal place should the timestamp be rounded
    TIME_ROUNDING = 1
    # The increment in which the current time should progess when generating the final script.
    # This corresponds to TIME_ROUNDING
    TIME_INCREMENT = 0.1

    # Which robots are reported as being connected at each timestamp
    connected_robots = dict()  # dict(k: time, v: set(robot_id))

    # Parsed script data
    parsed = dict()  # dict(k: time, v: dict(k: id, v: data))
    # Time at the end of the log
    end_time = 0

    for line in itertools.islice(file, 5, None):
        line = line.rstrip()
        # Each line is composed of <timestamp> <module> <process> <data>
        (time, module, _, data) = line.split(maxsplit=3)
        time = round(float(time), TIME_ROUNDING)
        end_time = time

        # Recognize that robot has connected or failed to indicate that it is still connected
        if "Registered_Bots" in module:
            # Data format is Bot_Ids=<id>:0|<id>:0|...
            # TODO: I'm not sure what the ":0" postfix means
            # Collect the robot ids
            robots = data.split("=")[-1].split("|")
            # Remove the ":0" from each id and discard any empty strings
            robots = [robot.split(":")[0] for robot in robots if robot]
            # Since this module lists ALL robots currently known to be connected, just directly set the connected robots
            connected_robots[time] = set(robots)
        elif "Reg_In" in module:
            # Data format is id=<id>
            robot_id = data.split("=")[-1]
            connected_robots.setdefault(time, set()).add(robot_id)
        elif "Reg_Ack" in module:
            # Module format is <id>_Reg_Ack
            robot_id = module.split("_")[0]
            if "true" in data:
                connected_robots.setdefault(time, set()).add(robot_id)
            else:
                connected_robots.setdefault(time, set()).remove(robot_id)
        # Update_Pos is robot reporting new position
        elif "Update_Pos" in module:
            # Remove all whitespace from data
            data = re.sub(r"\s+", "", data).split(",")

            # Get key-value pairs from the data
            items = dict()
            for item in data:
                (lhs, rhs) = item.split("=")
                items[lhs] = rhs

            if "id" in items:
                entry = parsed.setdefault(time, dict())[items["id"]] = \
                    {
                        "x": round(float(items.get("xPos") or 0.0), 3),
                        "y": round(float(items.get("yPos") or 0.0), 3),
                        "r": round(float(items.get("attitude") or 0.0), 3),
                        "s": round(float(items.get("current_speed") or 0.0), 3)
                    }

    # Fill in any time gaps
    current_time = 0.0
    # Last known connected status for each robot
    prev_connected = set()
    # Last known value for each robot
    prev_data = dict()  # dict(k: id, v: data)

    while current_time <= end_time:
        # Populate connected_robots with last known status if entry does not already exist,
        # other update last known status
        if current_time in connected_robots:
            prev_connected = connected_robots[current_time]
        else:
            connected_robots[current_time] = prev_connected

        # If parsed data has current time, update the last known data for each robot
        if current_time in parsed:
            for (robot_id, data) in parsed[current_time].items():
                prev_data[robot_id] = data
        else:
            # Have to directly set this here instead of using `setdefault(time, dict())` later on to make sure that
            # there is an empty entry here if no robots are connected
            parsed[current_time] = dict()

        # For the current time entry in the parsed data, fill in any missing robots with their last known data
        # if the robot is still known to be connected
        for (robot_id, data) in prev_data.items():
            if robot_id not in parsed[current_time] and robot_id in connected_robots[current_time]:
                parsed[current_time][robot_id] = data

        current_time = round(current_time + TIME_INCREMENT, TIME_ROUNDING)

    # Remove any non updated robots for a given timestamp
    # Last time updated pos for each robot
    last_updated_times = dict()  # dict(k: robot_id, v: time)
    for time in parsed.keys():
        if parsed[time]:
            idle_robots = []
            parsed[time]['updated'] = []
            for (robot_id, data) in parsed[time].items():
                if robot_id != 'updated':
                    # If it is robot's first update time, make last updated
                    if robot_id not in last_updated_times.keys():
                        last_updated_times[robot_id] = time
                        # Add 'id' field and append to updated list
                        data['id'] = robot_id
                        parsed[time]['updated'].append(data)
                    else:
                        # Get robot's data from it's last updated time
                        # Add 'id' field
                        last_updated_time = last_updated_times[robot_id]
                        prev_data = parsed[last_updated_time][robot_id]
                        data['id'] = robot_id

                        # Compare with current data
                        # If same, add to idle_robots list
                        # If different, update last_updated_times
                        if prev_data != data:
                            last_updated_times[robot_id] = time
                            parsed[time]['updated'].append(data)
                        else:
                            idle_robots.append(robot_id)

            # Add 'notUpdated' object to each timestamp
            parsed[time]['notUpdated'] = []
            # For each idle robot for this timestamp delete it's entry, and add robot_id to 'notUpdated' object
            for robot_id in idle_robots:
                del parsed[time][robot_id]
                parsed[time]['notUpdated'].append(robot_id)

    # Remove any first level 'Dolphin__: {}' objects, since there is now a first level 'updated: []' list for each timestamp
    for time in parsed.keys():
        if parsed[time]:
            for data in parsed[time]['updated']:
                del parsed[time][data['id']]

    # Change the values of parsed into lists rather than dictionaries
    # This is to prevent many small hashmaps from being created while deserializing the script in the visualization
    listified_parsed = dict()
    for (time, states) in parsed.items():
        if parsed[time]:
            updated_data = states['updated']
            not_updated_date = states['notUpdated']

            listified_parsed[time] = {"updated": [], "notUpdated": []}

            listified_parsed[time]['updated'] = updated_data
            listified_parsed[time]['notUpdated'] = not_updated_date
        else:
            parsed[time]['updated'] = []
            parsed[time]['notUpdated'] = []

    # print(json.dumps(parsed, indent=4))

    output = {"timeinc": TIME_INCREMENT, "timeround": TIME_ROUNDING, "timeend": end_time,
              "timestamps": listified_parsed}

    file.close()
    file = open(file_path + ".script", "w+")
    file.write(json.dumps(output))
    file.close()

