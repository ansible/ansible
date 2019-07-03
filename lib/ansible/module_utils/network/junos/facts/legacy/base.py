# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The junos interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
import platform

from ansible.module_utils.network.common.netconf import exec_rpc
from ansible.module_utils.network.junos.junos import get_param, tostring
from ansible.module_utils.network.junos.junos import get_configuration, get_capabilities
from ansible.module_utils._text import to_native


try:
    from lxml.etree import Element, SubElement
except ImportError:
    from xml.etree.ElementTree import Element, SubElement

try:
    from jnpr.junos import Device
    from jnpr.junos.exception import ConnectError
    HAS_PYEZ = True
except ImportError:
    HAS_PYEZ = False


class FactsBase(object):

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.warnings = []

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
        self.facts.update(self.platform_facts())

        reply = self.rpc('get-chassis-inventory')
        data = reply.find('.//chassis-inventory/chassis')
        self.facts['serialnum'] = self.get_text(data, 'serial-number')

    def platform_facts(self):
        platform_facts = {}

        resp = get_capabilities(self.module)
        device_info = resp['device_info']

        platform_facts['system'] = device_info['network_os']

        for item in ('model', 'image', 'version', 'platform', 'hostname'):
            val = device_info.get('network_os_%s' % item)
            if val:
                platform_facts[item] = val

        platform_facts['api'] = resp['network_api']
        platform_facts['python_version'] = platform.python_version()

        return platform_facts


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
