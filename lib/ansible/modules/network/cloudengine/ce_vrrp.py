#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: ce_vrrp
version_added: "2.4"
short_description: Manages VRRP interfaces on HUAWEI CloudEngine devices.
description:
    - Manages VRRP interface attributes on HUAWEI CloudEngine devices.
author:
    - Li Yanfeng (@CloudEngine-Ansible)
options:
    interface:
        description:
            - Name of an interface. The value is a string of 1 to 63 characters.
        required: false
        default: null
    vrid:
        description:
            - VRRP backup group ID.
              The value is an integer ranging from 1 to 255.
        required: false
        default: present
    virtual_ip :
        description:
            - Virtual IP address. The value is a string of 0 to 255 characters.
        required: false
        default: null
    vrrp_type:
        description:
            - Type of a VRRP backup group.
        required: false
        choices: ['normal', 'member', 'admin']
        default: null
    admin_ignore_if_down:
        description:
            - mVRRP ignores an interface Down event.
        required: false
        default: False
    admin_vrid:
        description:
            - Tracked mVRRP ID. The value is an integer ranging from 1 to 255.
        required: false
        default: null
    admin_interface:
        description:
            - Tracked mVRRP interface name. The value is a string of 1 to 63 characters.
        required: false
        default: null
    admin_flowdown:
        description:
            - Disable the flowdown function for service VRRP.
        required: false
        default: False
    priority:
        description:
            - Configured VRRP priority.
              The value ranges from 1 to 254. The default value is 100. A larger value indicates a higher priority.
        required: false
        default: null
    version:
        description:
            - VRRP version. The default version is v2.
        required: false
        choices: ['v2','v3']
        default: null
    advertise_interval:
        description:
            - Configured interval between sending advertisements, in milliseconds.
              Only the master router sends VRRP advertisements. The default value is 1000 milliseconds.
        required: false
        default: null
    preempt_timer_delay:
        description:
            - Preemption delay.
              The value is an integer ranging from 0 to 3600. The default value is 0.
        required: false
        default: null
    gratuitous_arp_interval:
        description:
            - Interval at which gratuitous ARP packets are sent, in seconds.
              The value ranges from 30 to 1200.The default value is 300.
        required: false
        default: null
    recover_delay:
        description:
            - Delay in recovering after an interface goes Up.
              The delay is used for interface flapping suppression.
              The value is an integer ranging from 0 to 3600.
              The default value is 0 seconds.
        required: false
        default: null
    holding_multiplier:
        description:
            - The configured holdMultiplier.The value is an integer ranging from 3 to 10. The default value is 3.
        required: false
        default: null
    auth_mode:
        description:
            - Authentication type used for VRRP packet exchanges between virtual routers.
              The values are noAuthentication, simpleTextPassword, md5Authentication.
              The default value is noAuthentication.
        required: false
        choices: ['simple','md5','none']
        default: null
    is_plain:
        description:
            - Select the display mode of an authentication key.
              By default, an authentication key is displayed in ciphertext.
        required: false
        default: False
    auth_key:
        description:
            - This object is set based on the authentication type.
              When noAuthentication is specified, the value is empty.
              When simpleTextPassword or md5Authentication is specified, the value is a string of 1 to 8 characters
              in plaintext and displayed as a blank text for security.
        required: false
        default: null
    fast_resume:
        description:
            - mVRRP's fast resume mode.
        required: false
        choices: ['enable','disable']
        default: null
    state:
        description:
            - Specify desired state of the resource.
        required: false
        default: present
        choices: ['present','absent']

'''

EXAMPLES = '''
- name: vrrp module test
  hosts: cloudengine
  connection: local
  gather_facts: no
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ username }}"
      password: "{{ password }}"
      transport: cli

  tasks:

  - name: Set vrrp version
    ce_vrrp:
      version: v3
      provider: "{{ cli }}"

  - name: Set vrrp gratuitous-arp interval
    ce_vrrp:
      gratuitous_arp_interval: 40
      mlag_id: 4
      provider: "{{ cli }}"

  - name: Set vrrp recover-delay
    ce_vrrp:
      recover_delay: 10
      provider: "{{ cli }}"

  - name: Set vrrp vrid virtual-ip
    ce_vrrp:
      interface: 40GE2/0/8
      vrid: 1
      virtual_ip: 10.14.2.7
      provider: "{{ cli }}"

  - name: Set vrrp vrid admin
    ce_vrrp:
      interface: 40GE2/0/8
      vrid: 1
      vrrp_type: admin
      provider: "{{ cli }}"

  - name: Set vrrp vrid fast_resume
    ce_vrrp:
      interface: 40GE2/0/8
      vrid: 1
      fast_resume: enable
      provider: "{{ cli }}"

  - name: Set vrrp vrid holding-multiplier
    ce_vrrp:
      interface: 40GE2/0/8
      vrid: 1
      holding_multiplier: 4
      provider: "{{ cli }}"

  - name: Set vrrp vrid preempt timer delay
    ce_vrrp:
      interface: 40GE2/0/8
      vrid: 1
      preempt_timer_delay: 10
      provider: "{{ cli }}"

  - name: Set vrrp vrid admin-vrrp
    ce_vrrp:
      interface: 40GE2/0/8
      vrid: 1
      admin_interface: 40GE2/0/9
      admin_vrid: 2
      vrrp_type: member
      provider: "{{ cli }}"

  - name: Set vrrp vrid authentication-mode
    ce_vrrp:
      interface: 40GE2/0/8
      vrid: 1
      is_plain: true
      auth_mode: simple
      auth_key: aaa
      provider: "{{ cli }}"
'''

RETURN = '''
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
                "auth_key": "aaa",
                "auth_mode": "simple",
                "interface": "40GE2/0/8",
                "is_plain": true,
                "state": "present",
                "vrid": "1"
            }
existing:
    description: k/v pairs of existing aaa server
    returned: always
    type: dict
    sample: {
                "auth_mode": "none",
                "interface": "40GE2/0/8",
                "is_plain": "false",
                "vrid": "1",
                "vrrp_type": "normal"
            }
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {
                "auth_mode": "simple",
                "interface": "40GE2/0/8",
                "is_plain": "true",
                "vrid": "1",
                "vrrp_type": "normal"
    }
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: { "interface 40GE2/0/8",
              "vrrp vrid 1 authentication-mode simple plain aaa"}
'''

from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ce import get_nc_config, set_nc_config, ce_argument_spec


CE_NC_GET_VRRP_GROUP_INFO = """
<filter type="subtree">
  <vrrp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <vrrpGroups>
      <vrrpGroup>
        <ifName>%s</ifName>
        <vrrpId>%s</vrrpId>
      </vrrpGroup>
    </vrrpGroups>
  </vrrp>
</filter>
"""

CE_NC_SET_VRRP_GROUP_INFO_HEAD = """
<config>
  <vrrp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <vrrpGroups>
      <vrrpGroup operation="merge">
        <ifName>%s</ifName>
        <vrrpId>%s</vrrpId>

"""
CE_NC_SET_VRRP_GROUP_INFO_TAIL = """
      </vrrpGroup>
    </vrrpGroups>
  </vrrp>
</config>

"""
CE_NC_GET_VRRP_GLOBAL_INFO = """
<filter type="subtree">
  <vrrp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <vrrpGlobalCfg>
      <gratuitousArpFlag></gratuitousArpFlag>
      <gratuitousArpTimeOut></gratuitousArpTimeOut>
      <recoverDelay></recoverDelay>
      <version></version>
    </vrrpGlobalCfg>
  </vrrp>
</filter>

"""

CE_NC_SET_VRRP_GLOBAL_HEAD = """
<config>
  <vrrp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <vrrpGlobalCfg operation="merge">
"""
CE_NC_SET_VRRP_GLOBAL_TAIL = """
    </vrrpGlobalCfg>
  </vrrp>
</config>

"""

CE_NC_GET_VRRP_VIRTUAL_IP_INFO = """
<filter type="subtree">
  <vrrp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <vrrpGroups>
      <vrrpGroup>
        <vrrpId>%s</vrrpId>
        <ifName>%s</ifName>
        <virtualIps>
          <virtualIp>
            <virtualIpAddress></virtualIpAddress>
          </virtualIp>
        </virtualIps>
      </vrrpGroup>
    </vrrpGroups>
  </vrrp>
</filter>

"""
CE_NC_CREATE_VRRP_VIRTUAL_IP_INFO = """
<config>
  <vrrp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <vrrpGroups>
      <vrrpGroup>
        <vrrpId>%s</vrrpId>
        <ifName>%s</ifName>
        <virtualIps>
          <virtualIp operation="create">
            <virtualIpAddress>%s</virtualIpAddress>
          </virtualIp>
        </virtualIps>
      </vrrpGroup>
    </vrrpGroups>
  </vrrp>
</config>

"""
CE_NC_DELETE_VRRP_VIRTUAL_IP_INFO = """
<config>
  <vrrp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <vrrpGroups>
      <vrrpGroup>
        <vrrpId>%s</vrrpId>
        <ifName>%s</ifName>
        <virtualIps>
          <virtualIp operation="delete">
            <virtualIpAddress>%s</virtualIpAddress>
          </virtualIp>
        </virtualIps>
      </vrrpGroup>
    </vrrpGroups>
  </vrrp>
</config>

"""


def is_valid_address(address):
    """check ip-address is valid"""

    if address.find('.') != -1:
        addr_list = address.split('.')
        if len(addr_list) != 4:
            return False
        for each_num in addr_list:
            if not each_num.isdigit():
                return False
            if int(each_num) > 255:
                return False
        return True

    return False


def get_interface_type(interface):
    """Gets the type of interface, such as 10GE, ETH-TRUNK, VLANIF..."""

    if interface is None:
        return None

    iftype = None

    if interface.upper().startswith('GE'):
        iftype = 'ge'
    elif interface.upper().startswith('10GE'):
        iftype = '10ge'
    elif interface.upper().startswith('25GE'):
        iftype = '25ge'
    elif interface.upper().startswith('40GE'):
        iftype = '40ge'
    elif interface.upper().startswith('100GE'):
        iftype = '100ge'
    elif interface.upper().startswith('ETH-TRUNK'):
        iftype = 'eth-trunk'
    elif interface.upper().startswith('NULL'):
        iftype = 'null'
    elif interface.upper().startswith('VLANIF'):
        iftype = 'vlanif'
    else:
        return None

    return iftype.lower()


class Vrrp(object):
    """
    Manages Manages vrrp information.
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.interface = self.module.params['interface']
        self.vrid = self.module.params['vrid']
        self.virtual_ip = self.module.params['virtual_ip']
        self.vrrp_type = self.module.params['vrrp_type']
        self.admin_ignore_if_down = self.module.params['admin_ignore_if_down']
        self.admin_vrid = self.module.params['admin_vrid']
        self.admin_interface = self.module.params['admin_interface']
        self.admin_flowdown = self.module.params['admin_flowdown']
        self.priority = self.module.params['priority']
        self.version = self.module.params['version']
        self.advertise_interval = self.module.params['advertise_interval']
        self.preempt_timer_delay = self.module.params['preempt_timer_delay']
        self.gratuitous_arp_interval = self.module.params[
            'gratuitous_arp_interval']
        self.recover_delay = self.module.params['recover_delay']
        self.holding_multiplier = self.module.params['holding_multiplier']
        self.auth_mode = self.module.params['auth_mode']
        self.is_plain = self.module.params['is_plain']
        self.auth_key = self.module.params['auth_key']
        self.fast_resume = self.module.params['fast_resume']
        self.state = self.module.params['state']

        # vrrp info
        self.vrrp_global_info = None
        self.virtual_ip_info = None
        self.vrrp_group_info = None

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.existing = dict()
        self.proposed = dict()
        self.end_state = dict()

    def init_module(self):
        """ init module """

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def get_virtual_ip_info(self):
        """ get vrrp virtual ip info."""
        virtual_ip_info = dict()
        conf_str = CE_NC_GET_VRRP_VIRTUAL_IP_INFO % (self.vrid, self.interface)
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return virtual_ip_info
        else:
            xml_str = xml_str.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
            virtual_ip_info["vrrpVirtualIpInfos"] = list()
            root = ElementTree.fromstring(xml_str)
            vrrp_virtual_ip_infos = root.findall(
                "data/vrrp/vrrpGroups/vrrpGroup/virtualIps/virtualIp")
            if vrrp_virtual_ip_infos:
                for vrrp_virtual_ip_info in vrrp_virtual_ip_infos:
                    virtual_ip_dict = dict()
                    for ele in vrrp_virtual_ip_info:
                        if ele.tag in ["virtualIpAddress"]:
                            virtual_ip_dict[ele.tag] = ele.text
                    virtual_ip_info["vrrpVirtualIpInfos"].append(
                        virtual_ip_dict)
            return virtual_ip_info

    def get_vrrp_global_info(self):
        """ get vrrp global info."""

        vrrp_global_info = dict()
        conf_str = CE_NC_GET_VRRP_GLOBAL_INFO
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return vrrp_global_info
        else:
            xml_str = xml_str.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

            root = ElementTree.fromstring(xml_str)
            global_info = root.findall(
                "data/vrrp/vrrpGlobalCfg")

            if global_info:
                for tmp in global_info:
                    for site in tmp:
                        if site.tag in ["gratuitousArpTimeOut", "gratuitousArpFlag", "recoverDelay", "version"]:
                            vrrp_global_info[site.tag] = site.text
            return vrrp_global_info

    def get_vrrp_group_info(self):
        """ get vrrp group info."""

        vrrp_group_info = dict()
        conf_str = CE_NC_GET_VRRP_GROUP_INFO % (self.interface, self.vrid)
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return vrrp_group_info
        else:
            xml_str = xml_str.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

            root = ElementTree.fromstring(xml_str)
            global_info = root.findall(
                "data/vrrp/vrrpGroups/vrrpGroup")

            if global_info:
                for tmp in global_info:
                    for site in tmp:
                        if site.tag in ["ifName", "vrrpId", "priority", "advertiseInterval", "preemptMode", "delayTime",
                                        "authenticationMode", "authenticationKey", "vrrpType", "adminVrrpId",
                                        "adminIfName", "adminIgnoreIfDown", "isPlain", "unflowdown", "fastResume",
                                        "holdMultiplier"]:
                            vrrp_group_info[site.tag] = site.text
            return vrrp_group_info

    def check_params(self):
        """Check all input params"""

        # interface check
        if self.interface:
            intf_type = get_interface_type(self.interface)
            if not intf_type:
                self.module.fail_json(
                    msg='Error: Interface name of %s '
                        'is error.' % self.interface)

        # vrid check
        if self.vrid:
            if not self.vrid.isdigit():
                self.module.fail_json(
                    msg='Error: The value of vrid is an integer.')
            if int(self.vrid) < 1 or int(self.vrid) > 255:
                self.module.fail_json(
                    msg='Error: The value of vrid ranges from 1 to 255.')

        # virtual_ip check
        if self.virtual_ip:
            if not is_valid_address(self.virtual_ip):
                self.module.fail_json(
                    msg='Error: The %s is not a valid ip address.' % self.virtual_ip)

        # admin_vrid check
        if self.admin_vrid:
            if not self.admin_vrid.isdigit():
                self.module.fail_json(
                    msg='Error: The value of admin_vrid is an integer.')
            if int(self.admin_vrid) < 1 or int(self.admin_vrid) > 255:
                self.module.fail_json(
                    msg='Error: The value of admin_vrid ranges from 1 to 255.')

        # admin_interface check
        if self.admin_interface:
            intf_type = get_interface_type(self.admin_interface)
            if not intf_type:
                self.module.fail_json(
                    msg='Error: Admin interface name of %s '
                        'is error.' % self.admin_interface)

        # priority check
        if self.priority:
            if not self.priority.isdigit():
                self.module.fail_json(
                    msg='Error: The value of priority is an integer.')
            if int(self.priority) < 1 or int(self.priority) > 254:
                self.module.fail_json(
                    msg='Error: The value of priority ranges from 1 to 254. The default value is 100.')

        # advertise_interval check
        if self.advertise_interval:
            if not self.advertise_interval.isdigit():
                self.module.fail_json(
                    msg='Error: The value of advertise_interval is an integer.')
            if int(self.advertise_interval) < 1 or int(self.advertise_interval) > 255000:
                self.module.fail_json(
                    msg='Error: The value of advertise_interval ranges from 1 to 255000. The default value is 1000.')

        # preempt_timer_delay check
        if self.preempt_timer_delay:
            if not self.preempt_timer_delay.isdigit():
                self.module.fail_json(
                    msg='Error: The value of preempt_timer_delay is an integer.')
            if int(self.preempt_timer_delay) < 1 or int(self.preempt_timer_delay) > 3600:
                self.module.fail_json(
                    msg='Error: The value of preempt_timer_delay ranges from 1 to 3600. The default value is 0.')

        # holding_multiplier check
        if self.holding_multiplier:
            if not self.holding_multiplier.isdigit():
                self.module.fail_json(
                    msg='Error: The value of holding_multiplier is an integer.')
            if int(self.holding_multiplier) < 3 or int(self.holding_multiplier) > 10:
                self.module.fail_json(
                    msg='Error: The value of holding_multiplier ranges from 3 to 10. The default value is 3.')

        # auth_key check
        if self.auth_key:
            if len(self.auth_key) > 16 \
                    or len(self.auth_key.replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: The length of auth_key is not in the range from 1 to 16.')

    def is_virtual_ip_change(self):
        """whether virtual ip change"""

        if not self.virtual_ip_info:
            return True

        for info in self.virtual_ip_info["vrrpVirtualIpInfos"]:
            if info["virtualIpAddress"] == self.virtual_ip:
                return False
        return True

    def is_virtual_ip_exist(self):
        """whether virtual ip info exist"""

        if not self.virtual_ip_info:
            return False

        for info in self.virtual_ip_info["vrrpVirtualIpInfos"]:
            if info["virtualIpAddress"] == self.virtual_ip:
                return True
        return False

    def is_vrrp_global_info_change(self):
        """whether vrrp global attribute info change"""

        if not self.vrrp_global_info:
            return True

        if self.gratuitous_arp_interval:
            if self.vrrp_global_info["gratuitousArpFlag"] == "false":
                self.module.fail_json(msg="Error: gratuitousArpFlag is false.")
            if self.vrrp_global_info["gratuitousArpTimeOut"] != self.gratuitous_arp_interval:
                return True
        if self.recover_delay:
            if self.vrrp_global_info["recoverDelay"] != self.recover_delay:
                return True
        if self.version:
            if self.vrrp_global_info["version"] != self.version:
                return True
        return False

    def is_vrrp_global_info_exist(self):
        """whether vrrp global attribute info exist"""

        if self.gratuitous_arp_interval or self.recover_delay or self.version:
            if self.gratuitous_arp_interval:
                if self.vrrp_global_info["gratuitousArpFlag"] == "false":
                    self.module.fail_json(
                        msg="Error: gratuitousArpFlag is false.")
                if self.vrrp_global_info["gratuitousArpTimeOut"] != self.gratuitous_arp_interval:
                    return False
            if self.recover_delay:
                if self.vrrp_global_info["recoverDelay"] != self.recover_delay:
                    return False
            if self.version:
                if self.vrrp_global_info["version"] != self.version:
                    return False
            return True

        return False

    def is_vrrp_group_info_change(self):
        """whether vrrp group attribute info change"""

        if self.vrrp_type:
            if self.vrrp_group_info["vrrpType"] != self.vrrp_type:
                return True
        if self.admin_ignore_if_down:
            if self.vrrp_group_info["adminIgnoreIfDown"] != self.admin_ignore_if_down:
                return True
        if self.admin_vrid:
            if self.vrrp_group_info["adminVrrpId"] != self.admin_vrid:
                return True
        if self.admin_interface:
            if self.vrrp_group_info["adminIfName"] != self.admin_interface:
                return True
        if self.admin_flowdown:
            if self.vrrp_group_info["unflowdown"] != self.admin_flowdown:
                return True
        if self.priority:
            if self.vrrp_group_info["priority"] != self.priority:
                return True
        if self.fast_resume:
            fast_resume = "false"
            if self.fast_resume == "enable":
                fast_resume = "true"
            if self.vrrp_group_info["fastResume"] != fast_resume:
                return True
        if self.advertise_interval:
            if self.vrrp_group_info["advertiseInterval"] != self.advertise_interval:
                return True
        if self.preempt_timer_delay:
            if self.vrrp_group_info["delayTime"] != self.preempt_timer_delay:
                return True
        if self.holding_multiplier:
            if self.vrrp_group_info["holdMultiplier"] != self.holding_multiplier:
                return True
        if self.auth_mode:
            if self.vrrp_group_info["authenticationMode"] != self.auth_mode:
                return True
        if self.auth_key:
            return True
        if self.is_plain:
            if self.vrrp_group_info["isPlain"] != self.is_plain:
                return True

        return False

    def is_vrrp_group_info_exist(self):
        """whether vrrp group attribute info exist"""

        if self.vrrp_type:
            if self.vrrp_group_info["vrrpType"] != self.vrrp_type:
                return False
        if self.admin_ignore_if_down:
            if self.vrrp_group_info["adminIgnoreIfDown"] != self.admin_ignore_if_down:
                return False
        if self.admin_vrid:
            if self.vrrp_group_info["adminVrrpId"] != self.admin_vrid:
                return False
        if self.admin_interface:
            if self.vrrp_group_info["adminIfName"] != self.admin_interface:
                return False
        if self.admin_flowdown:
            if self.vrrp_group_info["unflowdown"] != self.admin_flowdown:
                return False
        if self.priority:
            if self.vrrp_group_info["priority"] != self.priority:
                return False
        if self.fast_resume:
            fast_resume = "false"
            if self.fast_resume == "enable":
                fast_resume = "true"
            if self.vrrp_group_info["fastResume"] != fast_resume:
                return False
        if self.advertise_interval:
            if self.vrrp_group_info["advertiseInterval"] != self.advertise_interval:
                return False
        if self.preempt_timer_delay:
            if self.vrrp_group_info["delayTime"] != self.preempt_timer_delay:
                return False
        if self.holding_multiplier:
            if self.vrrp_group_info["holdMultiplier"] != self.holding_multiplier:
                return False
        if self.auth_mode:
            if self.vrrp_group_info["authenticationMode"] != self.auth_mode:
                return False
        if self.is_plain:
            if self.vrrp_group_info["isPlain"] != self.is_plain:
                return False
        return True

    def create_virtual_ip(self):
        """create virtual ip info"""

        if self.is_virtual_ip_change():
            conf_str = CE_NC_CREATE_VRRP_VIRTUAL_IP_INFO % (
                self.vrid, self.interface, self.virtual_ip)
            recv_xml = set_nc_config(self.module, conf_str)
            if "<ok/>" not in recv_xml:
                self.module.fail_json(
                    msg='Error: create virtual ip info failed.')

            self.updates_cmd.append("interface %s" % self.interface)
            self.updates_cmd.append(
                "vrrp vrid %s virtual-ip %s" % (self.vrid, self.virtual_ip))
            self.changed = True

    def delete_virtual_ip(self):
        """delete virtual ip info"""

        if self.is_virtual_ip_exist():
            conf_str = CE_NC_DELETE_VRRP_VIRTUAL_IP_INFO % (
                self.vrid, self.interface, self.virtual_ip)
            recv_xml = set_nc_config(self.module, conf_str)
            if "<ok/>" not in recv_xml:
                self.module.fail_json(
                    msg='Error: delete virtual ip info failed.')

            self.updates_cmd.append("interface %s" % self.interface)
            self.updates_cmd.append(
                "undo vrrp vrid %s virtual-ip %s " % (self.vrid, self.virtual_ip))
            self.changed = True

    def set_vrrp_global(self):
        """set vrrp global attribute info"""

        if self.is_vrrp_global_info_change():
            conf_str = CE_NC_SET_VRRP_GLOBAL_HEAD
            if self.gratuitous_arp_interval:
                conf_str += "<gratuitousArpTimeOut>%s</gratuitousArpTimeOut>" % self.gratuitous_arp_interval
            if self.recover_delay:
                conf_str += "<recoverDelay>%s</recoverDelay>" % self.recover_delay
            if self.version:
                conf_str += "<version>%s</version>" % self.version
            conf_str += CE_NC_SET_VRRP_GLOBAL_TAIL
            recv_xml = set_nc_config(self.module, conf_str)
            if "<ok/>" not in recv_xml:
                self.module.fail_json(
                    msg='Error: set vrrp global atrribute info failed.')

            if self.gratuitous_arp_interval:
                self.updates_cmd.append(
                    "vrrp gratuitous-arp interval %s" % self.gratuitous_arp_interval)

            if self.recover_delay:
                self.updates_cmd.append(
                    "vrrp recover-delay %s" % self.recover_delay)

            if self.version:
                version = "3"
                if self.version == "v2":
                    version = "2"
                self.updates_cmd.append("vrrp version %s" % version)
            self.changed = True

    def delete_vrrp_global(self):
        """delete vrrp global attribute info"""

        if self.is_vrrp_global_info_exist():
            conf_str = CE_NC_SET_VRRP_GLOBAL_HEAD
            if self.gratuitous_arp_interval:
                if self.gratuitous_arp_interval == "120":
                    self.module.fail_json(
                        msg='Error: The default value of gratuitous_arp_interval is 120.')
                gratuitous_arp_interval = "120"
                conf_str += "<gratuitousArpTimeOut>%s</gratuitousArpTimeOut>" % gratuitous_arp_interval
            if self.recover_delay:
                if self.recover_delay == "0":
                    self.module.fail_json(
                        msg='Error: The default value of recover_delay is 0.')
                recover_delay = "0"
                conf_str += "<recoverDelay>%s</recoverDelay>" % recover_delay
            if self.version:
                if self.version == "v2":
                    self.module.fail_json(
                        msg='Error: The default value of version is v2.')
                version = "v2"
                conf_str += "<version>%s</version>" % version
            conf_str += CE_NC_SET_VRRP_GLOBAL_TAIL
            recv_xml = set_nc_config(self.module, conf_str)
            if "<ok/>" not in recv_xml:
                self.module.fail_json(
                    msg='Error: set vrrp global atrribute info failed.')
            if self.gratuitous_arp_interval:
                self.updates_cmd.append("undo vrrp gratuitous-arp interval")

            if self.recover_delay:
                self.updates_cmd.append("undo vrrp recover-delay")

            if self.version == "v3":
                self.updates_cmd.append("undo vrrp version")
            self.changed = True

    def set_vrrp_group(self):
        """set vrrp group attribute info"""

        if self.is_vrrp_group_info_change():
            conf_str = CE_NC_SET_VRRP_GROUP_INFO_HEAD % (
                self.interface, self.vrid)
            if self.vrrp_type:
                conf_str += "<vrrpType>%s</vrrpType>" % self.vrrp_type
            if self.admin_vrid:
                conf_str += "<adminVrrpId>%s</adminVrrpId>" % self.admin_vrid
            if self.admin_interface:
                conf_str += "<adminIfName>%s</adminIfName>" % self.admin_interface
                if self.admin_flowdown is True or self.admin_flowdown is False:
                    admin_flowdown = "false"
                    if self.admin_flowdown is True:
                        admin_flowdown = "true"
                    conf_str += "<unflowdown>%s</unflowdown>" % admin_flowdown
            if self.priority:
                conf_str += "<priority>%s</priority>" % self.priority
            if self.vrrp_type == "admin":
                if self.admin_ignore_if_down is True or self.admin_ignore_if_down is False:
                    admin_ignore_if_down = "false"
                    if self.admin_ignore_if_down is True:
                        admin_ignore_if_down = "true"
                    conf_str += "<adminIgnoreIfDown>%s</adminIgnoreIfDown>" % admin_ignore_if_down
            if self.fast_resume:
                fast_resume = "false"
                if self.fast_resume == "enable":
                    fast_resume = "true"
                conf_str += "<fastResume>%s</fastResume>" % fast_resume
            if self.advertise_interval:
                conf_str += "<advertiseInterval>%s</advertiseInterval>" % self.advertise_interval
            if self.preempt_timer_delay:
                conf_str += "<delayTime>%s</delayTime>" % self.preempt_timer_delay
            if self.holding_multiplier:
                conf_str += "<holdMultiplier>%s</holdMultiplier>" % self.holding_multiplier
            if self.auth_mode:
                conf_str += "<authenticationMode>%s</authenticationMode>" % self.auth_mode
            if self.auth_key:
                conf_str += "<authenticationKey>%s</authenticationKey>" % self.auth_key
            if self.auth_mode == "simple":
                is_plain = "false"
                if self.is_plain is True:
                    is_plain = "true"
                conf_str += "<isPlain>%s</isPlain>" % is_plain

            conf_str += CE_NC_SET_VRRP_GROUP_INFO_TAIL
            recv_xml = set_nc_config(self.module, conf_str)
            if "<ok/>" not in recv_xml:
                self.module.fail_json(
                    msg='Error: set vrrp group atrribute info failed.')

            if self.interface and self.vrid:
                if self.vrrp_type == "admin":
                    if self.admin_ignore_if_down is True:
                        self.updates_cmd.append(
                            "interface %s" % self.interface)
                        self.updates_cmd.append(
                            "vrrp vrid %s admin ignore-if-down" % self.vrid)
                    else:
                        self.updates_cmd.append(
                            "interface %s" % self.interface)
                        self.updates_cmd.append(
                            "vrrp vrid %s admin" % self.vrid)

                if self.priority:
                    self.updates_cmd.append("interface %s" % self.interface)
                    self.updates_cmd.append(
                        "vrrp vrid %s priority %s" % (self.vrid, self.priority))

                if self.fast_resume == "enable":
                    self.updates_cmd.append("interface %s" % self.interface)
                    self.updates_cmd.append(
                        "vrrp vrid %s fast-resume" % self.vrid)
                if self.fast_resume == "disable":
                    self.updates_cmd.append("interface %s" % self.interface)
                    self.updates_cmd.append(
                        "undo vrrp vrid %s fast-resume" % self.vrid)

                if self.advertise_interval:
                    self.updates_cmd.append("interface %s" % self.interface)
                    self.updates_cmd.append("vrrp vrid %s timer advertise %s" % (
                        self.vrid, self.advertise_interval))

                if self.preempt_timer_delay:
                    self.updates_cmd.append("interface %s" % self.interface)
                    self.updates_cmd.append("vrrp vrid %s preempt timer delay %s" % (self.vrid,
                                                                                     self.preempt_timer_delay))

                if self.holding_multiplier:
                    self.updates_cmd.append("interface %s" % self.interface)
                    self.updates_cmd.append(
                        "vrrp vrid %s holding-multiplier %s" % (self.vrid, self.holding_multiplier))

                if self.admin_vrid and self.admin_interface:
                    if self.admin_flowdown is True:
                        self.updates_cmd.append(
                            "interface %s" % self.interface)
                        self.updates_cmd.append("vrrp vrid %s track admin-vrrp interface %s vrid %s unflowdown" %
                                                (self.vrid, self.admin_interface, self.admin_vrid))
                    else:
                        self.updates_cmd.append(
                            "interface %s" % self.interface)
                        self.updates_cmd.append("vrrp vrid %s track admin-vrrp interface %s vrid %s" %
                                                (self.vrid, self.admin_interface, self.admin_vrid))

                if self.auth_mode and self.auth_key:
                    if self.auth_mode == "simple":
                        if self.is_plain is True:
                            self.updates_cmd.append(
                                "interface %s" % self.interface)
                            self.updates_cmd.append("vrrp vrid %s authentication-mode simple plain %s" %
                                                    (self.vrid, self.auth_key))
                        else:
                            self.updates_cmd.append(
                                "interface %s" % self.interface)
                            self.updates_cmd.append("vrrp vrid %s authentication-mode simple cipher %s" %
                                                    (self.vrid, self.auth_key))
                    if self.auth_mode == "md5":
                        self.updates_cmd.append(
                            "interface %s" % self.interface)
                        self.updates_cmd.append(
                            "vrrp vrid %s authentication-mode md5 %s" % (self.vrid, self.auth_key))
                self.changed = True

    def delete_vrrp_group(self):
        """delete vrrp group attribute info"""

        if self.is_vrrp_group_info_exist():
            conf_str = CE_NC_SET_VRRP_GROUP_INFO_HEAD % (
                self.interface, self.vrid)
            if self.vrrp_type:
                vrrp_type = self.vrrp_type
                if self.vrrp_type == "admin":
                    vrrp_type = "normal"
                if self.vrrp_type == "member" and self.admin_vrid and self.admin_interface:
                    vrrp_type = "normal"
                conf_str += "<vrrpType>%s</vrrpType>" % vrrp_type
            if self.priority:
                if self.priority == "100":
                    self.module.fail_json(
                        msg='Error: The default value of priority is 100.')
                priority = "100"
                conf_str += "<priority>%s</priority>" % priority

            if self.fast_resume:
                fast_resume = "false"
                if self.fast_resume == "enable":
                    fast_resume = "true"
                conf_str += "<fastResume>%s</fastResume>" % fast_resume
            if self.advertise_interval:
                if self.advertise_interval == "1000":
                    self.module.fail_json(
                        msg='Error: The default value of advertise_interval is 1000.')
                advertise_interval = "1000"
                conf_str += "<advertiseInterval>%s</advertiseInterval>" % advertise_interval
            if self.preempt_timer_delay:
                if self.preempt_timer_delay == "0":
                    self.module.fail_json(
                        msg='Error: The default value of preempt_timer_delay is 0.')
                preempt_timer_delay = "0"
                conf_str += "<delayTime>%s</delayTime>" % preempt_timer_delay
            if self.holding_multiplier:
                if self.holding_multiplier == "0":
                    self.module.fail_json(
                        msg='Error: The default value of holding_multiplier is 3.')
                holding_multiplier = "3"
                conf_str += "<holdMultiplier>%s</holdMultiplier>" % holding_multiplier
            if self.auth_mode:
                auth_mode = self.auth_mode
                if self.auth_mode == "md5" or self.auth_mode == "simple":
                    auth_mode = "none"
                conf_str += "<authenticationMode>%s</authenticationMode>" % auth_mode

            conf_str += CE_NC_SET_VRRP_GROUP_INFO_TAIL
            recv_xml = set_nc_config(self.module, conf_str)
            if "<ok/>" not in recv_xml:
                self.module.fail_json(
                    msg='Error: set vrrp global atrribute info failed.')
            if self.interface and self.vrid:
                if self.vrrp_type == "admin":
                    self.updates_cmd.append(
                        "undo vrrp vrid %s admin" % self.vrid)

                if self.priority:
                    self.updates_cmd.append("interface %s" % self.interface)
                    self.updates_cmd.append(
                        "undo vrrp vrid %s priority" % self.vrid)

                if self.fast_resume:
                    self.updates_cmd.append("interface %s" % self.interface)
                    self.updates_cmd.append(
                        "undo vrrp vrid %s fast-resume" % self.vrid)

                if self.advertise_interval:
                    self.updates_cmd.append("interface %s" % self.interface)
                    self.updates_cmd.append(
                        "undo vrrp vrid %s timer advertise" % self.vrid)

                if self.preempt_timer_delay:
                    self.updates_cmd.append("interface %s" % self.interface)
                    self.updates_cmd.append(
                        "undo vrrp vrid %s preempt timer delay" % self.vrid)

                if self.holding_multiplier:
                    self.updates_cmd.append("interface %s" % self.interface)
                    self.updates_cmd.append(
                        "undo vrrp vrid %s holding-multiplier" % self.vrid)

                if self.admin_vrid and self.admin_interface:
                    self.updates_cmd.append("interface %s" % self.interface)
                    self.updates_cmd.append(
                        "undo vrrp vrid %s track admin-vrrp" % self.vrid)

                if self.auth_mode:
                    self.updates_cmd.append("interface %s" % self.interface)
                    self.updates_cmd.append(
                        "undo vrrp vrid %s authentication-mode" % self.vrid)
                self.changed = True

    def get_proposed(self):
        """get proposed info"""

        if self.interface:
            self.proposed["interface"] = self.interface
        if self.vrid:
            self.proposed["vrid"] = self.vrid
        if self.virtual_ip:
            self.proposed["virtual_ip"] = self.virtual_ip
        if self.vrrp_type:
            self.proposed["vrrp_type"] = self.vrrp_type
        if self.admin_vrid:
            self.proposed["admin_vrid"] = self.admin_vrid
        if self.admin_interface:
            self.proposed["admin_interface"] = self.admin_interface
        if self.admin_flowdown:
            self.proposed["unflowdown"] = self.admin_flowdown
        if self.admin_ignore_if_down:
            self.proposed["admin_ignore_if_down"] = self.admin_ignore_if_down
        if self.priority:
            self.proposed["priority"] = self.priority
        if self.version:
            self.proposed["version"] = self.version
        if self.advertise_interval:
            self.proposed["advertise_interval"] = self.advertise_interval
        if self.preempt_timer_delay:
            self.proposed["preempt_timer_delay"] = self.preempt_timer_delay
        if self.gratuitous_arp_interval:
            self.proposed[
                "gratuitous_arp_interval"] = self.gratuitous_arp_interval
        if self.recover_delay:
            self.proposed["recover_delay"] = self.recover_delay
        if self.holding_multiplier:
            self.proposed["holding_multiplier"] = self.holding_multiplier
        if self.auth_mode:
            self.proposed["auth_mode"] = self.auth_mode
        if self.is_plain:
            self.proposed["is_plain"] = self.is_plain
        if self.auth_key:
            self.proposed["auth_key"] = self.auth_key
        if self.fast_resume:
            self.proposed["fast_resume"] = self.fast_resume
        if self.state:
            self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""

        if self.gratuitous_arp_interval:
            self.existing["gratuitous_arp_interval"] = self.vrrp_global_info[
                "gratuitousArpTimeOut"]
        if self.version:
            self.existing["version"] = self.vrrp_global_info["version"]
        if self.recover_delay:
            self.existing["recover_delay"] = self.vrrp_global_info[
                "recoverDelay"]

        if self.virtual_ip:
            if self.virtual_ip_info:
                self.existing["interface"] = self.interface
                self.existing["vrid"] = self.vrid
                self.existing["virtual_ip_info"] = self.virtual_ip_info[
                    "vrrpVirtualIpInfos"]

        if self.vrrp_group_info:
            self.existing["interface"] = self.vrrp_group_info["ifName"]
            self.existing["vrid"] = self.vrrp_group_info["vrrpId"]
            self.existing["vrrp_type"] = self.vrrp_group_info["vrrpType"]
            if self.vrrp_type == "admin":
                self.existing["admin_ignore_if_down"] = self.vrrp_group_info[
                    "authenticationMode"]
            if self.admin_vrid and self.admin_interface:
                self.existing["admin_vrid"] = self.vrrp_group_info[
                    "adminVrrpId"]
                self.existing["admin_interface"] = self.vrrp_group_info[
                    "adminIfName"]
                self.existing["admin_flowdown"] = self.vrrp_group_info[
                    "unflowdown"]
            if self.priority:
                self.existing["priority"] = self.vrrp_group_info["priority"]
            if self.advertise_interval:
                self.existing["advertise_interval"] = self.vrrp_group_info[
                    "advertiseInterval"]
            if self.preempt_timer_delay:
                self.existing["preempt_timer_delay"] = self.vrrp_group_info[
                    "delayTime"]
            if self.holding_multiplier:
                self.existing["holding_multiplier"] = self.vrrp_group_info[
                    "holdMultiplier"]
            if self.fast_resume:
                fast_resume_exist = "disable"
                fast_resume = self.vrrp_group_info["fastResume"]
                if fast_resume == "true":
                    fast_resume_exist = "enable"
                self.existing["fast_resume"] = fast_resume_exist
            if self.auth_mode:
                self.existing["auth_mode"] = self.vrrp_group_info[
                    "authenticationMode"]
                self.existing["is_plain"] = self.vrrp_group_info["isPlain"]

    def get_end_state(self):
        """get end state info"""

        if self.gratuitous_arp_interval or self.version or self.recover_delay:
            self.vrrp_global_info = self.get_vrrp_global_info()
        if self.interface and self.vrid:
            if self.virtual_ip:
                self.virtual_ip_info = self.get_virtual_ip_info()
            if self.virtual_ip_info:
                self.vrrp_group_info = self.get_vrrp_group_info()

        if self.gratuitous_arp_interval:
            self.end_state["gratuitous_arp_interval"] = self.vrrp_global_info[
                "gratuitousArpTimeOut"]
        if self.version:
            self.end_state["version"] = self.vrrp_global_info["version"]
        if self.recover_delay:
            self.end_state["recover_delay"] = self.vrrp_global_info[
                "recoverDelay"]

        if self.virtual_ip:
            if self.virtual_ip_info:
                self.end_state["interface"] = self.interface
                self.end_state["vrid"] = self.vrid
                self.end_state["virtual_ip_info"] = self.virtual_ip_info[
                    "vrrpVirtualIpInfos"]

        if self.vrrp_group_info:
            self.end_state["interface"] = self.vrrp_group_info["ifName"]
            self.end_state["vrid"] = self.vrrp_group_info["vrrpId"]
            self.end_state["vrrp_type"] = self.vrrp_group_info["vrrpType"]
            if self.vrrp_type == "admin":
                self.end_state["admin_ignore_if_down"] = self.vrrp_group_info[
                    "authenticationMode"]
            if self.admin_vrid and self.admin_interface:
                self.existing["admin_vrid"] = self.vrrp_group_info[
                    "adminVrrpId"]
                self.end_state["admin_interface"] = self.vrrp_group_info[
                    "adminIfName"]
                self.end_state["admin_flowdown"] = self.vrrp_group_info[
                    "unflowdown"]
            if self.priority:
                self.end_state["priority"] = self.vrrp_group_info["priority"]
            if self.advertise_interval:
                self.end_state["advertise_interval"] = self.vrrp_group_info[
                    "advertiseInterval"]
            if self.preempt_timer_delay:
                self.end_state["preempt_timer_delay"] = self.vrrp_group_info[
                    "delayTime"]
            if self.holding_multiplier:
                self.end_state["holding_multiplier"] = self.vrrp_group_info[
                    "holdMultiplier"]
            if self.fast_resume:
                fast_resume_end = "disable"
                fast_resume = self.vrrp_group_info["fastResume"]
                if fast_resume == "true":
                    fast_resume_end = "enable"
                self.end_state["fast_resume"] = fast_resume_end
            if self.auth_mode:
                self.end_state["auth_mode"] = self.vrrp_group_info[
                    "authenticationMode"]
                self.end_state["is_plain"] = self.vrrp_group_info["isPlain"]

    def work(self):
        """worker"""

        self.check_params()
        if self.gratuitous_arp_interval or self.version or self.recover_delay:
            self.vrrp_global_info = self.get_vrrp_global_info()
        if self.interface and self.vrid:
            self.virtual_ip_info = self.get_virtual_ip_info()
            if self.virtual_ip_info:
                self.vrrp_group_info = self.get_vrrp_group_info()
        self.get_proposed()
        self.get_existing()

        if self.gratuitous_arp_interval or self.version or self.recover_delay:
            if self.state == "present":
                self.set_vrrp_global()
            else:
                self.delete_vrrp_global()
        else:
            if not self.interface or not self.vrid:
                self.module.fail_json(
                    msg='Error: interface, vrid must be config at the same time.')

        if self.interface and self.vrid:
            if self.virtual_ip:
                if self.state == "present":
                    self.create_virtual_ip()
                else:
                    self.delete_virtual_ip()
            else:
                if not self.vrrp_group_info:
                    self.module.fail_json(
                        msg='Error: The VRRP group does not exist.')
                if self.admin_ignore_if_down is True:
                    if self.vrrp_type != "admin":
                        self.module.fail_json(
                            msg='Error: vrrpType must be admin when admin_ignore_if_down is true.')
                if self.admin_interface or self.admin_vrid:
                    if self.vrrp_type != "member":
                        self.module.fail_json(
                            msg='Error: it binds a VRRP group to an mVRRP group, vrrp_type must be "member".')
                    if not self.vrrp_type or not self.interface or not self.vrid:
                        self.module.fail_json(
                            msg='Error: admin_interface admin_vrid vrrp_type interface vrid must '
                                'be config at the same time.')
                if self.auth_mode == "md5" and self.is_plain is True:
                    self.module.fail_json(
                        msg='Error: is_plain can not be True when auth_mode is md5.')

                if self.state == "present":
                    self.set_vrrp_group()
                else:
                    self.delete_vrrp_group()

        self.get_end_state()
        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        if self.changed:
            self.results['updates'] = self.updates_cmd
        else:
            self.results['updates'] = list()

        self.module.exit_json(**self.results)


def main():
    """ Module main """

    argument_spec = dict(
        interface=dict(type='str'),
        vrid=dict(type='str'),
        virtual_ip=dict(type='str'),
        vrrp_type=dict(type='str', choices=['normal', 'member', 'admin']),
        admin_ignore_if_down=dict(type='bool', default=False),
        admin_vrid=dict(type='str'),
        admin_interface=dict(type='str'),
        admin_flowdown=dict(type='bool', default=False),
        priority=dict(type='str'),
        version=dict(type='str', choices=['v2', 'v3']),
        advertise_interval=dict(type='str'),
        preempt_timer_delay=dict(type='str'),
        gratuitous_arp_interval=dict(type='str'),
        recover_delay=dict(type='str'),
        holding_multiplier=dict(type='str'),
        auth_mode=dict(type='str', choices=['simple', 'md5', 'none']),
        is_plain=dict(type='bool', default=False),
        auth_key=dict(type='str'),
        fast_resume=dict(type='str', choices=['enable', 'disable']),
        state=dict(type='str', default='present',
                   choices=['present', 'absent'])
    )

    argument_spec.update(ce_argument_spec)
    module = Vrrp(argument_spec=argument_spec)
    module.work()


if __name__ == '__main__':
    main()
