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

from __future__ import annotations

import shlex
import typing as t

from ansible.module_utils.facts.utils import get_file_content

from ansible.module_utils.facts.collector import BaseFactCollector


class CmdLineFactCollector(BaseFactCollector):
    name = 'cmdline'
    _fact_ids = set()  # type: t.Set[str]

    def _get_proc_cmdline(self):
        return get_file_content('/proc/cmdline')

    def _parse_proc_cmdline(self, data):
        cmdline_dict = {}
        try:
            for piece in shlex.split(data, posix=False):
                item = piece.split('=', 1)
                if len(item) == 1:
                    cmdline_dict[item[0]] = True
                else:
                    cmdline_dict[item[0]] = item[1]
        except ValueError:
            pass

        return cmdline_dict

    def _parse_proc_cmdline_facts(self, data):
        cmdline_dict = {}
        try:
            for piece in shlex.split(data, posix=False):
                item = piece.split('=', 1)
                if len(item) == 1:
                    cmdline_dict[item[0]] = True
                else:
                    if item[0] in cmdline_dict:
                        if isinstance(cmdline_dict[item[0]], list):
                            cmdline_dict[item[0]].append(item[1])
                        else:
                            new_list = [cmdline_dict[item[0]], item[1]]
                            cmdline_dict[item[0]] = new_list
                    else:
                        cmdline_dict[item[0]] = item[1]
        except ValueError:
            pass

        return cmdline_dict

    def collect(self, module=None, collected_facts=None):
        cmdline_facts = {}

        data = self._get_proc_cmdline()

        if not data:
            return cmdline_facts

        cmdline_facts['cmdline'] = self._parse_proc_cmdline(data)
        cmdline_facts['proc_cmdline'] = self._parse_proc_cmdline_facts(data)

        return cmdline_facts
