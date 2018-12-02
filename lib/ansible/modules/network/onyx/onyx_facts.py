#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: onyx_facts
version_added: "2.5"
author: "Waleed Mousa (@waleedym), Samer Deeb (@samerd)"
short_description: Collect facts from Mellanox ONYX network devices
description:
  - Collects a base set of device facts from a ONYX Mellanox network devices
    This module prepends all of the base network fact keys with
    C(ansible_net_<fact>).  The facts module will always collect a base set of
    facts from the device and can enable or disable collection of additional
    facts.
notes:
  - Tested against ONYX 3.6
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
    default: version
"""

EXAMPLES = """
---
- name: Collect all facts from the device
  onyx_facts:
    gather_subset: all
- name: Collect only the interfaces facts
  onyx_facts:
    gather_subset:
      - interfaces
- name: Do not collect version facts
  onyx_facts:
    gather_subset:
      - "!version"
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
# modules
ansible_net_modules:
  description: A hash of all modules on the systeme with status
  returned: when modules is configured
  type: dict
# interfaces
ansible_net_interfaces:
  description: A hash of all interfaces running on the system
  returned: when interfaces is configured
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems

from ansible.module_utils.network.onyx.onyx import BaseOnyxModule
from ansible.module_utils.network.onyx.onyx import show_cmd


class OnyxFactsModule(BaseOnyxModule):

    def get_runable_subset(self, gather_subset):
        runable_subsets = set()
        exclude_subsets = set()
        for subset in gather_subset:
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
                self._module.fail_json(msg='Bad subset')

            if exclude:
                exclude_subsets.add(subset)
            else:
                runable_subsets.add(subset)

        if not runable_subsets:
            runable_subsets.update(VALID_SUBSETS)

        runable_subsets.difference_update(exclude_subsets)
        if not runable_subsets:
            runable_subsets.add('version')
        return runable_subsets

    def init_module(self):
        """ module intialization
        """
        argument_spec = dict(
            gather_subset=dict(default=['version'], type='list')
        )
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def run(self):
        self.init_module()
        gather_subset = self._module.params['gather_subset']
        runable_subsets = self.get_runable_subset(gather_subset)
        facts = dict()
        facts['gather_subset'] = list(runable_subsets)

        instances = list()
        for key in runable_subsets:
            facter_cls = FACT_SUBSETS[key]
            instances.append(facter_cls(self._module))

        for inst in instances:
            inst.populate()
            facts.update(inst.facts)

        ansible_facts = dict()
        for key, value in iteritems(facts):
            key = 'ansible_net_%s' % key
            ansible_facts[key] = value
        self._module.exit_json(ansible_facts=ansible_facts)


class FactsBase(object):

    COMMANDS = ['']

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.responses = None

    def _show_cmd(self, cmd):
        return show_cmd(self.module, cmd, json_fmt=True)

    def populate(self):
        self.responses = []
        for cmd in self.COMMANDS:
            self.responses.append(self._show_cmd(cmd))


class Version(FactsBase):

    COMMANDS = ['show version']

    def populate(self):
        super(Version, self).populate()
        data = self.responses[0]
        if data:
            self.facts['version'] = data


class Module(FactsBase):

    COMMANDS = ['show module']

    def populate(self):
        super(Module, self).populate()
        data = self.responses[0]
        if data:
            self.facts['modules'] = data


class Interfaces(FactsBase):

    COMMANDS = ['show version', 'show interfaces ethernet']

    def populate(self):
        super(Interfaces, self).populate()

        version_data = self.responses[0]
        os_version = version_data['Product release']
        data = self.responses[1]

        if data:
            self.facts['interfaces'] = self.populate_interfaces(data, os_version)

    def extractIfData(self, interface_data):
        return {"MAC Address": interface_data["Mac address"],
                "Actual Speed": interface_data["Actual speed"],
                "MTU": interface_data["MTU"],
                "Admin State": interface_data["Admin state"],
                "Operational State": interface_data["Operational state"]}

    def populate_interfaces(self, interfaces, os_version):
        interfaces_dict = dict()
        for if_data in interfaces:
            if_dict = dict()
            if os_version >= BaseOnyxModule.ONYX_API_VERSION:
                for if_name, interface_data in iteritems(if_data):
                    interface_data = interface_data[0]
                    if_dict = self.extractIfData(interface_data)
                    if_name = if_dict["Interface Name"] = if_name

            else:
                if_dict = self.extractIfData(if_data)
                if_name = if_dict["Interface Name"] = if_data["header"]
            interfaces_dict[if_name] = if_dict
        return interfaces_dict


FACT_SUBSETS = dict(
    version=Version,
    modules=Module,
    interfaces=Interfaces
)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())


def main():
    """ main entry point for module execution
    """
    OnyxFactsModule.main()


if __name__ == '__main__':
    main()
