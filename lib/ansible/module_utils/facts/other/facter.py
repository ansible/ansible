# Copyright (c) 2023 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

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
        facter_path = module.get_bin_path(
            'facter',
            opt_dirs=['/opt/puppetlabs/bin']
        )
        cfacter_path = module.get_bin_path(
            'cfacter',
            opt_dirs=['/opt/puppetlabs/bin']
        )

        # Prefer to use cfacter if available
        if cfacter_path is not None:
            facter_path = cfacter_path

        return facter_path

    def run_facter(self, module, facter_path):
        # if facter is installed, and we can use --json because
        # ruby-json is ALSO installed, include facter data in the JSON
        rc, out, err = module.run_command(facter_path + " --puppet --json")

        # for some versions of facter, --puppet returns an error if puppet is not present,
        # try again w/o it, other errors should still appear and be sent back
        if rc != 0:
            rc, out, err = module.run_command(facter_path + " --json")

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
            module.warn("Failed to parse facter facts")

        return facter_dict
