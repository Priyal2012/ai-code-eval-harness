"""Regex-based parser for the combined log format."""

import re

_PATTERN = re.compile(
    r"""^(?P<ip>\S+)\s+-\s+(?P<user>\S+)\s+
        \[(?P<timestamp>[^\]]+)\]\s+
        "(?P<method>[A-Z]+)\s+(?P<path>\S+)\s+(?P<protocol>HTTP/[\d.]+)"\s+
        (?P<status>\d{3})\s+(?P<bytes>\d+|-)\s+
        "(?P<referrer>(?:[^"\\]|\\.)*)"\s+
        "(?P<user_agent>(?:[^"\\]|\\.)*)"\s*$""",
    re.VERBOSE,
)


def parse_log_line(line: str) -> dict:
    """Parse one combined-log-format line into a dict; raise ValueError if malformed."""
    match = _PATTERN.match(line)
    if not match:
        raise ValueError(f"line does not match the combined log format: {line[:80]!r}")
    g = match.groupdict()
    return {
        "ip": g["ip"],
        "user": None if g["user"] == "-" else g["user"],
        "timestamp": g["timestamp"],
        "method": g["method"],
        "path": g["path"],
        "protocol": g["protocol"],
        "status": int(g["status"]),
        "bytes": 0 if g["bytes"] == "-" else int(g["bytes"]),
        "referrer": None if g["referrer"] == "-" else g["referrer"].replace('\\"', '"'),
        "user_agent": g["user_agent"].replace('\\"', '"'),
    }
