# (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

import ansible.module_utils.compat.typing as t

from ansible.module_utils.facts.collector import BaseFactCollector


class LoadAvgFactCollector(BaseFactCollector):
    name = 'loadavg'
    _fact_ids = set()  # type: t.Set[str]

    def collect(self, module=None, collected_facts=None):
        facts = {}
        try:
            # (0.58, 0.82, 0.98)
            loadavg = os.getloadavg()
            facts['loadavg'] = {
                '1m': loadavg[0],
                '5m': loadavg[1],
                '15m': loadavg[2]
            }
        except OSError:
            pass

        return facts
