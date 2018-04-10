#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Cumulus Networks <ce-ceng@cumulusnetworks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: cl_bridge
version_added: "2.1"
author: "Cumulus Networks (@CumulusNetworks)"
short_description: Configures a bridge port on Cumulus Linux
deprecated:
  removed_in: "2.5"
  why: The M(nclu) module is designed to be easier to use for individuals who are new to Cumulus Linux by exposing the NCLU interface in an automatable way.
  alternative: Use M(nclu) instead.
description:
    - Configures a bridge interface on Cumulus Linux To configure a bond port
      use the cl_bond module. To configure any other type of interface use the
      cl_interface module. Follow the guidelines for bridging found in the
      Cumulus User Guide at U(http://docs.cumulusnetworks.com)
options:
    name:
        description:
            - Name of the interface.
        required: true
    alias_name:
        description:
            - Description of the port.
    ipv4:
        description:
            - List of IPv4 addresses to configure on the interface.
              In the form I(X.X.X.X/YY).
    ipv6:
        description:
            - List of IPv6 addresses to configure on the interface.
              In the form I(X:X:X::X/YYY).
    addr_method:
        description:
            - Configures the port to use DHCP.
              To enable this feature use the option I(dhcp).
        choices: ['dhcp']
    mtu:
        description:
            - Set MTU. Configure Jumbo Frame by setting MTU to I(9000).
    virtual_ip:
        description:
            - Define IPv4 virtual IP used by the Cumulus Linux VRR feature.
    virtual_mac:
        description:
            - Define Ethernet mac associated with Cumulus Linux VRR feature.
    vids:
        description:
            - In vlan-aware mode, lists VLANs defined under the interface.
    pvid:
        description:
            - In vlan-aware mode, defines vlan that is the untagged vlan.
    stp:
        description:
            - Enables spanning tree Protocol. As of Cumulus Linux 2.5 the default
              bridging mode, only per vlan RSTP or 802.1d is supported. For the
              vlan aware mode, only common instance STP is supported
        default: 'yes'
        choices: ['yes', 'no']
    ports:
        description:
            - List of bridge members.
        required: True
    vlan_aware:
        description:
            - Enables vlan-aware mode.
        choices: ['yes', 'no']
    mstpctl_treeprio:
        description:
            - Set spanning tree root priority. Must be a multiple of 4096.
    location:
        description:
            - Interface directory location.
        default:
            - '/etc/network/interfaces.d'


requirements: [ Alternate Debian network interface manager
ifupdown2 @ github.com/CumulusNetworks/ifupdown2 ]
notes:
    - As this module writes the interface directory location, ensure that
      ``/etc/network/interfaces`` has a 'source /etc/network/interfaces.d/\*' or
      whatever path is mentioned in the ``location`` attribute.

    - For the config to be activated, i.e installed in the kernel,
      "service networking reload" needs be be executed. See EXAMPLES section.
'''

EXAMPLES = '''
# Options ['virtual_mac', 'virtual_ip'] are required together
# configure a bridge vlan aware bridge.
- cl_bridge:
    name: br0
    ports: 'swp1-12'
    vlan_aware: 'yes'
  notify: reload networking

# configure bridge interface to define a default set of vlans
- cl_bridge:
    name: bridge
    ports: 'swp1-12'
    vlan_aware: 'yes'
    vids: '1-100'
  notify: reload networking

# define cl_bridge once in tasks file
# then write interface config in variables file
# with just the options you want.
- cl_bridge:
    name: "{{ item.key }}"
    ports: "{{ item.value.ports }}"
    vlan_aware: "{{ item.value.vlan_aware|default(omit) }}"
    ipv4:  "{{ item.value.ipv4|default(omit) }}"
    ipv6: "{{ item.value.ipv6|default(omit) }}"
    alias_name: "{{ item.value.alias_name|default(omit) }}"
    addr_method: "{{ item.value.addr_method|default(omit) }}"
    mtu: "{{ item.value.mtu|default(omit) }}"
    vids: "{{ item.value.vids|default(omit) }}"
    virtual_ip: "{{ item.value.virtual_ip|default(omit) }}"
    virtual_mac: "{{ item.value.virtual_mac|default(omit) }}"
    mstpctl_treeprio: "{{ item.value.mstpctl_treeprio|default(omit) }}"
  with_dict: "{{ cl_bridges }}"
  notify: reload networking

# In vars file
# ============
---
cl_bridge:
  br0:
    alias_name: 'vlan aware bridge'
    ports: ['swp1', 'swp3']
    vlan_aware: true
    vids: ['1-100']
'''

RETURN = '''
changed:
    description: whether the interface was changed
    returned: changed
    type: bool
    sample: True
msg:
    description: human-readable report of success or failure
    returned: always
    type: string
    sample: "interface bond0 config updated"
'''

from ansible.module_utils.common.removed import removed_module

if __name__ == '__main__':
    removed_module()
