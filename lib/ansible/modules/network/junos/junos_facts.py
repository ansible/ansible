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

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'version': '1.0',
}

DOCUMENTATION = """
---
module: junos_facts
version_added: "2.1"
author: "Nathaniel Case (@qalthos)"
short_description: Collect facts from remote devices running Junos
description:
  - Collects fact information from a remote device running the Junos
    operating system.  By default, the module will collect basic fact
    information from the device to be included with the hostvars.
    Additional fact information can be collected based on the
    configured set of arguments.
extends_documentation_fragment: junos
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset.  Possible values for this argument include
        all, default, config, and neighbors.  Can specify a list of
        values to include a larger subset.  Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected.
    required: false
    default: "!config"
  config_format:
    description:
      - The C(config_format) argument is used to specify the desired
        format of the configuration file.  Devices support three
        configuration file formats.  By default, the configuration
        from the device is returned as text.  The other option xml.
        If the xml option is chosen, the configuration file is
        returned as both xml and json.
    required: false
    default: text
    choices: ['xml', 'text']
"""

EXAMPLES = """
- name: collect default set of facts
  junos_facts:

- name: collect default set of facts and configuration
  junos_facts:
    gather_subset: config

- name: collect default set of facts and configuration in text format
  junos_facts:
    gather_subset: config
    config_format: text

- name: collect default set of facts and configuration in XML and JSON format
  junos_facts:
    gather_subset: config
    config_format: xml
"""

RETURN = """
ansible_facts:
  description: Returns the facts collect from the device
  returned: always
  type: dict
"""

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.junos import run_commands
from ansible.module_utils.junos import junos_argument_spec, check_args


class FactsBase(object):

    COMMANDS = frozenset()

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.responses = None

    def populate(self):
        self.responses = run_commands(self.module, list(self.COMMANDS))


class Default(FactsBase):

    COMMANDS = [
        'get-software-information',
    ]

    def populate(self):
        super(Default, self).populate()
        software = self.responses[0].find('.//software-information')
        self.facts['hostname'] = software.findtext('./host-name')
        self.facts['model'] = software.findtext('./product-model')
        self.facts['version'] = software.findtext('./junos-version')


FACT_SUBSETS = dict(
    default=Default,
    hadware=Hardware,
    config=Config,
    interfaces=Interfaces,
)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())


def main():
    """ Main entry point for AnsibleModule
    """
    argument_spec = dict(
        gather_subset=dict(default=['!config'], type='list'),
        config_format=dict(default='text', choices=['xml', 'text']),
    )

    argument_spec.update(junos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    gather_subset = module.params['gather_subset']

    runable_subsets = set()
    exclude_subsets = set()

    """if module.params['config'] is True:
        config_format = module.params['config_format']
        resp_config = module.config.get_config(config_format=config_format)

        if config_format in ['text']:
            facts['config'] = resp_config
        elif config_format == "xml":
            facts['config'] = xml_to_string(resp_config)
            facts['config_json'] = xml_to_json(resp_config)"""
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
            module.fail_json(msg='Subset must be one of [%s], got %s' %
                             (', '.join(VALID_SUBSETS), subset))

        if exclude:
            exclude_subsets.add(subset)
        else:
            runable_subsets.add(subset)

    if not runable_subsets:
        runable_subsets.update(VALID_SUBSETS)

    runable_subsets.difference_update(exclude_subsets)
    runable_subsets.add('default')

    facts = dict()
    facts['gather_subset'] = list(runable_subsets)

    instances = list()
    for key in runable_subsets:
        instances.append(FACT_SUBSETS[key](module))

    for inst in instances:
        inst.populate()
        facts.update(inst.facts)

    ansible_facts = dict()
    for key, value in iteritems(facts):
        key = 'ansible_net_%s' % key
        ansible_facts[key] = value

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()
