def parse_log_line(line):
    """Split on whitespace. Works for simple lines but breaks on quoted fields with spaces."""
    parts = line.split()
    if len(parts) < 10:
        raise ValueError("too few fields")
    return {
        "ip": parts[0],
        "user": None if parts[2] == "-" else parts[2],
        "timestamp": (parts[3] + " " + parts[4]).strip("[]"),
        "method": parts[5].strip('"'),
        "path": parts[6],
        "protocol": parts[7].strip('"'),
        "status": int(parts[8]),
        "bytes": 0 if parts[9] == "-" else int(parts[9]),
        "referrer": None if parts[10].strip('"') == "-" else parts[10].strip('"'),
        "user_agent": " ".join(parts[11:]).strip('"'),
    }
