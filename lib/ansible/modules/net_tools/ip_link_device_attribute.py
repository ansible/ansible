#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019-2020, George Shuklin <george.shuklin@gmail.com>
# this code is partially based on ip_netns.py code by
# (c) 2017, Arie Bregman <abregman@redhat.com>

# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: ip_link_device_attribute
version_added: "2.10"
author: "George Shuklin (@amarao)"
short_description: Set link-level properties for network interfaces for Linux
requirements: [iproute2]
description: >
    Supports the querying and modification of the link-level attributes of
    interfaces such as administrative state (up/down), MTU, arp, multicast,
    promisc, txqueuelen, address, broadcast, netns, alias.
    Does not currently support some features of ip link set, such as
    allmulticast, dynamic, protodown, trailers, link-netnsid, xdp, xdpgeneric,
    xdpdrv, xdpoffload, master/nomaster, addrgenmode, macaddr, vrf.

options:
    name:
        type: str
        aliases: [device]
        description:
            - Name of the network device.
            - Exactly one of I(name) or I(group_id) must be provided.

    group_id:
        type: str
        description:
            - Id of group of interfaces.
            - Settings are applied for all interfaces in the group.
            - Exactly one of I(name) or I(group_id) must be provided.

    namespace:
        type: str
        description:
            - Name of namespace where interface is present.
            - To modify the namespace use I(netns) options.

    state:
        type: str
        choices: [up, down]
        description:
            - Controls the state of interface. Up or down.

    arp:
        type: bool
        description:
            - Enable or disable ARP on an interface.

    multicast:
        type: bool
        description:
            - Enable or disable mutliscast for the interface.

    promisc:
        type: bool
        description:
            - Enable or disable promiscuous mode for the interface.

    txqueuelen:
        type: int
        description:
            - Set transmit queue length of the interface.
            - Default value for kernel is usually 1000.

    mtu:
        type: int
        description:
            - Set MTU value for interface.
            - Default value is defined by the kernel and it is 1500.
            - This is the L3 MTU (limit on size of IP packets).

    address:
        type: str
        description:
            - The MAC address (L2 address) for the interface.
            - Some interfaces can not have L2 address. Module will fail
              if address is specified for interface without L2 address
              support (for example 'type vcan').

    broadcast:
        type: str
        description:
            - The broadcast (L2) address for the interface.
            - The usual value is 'ff:ff:ff:ff:ff:ff'.
            - Some addresses have no broadcast support. Module will fail
              if broadcast is specified for interface without broadcast
              support (for example 'type vcan').

    netns:
        type: str
        description:
            - Set the namespace for an interface.
            - If both I(namespace) and I(netns) are set, the module
              will try to move interface from namespace I(namespace)
              into namespace I(netns).
            - Note, when the interface changes namespace it loses
              many of its properties (group, state, etc).
            - This option should not be mixed up with I(namespace).

    alias:
        type: str
        description:
            - Set or change the alias for the interface.
            - If no alias is specified, it does not change.
            - Removing aliases from an interface is not currently supported.

    group:
        type: str
        description:
            - Set or change group id for ther interface.
            - Interfaces in the same group can be addressed by
              I(group_id) parameter.
            - Group is a number or a name from /etc/iproute2/groups.
            - You can not change a group for a pre-existing group of interfaces
              (the I(group) and I(group_id) options are mutually exclusive).
"""

EXAMPLES = """
- name: Bring up eth0
  ip_link_device_attribute:
    device: eth0
    state: up

- name: Disable arp for fab in namespace jos
  ip_link_device_attribute:
    name: fab0
    namespace: jos
    arp: off

- name: Bring up and enable promisc mode and disable multicast
  ip_link_device_attribute:
    name: eth4
    state: up
    promisc: true
    multicast: false

- name: Reduce tx queue length
  ip_link_device_attribute:
     name: wlan0
     txqueuelen: 1

- name: Enable jumbo frames
  ip_link_device_attribute:
    name: bond0
    mtu: 8972

- name: Change mac and broadcast address for interface
  ip_link_device_attribute:
    name: wlan0
    address: ba:d0:ba:d0:ba:d0
    broadcast: ff:ff:ff:ff:ff:ff

- name: Move interface veth1 into namespace steam
  ip_link_device_attribute:
    name: veth1
    netns: steam

- name: Move interface veth1 from namespace steam into namespace debug
  ip_link_device_attribute:
    name: veth1
    namespace: steam
    netns: debug

- name: Enable promisc for interface
  ip_link_device_attribute:
    name: eno4
    promisc: true

- name: Assign group 42 to interfaces eth1 and eth0
  ip_link_device_attribute:
    name: '{{ item }}'
    group: '42'
  loop: ['eth0', 'eth1']

- name: Turn down all interfaces in group 42
  ip_link_device_attribute:
    group_id: '42'
    state: down

- name: Gather information about interfaces in default group in namespace foo
  ip_link_device_attribute:
    group_id: default
    namespace: foo
  register: foo_if_info

- name: Move interface into namespace foo and set it
  ip_link_device_attribute:
    name: eth3
    netns: foo
    state: up
    mtu: 8172
    arp: false
    promisc: true
    address: ba:ba:ba:ba:ba:ba
    group: '12'
"""

RETURN = """
interfaces:
    description: A list of all interfaces matching the I(group_id)
                 (or a list with a single interface for I(name))
    returned: success
    type: complex
    sample:
    contains:
      name:
        description: Name of the interface.
        type: str
      group:
        description: Group of the interface.
        type: str
      arp:
        description: State of ARP protocol for the interface.
        type: bool
      mtu:
        description: MTU value for the interface.
        type: int
      multicast:
        description: State of multicast for the interface.
        type: bool
      promisc:
        description: State of promisc mode for the interface.
        type: bool
      txqueuelen:
        description: Length of the TX queue.
        type: int
      state:
        description: Administrative state for interface, C(up) or C(down).
        type: str
      address:
        description: L2 address fof the interface
                     (may be C(None), if the interface can not have one).
        type: str
      broadcast:
        description: L2 broadcast address for the interface
                     (may be C(None), if the interface can not have one).
        type: str
      alias:
        description: Alias for the interface (C(None) if not present).
        type: str
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text


__metaclass__ = type


class Link(object):
    """Interface to 'link' object."""

    params_list = [  # module paramtes needed special treatment
        'group_id', 'namespace', 'name', 'netns'
    ]
    knob_cmds = {  # attributes we may change by calling 'ip'
        'address': lambda addr: ['address', str(addr)],
        'alias': lambda alias: ['alias', str(alias)],
        'arp': lambda is_arp: ['arp', ['off', 'on'][is_arp]],
        'broadcast': lambda addr: ['broadcast', addr],
        'group': lambda group: ['group', str(group)],
        'mtu': lambda mtu: ['mtu', str(mtu)],
        'multicast': lambda is_mc: ['multicast', ['off', 'on'][is_mc]],
        'promisc': lambda is_prms: ['promisc', ['off', 'on'][is_prms]],
        'txqueuelen': lambda qlen: ['txqueuelen', str(qlen)],
        'state': lambda state: [state],
    }

    def __init__(self, module):
        self.module = module
        self.check_mode = module.check_mode
        self.knobs = {}
        for knob in self.knob_cmds.keys():
            self.knobs[knob] = module.params[knob]
        for param in self.params_list:
            setattr(self, param, module.params[param])
        if self.name:
            self.id_postfix = ['dev', self.name]
        if self.group_id:
            self.id_postfix = ['group', self.group_id]
        if self.knobs['address']:
            self.knobs['address'] = self.knobs['address'].lower()
        if self.knobs['broadcast']:
            self.knobs['broadcast'] = self.knobs['broadcast'].lower()
        if self.knobs['state']:
            self.knobs['state'] = self.knobs['state'].lower()

    def _exec(self, namespace, cmd, not_found_is_ok=False):
        if namespace:
            return self._exec(
                None,
                ['ip', 'netns', 'exec', namespace] + cmd,
                not_found_is_ok
            )
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            if not_found_is_ok:
                # show for non-existing group  return empty output
                # show for non-existing device yield a specific error
                if self.name:
                    not_found_msg = 'Device "%s" does not exist' % self.name
                    if not_found_msg in err:
                        return ''
            self.module.fail_json(
                msg=to_text(err),
                failed_command=' '.join(cmd)
            )
        return out

    def _split_ifline(self, ifstring):
        _ifnum, ifname_raw, raw_data = ifstring.split(':', 2)
        ifname = ifname_raw.split('@')[0].strip()
        data = list(map(str.split, raw_data.split('\\')))

        retval = {
            'name': ifname,
            'flags': data[0].pop(0).strip('<>').split(',')
        }
        for snip in data:
            while snip:
                key = snip.pop(0)
                if not snip:
                    break
                value = snip.pop(0)
                retval[key] = value

        return retval

    def _parse_interface(self, ifstring):
        if not ifstring:
            return {}
        iface = self._split_ifline(ifstring)
        flags = iface['flags']
        multicast = 'MULTICAST' in flags
        is_up = 'UP' in flags
        arp = not ('NOARP' in flags)
        promisc = 'PROMISC' in flags
        return {
            'address': iface.get('link/ether', None),
            'alias': iface.get('alias', None),
            'arp': arp,
            'broadcast': iface.get('brd', None),
            'group': iface['group'],
            'mtu': int(iface['mtu']),
            'multicast': multicast,
            'name': iface['name'],
            'promisc': promisc,
            'txqueuelen': int(iface['qlen']),
            'state': ['down', 'up'][int(is_up)],
        }

    def _get_interfaces_info(self, namespace, not_found_is_ok=False):
        # we can't use json option of ip command
        # because of Centos6.
        # It's so young and so forever.
        cmd = ['ip', '-o', 'link', 'show'] + self.id_postfix
        output = self._exec(namespace, cmd, not_found_is_ok)
        interfaces = filter(
            lambda x: x,
            map(self._parse_interface, output.strip().split('\n'))
        )
        return interfaces

    def _is_changes_needed_for_interface(self, iface):
        attr_list = [  # address and broadcast are handled separately
            'alias', 'arp', 'group', 'mtu', 'multicast',
            'promisc', 'txqueuelen', 'state'
        ]
        for attr in attr_list:
            if self.knobs[attr] and self.knobs[attr] != iface[attr]:
                return True
        if self.knobs['broadcast'] and \
                self.knobs['broadcast'] != iface['broadcast']:
            if not iface['broadcast']:
                self.module.fail_json(msg=to_text(
                    'Interace %s can not have broadcast address'
                ) % (iface['name']))
            return True
        if self.knobs['address'] and \
                self.knobs['address'] != iface['address']:
            if not iface['address']:
                self.module.fail_json(msg=to_text(
                    'Interace %s can not have MAC address'
                ) % (iface['name']))
            return True
        return False

    def _is_changes_needed(self, iflist):
        return any(map(self._is_changes_needed_for_interface, iflist))

    def _apply_change(self, knob, value):
        cmd = ['ip', 'link', 'set'] + self.id_postfix
        cmd += self.knob_cmds[knob](value)
        self._exec(self.namespace, cmd)

    def _apply_changes(self):
        for knob, value in self.knobs.items():
            if value is None:
                continue
            self._apply_change(knob, value)

    def _get_iface_set(self, namespace):
        iface_list = self._get_interfaces_info(namespace, not_found_is_ok=True)
        return set(map(lambda x: x['name'], iface_list))

    def _netns_need_to_move(self):
        """
            When we need to change netns for the interface(s),
            there are few scenarios to consider:
            1. There is target interface in source 'namespace'
                and not target interface in destination 'netns'
                    -> change netns for interface
            2. There is a target interface in srouce 'namespace'
                and there is a target interface in destination 'netns'
                    -> Error
            3. There is no target interface in source 'namespace'
                and there is a target interface in destination 'netns'
                    -> no change (in this part)
            4. There is no target interface in source 'namespace'
                and there is no target interface in destination 'netns'
                    -> Error

            Additionally, we need to support partial cases with
            group_id (some of interfaces may be in one namespace
            and some may be moved already).
        """
        if self.namespace == self.netns:
            return False
        src = self._get_iface_set(self.namespace)
        dst = self._get_iface_set(self.netns)
        if src.intersection(dst):
            self.module.fail_json(
                msg='Interfaces %s are in both namespaces' %
                src.intersection(dst))
        if not src and not dst:
            self.module.fail_json(
                msg='Unable to find interface %s to change namespace' %
                ' '.join(self.id_postfix)
            )
        return bool(src)

    def _move(self):
        """If we moved the interface from
        one namespace into another, we need to apply
        the rest of parameters in the new namespace,
        so we need to update self.namespace parameter.
        """

        cmd = ['ip', 'link', 'set'] + self.id_postfix + ['netns', self.netns]
        self._exec(self.namespace, cmd)

    def run(self):
        changed = False
        if self.netns:
            if self._netns_need_to_move():
                if self.check_mode:
                    interfaces = self._get_interfaces_info(self.namespace)
                    return self.module.exit_json(
                        changed=True, interfaces=list(interfaces)
                    )
                self._move()
            self.namespace = self.netns
            self.netns = None
        interfaces_info = self._get_interfaces_info(self.namespace)
        if self._is_changes_needed(interfaces_info):
            changed = True
            if not self.check_mode:
                self._apply_changes()
        interfaces = self._get_interfaces_info(self.namespace)
        self.module.exit_json(changed=changed, interfaces=list(interfaces))


def main():
    """Entry point."""
    module = AnsibleModule(
        argument_spec={
            'name': {'aliases': ['device']},
            'group_id': {},
            'namespace': {},
            'state': {'choices': ['up', 'down']},
            'arp': {'type': 'bool'},
            'multicast': {'type': 'bool'},
            'promisc': {'type': 'bool'},
            'txqueuelen': {'type': 'int'},
            'mtu': {'type': 'int'},
            'address': {},
            'broadcast': {},
            'netns': {},
            'alias': {},
            'group': {}
        },
        supports_check_mode=True,
        mutually_exclusive=[['group_id', 'group'], ['name', 'group_id']],
        required_one_of=[['name', 'group_id']]
    )

    link = Link(module)
    link.run()


if __name__ == '__main__':
    main()
