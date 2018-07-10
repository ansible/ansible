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
module: cl_bond
version_added: "2.1"
author: "Cumulus Networks (@CumulusNetworks)"
short_description: Configures a bond port on Cumulus Linux
deprecated:
  removed_in: "2.5"
  why: The M(nclu) module is designed to be easier to use for individuals who are new to Cumulus Linux by exposing the NCLU interface in an automatable way.
  alternative: Use M(nclu) instead.
description:
    - Configures a bond interface on Cumulus Linux To configure a bridge port
      use the cl_bridge module. To configure any other type of interface use the
      cl_interface module. Follow the guidelines for bonding found in the
      Cumulus User Guide at U(http://docs.cumulusnetworks.com).
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
    mstpctl_bpduguard:
        description:
            - Enables BPDU Guard on a port in vlan-aware mode.
        choices:
            - true
            - false
    mstpctl_portnetwork:
        description:
            - Enables bridge assurance in vlan-aware mode.
        choices:
            - true
            - false
    mstpctl_portadminedge:
        description:
            - Enables admin edge port.
        choices:
            - true
            - false
    clag_id:
        description:
            - Specify a unique clag_id for every dual connected bond on each
              peer switch. The value must be between 1 and 65535 and must be the
              same on both peer switches in order for the bond to be considered
              dual-connected.
    pvid:
        description:
            - In vlan-aware mode, defines vlan that is the untagged vlan.
    miimon:
        description:
            - The mii link monitoring interval.
        default: 100
    mode:
        description:
            - The bond mode, as of Cumulus Linux 2.5 only LACP bond mode is
              supported.
        default: '802.3ad'
    min_links:
        description:
            - Minimum number of links.
        default: 1
    lacp_bypass_allow:
        description:
            - Enable LACP bypass.
    lacp_bypass_period:
        description:
            - Period for enabling LACP bypass. Max value is 900.
    lacp_bypass_priority:
        description:
            - List of ports and priorities. Example I("swp1=10, swp2=20").
    lacp_bypass_all_active:
        description:
            - Activate all interfaces for bypass.
              It is recommended to configure all_active instead
              of using bypass_priority.
    lacp_rate:
        description:
            - The lacp rate.
        default: 1
    slaves:
        description:
            - Bond members.
        required: True
    xmit_hash_policy:
        description:
            - Transmit load balancing algorithm. As of Cumulus Linux 2.5 only
              I(layer3+4) policy is supported.
        default: layer3+4
    location:
        description:
            - Interface directory location.
        default:
            - '/etc/network/interfaces.d'

requirements:  [ Alternate Debian network interface manager - \
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
# configure a bond interface with IP address
- cl_bond:
    name: bond0
    slaves:
      - swp4-5
    ipv4: 10.1.1.1/24

# configure bond as a dual-connected clag bond
- cl_bond:
    name: bond1
    slaves:
      - swp1s0
      - swp2s0
    clag_id: 1

# define cl_bond once in tasks file
# then write interface config in variables file
# with just the options you want.
- cl_bond:
    name: "{{ item.key }}"
    slaves: "{{ item.value.slaves }}"
    clag_id: "{{ item.value.clag_id|default(omit) }}"
    ipv4:  "{{ item.value.ipv4|default(omit) }}"
    ipv6: "{{ item.value.ipv6|default(omit) }}"
    alias_name: "{{ item.value.alias_name|default(omit) }}"
    addr_method: "{{ item.value.addr_method|default(omit) }}"
    mtu: "{{ item.value.mtu|default(omit) }}"
    vids: "{{ item.value.vids|default(omit) }}"
    virtual_ip: "{{ item.value.virtual_ip|default(omit) }}"
    virtual_mac: "{{ item.value.virtual_mac|default(omit) }}"
    mstpctl_portnetwork: "{{ item.value.mstpctl_portnetwork|default('no') }}"
    mstpctl_portadminedge: "{{ item.value.mstpctl_portadminedge|default('no') }}"
    mstpctl_bpduguard: "{{ item.value.mstpctl_bpduguard|default('no') }}"
  with_dict: "{{ cl_bonds }}"

# In vars file
# ============
---
cl_bonds:
  bond0:
    alias_name: uplink to isp
    slaves:
      - swp1
      - swp3
    ipv4: 10.1.1.1/24'
  bond2:
    vids:
      - 1
      - 50
    clag_id: 1
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
