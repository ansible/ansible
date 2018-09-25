#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Susant Sahani<susant@redhat.com>
# Copyright: (c) 2018, Ansible Project
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
module: networkd
author: "Susant Sahani (@ssahani)"
short_description: Configure Link, NetDev and Network for systemd-networkd
requirements: [ systemd-networkd, systemd]
version_added: "2.8"
description:
    - Generate systemd-networks configuration files.
options:
    state:
        description:
            - Whether the configuration files should exist or not.
        required: True
        choices: [ "present", "absent" ]
    name:
        description:
            - Where name will be the what we call the interface name.
        required: True
    config_type:
        description:
            - Specifies the configuration type file to create.
        required: true
        choices: [ "link", "netdev", "network" ]
    config_path:
        description:
            - Specifies the path where to write the configuration files.
        default: "/var/run/systemd/network"
        choices: [ "/var/run/systemd/network", "/lib/systemd/network", "/etc/systemd/network" ]
    file_name:
        description:
            - This configuration file name  where the configurations will be written.
    kind:
        description:
            - This is the type of netdev device you wish to create.
        choices: [ "bond", "bridge", "vlan", "macvlan", "ipip" ]
    mac_address:
        description:
            - Configures the MAC address.
    mtu_bytes:
        description:
            - Configures MTU of the interface.
    bond_mode:
        description:
            - This is the type of device or network connection that you wish to create for a bond.
        default: balance-rr
        choices: [ "balance-rr", "active-backup", "balance-xor", "broadcast", "802.3ad", "balance-tlb", "balance-alb" ]
    transmit_hash_policy:
        description:
            - Configures the transmit hash policy to use for slave selection in balance-xor, 802.3ad, and tlb modes.
              Applies only for Bond.
        required: false
        choices: [ "layer2", "layer3+4", "layer2+3", "encap2+3", "encap3+4" ]
    macvlan_mode:
        description:
            - Configures the macvlan or macvtap mode. Applies only for macvlan and macvtap kind netdevs.
        required: false
        choices: [ "private", "vepa", "bridge", "passthru" ]
    vlan_id:
        description:
            - The VLAN ID to use. An integer in the range 0–4094. This option is compulsory.
    tunnel_local:
        description:
            - Local IP address of tunnel. Applies only for tunnels.
        required: true
    tunnel_remote:
        description:
            - Remote IP address of tunnel. Applies only for tunnel
        required: true
    tunnel_create_independent:
        description:
            - Whether this tunnel shoube be created i.e. tunnel@none. Applies only for tunnel.
        required: false
    stp:
        description:
            - This enables the bridge's Spanning Tree Protocol (STP).
        choices: [ "yes", "no"]
    hello_time:
        description:
            - Configures the bridge's hello time in seconds.
        required: false
    forward_delay:
        description:
            - Configures the bridge's forward delay in seconds.
        required: false
    max_age:
        description:
            - Configures the bridge's max delay in seconds.
        required: false
    priority:
        description:
            - Configures the priority of the bridge.
        required: false
    lldp:
        description:
            - Controls support for Ethernet LLDP packet reception.
        choices: [ "yes", "no" ]
    ipv6_accept_ra:
        description:
            - Enable or disable IPv6 Router Advertisement (RA) reception support for the interface.
        choices: [ "yes", "no" ]
    dhcp:
        description:
            - Enables DHCPv4 and/or DHCPv6 client support.
        choices: ["yes", "no", "ipv4", "ipv6"]
    address:
        description:
            - A static IPv4 or IPv6 address and its prefix length, separated by a "/" character.
    gateway:
        description:
            - The gateway address.
        required: false
    dns:
        description:
            - A DNS server address to setup for the name.
        required: false
    domains:
        description:
            - A space separated list of domains which should be resolved using the DNS servers on this link.
        required: false
    ntp:
        description:
            - An NTP server address.
        required: false
    join_bridge:
        description:
            - Name of the bridge which name (interface) will join.
        required: false
    join_bond:
        description:
            - The name of the bond to add the link.
        required: false
    join_vlan:
        description:
            - The name of a vlan to create on the link.
        required: false
    join_macvlan:
        description:
            - The name of a macvlan to create on the link.
        required: false
    join_tunnel:
        description:
            - The name of a tunnel(ipip) to create on the link.
        required: false
    driver:
        description:
            - Matches against the hostname or machine ID of the host. Applies to link config [Match] section.
    host:
        description:
            - A whitespace-separated list of shell-style globs matching the driver currently bound to the device.
    alias:
        description:
            - The "ifalias" is set to this value. Applies to link config [Link] section.
    wake_on_lan:
        description:
            - The Wake-on-LAN policy to set for the device. Applies to link config [Link] section.
        choices: [ "phy", "unicast", "multicast", "broadcast", "arp", "magic", "secureon", "off"]
    link_name:
        description:
            - Matches against the hostname or machine ID of the host. Applies to link config [Link] section.
'''
EXAMPLES = '''

## playbook-add.yml example

---
# Configure interface with DHCP
  - networkd:
      conf_type: network
      name: eth1
      dhcp: yes
      state: present

# Bridge with two ports
  - networkd:
      conf_type: netdev
      name: brtest
      kind: bridge
      state: present

  - networkd:
      conf_type: network
      name: eth1
      join_bridge: brtest
      state: present

  - networkd:
      conf_type: network
      name: eth2
      join_bridge: brtest
      state: present

# Bond network
  - networkd:
       config_type=netdev
       name=bond1
       kind=bond
       bond_mode=active-backup
       state=present

  - networkd:
       config_type=network
       name=eth0
       join_bond=bond1
       state=present

  - networkd:
       config_type=network
       name=eth1
       join_bond=bond1
       state=present

  - networkd:
       config_type=network
       name=bond1
       dhcp=yes
       state=present
'''

UNIT_PATH_NETWORKD = '/lib/systemd/network'
UNIT_PATH_NETWORKD_SYSTEM = '/etc/systemd/network'
UNIT_PATH_NETWORKD_RUN = '/var/run/systemd/network'

RETURN = r"""#
"""

from ansible.module_utils.basic import AnsibleModule
import os


class NetworkdUtilities:

    def remove_files(self, conf_files, names):
        paths = [UNIT_PATH_NETWORKD_RUN, UNIT_PATH_NETWORKD_SYSTEM, UNIT_PATH_NETWORKD]
        conf_types = ['network', 'link', 'netdev']
        status = False

        if conf_files:
            list_conf_files = conf_files.split(' ')
            for conf_file in list_conf_files:
                for conf_path in paths:
                    if os.path.exists(os.path.join(conf_path, conf_file)):
                        os.remove(os.path.join(conf_path, conf_file))
                        status = True

        if names:
            list_names = names.split(' ')
            for name in list_names:
                for conf_type in conf_types:
                    file_name = name + '.{0}'.format(conf_type)
                    for conf_path in paths:
                        if os.path.exists(os.path.join(conf_path, file_name)):
                            os.remove(os.path.join(conf_path, file_name))
                            status = True
        return status

    def write_configs_to_file(self, config_type, path, name, config):
        if config_type == 'link':
            file_name = '{0}.link'.format(name)
            dest = os.path.join(path, file_name)
        elif config_type == 'netdev':
            file_name = '{0}.netdev'.format(name)
            dest = os.path.join(path, file_name)
        elif config_type == 'network':
            file_name = '{0}.network'.format(name)
            dest = os.path.join(path, file_name)
        else:
            return False

        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

        with open(dest, "w") as f:
            f.write(config)
            f.close()
            return True

        return False


class Link(NetworkdUtilities):

    def __init__(self, module):
        self.module = module
        self.config_path = module.params['config_path']
        self.name = module.params['name']
        self.link_name = module.params['link_name']
        self.mac_address = module.params['mac_address']
        self.host = module.params['host']
        self.wake_on_lan = module.params['wake_on_lan']
        self.driver = module.params['driver']
        self.alias = module.params['alias']
        self.mtu_bytes = module.params['mtu_bytes']

    def write_matchtion_config(self):
        conf = '[Match]\n'

        if self.driver:
            conf += 'Driver={0}\n'.format(self.driver)
        if self.mac_address:
            conf += 'MACAddress={0}\n'.format(self.mac_address)
        if self.name:
            conf += 'Name={0}\n'.format(self.name)
        if self.host:
            conf += 'Host={0}\n'.format(self.host)

        return conf + '\n'

    def create_config_link(self):
        conf = ''
        conf += self.write_matchtion_config()
        conf += '[Link]\n'

        if self.alias:
            conf += 'Alias={0}\n'.format(self.alias)
        if self.link_name:
            conf += 'Name={0}\n'.format(self.link_name)
        if self.mtu_bytes:
            conf += 'MTUBytes={0}\n'.format(self.mtu_bytes)
        if self.wake_on_lan:
            conf += 'WakeOnLan={0}\n'.format(self.wake_on_lan)

        self.write_configs_to_file('link', self.config_path, self.name, conf)

        return True


class Network(NetworkdUtilities):

    def __init__(self, module):
        self.module = module
        self.config_path = module.params['config_path']
        self.name = module.params['name']
        self.mac_address = module.params['mac_address']

        self.dhcp = module.params['dhcp']
        self.address = module.params['address']
        self.gateway = module.params['gateway']
        self.dns = module.params['dns']
        self.domains = module.params['domains']
        self.ntp = module.params['ntp']
        self.ipv6_accept_ra = module.params['ipv6_accept_ra']
        self.lldp = module.params['lldp']

        self.join_bridge = module.params['join_bridge']
        self.join_bond = module.params['join_bond']
        self.join_macvlan = module.params['join_macvlan']
        self.join_vlan = module.params['join_vlan']

    def create_config_network(self):
        conf = ''

        link = Link(self.module)
        conf += link.write_matchtion_config()
        conf += '[Network]\n'

        if self.dhcp:
            conf += 'DHCP={0}\n'.format(self.dhcp)
        if self.address:
            conf += 'Address={0}\n'.format(self.address)
        if self.gateway:
            conf += 'Gateway={0}\n'.format(self.gateway)
        if self.dns:
            conf += 'DNS={0}\n'.format(self.dns)
        if self.domains:
            conf += 'Domains={0}\n'.format(self.domains)
        if self.ntp:
            conf += 'NTP={0}\n'.format(self.ntp)
        if self.ipv6_accept_ra:
            conf += 'IPv6AcceptRA={0}\n'.format(self.ipv6_accept_ra)
        if self.lldp:
            conf += 'LLDP={0}\n'.format(self.lldp)
        if self.join_bridge:
            conf += 'Bridge={0}\n'.format(self.join_bridge)
        if self.join_bond:
            conf += 'Bond={0}\n'.format(self.join_bond)
        if self.join_vlan:

            list_vlans = self.join_vlan.split(' ')

            for vlan in list_vlans:
                conf += 'VLAN={0}\n'.format(vlan)
        if self.join_macvlan:
            conf += 'MACVLAN={0}\n'.format(self.join_macvlan)

        self.write_configs_to_file('network', self.config_path, self.name, conf)

        return True


class NetDev(NetworkdUtilities):

    def __init__(self, module):
        self.module = module
        self.config_path = module.params['config_path']
        self.name = module.params['name']
        self.kind = module.params['kind']
        self.mac_address = module.params['mac_address']
        self.mtu_bytes = module.params['mtu_bytes']

        # Bridge
        self.priority = module.params['priority']
        self.forward_delay = module.params['forward_delay']
        self.max_age = module.params['max_age']
        self.stp = module.params['stp']
        self.hello_time = module.params['hello_time']

        # Bond
        self.bond_mode = module.params['bond_mode']

        # Vlan
        self.vlan_id = module.params['vlan_id']

        # Macvlan and Macvtap
        self.macvlan_mode = module.params['macvlan_mode']

        # Tunnel
        self.tunnel_local = module.params['tunnel_local']
        self.tunnel_remote = module.params['tunnel_remote']
        self.tunnel_create_independent = module.params['tunnel_create_independent']

    def create_config_bridge_params(self):
        conf = ''

        if self.priority:
            conf += 'Priority={0}\n'.format(self.priority)
        if self.forward_delay:
            conf += 'ForwardDelaySec={0}\n'.format(self.forward_delay)
        if self.hello_time:
            conf += 'HelloTimeSec={0}\n'.format(self.hello_time)
        if self.max_age:
            conf += 'MaxAgeSec={0}\n'.format(self.max_age)
        if self.stp:
            conf += 'STP={0}\n'.format(self.stp)

        if conf:
            return '\n[Bridge]\n{0}'.format(conf)

        return conf

    def create_config_bond_params(self):
        conf = ''

        if self.bond_mode:
            conf += 'Mode={0}\n'.format(self.bond_mode)

        if conf:
            return '\n[Bond]\n{0}'.format(conf)

        return conf

    def create_config_tunnel_params(self):
        conf = ''

        if self.tunnel_local:
            conf += 'Local={0}\n'.format(self.tunnel_local)

        if self.tunnel_remote:
            conf += 'Remote={0}\n'.format(self.tunnel_remote)

        if self.tunnel_create_independent:
            conf += 'Independent={0}\n'.format(self.tunnel_create_independent)

        if conf:
            return '\n[Tunnel]\n{0}'.format(conf)

        return conf

    def create_config_netdev(self):
        conf = '[NetDev]\nName={0}\n'.format(self.name)

        if self.mac_address:
            conf += 'MACAddress={0}\n'.format(self.mac_address)

        if self.mtu_bytes:
            conf += 'MTUBytes={0}\n'.format(self.mtu_bytes)

        if self.kind == 'bridge':
            conf += 'Kind=bridge\n'
            conf += self.create_config_bridge_params()
        elif self.kind == 'bond':
            conf += 'Kind=bond\n'
            conf += self.create_config_bond_params()
        elif self.kind == 'vlan':
            conf += 'Kind=vlan\n\n[VLAN]\nId={0}\n'.format(self.vlan_id)
        elif self.kind == 'macvlan':
            conf += 'Kind=macvlan\n\n[MACVLAN]\nMode={0}\n'.format(self.macvlan_mode)
        elif self.kind == 'macvtap':
            conf += 'Kind=macvlan\n\n[MACVTAP]\nMode={0}\n'.format(self.macvlan_mode)
        elif self.kind == 'ipip':
            conf += 'Kind=ipip\n'
            conf += self.create_config_tunnel_params()

        self.write_configs_to_file('netdev', self.config_path, self.name, conf)

        return True


class Networkd(NetworkdUtilities):

    def __init__(self, module):
        self.module = module
        self.state = module.params['state']
        self.config_type = module.params['config_type']
        self.config_path = module.params['config_path']
        self.file_name = module.params['file_name']
        self.name = module.params['name']

    def create_config_link(self):
        status = False

        if self.state == 'absent':
            status = self.remove_files(self.file_name, self.name)
        else:
            if self.config_type == 'link':
                link = Link(self.module)
                status = link.create_config_link()
            elif self.config_type == 'netdev':
                netdev = NetDev(self.module)
                status = netdev.create_config_netdev()
            elif self.config_type == 'network':
                network = Network(self.module)
                status = network.create_config_network()
            else:
                self.module.fail_json(msg='Can not determine the configuration type')

            return status


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=True, choices=['present', 'absent'], type='str'),
            config_path=dict(default=UNIT_PATH_NETWORKD_RUN, type='str', choices=[UNIT_PATH_NETWORKD, UNIT_PATH_NETWORKD_RUN,
                                                                                  UNIT_PATH_NETWORKD_SYSTEM]),
            file_name=dict(default=None, type='str'),
            config_type=dict(type='str', default=None, choices=['link', 'netdev', 'network']),
            name=dict(required=True, type='str'),

            mac_address=dict(type='str', default=None),
            mtu_bytes=dict(type='str', default=None),

            # [link] section
            host=dict(type='str', default=None),
            driver=dict(type='str', default=None),
            alias=dict(type='str', default=None),
            wake_on_lan=dict(type='str', default=None, choices=['phy', 'unicast', 'multicast',
                                                                'broadcast', 'arp', 'magic', 'secureon', 'off']),
            link_name=dict(type='str', default=None),

            # [NetDev] section
            kind=dict(type='str', default=None, choices=['bridge', 'vlan', 'macvlan', 'bond', 'ipip']),

            # [VLAN] section
            vlan_id=dict(type='str', default=None),

            # [MACVLAN] and [macvtap] section
            macvlan_mode=dict(type='str', default=None, choices=['private', 'vepa', 'bridge', 'passthru']),

            # [Tunnel] section
            tunnel_local=dict(type='str', default=None),
            tunnel_remote=dict(type='str', default=None),
            tunnel_create_independent=dict(type='str', default=None),

            # [Bridge] section
            hello_time=dict(type='str', default=None),
            max_age=dict(type='str', default=None),
            priority=dict(type='str', default=None),
            forward_delay=dict(type='str', default=None),
            stp=dict(type='str', default=None, choices=['yes', 'no']),

            # [Bond] section
            bond_mode=dict(require=False, default='balance-rr', type='str', choices=['balance-rr', 'active-backup', 'balance-xor', 'broadcast', '802.3ad',
                                                                                     'balance-tlb', 'balance-alb']),
            transmit_hash_policy=dict(type='str', choices=['layer2', 'layer3+4', 'layer2+3', 'encap2+3', 'encap3+4']),
            # [Network] section
            dhcp=dict(type='str', default=None, choices=['yes', 'no', 'ipv4', 'ipv6']),
            address=dict(type='str', default=None),
            gateway=dict(type='str', default=None),
            dns=dict(type='str', default=None),
            domains=dict(type='str', default=None),
            ntp=dict(type='str', default=None),
            ipv6_accept_ra=dict(type='str', default=None, choices=['yes', 'no']),
            lldp=dict(type='str', default=None, choices=['yes', 'no']),

            # Enslave
            join_bridge=dict(type='str', default=None),
            join_bond=dict(type='str', default=None),
            join_macvlan=dict(type='str', default=None),
            join_vlan=dict(type='str', default=None),
            join_tunnel=dict(type='str', default=None),
        ),
    )

    if module.params['state'] == 'present' and not module.params['config_type']:
        module.fail_json(msg='Config type required when state is present')

    networkd = Networkd(module)
    status = networkd.create_config_link()

    module.exit_json(changed=status)


if __name__ == '__main__':
    main()
