#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---

module: ce_lldp
version_added: "2.10"
short_description: Manages LLDP configuration on HUAWEI CloudEngine switches.
description:
    - Manages LLDP configuration on HUAWEI CloudEngine switches.
author:
    - xuxiaowei0512 (@CloudEngine-Ansible)
notes:
    - This module requires the netconf system service be enabled on the remote device being managed.
    - Recommended connection is C(netconf).
    - This module also works with C(local) connections for legacy playbooks.
options:
    lldpenable:
        description:
            - Set global LLDP enable state.
        required: false
        choices: ['enabled', 'disabled']
        type: str
    mdnstatus:
        description:
            - Set global MDN enable state.
        required: false
        choices: ['rxOnly', 'disabled']
        type: str
    interval:
        description:
            - Frequency at which LLDP advertisements are sent (in seconds).
        required: false
        type: int
    hold_multiplier:
        description:
            - Time multiplier for device information in neighbor devices.
        required: false
        type: int
    restart_delay:
        description:
            - Specifies the delay time of the interface LLDP module from disabled state to re enable.
        required: false
        type: int
    transmit_delay:
        description:
            - Delay time for sending LLDP messages.
        required: false
        type: int
    notification_interval:
        description:
            - Suppression time for sending LLDP alarm.
        required: false
        type: int
    fast_count:
        description:
            - The number of LLDP messages sent to the neighbor nodes by the specified device.
        required: false
        type: int
    mdn_notification_interval:
        description:
            - Delay time for sending MDN neighbor information change alarm.
        required: false
        type: int
    management_address:
        description:
            - The management IP address of LLDP.
        required: false
        default: null
        type: str
    bind_name:
        description:
            - Binding interface name.
        required: false
        default: null
        type: str
    state:
        description:
            - Manage the state of the resource.
        required: false
        default: present
        type: str
        choices: ['present','absent']
'''

EXAMPLES = '''
  - name: "Configure global LLDP enable state"
    ce_lldp:
      lldpenable: enabled

  - name: "Configure global MDN enable state"
    ce_lldp:
      mdnstatus: rxOnly

  - name: "Configure LLDP transmit interval and ensure global LLDP state is already enabled"
    ce_lldp:
      enable: enable
      interval: 32

  - name: "Configure LLDP transmit multiplier hold and ensure global LLDP state is already enabled"
    ce_lldp:
      enable: enable
      hold_multiplier: 5

  - name: "Configure the delay time of the interface LLDP module from disabled state to re enable"
    ce_lldp:
      enable: enable
      restart_delay: 3

  - name: "Reset the delay time for sending LLDP messages"
    ce_lldp:
      enable: enable
      transmit_delay: 4

  - name: "Configure device to send neighbor device information change alarm delay time"
    ce_lldp:
      lldpenable: enabled
      notification_interval: 6

  - name: "Configure the number of LLDP messages sent to the neighbor nodes by the specified device"
    ce_lldp:
      enable: enable
      fast_count: 5

  - name: "Configure the delay time for sending MDN neighbor information change alarm"
    ce_lldp:
      enable: enable
      mdn_notification_interval: 6
  - name: "Configuring the management IP address of LLDP"
    ce_lldp:
      enable: enable
      management_address: 10.1.0.1

  - name: "Configuring LLDP to manage the binding relationship between IP addresses and interfaces"
    ce_lldp:
      enable: enable
      bind_name: LoopBack2
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
                "lldpenable": "enabled",
                "mdnstatus": "rxOnly",
                "interval": "32",
                "hold_multiplier": "5",
                "restart_delay": "3",
                "transmit_delay": "4",
                "notification_interval": "6",
                "fast_count": "5",
                "mdn_notification_interval": "6",
                "management_address": "10.1.0.1",
                "bind_name": "LoopBack2",
                "state": "present"
            }
existing:
    description: k/v pairs of existing global LLDP configuration.
    returned: always
    type: dict
    sample: {
                "lldpenable": "disabled",
                "mdnstatus": "disabled"
            }
end_state:
    description: k/v pairs of global LLDP configuration after module execution.
    returned: always
    type: dict
    sample: {
                "lldpenable": "enabled",
                "mdnstatus": "rxOnly",
                "interval": "32",
                "hold_multiplier": "5",
                "restart_delay": "3",
                "transmit_delay": "4",
                "notification_interval": "6",
                "fast_count": "5",
                "mdn_notification_interval": "6",
                "management_address": "10.1.0.1",
                "bind_name": "LoopBack2"
            }
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: [
                "lldp enable",
                "lldp mdn enable",
                "lldp transmit interval 32",
                "lldp transmit multiplier 5",
                "lldp restart 3",
                "lldp transmit delay 4",
                "lldp trap-interval 6",
                "lldp fast-count 5",
                "lldp mdn trap-interval 6",
                "lldp management-address 10.1.0.1",
                "lldp management-address bind interface LoopBack 2"
            ]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
'''

import copy
import re
from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import set_nc_config, get_nc_config

CE_NC_GET_GLOBAL_LLDPENABLE_CONFIG = """
<filter type="subtree">
  <lldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <lldpSys>
      <lldpEnable></lldpEnable>
      <mdnStatus></mdnStatus>
    </lldpSys>
  </lldp>
</filter>
"""

CE_NC_MERGE_GLOBA_LLDPENABLE_CONFIG = """
<config>
  <lldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <lldpSys operation="merge">
      <lldpEnable>%s</lldpEnable>
    </lldpSys>
  </lldp>
</config>
"""

CE_NC_MERGE_GLOBA_MDNENABLE_CONFIG = """
<config>
  <lldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <lldpSys operation="merge">
      <mdnStatus>%s</mdnStatus>
    </lldpSys>
  </lldp>
</config>
"""

CE_NC_GET_GLOBAL_LLDP_CONFIG = """
<filter type="subtree">
  <lldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <lldpSys>
      <lldpSysParameter>
        <messageTxInterval></messageTxInterval>
        <messageTxHoldMultiplier></messageTxHoldMultiplier>
        <reinitDelay></reinitDelay>
        <txDelay></txDelay>
        <notificationInterval></notificationInterval>
        <notificationEnable></notificationEnable>
        <fastMessageCount></fastMessageCount>
        <mdnNotificationInterval></mdnNotificationInterval>
        <mdnNotificationEnable></mdnNotificationEnable>
        <configManAddr></configManAddr>
        <bindifName></bindifName>
      </lldpSysParameter>
    </lldpSys>
  </lldp>
</filter>
"""

CE_NC_MERGE_GLOBAL_LLDP_CONFIG_HEADER = """
<config>
    <lldp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <lldpSys>
            <lldpSysParameter operation="merge">
"""

CE_NC_MERGE_GLOBAL_LLDP_CONFIG_INTERVAL = """
                <messageTxInterval>%s</messageTxInterval>
"""

CE_NC_MERGE_GLOBAL_LLDP_CONFIG_HOLD_MULTIPLIER = """
                <messageTxHoldMultiplier>%s</messageTxHoldMultiplier>
"""

CE_NC_MERGE_GLOBAL_LLDP_CONFIG_RESTART_DELAY = """
                <reinitDelay>%s</reinitDelay>
"""

CE_NC_MERGE_GLOBAL_LLDP_CONFIG_TRANSMIT_DELAY = """
                <txDelay>%s</txDelay>
"""

CE_NC_MERGE_GLOBAL_LLDP_CONFIG_NOTIFICATION_INTERVAL = """
                <notificationInterval>%s</notificationInterval>
"""

CE_NC_MERGE_GLOBAL_LLDP_CONFIG_FAST_COUNT = """
                <fastMessageCount>%s</fastMessageCount>
"""

CE_NC_MERGE_GLOBAL_LLDP_CONFIG_MDN_NOTIFICATION_INTERVAL = """
                <mdnNotificationInterval>%s</mdnNotificationInterval>
"""

CE_NC_MERGE_GLOBAL_LLDP_CONFIG_MANAGEMENT_ADDRESS = """
                <configManAddr>%s</configManAddr>
"""

CE_NC_MERGE_GLOBAL_LLDP_CONFIG_BIND_NAME = """
                <bindifName>%s</bindifName>
"""

CE_NC_MERGE_GLOBAL_LLDP_CONFIG_TAIL = """
            </lldpSysParameter>
        </lldpSys>
    </lldp>
</config>
"""


class Lldp(object):
    """Manage global lldp enable configuration"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()
        self.lldpenable = self.module.params['lldpenable'] or None
        self.interval = self.module.params['interval'] or None
        self.mdnstatus = self.module.params['mdnstatus'] or None
        self.hold_multiplier = self.module.params['hold_multiplier'] or None
        self.restart_delay = self.module.params['restart_delay'] or None
        self.transmit_delay = self.module.params['transmit_delay'] or None
        self.notification_interval = self.module.params['notification_interval'] or None
        self.fast_count = self.module.params['fast_count'] or None
        self.mdn_notification_interval = self.module.params['mdn_notification_interval'] or None
        self.management_address = self.module.params['management_address']
        self.bind_name = self.module.params['bind_name']
        self.state = self.module.params['state']
        self.lldp_conf = dict()
        self.conf_exsit = False
        self.conf_exsit_lldp = False
        self.enable_flag = 0
        self.check_params()
        self.existing_state_value = dict()
        self.existing_end_state_value = dict()
        self.changed = False
        self.proposed_changed = dict()
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def is_valid_v4addr(self):
        """check if ipv4 addr is valid"""
        if self.management_address.find('.') != -1:
            addr_list = self.management_address.split('.')
            if self.management_address == "0.0.0.0":
                self.module.fail_json(msg='Error: The management address is 0.0.0.0 .')
            if len(addr_list) != 4:
                self.module.fail_json(msg='Error: Invalid IPV4 address.')
            for each_num in addr_list:
                each_num_tmp = str(each_num)
                if not each_num_tmp.isdigit():
                    self.module.fail_json(msg='Error: The ip address is not digit.')
                if (int(each_num) > 255) or (int(each_num) < 0):
                    self.module.fail_json(
                        msg='Error: The value of ip address is out of [0 - 255].')
        else:
            self.module.fail_json(msg='Error: Invalid IP address.')

    def check_params(self):
        """Check all input params"""

        if self.interval:
            if int(self.interval) < 5 or int(self.interval) > 32768:
                self.module.fail_json(
                    msg='Error: The value of interval is out of [5 - 32768].')

        if self.hold_multiplier:
            if int(self.hold_multiplier) < 2 or int(self.hold_multiplier) > 10:
                self.module.fail_json(
                    msg='Error: The value of hold_multiplier is out of [2 - 10].')

        if self.restart_delay:
            if int(self.restart_delay) < 1 or int(self.restart_delay) > 10:
                self.module.fail_json(
                    msg='Error: The value of restart_delay is out of [1 - 10].')

        if self.transmit_delay:
            if int(self.transmit_delay) < 1 or int(self.transmit_delay) > 8192:
                self.module.fail_json(
                    msg='Error: The value of transmit_delay is out of [1 - 8192].')

        if self.notification_interval:
            if int(self.notification_interval) < 5 or int(self.notification_interval) > 3600:
                self.module.fail_json(
                    msg='Error: The value of notification_interval is out of [5 - 3600].')

        if self.fast_count:
            if int(self.fast_count) < 1 or int(self.fast_count) > 8:
                self.module.fail_json(
                    msg='Error: The value of fast_count is out of [1 - 8].')

        if self.mdn_notification_interval:
            if int(self.mdn_notification_interval) < 5 or int(self.mdn_notification_interval) > 3600:
                self.module.fail_json(
                    msg='Error: The value of mdn_notification_interval is out of [5 - 3600].')

        if self.management_address:
            self.is_valid_v4addr()

        if self.bind_name:
            if (len(self.bind_name) < 1) or (len(self.bind_name) > 63):
                self.module.fail_json(
                    msg='Error: Bind_name length is between 1 and 63.')

    def init_module(self):
        """Init module object"""

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed"""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def config_lldp(self):
        """Configure lldp enabled and mdn enabled parameters"""

        if self.state == 'present':
            if (self.enable_flag == 1 and self.lldpenable == 'enabled') and not self.conf_exsit:
                if self.mdnstatus:
                    xml_str = CE_NC_MERGE_GLOBA_MDNENABLE_CONFIG % self.mdnstatus
                    ret_xml = set_nc_config(self.module, xml_str)
                    self.check_response(ret_xml, "MDN_ENABLE_CONFIG")

            if self.lldpenable == 'enabled' and not self.conf_exsit:
                xml_str = CE_NC_MERGE_GLOBA_LLDPENABLE_CONFIG % self.lldpenable
                ret_xml = set_nc_config(self.module, xml_str)
                self.check_response(ret_xml, "LLDP_ENABLE_CONFIG")

                if self.mdnstatus:
                    xml_str = CE_NC_MERGE_GLOBA_MDNENABLE_CONFIG % self.mdnstatus
                    ret_xml = set_nc_config(self.module, xml_str)
                    self.check_response(ret_xml, "MDN_ENABLE_CONFIG")

            if (self.enable_flag == 1) and not self.conf_exsit:
                if self.mdnstatus:
                    xml_str = CE_NC_MERGE_GLOBA_MDNENABLE_CONFIG % self.mdnstatus
                    ret_xml = set_nc_config(self.module, xml_str)
                    self.check_response(ret_xml, "MDN_ENABLE_CONFIG")

            if (self.lldpenable == 'enabled' or self.enable_flag == 1) and not self.conf_exsit_lldp:
                if self.hold_multiplier:
                    xml_str = CE_NC_MERGE_GLOBAL_LLDP_CONFIG_HEADER + \
                        (CE_NC_MERGE_GLOBAL_LLDP_CONFIG_HOLD_MULTIPLIER % self.hold_multiplier) + \
                        CE_NC_MERGE_GLOBAL_LLDP_CONFIG_TAIL
                    ret_xml = set_nc_config(self.module, xml_str)
                    self.check_response(ret_xml, "LLDP_CONFIG_INTERVAL")

                if self.interval:
                    xml_str = CE_NC_MERGE_GLOBAL_LLDP_CONFIG_HEADER + \
                        (CE_NC_MERGE_GLOBAL_LLDP_CONFIG_INTERVAL % self.interval) + \
                        CE_NC_MERGE_GLOBAL_LLDP_CONFIG_TAIL
                    ret_xml = set_nc_config(self.module, xml_str)
                    self.check_response(ret_xml, "LLDP_CONFIG_INTERVAL")

                if self.restart_delay:
                    xml_str = CE_NC_MERGE_GLOBAL_LLDP_CONFIG_HEADER + \
                        (CE_NC_MERGE_GLOBAL_LLDP_CONFIG_RESTART_DELAY % self.restart_delay) + \
                        CE_NC_MERGE_GLOBAL_LLDP_CONFIG_TAIL
                    ret_xml = set_nc_config(self.module, xml_str)
                    self.check_response(ret_xml, "LLDP_CONFIG_INTERVAL")

                if self.transmit_delay:
                    xml_str = CE_NC_MERGE_GLOBAL_LLDP_CONFIG_HEADER + \
                        (CE_NC_MERGE_GLOBAL_LLDP_CONFIG_TRANSMIT_DELAY % self.transmit_delay) + \
                        CE_NC_MERGE_GLOBAL_LLDP_CONFIG_TAIL
                    ret_xml = set_nc_config(self.module, xml_str)
                    self.check_response(ret_xml, "LLDP_CONFIG_INTERVAL")

                if self.notification_interval:
                    xml_str = CE_NC_MERGE_GLOBAL_LLDP_CONFIG_HEADER + \
                        (CE_NC_MERGE_GLOBAL_LLDP_CONFIG_NOTIFICATION_INTERVAL % self.notification_interval) + \
                        CE_NC_MERGE_GLOBAL_LLDP_CONFIG_TAIL
                    ret_xml = set_nc_config(self.module, xml_str)
                    self.check_response(ret_xml, "LLDP_CONFIG_INTERVAL")

                if self.fast_count:
                    xml_str = CE_NC_MERGE_GLOBAL_LLDP_CONFIG_HEADER + \
                        (CE_NC_MERGE_GLOBAL_LLDP_CONFIG_FAST_COUNT % self.fast_count) + \
                        CE_NC_MERGE_GLOBAL_LLDP_CONFIG_TAIL
                    ret_xml = set_nc_config(self.module, xml_str)
                    self.check_response(ret_xml, "LLDP_CONFIG_INTERVAL")

                if self.mdn_notification_interval:
                    xml_str = CE_NC_MERGE_GLOBAL_LLDP_CONFIG_HEADER + \
                        (CE_NC_MERGE_GLOBAL_LLDP_CONFIG_MDN_NOTIFICATION_INTERVAL % self.mdn_notification_interval) + \
                        CE_NC_MERGE_GLOBAL_LLDP_CONFIG_TAIL
                    ret_xml = set_nc_config(self.module, xml_str)
                    self.check_response(ret_xml, "LLDP_CONFIG_INTERVAL")

                if self.management_address:
                    xml_str = CE_NC_MERGE_GLOBAL_LLDP_CONFIG_HEADER + \
                        (CE_NC_MERGE_GLOBAL_LLDP_CONFIG_MANAGEMENT_ADDRESS % self.management_address) + \
                        CE_NC_MERGE_GLOBAL_LLDP_CONFIG_TAIL
                    ret_xml = set_nc_config(self.module, xml_str)
                    self.check_response(ret_xml, "LLDP_CONFIG_INTERVAL")

                if self.bind_name:
                    xml_str = CE_NC_MERGE_GLOBAL_LLDP_CONFIG_HEADER + \
                        (CE_NC_MERGE_GLOBAL_LLDP_CONFIG_BIND_NAME % self.bind_name) + \
                        CE_NC_MERGE_GLOBAL_LLDP_CONFIG_TAIL
                    ret_xml = set_nc_config(self.module, xml_str)
                    self.check_response(ret_xml, "LLDP_CONFIG_INTERVAL")

                if self.lldpenable == 'disabled' and not self.conf_exsit:
                    xml_str = CE_NC_MERGE_GLOBA_LLDPENABLE_CONFIG % self.lldpenable
                    ret_xml = set_nc_config(self.module, xml_str)
                    self.check_response(ret_xml, "LLDP_DISABLE_CONFIG")

    def show_result(self):
        """Show result"""

        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        if self.changed:
            self.results['updates'] = self.updates_cmd
        else:
            self.results['updates'] = list()

        self.module.exit_json(**self.results)

    def get_lldp_exist_config(self):
        """Get lldp existed configure"""

        lldp_config = list()
        lldp_dict = dict()

        conf_enable_str = CE_NC_GET_GLOBAL_LLDPENABLE_CONFIG
        conf_enable_obj = get_nc_config(self.module, conf_enable_str)

        xml_enable_str = conf_enable_obj.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

        # get lldp enable config info
        root_enable = ElementTree.fromstring(xml_enable_str)
        ntpsite_enable = root_enable.findall("lldp/lldpSys")
        for nexthop_enable in ntpsite_enable:
            for ele_enable in nexthop_enable:
                if ele_enable.tag in ["lldpEnable", "mdnStatus"]:
                    lldp_dict[ele_enable.tag] = ele_enable.text

            if self.state == "present":
                cur_lldp_cfg = dict(lldpenable=lldp_dict['lldpEnable'], mdnstatus=lldp_dict['mdnStatus'])
                exp_lldp_cfg = dict(lldpenable=self.lldpenable, mdnstatus=self.mdnstatus)
                if lldp_dict['lldpEnable'] == 'enabled':
                    self.enable_flag = 1
                if cur_lldp_cfg == exp_lldp_cfg:
                    self.conf_exsit = True
            lldp_config.append(dict(lldpenable=lldp_dict['lldpEnable'], mdnstatus=lldp_dict['mdnStatus']))

        conf_str = CE_NC_GET_GLOBAL_LLDP_CONFIG
        conf_obj = get_nc_config(self.module, conf_str)
        if "<data/>" in conf_obj:
            pass

        else:
            xml_str = conf_obj.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

        # get all ntp config info
            root = ElementTree.fromstring(xml_str)
            ntpsite = root.findall("lldp/lldpSys/lldpSysParameter")
            for nexthop in ntpsite:
                for ele in nexthop:
                    if ele.tag in ["messageTxInterval", "messageTxHoldMultiplier", "reinitDelay", "txDelay",
                                   "notificationInterval", "fastMessageCount", "mdnNotificationInterval",
                                   "configManAddr", "bindifName"]:
                        lldp_dict[ele.tag] = ele.text

                if self.state == "present":
                    cur_ntp_cfg = dict(interval=lldp_dict['messageTxInterval'],
                                       hold_multiplier=lldp_dict['messageTxHoldMultiplier'],
                                       restart_delay=lldp_dict['reinitDelay'],
                                       transmit_delay=lldp_dict['txDelay'],
                                       notification_interval=lldp_dict['notificationInterval'],
                                       fast_count=lldp_dict['fastMessageCount'],
                                       mdn_notification_interval=lldp_dict['mdnNotificationInterval'],
                                       management_address=lldp_dict['configManAddr'],
                                       bind_name=lldp_dict['bindifName'])

                    exp_ntp_cfg = dict(interval=self.interval, hold_multiplier=self.hold_multiplier,
                                       restart_delay=self.restart_delay, transmit_delay=self.transmit_delay,
                                       notification_interval=self.notification_interval,
                                       fast_count=self.fast_count, mdn_notification_interval=self.mdn_notification_interval,
                                       management_address=self.management_address, bind_name=self.bind_name)

                    if cur_ntp_cfg == exp_ntp_cfg:
                        self.conf_exsit_lldp = True

                lldp_config.append(dict(interval=lldp_dict['messageTxInterval'],
                                        hold_multiplier=lldp_dict['messageTxHoldMultiplier'],
                                        restart_delay=lldp_dict['reinitDelay'], transmit_delay=lldp_dict['txDelay'],
                                        notification_interval=lldp_dict['notificationInterval'],
                                        fast_count=lldp_dict['fastMessageCount'],
                                        mdn_notification_interval=lldp_dict['mdnNotificationInterval'],
                                        management_address=lldp_dict['configManAddr'],
                                        bind_name=lldp_dict['bindifName']))

        tmp_dict = dict()
        str_1 = str(lldp_config)
        temp_1 = str_1.replace('[', '').replace(']', '').replace('{', '').replace('}', '').replace('\'', '')
        if temp_1:
            tmp_2 = temp_1.split(',')
            for i in tmp_2:
                tmp_value = re.match(r'(.*):(.*)', i)
                key_tmp = tmp_value.group(1)
                key_value = tmp_value.group(2)
                tmp_dict[key_tmp] = key_value
        return tmp_dict

    def get_existing(self):
        """Get existing info"""

        self.existing = self.get_lldp_exist_config()

    def get_proposed(self):
        """Get proposed info"""

        if self.enable_flag == 1:
            if self.lldpenable == 'enabled':
                self.proposed = dict(lldpenable=self.lldpenable)
                if self.mdnstatus:
                    self.proposed = dict(mdnstatus=self.mdnstatus)
            elif self.lldpenable == 'disabled':
                self.proposed = dict(lldpenable=self.lldpenable)
                self.changed = True
            else:
                if self.mdnstatus:
                    self.proposed = dict(mdnstatus=self.mdnstatus)
        else:
            if self.lldpenable == 'enabled':
                self.proposed = dict(lldpenable=self.lldpenable)
                self.changed = True
                if self.mdnstatus:
                    self.proposed = dict(mdnstatus=self.mdnstatus)
        if self.enable_flag == 1 or self.lldpenable == 'enabled':
            if self.interval:
                self.proposed = dict(interval=self.interval)
            if self.hold_multiplier:
                self.proposed = dict(hold_multiplier=self.hold_multiplier)
            if self.restart_delay:
                self.proposed = dict(restart_delay=self.restart_delay)
            if self.transmit_delay:
                self.proposed = dict(transmit_delay=self.transmit_delay)
            if self.notification_interval:
                self.proposed = dict(notification_interval=self.notification_interval)
            if self.fast_count:
                self.proposed = dict(fast_count=self.fast_count)
            if self.mdn_notification_interval:
                self.proposed = dict(mdn_notification_interval=self.mdn_notification_interval)
            if self.management_address:
                self.proposed = dict(management_address=self.management_address)
            if self.bind_name:
                self.proposed = dict(bind_name=self.bind_name)

    def get_end_state(self):
        """Get end state info"""

        self.end_state = self.get_lldp_exist_config()
        existing_key_list = self.existing.keys()
        end_state_key_list = self.end_state.keys()
        for i in end_state_key_list:
            for j in existing_key_list:
                if i == j and self.existing[i] != self.end_state[j]:
                    self.changed = True

    def get_update_cmd(self):
        """Get updated commands"""

        if self.conf_exsit and self.conf_exsit_lldp:
            return

        if self.state == "present":
            if self.lldpenable == "enabled":
                self.updates_cmd.append("lldp enable")

                if self.mdnstatus:
                    self.updates_cmd.append("lldp mdn enable")
                    if self.mdnstatus == "rxOnly":
                        self.updates_cmd.append("lldp mdn enable")
                    else:
                        self.updates_cmd.append("undo lldp mdn enable")
                if self.interval:
                    self.updates_cmd.append("lldp transmit interval %s" % self.interval)
                if self.hold_multiplier:
                    self.updates_cmd.append("lldp transmit multiplier %s" % self.hold_multiplier)
                if self.restart_delay:
                    self.updates_cmd.append("lldp restart %s" % self.restart_delay)
                if self.transmit_delay:
                    self.updates_cmd.append("lldp transmit delay %s" % self.transmit_delay)
                if self.notification_interval:
                    self.updates_cmd.append("lldp trap-interval %s" % self.notification_interval)
                if self.fast_count:
                    self.updates_cmd.append("lldp fast-count %s" % self.fast_count)
                if self.mdn_notification_interval:
                    self.updates_cmd.append("lldp mdn trap-interval %s" % self.mdn_notification_interval)
                if self.management_address:
                    self.updates_cmd.append("lldp management-address %s" % self.management_address)
                if self.bind_name:
                    self.updates_cmd.append("lldp management-address bind interface %s" % self.bind_name)
            elif self.lldpenable == "disabled":
                self.updates_cmd.append("undo lldp enable")
            else:
                if self.enable_flag == 1:
                    if self.mdnstatus:
                        if self.mdnstatus == "rxOnly":
                            self.updates_cmd.append("lldp mdn enable")
                        else:
                            self.updates_cmd.append("undo lldp mdn enable")
                    if self.interval:
                        self.updates_cmd.append("lldp transmit interval %s" % self.interval)
                    if self.hold_multiplier:
                        self.updates_cmd.append("lldp transmit multiplier %s" % self.hold_multiplier)
                    if self.restart_delay:
                        self.updates_cmd.append("lldp restart %s" % self.restart_delay)
                    if self.transmit_delay:
                        self.updates_cmd.append("lldp transmit delay %s" % self.transmit_delay)
                    if self.notification_interval:
                        self.updates_cmd.append("lldp trap-interval %s" % self.notification_interval)
                    if self.fast_count:
                        self.updates_cmd.append("lldp fast-count %s" % self.fast_count)
                    if self.mdn_notification_interval:
                        self.updates_cmd.append("lldp mdn trap-interval %s" % self.mdn_notification_interval)
                    if self.management_address:
                        self.updates_cmd.append("lldp management-address %s" % self.management_address)
                    if self.bind_name:
                        self.updates_cmd.append("lldp management-address bind interface %s" % self.bind_name)

    def work(self):
        """Execute task"""
        self.check_params()
        self.get_existing()
        self.get_proposed()
        self.config_lldp()
        self.get_update_cmd()
        self.get_end_state()
        self.show_result()


def main():
    """Main function entry"""

    argument_spec = dict(
        lldpenable=dict(required=False, choices=['enabled', 'disabled']),
        mdnstatus=dict(required=False, choices=['rxOnly', 'disabled']),
        interval=dict(required=False, type='int'),
        hold_multiplier=dict(required=False, type='int'),
        restart_delay=dict(required=False, type='int'),
        transmit_delay=dict(required=False, type='int'),
        notification_interval=dict(required=False, type='int'),
        fast_count=dict(required=False, type='int'),
        mdn_notification_interval=dict(required=False, type='int'),
        management_address=dict(required=False, type='str'),
        bind_name=dict(required=False, type='str'),
        state=dict(choices=['absent', 'present'], default='present'),
    )
    lldp_obj = Lldp(argument_spec)
    lldp_obj.work()


if __name__ == '__main__':
    main()
