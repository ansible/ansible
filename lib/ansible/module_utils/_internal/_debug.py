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


def _write_stacktraces(_signum, _frame):
    """
    Signal handler to write debug stacktrace information to a file.

    Captures two types of stacktraces:
    1. Current process stacktrace using `traceback.print_stack()` with the signal frame
       (the frame parameter is crucial - without it, we'd only see the signal handler's stack)
    2. All thread stacktraces using `faulthandler.dump_traceback()`

    This combination is useful for debugging deadlocks and other concurrency issues.

    The stacktrace file location can be controlled via the ANSIBLE_STACKTRACE_DIR
    environment variable, defaulting to the system temporary directory.
    """
    now = datetime.now()
    pid = os.getpid()
    stacktrace_dir = os.environ.get('ANSIBLE_STACKTRACE_DIR', tempfile.gettempdir())
    file = pathlib.Path(stacktrace_dir) / f'ansible-{pid}.debug'

    with contextlib.suppress(Exception):
        with file.open('a') as trace_file:
            trace_file.write(f'=== {now.isoformat()} on {platform.node()} ===\n\n')

            trace_file.write(f'*** Process {pid} stacktrace\n\n')
            traceback.print_stack(f=_frame, file=trace_file)

            trace_file.write('\n\n*** Thread stacktraces\n\n')
            faulthandler.dump_traceback(file=trace_file)


def register_for_stacktrace():
    """Register a signal handler to write debug stacktrace information to a file."""
    signal.signal(signal.SIGUSR1, _write_stacktraces)
