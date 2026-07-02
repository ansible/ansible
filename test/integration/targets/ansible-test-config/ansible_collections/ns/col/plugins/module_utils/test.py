from __future__ import annotations

import sys
import os


def version_to_str(value):
    return '.'.join(str(v) for v in value)


controller_min_python_version = tuple(int(v) for v in os.environ['ANSIBLE_CONTROLLER_MIN_PYTHON_VERSION'].split('.'))
current_python_version = sys.version_info[:2]

if current_python_version < controller_min_python_version:
    raise Exception('Current Python version %s is lower than the minimum controller Python version of %s. '
                    'Did the collection config get ignored?' % (version_to_str(current_python_version), version_to_str(controller_min_python_version)))
