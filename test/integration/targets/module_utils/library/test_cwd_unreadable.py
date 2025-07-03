#!/usr/bin/python
from __future__ import annotations

import os

from ansible.module_utils.basic import AnsibleModule


def main():
    # This module verifies that AnsibleModule works when cwd exists but is unreadable.
    # This situation can occur when running tasks as an unprivileged user.

    try:
        cwd = os.getcwd()
    except OSError:
        # Compensate for macOS being unable to access cwd as an unprivileged user.
        # This test is a no-op in this case.
        # Testing for os.getcwd() failures is handled by the test_cwd_missing module.
        cwd = '/'
        os.chdir(cwd)

    module = AnsibleModule(argument_spec=dict())
    module.exit_json(before=cwd, after=os.getcwd())


if __name__ == '__main__':
    main()
