# (C) 2017 Red Hat Inc.
# Copyright (C) 2019 APCON.
#
# GNU General Public License v3.0+
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Contains terminal Plugin methods for apconos Config Module
# Apcon Networking
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import re

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text, to_bytes
from ansible.plugins.terminal import TerminalBase


class TerminalModule(TerminalBase):

    terminal_stdout_re = [
        re.compile(br'>>\ |#\ |\$\ ')
    ]

    terminal_stderr_re = [
        re.compile(br"connection timed out", re.I),
    ]
