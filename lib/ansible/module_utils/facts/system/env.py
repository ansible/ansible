# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os

import ansible.module_utils.compat.typing as t

from ansible.module_utils.six import iteritems

from ansible.module_utils.facts.collector import BaseFactCollector


class EnvFactCollector(BaseFactCollector):
    name = 'env'
    _fact_ids = set()  # type: t.Set[str]

    def collect(self, module=None, collected_facts=None):
        env_facts = {
            'env': {}
        }

        for k, v in iteritems(os.environ):
            env_facts['env'][k] = v

        return env_facts
