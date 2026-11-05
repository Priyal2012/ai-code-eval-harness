"""Hidden tests for parse_log_line. Imports the candidate as `solution`."""

from solution import parse_log_line

LINE = (
    '10.0.0.7 - alice [05/Nov/2026:10:15:32 +0000] "GET /api/items?page=2 HTTP/1.1" '
    '200 5123 "https://example.com/" "Mozilla/5.0 (X11; Linux x86_64)"'
)


def test_parses_all_fields():
    rec = parse_log_line(LINE)
    assert rec["ip"] == "10.0.0.7"
    assert rec["user"] == "alice"
    assert rec["timestamp"] == "05/Nov/2026:10:15:32 +0000"
    assert rec["method"] == "GET"
    assert rec["path"] == "/api/items?page=2"
    assert rec["protocol"] == "HTTP/1.1"
    assert rec["status"] == 200
    assert rec["bytes"] == 5123


def test_numeric_types():
    rec = parse_log_line(LINE)
    assert isinstance(rec["status"], int)
    assert isinstance(rec["bytes"], int)


def test_user_agent_with_spaces():
    rec = parse_log_line(LINE)
    assert rec["user_agent"] == "Mozilla/5.0 (X11; Linux x86_64)"
    assert rec["referrer"] == "https://example.com/"


def test_edge_dash_user_and_referrer():
    line = '203.0.113.9 - - [05/Nov/2026:10:16:00 +0000] "POST /login HTTP/1.1" 302 - "-" "curl/8.4.0"'
    rec = parse_log_line(line)
    assert rec["user"] is None
    assert rec["referrer"] is None
    assert rec["bytes"] == 0
    assert rec["status"] == 302


def test_edge_path_with_spaces_encoded_and_quotes_in_agent():
    line = (
        '192.168.1.1 - bob [01/Jan/2026:00:00:00 +0530] "GET /files/my%20doc.pdf HTTP/2.0" '
        '404 0 "-" "Agent \\"quoted\\" 1.0"'
    )
    rec = parse_log_line(line)
    assert rec["path"] == "/files/my%20doc.pdf"
    assert rec["protocol"] == "HTTP/2.0"
    assert rec["status"] == 404
    assert "quoted" in rec["user_agent"]


def test_edge_referrer_with_spaces():
    line = (
        '10.0.0.8 - - [05/Nov/2026:10:17:00 +0000] "GET /x HTTP/1.1" 200 10 '
        '"https://example.com/search?q=blue widgets" "Mozilla/5.0"'
    )
    rec = parse_log_line(line)
    assert rec["referrer"] == "https://example.com/search?q=blue widgets"
    assert rec["user_agent"] == "Mozilla/5.0"


def test_edge_malformed_raises():
    for bad in ("", "not a log line", '10.0.0.7 - - [ts] "GET / HTTP/1.1" abc 12 "-" "-"', LINE.rsplit('"', 2)[0]):
        try:
            parse_log_line(bad)
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for {bad!r}")


def test_edge_no_partial_result_on_bad_status():
    bad = LINE.replace(" 200 ", " 2x0 ")
    try:
        parse_log_line(bad)
    except ValueError:
        return
    raise AssertionError("non-numeric status must raise ValueError")
