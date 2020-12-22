# Log parser for visualization script generation

# Currently, this just parses the Narwhal's log file

import itertools
import re
import json

file_path = "../test_logs/tworobotlog/LOG_Narwhal_1_12_2020_____12_55_43/LOG_Narwhal_1_12_2020_____12_55_43.alog"
file = open(file_path, "r")

# To which decimal place should the timestamp be rounded
TIME_ROUNDING = 1
# The increment in which the current time should progess when generating the final script.
# This corresponds to TIME_ROUNDING
TIME_INCREMENT = 0.1

# Which robots are reported as being connected at each timestamp
connected_robots = dict()   # dict(k: time, v: set(robot_id))

# Parsed script data
parsed = dict()             # dict(k: time, v: dict(k: id, v: data))
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
prev_data = dict()      # dict(k: id, v: data)

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
        if robot_id not in parsed[current_time] and robot_id in connected_robots:
            parsed[current_time][robot_id] = data

    current_time = round(current_time + TIME_INCREMENT, TIME_ROUNDING)

print(json.dumps(parsed, indent=4))

output = {"timeinc": TIME_INCREMENT, "timeround": TIME_ROUNDING, "timeend": end_time, "steps": parsed}

file.close()
file = open(file_path + ".script", "w+")
file.write(json.dumps(output))
file.close()
