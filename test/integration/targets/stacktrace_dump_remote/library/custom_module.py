#!/usr/bin/python

from __future__ import annotations

import os
import signal
import tempfile

from ..module_utils.basic import AnsibleModule  # pylint: disable=relative-beyond-top-level


def main():
    module = AnsibleModule(
        argument_spec=dict()
    )

    # Get PID of the current process (AnsiballZ)
    process_pid = os.getpid()

    # Send SIGUSR1 to the current process to trigger a stacktrace dump
    os.kill(process_pid, signal.SIGUSR1)

    # Exit with the tempdir and AnsiballZ PID
    module.exit_json(tempdir=tempfile.gettempdir(), process_pid=process_pid)


if __name__ == '__main__':
    main()
