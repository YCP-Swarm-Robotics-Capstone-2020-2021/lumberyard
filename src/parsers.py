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
        # print("This is a Narwhal log")
        log_type = "Narwhal"
        device_id = "Narwhal"
    elif "LOG_Dolphin" in file.name:
        # print("This is a Dolphin log")
        log_type = "Dolphin"
        # Extract dolphin id
        robot_match = re.search(r'Dolphin\d+', file.name)
        # if robot_match.group(0):
        try:
            device_id = robot_match.group(0)
        except AttributeError:
            # print('Error finding robot id from file name')
            sys.exit(1)
    # If the log does not contain dolphin or narwhal exit the parser
    else:
        # print('Log neither Dolphin nor Narwhal')
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

    # This set will filter duplicates out, and then be sorted on timestamp
    parsed_set = set()
    runs = []

    # Read the file, and place the tuples of the lines in the set
    for line in itertools.islice(file, 5, None):
        line = line.rstrip()
        try:
            # Each line is composed of <timestamp> <module> <process> <data>
            (time, module, process, data) = line.split(maxsplit=3)
            # Check for null character
            if '\u0000' in line:
                data = data.split('\u0000')[0]
            parsed_set.add((time, module, process, data))
        except ValueError as e:
            print("Key Value Error")

    # Convert set to list, then sort
    parsed_list = list(parsed_set)
    parsed_list.sort(key=sort_on)

    # Current run is outside the scope of the for loop, since it needs to persist each iteration
    current_run = ''
    record_run = False

    # Iterate sorted list and created json objects
    for i in parsed_list:
        parsed_line = {
            'time': i[0],
            'module': i[1],
            'process': i[2],
            'data': i[3]
        }
        parsed['log_content'].append(parsed_line)

        # Check to see if the current line is a start of stop marker for a run
        # If the current run is empty, then start filling out the current run
        if parsed_line['module'] == 'RUN_STARTED' and current_run == '':

            # Parse id and place in current run
            current_run_id = int(re.findall(r'[0-9]+', parsed_line['data'])[0])

            # noinspection PyDictCreation
            current_run = {
                'run_id': current_run_id,
                'start_time': parsed_line['time'],
                'stop_time': '',
                'run_content': []
            }

            # Append current run to runs list, and clear the current run
            runs.append(current_run)

            # Start recording the run
            record_run = True

        elif parsed_line['module'] == 'RUN_ENDED' and current_run != '':

            # Parse stop time
            current_run['stop_time'] = parsed_line['time']

            # Append stop line to run
            current_run['run_content'].append(parsed_line)

            current_run = ''
            record_run = False

        if record_run:
            # Append stop line to run
            current_run['run_content'].append(parsed_line)

    # Close log file
    file.close()

    # Open new json file, write the json contents, and close it
    with open(file_path + ".json", "w+") as file:
        file.write(json.dumps(parsed))
    # Return the information on the log for storing in DB
    try:
        del parsed['log_content']
    except KeyError:
        print('Error removing log_content from dict')
    print(json.dumps(parsed))

    for run in runs:
        run_key = run['run_id']
        # Log name with run appended to it
        run_name = file_path + f"-run{run_key}"
        # Write the run
        with open(run_name + ".json", "w+") as file:
            file.write(json.dumps(run))
        # If it's a Narwhal log file, run it through the visualization parser
        if "Narwhal" in log_type:
            visualization_parser(run, run_name.replace(".alog", "") + ".script")
        # Delete the run_content from the dictionary to do some memory cleanup
        try:
            del run['run_content']
        except KeyError:
            print('Error removing run_content from dict')
        print(json.dumps(run))
    return json.dumps(parsed), json.dumps(runs)


# This function defines what to sort the list on. The tuple has the timestamp in the first position
def sort_on(e):
    return float(e[0])


# Log parser for visualization script generation
# Currently, this just parses the Narwhal's log file
def visualization_parser(input_json, output_file):

    # To which decimal place should the timestamp be rounded
    TIME_ROUNDING = 1
    # The increment in which the current time should progess when generating the final script.
    # This corresponds to TIME_ROUNDING
    TIME_INCREMENT = 0.1

    start_time = round(float(input_json["run_content"][-1]["time"]), TIME_ROUNDING)
    stop_time = 0

    # Which robots are reported as being connected at each timestamp
    connected_robots = dict()  # dict(k: time, v: set(robot_id))

    # Parsed script data
    parsed = dict()  # dict(k: time, v: dict(k: id, v: data))

    for obj in input_json["run_content"]:
        time = round(float(obj["time"]), TIME_ROUNDING)

        if "Registered_Bots" in obj["module"]:

            # Data format is Bot_Ids=<id>:0|<id>:0|...
            # TODO: I'm not sure what the ":0" postfix means
            # Collect the robot ids
            robots = obj["data"].split("=")[-1].split("|")
            # Remove the ":0" from each id and discard any empty strings
            robots = [robot.split(":")[0] for robot in robots if robot]
            # Since this module lists ALL robots currently known to be connected, just directly set the connected robots
            connected_robots[time] = set(robots)
        elif "Reg_In" in obj["module"]:
            # Data format is id=<id>
            robot_id = obj["data"].split("=")[-1]
            connected_robots.setdefault(time, set()).add(robot_id)
        elif "Reg_Ack" in obj["module"]:
            # Module format is <id>_Reg_Ack
            robot_id = obj["module"].split("_")[0]
            if "true" in obj["data"]:
                connected_robots.setdefault(time, set()).add(robot_id)
            else:
                connected_robots.setdefault(time, set()).remove(robot_id)
        # Update_Pos is robot reporting new position
        elif "Update_Pos" in obj["module"]:
            if time < start_time: start_time = time
            if time > stop_time: stop_time = time

            # Remove all whitespace from data
            obj["data"] = re.sub(r"\s+", "", obj["data"]).split(",")

            # Get key-value pairs from the data
            items = dict()
            for item in obj["data"]:
                (lhs, rhs) = item.split("=")
                items[lhs] = rhs

            if "id" in items:
                parsed.setdefault(time, dict())[items["id"]] = \
                    {
                        "x": round(float(items.get("xPos") or 0.0), 3),
                        "y": round(float(items.get("yPos") or 0.0), 3),
                        "r": round(float(items.get("attitude") or 0.0), 3),
                        "s": round(float(items.get("current_speed") or 0.0), 3)
                    }
                
    # Fill in any time gaps

    current_time = start_time
    # Last known connected status for each robot
    prev_connected = set()
    # Last known value for each robot
    prev_data = dict()  # dict(k: id, v: data)

    while current_time <= stop_time:
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
    # NOTE: 'u' stands for 'updated' and 'nu' stands for 'notUpdated'. This is to 
    # cut down the file size slightly by removing unnecessary characters
    last_updated_times = dict()  # dict(k: robot_id, v: time)
    for time in parsed.keys():
        if parsed[time]:
            idle_robots = []
            parsed[time]['u'] = []
            for (robot_id, data) in parsed[time].items():
                if robot_id != 'u':
                    # If it is robot's first update time, make last updated
                    if robot_id not in last_updated_times.keys():
                        last_updated_times[robot_id] = time
                        # Add 'id' field and append to updated list
                        data['id'] = robot_id
                        parsed[time]['u'].append(data)
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
                            parsed[time]['u'].append(data)
                        else:
                            idle_robots.append(robot_id)

            # Add 'notUpdated' object to each timestamp
            parsed[time]['nu'] = []
            # For each idle robot for this timestamp delete it's entry, and add robot_id to 'notUpdated' object
            for robot_id in idle_robots:
                del parsed[time][robot_id]
                parsed[time]['nu'].append(robot_id)

    # Remove any first level 'Dolphin__: {}' objects, since there is now a first level 'updated: []' list for each timestamp
    for time in parsed.keys():
        if parsed[time]:
            for data in parsed[time]['u']:
                del parsed[time][data['id']]

    # Change the values of parsed into lists rather than dictionaries
    # This is to prevent many small hashmaps from being created while deserializing the script in the visualization
    listified_parsed = list()
    for (time, states) in parsed.items():
        if parsed[time]:
            updated_data = states['u']
            not_updated_date = states['nu']

            timestamp = {"t": time, "u": [], "nu": []}

            timestamp['u'] = updated_data
            timestamp['nu'] = not_updated_date

            listified_parsed.append(timestamp)
        else:
            parsed[time]['u'] = []
            parsed[time]['nu'] = []

    output = {"timeinc": TIME_INCREMENT, "timeround": TIME_ROUNDING, "timestart": start_time, "timeend": stop_time,
            "timestamps": listified_parsed}

    with open(output_file, "w+") as f:
        f.write(json.dumps(output))
