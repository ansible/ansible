#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: junos_facts
version_added: "2.1"
author: "Nathaniel Case (@qalthos)"
short_description: Collect facts from remote devices running Juniper Junos
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
        all, hardware, config, and interfaces.  Can specify a list of
        values to include a larger subset.  Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected. To maintain backward compatbility old style facts
        can be retrieved using all value, this reqires junos-eznc to be installed
        as a prerequisite. Valid value of gather_subset are default, hardware,
        config, interfaces, ofacts. If C(ofacts) is present in the list it fetches
        the old style facts (fact keys without 'ansible_' prefix) and it requires
        junos-eznc library to be installed on control node and the device login credentials
        must be given in C(provider) option.
    required: false
    default: ['!config', '!ofacts']
    version_added: "2.3"
  config_format:
    description:
      - The I(config_format) argument specifies the format of the configuration
         when serializing output from the device. This argument is applicable
         only when C(config) value is present in I(gather_subset).
         The I(config_format) should be supported by the junos version running on
         device. This value is not applicable while fetching old style facts that is
         when value of I(gather_subset) C(all) or C(ofacts) is present in the value.
    required: false
    default: 'text'
    choices: ['xml', 'text', 'set', 'json']
    version_added: "2.3"
requirements:
  - ncclient (>=v0.5.2)
notes:
  - Ensure I(config_format) used to retrieve configuration from device
    is supported by junos version running on device.
  - With I(config_format = json), configuration in the results will be a dictionary(and not a JSON string)
  - This module requires the netconf system service be enabled on
    the remote device being managed.
  - Tested against vSRX JUNOS version 15.1X49-D15.4, vqfx-10000 JUNOS Version 15.1X53-D60.4.
  - Recommended connection is C(netconf). See L(the Junos OS Platform Options,../network/user_guide/platform_junos.html).
  - This module also works with C(local) connections for legacy playbooks.
  - Fetching old style facts requires junos-eznc library to be installed on control node and the device login credentials
    must be given in provider option.
"""

EXAMPLES = """
- name: collect default set of facts
  junos_facts:

- name: collect default set of facts and configuration
  junos_facts:
    gather_subset: config
"""

RETURN = """
ansible_facts:
  description: Returns the facts collect from the device
  returned: always
  type: dict
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.netconf import exec_rpc
from ansible.module_utils.network.junos.junos import junos_argument_spec, get_param
from ansible.module_utils.network.junos.junos import get_configuration, get_connection
from ansible.module_utils._text import to_native
from ansible.module_utils.six import iteritems


try:
    from lxml.etree import Element, SubElement, tostring
except ImportError:
    from xml.etree.ElementTree import Element, SubElement, tostring

try:
    from jnpr.junos import Device
    from jnpr.junos.exception import ConnectError
    HAS_PYEZ = True
except ImportError:
    HAS_PYEZ = False

USE_PERSISTENT_CONNECTION = True


class FactsBase(object):

    def __init__(self, module):
        self.module = module
        self.facts = dict()

    def populate(self):
        raise NotImplementedError

    def cli(self, command):
        reply = command(self.module, command)
        output = reply.find('.//output')
        if not output:
            self.module.fail_json(msg='failed to retrieve facts for command %s' % command)
        return str(output.text).strip()

    def rpc(self, rpc):
        return exec_rpc(self.module, tostring(Element(rpc)))

    def get_text(self, ele, tag):
        try:
            return str(ele.find(tag).text).strip()
        except AttributeError:
            pass


class Default(FactsBase):

    def populate(self):
        reply = self.rpc('get-software-information')
        data = reply.find('.//software-information')

        self.facts.update({
            'hostname': self.get_text(data, 'host-name'),
            'version': self.get_text(data, 'junos-version'),
            'model': self.get_text(data, 'product-model')
        })

        reply = self.rpc('get-chassis-inventory')
        data = reply.find('.//chassis-inventory/chassis')
        self.facts['serialnum'] = self.get_text(data, 'serial-number')


class Config(FactsBase):

    def populate(self):
        config_format = self.module.params['config_format']
        reply = get_configuration(self.module, format=config_format)

        if config_format == 'xml':
            config = tostring(reply.find('configuration')).strip()

        elif config_format == 'text':
            config = self.get_text(reply, 'configuration-text')

        elif config_format == 'json':
            config = self.module.from_json(reply.text.strip())

        elif config_format == 'set':
            config = self.get_text(reply, 'configuration-set')

        self.facts['config'] = config


class Hardware(FactsBase):

    def populate(self):

        reply = self.rpc('get-system-memory-information')
        data = reply.find('.//system-memory-information/system-memory-summary-information')

        self.facts.update({
            'memfree_mb': int(self.get_text(data, 'system-memory-free')),
            'memtotal_mb': int(self.get_text(data, 'system-memory-total'))
        })

        reply = self.rpc('get-system-storage')
        data = reply.find('.//system-storage-information')

        filesystems = list()
        for obj in data:
            filesystems.append(self.get_text(obj, 'filesystem-name'))
        self.facts['filesystems'] = filesystems

        reply = self.rpc('get-route-engine-information')
        data = reply.find('.//route-engine-information')

        routing_engines = dict()
        for obj in data:
            slot = self.get_text(obj, 'slot')
            routing_engines.update({slot: {}})
            routing_engines[slot].update({'slot': slot})
            for child in obj:
                if child.text != "\n":
                    routing_engines[slot].update({child.tag.replace("-", "_"): child.text})

        self.facts['routing_engines'] = routing_engines

        if len(data) > 1:
            self.facts['has_2RE'] = True
        else:
            self.facts['has_2RE'] = False

        reply = self.rpc('get-chassis-inventory')
        data = reply.findall('.//chassis-module')

        modules = list()
        for obj in data:
            mod = dict()
            for child in obj:
                if child.text != "\n":
                    mod.update({child.tag.replace("-", "_"): child.text})
            modules.append(mod)

        self.facts['modules'] = modules


class Interfaces(FactsBase):

    def populate(self):
        ele = Element('get-interface-information')
        SubElement(ele, 'detail')
        reply = exec_rpc(self.module, tostring(ele))

        interfaces = {}

        for item in reply[0]:
            name = self.get_text(item, 'name')
            obj = {
                'oper-status': self.get_text(item, 'oper-status'),
                'admin-status': self.get_text(item, 'admin-status'),
                'speed': self.get_text(item, 'speed'),
                'macaddress': self.get_text(item, 'hardware-physical-address'),
                'mtu': self.get_text(item, 'mtu'),
                'type': self.get_text(item, 'if-type'),
            }

            interfaces[name] = obj

        self.facts['interfaces'] = interfaces


class OFacts(FactsBase):
    def _connect(self, module):
        host = get_param(module, 'host')

        kwargs = {
            'port': get_param(module, 'port') or 830,
            'user': get_param(module, 'username')
        }

        if get_param(module, 'password'):
            kwargs['passwd'] = get_param(module, 'password')

        if get_param(module, 'ssh_keyfile'):
            kwargs['ssh_private_key_file'] = get_param(module, 'ssh_keyfile')

        kwargs['gather_facts'] = False
        try:
            device = Device(host, **kwargs)
            device.open()
            device.timeout = get_param(module, 'timeout') or 10
        except ConnectError as exc:
            module.fail_json('unable to connect to %s: %s' % (host, to_native(exc)))

        return device

    def populate(self):

        device = self._connect(self.module)
        facts = dict(device.facts)

        if '2RE' in facts:
            facts['has_2RE'] = facts['2RE']
            del facts['2RE']

        facts['version_info'] = dict(facts['version_info'])
        if 'junos_info' in facts:
            for key, value in facts['junos_info'].items():
                if 'object' in value:
                    value['object'] = dict(value['object'])

        return facts


FACT_SUBSETS = dict(
    default=Default,
    hardware=Hardware,
    config=Config,
    interfaces=Interfaces,
    ofacts=OFacts
)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())


def main():
    """ Main entry point for AnsibleModule
    """
    argument_spec = dict(
        gather_subset=dict(default=['!config', '!ofacts'], type='list'),
        config_format=dict(default='text', choices=['xml', 'text', 'set', 'json']),
    )

    argument_spec.update(junos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    get_connection(module)
    warnings = list()
    gather_subset = module.params['gather_subset']

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
    ansible_facts = dict()

    if 'ofacts' in runable_subsets:
        if HAS_PYEZ:
            ansible_facts.update(OFacts(module).populate())
        else:
            warnings += ['junos-eznc is required to gather old style facts but does not appear to be installed. '
                         'It can be installed using `pip  install junos-eznc`']
        runable_subsets.remove('ofacts')

    for key in runable_subsets:
        instances.append(FACT_SUBSETS[key](module))

    for inst in instances:
        inst.populate()
        facts.update(inst.facts)

    for key, value in iteritems(facts):
        key = 'ansible_net_%s' % key
        ansible_facts[key] = value

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()
