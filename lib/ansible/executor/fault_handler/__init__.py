#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Fault handler implementation for Ansible processes."""

from __future__ import annotations

__all__ = ['setup_fault_handler']

import os
import signal
import faulthandler
import tempfile
import atexit
from pathlib import Path
from ansible.utils.display import Display

display = Display()

def setup_fault_handler(worker_id=None):
    """Register fault handler for stack trace dumps on SIGTRAP signal.

    Args:
        worker_id: Optional identifier for worker processes
    """
    pid = os.getpid()
    filename = f"ansible-worker-{worker_id}-{pid}.stack" if worker_id else f"ansible-{pid}.stack"
    stack_file_path = Path(tempfile.gettempdir()) / filename

    try:
        with open(stack_file_path, 'w', encoding='utf-8') as stack_file:
            def cleanup():
                try:
                    stack_file_path.unlink()
                except OSError as exc:
                    raise OSError("Failed to remove stack trace file") from exc

            def handle_trap(signum: int, frame: object) -> None:  # pylint: disable=unused-argument
                """Handle SIGTRAP signal by dumping stack trace.

                Args:
                    signum: Signal number (unused but required by signal handler interface)
                    frame: Current stack frame (unused but required by signal handler interface)
                """
                faulthandler.dump_traceback(stack_file)
                stack_file.flush()

            atexit.register(cleanup)
            signal.signal(signal.SIGTRAP, handle_trap)
            faulthandler.register(signal.SIGTRAP, file=stack_file, chain=True)
            display.vvv(f"Registered faulthandler for PID {pid}, traces -> {stack_file_path}")

    except (OSError, IOError) as e:
        display.warning(f"Failed to setup faulthandler: {str(e)}")
