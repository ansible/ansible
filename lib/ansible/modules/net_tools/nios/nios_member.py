#!/usr/bin/python
# Copyright (c) 2018 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''
---
module: nios_member
version_added: "2.8"
author: "Krishna Vasudevan (@krisvasudevan)"
short_description: Configure Infoblox NIOS members
description:
  - Adds and/or removes Infoblox NIOS servers.  This module manages NIOS C(member) objects using the Infoblox WAPI interface over REST.
requirements:
  - infoblox-client
extends_documentation_fragment: nios
options:
  host_name:
    description:
      - Specifies the host name of the member to either add or remove from
        the NIOS instance.
    required: true
    aliases:
      - name
  vip_setting:
    description:
      - Configures the network settings for the grid member.
    required: true
    suboptions:
      address:
        description:
          - The IPv4 Address of the Grid Member
      subnet_mask:
        description:
          - The subnet mask for the Grid Member
      gateway:
        description:
          - The default gateway for the Grid Member
  ipv6_setting:
    description:
      - Configures the IPv6 settings for the grid member.
    required: true
    suboptions:
      virtual_ip:
        description:
          - The IPv6 Address of the Grid Member
      cidr_prefix:
        description:
          - The IPv6 CIDR prefix for the Grid Member
      gateway:
        description:
          - The gateway address for the Grid Member
  config_addr_type:
    description:
      - Address configuration type (IPV4/IPV6/BOTH)
    default: IPV4
  comment:
    description:
      - A descriptive comment of the Grid member.
  extattrs:
    description:
      - Extensible attributes associated with the object.
  enable_ha:
    description:
      - If set to True, the member has two physical nodes (HA pair).
    type: bool
  router_id:
    description:
      - Virtual router identifier. Provide this ID if "ha_enabled" is set to "true". This is a unique VRID number (from 1 to 255) for the local subnet.
  lan2_enabled:
    description:
      - When set to "true", the LAN2 port is enabled as an independent port or as a port for failover purposes.
    type: bool
  lan2_port_setting:
    description:
      - Settings for the Grid member LAN2 port if 'lan2_enabled' is set to "true".
    suboptions:
      enabled:
        description:
          - If set to True, then it has its own IP settings.
        type: bool
      network_setting:
        description:
          - If the 'enable' field is set to True, this defines IPv4 network settings for LAN2.
        suboptions:
          address:
            description:
              - The IPv4 Address of LAN2
          subnet_mask:
            description:
              - The subnet mask of LAN2
          gateway:
            description:
              - The default gateway of LAN2
      v6_network_setting:
        description:
          - If the 'enable' field is set to True, this defines IPv6 network settings for LAN2.
        suboptions:
          virtual_ip:
            description:
              - The IPv6 Address of LAN2
          cidr_prefix:
            description:
              - The IPv6 CIDR prefix of LAN2
          gateway:
            description:
              - The gateway address of LAN2
  platform:
    description:
      - Configures the Hardware Platform.
    default: INFOBLOX
  node_info:
    description:
      - Configures the node information list with detailed status report on the operations of the Grid Member.
    suboptions:
      lan2_physical_setting:
        description:
          - Physical port settings for the LAN2 interface.
        suboptions:
          auto_port_setting_enabled:
            description:
              - Enable or disalbe the auto port setting.
            type: bool
          duplex:
            description:
              - The port duplex; if speed is 1000, duplex must be FULL.
          speed:
            description:
              - The port speed; if speed is 1000, duplex is FULL.
      lan_ha_port_setting:
        description:
          - LAN/HA port settings for the node.
        suboptions:
          ha_ip_address:
            description:
              - HA IP address.
          ha_port_setting:
            description:
              - Physical port settings for the HA interface.
            suboptions:
              auto_port_setting_enabled:
                description:
                  - Enable or disalbe the auto port setting.
                type: bool
              duplex:
                description:
                  - The port duplex; if speed is 1000, duplex must be FULL.
              speed:
                description:
                  - The port speed; if speed is 1000, duplex is FULL.
          lan_port_setting:
            description:
              - Physical port settings for the LAN interface.
            suboptions:
              auto_port_setting_enabled:
                description:
                  - Enable or disalbe the auto port setting.
                type: bool
              duplex:
                description:
                  - The port duplex; if speed is 1000, duplex must be FULL.
              speed:
                description:
                  - The port speed; if speed is 1000, duplex is FULL.
          mgmt_ipv6addr:
            description:
              - Public IPv6 address for the LAN1 interface.
          mgmt_lan:
            description:
              - Public IPv4 address for the LAN1 interface.
      mgmt_network_setting:
        description:
          - Network settings for the MGMT port of the node.
        suboptions:
          address:
            description:
              - The IPv4 Address of MGMT
          subnet_mask:
            description:
              - The subnet mask of MGMT
          gateway:
            description:
              - The default gateway of MGMT
      v6_mgmt_network_setting:
        description:
          - The network settings for the IPv6 MGMT port of the node.
        suboptions:
          virtual_ip:
            description:
              - The IPv6 Address of MGMT
          cidr_prefix:
            description:
              - The IPv6 CIDR prefix of MGMT
          gateway:
            description:
              - The gateway address of MGMT
  mgmt_port_setting:
    description:
      - Settings for the member MGMT port.
    suboptions:
      enabled:
        description:
          - Determines if MGMT port settings should be enabled.
        type: bool
      security_access_enabled:
        description:
          - Determines if security access on the MGMT port is enabled or not.
        type: bool
      vpn_enabled:
        description:
          - Determines if VPN on the MGMT port is enabled or not.
        type: bool
  upgrade_group:
    description:
      - The name of the upgrade group to which this Grid member belongs.
    default: Default
  use_syslog_proxy_setting:
    description:
      - Use flag for external_syslog_server_enable , syslog_servers, syslog_proxy_setting, syslog_size
    type: bool
  external_syslog_server_enable:
    description:
      - Determines if external syslog servers should be enabled
    type: bool
  syslog_servers:
    description:
      - The list of external syslog servers.
    suboptions:
      address:
        description:
          - The server address.
      category_list:
        description:
          - The list of all syslog logging categories.
      connection_type:
        description:
          - The connection type for communicating with this server.(STCP/TCP?UDP)
        default: UDP
      local_interface:
        description:
          - The local interface through which the appliance sends syslog messages to the syslog server.(ANY/LAN/MGMT)
        default: ANY
      message_node_id:
        description:
          - Identify the node in the syslog message. (HOSTNAME/IP_HOSTNAME/LAN/MGMT)
        default: LAN
      message_source:
        description:
          - The source of syslog messages to be sent to the external syslog server.
        default: ANY
      only_category_list:
        description:
          - The list of selected syslog logging categories. The appliance forwards syslog messages that belong to the selected categories.
        type: bool
      port:
        description:
          - The port this server listens on.
        default: 514
      severity:
        description:
          - The severity filter. The appliance sends log messages of the specified severity and above to the external syslog server.
        default: DEBUG
  pre_provisioning:
    description:
      - Pre-provisioning information.
    suboptions:
      hardware_info:
        description:
          - An array of structures that describe the hardware being pre-provisioned.
        suboptions:
          hwmodel:
            description:
              - Hardware model
          hwtype:
            description:
              - Hardware type.
      licenses:
        description:
          - An array of license types.
  create_token:
    description:
      - Flag for initiating a create token request for pre-provisioned members.
    type: bool
    default: False
  state:
    description:
      - Configures the intended state of the instance of the object on
        the NIOS server.  When this value is set to C(present), the object
        is configured on the device and when this value is set to C(absent)
        the value is removed (if necessary) from the device.
    default: present
    choices:
      - present
      - absent
'''

EXAMPLES = '''
- name: add a member to the grid with IPv4 address
  nios_member:
    host_name: member01.localdomain
    vip_setting:
      address: 192.168.1.100
      subnet_mask: 255.255.255.0
      gateway: 192.168.1.1
    config_addr_type: IPV4
    platform: VNIOS
    comment: "Created by Ansible"
    state: present
    provider:
      host: "{{ inventory_hostname_short }}"
      username: admin
      password: admin
  connection: local
- name: add a HA member to the grid
  nios_member:
    host_name: memberha.localdomain
    vip_setting:
      address: 192.168.1.100
      subnet_mask: 255.255.255.0
      gateway: 192.168.1.1
    config_addr_type: IPV4
    platform: VNIOS
    enable_ha: true
    router_id: 150
    node_info:
      - lan_ha_port_setting:
          ha_ip_address: 192.168.1.70
          mgmt_lan: 192.168.1.80
      - lan_ha_port_setting:
          ha_ip_address: 192.168.1.71
          mgmt_lan: 192.168.1.81
    comment: "Created by Ansible"
    state: present
    provider:
      host: "{{ inventory_hostname_short }}"
      username: admin
      password: admin
  connection: local
- name: update the member with pre-provisioning details specified
  nios_member:
    name: member01.localdomain
    pre_provisioning:
      hardware_info:
        - hwmodel: IB-VM-820
          hwtype: IB-VNIOS
      licenses:
        - dns
        - dhcp
        - enterprise
        - vnios
    comment: "Updated by Ansible"
    state: present
    provider:
      host: "{{ inventory_hostname_short }}"
      username: admin
      password: admin
  connection: local
- name: remove the member
  nios_member:
    name: member01.localdomain
    state: absent
    provider:
      host: "{{ inventory_hostname_short }}"
      username: admin
      password: admin
  connection: local
'''

RETURN = ''' # '''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.net_tools.nios.api import WapiModule
from ansible.module_utils.net_tools.nios.api import NIOS_MEMBER


def main():
    ''' Main entry point for module execution
    '''
    ipv4_spec = dict(
        address=dict(),
        subnet_mask=dict(),
        gateway=dict(),
    )

    ipv6_spec = dict(
        virtual_ip=dict(),
        cidr_prefix=dict(type='int'),
        gateway=dict(),
    )

    port_spec = dict(
        auto_port_setting_enabled=dict(type='bool'),
        duplex=dict(),
        speed=dict(),
    )

    lan2_port_spec = dict(
        enabled=dict(type='bool'),
        network_setting=dict(type='dict', elements='dict', options=ipv4_spec),
        v6_network_setting=dict(type='dict', elements='dict', options=ipv6_spec),
    )

    ha_port_spec = dict(
        ha_ip_address=dict(),
        ha_port_setting=dict(type='dict', elements='dict', options=port_spec),
        lan_port_setting=dict(type='dict', elements='dict', options=port_spec),
        mgmt_lan=dict(),
        mgmt_ipv6addr=dict(),
    )

    node_spec = dict(
        lan2_physical_setting=dict(type='dict', elements='dict', options=port_spec),
        lan_ha_port_setting=dict(type='dict', elements='dict', options=ha_port_spec),
        mgmt_network_setting=dict(type='dict', elements='dict', options=ipv4_spec),
        v6_mgmt_network_setting=dict(type='dict', elements='dict', options=ipv6_spec),
    )

    mgmt_port_spec = dict(
        enabled=dict(type='bool'),
        security_access_enabled=dict(type='bool'),
        vpn_enabled=dict(type='bool'),
    )

    syslog_spec = dict(
        address=dict(),
        category_list=dict(type='list'),
        connection_type=dict(default='UDP'),
        local_interface=dict(default='ANY'),
        message_node_id=dict(default='LAN'),
        message_source=dict(default='ANY'),
        only_category_list=dict(type='bool'),
        port=dict(type='int', default=514),
        severity=dict(default='DEBUG'),
    )

    hw_spec = dict(
        hwmodel=dict(),
        hwtype=dict(),
    )

    pre_prov_spec = dict(
        hardware_info=dict(type='list', elements='dict', options=hw_spec),
        licenses=dict(type='list'),
    )

    ib_spec = dict(
        host_name=dict(required=True, aliases=['name'], ib_req=True),
        vip_setting=dict(type='dict', elements='dict', options=ipv4_spec),
        ipv6_setting=dict(type='dict', elements='dict', options=ipv6_spec),
        config_addr_type=dict(default='IPV4'),
        comment=dict(),
        enable_ha=dict(type='bool', default=False),
        router_id=dict(type='int'),
        lan2_enabled=dict(type='bool', default=False),
        lan2_port_setting=dict(type='dict', elements='dict', options=lan2_port_spec),
        platform=dict(default='INFOBLOX'),
        node_info=dict(type='list', elements='dict', options=node_spec),
        mgmt_port_setting=dict(type='dict', elements='dict', options=mgmt_port_spec),
        upgrade_group=dict(default='Default'),
        use_syslog_proxy_setting=dict(type='bool'),
        external_syslog_server_enable=dict(type='bool'),
        syslog_servers=dict(type='list', elements='dict', options=syslog_spec),
        pre_provisioning=dict(type='dict', elements='dict', options=pre_prov_spec),
        extattrs=dict(type='dict'),
        create_token=dict(type='bool', default=False),
    )

    argument_spec = dict(
        provider=dict(required=True),
        state=dict(default='present', choices=['present', 'absent'])
    )

    argument_spec.update(ib_spec)
    argument_spec.update(WapiModule.provider_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    wapi = WapiModule(module)
    result = wapi.run(NIOS_MEMBER, ib_spec)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
