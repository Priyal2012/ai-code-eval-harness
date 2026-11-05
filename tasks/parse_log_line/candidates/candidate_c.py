import re
import sys
import os


def parse_log_line(line, defaults={}):
    result = dict(defaults)
    try:
        m = re.match(r'(\S+) - (\S+) \[(.*?)\] "(\S+) (\S+) (\S+)" (\d+) (\S+) "(.*?)" "(.*)"', line)
        if m:
            result["ip"] = m.group(1)
            if m.group(2) == "-":
                result["user"] = None
            else:
                result["user"] = m.group(2)
            result["timestamp"] = m.group(3)
            result["method"] = m.group(4)
            result["path"] = m.group(5)
            result["protocol"] = m.group(6)
            result["status"] = int(m.group(7))
            if m.group(8) == "-":
                result["bytes"] = 0
            else:
                result["bytes"] = int(m.group(8))
            if m.group(9) == "-":
                result["referrer"] = None
            else:
                result["referrer"] = m.group(9)
            result["user_agent"] = m.group(10)
        else:
            print("could not parse line")
            return None
    except:
        return None
    return result
