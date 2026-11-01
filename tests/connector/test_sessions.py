# checks the one-active-session rule of pod-contract.md section 2

import sys

from GitHub_Connector import course


def test_one_session_at_a_time(monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr(course, "_clock", lambda: clock[0])
    sessions = course.Sessions()

    assert sessions.open("a") is None
    assert sessions.open("a") == "session a already exists"
    # a new id waits while a is active and its report is unread
    assert sessions.open("b") == "another test session is active"

    # reading a's report frees the system for the next setup
    first = sessions.report("a")
    assert sessions.open("b") is None
    # a's report stays readable, frozen when b took over
    assert sessions.report("a") == first

    # an unread session is released 720 s after its setup
    clock[0] += 719
    assert sessions.open("c") == "another test session is active"
    clock[0] += 1
    assert sessions.open("c") is None


def test_the_line_callback_survives_interpreter_shutdown(monkeypatch):
    # shutdown clears module globals, so sys is None when a last line event fires
    disable = sys.monitoring.DISABLE
    monitor = course.LineMonitor(course.PACKAGE_DIR)
    monkeypatch.setattr(course, "sys", None)

    assert monitor._on_line(test_the_line_callback_survives_interpreter_shutdown.__code__, 1) is disable
