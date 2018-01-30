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
module: cl_interface
version_added: "2.1"
author: "Cumulus Networks (@CumulusNetworks)"
short_description: Configures a front panel port, loopback or
                  management port on Cumulus Linux.
deprecated:
  removed_in: "2.5"
  why: The M(nclu) module is designed to be easier to use for individuals who are new to Cumulus Linux by exposing the NCLU interface in an automatable way.
  alternative: Use M(nclu) instead.
description:
    - Configures a front panel, sub-interface, SVI, management or loopback port
      on a Cumulus Linux switch. For bridge ports use the cl_bridge module. For
      bond ports use the cl_bond module. When configuring bridge related
      features like the "vid" option, please follow the guidelines for
      configuring "vlan aware" bridging. For more details review the Layer2
      Interface Guide at U(http://docs.cumulusnetworks.com)
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
            - Address method.
        choices:
            - loopback
            - dhcp
    speed:
        description:
            - Set speed of the swp(front panel) or management(eth0) interface.
              speed is in MB.
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
    mstpctl_portnetwork:
        description:
            - Enables bridge assurance in vlan-aware mode.
    mstpctl_portadminedge:
        description:
            - Enables admin edge port.
    clagd_enable:
        description:
            - Enables the clagd daemon. This command should only be applied to
              the clag peerlink interface.
    clagd_priority:
        description:
            - Integer that changes the role the switch has in the clag domain.
              The lower priority switch will assume the primary role. The number
              can be between 0 and 65535.
    clagd_peer_ip:
        description:
            - IP address of the directly connected peer switch interface.
    clagd_sys_mac:
        description:
            - Clagd system mac address. Recommended to use the range starting
              with 44:38:39:ff. Needs to be the same between 2 Clag switches.
    pvid:
        description:
            - In vlan-aware mode, defines vlan that is the untagged vlan.
    location:
        description:
            - Interface directory location
        default:
            - '/etc/network/interfaces.d'

requirements: [ Alternate Debian network interface manager - \
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
- name: Configure a front panel port with an IP
  cl_interface:
    name: swp1
    ipv4: 10.1.1.1/24
  notify: reload networking

- name: Configure front panel to use DHCP
  cl_interface:
    name: swp2
    addr_family: dhcp
  notify: reload networking

- name: Configure a SVI for vlan 100 interface with an IP
  cl_interface:
    name: bridge.100
    ipv4: 10.1.1.1/24
  notify: reload networking

- name: Configure subinterface with an IP
  cl_interface:
    name: bond0.100
    alias_name: my bond
    ipv4: 10.1.1.1/24
  notify: reload networking

# define cl_interfaces once in tasks
# then write interfaces in variables file
# with just the options you want.
- name: Create interfaces
  cl_interface:
      name: '{{ item.key }}'
      ipv4: '{{ item.value.ipv4 | default(omit) }}'
      ipv6: '{{ item.value.ipv6 | default(omit) }}'
      alias_name: '{{ item.value.alias_name | default(omit) }}'
      addr_method: '{{ item.value.addr_method | default(omit) }}'
      speed: '{{ item.value.link_speed | default(omit) }}'
      mtu: '{{ item.value.mtu | default(omit) }}'
      clagd_enable: '{{ item.value.clagd_enable | default(omit) }}'
      clagd_peer_ip: '{{ item.value.clagd_peer_ip | default(omit) }}'
      clagd_sys_mac: '{{ item.value.clagd_sys_mac | default(omit) }}'
      clagd_priority: '{{ item.value.clagd_priority | default(omit) }}'
      vids: '{{ item.value.vids | default(omit) }}'
      virtual_ip: '{{ item.value.virtual_ip | default(omit) }}'
      virtual_mac: '{{ item.value.virtual_mac | default(omit) }}'
      mstpctl_portnetwork: "{{ item.value.mstpctl_portnetwork | default('no') }}"
      mstpctl_portadminedge: "{{ item.value.mstpctl_portadminedge | default('no') }}"
      mstpctl_bpduguard: "{{ item.value.mstpctl_bpduguard | default('no') }}"
  with_dict: '{{ cl_interfaces }}'
  notify: reload networking

# In vars file
# ============
---
cl_interfaces:
  swp1:
    alias_name: uplink to isp
    ipv4: 10.1.1.1/24
  swp2:
    alias_name: l2 trunk connection
    vids:
      - 1
      - 50
  swp3:
    speed: 1000
    alias_name: connects to 1G link
##########
#   br0 interface is configured by cl_bridge
##########
  br0.100:
    alias_name: SVI for vlan 100
    ipv4: 10.2.2.2/24
    ipv6: '10:2:2::2/127'
    virtual_ip: 10.2.2.254
    virtual_mac: 00:00:5E:00:10:10
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
