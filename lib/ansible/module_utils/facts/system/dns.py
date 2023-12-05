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

import ansible.module_utils.compat.typing as t

from ansible.module_utils.facts.utils import get_file_content

from ansible.module_utils.facts.collector import BaseFactCollector


class DnsFactCollector(BaseFactCollector):
    name = 'dns'
    _fact_ids = set()  # type: t.Set[str]

    def collect(self, module=None, collected_facts=None):
        dns_facts = {}

        # TODO: flatten
        dns_facts['dns'] = {}

        for line in get_file_content('/etc/resolv.conf', '').splitlines():
            if line.startswith('#') or line.startswith(';') or line.strip() == '':
                continue
            tokens = line.split()
            if len(tokens) == 0:
                continue
            if tokens[0] == 'nameserver':
                if 'nameservers' not in dns_facts['dns']:
                    dns_facts['dns']['nameservers'] = []
                for nameserver in tokens[1:]:
                    dns_facts['dns']['nameservers'].append(nameserver)
            elif tokens[0] == 'domain':
                if len(tokens) > 1:
                    dns_facts['dns']['domain'] = tokens[1]
            elif tokens[0] == 'search':
                dns_facts['dns']['search'] = []
                for suffix in tokens[1:]:
                    dns_facts['dns']['search'].append(suffix)
            elif tokens[0] == 'sortlist':
                dns_facts['dns']['sortlist'] = []
                for address in tokens[1:]:
                    dns_facts['dns']['sortlist'].append(address)
            elif tokens[0] == 'options':
                dns_facts['dns']['options'] = {}
                if len(tokens) > 1:
                    for option in tokens[1:]:
                        option_tokens = option.split(':', 1)
                        if len(option_tokens) == 0:
                            continue
                        val = len(option_tokens) == 2 and option_tokens[1] or True
                        dns_facts['dns']['options'][option_tokens[0]] = val

        return dns_facts
