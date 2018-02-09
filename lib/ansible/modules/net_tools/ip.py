#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, Luis Eduardo <leduardo@lsd.ufcg.edu.br>
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
module: ip
author:
    - Luis Eduardo (@lets00)
short_description: Manage all network configuration using iproute2 module.
version_added: "2.6"
description:
    - This module allows manage network configurations using iproute2 tool.
      You can create/remove several types of network interfaces (veth, bridges,
      gre, vxlan, and others).
options:
    name:
        description:
            - Name of interface that operations will be realized.
        required: true
    link:
        description:
            - C(present) create a new net interface if It does not exist. C(type) is required.
              C(absent) remove a net interface if It exist.
              C(up) turn on a net interface if It exist. This options implements idempotence.
              C(down) turn off a net interface if It exist. This options implements idempotence.
        choices: [ present, absent, up, down]
        required: false
    type:
        description:
            - Interface type that will be create when C(link) is present.
              C(bridge) creates a bridge interface.
              C(dummy) creates a dummy interface. Module dummy needs to enabled in Kernel.
              C(gre) creates a gre interface.
              C(macvlan) creates a macvlan interface. C(macvlan_mode) is required.
              C(macvtap) creates a macvtap interface. C(macvtap_mode) is required.
              C(tuntap) creates a tuntap interface. C(tuntap_mode) is required.
              C(veth) creates two interfaces connect by one enlace. C(peer) is required.
              C(vlan) creates a vlan interface. C(vlan_id) and C(vlan_protocol) are required.
              C(vrf) creates a vrf interface. C(vrf_table) is required.
        choices: [ bridge, dummy, gre, macvlan, macvtap, tuntap, veth, vlan, vrf ]
        required: false
    link_interface:
        description:
            - The interface that new interface will referenciate. It is required when C(type) is
              C(macvlan), C(macvtap), C(vlan).
        required: false
    peer:
        description:
            - Name of peer interface when C(type) is C(veth). It is required when C(type) is C(veth).
        required: false
    mtu:
        description:
            - Change MTU on interface.
        required: false
    promiscuity:
        description:
            - Change promiscuity mode.
        required: false
        type: bool
    addr:
        description:
            - Ip address operations
        required: false
        choices: [ present, absent, flush ]
    ip:
        description:
            - Add/Remove IP (v4 or v6) address on a specific interface. It must be expressed using CIDR (10.0.0.1/8).
        required: false
    vlan_id:
        description:
            - Vlan ID number. Between 1 and 4095.
        required: false
    vlan_protocol:
        description:
            - Kind vlan protocol to use.
        required: false
        choices: [ 802.1q, 802.1ad ]
    macvlan_mode:
        description:
            - MacVLAN mode.
        required: false
        choices: [ vepa, private, bridge, passthru ]
    macvtap_mode:
        description:
            - MacVtap mode.
        required: false
        choices: [ vepa, private, bridge, passthru ]
    tuntap_mode:
        description:
            - TUNTAP mode.
        required: false
        choices: [ tun, tap ]
    vrf_table:
        description:
            - VRF table value. 1 <= vrf_table <= 4294967295
        required: false
    gre_local:
        description:
            - Local GRE address
        required: false
    gre_remote:
        description:
            - Remote GRE address
        required: false
    gre_ttl:
        description:
            - GRE Time to Live. 1 <= gre_ttl <= 255
        required: false
    gre_ikey:
        description:
            - ????
        required: false
    gre_okey:
        description:
            - ????
        required: false
    gre_iflag:
        description:
            - ????
        required: false
    gre_oflag:
        description:
            - ????
        required: false
    vxlan_link:
        description:
            - VXLAN source interface.
        required: false
    vxlan_id:
        description:
            - VXLAN Network Identifier (VNI). 0 <= vxlan_id <= 16777215
        required: false
        type: int
    vxlan_group:
        description:
            - VXLAN Multicast Group address.
        required: false
    vxlan_ttl:
        description:
            - VXLAN Time To Live. 1 <= vxlan_ttl <= 255
        required: false
    netns:
        description:
            - Process network namespace management.
              C(present) creates a new network namespace.
              C(absent) removes a existent namespace.
        choices: [ present, absent ]
        required: false
requirements: [ pyroute2 ]
notes:
    - Online iproute2 Manpage
'''

EXAMPLES = '''

# This module can execute more than one network operation using a unique role.
# Create new veth interface, define ipv4 address and MTU (ip command):
# # ip link add dev veth0 type veth peer name veth1
# # ip link set dev veth0 mtu 1200
# # ip addr add dev veth0 192.168.100.1/24

- name: Create a veth interface, define ipv4 and MTU...
  ip:
    name: veth0
    link: present
    type: veth
    peer: veth1
    mtu: 1200
    addr: present
    ip: 192.168.100.1/24

# Set up a interface (ip command)
# # ip link set up dev veth0

- name: Set up veth0 interface...
  ip:
    name: veth0
    link: up

# Delete a interface (ip command)
# # ip link del dev veth0
# In this case, veth1 will be deleted too (veth interface must de exist in pair)

- name: Delete veth0 interface...
  ip:
    name: veth0
    link: absent

# Delete a namespace (ip command)
# # ip link del dev veth0
# In this case, veth1 will be deleted too (veth interface must de exist in pair)

- name: Delete veth0 interface...
  ip:
    name: veth0
    link: absent

# Create a vlan interface
- name: Create vlan interface
  ip:
    name: vlan13
    link: present
    type: vlan
    vlan_id: 13
    vlan_protocol: 802.1q
'''

from ansible.module_utils.basic import AnsibleModule
import struct
import socket

try:
    from pyroute2 import IPDB, netns, NetlinkError
    from pyroute2.ipdb.exceptions import CreateException, CommitException

    HAS_PYROUTE2 = True
except:
    HAS_PYROUTE2 = False


class IP(object):
    def __init__(self):
        self.ipdb = IPDB()

    def change_link_state_interface(self, interface_name, link_state):
        # except KeyError as k
        with self.ipdb.interfaces[interface_name] as iface:
            if iface.operstate.lower() != link_state:
                if link_state == 'up':
                    iface.up()
                else:
                    iface.down()
            else:
                raise Exception(message=interface_name)

    def create_veth_interface(self, interface, peer):
        # pyroute2.ipdb.exceptions.CreateException: interface x exists
        self.ipdb.create(ifname=interface,
                         kind='veth',
                         peer=peer).commit()

    def create_vlan_interface(self, interface, link_interface, vlan_id, vlan_protocol):
        # pyroute2.ipdb.exceptions.CreateException: interface x exists
        # pyroute2.netlink.exceptions.NetlinkError: (34, 'Resultado num\xc3\xa9rico fora de alcance')
        if vlan_protocol == '802.1q' or not vlan_protocol:
            self.ipdb.create(ifname=interface,
                             kind='vlan',
                             link=link_interface,
                             vlan_id=vlan_id,
                             vlan_protocol=0x8100).commit()
        elif vlan_protocol == '802.1ad':
            self.ipdb.create(ifname=interface,
                             kind='vlan',
                             link=link_interface,
                             vlan_id=vlan_id,
                             vlan_protocol=0x88a8).commit()

    def create_vxlan_interface(self, interface, link_interface, vxlan_id, vxlan_group, vxlan_ttl):
        self.ipdb.create(ifname=interface,
                         kind='vxlan',
                         vxlan_link=link_interface,
                         vxlan_id=vxlan_id,
                         vxlan_group=vxlan_group,
                         vxlan_ttl=vxlan_ttl).commit()

    def create_macvlan_interface(self, interface, link_interface, macvlan_mode):
        # pyroute2.ipdb.exceptions.CreateException: interface x exists
        self.ipdb.create(ifname=interface,
                         kind='macvlan',
                         link=link_interface,
                         macvlan_mode=macvlan_mode).commit()

    def create_macvtap_interface(self, interface, link_interface, macvtap_mode):
        # pyroute2.ipdb.exceptions.CreateException: interface x exists
        self.ipdb.create(ifname=interface,
                         kind='macvtap',
                         link=link_interface,
                         macvtap_mode=macvtap_mode).commit()

    def create_tuntap_interface(self, interface, tuntap_mode):
        # pyroute2.ipdb.exceptions.CreateException: interface x exists
        self.ipdb.create(ifname=interface,
                         kind='tuntap',
                         mode=tuntap_mode).commit()

    def create_vrf_interface(self, interface, vrf_table):
        # pyroute2.netlink.exceptions.NetlinkError: (22, 'Invalid Argument')
        # pyroute2.ipdb.exceptions.CreateException: interface x exists
        self.ipdb.create(ifname=interface,
                         kind='vrf',
                         vrf_table=vrf_table).commit()

    def create_dummy_interface(self, interface):
        self.ipdb.create(ifname=interface,
                         kind='dummy').commit()

    def create_bridge_interface(self, interface):
        self.ipdb.create(ifname=interface,
                         kind='bridge').commit()

    def close_modules(self):
        self.ipdb.release()

    def create_netns(self, netns_name):
        # OSError: [Errno 17] File exists:
        netns.create(netns_name)

    def remove_netns(self, netns_name):
        # OSError: [Errno 2] No such file or directory:
        netns.remove(netns_name)

    def remove_interface(self, interface_name):
        # except KeyError as k
        with self.ipdb.interfaces[interface_name] as iface:
            iface.remove()

    def set_mtu(self, interface_name, mtu):
        # except KeyError as k
        # except Exception as e (Already set)
        with self.ipdb.interfaces[interface_name] as iface:
            if not iface.mtu == mtu:
                iface.set('mtu', mtu)
            else:
                raise Exception(message='Interface {0} already have this MTU defined'.format(interface_name))

    def set_promiscuity(self, interface_name, promiscuity):
        # except KeyError as k
        # except Exception as e (Already set)
        # except CommitException: target promiscuity is not set
        with self.ipdb.interfaces[interface_name] as iface:
            if not iface.promiscuity == promiscuity:
                iface.set('promiscuity', promiscuity)
            else:
                raise Exception(message='Interface {0} already promisc'.format(interface_name))

    def ip_operation(self, interface_name, address, operation):
        # except KeyError as k
        # except NetlinkError: (105, 'No buffer space available')
        # If delete an inexistent IP, throw exception
        # If try add a existent IP, throw exception
        with self.ipdb.interfaces[interface_name] as iface:
            if operation == 'add':
                if not self._is_ip_present(interface_name, address):
                    iface.add_ip(address)
                else:
                    raise Exception(message='IP {0} already added'.format(interface_name))
            else:
                if self._is_ip_present(interface_name, address):
                    iface.del_ip(address)
                else:
                    raise Exception(message='IP {0} inexistent'.format(interface_name))

    def _is_ip_present(self, interface_name, address):
        tuple_addr = tuple(address.split('/'))
        with self.ipdb.interfaces[interface_name] as iface:
            for ips in iface['ipaddr']:
                if ips[0] == tuple_addr[0] and ips[1] == tuple_addr[1]:
                    return True
        return False

    def flush(self, interface_name):
        # except KeyError as k
        with self.ipdb.interfaces[interface_name] as iface:
            iface.flush()

    def get_status(self, interface_name):
        # except KeyError as k
        if self.ipdb.interfaces.get(interface_name):
            return self.ipdb.interfaces[interface_name].operstate


def parse_params(module):
    # LINK OPERATION
    # Link absent param does not allow more params
    if module.params.get('link'):
        if module.params.get('netns') or module.params.get('route') \
                or module.params.get('neigh') or module.params.get('maddr'):
            module.fail_json(msg='Link can not be defined with route, neigh, maddr or netns params')

        if module.params.get('link') == 'absent':
            if module.params.get('link_interface') or module.params.get('type') or module.params.get('netns')\
                    or module.params.get('vlan_id') or module.params.get('vlan_protocol')\
                    or module.params.get('macvlan_mode') or module.params.get('peer')\
                    or module.params.get('macvtap_mode') or module.params.get('tuntap_mode')\
                    or module.params.get('vrf_table') or module.params.get('gre_local')\
                    or module.params.get('gre_remote') or module.params.get('gre_tty')\
                    or module.params.get('gre_ikey') or module.params.get('gre_okey')\
                    or module.params.get('gre_iflag') or module.params.get('gre_oflag')\
                    or module.params.get('vxlan_link') or module.params.get('vxlan_id')\
                    or module.params.get('vxlan_group') or module.params.get('vxlan_ttl')\
                    or module.params.get('addr') or module.params.get('ip')\
                    or module.params.get('mtu') or module.params.get('promiscuity'):
                module.fail_json(msg='Link absent must only use name param')
        elif module.params.get('link') == 'present':
            pass
        elif module.params.get('link') == 'up':
            if module.params.get('link_interface') or module.params.get('type') or module.params.get('netns')\
                    or module.params.get('vlan_id') or module.params.get('vlan_protocol')\
                    or module.params.get('macvlan_mode') or module.params.get('peer')\
                    or module.params.get('macvtap_mode') or module.params.get('tuntap_mode')\
                    or module.params.get('vrf_table') or module.params.get('gre_local')\
                    or module.params.get('gre_remote') or module.params.get('gre_tty')\
                    or module.params.get('gre_ikey') or module.params.get('gre_okey')\
                    or module.params.get('gre_iflag') or module.params.get('gre_oflag')\
                    or module.params.get('vxlan_link') or module.params.get('vxlan_id')\
                    or module.params.get('vxlan_group') or module.params.get('vxlan_ttl'):
                module.fail_json(msg='Link up param does not be used with veth, vlan, macvlan,'
                                     'tuntap, vrf and gre options')

        # NetNS params
        if module.params.get('netns'):
            if module.params.get('route') or module.params.get('neigh')\
                    or module.params.get('maddr') or module.params.get('vlan_id')\
                    or module.params.get('vlan_protocol') or module.params.get('macvlan_mode')\
                    or module.params.get('macvtap_mode') or module.params.get('tuntap_mode')\
                    or module.params.get('vrf_table') or module.params.get('gre_local')\
                    or module.params.get('gre_remote') or module.params.get('gre_tty')\
                    or module.params.get('gre_ikey') or module.params.get('gre_okey')\
                    or module.params.get('gre_iflag') or module.params.get('gre_oflag')\
                    or module.params.get('vxlan_link') or module.params.get('vxlan_id')\
                    or module.params.get('vxlan_group') or module.params.get('vxlan_ttl')\
                    or module.params.get('addr') or module.params.get('ip'):
                module.fail_json(msg='netns param must only use name param')


def main():
    # ip link  (name, type, peer, link_interface)
    # ip netns
    # ip addr (name, ip)
    # ip route (name, ip, default, via)
    # ip neigh
    # ip maddr (name, ip)

    # Cases to think:
    # Set an interface to bridge
    # ip link set veth0 master br0

    # Set an interface to VRF
    # ip link set veth0 vrf vrf0
    # ip route add vrf vrf0 ...

    # TODO: Verify vlan_id interval to 1-4095 (2**12)
    # TODO: Verify vrf_table interval to 1-4294967295 (2**32). This raise NetlinkError
    argument_spec = {
        'name': {'required': True},
        'link': {'choices': ['present', 'absent', 'up', 'down'],
                 'required': False},
        'type': {'choices': ['bridge', 'dummy', 'gre', 'macvlan',
                             'macvtap', 'tuntap', 'veth',
                             'vlan', 'vrf', 'vxlan'],
                 'required': False},
        'netns': {'choices': ['present', 'absent'],
                  'required': False},
        'vlan_id': {'required': False,
                    'type': 'int'},
        'vlan_protocol': {'choices': ['802.1q', '802.1ad'],
                          'required': False},
        'macvlan_mode': {'choices': ['vepa', 'private', 'bridge', 'passthru'],
                         'required': False},
        'macvtap_mode': {'choices': ['vepa', 'private', 'bridge', 'passthru'],
                         'required': False},
        'tuntap_mode': {'choices': ['tun', 'tap'],
                        'required': False},
        'vrf_table': {'required': False,
                      'type': 'int'},
        'gre_local': {'required': False},
        'gre_remote': {'required': False},
        'gre_ttl': {'required': False,
                    'type': 'int'},
        'gre_ikey': {'required': False},
        'gre_okey': {'required': False},
        'gre_iflag': {'required': False},
        'gre_oflag': {'required': False},
        'vxlan_link': {'required': False},
        'vxlan_id': {'required': False,
                     'type': 'int'},
        'vxlan_group': {'required': False},
        'vxlan_ttl': {'required': False,
                      'type': 'int'},
        'link_interface': {'required': False},
        'peer': {'required': False},
        'mtu': {'type': 'int'},
        'promiscuity': {'type': 'bool'},
        'addr': {'choices': ['present', 'absent', 'flush']},
        'ip': {'required': False,
               'type': 'str'}
    }

    required_if = [['link', 'present', ['type']],
                   ['type', 'gre', ['gre_local', 'gre_remote', 'gre_ttl', 'gre_ikey',
                                    'gre_okey', 'gre_iflag', 'gre_oflag']],
                   ['type', 'macvlan', ['link_interface', 'macvlan_mode']],
                   ['type', 'macvtap', ['link_interface', 'macvtap_mode']],
                   ['type', 'tuntap', ['tuntap_mode']],
                   ['type', 'veth', ['peer']],
                   ['type', 'vlan', ['vlan_id', 'vlan_protocol']],
                   ['type', 'vrf', ['vrf_table']],
                   ['type', 'vxlan', ['vxlan_link', 'vxlan_id', 'vxlan_group', 'vxlan_ttl']],
                   ['addr', 'present', ['ip']],
                   ['addr', 'absent', ['ip']]
                   ]

    required_together = [['gre_local', 'gre_remote', 'gre_tty', 'gre_ikey',
                          'gre_okey', 'gre_iflag', 'gre_oflag'],
                         ['vlan_id', 'vlan_protocol'],
                         ]

    mutually_exclusive = [['vlan_id', 'macvlan_mode', 'macvtap_mode', 'tuntap_mode', 'vrf_table', 'gre_local'],
                          ['link_interface', 'tuntap_mode', 'peer']
                          # ('state', 'absent', 'type'),
                          # ('state', 'absent', 'add_ip'),
                          # ('state', 'absent', 'del_ip'),
                          # ('state', 'absent', 'peer'),
                          # ('state', 'absent', 'mtu'),
                          # ('state', 'absent', 'flush'),
                          # ('state', 'absent', 'vlan_id'),
                          # ('state', 'absent', 'vlan_protocol'),
                          # ('state', 'absent', 'vrf_table'),
                          # ('state', 'absent', 'gre_local'),
                          # ('state', 'absent', 'gre_remote'),
                          # ('state', 'absent', 'gre_ttl'),
                          # ('state', 'absent', 'gre_ikey'),
                          # ('state', 'absent', 'gre_okey'),
                          # ('state', 'absent', 'gre_iflag'),
                          # ('state', 'absent', 'gre_oflag'),
                          #
                          # ('state', 'up', 'type'),
                          # ('state', 'up', 'peer'),
                          # ('state', 'up', 'mtu'),
                          # ('state', 'up', 'vlan_id'),
                          # ('state', 'up', 'vlan_protocol'),
                          # ('state', 'up', 'vrf_table'),
                          # ('state', 'up', 'gre_local'),
                          # ('state', 'up', 'gre_remote'),
                          # ('state', 'up', 'gre_ttl'),
                          # ('state', 'up', 'gre_ikey'),
                          # ('state', 'up', 'gre_okey'),
                          # ('state', 'up', 'gre_iflag'),
                          # ('state', 'up', 'gre_oflag'),
                          #
                          # ('state', 'down', 'type'),
                          # ('state', 'down', 'peer'),
                          # ('state', 'down', 'mtu'),
                          # ('state', 'down', 'vlan_id'),
                          # ('state', 'down', 'vlan_protocol'),
                          # ('state', 'down', 'vrf_table'),
                          # ('state', 'down', 'gre_local'),
                          # ('state', 'down', 'gre_remote'),
                          # ('state', 'down', 'gre_ttl'),
                          # ('state', 'down', 'gre_ikey'),
                          # ('state', 'down', 'gre_okey'),
                          # ('state', 'down', 'gre_iflag'),
                          # ('state', 'down', 'gre_oflag'),
                          ]

    res_args_by_field = {'link': {'value': False, 'msg': 'ok'},
                         'interface': {'value': False, 'msg': 'ok'},
                         'addr': {'value': False, 'msg': 'ok'}}

    module = AnsibleModule(argument_spec,
                           required_together=required_together,
                           mutually_exclusive=mutually_exclusive,
                           required_if=required_if,
                           supports_check_mode=True)
    if not HAS_PYROUTE2:
        module.fail_json(msg='pyroute2 required for this module')
    ip = IP()

    parse_params(module)

    # TODO: put this on parse_params()
    if module.params.get('link_interface') and module.params.get('link') != 'present':
        module.fail_json(msg='present link must be defined when link is used')

    # LINK OPERATION
    # -------------------------------------------
    if module.params.get('link'):
        if module.params.get('link') == 'present':
            if module.params.get('type') == 'veth':
                try:
                    ip.create_veth_interface(module.params.get('name'),
                                             module.params.get('peer'))
                    res_args_by_field['link']['value'] = True
                except CreateException:
                    res_args_by_field['link']['msg'] = 'Interface {0} already exists'.format(module.params.get('name'))
            if module.params.get('type') == 'vlan':
                try:
                    ip.create_vlan_interface(module.params.get('name'),
                                             module.params.get('link_interface'),
                                             module.params.get('vlan_id'),
                                             module.params.get('vlan_protocol'))
                    res_args_by_field['link']['value'] = True
                except CreateException:
                    res_args_by_field['link']['msg'] = 'Interface {0} already exists'.format(module.params.get('name'))
                except NetlinkError as neterr:
                    module.fail_json(msg='0 <= vlan_id <= 4095')
            if module.params.get('type') == 'macvlan':
                try:
                    ip.create_macvlan_interface(module.params.get('name'),
                                                module.params.get('link_interface'),
                                                module.params.get('macvlan_mode'))
                    res_args_by_field['link']['value'] = True
                except CreateException:
                    res_args_by_field['link']['msg'] = 'Interface {0} already exists'.format(module.params.get('name'))
            if module.params.get('type') == 'macvtap':
                try:
                    ip.create_macvtap_interface(module.params.get('name'),
                                                module.params.get('link_interface'),
                                                module.params.get('macvtap_mode'))
                    res_args_by_field['link']['value'] = True
                except CreateException:
                    res_args_by_field['link']['msg'] = 'Interface {0} already exists'.format(module.params.get('name'))
            if module.params.get('type') == 'tuntap':
                try:
                    ip.create_tuntap_interface(module.params.get('name'),
                                               module.params.get('tuntap_mode'))
                    res_args_by_field['link']['value'] = True
                except CreateException:
                    res_args_by_field['link']['msg'] = 'Interface {0} already exists'.format(module.params.get('name'))
            # VRF manipulation support is present in iproute2 version 4.3.
            if module.params.get('type') == 'vrf':
                try:
                    ip.create_vrf_interface(module.params.get('name'),
                                            module.params.get('vrf_table'))
                    res_args_by_field['link']['value'] = True
                except CreateException:
                    res_args_by_field['link']['msg'] = 'Interface {0} already exists'.format(module.params.get('name'))
                except NetlinkError as uint32:
                    # If vrf_table == 0
                    if uint32.code == 22:
                        module.fail_json(msg='1 <= vrf_table <= 4294967295(2**32 - 1)')
                except struct.error:
                    module.fail_json(msg='1 <= vrf_table <= 4294967295(2**32 - 1)')
            if module.params.get('type') == 'vxlan':
                try:
                    ip.create_vxlan_interface(module.params.get('name'),
                                              module.params.get('vxlan_link'),
                                              module.params.get('vxlan_id'),
                                              module.params.get('vxlan_group'),
                                              module.params.get('vxlan_ttl'))
                    res_args_by_field['link']['value'] = True
                except CreateException:
                    res_args_by_field['link']['msg'] = 'Interface {0} already exists'.format(module.params.get('name'))
                except NetlinkError as neterr:
                    module.fail_json(msg='0 <= vxlan_id <= 16777215 and 1 <= vxlan_ttl <= 255')
                except struct.error:
                    module.fail_json(msg='1 <= vxlan_ttl <= 255')
            if module.params.get('type') == 'dummy':
                try:
                    ip.create_dummy_interface(module.params.get('name'))
                    res_args_by_field['link']['value'] = True
                except CreateException:
                    res_args_by_field['link']['msg'] = 'Interface {0} already exists'.format(module.params.get('name'))
            if module.params.get('type') == 'bridge':
                try:
                    ip.create_bridge_interface(module.params.get('name'))
                except CreateException:
                    res_args_by_field['link']['msg'] = 'Interface {0} already exists'.format(module.params.get('name'))
        elif module.params.get('link') == 'up' or module.params.get('link') == 'down':
            try:
                ip.change_link_state_interface(module.params.get('name'),
                                               module.params.get('link'))
                res_args_by_field['link']['value'] = True
            except KeyError as k:
                module.fail_json(msg='Interface {0} does not exist.'.format(k.args[0]))
            except Exception as e:
                res_args_by_field['link']['msg'] = 'Interface {0} already {1}'.format(e.args[0],
                                                                                      module.params.get('link'))
        elif module.params.get('link') == 'absent':
            try:
                ip.remove_interface(module.params.get('name'))
                res_args_by_field['link']['value'] = True
            except KeyError as k:
                module.fail_json(msg='Interface {0} does not exist.'.format(k.args[0]))
        else:
            pass

    # NETNS OPERATION
    # -------------------------------------------
    if module.params.get('netns'):
        if module.params.get('netns') == 'present':
            try:
                ip.create_netns(module.params.get('name'))
                res_args_by_field['link']['value'] = True
            except OSError as os:
                # File exists
                if os.errno == 17:
                    res_args_by_field['link']['value'] = False
                else:
                    module.fail_json(msg='netns {0}: {1}'.format(module.params.get('name'),
                                                                 os.strerror))
        else:
            try:
                ip.remove_netns(module.params.get('name'))
                res_args_by_field['link']['value'] = True
            except OSError as os:
                module.fail_json(msg='Netns {0}: {1}'.format(module.params.get('name'),
                                                             os.strerror))

    # INTERFACE OPERATION
    # -------------------------------------------
    if module.params.get('mtu'):
        try:
            ip.set_mtu(module.params.get('name'), module.params.get('mtu'))
            res_args_by_field['interface']['value'] = True
        except KeyError as k:
            module.fail_json(msg='Interface {0} does not exist.'.format(k.args[0]))
        except Exception as e:
            res_args_by_field['interface']['msg'] = 'Interface {0}, MTU already {1}'.format(e.args[0],
                                                                                            module.params.get('mtu'))
    # pyroute2 error to change interface to promiscuity option. Needs investigation
    # if module.params.get('promiscuity') is not None:
    #     try:
    #         ip.set_promiscuity(module.params.get('name'), int(module.params.get('promiscuity')))
    #         res_args_by_field['interface']['value'] = True
    #     except KeyError as k:
    #         module.fail_json(msg='Interface {0} does not exist.'.format(k.args[0]))
    #     except CommitException as c:
    #         # Bug in pyroute2?!?
    #         module.fail_json(msg='{0}.'.format(c.args[0]))
    #     except Exception as e:
    #         res_args_by_field['interface']['msg'] = 'Interface {0}, promiscuity already {1}'.format(e.args[0],
    #                                                                                                 module.params.get('promiscuity'))

    # ADDRESS OPERATION
    # -------------------------------------------
    if module.params.get('addr'):
        if module.params.get('addr') == 'present':
            try:
                ip.ip_operation(module.params.get('name'), module.params.get('ip'), 'add')
            except socket.error as skerr:
                module.fail_json(msg=skerr.args[0])
            except KeyError as k:
                module.fail_json(msg='Interface {0} does not exist.'.format(k.args[0]))
            except NetlinkError as neterr:
                if neterr.code == 105:
                    module.fail_json(msg='Interface {0} does not support add ip: {1}'.format(module.params.get('name'),
                                                                                             neterr.args[1]))
        elif module.params.get('addr') == 'absent':
            try:
                ip.ip_operation(module.params.get('name'), module.params.get('ip'), 'del')
            except socket.error as skerr:
                module.fail_json(msg=skerr.args[0])
            except KeyError as k:
                module.fail_json(msg='Interface {0} does not exist.'.format(k.args[0]))
        else:
            try:
                ip.flush(module.params.get('name'))
            except KeyError as k:
                module.fail_json(msg='Interface {0} does not exist.'.format(k.args[0]))

    # At least one item changed, return changed
    for item in res_args_by_field:
        if res_args_by_field[item]['value']:
            module.exit_json(changed=True, msg=res_args_by_field[item]['msg'])
    module.exit_json(changed=False)


if __name__ == '__main__':
    main()
