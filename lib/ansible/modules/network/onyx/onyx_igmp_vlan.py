#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: onyx_igmp_vlan
version_added: '2.8'
author: Anas Badaha (@anasbadaha)
short_description: Configures IGMP Vlan parameters
description:
  - This module provides declarative management of IGMP vlan configuration on Mellanox ONYX network devices.
notes:
  - Tested on ONYX 3.7.0932-01
options:
  vlan_id:
    description:
      - VLAN ID, vlan should exist.
    required: true
  state:
    description:
      - IGMP state.
    choices: ['enabled', 'disabled']
    default: enabled
  mrouter:
    description:
      - Configure ip igmp snooping mrouter port on vlan
    suboptions:
      state:
        description:
          - Enable IGMP snooping mrouter on vlan interface.
        choices: ['enabled', 'disabled']
        default: enabled
      name:
        description:
          - Configure mrouter interface
        required: true
  querier:
    description:
      - Configure the IGMP querier parameters
    suboptions:
      state:
        description:
          - Enable IGMP snooping querier on vlan in the switch.
        choices: ['enabled', 'disabled']
        default: enabled
      interval:
        description:
          - Update time interval between querier queries, range 60-600
      address:
        description:
          - Update IP address for the querier
  static_groups:
    description:
      - List of IGMP static groups.
    suboptions:
      multicast_ip_address:
        description:
          - Configure static IP multicast group, range 224.0.1.0-239.255.255.25.
        required: true
      name:
        description:
          - interface name to configure static groups on it.
      sources:
        description:
          - List of IP sources to be configured
  version:
    description:
      - IGMP snooping operation version on this vlan
    choices: ['V2','V3']
"""

EXAMPLES = """
- name: configure igmp vlan
  onyx_igmp_vlan:
    state: enabled
    vlan_id: 10
    version:
      V2
    querier:
      state: enabled
      interval: 70
      address: 10.11.121.13
    mrouter:
      state: disabled
      name: Eth1/2
    static_groups:
      - multicast_ip_address: 224.5.5.8
        name: Eth1/1
        sources:
          - 1.1.1.1
          - 1.1.1.2
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - vlan 10 ip igmp snooping
    - vlan 10 ip igmp snooping static-group 224.5.5.5 interface ethernet 1/1
"""
import socket
import struct

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.onyx.onyx import show_cmd
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule


def _ip_to_int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]


class OnyxIgmpVlanModule(BaseOnyxModule):
    MIN_MULTICAST_IP = _ip_to_int("224.0.1.0")
    MAX_MULTICAST_IP = _ip_to_int("239.255.255.255")

    def init_module(self):
        """ initialize module
        """
        mrouter_spec = dict(name=dict(required=True),
                            state=dict(choices=['enabled', 'disabled'], default='enabled'))
        querier_spec = dict(state=dict(choices=['enabled', 'disabled'], default='enabled'),
                            interval=dict(type='int'), address=dict())
        static_groups_spec = dict(multicast_ip_address=dict(required=True),
                                  name=dict(required=True), sources=dict(type='list'))
        element_spec = dict(vlan_id=dict(type='int', required=True),
                            state=dict(choices=['enabled', 'disabled'], default='enabled'),
                            querier=dict(type='dict', options=querier_spec),
                            static_groups=dict(type='list', elements='dict', options=static_groups_spec),
                            mrouter=dict(type='dict', options=mrouter_spec),
                            version=dict(choices=['V2', 'V3']))
        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def get_required_config(self):
        module_params = self._module.params
        self._required_config = dict(module_params)
        self.validate_param_values(self._required_config)

    def _validate_attr_is_not_none(self, attr_name, attr_value):
        if attr_name == 'vlan_id' or attr_name == 'state':
            pass
        elif attr_value is not None:
            self._module.fail_json(msg='Can not set %s value on switch while state is disabled' % attr_name)

    def validate_param_values(self, obj, param=None):
        if obj['state'] == 'disabled':
            for attr_name in obj:
                self._validate_attr_is_not_none(attr_name, obj[attr_name])
        super(OnyxIgmpVlanModule, self).validate_param_values(obj, param)

    def validate_querier(self, value):
        interval = value.get('interval')
        if interval and not 60 <= int(interval) <= 600:
            self._module.fail_json(msg='query-interval value must be between 60 and 600')

    def validate_static_groups(self, value):
        multicast_ip = value.get('multicast_ip_address')
        multicast_ip = _ip_to_int(multicast_ip)

        if multicast_ip < self.MIN_MULTICAST_IP or multicast_ip > self.MAX_MULTICAST_IP:
            self._module.fail_json(msg='multicast IP address must be in range 224.0.1.0 - 239.255.255.255')

    @staticmethod
    def _get_curr_mrouter_config(mrouter_port):
        if mrouter_port == "none":
            return {'state': 'disabled'}
        else:
            return {'state': 'enabled',
                    'name': mrouter_port}

    def _get_curr_querier_config(self, querier_config):
        if "Non-Querier" in querier_config:
            return {'state': 'disabled'}
        elif "Querier" in querier_config:
            igmp_querier_config = self._show_igmp_querier_config()[0]
            snooping_querier_info = igmp_querier_config["Snooping querier information for VLAN %d" % (
                self._required_config['vlan_id'])]
            snooping_querier_info = snooping_querier_info[1]
            interval = int(snooping_querier_info["Query interval"])
            address = snooping_querier_info["Configured querier IP address"]
            return {'state': 'enabled',
                    'interval': interval,
                    'address': address}

    @staticmethod
    def _get_curr_version(version):
        if "V3" in version:
            return "V3"
        elif "V2" in version:
            return "V2"

    def _get_curr_static_group_config(self, multicast_ip_address):
        sources = None
        names = None
        igmp_snooping_groups_config = self._show_igmp_snooping_groups_config(multicast_ip_address)
        if igmp_snooping_groups_config is not None:
            igmp_snooping_groups_config = igmp_snooping_groups_config[0]
            snooping_group_information = igmp_snooping_groups_config.get('Snooping group '
                                                                         'information for VLAN %d and group '
                                                                         '%s' % (self._required_config['vlan_id'],
                                                                                 multicast_ip_address))
            if snooping_group_information is not None:
                if len(snooping_group_information) == 1:
                    names = snooping_group_information[0].get('V1/V2 Receiver Ports')
                elif len(snooping_group_information) == 2:
                    sources_dict = dict()
                    v3_receiver_ports = snooping_group_information[1].get('V3 Receiver Ports')
                    ports_number = v3_receiver_ports[0].get('Port Number')
                    sources = v3_receiver_ports[0].get('Include sources')
                    if isinstance(ports_number, list):
                        i = 0
                        for port_number in ports_number:
                            sources_dict[port_number] = sources[i]
                            i += 1
                    else:
                        sources_dict[ports_number] = sources
                    names = snooping_group_information[0].get('V1/V2 Receiver Ports')
                    sources = sources_dict

                return {'sources': sources,
                        'names': names}
            else:
                return None
        else:
            return None

    def _set_igmp_config(self, igmp_vlan_config):
        igmp_vlan_config = igmp_vlan_config[0]
        if not igmp_vlan_config:
            return

        self._current_config['state'] = igmp_vlan_config.get('message 1')
        if "enabled" in self._current_config['state']:
            self._current_config['state'] = "enabled"
        elif "disabled" in self._current_config['state']:
            self._current_config['state'] = "disabled"

        mrouter_port = igmp_vlan_config.get('mrouter static port list')
        self._current_config['mrouter'] = dict(self._get_curr_mrouter_config(mrouter_port))

        querier_config = igmp_vlan_config.get('message 3')
        self._current_config['querier'] = dict(self._get_curr_querier_config(querier_config))

        version = igmp_vlan_config.get('message 2')
        self._current_config['version'] = self._get_curr_version(version)

        req_static_groups = self._required_config.get('static_groups')
        if req_static_groups is not None:
            static_groups = self._current_config['static_groups'] = dict()
            for static_group in req_static_groups:
                static_group_config = self._get_curr_static_group_config(static_group['multicast_ip_address'])
                static_groups[static_group['multicast_ip_address']] = static_group_config

    def _show_igmp_vlan(self):
        cmd = ("show ip igmp snooping vlan %d" % self._required_config['vlan_id'])
        return show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False)

    def _show_igmp_querier_config(self):
        cmd = ("show ip igmp snooping querier vlan %d " % self._required_config['vlan_id'])
        return show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False)

    def _show_igmp_snooping_groups_config(self, multicast_ip_address):
        cmd = ("show ip igmp snooping groups vlan %d group %s" % (self._required_config['vlan_id'],
                                                                  multicast_ip_address))
        return show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False)

    def load_current_config(self):
        self._current_config = dict()
        igmp_vlan_config = self._show_igmp_vlan()
        if igmp_vlan_config:
            self._set_igmp_config(igmp_vlan_config)

    def generate_commands(self):
        req_state = self._required_config.get('state', 'enabled')
        self._generate_igmp_vlan_cmds(req_state)

        _mrouter = self._required_config.get('mrouter')
        if _mrouter is not None:
            self._generate_igmp_mrouter_cmds(_mrouter)

        _querier = self._required_config.get('querier')
        if _querier is not None:
            req_querier_state = _querier.get('state', 'enabled')
            self._generate_igmp_querier_cmds(req_querier_state)

            req_querier_interval = _querier.get('interval')
            if req_querier_interval is not None:
                self._gen_querier_attr_commands("interval", req_querier_interval, "query-interval")

            req_querier_address = _querier.get('address')
            if req_querier_address is not None:
                self._gen_querier_attr_commands("address", req_querier_address, "address")

        _version = self._required_config.get('version')
        if _version is not None:
            self._generate_igmp_version_cmds(_version)

        _static_groups = self._required_config.get('static_groups')
        if _static_groups is not None:
            for static_group in _static_groups:
                self._generate_igmp_static_groups_cmd(static_group)

    def _add_igmp_vlan_commands(self, req_state):
        if req_state == 'enabled':
            igmp_vlan_cmd = 'vlan %d ip igmp snooping' % self._required_config['vlan_id']
        else:
            igmp_vlan_cmd = 'vlan %d no ip igmp snooping' % self._required_config['vlan_id']

        self._commands.append(igmp_vlan_cmd)

    def _generate_igmp_vlan_cmds(self, req_state):
        curr_state = self._current_config.get('state')
        if curr_state != req_state:
            self._add_igmp_vlan_commands(req_state)

    def _gen_querier_attr_commands(self, attr_name, req_attr_value, attr_cmd_name):
        _curr_querier = self._current_config.get('querier')
        curr_querier_val = _curr_querier.get(attr_name)
        if req_attr_value != curr_querier_val:
            self._commands.append('vlan %d ip igmp snooping querier %s %s' % (self._required_config['vlan_id'],
                                                                              attr_cmd_name, req_attr_value))

    def _add_querier_commands(self, req_querier_state):
        if req_querier_state == 'enabled':
            self._commands.append('vlan %d ip igmp snooping querier' % self._required_config['vlan_id'])
        elif req_querier_state == 'disabled':
            self._commands.append('vlan %d no ip igmp snooping querier' % (
                self._required_config['vlan_id']))

    def _generate_igmp_querier_cmds(self, req_querier_state):
        _curr_querier = self._current_config.get('querier')
        curr_querier_state = _curr_querier.get('state')
        if req_querier_state != curr_querier_state:
            self._add_querier_commands(req_querier_state)

    def _generate_igmp_version_cmds(self, version):
        _curr_version = self._current_config.get('version')
        if version != _curr_version:
            self._commands.append('vlan %d ip igmp snooping version %s' % (
                self._required_config['vlan_id'], version[1]))

    def _add_mrouter_commands(self, req_mrouter, curr_mrouter):
        curr_state = curr_mrouter.get('state')
        curr_interface = curr_mrouter.get('name')
        req_state = req_mrouter.get('state')
        req_interface = req_mrouter.get('name')
        mrouter_interface = req_interface.replace("Eth", "ethernet ")
        if curr_state == 'enabled' and req_state == 'disabled':
            self._commands.append('vlan %d no ip igmp snooping mrouter interface '
                                  '%s' % (self._required_config['vlan_id'], mrouter_interface))
        elif curr_state == 'disabled' and req_state == 'enabled':
            self._commands.append('vlan %d ip igmp snooping mrouter interface '
                                  '%s' % (self._required_config['vlan_id'], mrouter_interface))
        elif req_state == 'enabled' and curr_state == 'enabled' and req_interface != curr_interface:
            self._commands.append('vlan %d ip igmp snooping mrouter interface '
                                  '%s' % (self._required_config['vlan_id'], mrouter_interface))

    def _generate_igmp_mrouter_cmds(self, req_mrouter):
        curr_mrouter = self._current_config.get('mrouter')
        if curr_mrouter != req_mrouter:
            self._add_mrouter_commands(req_mrouter, curr_mrouter)

    def _add_igmp_static_groups_cmd(self, req_name, req_multicast_ip_address, curr_names):
        if curr_names is None:
            self._commands.append('vlan %d ip igmp snooping static-group %s interface %s' % (
                self._required_config['vlan_id'], req_multicast_ip_address, req_name.replace('Eth', 'ethernet ')))
        elif req_name.replace('E', 'e') not in curr_names:
            self._commands.append('vlan %d ip igmp snooping static-group %s interface %s' % (
                self._required_config['vlan_id'], req_multicast_ip_address, req_name.replace('Eth', 'ethernet ')))

    def _add_igmp_static_groups_sources_cmd(self, req_sources, req_name, req_multicast_ip_address, curr_sources):
        if curr_sources is None:
            for source in req_sources:
                self._commands.append('vlan %d ip igmp snooping static-group %s interface %s source %s' % (
                    self._required_config['vlan_id'], req_multicast_ip_address, req_name.replace('Eth', 'ethernet '),
                    source))
        else:
            curr_sources = curr_sources.get(req_name.replace('E', 'e'))
            if curr_sources is None:
                curr_sources = set([])
            else:
                curr_sources = set(x.strip() for x in curr_sources.split(','))
            sources_to_add = set(req_sources) - set(curr_sources)
            sources_to_remove = set(curr_sources) - set(req_sources)
            if len(sources_to_add) != 0:
                for source in sources_to_add:
                    self._commands.append('vlan %d ip igmp snooping static-group %s interface %s source %s' % (
                        self._required_config['vlan_id'], req_multicast_ip_address,
                        req_name.replace('Eth', 'ethernet '), source))
            if len(sources_to_remove) != 0:
                for source in sources_to_remove:
                    self._commands.append('vlan %d no ip igmp snooping static-group %s interface %s source %s' % (
                        self._required_config['vlan_id'], req_multicast_ip_address,
                        req_name.replace('Eth', 'ethernet '),
                        source))

    def _generate_igmp_static_groups_cmd(self, static_group):
        req_multicast_ip_address = static_group.get('multicast_ip_address')
        req_name = static_group.get('name')
        req_sources = static_group.get('sources')
        curr_static_groups = self._current_config.get('static_groups')
        curr_static_group = curr_static_groups.get(req_multicast_ip_address)
        curr_names = None
        curr_sources = None
        if curr_static_group is not None:
            curr_names = curr_static_group.get('names')
            curr_sources = curr_static_group.get('sources')

        self._add_igmp_static_groups_cmd(req_name, req_multicast_ip_address, curr_names)
        if req_sources is not None:
            self._add_igmp_static_groups_sources_cmd(req_sources, req_name, req_multicast_ip_address, curr_sources)


def main():
    """ main entry point for module execution
    """
    OnyxIgmpVlanModule.main()


if __name__ == '__main__':
    main()
