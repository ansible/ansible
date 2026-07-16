#!/usr/bin/env python
from __future__ import annotations

import io
import os
import sys

import pexpect


env_vars = {
    'ANSIBLE_NOCOLOR': 'True',
    'ANSIBLE_RETRY_FILES_ENABLED': 'False',
}

env = os.environ.copy()
env.update(env_vars)

with io.BytesIO() as logfile:
    step_test = pexpect.spawn(
        'ansible-playbook',
        args=[sys.argv[1], '--step'],
        timeout=10,
        env=env
    )

    step_test.logfile = logfile

    step_test.expect_exact('Perform task: TASK: ping on localhost (N)o/(y)es/(c)ontinue: ')
    step_test.send('\r')
    step_test.expect(pexpect.EOF)
    step_test.close()

    assert 'PLAY RECAP' in str(logfile.getvalue())
