"""Constants used by ansible-test. Imports should not be used in this file."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# Setting a low soft RLIMIT_NOFILE value will improve the performance of subprocess.Popen on Python 2.x when close_fds=True.
# This will affect all Python subprocesses. It will also affect the current Python process if set before subprocess is imported for the first time.
SOFT_RLIMIT_NOFILE = 1024

# File used to track the ansible-test test execution timeout.
TIMEOUT_PATH = '.ansible-test-timeout.json'
