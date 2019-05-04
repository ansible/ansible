#!/usr/bin/python

# Copyright: (c) 2019, Chris Redit, github.com/chrisred
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
module: virt_net_facts
short_description: Retrieve facts about a libvirt virtual network.
description: Retrieve facts about a libvirt virtual network. Facts from the file config and live config
  are both retrieved when applicable.
version_added: "2.9"
author: Chris Redit (@chrisred)
options:
  name:
    description: Defines the name of the virtual network(s) to retrieve facts for. If no I(name)
      parameter is provided all virtual networks on the host will be retrieved.
    type: list
  uri:
    description: The libvirt connection URI.
    default: qemu:///system
    type: str
notes:
  - Facts are generated from the XML configuration of the virtual network. The keys returned for each
    of the items listed in the return values can vary based on the network configuration.
requirements:
  - python >= 2.6
  - python-lxml
  - libvirt-python
'''

EXAMPLES = '''
- name: Retrieve facts for all the networks on a host
  virt_net_facts:

- name: Retrieve facts for the networks mynet1 and mynet2
  virt_net_facts: name=mynet1,mynet2

- name: Retrieve the name of the associated bridge device for each network on the host
  virt_net_facts:
- debug:
    msg: "{{item.key}}: {{item.value.bridge.name}}"
  loop: "{{virt_networks | dict2items}}"
  loop_control:
    label: "{{item.key}}"
'''

RETURN = '''
virt_networks:
  description: Facts retrieved from the persistent virtual network config, with the virtual network
    name as a key.
  returned: always
  type: complex
  contains:
    active:
      description: Defines whether the network is active or stopped.
      returned: success
      type: bool
    autostart:
      description: Defines whether the network will start automatically after the host has booted.
      returned: success
      type: bool
    connections:
      description: The number of network interfaces currently connected via this network from a domain.
      returned: success
      type: str
    mac_address:
      description: The MAC address assigned to the bridge device defined for the network.
      returned: success
      type: str
    name:
      description: The short name for the network.
      returned: success
      type: str
    persistent:
      description: Defines whether the network is persistent or transient.
      returned: success
      type: bool
    uuid:
      description: The globally unique identifier for the network.
      returned: success
      type: str
    bridge:
      description: The bridge device defined for the network.
      returned: success
      type: complex
    dns:
      description: The DNS server defined for the network.
      returned: success
      type: complex
    domain:
      description: The DNS domain defined for the network's DHCP server.
      returned: success
      type: complex
    forward:
      description: The forwarding defined for the network.
      returned: success
      type: complex
    mtu:
      description: The maximum transmission unit (MTU) defined for the network.
      returned: success
      type: complex
    virtualport:
      description: The virtual ports (VEPA) defined for the network.
      returned: success
      type: complex
    vlan:
      description: The guest-transparent VLAN tagging defined for the network.
      returned: success
      type: complex
    ip:
      description: The IPv4 or IPv6 address assigned to the bridge device defined for the network.
      returned: success
      type: complex
    portgroup:
      description: The port group defined for the network.
      returned: success
      type: complex
    static_route:
      description: The static route definitions provided to the host for the network.
      returned: success
      type: complex
virt_networks_live:
  description: Facts retrieved from the live virtual network config, with the virtual network name
    as a key. This contains an identical set of return values as the C(virt_networks) key.
  returned: always
  type: complex
  contains: dict
'''

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.virt import Config, etree_to_dict, flatten_dict, get_facts
import traceback

LIBVIRT_IMPORT_ERROR = None
try:
    import libvirt
    HAS_LIBVIRT = True
except ImportError:
    LIBVIRT_IMPORT_ERROR = traceback.format_exc()
    HAS_LIBVIRT = False


class NetworkConfig(Config):
    @property
    def connections(self):
        return self._etree.find('.').attrib.get('connections')

    @property
    def mac_address(self):
        return self._etree.find('./mac').attrib.get('address')

    @property
    def name(self):
        return self._etree.findtext('./name')

    @property
    def uuid(self):
        return self._etree.findtext('./uuid')

    @property
    def bridge(self):
        return self._etree.find('./bridge')

    @property
    def dns(self):
        return self._etree.find('./dns')

    @property
    def domain(self):
        return self._etree.find('./domain')

    @property
    def forward(self):
        return self._etree.find('./forward')

    @property
    def mtu(self):
        return self._etree.find('./mtu')

    @property
    def virtualport(self):
        return self._etree.find('./virtualport')

    @property
    def vlan(self):
        return self._etree.find('./vlan')

    @property
    def ip(self):
        return self._etree.findall('./ip')

    @property
    def portgroup(self):
        return self._etree.findall('./portgroup')

    @property
    def static_route(self):
        return self._etree.findall('./route')


def main():
    module_args = dict(
        name=dict(type='list'),
        uri=dict(type='str', default='qemu:///system'),
    )

    host = None
    config_live = None
    config_file = None
    active = False
    autostart = None
    persistent = True
    facts_file = dict()
    facts_live = dict()
    networks = list()
    module = AnsibleModule(module_args, supports_check_mode=True)
    name = module.params['name']

    if not HAS_LIBVIRT:
        module.fail_json(msg=missing_required_lib('libvirt'), exception=LIBVIRT_IMPORT_ERROR)

    try:
        host = libvirt.open(module.params['uri'])
        try:
            if name is not None and isinstance(name, list):
                networks = [host.networkLookupByName(item) for item in name]
            else:
                networks = host.listAllNetworks(
                    libvirt.VIR_CONNECT_LIST_NETWORKS_PERSISTENT |
                    libvirt.VIR_CONNECT_LIST_NETWORKS_TRANSIENT
                )
        except libvirt.libvirtError:
            module.fail_json(msg='Network(s) not found on this host.')

        # the properties of the Config object that will be returned as facts
        wanted_properties = [
            'connections', 'mac_address', 'name', 'uuid', 'bridge', 'dns', 'domain', 'forward', 'mtu',
            'virtualport', 'vlan', 'ip', 'portgroup', 'static_route'
        ]

        for network in networks:
            if network.isPersistent():
                config_file = NetworkConfig(module, network.XMLDesc(libvirt.VIR_NETWORK_XML_INACTIVE))
                autostart = True if network.autostart() else False

                if network.isActive():
                    config_live = NetworkConfig(module, network.XMLDesc())
                    active = True
            else:
                # a transient network only has a "live" configuration
                config_live = NetworkConfig(module, network.XMLDesc())
                active = True
                persistent = False

            if config_file:
                facts_file[config_file.name] = get_facts(config_file, wanted_properties)
                facts_file[config_file.name]['active'] = active
                facts_file[config_file.name]['autostart'] = autostart
                facts_file[config_file.name]['persistent'] = persistent

            if config_live:
                facts_live[config_live.name] = get_facts(config_live, wanted_properties)
                facts_live[config_live.name]['active'] = active
                facts_live[config_live.name]['autostart'] = autostart
                facts_live[config_live.name]['persistent'] = persistent

        module.exit_json(
            changed=False,
            ansible_facts=dict(
                virt_networks=facts_file if len(facts_file) > 0 else None,
                virt_networks_live=facts_live if len(facts_live) > 0 else None,
            ),
        )

    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        if host is not None:
            host.close()


if __name__ == '__main__':
    main()
