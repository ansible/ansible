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

import socket

from ansible.module_utils.facts.collector import BaseFactCollector


class FQDNFactCollector(BaseFactCollector):
    name = 'fqdn'
    _fact_ids = {
        'domain',
        'fqdn',
    }

    def collect(self, module=None, collected_facts=None):
        fqdn_facts = {}

        # NOTE: socket.getfqdn() calls gethostbyaddr(socket.gethostname()),
        # which can be slow to return if the name does not resolve correctly.
        # On macOS if the name ends with .local then "local network privacy"
        # policies may be applied.
        fqdn_facts['fqdn'] = socket.getfqdn()
        fqdn_facts['domain'] = '.'.join(fqdn_facts['fqdn'].split('.')[1:])
        return fqdn_facts
