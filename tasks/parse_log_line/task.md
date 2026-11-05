# parse_log_line — parse one line of an access log

Implement `parse_log_line(line: str) -> dict`.

Lines follow the common log format with a referrer and user agent:

```
<ip> - <user> [<timestamp>] "<method> <path> <protocol>" <status> <bytes> "<referrer>" "<user_agent>"
```

Example:

```
10.0.0.7 - alice [05/Nov/2026:10:15:32 +0000] "GET /api/items?page=2 HTTP/1.1" 200 5123 "https://example.com/" "Mozilla/5.0 (X11; Linux x86_64)"
```

Return a dict with keys `ip`, `user`, `timestamp`, `method`, `path`, `protocol`,
`status` (int), `bytes` (int, `-` means 0), `referrer`, `user_agent`.

Requirements

- `user` and `referrer` may be `-`; return `None` for those.
- Quoted fields may contain spaces (user agents almost always do).
- Raise `ValueError` for lines that do not match the format — never return partial data.
