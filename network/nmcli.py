#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Chris Long <alcamie@gmail.com> <chlong@redhat.com>
#
# This file is a module for Ansible that interacts with Network Manager
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.    If not, see <http://www.gnu.org/licenses/>.


DOCUMENTATION='''
---
module: nmcli
author: "Chris Long (@alcamie101)"
short_description: Manage Networking
requirements: [ nmcli, dbus ]
version_added: "2.0"
description:
    - Manage the network devices. Create, modify, and manage, ethernet, teams, bonds, vlans etc.
options:
    state:
        required: True
        choices: [ present, absent ]
        description:
            - Whether the device should exist or not, taking action if the state is different from what is stated.
    autoconnect:
        required: False
        default: "yes"
        choices: [ "yes", "no" ]
        description:
            - Whether the connection should start on boot.
            - Whether the connection profile can be automatically activated
    conn_name:
        required: True
        description:
            - 'Where conn_name will be the name used to call the connection. when not provided a default name is generated: <type>[-<ifname>][-<num>]'
    ifname:
        required: False
        default: conn_name
        description:
            - Where IFNAME will be the what we call the interface name.
            - interface to bind the connection to. The connection will only be applicable to this interface name.
            - A special value of "*" can be used for interface-independent connections.
            - The ifname argument is mandatory for all connection types except bond, team, bridge and vlan.
    type:
        required: False
        choices: [ ethernet, team, team-slave, bond, bond-slave, bridge, vlan ]
        description:
            - This is the type of device or network connection that you wish to create.
    mode:
        required: False
        choices: [ "balance-rr", "active-backup", "balance-xor", "broadcast", "802.3ad", "balance-tlb", "balance-alb" ]
        default: balence-rr
        description:
            - This is the type of device or network connection that you wish to create for a bond, team or bridge.
    master:
        required: False
        default: None
        description:
            - master <master (ifname, or connection UUID or conn_name) of bridge, team, bond master connection profile.
    ip4:
        required: False
        default: None
        description:
            - 'The IPv4 address to this interface using this format ie: "192.0.2.24/24"'
    gw4:
        required: False
        description:
            - 'The IPv4 gateway for this interface using this format ie: "192.0.2.1"'
    dns4:
        required: False
        default: None
        description:
            - 'A list of upto 3 dns servers, ipv4 format e.g. To add two IPv4 DNS server addresses: ["192.0.2.53", "198.51.100.53"]'
    ip6:
        required: False
        default: None
        description:
            - 'The IPv6 address to this interface using this format ie: "abbe::cafe"'
    gw6:
        required: False
        default: None
        description:
            - 'The IPv6 gateway for this interface using this format ie: "2001:db8::1"'
    dns6:
        required: False
        description:
            - 'A list of upto 3 dns servers, ipv6 format e.g. To add two IPv6 DNS server addresses: ["2001:4860:4860::8888 2001:4860:4860::8844"]'
    mtu:
        required: False
        default: 1500
        description:
            - The connection MTU, e.g. 9000. This can't be applied when creating the interface and is done once the interface has been created.
            - Can be used when modifying Team, VLAN, Ethernet (Future plans to implement wifi, pppoe, infiniband)
    primary:
        required: False
        default: None
        description:
            - This is only used with bond and is the primary interface name (for "active-backup" mode), this is the usually the 'ifname'
    miimon:
        required: False
        default: 100
        description:
            - This is only used with bond - miimon
    downdelay:
        required: False
        default: None
        description:
            - This is only used with bond - downdelay
    updelay:
        required: False
        default: None
        description:
            - This is only used with bond - updelay
    arp_interval:
        required: False
        default: None
        description:
            - This is only used with bond - ARP interval
    arp_ip_target:
        required: False
        default: None
        description:
            - This is only used with bond - ARP IP target
    stp:
        required: False
        default: None
        description:
            - This is only used with bridge and controls whether Spanning Tree Protocol (STP) is enabled for this bridge
    priority:
        required: False
        default: 128
        description:
            - This is only used with 'bridge' - sets STP priority
    forwarddelay:
        required: False
        default: 15
        description:
            - This is only used with bridge - [forward-delay <2-30>] STP forwarding delay, in seconds
    hellotime:
        required: False
        default: 2
        description:
            - This is only used with bridge - [hello-time <1-10>] STP hello time, in seconds
    maxage:
        required: False
        default: 20
        description:
            - This is only used with bridge - [max-age <6-42>] STP maximum message age, in seconds
    ageingtime:
        required: False
        default: 300
        description:
            - This is only used with bridge - [ageing-time <0-1000000>] the Ethernet MAC address aging time, in seconds
    mac:
        required: False
        default: None
        description:
            - 'This is only used with bridge - MAC address of the bridge (note: this requires a recent kernel feature, originally introduced in 3.15 upstream kernel)'
    slavepriority:
        required: False
        default: 32
        description:
            - This is only used with 'bridge-slave' - [<0-63>] - STP priority of this slave
    path_cost:
        required: False
        default: 100
        description:
            - This is only used with 'bridge-slave' - [<1-65535>] - STP port cost for destinations via this slave
    hairpin:
        required: False
        default: yes
        description:
            - This is only used with 'bridge-slave' - 'hairpin mode' for the slave, which allows frames to be sent back out through the slave the frame was received on.
    vlanid:
        required: False
        default: None
        description:
            - This is only used with VLAN - VLAN ID in range <0-4095>
    vlandev:
        required: False
        default: None
        description:
            - This is only used with VLAN - parent device this VLAN is on, can use ifname
    flags:
        required: False
        default: None
        description:
            - This is only used with VLAN - flags
    ingress:
        required: False
        default: None
        description:
            - This is only used with VLAN - VLAN ingress priority mapping
    egress:
        required: False
        default: None
        description:
            - This is only used with VLAN - VLAN egress priority mapping

'''

EXAMPLES='''
The following examples are working examples that I have run in the field. I followed follow the structure:
```
|_/inventory/cloud-hosts
|           /group_vars/openstack-stage.yml
|           /host_vars/controller-01.openstack.host.com
|           /host_vars/controller-02.openstack.host.com
|_/playbook/library/nmcli.py
|          /playbook-add.yml
|          /playbook-del.yml
```

## inventory examples
### groups_vars
```yml
---
#devops_os_define_network
storage_gw: "192.0.2.254"
external_gw: "198.51.100.254"
tenant_gw: "203.0.113.254"

#Team vars
nmcli_team:
    - {conn_name: 'tenant', ip4: "{{tenant_ip}}", gw4: "{{tenant_gw}}"}
    - {conn_name: 'external', ip4: "{{external_ip}}", gw4: "{{external_gw}}"}
    - {conn_name: 'storage', ip4: "{{storage_ip}}", gw4: "{{storage_gw}}"}
nmcli_team_slave:
    - {conn_name: 'em1', ifname: 'em1', master: 'tenant'}
    - {conn_name: 'em2', ifname: 'em2', master: 'tenant'}
    - {conn_name: 'p2p1', ifname: 'p2p1', master: 'storage'}
    - {conn_name: 'p2p2', ifname: 'p2p2', master: 'external'}

#bond vars
nmcli_bond:
    - {conn_name: 'tenant', ip4: "{{tenant_ip}}", gw4: '', mode: 'balance-rr'}
    - {conn_name: 'external', ip4: "{{external_ip}}", gw4: '', mode: 'balance-rr'}
    - {conn_name: 'storage', ip4: "{{storage_ip}}", gw4: "{{storage_gw}}", mode: 'balance-rr'}
nmcli_bond_slave:
    - {conn_name: 'em1', ifname: 'em1', master: 'tenant'}
    - {conn_name: 'em2', ifname: 'em2', master: 'tenant'}
    - {conn_name: 'p2p1', ifname: 'p2p1', master: 'storage'}
    - {conn_name: 'p2p2', ifname: 'p2p2', master: 'external'}

#ethernet vars
nmcli_ethernet:
    - {conn_name: 'em1', ifname: 'em1', ip4: "{{tenant_ip}}", gw4: "{{tenant_gw}}"}
    - {conn_name: 'em2', ifname: 'em2', ip4: "{{tenant_ip1}}", gw4: "{{tenant_gw}}"}
    - {conn_name: 'p2p1', ifname: 'p2p1', ip4: "{{storage_ip}}", gw4: "{{storage_gw}}"}
    - {conn_name: 'p2p2', ifname: 'p2p2', ip4: "{{external_ip}}", gw4: "{{external_gw}}"}
```

### host_vars
```yml
---
storage_ip: "192.0.2.91/23"
external_ip: "198.51.100.23/21"
tenant_ip: "203.0.113.77/23"
```



## playbook-add.yml example

```yml
---
- hosts: openstack-stage
  remote_user: root
  tasks:

- name: install needed network manager libs
  yum: name={{ item }} state=installed
  with_items:
    - NetworkManager-glib
    - libnm-qt-devel.x86_64
    - nm-connection-editor.x86_64
    - libsemanage-python
    - policycoreutils-python

##### Working with all cloud nodes - Teaming
  - name: try nmcli add team - conn_name only & ip4 gw4
    nmcli: type=team conn_name={{item.conn_name}} ip4={{item.ip4}} gw4={{item.gw4}} state=present
    with_items:
      - "{{nmcli_team}}"

  - name: try nmcli add teams-slave
    nmcli: type=team-slave conn_name={{item.conn_name}} ifname={{item.ifname}} master={{item.master}} state=present
    with_items:
      - "{{nmcli_team_slave}}"

###### Working with all cloud nodes - Bonding
#  - name: try nmcli add bond - conn_name only & ip4 gw4 mode
#    nmcli: type=bond conn_name={{item.conn_name}} ip4={{item.ip4}} gw4={{item.gw4}} mode={{item.mode}} state=present
#    with_items:
#      - "{{nmcli_bond}}"
#
#  - name: try nmcli add bond-slave
#    nmcli: type=bond-slave conn_name={{item.conn_name}} ifname={{item.ifname}} master={{item.master}} state=present
#    with_items:
#      - "{{nmcli_bond_slave}}"

##### Working with all cloud nodes - Ethernet
#  - name: nmcli add Ethernet - conn_name only & ip4 gw4
#    nmcli: type=ethernet conn_name={{item.conn_name}} ip4={{item.ip4}} gw4={{item.gw4}} state=present
#    with_items:
#      - "{{nmcli_ethernet}}"
```

## playbook-del.yml example

```yml
---
- hosts: openstack-stage
  remote_user: root
  tasks:

  - name: try nmcli del team - multiple
    nmcli: conn_name={{item.conn_name}} state=absent
    with_items:
      - { conn_name: 'em1'}
      - { conn_name: 'em2'}
      - { conn_name: 'p1p1'}
      - { conn_name: 'p1p2'}
      - { conn_name: 'p2p1'}
      - { conn_name: 'p2p2'}
      - { conn_name: 'tenant'}
      - { conn_name: 'storage'}
      - { conn_name: 'external'}
      - { conn_name: 'team-em1'}
      - { conn_name: 'team-em2'}
      - { conn_name: 'team-p1p1'}
      - { conn_name: 'team-p1p2'}
      - { conn_name: 'team-p2p1'}
      - { conn_name: 'team-p2p2'}
```
# To add an Ethernet connection with static IP configuration, issue a command as follows
- nmcli: conn_name=my-eth1 ifname=eth1 type=ethernet ip4=192.0.2.100/24 gw4=192.0.2.1 state=present

# To add an Team connection with static IP configuration, issue a command as follows
- nmcli: conn_name=my-team1 ifname=my-team1 type=team ip4=192.0.2.100/24 gw4=192.0.2.1 state=present autoconnect=yes

# Optionally, at the same time specify IPv6 addresses for the device as follows:
- nmcli: conn_name=my-eth1 ifname=eth1 type=ethernet ip4=192.0.2.100/24 gw4=192.0.2.1 ip6=2001:db8::cafe gw6=2001:db8::1 state=present

# To add two IPv4 DNS server addresses:
-nmcli: conn_name=my-eth1 dns4=["192.0.2.53", "198.51.100.53"] state=present

# To make a profile usable for all compatible Ethernet interfaces, issue a command as follows
- nmcli: ctype=ethernet name=my-eth1 ifname="*" state=present

# To change the property of a setting e.g. MTU, issue a command as follows:
- nmcli: conn_name=my-eth1 mtu=9000 type=ethernet state=present

    Exit Status's:
        - nmcli exits with status 0 if it succeeds, a value greater than 0 is
        returned if an error occurs.
        - 0 Success - indicates the operation succeeded
        - 1 Unknown or unspecified error
        - 2 Invalid user input, wrong nmcli invocation
        - 3 Timeout expired (see --wait option)
        - 4 Connection activation failed
        - 5 Connection deactivation failed
        - 6 Disconnecting device failed
        - 7 Connection deletion failed
        - 8 NetworkManager is not running
        - 9 nmcli and NetworkManager versions mismatch
        - 10 Connection, device, or access point does not exist.
'''
# import ansible.module_utils.basic
import os
import sys
HAVE_DBUS=False
try:
    import dbus
    HAVE_DBUS=True
except ImportError:
    pass

HAVE_NM_CLIENT=False
try:
    from gi.repository import NetworkManager, NMClient
    HAVE_NM_CLIENT=True
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule


class Nmcli(object):
    """
    This is the generic nmcli manipulation class that is subclassed based on platform.
    A subclass may wish to override the following action methods:-
            - create_connection()
            - delete_connection()
            - modify_connection()
            - show_connection()
            - up_connection()
            - down_connection()
    All subclasses MUST define platform and distribution (which may be None).
    """

    platform='Generic'
    distribution=None
    bus=dbus.SystemBus()
    # The following is going to be used in dbus code
    DEVTYPES={1: "Ethernet",
                   2: "Wi-Fi",
                   5: "Bluetooth",
                   6: "OLPC",
                   7: "WiMAX",
                   8: "Modem",
                   9: "InfiniBand",
                   10: "Bond",
                   11: "VLAN",
                   12: "ADSL",
                   13: "Bridge",
                   14: "Generic",
                   15: "Team"
                }
    STATES={0: "Unknown",
                 10: "Unmanaged",
                 20: "Unavailable",
                 30: "Disconnected",
                 40: "Prepare",
                 50: "Config",
                 60: "Need Auth",
                 70: "IP Config",
                 80: "IP Check",
                 90: "Secondaries",
                 100: "Activated",
                 110: "Deactivating",
                 120: "Failed"
            }


    def __init__(self, module):
        self.module=module
        self.state=module.params['state']
        self.autoconnect=module.params['autoconnect']
        self.conn_name=module.params['conn_name']
        self.master=module.params['master']
        self.ifname=module.params['ifname']
        self.type=module.params['type']
        self.ip4=module.params['ip4']
        self.gw4=module.params['gw4']
        self.dns4=module.params['dns4']
        self.ip6=module.params['ip6']
        self.gw6=module.params['gw6']
        self.dns6=module.params['dns6']
        self.mtu=module.params['mtu']
        self.stp=module.params['stp']
        self.priority=module.params['priority']
        self.mode=module.params['mode']
        self.miimon=module.params['miimon']
        self.downdelay=module.params['downdelay']
        self.updelay=module.params['updelay']
        self.arp_interval=module.params['arp_interval']
        self.arp_ip_target=module.params['arp_ip_target']
        self.slavepriority=module.params['slavepriority']
        self.forwarddelay=module.params['forwarddelay']
        self.hellotime=module.params['hellotime']
        self.maxage=module.params['maxage']
        self.ageingtime=module.params['ageingtime']
        self.mac=module.params['mac']
        self.vlanid=module.params['vlanid']
        self.vlandev=module.params['vlandev']
        self.flags=module.params['flags']
        self.ingress=module.params['ingress']
        self.egress=module.params['egress']

    def execute_command(self, cmd, use_unsafe_shell=False, data=None):
        return self.module.run_command(cmd, use_unsafe_shell=use_unsafe_shell, data=data)

    def merge_secrets(self, proxy, config, setting_name):
        try:
            # returns a dict of dicts mapping name::setting, where setting is a dict
            # mapping key::value.  Each member of the 'setting' dict is a secret
            secrets=proxy.GetSecrets(setting_name)

            # Copy the secrets into our connection config
            for setting in secrets:
                for key in secrets[setting]:
                    config[setting_name][key]=secrets[setting][key]
        except Exception as e:
            pass

    def dict_to_string(self, d):
        # Try to trivially translate a dictionary's elements into nice string
        # formatting.
        dstr=""
        for key in d:
            val=d[key]
            str_val=""
            add_string=True
            if isinstance(val, dbus.Array):
                for elt in val:
                    if isinstance(elt, dbus.Byte):
                        str_val+="%s " % int(elt)
                    elif isinstance(elt, dbus.String):
                        str_val+="%s" % elt
            elif isinstance(val, dbus.Dictionary):
                dstr+=self.dict_to_string(val)
                add_string=False
            else:
                str_val=val
            if add_string:
                dstr+="%s: %s\n" % ( key, str_val)
        return dstr

    def connection_to_string(self, config):
        # dump a connection configuration to use in list_connection_info
        setting_list=[]
        for setting_name in config:
            setting_list.append(self.dict_to_string(config[setting_name]))
        return setting_list
        # print ""

    def bool_to_string(self, boolean):
        if boolean:
            return "yes"
        else:
            return "no"

    def list_connection_info(self):
        # Ask the settings service for the list of connections it provides
        bus=dbus.SystemBus()

        service_name="org.freedesktop.NetworkManager"
        proxy=bus.get_object(service_name, "/org/freedesktop/NetworkManager/Settings")
        settings=dbus.Interface(proxy, "org.freedesktop.NetworkManager.Settings")
        connection_paths=settings.ListConnections()
        connection_list=[]
        # List each connection's name, UUID, and type
        for path in connection_paths:
            con_proxy=bus.get_object(service_name, path)
            settings_connection=dbus.Interface(con_proxy, "org.freedesktop.NetworkManager.Settings.Connection")
            config=settings_connection.GetSettings()

            # Now get secrets too; we grab the secrets for each type of connection
            # (since there isn't a "get all secrets" call because most of the time
            # you only need 'wifi' secrets or '802.1x' secrets, not everything) and
            # merge that into the configuration data - To use at a later stage
            self.merge_secrets(settings_connection, config, '802-11-wireless')
            self.merge_secrets(settings_connection, config, '802-11-wireless-security')
            self.merge_secrets(settings_connection, config, '802-1x')
            self.merge_secrets(settings_connection, config, 'gsm')
            self.merge_secrets(settings_connection, config, 'cdma')
            self.merge_secrets(settings_connection, config, 'ppp')

            # Get the details of the 'connection' setting
            s_con=config['connection']
            connection_list.append(s_con['id'])
            connection_list.append(s_con['uuid'])
            connection_list.append(s_con['type'])
            connection_list.append(self.connection_to_string(config))
        return connection_list

    def connection_exists(self):
        # we are going to use name and type in this instance to find if that connection exists and is of type x
        connections=self.list_connection_info()

        for con_item in connections:
            if self.conn_name==con_item:
                return True

    def down_connection(self):
        cmd=[self.module.get_bin_path('nmcli', True)]
        # if self.connection_exists():
        cmd.append('con')
        cmd.append('down')
        cmd.append(self.conn_name)
        return self.execute_command(cmd)

    def up_connection(self):
        cmd=[self.module.get_bin_path('nmcli', True)]
        cmd.append('con')
        cmd.append('up')
        cmd.append(self.conn_name)
        return self.execute_command(cmd)

    def create_connection_team(self):
        cmd=[self.module.get_bin_path('nmcli', True)]
        # format for creating team interface
        cmd.append('con')
        cmd.append('add')
        cmd.append('type')
        cmd.append('team')
        cmd.append('con-name')
        if self.conn_name is not None:
            cmd.append(self.conn_name)
        elif self.ifname is not None:
            cmd.append(self.ifname)
        cmd.append('ifname')
        if self.ifname is not None:
            cmd.append(self.ifname)
        elif self.conn_name is not None:
            cmd.append(self.conn_name)
        if self.ip4 is not None:
            cmd.append('ip4')
            cmd.append(self.ip4)
        if self.gw4 is not None:
            cmd.append('gw4')
            cmd.append(self.gw4)
        if self.ip6 is not None:
            cmd.append('ip6')
            cmd.append(self.ip6)
        if self.gw6 is not None:
            cmd.append('gw6')
            cmd.append(self.gw6)
        if self.autoconnect is not None:
            cmd.append('autoconnect')
            cmd.append(self.bool_to_string(self.autoconnect))
        return cmd

    def modify_connection_team(self):
        cmd=[self.module.get_bin_path('nmcli', True)]
        # format for modifying team interface
        cmd.append('con')
        cmd.append('mod')
        cmd.append(self.conn_name)
        if self.ip4 is not None:
            cmd.append('ipv4.address')
            cmd.append(self.ip4)
        if self.gw4 is not None:
            cmd.append('ipv4.gateway')
            cmd.append(self.gw4)
        if self.dns4 is not None:
            cmd.append('ipv4.dns')
            cmd.append(self.dns4)
        if self.ip6 is not None:
            cmd.append('ipv6.address')
            cmd.append(self.ip6)
        if self.gw6 is not None:
            cmd.append('ipv6.gateway')
            cmd.append(self.gw6)
        if self.dns6 is not None:
            cmd.append('ipv6.dns')
            cmd.append(self.dns6)
        if self.autoconnect is not None:
            cmd.append('autoconnect')
            cmd.append(self.bool_to_string(self.autoconnect))
            # Can't use MTU with team
        return cmd

    def create_connection_team_slave(self):
        cmd=[self.module.get_bin_path('nmcli', True)]
        # format for creating team-slave interface
        cmd.append('connection')
        cmd.append('add')
        cmd.append('type')
        cmd.append(self.type)
        cmd.append('con-name')
        if self.conn_name is not None:
            cmd.append(self.conn_name)
        elif self.ifname is not None:
            cmd.append(self.ifname)
        cmd.append('ifname')
        if self.ifname is not None:
            cmd.append(self.ifname)
        elif self.conn_name is not None:
            cmd.append(self.conn_name)
        cmd.append('master')
        if self.conn_name is not None:
            cmd.append(self.master)
        # if self.mtu is not None:
        #     cmd.append('802-3-ethernet.mtu')
        #     cmd.append(self.mtu)
        return cmd

    def modify_connection_team_slave(self):
        cmd=[self.module.get_bin_path('nmcli', True)]
        # format for modifying team-slave interface
        cmd.append('con')
        cmd.append('mod')
        cmd.append(self.conn_name)
        cmd.append('connection.master')
        cmd.append(self.master)
        if self.mtu is not None:
            cmd.append('802-3-ethernet.mtu')
            cmd.append(self.mtu)
        return cmd

    def create_connection_bond(self):
        cmd=[self.module.get_bin_path('nmcli', True)]
        # format for creating bond interface
        cmd.append('con')
        cmd.append('add')
        cmd.append('type')
        cmd.append('bond')
        cmd.append('con-name')
        if self.conn_name is not None:
            cmd.append(self.conn_name)
        elif self.ifname is not None:
            cmd.append(self.ifname)
        cmd.append('ifname')
        if self.ifname is not None:
            cmd.append(self.ifname)
        elif self.conn_name is not None:
            cmd.append(self.conn_name)
        if self.ip4 is not None:
            cmd.append('ip4')
            cmd.append(self.ip4)
        if self.gw4 is not None:
            cmd.append('gw4')
            cmd.append(self.gw4)
        if self.ip6 is not None:
            cmd.append('ip6')
            cmd.append(self.ip6)
        if self.gw6 is not None:
            cmd.append('gw6')
            cmd.append(self.gw6)
        if self.autoconnect is not None:
            cmd.append('autoconnect')
            cmd.append(self.bool_to_string(self.autoconnect))
        if self.mode is not None:
            cmd.append('mode')
            cmd.append(self.mode)
        if self.miimon is not None:
            cmd.append('miimon')
            cmd.append(self.miimon)
        if self.downdelay is not None:
            cmd.append('downdelay')
            cmd.append(self.downdelay)
        if self.downdelay is not None:
            cmd.append('updelay')
            cmd.append(self.updelay)
        if self.downdelay is not None:
            cmd.append('arp-interval')
            cmd.append(self.arp_interval)
        if self.downdelay is not None:
            cmd.append('arp-ip-target')
            cmd.append(self.arp_ip_target)
        return cmd

    def modify_connection_bond(self):
        cmd=[self.module.get_bin_path('nmcli', True)]
        # format for modifying bond interface
        cmd.append('con')
        cmd.append('mod')
        cmd.append(self.conn_name)
        if self.ip4 is not None:
            cmd.append('ipv4.address')
            cmd.append(self.ip4)
        if self.gw4 is not None:
            cmd.append('ipv4.gateway')
            cmd.append(self.gw4)
        if self.dns4 is not None:
            cmd.append('ipv4.dns')
            cmd.append(self.dns4)
        if self.ip6 is not None:
            cmd.append('ipv6.address')
            cmd.append(self.ip6)
        if self.gw6 is not None:
            cmd.append('ipv6.gateway')
            cmd.append(self.gw6)
        if self.dns6 is not None:
            cmd.append('ipv6.dns')
            cmd.append(self.dns6)
        if self.autoconnect is not None:
            cmd.append('autoconnect')
            cmd.append(self.bool_to_string(self.autoconnect))
        return cmd

    def create_connection_bond_slave(self):
        cmd=[self.module.get_bin_path('nmcli', True)]
        # format for creating bond-slave interface
        cmd.append('connection')
        cmd.append('add')
        cmd.append('type')
        cmd.append('bond-slave')
        cmd.append('con-name')
        if self.conn_name is not None:
            cmd.append(self.conn_name)
        elif self.ifname is not None:
            cmd.append(self.ifname)
        cmd.append('ifname')
        if self.ifname is not None:
            cmd.append(self.ifname)
        elif self.conn_name is not None:
            cmd.append(self.conn_name)
        cmd.append('master')
        if self.conn_name is not None:
            cmd.append(self.master)
        return cmd

    def modify_connection_bond_slave(self):
        cmd=[self.module.get_bin_path('nmcli', True)]
        # format for modifying bond-slave interface
        cmd.append('con')
        cmd.append('mod')
        cmd.append(self.conn_name)
        cmd.append('connection.master')
        cmd.append(self.master)
        return cmd

    def create_connection_ethernet(self):
        cmd=[self.module.get_bin_path('nmcli', True)]
        # format for creating ethernet interface
        # To add an Ethernet connection with static IP configuration, issue a command as follows
        # - nmcli: name=add conn_name=my-eth1 ifname=eth1 type=ethernet ip4=192.0.2.100/24 gw4=192.0.2.1 state=present
        # nmcli con add con-name my-eth1 ifname eth1 type ethernet ip4 192.0.2.100/24 gw4 192.0.2.1
        cmd.append('con')
        cmd.append('add')
        cmd.append('type')
        cmd.append('ethernet')
        cmd.append('con-name')
        if self.conn_name is not None:
            cmd.append(self.conn_name)
        elif self.ifname is not None:
            cmd.append(self.ifname)
        cmd.append('ifname')
        if self.ifname is not None:
            cmd.append(self.ifname)
        elif self.conn_name is not None:
            cmd.append(self.conn_name)
        if self.ip4 is not None:
            cmd.append('ip4')
            cmd.append(self.ip4)
        if self.gw4 is not None:
            cmd.append('gw4')
            cmd.append(self.gw4)
        if self.ip6 is not None:
            cmd.append('ip6')
            cmd.append(self.ip6)
        if self.gw6 is not None:
            cmd.append('gw6')
            cmd.append(self.gw6)
        if self.autoconnect is not None:
            cmd.append('autoconnect')
            cmd.append(self.bool_to_string(self.autoconnect))
        return cmd

    def modify_connection_ethernet(self):
        cmd=[self.module.get_bin_path('nmcli', True)]
        # format for  modifying ethernet interface
        # To add an Ethernet connection with static IP configuration, issue a command as follows
        # - nmcli: name=add conn_name=my-eth1 ifname=eth1 type=ethernet ip4=192.0.2.100/24 gw4=192.0.2.1 state=present
        # nmcli con add con-name my-eth1 ifname eth1 type ethernet ip4 192.0.2.100/24 gw4 192.0.2.1
        cmd.append('con')
        cmd.append('mod')
        cmd.append(self.conn_name)
        if self.ip4 is not None:
            cmd.append('ipv4.address')
            cmd.append(self.ip4)
        if self.gw4 is not None:
            cmd.append('ipv4.gateway')
            cmd.append(self.gw4)
        if self.dns4 is not None:
            cmd.append('ipv4.dns')
            cmd.append(self.dns4)
        if self.ip6 is not None:
            cmd.append('ipv6.address')
            cmd.append(self.ip6)
        if self.gw6 is not None:
            cmd.append('ipv6.gateway')
            cmd.append(self.gw6)
        if self.dns6 is not None:
            cmd.append('ipv6.dns')
            cmd.append(self.dns6)
        if self.mtu is not None:
            cmd.append('802-3-ethernet.mtu')
            cmd.append(self.mtu)
        if self.autoconnect is not None:
            cmd.append('autoconnect')
            cmd.append(self.bool_to_string(self.autoconnect))
        return cmd

    def create_connection_bridge(self):
        cmd=[self.module.get_bin_path('nmcli', True)]
        # format for creating bridge interface
        return cmd

    def modify_connection_bridge(self):
        cmd=[self.module.get_bin_path('nmcli', True)]
        # format for modifying bridge interface
        return cmd

    def create_connection_vlan(self):
        cmd=[self.module.get_bin_path('nmcli', True)]
        # format for creating ethernet interface
        return cmd

    def modify_connection_vlan(self):
        cmd=[self.module.get_bin_path('nmcli', True)]
        # format for modifying ethernet interface
        return cmd

    def create_connection(self):
        cmd=[]
        if self.type=='team':
            # cmd=self.create_connection_team()
            if (self.dns4 is not None) or (self.dns6 is not None):
                cmd=self.create_connection_team()
                self.execute_command(cmd)
                cmd=self.modify_connection_team()
                self.execute_command(cmd)
                cmd=self.up_connection()
                return self.execute_command(cmd)
            elif (self.dns4 is None) or (self.dns6 is None):
                cmd=self.create_connection_team()
                return self.execute_command(cmd)
        elif self.type=='team-slave':
            if self.mtu is not None:
                cmd=self.create_connection_team_slave()
                self.execute_command(cmd)
                cmd=self.modify_connection_team_slave()
                self.execute_command(cmd)
                # cmd=self.up_connection()
                return self.execute_command(cmd)
            else:
                cmd=self.create_connection_team_slave()
                return self.execute_command(cmd)
        elif self.type=='bond':
            if (self.mtu is not None) or (self.dns4 is not None) or (self.dns6 is not None):
                cmd=self.create_connection_bond()
                self.execute_command(cmd)
                cmd=self.modify_connection_bond()
                self.execute_command(cmd)
                cmd=self.up_connection()
                return self.execute_command(cmd)
            else:
                cmd=self.create_connection_bond()
                return self.execute_command(cmd)
        elif self.type=='bond-slave':
            cmd=self.create_connection_bond_slave()
        elif self.type=='ethernet':
            if (self.mtu is not None) or (self.dns4 is not None) or (self.dns6 is not None):
                cmd=self.create_connection_ethernet()
                self.execute_command(cmd)
                cmd=self.modify_connection_ethernet()
                self.execute_command(cmd)
                cmd=self.up_connection()
                return self.execute_command(cmd)
            else:
                cmd=self.create_connection_ethernet()
                return self.execute_command(cmd)
        elif self.type=='bridge':
            cmd=self.create_connection_bridge()
        elif self.type=='vlan':
            cmd=self.create_connection_vlan()
        return self.execute_command(cmd)

    def remove_connection(self):
        # self.down_connection()
        cmd=[self.module.get_bin_path('nmcli', True)]
        cmd.append('con')
        cmd.append('del')
        cmd.append(self.conn_name)
        return self.execute_command(cmd)

    def modify_connection(self):
        cmd=[]
        if self.type=='team':
            cmd=self.modify_connection_team()
        elif self.type=='team-slave':
            cmd=self.modify_connection_team_slave()
        elif self.type=='bond':
            cmd=self.modify_connection_bond()
        elif self.type=='bond-slave':
            cmd=self.modify_connection_bond_slave()
        elif self.type=='ethernet':
            cmd=self.modify_connection_ethernet()
        elif self.type=='bridge':
            cmd=self.modify_connection_bridge()
        elif self.type=='vlan':
            cmd=self.modify_connection_vlan()
        return self.execute_command(cmd)


def main():
    # Parsing argument file
    module=AnsibleModule(
        argument_spec=dict(
            autoconnect=dict(required=False, default=None, type='bool'),
            state=dict(required=True, choices=['present', 'absent'], type='str'),
            conn_name=dict(required=True, type='str'),
            master=dict(required=False, default=None, type='str'),
            ifname=dict(required=False, default=None, type='str'),
            type=dict(required=False, default=None, choices=['ethernet', 'team', 'team-slave', 'bond', 'bond-slave', 'bridge', 'vlan'], type='str'),
            ip4=dict(required=False, default=None, type='str'),
            gw4=dict(required=False, default=None, type='str'),
            dns4=dict(required=False, default=None, type='str'),
            ip6=dict(required=False, default=None, type='str'),
            gw6=dict(required=False, default=None, type='str'),
            dns6=dict(required=False, default=None, type='str'),
            # Bond Specific vars
            mode=dict(require=False, default="balance-rr", choices=["balance-rr", "active-backup", "balance-xor", "broadcast", "802.3ad", "balance-tlb", "balance-alb"], type='str'),
            miimon=dict(required=False, default=None, type='str'),
            downdelay=dict(required=False, default=None, type='str'),
            updelay=dict(required=False, default=None, type='str'),
            arp_interval=dict(required=False, default=None, type='str'),
            arp_ip_target=dict(required=False, default=None, type='str'),
            # general usage
            mtu=dict(required=False, default=None, type='str'),
            mac=dict(required=False, default=None, type='str'),
            # bridge specific vars
            stp=dict(required=False, default=True, type='bool'),
            priority=dict(required=False, default="128", type='str'),
            slavepriority=dict(required=False, default="32", type='str'),
            forwarddelay=dict(required=False, default="15", type='str'),
            hellotime=dict(required=False, default="2", type='str'),
            maxage=dict(required=False, default="20", type='str'),
            ageingtime=dict(required=False, default="300", type='str'),
            # vlan specific vars
            vlanid=dict(required=False, default=None, type='str'),
            vlandev=dict(required=False, default=None, type='str'),
            flags=dict(required=False, default=None, type='str'),
            ingress=dict(required=False, default=None, type='str'),
            egress=dict(required=False, default=None, type='str'),
        ),
        supports_check_mode=True
    )

    if not HAVE_DBUS:
        module.fail_json(msg="This module requires dbus python bindings")

    if not HAVE_NM_CLIENT:
        module.fail_json(msg="This module requires NetworkManager glib API")

    nmcli=Nmcli(module)

    rc=None
    out=''
    err=''
    result={}
    result['conn_name']=nmcli.conn_name
    result['state']=nmcli.state

    # check for issues
    if nmcli.conn_name is None:
        nmcli.module.fail_json(msg="You haven't specified a name for the connection")
    # team-slave checks
    if nmcli.type=='team-slave' and nmcli.master is None:
        nmcli.module.fail_json(msg="You haven't specified a name for the master so we're not changing a thing")
    if nmcli.type=='team-slave' and nmcli.ifname is None:
        nmcli.module.fail_json(msg="You haven't specified a name for the connection")

    if nmcli.state=='absent':
        if nmcli.connection_exists():
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err)=nmcli.down_connection()
            (rc, out, err)=nmcli.remove_connection()
        if rc!=0:
            module.fail_json(name =('No Connection named %s exists' % nmcli.conn_name), msg=err, rc=rc)

    elif nmcli.state=='present':
        if nmcli.connection_exists():
            # modify connection (note: this function is check mode aware)
            # result['Connection']=('Connection %s of Type %s is not being added' % (nmcli.conn_name, nmcli.type))
            result['Exists']='Connections do exist so we are modifying them'
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err)=nmcli.modify_connection()
        if not nmcli.connection_exists():
            result['Connection']=('Connection %s of Type %s is being added' % (nmcli.conn_name, nmcli.type))
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err)=nmcli.create_connection()
        if rc is not None and rc!=0:
            module.fail_json(name=nmcli.conn_name, msg=err, rc=rc)

    if rc is None:
        result['changed']=False
    else:
        result['changed']=True
    if out:
        result['stdout']=out
    if err:
        result['stderr']=err

    module.exit_json(**result)

main()
