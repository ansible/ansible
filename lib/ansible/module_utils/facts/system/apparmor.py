# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Collect facts related to apparmor

from __future__ import annotations

import os

import ansible.module_utils.compat.typing as t

from ansible.module_utils.facts.collector import BaseFactCollector


class ApparmorFactCollector(BaseFactCollector):
    name = 'apparmor'
    _fact_ids = set()  # type: t.Set[str]

    def collect(self, module=None, collected_facts=None):
        facts_dict = {
            'apparmor': {
                'status': 'disabled'
            }
        }
        if os.path.exists('/sys/kernel/security/apparmor'):
            facts_dict['apparmor']['status'] = 'enabled'

        return facts_dict
