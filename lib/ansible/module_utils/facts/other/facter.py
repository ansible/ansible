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

import json

import ansible.module_utils.compat.typing as t

from ansible.module_utils.facts.namespace import PrefixFactNamespace

from ansible.module_utils.facts.collector import BaseFactCollector


class FacterFactCollector(BaseFactCollector):
    name = 'facter'
    _fact_ids = set(['facter'])  # type: t.Set[str]

    def __init__(self, collectors=None, namespace=None):
        namespace = PrefixFactNamespace(namespace_name='facter',
                                        prefix='facter_')
        super(FacterFactCollector, self).__init__(collectors=collectors,
                                                  namespace=namespace)

    def find_facter(self, module):
        facter_path = module.get_bin_path('facter', opt_dirs=['/opt/puppetlabs/bin'])
        cfacter_path = module.get_bin_path('cfacter', opt_dirs=['/opt/puppetlabs/bin'])

        # Prefer to use cfacter if available
        if cfacter_path is not None:
            facter_path = cfacter_path

        return facter_path

    def run_facter(self, module, facter_path):
        # if facter is installed, and we can use --json because
        # ruby-json is ALSO installed, include facter data in the JSON
        rc, out, err = module.run_command(facter_path + " --puppet --json")
        return rc, out, err

    def get_facter_output(self, module):
        facter_path = self.find_facter(module)
        if not facter_path:
            return None

        rc, out, err = self.run_facter(module, facter_path)

        if rc != 0:
            return None

        return out

    def collect(self, module=None, collected_facts=None):
        # Note that this mirrors previous facter behavior, where there isnt
        # a 'ansible_facter' key in the main fact dict, but instead, 'facter_whatever'
        # items are added to the main dict.
        facter_dict = {}

        if not module:
            return facter_dict

        facter_output = self.get_facter_output(module)

        # TODO: if we fail, should we add a empty facter key or nothing?
        if facter_output is None:
            return facter_dict

        try:
            facter_dict = json.loads(facter_output)
        except Exception:
            # FIXME: maybe raise a FactCollectorError with some info attrs?
            pass

        return facter_dict
