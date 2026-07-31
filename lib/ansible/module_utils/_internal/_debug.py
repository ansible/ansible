# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

import contextlib
import faulthandler
import os
import pathlib
import platform
import signal
import tempfile
import traceback

from datetime import datetime

from ansible.module_utils._internal._logging import log_to_system


def _write_stacktraces(stacktrace_dir: str | None = None):
    """
    Signal handler to write debug stacktrace information to a file located in `stacktrace_dir` or the system's temp directory.

    In theory, the system temp directory should never be needed since the current practice is to use either
    $ANSIBLE_HOME on the controller and `remote_tmp` on the target as the location for these files. Problems
    accessing those locations should surface long before here, but this will remain a fallback just in case.
    """

    def inner(_signum, _frame):
        now = datetime.now()
        pid = os.getpid()
        trace_dir = stacktrace_dir if stacktrace_dir is not None else tempfile.gettempdir()
        file = pathlib.Path(trace_dir) / f'ansible-{pid}.debug'

        with contextlib.suppress(Exception):
            # Drop a breadcrumb to help identify where the stacktrace was saved.
            log_to_system(f"Writing debug stacktrace to {file}", module_name="stacktrace", syslog_facility="LOG_USER")

            with file.open('a') as trace_file:
                trace_file.write(f'=== {now.isoformat()} on {platform.node()} ===\n\n')

                # The `faulthandler` output will also contain the main process stacktrace (as current thread),
                # but it won't be as detailed as the `traceback` output.
                trace_file.write(f'*** Process {pid} stacktrace\n\n')
                traceback.print_stack(f=_frame, file=trace_file)

                # Let `faulthandler` handle the threads since it can handle those more efficiently/correctly.
                trace_file.write('\n\n*** Thread stacktraces\n\n')
                faulthandler.dump_traceback(file=trace_file)

    return inner


def register_for_stacktrace(stacktrace_dir: str | None = None):
    """Register a signal handler to write debug stacktrace information to a file."""
    signal.signal(signal.SIGUSR1, _write_stacktraces(stacktrace_dir))
