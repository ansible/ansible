# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Determine if a system is in 'fips' mode

from __future__ import annotations

import typing as t

from ansible.module_utils.facts.utils import get_file_content

from ansible.module_utils.facts.collector import BaseFactCollector


class FipsFactCollector(BaseFactCollector):
    name = 'fips'
    _fact_ids = set()  # type: t.Set[str]

    def collect(self, module=None, collected_facts=None):
        # NOTE: this is populated even if it is not set
        fips_facts = {
            'fips': False
        }
        if get_file_content('/proc/sys/crypto/fips_enabled') == '1':
            fips_facts['fips'] = True
        return fips_facts
