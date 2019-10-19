#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ce lldp ineterface fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re
from copy import deepcopy
from ansible.module_utils.network.common import utils
from ansible.module_utils.network.cloudengine.argspec.lldp_interface.lldp_interface import LldpInterfaceArgs
from ansible.module_utils.network.cloudengine.ce import get_nc_config
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_bytes
try:
    from lxml import etree
    HAS_LXML = True
except ImportError:
    HAS_LXML = False


class LldpInterfaceFacts(object):
    """ The ce lldp interface fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = LldpInterfaceArgs.argument_spec
        spec = deepcopy(self.argument_spec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        self.generated_spec = utils.generate_dict(facts_argument_spec)

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for lldp
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            lldp_interface_filter = """<filter type="subtree">
                              <lldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
                                <lldpInterfaces>
                                  <lldpInterface>
                                    <ifName>%s</ifName>
                                    <tlvTxEnable></tlvTxEnable>
                                    <msgInterval>
                                     <txInterval></txInterval>
                                    </msgInterval>
                                  </lldpInterface>
                                </lldpInterfaces>
                              </lldp>
                            </filter>""" % self._module.params['config']['ifname']
            data = get_nc_config(self._module, lldp_interface_filter)
            data = re.sub(r'xmlns=.+? ', '', data)
        if isinstance(data, string_types):
            data = etree.fromstring(to_bytes(data, errors='surrogate_then_replace'))
        config = deepcopy(self.generated_spec)
        lldp_ineterface = data.xpath('.//lldp/lldpInterfaces/lldpInterface')

        if lldp_ineterface:
            interface_status = lldp_ineterface[0]
            config['admin_status'] = str(utils.get_xml_conf_arg(interface_status, 'lldpAdminStatus')).lower()
            config['ifname'] = utils.get_xml_conf_arg(interface_status, 'ifName')

            msg_interval = interface_status.xpath('.//msgInterval')
            if msg_interval:
                config['msg_interval'] = utils.get_xml_conf_arg(msg_interval[0], 'txInterval')

            tlv_tx_enable = interface_status.xpath('.//tlvTxEnable')
            if tlv_tx_enable:
                tlv_root = tlv_tx_enable[0]
                basic_tlv = dict()
                basic_tlv['management_addr'] = utils.get_xml_conf_arg(tlv_root, 'manAddrTxEnable')
                basic_tlv['port_desc'] = utils.get_xml_conf_arg(tlv_root, 'portDescTxEnable')
                basic_tlv['system_capability'] = utils.get_xml_conf_arg(tlv_root, 'sysCapTxEnable')
                basic_tlv['system_description'] = utils.get_xml_conf_arg(tlv_root, 'sysDescTxEnable')
                basic_tlv['system_name'] = utils.get_xml_conf_arg(tlv_root, 'sysNameTxEnable')
                dot1_tlv = dict()
                dot1_tlv['port_vlan_enable'] = utils.get_xml_conf_arg(tlv_root, 'portVlanTxEnable')
                dot1_tlv['prot_vlan_enable'] = utils.get_xml_conf_arg(tlv_root, 'protoVlanTxEnable')
                dot1_tlv['prot_vlan_id'] = utils.get_xml_conf_arg(tlv_root, 'txProtocolVlanId')
                dot1_tlv['vlan_name_enable'] = utils.get_xml_conf_arg(tlv_root, 'vlanNameTxEnable')
                dot1_tlv['vlan_name'] = utils.get_xml_conf_arg(tlv_root, 'txVlanNameId')
                dot3_tlv = dict()
                dot3_tlv['link_aggregation'] = utils.get_xml_conf_arg(tlv_root, 'linkAggreTxEnable')
                dot3_tlv['mac_physic'] = utils.get_xml_conf_arg(tlv_root, 'macPhyTxEnable')
                dot3_tlv['max_frame_size'] = utils.get_xml_conf_arg(tlv_root, 'maxFrameTxEnable')
                dot3_tlv['eee'] = utils.get_xml_conf_arg(tlv_root, 'eee')
                config['basic_tlv'] = basic_tlv
                config['dot1_tlv'] = dot1_tlv
                config['dot3_tlv'] = dot3_tlv

        facts = {}
        params = utils.validate_config(self.argument_spec, {'config': utils.remove_empties(config)})
        facts['lldp_interface'] = utils.remove_empties(params['config'])
        ansible_facts['ansible_network_resources'].update(facts)

        return ansible_facts
