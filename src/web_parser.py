# Log parser to create json from a log file

import itertools
import re
import json


file_path = "../test_logs/sixrobotlog/LOG_Narwhal_1_12_2020_____13_01_34/LOG_Narwhal_1_12_2020_____13_01_34.alog"
file = open(file_path, "r")

if "LOG_Narwhal" in file_path:
    print("This is a Narwhal log")
elif "LOG_Dolphin" in file_path:
    print("This is a Dolphin log")

# Which robots are reported as being connected at each timestamp
connected_robots = dict()

# Parsed script data
parsed = dict()

for line in itertools.islice(file, 5, None):
    line = line.rstrip()
    # Each line is composed of <timestamp> <module> <process> <data>
    (time, module, _, data) = line.split(maxsplit=3)
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



# Close log file
file.close()
# Open new json file, write the json contents, and close it
file = open(file_path + ".json", "w+")
file.write(json.dumps(parsed))
file.close()