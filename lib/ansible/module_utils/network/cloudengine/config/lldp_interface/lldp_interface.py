#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ce_lldp_interface class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.cloudengine.ce import set_nc_config
from ansible.module_utils.network.cloudengine.facts.facts import Facts
from ansible.module_utils.network.common.netconf import build_root_xml_node, build_child_xml_node

try:
    from lxml.etree import tostring
except ImportError:
    from xml.etree.ElementTree import tostring


class LldpInterface(ConfigBase):
    """
    The ce_lldp_interface class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lldp_interface',
    ]

    tlv_tag_param = {'management_addr': 'manAddrTxEnable',
                     'port_desc': 'portDescTxEnable',
                     'system_capability': 'sysCapTxEnable',
                     'system_description': 'sysDescTxEnable',
                     'system_name': 'sysNameTxEnable',
                     'port_vlan_enable': 'portVlanTxEnable',
                     'prot_vlan_enable': 'protoVlanTxEnable',
                     'prot_vlan_id': 'txProtocolVlanId',
                     'vlan_name_enable': 'vlanNameTxEnable',
                     'vlan_name': 'txVlanNameId',
                     'link_aggregation': 'linkAggreTxEnable',
                     'mac_physic': 'macPhyTxEnable',
                     'max_frame_size': 'maxFrameTxEnable',
                     'eee': 'eee'
                     }

    def __init__(self, module):
        super(LldpInterface, self).__init__(module)

    def get_lldp_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        lldp_interface_facts = facts['ansible_network_resources'].get('lldp_interface')
        if not lldp_interface_facts:
            return []
        return lldp_interface_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()

        existing_lldp_facts = self.get_lldp_facts()
        commands = self.set_config(existing_lldp_facts)
        if commands:
            if not self._module.check_mode:
                set_nc_config(self._module, commands)
            result['changed'] = True

        changed_lldp_facts = self.get_lldp_facts()
        result['before'] = existing_lldp_facts
        
        if result['changed']:
            result['after'] = changed_lldp_facts
        result['warnings'] = warnings
        result['commands'] = self.get_update_commands(existing_lldp_facts, changed_lldp_facts)
        return result

    def get_update_commands(self, existing_lldp_facts, changed_lldp_facts):
        commands = []
        existing_msg_int = existing_lldp_facts.get('msg_interval')
        changed_msg_int = changed_lldp_facts.get('msg_interval')
        changed_msg_ad = changed_lldp_facts.get('admin_status')
        existing_msg_ad = existing_lldp_facts.get('admin_status')
        existing_basic_tlv = existing_lldp_facts.get('basic_tlv')
        changed_basic_tlv = changed_lldp_facts.get('basic_tlv')
        existing_dot1_tlv = existing_lldp_facts.get('dot1_tlv')
        changed_dot1_tlv = changed_lldp_facts.get('dot1_tlv')
        existing_dot3_tlv = existing_lldp_facts.get('dot3_tlv')
        changed_dot3_tlv = changed_lldp_facts.get('dot3_tlv')

        if existing_msg_int != changed_msg_int and changed_msg_int is not None:
            commands.append('lldp transmit fast-mode interval %s' % changed_msg_int)

        if changed_msg_ad != existing_msg_ad and changed_msg_ad is not None:
            if changed_msg_ad.lower() == 'txonly':
                commands.append('lldp admin-status tx')
            elif changed_msg_ad.lower() == 'rxonly':
                commands.append('lldp admin-status rx')
            elif changed_msg_ad.lower() == 'txandrx':
                commands.append('lldp admin-status txrx')

        if existing_basic_tlv != changed_basic_tlv and changed_basic_tlv is not None:
            existing_basic_tlv = existing_basic_tlv or {}
            if existing_basic_tlv.get('management_addr') != changed_basic_tlv.get('management_addr'):
                if changed_basic_tlv.get('management_addr') is True:
                    commands.append('undo lldp tlv-disable basic-tlv management-address')
                elif changed_basic_tlv.get('management_addr') is False:
                    commands.append('lldp tlv-disable basic-tlv management-address')
            if existing_basic_tlv.get('port_desc') != changed_basic_tlv.get('port_desc'):
                if changed_basic_tlv.get('port_desc') is True:
                    commands.append('undo lldp tlv-disable basic-tlv port-description')
                elif changed_basic_tlv.get('port_desc') is False:
                    commands.append('lldp tlv-disable basic-tlv port-description')
            if existing_basic_tlv.get('system_capability') != changed_basic_tlv.get('system_capability'):
                if changed_basic_tlv.get('system_capability') is True:
                    commands.append('undo lldp tlv-disable basic-tlv system-capability')
                elif changed_basic_tlv.get('system_capability') is False:
                    commands.append('lldp tlv-disable basic-tlv port-description')
            if existing_basic_tlv.get('system_description') != changed_basic_tlv.get('system_description'):
                if changed_basic_tlv.get('system_description') is True:
                    commands.append('undo lldp tlv-disable basic-tlv system-description')
                elif changed_basic_tlv.get('system_description') is False:
                    commands.append('lldp tlv-disable basic-tlv system-description')
            if existing_basic_tlv.get('system_name') != changed_basic_tlv.get('system_name'):
                if changed_basic_tlv.get('system_name') is True:
                    commands.append('undo lldp tlv-disable basic-tlv system-name')
                elif changed_basic_tlv.get('system_name') is False:
                    commands.append('lldp tlv-disable basic-tlv system-name')

        if existing_dot1_tlv != changed_dot1_tlv and changed_dot1_tlv is not None:
            existing_dot1_tlv = existing_dot1_tlv or {}
            if existing_dot1_tlv.get('port_vlan_enable') != changed_dot1_tlv.get('port_vlan_enable'):
                if changed_dot1_tlv.get('port_vlan_enable') is True:
                    commands.append('undo lldp tlv-disable dot1-tlv port-vlan-id')
                elif changed_dot1_tlv.get('port_vlan_enable') is False:
                    commands.append('lldp tlv-disable dot1-tlv port-vlan-id')
            if existing_dot1_tlv.get('prot_vlan_enable') != changed_dot1_tlv.get('prot_vlan_enable'):
                if changed_dot1_tlv.get('prot_vlan_enable') is True:
                    cmd = 'undo lldp tlv-disable dot1-tlv protocol-vlan-id'
                elif changed_dot1_tlv.get('prot_vlan_enable') is False:
                    cmd = 'lldp tlv-disable dot1-tlv protocol-vlan-id'
                if existing_dot1_tlv.get('prot_vlan_id') != changed_dot1_tlv.get('prot_vlan_id'):
                    if changed_dot1_tlv.get('prot_vlan_id') is not None:
                        cmd = '%s %s' % (cmd, changed_dot1_tlv['prot_vlan_id'])
                commands.append(cmd)
            if existing_dot1_tlv.get('vlan_name_enable') != changed_dot1_tlv.get('vlan_name_enable'):
                if changed_dot1_tlv.get('vlan_name_enable') is True:
                    cmd = 'undo lldp tlv-disable dot1-tlv vlan-name'
                elif changed_dot1_tlv.get('vlan_name_enable') is False:
                    cmd = 'lldp tlv-disable dot1-tlv vlan-name'
                if existing_dot1_tlv.get('vlan_name') != changed_dot1_tlv.get('vlan_name'):
                    if changed_dot1_tlv.get('vlan_name') is not None:
                        cmd = '%s %s' % (cmd, changed_dot1_tlv['vlan_name'])
                commands.append(cmd)

        if existing_dot3_tlv != changed_dot3_tlv and changed_dot3_tlv is not None:
            existing_dot3_tlv = existing_dot3_tlv or {}
            if existing_dot3_tlv.get('link_aggregation') != changed_dot3_tlv.get('link_aggregation'):
                if changed_dot3_tlv.get('link_aggregation') is True:
                    commands.append('undo lldp tlv-disable dot3-tlv link-aggregation')
                elif changed_dot3_tlv.get('link_aggregation') is False:
                    commands.append('lldp tlv-disable dot3-tlv  dot1-tlv')
            if existing_dot3_tlv.get('mac_physic') != changed_dot3_tlv.get('mac_physic'):
                if changed_dot3_tlv.get('mac_physic') is True:
                    commands.append('undo lldp tlv-disable dot3-tlv mac-physic')
                elif changed_dot3_tlv.get('mac_physic') is False:
                    commands.append('lldp tlv-disable dot3-tlv mac-physic')
            if existing_dot3_tlv.get('max_frame_size') != changed_dot3_tlv.get('max_frame_size'):
                if changed_dot3_tlv.get('max_frame_size') is True:
                    commands.append('undo lldp tlv-disable dot3-tlv max-frame-size')
                elif changed_dot3_tlv.get('max_frame_size') is False:
                    commands.append('lldp tlv-disable dot3-tlv max-frame-size ')
            if existing_dot3_tlv.get('eee') != changed_dot3_tlv.get('eee'):
                if changed_dot3_tlv.get('eee') is True:
                    commands.append('undo lldp tlv-disable dot3-tlv eee')
                elif changed_dot3_tlv.get('eee') is False:
                    commands.append('lldp tlv-disable dot3-tlv eee')

        return commands

    def set_config(self, existing_lldp_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_lldp_facts
        resp = self._state_merged(want, have)
        if resp is not None:
            return """<config>
                      <lldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
                         <lldpInterfaces>
                         %s
                         </lldpInterfaces>
                      </lldp>
                   </config>""" % tostring(resp)
        return None

    def _bulid_node(self, parent, want, have):
        state = self._module.params['state']
        for key, tag in iteritems(self.tlv_tag_param):
            if want.get(key) != have.get(key) and want.get(key) is not None:
                value = str(want.get(key)).lower()
                if state == 'absent':
                    if key not in ('prot_vlan_id', 'vlan_name'):
                        # set default value
                        value = 'true'
                    else:
                        # some has no default.
                        value = ''
                build_child_xml_node(parent, tag, value)

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A xml object
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        state = self._module.params['state']
        interface = build_root_xml_node('interface')
        build_child_xml_node(interface, 'ifName', want['ifname'])
        want_config = False
        if want.get('admin_status') is not None and want.get('admin_status') != have.get('admin_status'):
            want_config = True
            if state == 'present':
                build_child_xml_node(interface, 'ifName', want['admin_status'])
            elif state == 'absent':
                build_child_xml_node(interface, 'ifName', 'txAndRx')

        if want.get('msg_interval') is not None and want.get('msg_interval') != have.get('msg_interval'):
            want_config = True
            msg_interval = build_child_xml_node(interface, 'msgInterval', None)
            msg_interval.set('operation', 'merge')
            if state == 'present':
                build_child_xml_node(msg_interval, 'txInterval', want['msg_interval'])
            # state absent: set up default value, default value will depend on global set.
            tlv = build_root_xml_node('tlvTxEnable')
            self._bulid_node(tlv, want, have)
            if len(tlv) > 0:
                want_config = True
                tlv.set('operation', 'merge')
                interface.append(tlv)
        if want_config is True:
            return interface
        return None
