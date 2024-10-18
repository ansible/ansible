# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Collect facts related to systems 'capabilities' via capsh

from __future__ import annotations

import ansible.module_utils.compat.typing as t

from ansible.module_utils.facts.collector import BaseFactCollector


class SystemCapabilitiesFactCollector(BaseFactCollector):
    name = 'caps'
    _fact_ids = set(['system_capabilities',
                     'system_capabilities_enforced'])  # type: t.Set[str]

    def get_caps_data(self, module=None):
        rc, out, err = (-1, '', '')
        capsh_path = module.get_bin_path('capsh')
        if capsh_path is None:
            return rc, out, err

        try:
            rc, out, err = module.run_command(
                [capsh_path, "--print"],
                errors='surrogate_then_replace',
                handle_exceptions=False
            )
        except (IOError, OSError) as e:
            module.warn('Could not query system capabilities: %s' % str(e))

        return rc, out, err

    def parse_caps_data(self, caps_data=None):
        enforced = 'NA'
        enforced_caps = []
        if caps_data is None:
            return enforced, enforced_caps

        for line in caps_data.splitlines():
            if len(line) < 1:
                continue
            if line.startswith('Current:'):
                if line.split(':')[1].strip() == '=ep':
                    enforced = 'False'
                else:
                    enforced = 'True'
                    enforced_caps = [i.strip() for i in line.split('=')[1].split(',')]

        return enforced, enforced_caps

    def collect(self, module=None, collected_facts=None):
        facts_dict = {
            'system_capabilities_enforced': 'N/A',
            'system_capabilities': 'N/A'
        }
        if module is None:
            return facts_dict

        rc, out, dummy = self.get_caps_data(module=module)

        if rc != 0:
            return facts_dict

        enforced, enforced_caps = self.parse_caps_data(caps_data=out)
        facts_dict['system_capabilities_enforced'] = enforced
        facts_dict['system_capabilities'] = enforced_caps
        return facts_dict
