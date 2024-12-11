# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

import os as _os
import pathlib as _pathlib
import platform as _platform
import signal as _signal
import sys as _sys
import tempfile as _tempfile
import threading as _threading
import traceback as _traceback
from datetime import datetime as _datetime


def _writer(msg):
    now = _datetime.now()
    pid = _os.getpid()
    file = _pathlib.Path(_tempfile.gettempdir()) / f'ansible-{pid}.debug'

    with file.open('a') as f:
        f.write(f'=== {now.isoformat()} on {_platform.node()} ===\n')
        f.write(msg)
        f.write('\n')


def _handle_trap(writer):
    def inner(_signum, _frame):
        frames = _sys._current_frames()
        for thread in _threading.enumerate():
            frame = frames[thread.ident]
            stack = ''.join(_traceback.format_stack(frame)[:-1])
            writer(f'{thread.name}:\n{stack}')

    return inner


def register(writer=_writer):
    _signal.signal(_signal.SIGTRAP, _handle_trap(writer))
