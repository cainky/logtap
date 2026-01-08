"""Unit tests for logtap.core.parsers module."""

import pytest

from logtap.core.parsers import (
    LogLevel,
    ParsedLogEntry,
    SyslogParser,
    JsonLogParser,
    NginxParser,
    ApacheParser,
    AutoParser,
    detect_format,
)


class TestLogLevel:
    """Tests for LogLevel enum."""

    def test_from_string_standard_names(self):
        assert LogLevel.from_string("error") == LogLevel.ERROR
        assert LogLevel.from_string("ERROR") == LogLevel.ERROR
        assert LogLevel.from_string("warn") == LogLevel.WARNING
        assert LogLevel.from_string("warning") == LogLevel.WARNING
        assert LogLevel.from_string("info") == LogLevel.INFO
        assert LogLevel.from_string("debug") == LogLevel.DEBUG

    def test_from_string_numeric(self):
        assert LogLevel.from_string("0") == LogLevel.EMERGENCY
        assert LogLevel.from_string("3") == LogLevel.ERROR
        assert LogLevel.from_string("7") == LogLevel.DEBUG

    def test_severity_ordering(self):
        assert LogLevel.EMERGENCY.severity < LogLevel.ERROR.severity
        assert LogLevel.ERROR.severity < LogLevel.WARNING.severity
        assert LogLevel.WARNING.severity < LogLevel.INFO.severity
        assert LogLevel.INFO.severity < LogLevel.DEBUG.severity


class TestSyslogParser:
    """Tests for SyslogParser."""

    def test_can_parse_valid(self):
        parser = SyslogParser()
        assert parser.can_parse("Jan  8 10:23:45 server sshd[1234]: Accepted publickey")
        assert parser.can_parse("Dec 31 23:59:59 host process: message")

    def test_can_parse_invalid(self):
        parser = SyslogParser()
        assert not parser.can_parse('{"level": "error"}')
        assert not parser.can_parse("192.168.1.1 - - [08/Jan/2024:10:23:45 +0000]")

    def test_parse_with_pid(self):
        parser = SyslogParser()
        entry = parser.parse("Jan  8 10:23:45 server sshd[1234]: Connection closed")

        assert entry.message == "Connection closed"
        assert entry.metadata["hostname"] == "server"
        assert entry.metadata["process"] == "sshd"
        assert entry.metadata["pid"] == "1234"
        assert entry.source == "server/sshd"

    def test_parse_error_detection(self):
        parser = SyslogParser()
        entry = parser.parse("Jan  8 10:23:45 server app[1]: Error: connection failed")
        assert entry.level == LogLevel.ERROR

    def test_parse_warning_detection(self):
        parser = SyslogParser()
        entry = parser.parse("Jan  8 10:23:45 server app[1]: Warning: disk space low")
        assert entry.level == LogLevel.WARNING


class TestJsonLogParser:
    """Tests for JsonLogParser."""

    def test_can_parse_valid_json(self):
        parser = JsonLogParser()
        assert parser.can_parse('{"message": "test"}')
        assert parser.can_parse('{"level": "error", "msg": "failed"}')

    def test_can_parse_invalid(self):
        parser = JsonLogParser()
        assert not parser.can_parse("Jan  8 10:23:45 server")
        assert not parser.can_parse("not json at all")
        assert not parser.can_parse("[array, not, object]")

    def test_parse_extracts_message(self):
        parser = JsonLogParser()
        entry = parser.parse('{"message": "test message", "level": "info"}')
        assert entry.message == "test message"
        assert entry.level == LogLevel.INFO

    def test_parse_extracts_level(self):
        parser = JsonLogParser()
        entry = parser.parse('{"msg": "error occurred", "severity": "ERROR"}')
        assert entry.level == LogLevel.ERROR

    def test_parse_metadata(self):
        parser = JsonLogParser()
        entry = parser.parse('{"message": "test", "custom_field": "value"}')
        assert entry.metadata["custom_field"] == "value"


class TestNginxParser:
    """Tests for NginxParser."""

    def test_can_parse_valid(self):
        parser = NginxParser()
        line = '192.168.1.1 - - [08/Jan/2024:10:23:45 +0000] "GET /api HTTP/1.1" 200 45 "-" "curl"'
        assert parser.can_parse(line)

    def test_parse_extracts_fields(self):
        parser = NginxParser()
        line = '192.168.1.1 - frank [08/Jan/2024:10:23:45 +0000] "GET /api/health HTTP/1.1" 200 45 "-" "curl/7.68.0"'
        entry = parser.parse(line)

        assert entry.metadata["remote_addr"] == "192.168.1.1"
        assert entry.metadata["method"] == "GET"
        assert entry.metadata["path"] == "/api/health"
        assert entry.metadata["status"] == 200
        assert entry.metadata["user_agent"] == "curl/7.68.0"

    def test_parse_status_to_level(self):
        parser = NginxParser()

        # 200 -> INFO
        entry = parser.parse('1.1.1.1 - - [08/Jan/2024:10:23:45 +0000] "GET / HTTP/1.1" 200 0 "-" "-"')
        assert entry.level == LogLevel.INFO

        # 404 -> WARNING
        entry = parser.parse('1.1.1.1 - - [08/Jan/2024:10:23:45 +0000] "GET / HTTP/1.1" 404 0 "-" "-"')
        assert entry.level == LogLevel.WARNING

        # 500 -> ERROR
        entry = parser.parse('1.1.1.1 - - [08/Jan/2024:10:23:45 +0000] "GET / HTTP/1.1" 500 0 "-" "-"')
        assert entry.level == LogLevel.ERROR


class TestAutoParser:
    """Tests for AutoParser."""

    def test_auto_detect_json(self):
        parser = AutoParser()
        entry = parser.parse('{"message": "test", "level": "error"}')
        assert entry.message == "test"
        assert "auto:json" in parser.name

    def test_auto_detect_syslog(self):
        parser = AutoParser()
        entry = parser.parse("Jan  8 10:23:45 server process[1]: test message")
        assert entry.message == "test message"
        assert "auto:syslog" in parser.name

    def test_parse_many_detects_format(self):
        parser = AutoParser()
        lines = [
            "Jan  8 10:23:45 server process[1]: line 1",
            "Jan  8 10:23:46 server process[1]: line 2",
            "Jan  8 10:23:47 server process[1]: line 3",
        ]
        entries = parser.parse_many(lines)
        assert len(entries) == 3
        assert all(e.metadata.get("process") == "process" for e in entries)


class TestDetectFormat:
    """Tests for detect_format function."""

    def test_detect_json_format(self):
        lines = ['{"msg": "line 1"}', '{"msg": "line 2"}', '{"msg": "line 3"}']
        parser = detect_format(lines)
        assert parser is not None
        assert parser.name == "json"

    def test_detect_syslog_format(self):
        lines = [
            "Jan  8 10:23:45 server process[1]: line 1",
            "Jan  8 10:23:46 server process[1]: line 2",
        ]
        parser = detect_format(lines)
        assert parser is not None
        assert parser.name == "syslog"

    def test_detect_empty_returns_none(self):
        assert detect_format([]) is None
