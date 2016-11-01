# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import shlex

from ansible.module_utils.facts.utils import get_file_content

from ansible.module_utils.facts.collector import BaseFactCollector


class CmdLineFactCollector(BaseFactCollector):
    name = 'cmdline'
    _fact_ids = set()

    def collect(self, module=None, collected_facts=None):
        cmdline_facts = {}

        data = get_file_content('/proc/cmdline')

        if not data:
            return cmdline_facts

        cmdline_facts['cmdline'] = {}

        try:
            for piece in shlex.split(data):
                item = piece.split('=', 1)
                if len(item) == 1:
                    cmdline_facts['cmdline'][item[0]] = True
                else:
                    cmdline_facts['cmdline'][item[0]] = item[1]
        except ValueError:
            pass

        return cmdline_facts
