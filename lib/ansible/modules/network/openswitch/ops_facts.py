#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: ops_facts
version_added: "2.1"
author: "Peter Sprygada (@privateip)"
short_description: Collect device specific facts from OpenSwitch
description:
  - Collects facts from devices running the OpenSwitch operating
    system.  Fact collection is supported over both Cli and Rest
    transports.  This module prepends all of the base network fact keys
    with C(ansible_net_<fact>).  The facts module will always collect a
    base set of facts from the device and can enable or disable
    collection of additional facts.
  - The facts collected from pre Ansible 2.2 are still available and
    are collected for backwards compatibility; however, these facts
    should be considered deprecated and will be removed in a future
    release.
extends_documentation_fragment: openswitch
options:
  config:
    description:
      - When enabled, this argument will collect the current
        running configuration from the remote device.  If the
        C(transport=rest) then the collected configuration will
        be the full system configuration.
    required: false
    choices:
        - true
        - false
    default: false
  endpoints:
    description:
      - Accepts a list of endpoints to retrieve from the remote
        device using the REST API.  The endpoints should be valid
        endpoints available on the device.  This argument is only
        valid when the C(transport=rest).
    required: false
    default: null
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset.  Possible values for this argument include
        all, hardware, config, legacy, and interfaces.  Can specify a
        list of values to include a larger subset.  Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected.
    required: false
    default: '!config'
    version_added: "2.2"
"""

EXAMPLES = """
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
---
vars:
  cli:
    host: "{{ inventory_hostname }}"
    username: netop
    password: netop
    transport: cli
  rest:
    host: "{{ inventory_hostname }}"
    username: netop
    password: netop
    transport: rest

---
- ops_facts:
    gather_subset: all
    provider: "{{ rest }}"

# Collect only the config and default facts
- ops_facts:
    gather_subset: config
    provider: "{{ cli }}"

# Do not collect config facts
- ops_facts:
    gather_subset:
      - "!config"
    provider: "{{ cli }}"

- name: collect device facts
  ops_facts:
    provider: "{{ cli }}"

- name: include the config
  ops_facts:
    config: yes
    provider: "{{ rest }}"

- name: include a set of rest endpoints
  ops_facts:
    endpoints:
      - /system/interfaces/1
      - /system/interfaces/2
    provider: "{{ rest }}"
"""

RETURN = """
ansible_net_gather_subset:
  description: The list of fact subsets collected from the device
  returned: always
  type: list

# default
ansible_net_model:
  description: The model name returned from the device
  returned: when transport is cli
  type: str
ansible_net_serialnum:
  description: The serial number of the remote device
  returned: when transport is cli
  type: str
ansible_net_version:
  description: The operating system version running on the remote device
  returned: always
  type: str
ansible_net_hostname:
  description: The configured hostname of the device
  returned: always
  type: string
ansible_net_image:
  description: The image file the device is running
  returned: when transport is cli
  type: string

# config
ansible_net_config:
  description: The current active config from the device
  returned: when config is enabled
  type: str

# legacy (pre Ansible 2.2)
config:
  description: The current system configuration
  returned: when enabled
  type: string
  sample: '....'
hostname:
  description: returns the configured hostname
  returned: always
  type: string
  sample: ops01
version:
  description: The current version of OpenSwitch
  returned: always
  type: string
  sample: '0.3.0'
endpoints:
  description: The JSON response from the URL endpoint
  returned: when endpoints argument is defined and transport is rest
  type: list
  sample: [{....}, {....}]
"""
import re

import ansible.module_utils.openswitch
from ansible.module_utils.netcli import CommandRunner, AddCommandError
from ansible.module_utils.network import NetworkModule
from ansible.module_utils.six import iteritems


def add_command(runner, command):
    try:
        runner.add_command(command)
    except AddCommandError:
        # AddCommandError is raised for any issue adding a command to
        # the runner.  Silently ignore the exception in this case
        pass


class FactsBase(object):

    def __init__(self, module, runner):
        self.module = module
        self.transport = module.params['transport']
        self.runner = runner
        self.facts = dict()

        if self.transport == 'cli':
            self.commands()

    def commands(self):
        raise NotImplementedError

    def populate(self):
        getattr(self, self.transport)()

    def cli(self):
        pass

    def rest(self):
        pass


class Default(FactsBase):

    def commands(self):
        add_command(self.runner, 'show system')
        add_command(self.runner, 'show hostname')

    def rest(self):
        self.facts.update(self.get_system())

    def cli(self):
        data = self.runner.get_command('show system')

        self.facts['version'] = self.parse_version(data)
        self.facts['serialnum'] = self.parse_serialnum(data)
        self.facts['model'] = self.parse_model(data)
        self.facts['image'] = self.parse_image(data)

        self.facts['hostname'] = self.runner.get_command('show hostname')

    def parse_version(self, data):
        match = re.search(r'OpenSwitch Version\s+: (\S+)', data)
        if match:
            return match.group(1)

    def parse_model(self, data):
        match = re.search(r'Platform\s+:\s(\S+)', data, re.M)
        if match:
            return match.group(1)

    def parse_image(self, data):
        match = re.search(r'\(Build: (\S+)\)', data, re.M)
        if match:
            return match.group(1)

    def parse_serialnum(self, data):
        match = re.search(r'Serial Number\s+: (\S+)', data)
        if match:
            return match.group(1)

    def get_system(self):
        response = self.module.connection.get('/system')
        return dict(
            hostname=response.json['configuration']['hostname'],
            version=response.json['status']['switch_version']
        )


class Config(FactsBase):

    def commands(self):
        add_command(self.runner, 'show running-config')

    def cli(self):
        self.facts['config'] = self.runner.get_command('show running-config')

class Legacy(FactsBase):
    # facts from ops_facts 2.1

    def commands(self):
        add_command(self.runner, 'show system')
        add_command(self.runner, 'show hostname')

        if self.module.params['config']:
            add_command(self.runner, 'show running-config')

    def rest(self):
        self.facts['_endpoints'] = self.get_endpoints()
        self.facts.update(self.get_system())

        if self.module.params['config']:
            self.facts['_config'] = self.get_config()

    def cli(self):
        self.facts['_hostname'] = self.runner.get_command('show hostname')

        data = self.runner.get_command('show system')
        self.facts['_version'] = self.parse_version(data)

        if self.module.params['config']:
            self.facts['_config'] = self.runner.get_command('show running-config')

    def parse_version(self, data):
        match = re.search(r'OpenSwitch Version\s+: (\S+)', data)
        if match:
            return match.group(1)

    def get_endpoints(self):
        responses = list()
        urls = self.module.params['endpoints'] or list()
        for ep in urls:
            response = self.module.connection.get(ep)
            if response.headers['status'] != 200:
                self.module.fail_json(msg=response.headers['msg'])
            responses.append(response.json)
        return responses

    def get_system(self):
        response = self.module.connection.get('/system')
        return dict(
            _hostname=response.json['configuration']['hostname'],
            _version=response.json['status']['switch_version']
        )

    def get_config(self):
        response = self.module.connection.get('/system/full-configuration')
        return response.json

def check_args(module, warnings):
    if module.params['transport'] != 'rest' and module.params['endpoints']:
        warnings.append('Endpoints can only be collected when transport is '
                        'set to "rest".  Endpoints will not be collected')


FACT_SUBSETS = dict(
    default=Default,
    config=Config,
    legacy=Legacy
)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())

def main():
    spec = dict(
        gather_subset=dict(default=['!config'], type='list'),

        # the next two arguments are legacy from pre 2.2 ops_facts
        # these will be deprecated and ultimately removed
        config=dict(default=False, type='bool'),
        endpoints=dict(type='list'),

        transport=dict(default='cli', choices=['cli', 'rest'])
    )

    module = NetworkModule(argument_spec=spec, supports_check_mode=True)

    gather_subset = module.params['gather_subset']

    warnings = list()
    check_args(module, warnings)

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
            module.fail_json(msg='Bad subset')

        if exclude:
            exclude_subsets.add(subset)
        else:
            runable_subsets.add(subset)

    if not runable_subsets:
        runable_subsets.update(VALID_SUBSETS)

    runable_subsets.difference_update(exclude_subsets)
    runable_subsets.add('default')
    runable_subsets.add('legacy')

    facts = dict()
    facts['gather_subset'] = list(runable_subsets)

    runner = CommandRunner(module)

    instances = list()
    for key in runable_subsets:
        instances.append(FACT_SUBSETS[key](module, runner))

    if module.params['transport'] == 'cli':
        runner.run()

    try:
        for inst in instances:
            inst.populate()
            facts.update(inst.facts)
    except Exception:
        module.exit_json(out=module.from_json(runner.items))

    ansible_facts = dict()
    for key, value in iteritems(facts):
        # this is to maintain capability with ops_facts 2.1
        if key.startswith('_'):
            ansible_facts[key[1:]] = value
        else:
            key = 'ansible_net_%s' % key
            ansible_facts[key] = value

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()
