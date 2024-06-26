"""Run each test in its own fork. PYTEST_DONT_REWRITE"""
# MIT License (see licenses/MIT-license.txt or https://opensource.org/licenses/MIT)
# Based on code originally from:
# https://github.com/pytest-dev/pytest-forked
# https://github.com/pytest-dev/py
# TIP: Disable pytest-xdist when debugging internal errors in this plugin.
from __future__ import annotations

import os
import pickle
import tempfile
import warnings

from pytest import Item, hookimpl, TestReport

from _pytest.runner import runtestprotocol


@hookimpl(tryfirst=True)
def pytest_runtest_protocol(item, nextitem):  # type: (Item, Item | None) -> object | None
    """Entry point for enabling this plugin."""
    # This is needed because pytest-xdist creates an OS thread (using execnet).
    # See: https://github.com/pytest-dev/execnet/blob/d6aa1a56773c2e887515d63e50b1d08338cb78a7/execnet/gateway_base.py#L51
    warnings.filterwarnings("ignore", "^This process .* is multi-threaded, use of .* may lead to deadlocks in the child.$", DeprecationWarning)

    item_hook = item.ihook
    item_hook.pytest_runtest_logstart(nodeid=item.nodeid, location=item.location)

    reports = run_item(item, nextitem)

    for report in reports:
        item_hook.pytest_runtest_logreport(report=report)

    item_hook.pytest_runtest_logfinish(nodeid=item.nodeid, location=item.location)

    return True


def run_item(item, nextitem):  # type: (Item, Item | None) -> list[TestReport]
    """Run the item in a child process and return a list of reports."""
    with tempfile.NamedTemporaryFile() as temp_file:
        pid = os.fork()

        if not pid:
            temp_file.delete = False
            run_child(item, nextitem, temp_file.name)

        return run_parent(item, pid, temp_file.name)


def run_child(item, nextitem, result_path):  # type: (Item, Item | None, str) -> None
    """Run the item, record the result and exit. Called in the child process."""
    with warnings.catch_warnings(record=True) as captured_warnings:
        reports = runtestprotocol(item, nextitem=nextitem, log=False)

    with open(result_path, "wb") as result_file:
        pickle.dump((reports, captured_warnings), result_file)

    os._exit(0)  # noqa


def run_parent(item, pid, result_path):  # type: (Item, int, str) -> list[TestReport]
    """Wait for the child process to exit and return the test reports. Called in the parent process."""
    exit_code = waitstatus_to_exitcode(os.waitpid(pid, 0)[1])

    if exit_code:
        reason = "Test CRASHED with exit code {}.".format(exit_code)
        report = TestReport(item.nodeid, item.location, {x: 1 for x in item.keywords}, "failed", reason, "call", user_properties=item.user_properties)

        if item.get_closest_marker("xfail"):
            report.outcome = "skipped"
            report.wasxfail = reason

        reports = [report]
    else:
        with open(result_path, "rb") as result_file:
            reports, captured_warnings = pickle.load(result_file)  # type: list[TestReport], list[warnings.WarningMessage]

        for warning in captured_warnings:
            warnings.warn_explicit(warning.message, warning.category, warning.filename, warning.lineno)

    return reports


def waitstatus_to_exitcode(status):  # type: (int) -> int
    """Convert a wait status to an exit code."""
    # This function was added in Python 3.9.
    # See: https://docs.python.org/3/library/os.html#os.waitstatus_to_exitcode

    if os.WIFEXITED(status):
        return os.WEXITSTATUS(status)

    if os.WIFSIGNALED(status):
        return -os.WTERMSIG(status)

    raise ValueError(status)
