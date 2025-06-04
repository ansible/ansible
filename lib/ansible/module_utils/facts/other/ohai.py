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

import json
import typing as t

from ansible.module_utils.facts.namespace import PrefixFactNamespace

from ansible.module_utils.facts.collector import BaseFactCollector


class OhaiFactCollector(BaseFactCollector):
    """This is a subclass of Facts for including information gathered from Ohai."""
    name = 'ohai'
    _fact_ids = set()  # type: t.Set[str]

    def __init__(self, collectors=None, namespace=None):
        namespace = PrefixFactNamespace(namespace_name='ohai',
                                        prefix='ohai_')
        super(OhaiFactCollector, self).__init__(collectors=collectors,
                                                namespace=namespace)

    def find_ohai(self, module):
        return module.get_bin_path(
            'ohai'
        )

    def run_ohai(self, module, ohai_path):
        rc, out, err = module.run_command(ohai_path)
        return rc, out, err

    def get_ohai_output(self, module):
        ohai_path = self.find_ohai(module)
        if not ohai_path:
            return None

        rc, out, err = self.run_ohai(module, ohai_path)
        if rc != 0:
            return None

        return out

    def collect(self, module=None, collected_facts=None):
        ohai_facts = {}
        if not module:
            return ohai_facts

        ohai_output = self.get_ohai_output(module)

        if ohai_output is None:
            return ohai_facts

        try:
            ohai_facts = json.loads(ohai_output)
        except Exception:
            module.warn("Failed to gather ohai facts")

        return ohai_facts
