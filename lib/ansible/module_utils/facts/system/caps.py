# Collect facts related to systems 'capabilities' via capsh
#
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


from ansible.module_utils.facts.collector import BaseFactCollector


class SystemCapabilitiesFactCollector(BaseFactCollector):
    name = 'caps'
    _fact_ids = set(['system_capabilities',
                     'system_capabilities_enforced'])

    def collect(self, module=None, collected_facts=None):
        facts_dict = {}
        if not module:
            return facts_dict

        capsh_path = module.get_bin_path('capsh')
        # NOTE: early exit 'if not crash_path' and unindent rest of method -akl
        if capsh_path:
            # NOTE: -> get_caps_data()/parse_caps_data() for easier mocking -akl
            rc, out, err = module.run_command([capsh_path, "--print"], errors='surrogate_then_replace')
            enforced_caps = []
            enforced = 'NA'
            for line in out.splitlines():
                if len(line) < 1:
                    continue
                if line.startswith('Current:'):
                    if line.split(':')[1].strip() == '=ep':
                        enforced = 'False'
                    else:
                        enforced = 'True'
                        enforced_caps = [i.strip() for i in line.split('=')[1].split(',')]

            facts_dict['system_capabilities_enforced'] = enforced
            facts_dict['system_capabilities'] = enforced_caps

        return facts_dict
