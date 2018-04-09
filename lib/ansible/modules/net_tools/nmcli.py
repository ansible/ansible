#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2015, Chris Long <alcamie@gmail.com> <chlong@redhat.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: nmcli
author: "Chris Long (@alcamie101)"
short_description: Manage Networking
requirements: [ nmcli, dbus, NetworkManager-glib ]
version_added: "2.0"
description:
    - Manage the network devices. Create, modify and manage various connection and device type e.g., ethernet, teams, bonds, vlans etc.
    - "On CentOS and Fedora like systems, install dependencies as 'yum/dnf install -y python-gobject NetworkManager-glib'"
    - "On Ubuntu and Debian like systems, install dependencies as 'apt-get install -y libnm-glib-dev'"
options:
    state:
        description:
            - Whether the device should exist or not, taking action if the state is different from what is stated.
        required: True
        choices: [ present, absent ]
    autoconnect:
        description:
            - Whether the connection should start on boot.
            - Whether the connection profile can be automatically activated
        type: bool
        default: True
    conn_name:
        description:
            - 'Where conn_name will be the name used to call the connection. when not provided a default name is generated: <type>[-<ifname>][-<num>]'
        required: True
    ifname:
        description:
            - Where IFNAME will be the what we call the interface name.
            - interface to bind the connection to. The connection will only be applicable to this interface name.
            - A special value of "*" can be used for interface-independent connections.
            - The ifname argument is mandatory for all connection types except bond, team, bridge and vlan.
        default: conn_name
    type:
        description:
            - This is the type of device or network connection that you wish to create or modify.
            - "type C(generic) is added in version 2.5."
        choices: [ ethernet, team, team-slave, bond, bond-slave, bridge, bridge-slave, vlan, generic ]
    mode:
        description:
            - This is the type of device or network connection that you wish to create for a bond, team or bridge.
        choices: [ "balance-rr", "active-backup", "balance-xor", "broadcast", "802.3ad", "balance-tlb", "balance-alb" ]
        default: balence-rr
    master:
        description:
            - master <master (ifname, or connection UUID or conn_name) of bridge, team, bond master connection profile.
    ip4:
        description:
            - 'The IPv4 address to this interface using this format ie: "192.0.2.24/24"'
    gw4:
        description:
            - 'The IPv4 gateway for this interface using this format ie: "192.0.2.1"'
    dns4:
        description:
            - 'A list of upto 3 dns servers, ipv4 format e.g. To add two IPv4 DNS server addresses: "192.0.2.53 198.51.100.53"'
    dns4_search:
        description:
            - 'A list of DNS search domains.'
        version_added: 2.5
    ip6:
        description:
            - 'The IPv6 address to this interface using this format ie: "abbe::cafe"'
    gw6:
        description:
            - 'The IPv6 gateway for this interface using this format ie: "2001:db8::1"'
    dns6:
        description:
            - 'A list of upto 3 dns servers, ipv6 format e.g. To add two IPv6 DNS server addresses: "2001:4860:4860::8888 2001:4860:4860::8844"'
    dns6_search:
        description:
            - 'A list of DNS search domains.'
        version_added: 2.5
    mtu:
        description:
            - The connection MTU, e.g. 9000. This can't be applied when creating the interface and is done once the interface has been created.
            - Can be used when modifying Team, VLAN, Ethernet (Future plans to implement wifi, pppoe, infiniband)
        default: 1500
    dhcp_client_id:
        description:
            - DHCP Client Identifier sent to the DHCP server.
        version_added: "2.5"
    primary:
        description:
            - This is only used with bond and is the primary interface name (for "active-backup" mode), this is the usually the 'ifname'
    miimon:
        description:
            - This is only used with bond - miimon
        default: 100
    downdelay:
        description:
            - This is only used with bond - downdelay
    updelay:
        description:
            - This is only used with bond - updelay
    arp_interval:
        description:
            - This is only used with bond - ARP interval
    arp_ip_target:
        description:
            - This is only used with bond - ARP IP target
    stp:
        description:
            - This is only used with bridge and controls whether Spanning Tree Protocol (STP) is enabled for this bridge
        type: bool
    priority:
        description:
            - This is only used with 'bridge' - sets STP priority
        default: 128
    forwarddelay:
        description:
            - This is only used with bridge - [forward-delay <2-30>] STP forwarding delay, in seconds
        default: 15
    hellotime:
        description:
            - This is only used with bridge - [hello-time <1-10>] STP hello time, in seconds
        default: 2
    maxage:
        description:
            - This is only used with bridge - [max-age <6-42>] STP maximum message age, in seconds
        default: 20
    ageingtime:
        description:
            - This is only used with bridge - [ageing-time <0-1000000>] the Ethernet MAC address aging time, in seconds
        default: 300
    mac:
        description:
            - >
              This is only used with bridge - MAC address of the bridge
              (note: this requires a recent kernel feature, originally introduced in 3.15 upstream kernel)
    slavepriority:
        description:
            - This is only used with 'bridge-slave' - [<0-63>] - STP priority of this slave
        default: 32
    path_cost:
        description:
            - This is only used with 'bridge-slave' - [<1-65535>] - STP port cost for destinations via this slave
        default: 100
    hairpin:
        description:
            - This is only used with 'bridge-slave' - 'hairpin mode' for the slave, which allows frames to be sent back out through the slave the
              frame was received on.
        type: bool
        default: 'yes'
    vlanid:
        description:
            - This is only used with VLAN - VLAN ID in range <0-4095>
    vlandev:
        description:
            - This is only used with VLAN - parent device this VLAN is on, can use ifname
    flags:
        description:
            - This is only used with VLAN - flags
    ingress:
        description:
            - This is only used with VLAN - VLAN ingress priority mapping
    egress:
        description:
            - This is only used with VLAN - VLAN egress priority mapping

'''

EXAMPLES = '''
# These examples are using the following inventory:
#
# ## Directory layout:
#
# |_/inventory/cloud-hosts
# |           /group_vars/openstack-stage.yml
# |           /host_vars/controller-01.openstack.host.com
# |           /host_vars/controller-02.openstack.host.com
# |_/playbook/library/nmcli.py
# |          /playbook-add.yml
# |          /playbook-del.yml
# ```
#
# ## inventory examples
# ### groups_vars
# ```yml
# ---
# #devops_os_define_network
# storage_gw: "192.0.2.254"
# external_gw: "198.51.100.254"
# tenant_gw: "203.0.113.254"
#
# #Team vars
# nmcli_team:
#   - conn_name: tenant
#     ip4: '{{ tenant_ip }}'
#     gw4: '{{ tenant_gw }}'
#   - conn_name: external
#     ip4: '{{ external_ip }}'
#     gw4: '{{ external_gw }}'
#   - conn_name: storage
#     ip4: '{{ storage_ip }}'
#     gw4: '{{ storage_gw }}'
# nmcli_team_slave:
#   - conn_name: em1
#     ifname: em1
#     master: tenant
#   - conn_name: em2
#     ifname: em2
#     master: tenant
#   - conn_name: p2p1
#     ifname: p2p1
#     master: storage
#   - conn_name: p2p2
#     ifname: p2p2
#     master: external
#
# #bond vars
# nmcli_bond:
#   - conn_name: tenant
#     ip4: '{{ tenant_ip }}'
#     gw4: ''
#     mode: balance-rr
#   - conn_name: external
#     ip4: '{{ external_ip }}'
#     gw4: ''
#     mode: balance-rr
#   - conn_name: storage
#     ip4: '{{ storage_ip }}'
#     gw4: '{{ storage_gw }}'
#     mode: balance-rr
# nmcli_bond_slave:
#   - conn_name: em1
#     ifname: em1
#     master: tenant
#   - conn_name: em2
#     ifname: em2
#     master: tenant
#   - conn_name: p2p1
#     ifname: p2p1
#     master: storage
#   - conn_name: p2p2
#     ifname: p2p2
#     master: external
#
# #ethernet vars
# nmcli_ethernet:
#   - conn_name: em1
#     ifname: em1
#     ip4: '{{ tenant_ip }}'
#     gw4: '{{ tenant_gw }}'
#   - conn_name: em2
#     ifname: em2
#     ip4: '{{ tenant_ip }}'
#     gw4: '{{ tenant_gw }}'
#   - conn_name: p2p1
#     ifname: p2p1
#     ip4: '{{ storage_ip }}'
#     gw4: '{{ storage_gw }}'
#   - conn_name: p2p2
#     ifname: p2p2
#     ip4: '{{ external_ip }}'
#     gw4: '{{ external_gw }}'
# ```
#
# ### host_vars
# ```yml
# ---
# storage_ip: "192.0.2.91/23"
# external_ip: "198.51.100.23/21"
# tenant_ip: "203.0.113.77/23"
# ```



## playbook-add.yml example

---
- hosts: openstack-stage
  remote_user: root
  tasks:

  - name: install needed network manager libs
    yum:
      name: '{{ item }}'
      state: installed
    with_items:
      - NetworkManager-glib
      - libnm-qt-devel.x86_64
      - nm-connection-editor.x86_64
      - libsemanage-python
      - policycoreutils-python

##### Working with all cloud nodes - Teaming
  - name: try nmcli add team - conn_name only & ip4 gw4
    nmcli:
      type: team
      conn_name: '{{ item.conn_name }}'
      ip4: '{{ item.ip4 }}'
      gw4: '{{ item.gw4 }}'
      state: present
    with_items:
      - '{{ nmcli_team }}'

  - name: try nmcli add teams-slave
    nmcli:
      type: team-slave
      conn_name: '{{ item.conn_name }}'
      ifname: '{{ item.ifname }}'
      master: '{{ item.master }}'
      state: present
    with_items:
      - '{{ nmcli_team_slave }}'

###### Working with all cloud nodes - Bonding
  - name: try nmcli add bond - conn_name only & ip4 gw4 mode
    nmcli:
      type: bond
      conn_name: '{{ item.conn_name }}'
      ip4: '{{ item.ip4 }}'
      gw4: '{{ item.gw4 }}'
      mode: '{{ item.mode }}'
      state: present
    with_items:
      - '{{ nmcli_bond }}'

  - name: try nmcli add bond-slave
    nmcli:
      type: bond-slave
      conn_name: '{{ item.conn_name }}'
      ifname: '{{ item.ifname }}'
      master: '{{ item.master }}'
      state: present
    with_items:
      - '{{ nmcli_bond_slave }}'

##### Working with all cloud nodes - Ethernet
  - name: nmcli add Ethernet - conn_name only & ip4 gw4
    nmcli:
      type: ethernet
      conn_name: '{{ item.conn_name }}'
      ip4: '{{ item.ip4 }}'
      gw4: '{{ item.gw4 }}'
      state: present
    with_items:
      - '{{ nmcli_ethernet }}'

## playbook-del.yml example
- hosts: openstack-stage
  remote_user: root
  tasks:

  - name: try nmcli del team - multiple
    nmcli:
      conn_name: '{{ item.conn_name }}'
      state: absent
    with_items:
      - conn_name: em1
      - conn_name: em2
      - conn_name: p1p1
      - conn_name: p1p2
      - conn_name: p2p1
      - conn_name: p2p2
      - conn_name: tenant
      - conn_name: storage
      - conn_name: external
      - conn_name: team-em1
      - conn_name: team-em2
      - conn_name: team-p1p1
      - conn_name: team-p1p2
      - conn_name: team-p2p1
      - conn_name: team-p2p2

# To add an Ethernet connection with static IP configuration, issue a command as follows
  - nmcli:
    conn_name: my-eth1
    ifname: eth1
    type: ethernet
    ip4: 192.0.2.100/24
    gw4: 192.0.2.1
    state: present

# To add an Team connection with static IP configuration, issue a command as follows
  - nmcli:
      conn_name: my-team1
      ifname: my-team1
      type: team
      ip4: 192.0.2.100/24
      gw4: 192.0.2.1
      state: present
      autoconnect: yes

# Optionally, at the same time specify IPv6 addresses for the device as follows:
  - nmcli:
      conn_name: my-eth1
      ifname: eth1
      type: ethernet
      ip4: 192.0.2.100/24
      gw4: 192.0.2.1
      ip6: '2001:db8::cafe'
      gw6: '2001:db8::1'
      state: present

# To add two IPv4 DNS server addresses:
  - nmcli:
      conn_name: my-eth1
      type: ethernet
      dns4:
        - 192.0.2.53
        - 198.51.100.53
      state: present

# To make a profile usable for all compatible Ethernet interfaces, issue a command as follows
  - nmcli:
      ctype: ethernet
      name: my-eth1
      ifname: '*'
      state: present

# To change the property of a setting e.g. MTU, issue a command as follows:
  - nmcli:
      conn_name: my-eth1
      mtu: 9000
      type: ethernet
      state: present

# nmcli exits with status 0 if it succeeds and exits with a status greater
# than zero when there is a failure. The following list of status codes may be
# returned:
#
#     - 0 Success - indicates the operation succeeded
#     - 1 Unknown or unspecified error
#     - 2 Invalid user input, wrong nmcli invocation
#     - 3 Timeout expired (see --wait option)
#     - 4 Connection activation failed
#     - 5 Connection deactivation failed
#     - 6 Disconnecting device failed
#     - 7 Connection deletion failed
#     - 8 NetworkManager is not running
#     - 9 nmcli and NetworkManager versions mismatch
#     - 10 Connection, device, or access point does not exist.
'''

RETURN = r"""#
"""

try:
    import dbus
    HAVE_DBUS = True
except ImportError:
    HAVE_DBUS = False

try:
    import gi
    gi.require_version('NMClient', '1.0')
    gi.require_version('NetworkManager', '1.0')

    from gi.repository import NetworkManager, NMClient
    HAVE_NM_CLIENT = True
except (ImportError, ValueError):
    HAVE_NM_CLIENT = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


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

    platform = 'Generic'
    distribution = None
    if HAVE_DBUS:
        bus = dbus.SystemBus()
    # The following is going to be used in dbus code
    DEVTYPES = {
        1: "Ethernet",
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
    STATES = {
        0: "Unknown",
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
        self.module = module
        self.state = module.params['state']
        self.options = {
            'type': module.params['type'],
            'con-name': module.params['conn_name'],
            'autoconnect': self.bool_to_string(module.params['autoconnect']),
            'connection.autoconnect': self.bool_to_string(module.params['autoconnect']),
            'ifname': module.params['ifname'],
            'master': module.params['master'],
            'ip4': module.params['ip4'],
            'ipv4.addresses': module.params['ip4'],
            'gw4': module.params['gw4'],
            'ipv4.gateway': module.params['gw4'],
            'dns4': module.params['dns4'],
            'ipv4.dns': module.params['dns4'],
            'ipv4.dns-search': ' '.join(module.params['dns4_search']) if module.params.get('dns4_search') else None,
            'ip6': module.params['ip6'],
            'ipv6.addresses': module.params['ip6'],
            'gw6': module.params['gw6'],
            'ipv6.gateway': module.params['gw6'],
            'dns6': module.params['dns6'],
            'ipv6.dns': module.params['dns6'],
            'ipv6.dns-search': ' '.join(module.params['dns6_search']) if module.params.get('dns6_search') else None,
            'mtu': module.params['mtu'],
            '802-3-ethernet.mtu': module.params['mtu'],
            'bridge.stp': self.bool_to_string(module.params['stp']),
            'bridge.priority': module.params['priority'],
            'mode': module.params['mode'],
            'miimon': module.params['miimon'],
            'primary': module.params['primary'],
            'downdelay': module.params['downdelay'],
            'updelay': module.params['updelay'],
            'arp-interval': module.params['arp_interval'],
            'arp-ip-target': module.params['arp_ip_target'],
            'bridge-port.priority': module.params['slavepriority'],
            'bridge.forward-delay': module.params['forwarddelay'],
            'bridge.hello-time': module.params['hellotime'],
            'bridge.max-age': module.params['maxage'],
            'bridge.ageing-time': module.params['ageingtime'],
            'bridge-port.hairpin': module.params['hairpin'],
            'bridge-port.path-cost': module.params['path_cost'],
            'bridge.mac-address': module.params['mac'],
            'id': module.params['vlanid'],
            'vlan.id': module.params['vlanid'],
            'vlan.parent': module.params['vlandev'],
            'dev': module.params['vlandev'],
            'flags': module.params['flags'],
            'ingress': module.params['ingress'],
            'egress': module.params['egress'],
            'ipv4.dhcp-client-id': module.params['dhcp_client_id'],
        }
        self.nmcli_bin = self.module.get_bin_path('nmcli', True)

    def execute_command(self, cmd, use_unsafe_shell=False, data=None):
        return self.module.run_command(cmd, use_unsafe_shell=use_unsafe_shell, data=data)

    def merge_secrets(self, proxy, config, setting_name):
        try:
            # returns a dict of dicts mapping name::setting, where setting is a dict
            # mapping key::value.  Each member of the 'setting' dict is a secret
            secrets = proxy.GetSecrets(setting_name)

            # Copy the secrets into our connection config
            for setting in secrets:
                for key in secrets[setting]:
                    config[setting_name][key] = secrets[setting][key]
        except:
            pass

    def dict_to_string(self, d):
        # Try to trivially translate a dictionary's elements into nice string
        # formatting.
        dstr = ""
        for key in d:
            val = d[key]
            str_val = ""
            add_string = True
            if isinstance(val, dbus.Array):
                for elt in val:
                    if isinstance(elt, dbus.Byte):
                        str_val += "%s " % int(elt)
                    elif isinstance(elt, dbus.String):
                        str_val += "%s" % elt
            elif isinstance(val, dbus.Dictionary):
                dstr += self.dict_to_string(val)
                add_string = False
            else:
                str_val = val
            if add_string:
                dstr += "%s: %s\n" % (key, str_val)
        return dstr

    def connection_to_string(self, config):
        # dump a connection configuration to use in list_connection_info
        setting_list = []
        for setting_name in config:
            setting_list.append(self.dict_to_string(config[setting_name]))
        return setting_list

    @staticmethod
    def bool_to_string(boolean):
        return "yes" if boolean else "no"

    def _prepare_cmd(self, cmd, options):
        for key in options:
            if self.options[key] is not None:
                cmd.extend([key, self.options[key]])
        return cmd

    def _prepare_create_connection_cmd(self, cmd, slave=False):
        if self.options['con-name'] is not None:
            cmd.append(self.options['con-name'])
        elif self.options['ifname'] is not None:
            cmd.append(self.options['ifname'])
        cmd.append('ifname')
        if self.options['ifname'] is not None:
            cmd.append(self.options['ifname'])
        elif self.options['con-name'] is not None:
            cmd.append(self.options['con-name'])

        if slave:
            cmd.append('master')
            if self.options['con-name'] is not None:
                cmd.append(self.options['master'])

        return cmd

    def list_connection_info(self):
        # Ask the settings service for the list of connections it provides
        bus = dbus.SystemBus()

        service_name = "org.freedesktop.NetworkManager"
        settings = None
        try:
            proxy = bus.get_object(service_name, "/org/freedesktop/NetworkManager/Settings")
            settings = dbus.Interface(proxy, "org.freedesktop.NetworkManager.Settings")
        except dbus.DBusException as e:
            self.module.fail_json(msg="Unable to read Network Manager settings from DBus system bus: %s" % to_native(e),
                                  details="Please check if NetworkManager is installed and"
                                          " service network-manager is started.")
        connection_paths = settings.ListConnections()
        connection_list = []
        # List each connection's name, UUID, and type
        for path in connection_paths:
            con_proxy = bus.get_object(service_name, path)
            settings_connection = dbus.Interface(con_proxy, "org.freedesktop.NetworkManager.Settings.Connection")
            config = settings_connection.GetSettings()

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
            s_con = config['connection']
            connection_list.append(s_con['id'])
            connection_list.append(s_con['uuid'])
            connection_list.append(s_con['type'])
            connection_list.append(self.connection_to_string(config))
        return connection_list

    def connection_exists(self):
        # we are going to use name and type in this instance to find if that connection exists and is of type x
        connections = self.list_connection_info()

        for con_item in connections:
            if self.options['con-name'] == con_item:
                return True

    def down_connection(self):
        cmd = [self.nmcli_bin, 'con', 'down', self.options['con-name']]
        return self.execute_command(cmd)

    def up_connection(self):
        cmd = [self.nmcli_bin, 'con', 'up', self.options['con-name']]
        return self.execute_command(cmd)

    def create_connection_team(self):
        # format for creating team interface
        cmd = [self.nmcli_bin, 'con', 'add', 'type', 'team', 'con-name']
        options = ['autoconnect', 'ip4', 'gw4', 'ip6', 'gw6', 'ipv4.dns-search', 'ipv6.dns-search', 'ipv4.dhcp-client-id']
        cmd = self._prepare_create_connection_cmd(cmd)

        return self._prepare_cmd(cmd, options)

    def modify_connection_team(self):
        cmd = [self.nmcli_bin, 'con', 'mod', self.options['con-name']]
        options = ['autoconnect', 'ip4', 'gw4', 'dns4', 'ip6', 'gw6', 'dns6', 'ipv4.dns-search', 'ipv6.dns-search', 'ipv4.dhcp-client-id']

        return self._prepare_cmd(cmd, options)

    def create_connection_team_slave(self):
        # format for creating team-slave interface
        cmd = [self.nmcli_bin, 'connection', 'add', 'type', self.options['type'], 'con-name']
        cmd = self._prepare_create_connection_cmd(cmd, slave=True)
        return cmd

    def modify_connection_team_slave(self):
        # format for modifying team-slave interface
        cmd = [self.nmcli_bin, 'con', 'mod', self.options['con-name'], 'connection.master', self.options['master']]
        options = ['802-3-ethernet.mtu']
        return self._prepare_cmd(cmd, options)

    def create_connection_bond(self):
        # format for creating bond interface
        cmd = [self.nmcli_bin, 'con', 'add', 'type', 'bond', 'con-name']
        options = ['autoconnect', 'mode', 'ip4', 'gw4', 'ip6', 'gw6', 'ipv4.dns-search', 'ipv6.dns-search', 'ipv4.dhcp-client-id', 'miimon', 'downdelay',
                   'updelay', 'arp-interval', 'arp-ip-target', 'primary', 'ipv4.dhcp-client-id']
        cmd = self._prepare_create_connection_cmd(cmd)

        return self._prepare_cmd(cmd, options)

    def modify_connection_bond(self):
        # format for modifying bond interface
        cmd = [self.nmcli_bin, 'con', 'mod', self.options['con-name']]
        options = ['autoconnect', 'ip4', 'gw4', 'dns4', 'ip6', 'gw6', 'dns6', 'ipv4.dns-search', 'ipv6.dns-search', 'ipv4.dhcp-client-id', 'miimon',
                   'downdelay', 'updelay', 'arp-interval', 'arp-ip-target', 'ipv4.dhcp-client-id']

        return self._prepare_cmd(cmd, options)

    def create_connection_bond_slave(self):
        # format for creating bond-slave interface
        cmd = [self.nmcli_bin, 'connection', 'add', 'type', 'bond-slave', 'con-name']
        return self._prepare_create_connection_cmd(cmd, slave=True)

    def modify_connection_bond_slave(self):
        # format for modifying bond-slave interface
        cmd = [self.nmcli_bin, 'con', 'mod', self.options['con-name'], 'connection.master', self.options['master']]
        return cmd

    def create_connection_ethernet(self):
        # format for creating ethernet interface
        # To add an Ethernet connection with static IP configuration, issue a command as follows
        # - nmcli: name=add conn_name=my-eth1 ifname=eth1 type=ethernet ip4=192.0.2.100/24 gw4=192.0.2.1 state=present
        # nmcli con add con-name my-eth1 ifname eth1 type ethernet ip4 192.0.2.100/24 gw4 192.0.2.1
        cmd = [self.nmcli_bin, 'con', 'add', 'type', self.options['type'], 'con-name']
        options = ['autoconnect', 'ip4', 'gw4', 'ip6', 'gw6', 'ipv4.dns-search', 'ipv6.dns-search', 'ipv4.dhcp-client-id']
        cmd = self._prepare_create_connection_cmd(cmd)

        return self._prepare_cmd(cmd, options)

    def create_connection_generic(self):
        return self.create_connection_ethernet()

    def modify_connection_ethernet(self):
        # format for modifying ethernet interface
        # To modify an Ethernet connection with static IP configuration, issue a command as follows
        # - nmcli: conn_name=my-eth1 ifname=eth1 type=ethernet ip4=192.0.2.100/24 gw4=192.0.2.1 state=present
        # nmcli con mod con-name my-eth1 ifname eth1 type ethernet ip4 192.0.2.100/24 gw4 192.0.2.1
        cmd = [self.nmcli_bin, 'con', 'mod', self.options['con-name']]
        options = ['connection.autoconnect', 'ipv4.addresses', 'ipv4.gateway', 'ipv4.dns', 'ipv6.addresses', 'ipv6.gateway', 'ipv6.dns', 'ipv4.dns-search',
                   'ipv6.dns-search', '802-3-ethernet.mtu', 'ipv4.dhcp-client-id']
        return self._prepare_cmd(cmd, options)

    def modify_connection_generic(self):
        cmd = [self.nmcli_bin, 'con', 'mod', self.options['con-name']]
        options = ['connection.autoconnect', 'ipv4.addresses', 'ipv4.gateway', 'ipv4.dns', 'ipv6.addresses', 'ipv6.gateway', 'ipv6.dns', 'ipv4.dns-search',
                   'ipv6.dns-search', 'ipv4.dhcp-client-id']
        return self._prepare_cmd(cmd, options)

    def create_connection_bridge(self):
        # format for creating bridge interface
        # To add an Bridge connection with static IP configuration, issue a command as follows
        # - nmcli: name=add conn_name=my-eth1 ifname=eth1 type=bridge ip4=192.0.2.100/24 gw4=192.0.2.1 state=present
        # nmcli con add con-name my-eth1 ifname eth1 type bridge ip4 192.0.2.100/24 gw4 192.0.2.1
        cmd = [self.nmcli_bin, 'con', 'add', 'type', 'bridge', 'con-name']
        options = ['autoconnect', 'ip4', 'gw4', 'ip6', 'gw6', 'bridge.ageing-time', 'bridge.forward-delay', 'bridge.hello-time', 'bridge.mac-address',
                   'bridge.max-age', 'bridge.priority', 'bridge.stp']
        cmd = self._prepare_create_connection_cmd(cmd)

        return self._prepare_cmd(cmd, options)

    def modify_connection_bridge(self):
        # format for modifying bridge interface
        # To add an Bridge connection with static IP configuration, issue a command as follows
        # - nmcli: name=mod conn_name=my-eth1 ifname=eth1 type=bridge ip4=192.0.2.100/24 gw4=192.0.2.1 state=present
        # nmcli con mod my-eth1 ifname eth1 type bridge ip4 192.0.2.100/24 gw4 192.0.2.1
        cmd = [self.nmcli_bin, 'con', 'mod', self.options['con-name']]
        options = ['autoconnect', 'ip4', 'gw4', 'ip6', 'gw6', 'bridge.ageing-time', 'bridge.forward-delay', 'bridge.hello-time',
                   'bridge.mac-address', 'bridge.max-age', 'bridge.priority', 'bridge.stp']

        return self._prepare_cmd(cmd, options)

    def create_connection_bridge_slave(self):
        # format for creating bond-slave interface
        cmd = [self.nmcli_bin, 'con', 'add', 'type', 'bridge-slave', 'con-name']
        options = ['master', 'bridge-port.path-cost', 'bridge-port.hairpin', 'bridge-port.priority']
        cmd = self._prepare_create_connection_cmd(cmd)

        return self._prepare_cmd(cmd, options)

    def modify_connection_bridge_slave(self):
        # format for modifying bond-slave interface
        cmd = [self.nmcli_bin, 'con', 'mod', self.options['con-name']]
        options = ['master', 'bridge-port.path-cost', 'bridge-port.hairpin', 'bridge-port.priority']

        return self._prepare_cmd(cmd, options)

    def create_connection_vlan(self):
        cmd = [self.nmcli_bin, 'con', 'add', 'type', 'vlan', 'con-name']
        options = ['autoconnect', 'dev', 'id', 'ip4', 'gw4', 'ip6', 'gw6', ]

        if self.options['con-name'] is not None:
            cmd.append(self.options['con-name'])
        elif self.options['ifname'] is not None:
            cmd.append(self.options['ifname'])
        else:
            cmd.append('vlan%s' % self.options['vlan.id'])

        cmd.append('ifname')

        if self.options['ifname'] is not None:
            cmd.append(self.options['ifname'])
        elif self.options['con-name'] is not None:
            cmd.append(self.options['con-name'])
        else:
            cmd.append('vlan%s' % self.options['vlan.id'])

        return self._prepare_cmd(cmd, options)

    def modify_connection_vlan(self):
        cmd = [self.nmcli_bin, 'con', 'mod', 'con-name']
        options = ['autoconnect', 'vlan.parent', 'vlan.id', 'ip4', 'gw4', 'dns4', 'ip6', 'gw6', 'dns6']
        return self._prepare_cmd(cmd, options)

    def create_connection(self):
        create_connection = 'create_connection_{type}'.format(type=self.options['type'].replace("-", "_"))
        modify_connection = 'modify_connection_{type}'.format(type=self.options['type'].replace("-", "_"))

        cmd_create = getattr(self, create_connection, False)
        cmd_modify = getattr(self, modify_connection, False)

        bool_dns4_dns6 = (self.options['dns4'] is not None) or (self.options['dns6'] is not None)
        bool_mtu_dns4_dns6 = (self.options['mtu'] is not None) or bool_dns4_dns6

        if self.options['type'] == 'team' and bool_dns4_dns6:
            self.execute_command(cmd_create())
            self.execute_command(cmd_modify())
            return self.up_connection()
        elif self.options['type'] == 'team-slave' and self.options['mtu'] is not None:
            self.execute_command(cmd_create())
            return self.execute_command(cmd_modify())
        elif self.options['type'] == 'bond' and bool_mtu_dns4_dns6:
            self.execute_command(cmd_create())
            self.execute_command(cmd_modify())
            return self.up_connection()

        elif self.options['type'] == 'ethernet' and bool_mtu_dns4_dns6:
            self.execute_command(cmd_create())
            self.execute_command(cmd_modify())

            return self.up_connection()

        if cmd_create:
            return self.execute_command(cmd_create())
        else:
            self.module.fail_json(msg="Type of device or network connection is required "
                                      "while performing 'create' operation. Please specify 'type' as an argument.")

    def remove_connection(self):
        # self.down_connection()
        cmd = [self.nmcli_bin, 'con', 'del', self.options['con-name']]
        return self.execute_command(cmd)

    def modify_connection(self):
        modify_connection = 'modify_connection_{type}'.format(type=self.options['type'].replace("-", "_"))
        cmd = getattr(self, modify_connection, False)

        if cmd:
            return self.execute_command(cmd())
        else:
            self.module.fail_json(msg="Type of device or network connection is required "
                                      "while performing 'modify' operation. Please specify 'type' as an argument.")


def main():
    # Parsing argument file
    module = AnsibleModule(
        argument_spec=dict(
            autoconnect=dict(required=False, default=True, type='bool'),
            state=dict(required=True, choices=['present', 'absent'], type='str'),
            conn_name=dict(required=True, type='str'),
            master=dict(required=False, default=None, type='str'),
            ifname=dict(required=False, default=None, type='str'),
            type=dict(required=False, default=None,
                      choices=['ethernet', 'team', 'team-slave', 'bond',
                               'bond-slave', 'bridge', 'bridge-slave',
                               'vlan', 'generic'],
                      type='str'),
            ip4=dict(required=False, default=None, type='str'),
            gw4=dict(required=False, default=None, type='str'),
            dns4=dict(required=False, default=None, type='list'),
            dns4_search=dict(type='list'),
            dhcp_client_id=dict(required=False, default=None, type='str'),
            ip6=dict(required=False, default=None, type='str'),
            gw6=dict(required=False, default=None, type='str'),
            dns6=dict(required=False, default=None, type='str'),
            dns6_search=dict(type='list'),
            # Bond Specific vars
            mode=dict(require=False, default="balance-rr", type='str', choices=["balance-rr", "active-backup", "balance-xor", "broadcast", "802.3ad",
                                                                                "balance-tlb", "balance-alb"]),
            miimon=dict(required=False, default=None, type='str'),
            downdelay=dict(required=False, default=None, type='str'),
            updelay=dict(required=False, default=None, type='str'),
            arp_interval=dict(required=False, default=None, type='str'),
            arp_ip_target=dict(required=False, default=None, type='str'),
            primary=dict(required=False, default=None, type='str'),
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
            hairpin=dict(required=False, default=True, type='str'),
            path_cost=dict(required=False, default="100", type='str'),
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

    nmcli = Nmcli(module)

    (rc, out, err) = (None, '', '')
    result = {'conn_name': nmcli.options['con-name'], 'state': nmcli.state}

    # check for issues
    if nmcli.options['con-name'] is None:
        nmcli.module.fail_json(msg="Please specify a name for the connection")
    # team-slave checks
    if nmcli.options['type'] == 'team-slave' and nmcli.options['master'] is None:
        nmcli.module.fail_json(msg="Please specify a name for the master")
    if nmcli.options['type'] == 'team-slave' and nmcli.options['ifname'] is None:
        nmcli.module.fail_json(msg="Please specify an interface name for the connection")

    if nmcli.state == 'absent':
        if nmcli.connection_exists():
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = nmcli.down_connection()
            (rc, out, err) = nmcli.remove_connection()
            if rc != 0:
                module.fail_json(name=('No Connection named %s exists' % nmcli.options['con-name']), msg=err, rc=rc)

    elif nmcli.state == 'present':
        if nmcli.connection_exists():
            # modify connection (note: this function is check mode aware)
            # result['Connection']=('Connection %s of Type %s is not being added' % (nmcli.conn_name, nmcli.type))
            result['Exists'] = 'Connections do exist so we are modifying them'
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = nmcli.modify_connection()
        if not nmcli.connection_exists():
            result['Connection'] = ('Connection %s of Type %s is being added' % (nmcli.options['con-name'], nmcli.options['type']))
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = nmcli.create_connection()
        if rc is not None and rc != 0:
            module.fail_json(name=nmcli.options['con-name'], msg=err, rc=rc)

    if rc is None:
        result['changed'] = False
    else:
        result['changed'] = True
    if out:
        result['stdout'] = out
    if err:
        result['stderr'] = err

    module.exit_json(**result)


if __name__ == '__main__':
    main()
