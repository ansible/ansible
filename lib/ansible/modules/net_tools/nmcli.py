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

DOCUMENTATION = r'''
---
module: nmcli
author:
- Chris Long (@alcamie101)
short_description: Manage Networking
requirements:
- dbus
- NetworkManager-glib
- nmcli
version_added: "2.0"
description:
    - Manage the network devices. Create, modify and manage various connection and device type e.g., ethernet, teams, bonds, vlans etc.
    - 'On CentOS and Fedora like systems, the requirements can be met by installing the following packages: NetworkManager-glib,
      libnm-qt-devel.x86_64, nm-connection-editor.x86_64, libsemanage-python, policycoreutils-python.'
    - 'On Ubuntu and Debian like systems, the requirements can be met by installing the following packages: network-manager,
      python-dbus (or python3-dbus, depending on the Python version in use), libnm-glib-dev.'
    - 'On openSUSE, the requirements can be met by installing the following packages: NetworkManager, python2-dbus-python (or
      python3-dbus-python), typelib-1_0-NMClient-1_0 and typelib-1_0-NetworkManager-1_0.'
options:
    state:
        description:
            - Whether the device should exist or not, taking action if the state is different from what is stated.
        type: str
        required: true
        choices: [ absent, present ]
    autoconnect:
        description:
            - Whether the connection should start on boot.
            - Whether the connection profile can be automatically activated
        type: bool
        default: yes
    conn_name:
        description:
            - 'Where conn_name will be the name used to call the connection. when not provided a default name is generated: <type>[-<ifname>][-<num>]'
        type: str
        required: true
    ifname:
        description:
            - The interface to bind the connection to.
            - The connection will only be applicable to this interface name.
            - A special value of C('*') can be used for interface-independent connections.
            - The ifname argument is mandatory for all connection types except bond, team, bridge and vlan.
            - This parameter defaults to C(conn_name) when left unset.
        type: str
    type:
        description:
            - This is the type of device or network connection that you wish to create or modify.
            - Type C(generic) is added in Ansible 2.5.
        type: str
        choices: [ bond, bond-slave, bridge, bridge-slave, ethernet, generic, ipip, sit, team, team-slave, vlan, vxlan ]
    mode:
        description:
            - This is the type of device or network connection that you wish to create for a bond, team or bridge.
        type: str
        choices: [ 802.3ad, active-backup, balance-alb, balance-rr, balance-tlb, balance-xor, broadcast ]
        default: balance-rr
    master:
        description:
            - Master <master (ifname, or connection UUID or conn_name) of bridge, team, bond master connection profile.
        type: str
    ip4:
        description:
            - The IPv4 address to this interface.
            - Use the format C(192.0.2.24/24).
        type: str
    gw4:
        description:
            - The IPv4 gateway for this interface.
            - Use the format C(192.0.2.1).
        type: str
    dns4:
        description:
            - A list of up to 3 dns servers.
            - IPv4 format e.g. to add two IPv4 DNS server addresses, use C(192.0.2.53 198.51.100.53).
        type: list
    dns4_search:
        description:
            - A list of DNS search domains.
        type: list
        version_added: '2.5'
    ip6:
        description:
            - The IPv6 address to this interface.
            - Use the format C(abbe::cafe).
        type: str
    gw6:
        description:
            - The IPv6 gateway for this interface.
            - Use the format C(2001:db8::1).
        type: str
    dns6:
        description:
            - A list of up to 3 dns servers.
            - IPv6 format e.g. to add two IPv6 DNS server addresses, use C(2001:4860:4860::8888 2001:4860:4860::8844).
        type: list
    dns6_search:
        description:
            - A list of DNS search domains.
        type: list
        version_added: '2.5'
    mtu:
        description:
            - The connection MTU, e.g. 9000. This can't be applied when creating the interface and is done once the interface has been created.
            - Can be used when modifying Team, VLAN, Ethernet (Future plans to implement wifi, pppoe, infiniband)
            - This parameter defaults to C(1500) when unset.
        type: int
    dhcp_client_id:
        description:
            - DHCP Client Identifier sent to the DHCP server.
        type: str
        version_added: "2.5"
    primary:
        description:
            - This is only used with bond and is the primary interface name (for "active-backup" mode), this is the usually the 'ifname'.
        type: str
    miimon:
        description:
            - This is only used with bond - miimon.
            - This parameter defaults to C(100) when unset.
        type: int
    downdelay:
        description:
            - This is only used with bond - downdelay.
        type: int
    updelay:
        description:
            - This is only used with bond - updelay.
        type: int
    arp_interval:
        description:
            - This is only used with bond - ARP interval.
        type: int
    arp_ip_target:
        description:
            - This is only used with bond - ARP IP target.
        type: str
    stp:
        description:
            - This is only used with bridge and controls whether Spanning Tree Protocol (STP) is enabled for this bridge.
        type: bool
        default: yes
    priority:
        description:
            - This is only used with 'bridge' - sets STP priority.
        type: int
        default: 128
    forwarddelay:
        description:
            - This is only used with bridge - [forward-delay <2-30>] STP forwarding delay, in seconds.
        type: int
        default: 15
    hellotime:
        description:
            - This is only used with bridge - [hello-time <1-10>] STP hello time, in seconds.
        type: int
        default: 2
    maxage:
        description:
            - This is only used with bridge - [max-age <6-42>] STP maximum message age, in seconds.
        type: int
        default: 20
    ageingtime:
        description:
            - This is only used with bridge - [ageing-time <0-1000000>] the Ethernet MAC address aging time, in seconds.
        type: int
        default: 300
    mac:
        description:
            - This is only used with bridge - MAC address of the bridge.
            - Note this requires a recent kernel feature, originally introduced in 3.15 upstream kernel.
    slavepriority:
        description:
            - This is only used with 'bridge-slave' - [<0-63>] - STP priority of this slave.
        type: int
        default: 32
    path_cost:
        description:
            - This is only used with 'bridge-slave' - [<1-65535>] - STP port cost for destinations via this slave.
        type: int
        default: 100
    hairpin:
        description:
            - This is only used with 'bridge-slave' - 'hairpin mode' for the slave, which allows frames to be sent back out through the slave the
              frame was received on.
        type: bool
        default: yes
    vlanid:
        description:
            - This is only used with VLAN - VLAN ID in range <0-4095>.
        type: int
    vlandev:
        description:
            - This is only used with VLAN - parent device this VLAN is on, can use ifname.
        type: str
    flags:
        description:
            - This is only used with VLAN - flags.
        type: str
    ingress:
        description:
            - This is only used with VLAN - VLAN ingress priority mapping.
        type: str
    egress:
        description:
            - This is only used with VLAN - VLAN egress priority mapping.
        type: str
    vxlan_id:
        description:
            - This is only used with VXLAN - VXLAN ID.
        type: int
        version_added: "2.8"
    vxlan_remote:
       description:
            - This is only used with VXLAN - VXLAN destination IP address.
       type: str
       version_added: "2.8"
    vxlan_local:
       description:
            - This is only used with VXLAN - VXLAN local IP address.
       type: str
       version_added: "2.8"
    ip_tunnel_dev:
        description:
            - This is used with IPIP/SIT - parent device this IPIP/SIT tunnel, can use ifname.
        type: str
        version_added: "2.8"
    ip_tunnel_remote:
       description:
            - This is used with IPIP/SIT - IPIP/SIT destination IP address.
       type: str
       version_added: "2.8"
    ip_tunnel_local:
       description:
            - This is used with IPIP/SIT - IPIP/SIT local IP address.
       type: str
       version_added: "2.8"
'''

EXAMPLES = r'''
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
#     ip4: '{{ tenant_ip1 }}'
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
    package:
      name:
        - NetworkManager-glib
        - nm-connection-editor
        - libsemanage-python
        - policycoreutils-python
      state: present

##### Working with all cloud nodes - Teaming
  - name: Try nmcli add team - conn_name only & ip4 gw4
    nmcli:
      type: team
      conn_name: '{{ item.conn_name }}'
      ip4: '{{ item.ip4 }}'
      gw4: '{{ item.gw4 }}'
      state: present
    with_items:
      - '{{ nmcli_team }}'

  - name: Try nmcli add teams-slave
    nmcli:
      type: team-slave
      conn_name: '{{ item.conn_name }}'
      ifname: '{{ item.ifname }}'
      master: '{{ item.master }}'
      state: present
    with_items:
      - '{{ nmcli_team_slave }}'

###### Working with all cloud nodes - Bonding
  - name: Try nmcli add bond - conn_name only & ip4 gw4 mode
    nmcli:
      type: bond
      conn_name: '{{ item.conn_name }}'
      ip4: '{{ item.ip4 }}'
      gw4: '{{ item.gw4 }}'
      mode: '{{ item.mode }}'
      state: present
    with_items:
      - '{{ nmcli_bond }}'

  - name: Try nmcli add bond-slave
    nmcli:
      type: bond-slave
      conn_name: '{{ item.conn_name }}'
      ifname: '{{ item.ifname }}'
      master: '{{ item.master }}'
      state: present
    with_items:
      - '{{ nmcli_bond_slave }}'

##### Working with all cloud nodes - Ethernet
  - name: Try nmcli add Ethernet - conn_name only & ip4 gw4
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

  - name: Try nmcli del team - multiple
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

  - name: Add an Ethernet connection with static IP configuration
    nmcli:
    conn_name: my-eth1
    ifname: eth1
    type: ethernet
    ip4: 192.0.2.100/24
    gw4: 192.0.2.1
    state: present

  - name: Add an Team connection with static IP configuration
    nmcli:
      conn_name: my-team1
      ifname: my-team1
      type: team
      ip4: 192.0.2.100/24
      gw4: 192.0.2.1
      state: present
      autoconnect: yes

  - name: Optionally, at the same time specify IPv6 addresses for the device
    nmcli:
      conn_name: my-eth1
      ifname: eth1
      type: ethernet
      ip4: 192.0.2.100/24
      gw4: 192.0.2.1
      ip6: 2001:db8::cafe
      gw6: 2001:db8::1
      state: present

  - name: Add two IPv4 DNS server addresses
    nmcli:
      conn_name: my-eth1
      type: ethernet
      dns4:
      - 192.0.2.53
      - 198.51.100.53
      state: present

  - name: Make a profile usable for all compatible Ethernet interfaces
    nmcli:
      ctype: ethernet
      name: my-eth1
      ifname: '*'
      state: present

  - name: Change the property of a setting e.g. MTU
    nmcli:
      conn_name: my-eth1
      mtu: 9000
      type: ethernet
      state: present

  - name: Add VxLan
    nmcli:
      type: vxlan
      conn_name: vxlan_test1
      vxlan_id: 16
      vxlan_local: 192.168.1.2
      vxlan_remote: 192.168.1.5

  - name: Add ipip
    nmcli:
      type: ipip
      conn_name: ipip_test1
      ip_tunnel_dev: eth0
      ip_tunnel_local: 192.168.1.2
      ip_tunnel_remote: 192.168.1.5

  - name: Add sit
    nmcli:
      type: sit
      conn_name: sit_test1
      ip_tunnel_dev: eth0
      ip_tunnel_local: 192.168.1.2
      ip_tunnel_remote: 192.168.1.5

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

import traceback

DBUS_IMP_ERR = None
try:
    import dbus
    HAVE_DBUS = True
except ImportError:
    DBUS_IMP_ERR = traceback.format_exc()
    HAVE_DBUS = False

NM_CLIENT_IMP_ERR = None
try:
    import gi
    gi.require_version('NMClient', '1.0')
    gi.require_version('NetworkManager', '1.0')

    from gi.repository import NetworkManager, NMClient
    HAVE_NM_CLIENT = True
except (ImportError, ValueError):
    NM_CLIENT_IMP_ERR = traceback.format_exc()
    HAVE_NM_CLIENT = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
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
        15: "Team",
        16: "VxLan",
        17: "ipip",
        18: "sit",
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
        self.autoconnect = module.params['autoconnect']
        self.conn_name = module.params['conn_name']
        self.master = module.params['master']
        self.ifname = module.params['ifname']
        self.type = module.params['type']
        self.ip4 = module.params['ip4']
        self.gw4 = module.params['gw4']
        self.dns4 = ' '.join(module.params['dns4']) if module.params.get('dns4') else None
        self.dns4_search = ' '.join(module.params['dns4_search']) if module.params.get('dns4_search') else None
        self.ip6 = module.params['ip6']
        self.gw6 = module.params['gw6']
        self.dns6 = ' '.join(module.params['dns6']) if module.params.get('dns6') else None
        self.dns6_search = ' '.join(module.params['dns6_search']) if module.params.get('dns6_search') else None
        self.mtu = module.params['mtu']
        self.stp = module.params['stp']
        self.priority = module.params['priority']
        self.mode = module.params['mode']
        self.miimon = module.params['miimon']
        self.primary = module.params['primary']
        self.downdelay = module.params['downdelay']
        self.updelay = module.params['updelay']
        self.arp_interval = module.params['arp_interval']
        self.arp_ip_target = module.params['arp_ip_target']
        self.slavepriority = module.params['slavepriority']
        self.forwarddelay = module.params['forwarddelay']
        self.hellotime = module.params['hellotime']
        self.maxage = module.params['maxage']
        self.ageingtime = module.params['ageingtime']
        self.hairpin = module.params['hairpin']
        self.path_cost = module.params['path_cost']
        self.mac = module.params['mac']
        self.vlanid = module.params['vlanid']
        self.vlandev = module.params['vlandev']
        self.flags = module.params['flags']
        self.ingress = module.params['ingress']
        self.egress = module.params['egress']
        self.vxlan_id = module.params['vxlan_id']
        self.vxlan_local = module.params['vxlan_local']
        self.vxlan_remote = module.params['vxlan_remote']
        self.ip_tunnel_dev = module.params['ip_tunnel_dev']
        self.ip_tunnel_local = module.params['ip_tunnel_local']
        self.ip_tunnel_remote = module.params['ip_tunnel_remote']
        self.nmcli_bin = self.module.get_bin_path('nmcli', True)
        self.dhcp_client_id = module.params['dhcp_client_id']

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
        except Exception:
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
        if boolean:
            return "yes"
        else:
            return "no"

    def list_connection_info(self):
        # Ask the settings service for the list of connections it provides
        bus = dbus.SystemBus()

        service_name = "org.freedesktop.NetworkManager"
        settings = None
        try:
            proxy = bus.get_object(service_name, "/org/freedesktop/NetworkManager/Settings")
            settings = dbus.Interface(proxy, "org.freedesktop.NetworkManager.Settings")
        except dbus.exceptions.DBusException as e:
            self.module.fail_json(msg="Unable to read Network Manager settings from DBus system bus: %s" % to_native(e),
                                  details="Please check if NetworkManager is installed and"
                                          "service network-manager is started.")
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
            if self.conn_name == con_item:
                return True

    def down_connection(self):
        cmd = [self.nmcli_bin, 'con', 'down', self.conn_name]
        return self.execute_command(cmd)

    def up_connection(self):
        cmd = [self.nmcli_bin, 'con', 'up', self.conn_name]
        return self.execute_command(cmd)

    def create_connection_team(self):
        cmd = [self.nmcli_bin, 'con', 'add', 'type', 'team', 'con-name']
        # format for creating team interface
        if self.conn_name is not None:
            cmd.append(self.conn_name)
        elif self.ifname is not None:
            cmd.append(self.ifname)
        cmd.append('ifname')
        if self.ifname is not None:
            cmd.append(self.ifname)
        elif self.conn_name is not None:
            cmd.append(self.conn_name)

        options = {
            'ipv4.address': self.ip4,
            'ipv4.gateway': self.gw4,
            'ipv6.address': self.ip6,
            'ipv6.gateway': self.gw6,
            'autoconnect': self.bool_to_string(self.autoconnect),
            'ipv4.dns-search': self.dns4_search,
            'ipv6.dns-search': self.dns6_search,
            'ipv4.dhcp-client-id': self.dhcp_client_id,
        }

        for key, value in options.items():
            if value is not None:
                cmd.extend([key, value])

        return cmd

    def modify_connection_team(self):
        cmd = [self.nmcli_bin, 'con', 'mod', self.conn_name]
        options = {
            'ipv4.address': self.ip4,
            'ipv4.gateway': self.gw4,
            'ipv4.dns': self.dns4,
            'ipv6.address': self.ip6,
            'ipv6.gateway': self.gw6,
            'ipv6.dns': self.dns6,
            'autoconnect': self.bool_to_string(self.autoconnect),
            'ipv4.dns-search': self.dns4_search,
            'ipv6.dns-search': self.dns6_search,
            'ipv4.dhcp-client-id': self.dhcp_client_id,
        }

        for key, value in options.items():
            if value is not None:
                cmd.extend([key, value])

        return cmd

    def create_connection_team_slave(self):
        cmd = [self.nmcli_bin, 'connection', 'add', 'type', self.type, 'con-name']
        # format for creating team-slave interface
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

    def modify_connection_team_slave(self):
        cmd = [self.nmcli_bin, 'con', 'mod', self.conn_name, 'connection.master', self.master]
        # format for modifying team-slave interface
        if self.mtu is not None:
            cmd.append('802-3-ethernet.mtu')
            cmd.append(self.mtu)
        return cmd

    def create_connection_bond(self):
        cmd = [self.nmcli_bin, 'con', 'add', 'type', 'bond', 'con-name']
        # format for creating bond interface
        if self.conn_name is not None:
            cmd.append(self.conn_name)
        elif self.ifname is not None:
            cmd.append(self.ifname)
        cmd.append('ifname')
        if self.ifname is not None:
            cmd.append(self.ifname)
        elif self.conn_name is not None:
            cmd.append(self.conn_name)
        options = {
            'mode': self.mode,
            'ipv4.address': self.ip4,
            'ipv4.gateway': self.gw4,
            'ipv6.address': self.ip6,
            'ipv6.gateway': self.gw6,
            'autoconnect': self.bool_to_string(self.autoconnect),
            'ipv4.dns-search': self.dns4_search,
            'ipv6.dns-search': self.dns6_search,
            'miimon': self.miimon,
            'downdelay': self.downdelay,
            'updelay': self.updelay,
            'arp-interval': self.arp_interval,
            'arp-ip-target': self.arp_ip_target,
            'primary': self.primary,
            'ipv4.dhcp-client-id': self.dhcp_client_id,
        }

        for key, value in options.items():
            if value is not None:
                cmd.extend([key, value])
        return cmd

    def modify_connection_bond(self):
        cmd = [self.nmcli_bin, 'con', 'mod', self.conn_name]
        # format for modifying bond interface

        options = {
            'ipv4.address': self.ip4,
            'ipv4.gateway': self.gw4,
            'ipv4.dns': self.dns4,
            'ipv6.address': self.ip6,
            'ipv6.gateway': self.gw6,
            'ipv6.dns': self.dns6,
            'autoconnect': self.bool_to_string(self.autoconnect),
            'ipv4.dns-search': self.dns4_search,
            'ipv6.dns-search': self.dns6_search,
            'miimon': self.miimon,
            'downdelay': self.downdelay,
            'updelay': self.updelay,
            'arp-interval': self.arp_interval,
            'arp-ip-target': self.arp_ip_target,
            'ipv4.dhcp-client-id': self.dhcp_client_id,
        }

        for key, value in options.items():
            if value is not None:
                cmd.extend([key, value])

        return cmd

    def create_connection_bond_slave(self):
        cmd = [self.nmcli_bin, 'connection', 'add', 'type', 'bond-slave', 'con-name']
        # format for creating bond-slave interface
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
        cmd = [self.nmcli_bin, 'con', 'mod', self.conn_name, 'connection.master', self.master]
        # format for modifying bond-slave interface
        return cmd

    def create_connection_ethernet(self, conn_type='ethernet'):
        # format for creating ethernet interface
        # To add an Ethernet connection with static IP configuration, issue a command as follows
        # - nmcli: name=add conn_name=my-eth1 ifname=eth1 type=ethernet ip4=192.0.2.100/24 gw4=192.0.2.1 state=present
        # nmcli con add con-name my-eth1 ifname eth1 type ethernet ip4 192.0.2.100/24 gw4 192.0.2.1
        cmd = [self.nmcli_bin, 'con', 'add', 'type']
        if conn_type == 'ethernet':
            cmd.append('ethernet')
        elif conn_type == 'generic':
            cmd.append('generic')
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

        options = {
            'ipv4.address': self.ip4,
            'ipv4.gateway': self.gw4,
            'ipv6.address': self.ip6,
            'ipv6.gateway': self.gw6,
            'autoconnect': self.bool_to_string(self.autoconnect),
            'ipv4.dns-search': self.dns4_search,
            'ipv6.dns-search': self.dns6_search,
            'ipv4.dhcp-client-id': self.dhcp_client_id,
        }

        for key, value in options.items():
            if value is not None:
                cmd.extend([key, value])

        return cmd

    def modify_connection_ethernet(self, conn_type='ethernet'):
        cmd = [self.nmcli_bin, 'con', 'mod', self.conn_name]
        # format for modifying ethernet interface
        # To modify an Ethernet connection with static IP configuration, issue a command as follows
        # - nmcli: conn_name=my-eth1 ifname=eth1 type=ethernet ip4=192.0.2.100/24 gw4=192.0.2.1 state=present
        # nmcli con mod con-name my-eth1 ifname eth1 type ethernet ip4 192.0.2.100/24 gw4 192.0.2.1
        options = {
            'ipv4.address': self.ip4,
            'ipv4.gateway': self.gw4,
            'ipv4.dns': self.dns4,
            'ipv6.address': self.ip6,
            'ipv6.gateway': self.gw6,
            'ipv6.dns': self.dns6,
            'autoconnect': self.bool_to_string(self.autoconnect),
            'ipv4.dns-search': self.dns4_search,
            'ipv6.dns-search': self.dns6_search,
            '802-3-ethernet.mtu': self.mtu,
            'ipv4.dhcp-client-id': self.dhcp_client_id,
        }

        for key, value in options.items():
            if value is not None:
                if key == '802-3-ethernet.mtu' and conn_type != 'ethernet':
                    continue
                cmd.extend([key, value])

        return cmd

    def create_connection_bridge(self):
        # format for creating bridge interface
        # To add an Bridge connection with static IP configuration, issue a command as follows
        # - nmcli: name=add conn_name=my-eth1 ifname=eth1 type=bridge ip4=192.0.2.100/24 gw4=192.0.2.1 state=present
        # nmcli con add con-name my-eth1 ifname eth1 type bridge ip4 192.0.2.100/24 gw4 192.0.2.1
        cmd = [self.nmcli_bin, 'con', 'add', 'type', 'bridge', 'con-name']
        if self.conn_name is not None:
            cmd.append(self.conn_name)
        elif self.ifname is not None:
            cmd.append(self.ifname)
        cmd.append('ifname')
        if self.ifname is not None:
            cmd.append(self.ifname)
        elif self.conn_name is not None:
            cmd.append(self.conn_name)

        options = {
            'ip4': self.ip4,
            'gw4': self.gw4,
            'ip6': self.ip6,
            'gw6': self.gw6,
            'autoconnect': self.bool_to_string(self.autoconnect),
            'bridge.ageing-time': self.ageingtime,
            'bridge.forward-delay': self.forwarddelay,
            'bridge.hello-time': self.hellotime,
            'bridge.mac-address': self.mac,
            'bridge.max-age': self.maxage,
            'bridge.priority': self.priority,
            'bridge.stp': self.bool_to_string(self.stp)
        }

        for key, value in options.items():
            if value is not None:
                cmd.extend([key, value])

        return cmd

    def modify_connection_bridge(self):
        # format for modifying bridge interface
        # To add an Bridge connection with static IP configuration, issue a command as follows
        # - nmcli: name=mod conn_name=my-eth1 ifname=eth1 type=bridge ip4=192.0.2.100/24 gw4=192.0.2.1 state=present
        # nmcli con mod my-eth1 ifname eth1 type bridge ip4 192.0.2.100/24 gw4 192.0.2.1
        cmd = [self.nmcli_bin, 'con', 'mod', self.conn_name]

        options = {
            'ip4': self.ip4,
            'gw4': self.gw4,
            'ip6': self.ip6,
            'gw6': self.gw6,
            'autoconnect': self.bool_to_string(self.autoconnect),
            'bridge.ageing-time': self.ageingtime,
            'bridge.forward-delay': self.forwarddelay,
            'bridge.hello-time': self.hellotime,
            'bridge.mac-address': self.mac,
            'bridge.max-age': self.maxage,
            'bridge.priority': self.priority,
            'bridge.stp': self.bool_to_string(self.stp)
        }

        for key, value in options.items():
            if value is not None:
                cmd.extend([key, value])

        return cmd

    def create_connection_bridge_slave(self):
        # format for creating bond-slave interface
        cmd = [self.nmcli_bin, 'con', 'add', 'type', 'bridge-slave', 'con-name']
        if self.conn_name is not None:
            cmd.append(self.conn_name)
        elif self.ifname is not None:
            cmd.append(self.ifname)
        cmd.append('ifname')
        if self.ifname is not None:
            cmd.append(self.ifname)
        elif self.conn_name is not None:
            cmd.append(self.conn_name)

        options = {
            'master': self.master,
            'bridge-port.path-cost': self.path_cost,
            'bridge-port.hairpin': self.bool_to_string(self.hairpin),
            'bridge-port.priority': self.slavepriority,
        }

        for key, value in options.items():
            if value is not None:
                cmd.extend([key, value])

        return cmd

    def modify_connection_bridge_slave(self):
        # format for modifying bond-slave interface
        cmd = [self.nmcli_bin, 'con', 'mod', self.conn_name]
        options = {
            'master': self.master,
            'bridge-port.path-cost': self.path_cost,
            'bridge-port.hairpin': self.bool_to_string(self.hairpin),
            'bridge-port.priority': self.slavepriority,
        }

        for key, value in options.items():
            if value is not None:
                cmd.extend([key, value])

        return cmd

    def create_connection_vlan(self):
        cmd = [self.nmcli_bin]
        cmd.append('con')
        cmd.append('add')
        cmd.append('type')
        cmd.append('vlan')
        cmd.append('con-name')

        if self.conn_name is not None:
            cmd.append(self.conn_name)
        elif self.ifname is not None:
            cmd.append(self.ifname)
        else:
            cmd.append('vlan%s' % self.vlanid)

        cmd.append('ifname')
        if self.ifname is not None:
            cmd.append(self.ifname)
        elif self.conn_name is not None:
            cmd.append(self.conn_name)
        else:
            cmd.append('vlan%s' % self.vlanid)

        params = {'dev': self.vlandev,
                  'id': self.vlanid,
                  'ip4': self.ip4 or '',
                  'gw4': self.gw4 or '',
                  'ip6': self.ip6 or '',
                  'gw6': self.gw6 or '',
                  'autoconnect': self.bool_to_string(self.autoconnect)
                  }
        for k, v in params.items():
            cmd.extend([k, v])

        return cmd

    def modify_connection_vlan(self):
        cmd = [self.nmcli_bin]
        cmd.append('con')
        cmd.append('mod')

        if self.conn_name is not None:
            cmd.append(self.conn_name)
        elif self.ifname is not None:
            cmd.append(self.ifname)
        else:
            cmd.append('vlan%s' % self.vlanid)

        params = {'vlan.parent': self.vlandev,
                  'vlan.id': self.vlanid,
                  'ipv4.address': self.ip4 or '',
                  'ipv4.gateway': self.gw4 or '',
                  'ipv4.dns': self.dns4 or '',
                  'ipv6.address': self.ip6 or '',
                  'ipv6.gateway': self.gw6 or '',
                  'ipv6.dns': self.dns6 or '',
                  'autoconnect': self.bool_to_string(self.autoconnect)
                  }

        for k, v in params.items():
            cmd.extend([k, v])

        return cmd

    def create_connection_vxlan(self):
        cmd = [self.nmcli_bin, 'con', 'add', 'type', 'vxlan', 'con-name']

        if self.conn_name is not None:
            cmd.append(self.conn_name)
        elif self.ifname is not None:
            cmd.append(self.ifname)
        else:
            cmd.append('vxlan%s' % self.vxlanid)

        cmd.append('ifname')
        if self.ifname is not None:
            cmd.append(self.ifname)
        elif self.conn_name is not None:
            cmd.append(self.conn_name)
        else:
            cmd.append('vxan%s' % self.vxlanid)

        params = {'vxlan.id': self.vxlan_id,
                  'vxlan.local': self.vxlan_local,
                  'vxlan.remote': self.vxlan_remote,
                  'autoconnect': self.bool_to_string(self.autoconnect)
                  }
        for k, v in params.items():
            cmd.extend([k, v])

        return cmd

    def modify_connection_vxlan(self):
        cmd = [self.nmcli_bin, 'con', 'mod']

        if self.conn_name is not None:
            cmd.append(self.conn_name)
        elif self.ifname is not None:
            cmd.append(self.ifname)
        else:
            cmd.append('vxlan%s' % self.vxlanid)

        params = {'vxlan.id': self.vxlan_id,
                  'vxlan.local': self.vxlan_local,
                  'vxlan.remote': self.vxlan_remote,
                  'autoconnect': self.bool_to_string(self.autoconnect)
                  }
        for k, v in params.items():
            cmd.extend([k, v])
        return cmd

    def create_connection_ipip(self):
        cmd = [self.nmcli_bin, 'con', 'add', 'type', 'ip-tunnel', 'mode', 'ipip', 'con-name']

        if self.conn_name is not None:
            cmd.append(self.conn_name)
        elif self.ifname is not None:
            cmd.append(self.ifname)
        elif self.ip_tunnel_dev is not None:
            cmd.append('ipip%s' % self.ip_tunnel_dev)

        cmd.append('ifname')
        if self.ifname is not None:
            cmd.append(self.ifname)
        elif self.conn_name is not None:
            cmd.append(self.conn_name)
        else:
            cmd.append('ipip%s' % self.ipip_dev)

        if self.ip_tunnel_dev is not None:
            cmd.append('dev')
            cmd.append(self.ip_tunnel_dev)

        params = {'ip-tunnel.local': self.ip_tunnel_local,
                  'ip-tunnel.remote': self.ip_tunnel_remote,
                  'autoconnect': self.bool_to_string(self.autoconnect)
                  }
        for k, v in params.items():
            cmd.extend([k, v])

        return cmd

    def modify_connection_ipip(self):
        cmd = [self.nmcli_bin, 'con', 'mod']

        if self.conn_name is not None:
            cmd.append(self.conn_name)
        elif self.ifname is not None:
            cmd.append(self.ifname)
        elif self.ip_tunnel_dev is not None:
            cmd.append('ipip%s' % self.ip_tunnel_dev)

        params = {'ip-tunnel.local': self.ip_tunnel_local,
                  'ip-tunnel.remote': self.ip_tunnel_remote,
                  'autoconnect': self.bool_to_string(self.autoconnect)
                  }
        for k, v in params.items():
            cmd.extend([k, v])
        return cmd

    def create_connection_sit(self):
        cmd = [self.nmcli_bin, 'con', 'add', 'type', 'ip-tunnel', 'mode', 'sit', 'con-name']

        if self.conn_name is not None:
            cmd.append(self.conn_name)
        elif self.ifname is not None:
            cmd.append(self.ifname)
        elif self.ip_tunnel_dev is not None:
            cmd.append('sit%s' % self.ip_tunnel_dev)

        cmd.append('ifname')
        if self.ifname is not None:
            cmd.append(self.ifname)
        elif self.conn_name is not None:
            cmd.append(self.conn_name)
        else:
            cmd.append('sit%s' % self.ipip_dev)

        if self.ip_tunnel_dev is not None:
            cmd.append('dev')
            cmd.append(self.ip_tunnel_dev)

        params = {'ip-tunnel.local': self.ip_tunnel_local,
                  'ip-tunnel.remote': self.ip_tunnel_remote,
                  'autoconnect': self.bool_to_string(self.autoconnect)
                  }
        for k, v in params.items():
            cmd.extend([k, v])

        return cmd

    def modify_connection_sit(self):
        cmd = [self.nmcli_bin, 'con', 'mod']

        if self.conn_name is not None:
            cmd.append(self.conn_name)
        elif self.ifname is not None:
            cmd.append(self.ifname)
        elif self.ip_tunnel_dev is not None:
            cmd.append('sit%s' % self.ip_tunnel_dev)

        params = {'ip-tunnel.local': self.ip_tunnel_local,
                  'ip-tunnel.remote': self.ip_tunnel_remote,
                  'autoconnect': self.bool_to_string(self.autoconnect)
                  }
        for k, v in params.items():
            cmd.extend([k, v])
        return cmd

    def create_connection(self):
        cmd = []
        if self.type == 'team':
            if (self.dns4 is not None) or (self.dns6 is not None):
                cmd = self.create_connection_team()
                self.execute_command(cmd)
                cmd = self.modify_connection_team()
                self.execute_command(cmd)
                return self.up_connection()
            elif (self.dns4 is None) or (self.dns6 is None):
                cmd = self.create_connection_team()
        elif self.type == 'team-slave':
            if self.mtu is not None:
                cmd = self.create_connection_team_slave()
                self.execute_command(cmd)
                cmd = self.modify_connection_team_slave()
                return self.execute_command(cmd)
            else:
                cmd = self.create_connection_team_slave()
        elif self.type == 'bond':
            if (self.mtu is not None) or (self.dns4 is not None) or (self.dns6 is not None):
                cmd = self.create_connection_bond()
                self.execute_command(cmd)
                cmd = self.modify_connection_bond()
                self.execute_command(cmd)
                return self.up_connection()
            else:
                cmd = self.create_connection_bond()
        elif self.type == 'bond-slave':
            cmd = self.create_connection_bond_slave()
        elif self.type == 'ethernet':
            if (self.mtu is not None) or (self.dns4 is not None) or (self.dns6 is not None):
                cmd = self.create_connection_ethernet()
                self.execute_command(cmd)
                cmd = self.modify_connection_ethernet()
                self.execute_command(cmd)
                return self.up_connection()
            else:
                cmd = self.create_connection_ethernet()
        elif self.type == 'bridge':
            cmd = self.create_connection_bridge()
        elif self.type == 'bridge-slave':
            cmd = self.create_connection_bridge_slave()
        elif self.type == 'vlan':
            cmd = self.create_connection_vlan()
        elif self.type == 'vxlan':
            cmd = self.create_connection_vxlan()
        elif self.type == 'ipip':
            cmd = self.create_connection_ipip()
        elif self.type == 'sit':
            cmd = self.create_connection_sit()
        elif self.type == 'generic':
            cmd = self.create_connection_ethernet(conn_type='generic')

        if cmd:
            return self.execute_command(cmd)
        else:
            self.module.fail_json(msg="Type of device or network connection is required "
                                      "while performing 'create' operation. Please specify 'type' as an argument.")

    def remove_connection(self):
        # self.down_connection()
        cmd = [self.nmcli_bin, 'con', 'del', self.conn_name]
        return self.execute_command(cmd)

    def modify_connection(self):
        cmd = []
        if self.type == 'team':
            cmd = self.modify_connection_team()
        elif self.type == 'team-slave':
            cmd = self.modify_connection_team_slave()
        elif self.type == 'bond':
            cmd = self.modify_connection_bond()
        elif self.type == 'bond-slave':
            cmd = self.modify_connection_bond_slave()
        elif self.type == 'ethernet':
            cmd = self.modify_connection_ethernet()
        elif self.type == 'bridge':
            cmd = self.modify_connection_bridge()
        elif self.type == 'bridge-slave':
            cmd = self.modify_connection_bridge_slave()
        elif self.type == 'vlan':
            cmd = self.modify_connection_vlan()
        elif self.type == 'vxlan':
            cmd = self.modify_connection_vxlan()
        elif self.type == 'ipip':
            cmd = self.modify_connection_ipip()
        elif self.type == 'sit':
            cmd = self.modify_connection_sit()
        elif self.type == 'generic':
            cmd = self.modify_connection_ethernet(conn_type='generic')
        if cmd:
            return self.execute_command(cmd)
        else:
            self.module.fail_json(msg="Type of device or network connection is required "
                                      "while performing 'modify' operation. Please specify 'type' as an argument.")


def main():
    # Parsing argument file
    module = AnsibleModule(
        argument_spec=dict(
            autoconnect=dict(type='bool', default=True),
            state=dict(type='str', required=True, choices=['absent', 'present']),
            conn_name=dict(type='str', required=True),
            master=dict(type='str'),
            ifname=dict(type='str'),
            type=dict(type='str',
                      choices=['bond', 'bond-slave', 'bridge', 'bridge-slave', 'ethernet', 'generic', 'ipip', 'sit', 'team', 'team-slave', 'vlan', 'vxlan']),
            ip4=dict(type='str'),
            gw4=dict(type='str'),
            dns4=dict(type='list'),
            dns4_search=dict(type='list'),
            dhcp_client_id=dict(type='str'),
            ip6=dict(type='str'),
            gw6=dict(type='str'),
            dns6=dict(type='list'),
            dns6_search=dict(type='list'),
            # Bond Specific vars
            mode=dict(type='str', default='balance-rr',
                      choices=['802.3ad', 'active-backup', 'balance-alb', 'balance-rr', 'balance-tlb', 'balance-xor', 'broadcast']),
            miimon=dict(type='int'),
            downdelay=dict(type='int'),
            updelay=dict(type='int'),
            arp_interval=dict(type='int'),
            arp_ip_target=dict(type='str'),
            primary=dict(type='str'),
            # general usage
            mtu=dict(type='int'),
            mac=dict(type='str'),
            # bridge specific vars
            stp=dict(type='bool', default=True),
            priority=dict(type='int', default=128),
            slavepriority=dict(type='int', default=32),
            forwarddelay=dict(type='int', default=15),
            hellotime=dict(type='int', default=2),
            maxage=dict(type='int', default=20),
            ageingtime=dict(type='int', default=300),
            hairpin=dict(type='bool', default=True),
            path_cost=dict(type='int', default=100),
            # vlan specific vars
            vlanid=dict(type='int'),
            vlandev=dict(type='str'),
            flags=dict(type='str'),
            ingress=dict(type='str'),
            egress=dict(type='str'),
            # vxlan specific vars
            vxlan_id=dict(type='int'),
            vxlan_local=dict(type='str'),
            vxlan_remote=dict(type='str'),
            # ip-tunnel specific vars
            ip_tunnel_dev=dict(type='str'),
            ip_tunnel_local=dict(type='str'),
            ip_tunnel_remote=dict(type='str'),
        ),
        supports_check_mode=True,
    )

    if not HAVE_DBUS:
        module.fail_json(msg=missing_required_lib('dbus'), exception=DBUS_IMP_ERR)

    if not HAVE_NM_CLIENT:
        module.fail_json(msg=missing_required_lib('NetworkManager glib API'), exception=NM_CLIENT_IMP_ERR)

    nmcli = Nmcli(module)

    (rc, out, err) = (None, '', '')
    result = {'conn_name': nmcli.conn_name, 'state': nmcli.state}

    # check for issues
    if nmcli.conn_name is None:
        nmcli.module.fail_json(msg="Please specify a name for the connection")
    # team-slave checks
    if nmcli.type == 'team-slave' and nmcli.master is None:
        nmcli.module.fail_json(msg="Please specify a name for the master")
    if nmcli.type == 'team-slave' and nmcli.ifname is None:
        nmcli.module.fail_json(msg="Please specify an interface name for the connection")

    if nmcli.state == 'absent':
        if nmcli.connection_exists():
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = nmcli.down_connection()
            (rc, out, err) = nmcli.remove_connection()
            if rc != 0:
                module.fail_json(name=('No Connection named %s exists' % nmcli.conn_name), msg=err, rc=rc)

    elif nmcli.state == 'present':
        if nmcli.connection_exists():
            # modify connection (note: this function is check mode aware)
            # result['Connection']=('Connection %s of Type %s is not being added' % (nmcli.conn_name, nmcli.type))
            result['Exists'] = 'Connections do exist so we are modifying them'
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = nmcli.modify_connection()
        if not nmcli.connection_exists():
            result['Connection'] = ('Connection %s of Type %s is being added' % (nmcli.conn_name, nmcli.type))
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = nmcli.create_connection()
        if rc is not None and rc != 0:
            module.fail_json(name=nmcli.conn_name, msg=err, rc=rc)

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
