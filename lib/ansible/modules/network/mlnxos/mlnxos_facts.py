#!/usr/bin/python
#
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
#
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: mlnxos_facts
version_added: "2.5"
author: "Waleed Mousa (@waleedym)"
short_description: Collect facts from remote devices running MLNXOS
description:
  - Collects a base set of device facts from a remote device that
    is running MLNXOS.  This module prepends all of the
    base network fact keys with C(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
extends_documentation_fragment: mlnxos
notes:
  - Tested against MLNX-OS 3.6
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset.  Possible values for this argument include
        all, version, module, and interfaces.  Can specify a list of
        values to include a larger subset.  Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected.
    required: false
    default: 'version'
"""

EXAMPLES = """
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
---
- name: configure provider
  set_fact:
    provider:
      username: admin
      password: admin
      host: "{{inventory_hostname}}"
      port: 22
      timeout: 30

---
# Collect all facts from the device
- mlnxos_facts:
    gather_subset: all
    provider: "{{ provider }}"

# Collect only the interfaces facts
- mlnxos_facts:
    gather_subset:
      - interfaces
    provider: "{{ provider }}"

# Do not collect version facts
- mlnxos_facts:
    gather_subset:
      - "!version"
    provider: "{{ provider }}"
"""

RETURN = """
ansible_net_gather_subset:
  description: The list of fact subsets collected from the device
  returned: always
  type: list

# version
ansible_net_version:
  description: A hash of all curently running system image information
  returned: when version is configured or when no gather_subset is provided
  type: dict

# module
ansible_net_module:
  description: A hash of all modules on the systeme with status
  returned: when module is configured
  type: dict

# interfaces
ansible_net_interfaces:
  description: A hash of all interfaces running on the system
  returned: when interfaces is configured
  type: dict
"""
import re

from ansible.module_utils.mlnxos import show_command
from ansible.module_utils.mlnxos import mlnxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.six.moves import zip
from ansible.modules.network.mlnxos import BaseMlnxosApp


class MlnxosFactsApp(BaseMlnxosApp):

    def get_runable_subset(self):

        runable_subsets = set()
        exclude_subsets = set()
        for subset in self.gather_subset:
            if subset == 'all':
                runable_subsets.update(VALID_SUBSETS)
                continue

            if subset.startswith('!'):
                subset = subset[1:]
                if subset == 'all':
                    exclude_subsets.update(VALID_SUBSETS)
                    continue
                exclude = True
            else:
                exclude = False

            if subset not in VALID_SUBSETS:
                module.fail_json(msg='Bad subset')

            if exclude:
                exclude_subsets.add(subset)
            else:
                runable_subsets.add(subset)

        if not runable_subsets:
            runable_subsets.update(VALID_SUBSETS)

        runable_subsets.difference_update(exclude_subsets)
        if(len(runable_subsets) == 0):
            runable_subsets.add('version')
        return runable_subsets

    def init_module(self):
        """ main entry point for module execution
        """
        argument_spec = dict(
            gather_subset=dict(default=['version'], type='list')
        )
        argument_spec.update(mlnxos_argument_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def run(self):
        self.init_module()
        self.gather_subset = self._module.params['gather_subset']
        runable_subsets = self.get_runable_subset()
        facts = dict()
        facts['gather_subset'] = list(runable_subsets)

        instances = list()
        for key in runable_subsets:
            instances.append(FACT_SUBSETS[key](self._module))

        for inst in instances:
            inst.populate()
            facts.update(inst.facts)

        ansible_facts = dict()
        for key, value in iteritems(facts):
            key = 'ansible_net_%s' % key
            ansible_facts[key] = value

        warnings = list()
        check_args(self._module, warnings)
        self._module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


class FactsBase(object):

    COMMANDS = ['']

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.responses = None

    def populate(self):
        self.responses = show_command(
            self.module, self.COMMANDS)


class Version(FactsBase):

    COMMANDS = ['version']

    def populate(self):
        super(Version, self).populate()
        data = self.responses[0]
        if data:
            self.facts['version'] = data


class Module(FactsBase):

    COMMANDS = ['module']

    def populate(self):
        super(Module, self).populate()
        data = self.responses[0]
        if data:
            self.facts['modules'] = data


class Interfaces(FactsBase):

    COMMANDS = ['interfaces ethernet']

    def populate(self):
        super(Interfaces, self).populate()

        data = self.responses[0]
        if data:
            self.facts['Interfaces'] = self.populate_interfaces(data)

    def populate_interfaces(self, interfaces):
        intf = dict()
        for i in range(0, len(interfaces)):
            temp_dict = dict()
            temp_dict.update({"MAC Address": interfaces[i]["Mac address"]})
            temp_dict.update({"Actual Speed": interfaces[i]["Actual speed"]})
            temp_dict.update({"MTU": interfaces[i]["MTU"]})
            temp_dict.update({"Admin State": interfaces[i]["Admin state"]})
            temp_dict.update({"Operational State":
                              interfaces[i]["Operational state"]})
            temp_dict.update({"Interface name": interfaces[i]["header"]})

            intf.update({interfaces[i]["header"]: temp_dict})
        return intf


FACT_SUBSETS = dict(
    version=Version,
    module=Module,
    interfaces=Interfaces
)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())

if __name__ == '__main__':
    MlnxosFactsApp.main()
