# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# This file will be overwridden by ansible.executor.module_common during
# module building. This specific version will only be used by controller imports

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.release import __version__, __author__, __codename__
from ansible.utils.display import Display

# When removing this file, also delete the corresponding contents
# from py_module_cache lib/ansible/executor/module_common.py
Display().deprecated(
    "`ansible.module_utils.ansible_release` is deprecated. "
    "Please make use of `ansible.release` for controller code.",
    version="2.16"
)
