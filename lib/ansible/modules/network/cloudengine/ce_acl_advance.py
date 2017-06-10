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
module: ce_acl_advance
version_added: "2.4"
short_description: Manages advanced ACL configuration on HUAWEI CloudEngine switches.
description:
    - Manages advanced ACL configurations on HUAWEI CloudEngine switches.
author:
    - wangdezhuang (@CloudEngine-Ansible)
options:
    state:
        description:
            - Specify desired state of the resource.
        required: false
        default: present
        choices: ['present','absent','delete_acl']
    acl_name:
        description:
            - ACL number or name.
              For a numbered rule group, the value ranging from 3000 to 3999 indicates a advance ACL.
              For a named rule group, the value is a string of 1 to 32 case-sensitive characters starting
              with a letter, spaces not supported.
        required: true
    acl_num:
        description:
            - ACL number.
              The value is an integer ranging from 3000 to 3999.
        required: false
        default: null
    acl_step:
        description:
            - ACL step.
              The value is an integer ranging from 1 to 20. The default value is 5.
        required: false
        default: null
    acl_description:
        description:
            - ACL description.
              The value is a string of 1 to 127 characters.
        required: false
        default: null
    rule_name:
        description:
            - Name of a basic ACL rule.
              The value is a string of 1 to 32 characters.
        required: false
        default: null
    rule_id:
        description:
            - ID of a basic ACL rule in configuration mode.
              The value is an integer ranging from 0 to 4294967294.
        required: false
        default: null
    rule_action:
        description:
            - Matching mode of basic ACL rules.
        required: false
        default: null
        choices: ['permit','deny']
    protocol:
        description:
            - Protocol type.
        required: false
        default: null
        choices: ['ip', 'icmp', 'igmp', 'ipinip', 'tcp', 'udp', 'gre', 'ospf']
    source_ip:
        description:
            - Source IP address.
              The value is a string of 0 to 255 characters.The default value is 0.0.0.0.
              The value is in dotted decimal notation.
        required: false
        default: null
    src_mask:
        description:
            - Source IP address mask.
              The value is an integer ranging from 1 to 32.
        required: false
        default: null
    src_pool_name:
        description:
            - Name of a source pool.
              The value is a string of 1 to 32 characters.
        required: false
        default: null
    dest_ip:
        description:
            - Destination IP address.
              The value is a string of 0 to 255 characters.The default value is 0.0.0.0.
              The value is in dotted decimal notation.
        required: false
        default: null
    dest_mask:
        description:
            - Destination IP address mask.
              The value is an integer ranging from 1 to 32.
        required: false
        default: null
    dest_pool_name:
        description:
            - Name of a destination pool.
              The value is a string of 1 to 32 characters.
        required: false
        default: null
    src_port_op:
        description:
            - Range type of the source port.
        required: false
        default: null
        choices: ['lt','eq', 'gt', 'range']
    src_port_begin:
        description:
            - Start port number of the source port.
              The value is an integer ranging from 0 to 65535.
        required: false
        default: null
    src_port_end:
        description:
            - End port number of the source port.
              The value is an integer ranging from 0 to 65535.
        required: false
        default: null
    src_port_pool_name:
        description:
            - Name of a source port pool.
              The value is a string of 1 to 32 characters.
        required: false
        default: null
    dest_port_op:
        description:
            - Range type of the destination port.
        required: false
        default: null
        choices: ['lt','eq', 'gt', 'range']
    dest_port_begin:
        description:
            - Start port number of the destination port.
              The value is an integer ranging from 0 to 65535.
        required: false
        default: null
    dest_port_end:
        description:
            - End port number of the destination port.
              The value is an integer ranging from 0 to 65535.
        required: false
        default: null
    dest_port_pool_name:
        description:
            - Name of a destination port pool.
              The value is a string of 1 to 32 characters.
        required: false
        default: null
    frag_type:
        description:
            - Type of packet fragmentation.
        required: false
        default: null
        choices: ['fragment', 'clear_fragment']
    precedence:
        description:
            - Data packets can be filtered based on the priority field.
              The value is an integer ranging from 0 to 7.
        required: false
        default: null
    tos:
        description:
            - ToS value on which data packet filtering is based.
              The value is an integer ranging from 0 to 15.
        required: false
        default: null
    dscp:
        description:
            - Differentiated Services Code Point.
              The value is an integer ranging from 0 to 63.
        required: false
        default: null
    icmp_name:
        description:
            - ICMP name.
        required: false
        default: null
        choices: ['unconfiged', 'echo', 'echo-reply', 'fragmentneed-DFset', 'host-redirect',
                  'host-tos-redirect', 'host-unreachable', 'information-reply', 'information-request',
                  'net-redirect', 'net-tos-redirect', 'net-unreachable', 'parameter-problem',
                  'port-unreachable', 'protocol-unreachable', 'reassembly-timeout', 'source-quench',
                  'source-route-failed', 'timestamp-reply', 'timestamp-request', 'ttl-exceeded',
                  'address-mask-reply', 'address-mask-request', 'custom']
    icmp_type:
        description:
            - ICMP type. This parameter is available only when the packet protocol is ICMP.
              The value is an integer ranging from 0 to 255.
        required: false
        default: null
    icmp_code:
        description:
            - ICMP message code. Data packets can be filtered based on the ICMP message code.
              The value is an integer ranging from 0 to 255.
        required: false
        default: null
    ttl_expired:
        description:
            - Whether TTL Expired is matched, with the TTL value of 1.
        required: false
        default: false
        choices: ['true', 'false']
    vrf_name:
        description:
            - VPN instance name.
              The value is a string of 1 to 31 characters.The default value is _public_.
        required: false
        default: null
    syn_flag:
        description:
            - TCP flag value.
              The value is an integer ranging from 0 to 63.
        required: false
        default: null
    tcp_flag_mask:
        description:
            - TCP flag mask value.
              The value is an integer ranging from 0 to 63.
        required: false
        default: null
    established:
        description:
            - Match established connections.
        required: false
        default: false
        choices: ['true', 'false']
    time_range:
        description:
            - Name of a time range in which an ACL rule takes effect.
        required: false
        default: null
    rule_description:
        description:
            - Description about an ACL rule.
        required: false
        default: null
    igmp_type:
        description:
            - Internet Group Management Protocol.
        required: false
        default: null
        choices: ['host-query', 'mrouter-adver', 'mrouter-solic', 'mrouter-termi', 'mtrace-resp', 'mtrace-route',
                  'v1host-report', 'v2host-report', 'v2leave-group', 'v3host-report']
    log_flag:
        description:
            - Flag of logging matched data packets.
        required: false
        default: false
        choices: ['true', 'false']
'''

EXAMPLES = '''

- name: CloudEngine advance acl test
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

  - name: "Config ACL"
    ce_acl_advance:
      state: present
      acl_name: 3200
      provider: "{{ cli }}"

  - name: "Undo ACL"
    ce_acl_advance:
      state: delete_acl
      acl_name: 3200
      provider: "{{ cli }}"

  - name: "Config ACL advance rule"
    ce_acl_advance:
      state: present
      acl_name: test
      rule_name: test_rule
      rule_id: 111
      rule_action: permit
      protocol: tcp
      source_ip: 10.10.10.10
      src_mask: 24
      frag_type: fragment
      provider: "{{ cli }}"

  - name: "Undo ACL advance rule"
    ce_acl_advance:
      state: absent
      acl_name: test
      rule_name: test_rule
      rule_id: 111
      rule_action: permit
      protocol: tcp
      source_ip: 10.10.10.10
      src_mask: 24
      frag_type: fragment
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
    sample: {"acl_name": "test", "state": "delete_acl"}
existing:
    description: k/v pairs of existing aaa server
    returned: always
    type: dict
    sample: {"aclNumOrName": "test", "aclType": "Advance"}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["undo acl name test"]
'''

from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ce import get_nc_config, set_nc_config, ce_argument_spec, check_ip_addr


# get acl
CE_GET_ACL_HEADER = """
    <filter type="subtree">
      <acl xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <aclGroups>
          <aclGroup>
            <aclNumOrName></aclNumOrName>
"""
CE_GET_ACL_TAIL = """
          </aclGroup>
        </aclGroups>
      </acl>
    </filter>
"""
# merge acl
CE_MERGE_ACL_HEADER = """
    <config>
      <acl xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <aclGroups>
          <aclGroup operation="merge">
            <aclNumOrName>%s</aclNumOrName>
"""
CE_MERGE_ACL_TAIL = """
          </aclGroup>
        </aclGroups>
      </acl>
    </config>
"""
# delete acl
CE_DELETE_ACL_HEADER = """
    <config>
      <acl xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <aclGroups>
          <aclGroup operation="delete">
            <aclNumOrName>%s</aclNumOrName>
"""
CE_DELETE_ACL_TAIL = """
          </aclGroup>
        </aclGroups>
      </acl>
    </config>
"""

# get acl advance rule
CE_GET_ACL_ADVANCE_RULE_HEADER = """
    <filter type="subtree">
      <acl xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <aclGroups>
          <aclGroup>
            <aclNumOrName>%s</aclNumOrName>
            <aclRuleAdv4s>
              <aclRuleAdv4>
                <aclRuleName></aclRuleName>
"""
CE_GET_ACL_ADVANCE_RULE_TAIL = """
              </aclRuleAdv4>
            </aclRuleAdv4s>
          </aclGroup>
        </aclGroups>
      </acl>
    </filter>
"""
# merge acl advance rule
CE_MERGE_ACL_ADVANCE_RULE_HEADER = """
    <config>
      <acl xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <aclGroups>
          <aclGroup>
            <aclNumOrName>%s</aclNumOrName>
            <aclRuleAdv4s>
              <aclRuleAdv4 operation="merge">
                <aclRuleName>%s</aclRuleName>
"""
CE_MERGE_ACL_ADVANCE_RULE_TAIL = """
              </aclRuleAdv4>
            </aclRuleAdv4s>
          </aclGroup>
        </aclGroups>
      </acl>
    </config>
"""
# delete acl advance rule
CE_DELETE_ACL_ADVANCE_RULE_HEADER = """
    <config>
      <acl xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <aclGroups>
          <aclGroup>
            <aclNumOrName>%s</aclNumOrName>
            <aclRuleAdv4s>
              <aclRuleAdv4 operation="delete">
                <aclRuleName>%s</aclRuleName>
"""
CE_DELETE_ACL_ADVANCE_RULE_TAIL = """
              </aclRuleAdv4>
            </aclRuleAdv4s>
          </aclGroup>
        </aclGroups>
      </acl>
    </config>
"""


PROTOCOL_NUM = {"ip": "0",
                "icmp": "1",
                "igmp": "2",
                "ipinip": "4",
                "tcp": "6",
                "udp": "17",
                "gre": "47",
                "ospf": "89"}

IGMP_TYPE_NUM = {"host-query": "17",
                 "mrouter-adver": "48",
                 "mrouter-solic": "49",
                 "mrouter-termi": "50",
                 "mtrace-resp": "30",
                 "mtrace-route": "31",
                 "v1host-report": "18",
                 "v2host-report": "22",
                 "v2leave-group": "23",
                 "v3host-report": "34"}


def get_wildcard_mask(mask):
    """ convert mask length to ip address wildcard mask, i.e. 24 to 0.0.0.255 """

    mask_int = ["255"] * 4
    value = int(mask)

    if value > 32:
        return None
    if value < 8:
        mask_int[0] = str(int(~(0xFF << (8 - value % 8)) & 0xFF))
    if value >= 8:
        mask_int[0] = '0'
        mask_int[1] = str(int(~(0xFF << (16 - (value % 16))) & 0xFF))
    if value >= 16:
        mask_int[1] = '0'
        mask_int[2] = str(int(~(0xFF << (24 - (value % 24))) & 0xFF))
    if value >= 24:
        mask_int[2] = '0'
        mask_int[3] = str(int(~(0xFF << (32 - (value % 32))) & 0xFF))
    if value == 32:
        mask_int[3] = '0'

    return '.'.join(mask_int)


class AdvanceAcl(object):
    """ Manages advance acl configuration """

    def __init__(self, **kwargs):
        """ Class init """

        # argument spec
        argument_spec = kwargs["argument_spec"]
        self.spec = argument_spec
        self.module = AnsibleModule(argument_spec=self.spec, supports_check_mode=True)

        # module args
        self.state = self.module.params['state']
        self.acl_name = self.module.params['acl_name'] or None
        self.acl_num = self.module.params['acl_num'] or None
        self.acl_type = None
        self.acl_step = self.module.params['acl_step'] or None
        self.acl_description = self.module.params['acl_description'] or None
        self.rule_name = self.module.params['rule_name'] or None
        self.rule_id = self.module.params['rule_id'] or None
        self.rule_action = self.module.params['rule_action'] or None
        self.protocol = self.module.params['protocol'] or None
        self.protocol_num = None
        self.source_ip = self.module.params['source_ip'] or None
        self.src_mask = self.module.params['src_mask'] or None
        self.src_wild = None
        self.src_pool_name = self.module.params['src_pool_name'] or None
        self.dest_ip = self.module.params['dest_ip'] or None
        self.dest_mask = self.module.params['dest_mask'] or None
        self.dest_wild = None
        self.dest_pool_name = self.module.params['dest_pool_name'] or None
        self.src_port_op = self.module.params['src_port_op'] or None
        self.src_port_begin = self.module.params['src_port_begin'] or None
        self.src_port_end = self.module.params['src_port_end'] or None
        self.src_port_pool_name = self.module.params[
            'src_port_pool_name'] or None
        self.dest_port_op = self.module.params['dest_port_op'] or None
        self.dest_port_begin = self.module.params['dest_port_begin'] or None
        self.dest_port_end = self.module.params['dest_port_end'] or None
        self.dest_port_pool_name = self.module.params[
            'dest_port_pool_name'] or None
        self.frag_type = self.module.params['frag_type'] or None
        self.precedence = self.module.params['precedence'] or None
        self.tos = self.module.params['tos'] or None
        self.dscp = self.module.params['dscp'] or None
        self.icmp_name = self.module.params['icmp_name'] or None
        self.icmp_type = self.module.params['icmp_type'] or None
        self.icmp_code = self.module.params['icmp_code'] or None
        self.ttl_expired = self.module.params['ttl_expired']
        self.vrf_name = self.module.params['vrf_name'] or None
        self.syn_flag = self.module.params['syn_flag'] or None
        self.tcp_flag_mask = self.module.params['tcp_flag_mask'] or None
        self.established = self.module.params['established']
        self.time_range = self.module.params['time_range'] or None
        self.rule_description = self.module.params['rule_description'] or None
        self.igmp_type = self.module.params['igmp_type'] or None
        self.igmp_type_num = None
        self.log_flag = self.module.params['log_flag']

        self.precedence_name = dict()
        self.precedence_name["0"] = "routine"
        self.precedence_name["1"] = "priority"
        self.precedence_name["2"] = "immediate"
        self.precedence_name["3"] = "flash"
        self.precedence_name["4"] = "flash-override"
        self.precedence_name["5"] = "critical"
        self.precedence_name["6"] = "internet"
        self.precedence_name["7"] = "network"

        # cur config
        self.cur_acl_cfg = dict()
        self.cur_advance_rule_cfg = dict()

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def netconf_get_config(self, conf_str):
        """ Get configure by netconf """

        xml_str = get_nc_config(self.module, conf_str)

        return xml_str

    def netconf_set_config(self, conf_str):
        """ Set configure by netconf """

        xml_str = set_nc_config(self.module, conf_str)

        return xml_str

    def get_protocol_num(self):
        """ Get protocol num by name """

        if self.protocol:
            self.protocol_num = PROTOCOL_NUM.get(self.protocol)

    def get_igmp_type_num(self):
        """ Get igmp type num by type """

        if self.igmp_type:
            self.igmp_type_num = IGMP_TYPE_NUM.get(self.igmp_type)

    def check_acl_args(self):
        """ Check acl invalid args """

        need_cfg = False
        find_flag = False
        self.cur_acl_cfg["acl_info"] = []

        if self.acl_name:

            if self.acl_name.isdigit():
                if int(self.acl_name) < 3000 or int(self.acl_name) > 3999:
                    self.module.fail_json(
                        msg='Error: The value of acl_name is out of [3000-3999] for advance ACL.')

                if self.acl_num:
                    self.module.fail_json(
                        msg='Error: The acl_name is digit, so should not input acl_num at the same time.')
            else:

                self.acl_type = "Advance"

                if len(self.acl_name) < 1 or len(self.acl_name) > 32:
                    self.module.fail_json(
                        msg='Error: The len of acl_name is out of [1 - 32].')

                if self.state == "present":
                    if not self.acl_num and not self.acl_type and not self.rule_name:
                        self.module.fail_json(
                            msg='Error: Please input acl_num or acl_type when config ACL.')

            if self.acl_num:
                if self.acl_num.isdigit():
                    if int(self.acl_num) < 3000 or int(self.acl_num) > 3999:
                        self.module.fail_json(
                            msg='Error: The value of acl_name is out of [3000-3999] for advance ACL.')
                else:
                    self.module.fail_json(
                        msg='Error: The acl_num is not digit.')

            if self.acl_step:
                if self.acl_step.isdigit():
                    if int(self.acl_step) < 1 or int(self.acl_step) > 20:
                        self.module.fail_json(
                            msg='Error: The value of acl_step is out of [1 - 20].')
                else:
                    self.module.fail_json(
                        msg='Error: The acl_step is not digit.')

            if self.acl_description:
                if len(self.acl_description) < 1 or len(self.acl_description) > 127:
                    self.module.fail_json(
                        msg='Error: The len of acl_description is out of [1 - 127].')

            conf_str = CE_GET_ACL_HEADER

            if self.acl_type:
                conf_str += "<aclType></aclType>"
            if self.acl_num:
                conf_str += "<aclNumber></aclNumber>"
            if self.acl_step:
                conf_str += "<aclStep></aclStep>"
            if self.acl_description:
                conf_str += "<aclDescription></aclDescription>"

            conf_str += CE_GET_ACL_TAIL
            recv_xml = self.netconf_get_config(conf_str=conf_str)

            if "<data/>" in recv_xml:
                find_flag = False

            else:
                xml_str = recv_xml.replace('\r', '').replace('\n', '').\
                    replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                    replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

                root = ElementTree.fromstring(xml_str)

                # parse acl
                acl_info = root.findall(
                    "data/acl/aclGroups/aclGroup")
                if acl_info:
                    for tmp in acl_info:
                        tmp_dict = dict()
                        for site in tmp:
                            if site.tag in ["aclNumOrName", "aclType", "aclNumber", "aclStep", "aclDescription"]:
                                tmp_dict[site.tag] = site.text

                        self.cur_acl_cfg["acl_info"].append(tmp_dict)

                if self.cur_acl_cfg["acl_info"]:
                    for tmp in self.cur_acl_cfg["acl_info"]:
                        find_flag = True

                        if self.acl_name and tmp.get("aclNumOrName") != self.acl_name:
                            find_flag = False
                        if self.acl_type and tmp.get("aclType") != self.acl_type:
                            find_flag = False
                        if self.acl_num and tmp.get("aclNumber") != self.acl_num:
                            find_flag = False
                        if self.acl_step and tmp.get("aclStep") != self.acl_step:
                            find_flag = False
                        if self.acl_description and tmp.get("aclDescription") != self.acl_description:
                            find_flag = False

                        if find_flag:
                            break
                else:
                    find_flag = False

        if self.state == "present":
            need_cfg = bool(not find_flag)
        elif self.state == "delete_acl":
            need_cfg = bool(find_flag)
        else:
            need_cfg = False

        self.cur_acl_cfg["need_cfg"] = need_cfg

    def check_advance_rule_args(self):
        """ Check advance rule invalid args """

        need_cfg = False
        find_flag = False
        self.cur_advance_rule_cfg["adv_rule_info"] = []

        if self.acl_name:

            if self.state == "absent":
                if not self.rule_name:
                    self.module.fail_json(
                        msg='Error: Please input rule_name when state is absent.')

            # config rule
            if self.rule_name:
                if len(self.rule_name) < 1 or len(self.rule_name) > 32:
                    self.module.fail_json(
                        msg='Error: The len of rule_name is out of [1 - 32].')

                if self.state != "delete_acl" and not self.rule_id:
                    self.module.fail_json(
                        msg='Error: Please input rule_id.')

                if self.rule_id:
                    if self.rule_id.isdigit():
                        if int(self.rule_id) < 0 or int(self.rule_id) > 4294967294:
                            self.module.fail_json(
                                msg='Error: The value of rule_id is out of [0 - 4294967294].')
                    else:
                        self.module.fail_json(
                            msg='Error: The rule_id is not digit.')

                if self.rule_action and not self.protocol:
                    self.module.fail_json(
                        msg='Error: The rule_action and the protocol must input at the same time.')

                if not self.rule_action and self.protocol:
                    self.module.fail_json(
                        msg='Error: The rule_action and the protocol must input at the same time.')

                if self.protocol:
                    self.get_protocol_num()

                if self.source_ip:
                    if not check_ip_addr(self.source_ip):
                        self.module.fail_json(
                            msg='Error: The source_ip %s is invalid.' % self.source_ip)
                    if not self.src_mask:
                        self.module.fail_json(
                            msg='Error: Please input src_mask.')

                if self.src_mask:
                    if self.src_mask.isdigit():
                        if int(self.src_mask) < 1 or int(self.src_mask) > 32:
                            self.module.fail_json(
                                msg='Error: The value of src_mask is out of [1 - 32].')
                        self.src_wild = get_wildcard_mask(self.src_mask)
                    else:
                        self.module.fail_json(
                            msg='Error: The src_mask is not digit.')

                if self.src_pool_name:
                    if len(self.src_pool_name) < 1 or len(self.src_pool_name) > 32:
                        self.module.fail_json(
                            msg='Error: The len of src_pool_name is out of [1 - 32].')

                if self.dest_ip:
                    if not check_ip_addr(self.dest_ip):
                        self.module.fail_json(
                            msg='Error: The dest_ip %s is invalid.' % self.dest_ip)
                    if not self.dest_mask:
                        self.module.fail_json(
                            msg='Error: Please input dest_mask.')

                if self.dest_mask:
                    if self.dest_mask.isdigit():
                        if int(self.dest_mask) < 1 or int(self.dest_mask) > 32:
                            self.module.fail_json(
                                msg='Error: The value of dest_mask is out of [1 - 32].')
                        self.dest_wild = get_wildcard_mask(self.dest_mask)
                    else:
                        self.module.fail_json(
                            msg='Error: The dest_mask is not digit.')

                if self.dest_pool_name:
                    if len(self.dest_pool_name) < 1 or len(self.dest_pool_name) > 32:
                        self.module.fail_json(
                            msg='Error: The len of dest_pool_name is out of [1 - 32].')

                if self.src_port_op:
                    if self.src_port_op == "lt":
                        if not self.src_port_end:
                            self.module.fail_json(
                                msg='Error: The src_port_end must input.')
                        if self.src_port_begin:
                            self.module.fail_json(
                                msg='Error: The src_port_begin should not input.')
                    if self.src_port_op == "eq" or self.src_port_op == "gt":
                        if not self.src_port_begin:
                            self.module.fail_json(
                                msg='Error: The src_port_begin must input.')
                        if self.src_port_end:
                            self.module.fail_json(
                                msg='Error: The src_port_end should not input.')
                    if self.src_port_op == "range":
                        if not self.src_port_begin or not self.src_port_end:
                            self.module.fail_json(
                                msg='Error: The src_port_begin and src_port_end must input.')

                if self.src_port_begin:
                    if self.src_port_begin.isdigit():
                        if int(self.src_port_begin) < 0 or int(self.src_port_begin) > 65535:
                            self.module.fail_json(
                                msg='Error: The value of src_port_begin is out of [0 - 65535].')
                    else:
                        self.module.fail_json(
                            msg='Error: The src_port_begin is not digit.')

                if self.src_port_end:
                    if self.src_port_end.isdigit():
                        if int(self.src_port_end) < 0 or int(self.src_port_end) > 65535:
                            self.module.fail_json(
                                msg='Error: The value of src_port_end is out of [0 - 65535].')
                    else:
                        self.module.fail_json(
                            msg='Error: The src_port_end is not digit.')

                if self.src_port_pool_name:
                    if len(self.src_port_pool_name) < 1 or len(self.src_port_pool_name) > 32:
                        self.module.fail_json(
                            msg='Error: The len of src_port_pool_name is out of [1 - 32].')

                if self.dest_port_op:
                    if self.dest_port_op == "lt":
                        if not self.dest_port_end:
                            self.module.fail_json(
                                msg='Error: The dest_port_end must input.')
                        if self.dest_port_begin:
                            self.module.fail_json(
                                msg='Error: The dest_port_begin should not input.')
                    if self.dest_port_op == "eq" or self.dest_port_op == "gt":
                        if not self.dest_port_begin:
                            self.module.fail_json(
                                msg='Error: The dest_port_begin must input.')
                        if self.dest_port_end:
                            self.module.fail_json(
                                msg='Error: The dest_port_end should not input.')
                    if self.dest_port_op == "range":
                        if not self.dest_port_begin or not self.dest_port_end:
                            self.module.fail_json(
                                msg='Error: The dest_port_begin and dest_port_end must input.')

                if self.dest_port_begin:
                    if self.dest_port_begin.isdigit():
                        if int(self.dest_port_begin) < 0 or int(self.dest_port_begin) > 65535:
                            self.module.fail_json(
                                msg='Error: The value of dest_port_begin is out of [0 - 65535].')
                    else:
                        self.module.fail_json(
                            msg='Error: The dest_port_begin is not digit.')

                if self.dest_port_end:
                    if self.dest_port_end.isdigit():
                        if int(self.dest_port_end) < 0 or int(self.dest_port_end) > 65535:
                            self.module.fail_json(
                                msg='Error: The value of dest_port_end is out of [0 - 65535].')
                    else:
                        self.module.fail_json(
                            msg='Error: The dest_port_end is not digit.')

                if self.dest_port_pool_name:
                    if len(self.dest_port_pool_name) < 1 or len(self.dest_port_pool_name) > 32:
                        self.module.fail_json(
                            msg='Error: The len of dest_port_pool_name is out of [1 - 32].')

                if self.precedence:
                    if self.precedence.isdigit():
                        if int(self.precedence) < 0 or int(self.precedence) > 7:
                            self.module.fail_json(
                                msg='Error: The value of precedence is out of [0 - 7].')
                    else:
                        self.module.fail_json(
                            msg='Error: The precedence is not digit.')

                if self.tos:
                    if self.tos.isdigit():
                        if int(self.tos) < 0 or int(self.tos) > 15:
                            self.module.fail_json(
                                msg='Error: The value of tos is out of [0 - 15].')
                    else:
                        self.module.fail_json(
                            msg='Error: The tos is not digit.')

                if self.dscp:
                    if self.dscp.isdigit():
                        if int(self.dscp) < 0 or int(self.dscp) > 63:
                            self.module.fail_json(
                                msg='Error: The value of dscp is out of [0 - 63].')
                    else:
                        self.module.fail_json(
                            msg='Error: The dscp is not digit.')

                if self.icmp_type:
                    if self.icmp_type.isdigit():
                        if int(self.icmp_type) < 0 or int(self.icmp_type) > 255:
                            self.module.fail_json(
                                msg='Error: The value of icmp_type is out of [0 - 255].')
                    else:
                        self.module.fail_json(
                            msg='Error: The icmp_type is not digit.')

                if self.icmp_code:
                    if self.icmp_code.isdigit():
                        if int(self.icmp_code) < 0 or int(self.icmp_code) > 255:
                            self.module.fail_json(
                                msg='Error: The value of icmp_code is out of [0 - 255].')
                    else:
                        self.module.fail_json(
                            msg='Error: The icmp_code is not digit.')

                if self.vrf_name:
                    if len(self.vrf_name) < 1 or len(self.vrf_name) > 31:
                        self.module.fail_json(
                            msg='Error: The len of vrf_name is out of [1 - 31].')

                if self.syn_flag:
                    if self.syn_flag.isdigit():
                        if int(self.syn_flag) < 0 or int(self.syn_flag) > 63:
                            self.module.fail_json(
                                msg='Error: The value of syn_flag is out of [0 - 63].')
                    else:
                        self.module.fail_json(
                            msg='Error: The syn_flag is not digit.')

                if self.tcp_flag_mask:
                    if self.tcp_flag_mask.isdigit():
                        if int(self.tcp_flag_mask) < 0 or int(self.tcp_flag_mask) > 63:
                            self.module.fail_json(
                                msg='Error: The value of tcp_flag_mask is out of [0 - 63].')
                    else:
                        self.module.fail_json(
                            msg='Error: The tcp_flag_mask is not digit.')

                if self.time_range:
                    if len(self.time_range) < 1 or len(self.time_range) > 32:
                        self.module.fail_json(
                            msg='Error: The len of time_range is out of [1 - 32].')

                if self.rule_description:
                    if len(self.rule_description) < 1 or len(self.rule_description) > 127:
                        self.module.fail_json(
                            msg='Error: The len of rule_description is out of [1 - 127].')

                if self.igmp_type:
                    self.get_igmp_type_num()

                conf_str = CE_GET_ACL_ADVANCE_RULE_HEADER % self.acl_name

                if self.rule_id:
                    conf_str += "<aclRuleID></aclRuleID>"
                if self.rule_action:
                    conf_str += "<aclAction></aclAction>"
                if self.protocol:
                    conf_str += "<aclProtocol></aclProtocol>"
                if self.source_ip:
                    conf_str += "<aclSourceIp></aclSourceIp>"
                if self.src_wild:
                    conf_str += "<aclSrcWild></aclSrcWild>"
                if self.src_pool_name:
                    conf_str += "<aclSPoolName></aclSPoolName>"
                if self.dest_ip:
                    conf_str += "<aclDestIp></aclDestIp>"
                if self.dest_wild:
                    conf_str += "<aclDestWild></aclDestWild>"
                if self.dest_pool_name:
                    conf_str += "<aclDPoolName></aclDPoolName>"
                if self.src_port_op:
                    conf_str += "<aclSrcPortOp></aclSrcPortOp>"
                if self.src_port_begin:
                    conf_str += "<aclSrcPortBegin></aclSrcPortBegin>"
                if self.src_port_end:
                    conf_str += "<aclSrcPortEnd></aclSrcPortEnd>"
                if self.src_port_pool_name:
                    conf_str += "<aclSPortPoolName></aclSPortPoolName>"
                if self.dest_port_op:
                    conf_str += "<aclDestPortOp></aclDestPortOp>"
                if self.dest_port_begin:
                    conf_str += "<aclDestPortB></aclDestPortB>"
                if self.dest_port_end:
                    conf_str += "<aclDestPortE></aclDestPortE>"
                if self.dest_port_pool_name:
                    conf_str += "<aclDPortPoolName></aclDPortPoolName>"
                if self.frag_type:
                    conf_str += "<aclFragType></aclFragType>"
                if self.precedence:
                    conf_str += "<aclPrecedence></aclPrecedence>"
                if self.tos:
                    conf_str += "<aclTos></aclTos>"
                if self.dscp:
                    conf_str += "<aclDscp></aclDscp>"
                if self.icmp_name:
                    conf_str += "<aclIcmpName></aclIcmpName>"
                if self.icmp_type:
                    conf_str += "<aclIcmpType></aclIcmpType>"
                if self.icmp_code:
                    conf_str += "<aclIcmpCode></aclIcmpCode>"
                conf_str += "<aclTtlExpired></aclTtlExpired>"
                if self.vrf_name:
                    conf_str += "<vrfName></vrfName>"
                if self.syn_flag:
                    conf_str += "<aclSynFlag></aclSynFlag>"
                if self.tcp_flag_mask:
                    conf_str += "<aclTcpFlagMask></aclTcpFlagMask>"
                conf_str += "<aclEstablished></aclEstablished>"
                if self.time_range:
                    conf_str += "<aclTimeName></aclTimeName>"
                if self.rule_description:
                    conf_str += "<aclRuleDescription></aclRuleDescription>"
                if self.igmp_type:
                    conf_str += "<aclIgmpType></aclIgmpType>"
                conf_str += "<aclLogFlag></aclLogFlag>"

                conf_str += CE_GET_ACL_ADVANCE_RULE_TAIL
                recv_xml = self.netconf_get_config(conf_str=conf_str)

                if "<data/>" in recv_xml:
                    find_flag = False

                else:
                    xml_str = recv_xml.replace('\r', '').replace('\n', '').\
                        replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                        replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

                    root = ElementTree.fromstring(xml_str)

                    # parse advance rule
                    adv_rule_info = root.findall(
                        "data/acl/aclGroups/aclGroup/aclRuleAdv4s/aclRuleAdv4")
                    if adv_rule_info:
                        for tmp in adv_rule_info:
                            tmp_dict = dict()
                            for site in tmp:
                                if site.tag in ["aclRuleName", "aclRuleID", "aclAction", "aclProtocol", "aclSourceIp",
                                                "aclSrcWild", "aclSPoolName", "aclDestIp", "aclDestWild",
                                                "aclDPoolName", "aclSrcPortOp", "aclSrcPortBegin", "aclSrcPortEnd",
                                                "aclSPortPoolName", "aclDestPortOp", "aclDestPortB", "aclDestPortE",
                                                "aclDPortPoolName", "aclFragType", "aclPrecedence", "aclTos",
                                                "aclDscp", "aclIcmpName", "aclIcmpType", "aclIcmpCode", "aclTtlExpired",
                                                "vrfName", "aclSynFlag", "aclTcpFlagMask", "aclEstablished",
                                                "aclTimeName", "aclRuleDescription", "aclIgmpType", "aclLogFlag"]:
                                    tmp_dict[site.tag] = site.text

                            self.cur_advance_rule_cfg[
                                "adv_rule_info"].append(tmp_dict)

                    if self.cur_advance_rule_cfg["adv_rule_info"]:
                        for tmp in self.cur_advance_rule_cfg["adv_rule_info"]:
                            find_flag = True

                            if self.rule_name and tmp.get("aclRuleName") != self.rule_name:
                                find_flag = False
                            if self.rule_id and tmp.get("aclRuleID") != self.rule_id:
                                find_flag = False
                            if self.rule_action and tmp.get("aclAction") != self.rule_action:
                                find_flag = False
                            if self.protocol and tmp.get("aclProtocol") != self.protocol_num:
                                find_flag = False
                            if self.source_ip:
                                tmp_src_ip = self.source_ip.split(".")
                                tmp_src_wild = self.src_wild.split(".")
                                tmp_addr_item = []
                                for idx in range(4):
                                    item1 = 255 - int(tmp_src_wild[idx])
                                    item2 = item1 & int(tmp_src_ip[idx])
                                    tmp_addr_item.append(item2)
                                tmp_addr = "%s.%s.%s.%s" % (tmp_addr_item[0], tmp_addr_item[1],
                                                            tmp_addr_item[2], tmp_addr_item[3])
                                if tmp_addr != tmp.get("aclSourceIp"):
                                    find_flag = False
                            if self.src_wild and tmp.get("aclSrcWild") != self.src_wild:
                                find_flag = False
                            if self.src_pool_name and tmp.get("aclSPoolName") != self.src_pool_name:
                                find_flag = False
                            if self.dest_ip:
                                tmp_src_ip = self.dest_ip.split(".")
                                tmp_src_wild = self.dest_wild.split(".")
                                tmp_addr_item = []
                                for idx in range(4):
                                    item1 = 255 - int(tmp_src_wild[idx])
                                    item2 = item1 & int(tmp_src_ip[idx])
                                    tmp_addr_item.append(item2)
                                tmp_addr = "%s.%s.%s.%s" % (tmp_addr_item[0], tmp_addr_item[1],
                                                            tmp_addr_item[2], tmp_addr_item[3])
                                if tmp_addr != tmp.get("aclDestIp"):
                                    find_flag = False
                            if self.dest_wild and tmp.get("aclDestWild") != self.dest_wild:
                                find_flag = False
                            if self.dest_pool_name and tmp.get("aclDPoolName") != self.dest_pool_name:
                                find_flag = False
                            if self.src_port_op and tmp.get("aclSrcPortOp") != self.src_port_op:
                                find_flag = False
                            if self.src_port_begin and tmp.get("aclSrcPortBegin") != self.src_port_begin:
                                find_flag = False
                            if self.src_port_end and tmp.get("aclSrcPortEnd") != self.src_port_end:
                                find_flag = False
                            if self.src_port_pool_name and tmp.get("aclSPortPoolName") != self.src_port_pool_name:
                                find_flag = False
                            if self.dest_port_op and tmp.get("aclDestPortOp") != self.dest_port_op:
                                find_flag = False
                            if self.dest_port_begin and tmp.get("aclDestPortB") != self.dest_port_begin:
                                find_flag = False
                            if self.dest_port_end and tmp.get("aclDestPortE") != self.dest_port_end:
                                find_flag = False
                            if self.dest_port_pool_name and tmp.get("aclDPortPoolName") != self.dest_port_pool_name:
                                find_flag = False
                            if self.frag_type and tmp.get("aclFragType") != self.frag_type:
                                find_flag = False
                            if self.precedence and tmp.get("aclPrecedence") != self.precedence:
                                find_flag = False
                            if self.tos and tmp.get("aclTos") != self.tos:
                                find_flag = False
                            if self.dscp and tmp.get("aclDscp") != self.dscp:
                                find_flag = False
                            if self.icmp_name and tmp.get("aclIcmpName") != self.icmp_name:
                                find_flag = False
                            if self.icmp_type and tmp.get("aclIcmpType") != self.icmp_type:
                                find_flag = False
                            if self.icmp_code and tmp.get("aclIcmpCode") != self.icmp_code:
                                find_flag = False
                            if tmp.get("aclTtlExpired").lower() != str(self.ttl_expired).lower():
                                find_flag = False
                            if self.vrf_name and tmp.get("vrfName") != self.vrf_name:
                                find_flag = False
                            if self.syn_flag and tmp.get("aclSynFlag") != self.syn_flag:
                                find_flag = False
                            if self.tcp_flag_mask and tmp.get("aclTcpFlagMask") != self.tcp_flag_mask:
                                find_flag = False
                            if self.protocol == "tcp" and \
                                    tmp.get("aclEstablished").lower() != str(self.established).lower():
                                find_flag = False
                            if self.time_range and tmp.get("aclTimeName") != self.time_range:
                                find_flag = False
                            if self.rule_description and tmp.get("aclRuleDescription") != self.rule_description:
                                find_flag = False
                            if self.igmp_type and tmp.get("aclIgmpType") != self.igmp_type_num:
                                find_flag = False
                            if tmp.get("aclLogFlag").lower() != str(self.log_flag).lower():
                                find_flag = False

                            if find_flag:
                                break
                    else:
                        find_flag = False

                if self.state == "present":
                    need_cfg = bool(not find_flag)
                elif self.state == "absent":
                    need_cfg = bool(find_flag)
                else:
                    need_cfg = False

        self.cur_advance_rule_cfg["need_cfg"] = need_cfg

    def get_proposed(self):
        """ Get proposed state """

        self.proposed["state"] = self.state

        if self.acl_name:
            self.proposed["acl_name"] = self.acl_name
        if self.acl_num:
            self.proposed["acl_num"] = self.acl_num
        if self.acl_step:
            self.proposed["acl_step"] = self.acl_step
        if self.acl_description:
            self.proposed["acl_description"] = self.acl_description
        if self.rule_name:
            self.proposed["rule_name"] = self.rule_name
        if self.rule_id:
            self.proposed["rule_id"] = self.rule_id
        if self.rule_action:
            self.proposed["rule_action"] = self.rule_action
        if self.protocol:
            self.proposed["protocol"] = self.protocol
        if self.source_ip:
            self.proposed["source_ip"] = self.source_ip
        if self.src_mask:
            self.proposed["src_mask"] = self.src_mask
        if self.src_pool_name:
            self.proposed["src_pool_name"] = self.src_pool_name
        if self.dest_ip:
            self.proposed["dest_ip"] = self.dest_ip
        if self.dest_mask:
            self.proposed["dest_mask"] = self.dest_mask
        if self.dest_pool_name:
            self.proposed["dest_pool_name"] = self.dest_pool_name
        if self.src_port_op:
            self.proposed["src_port_op"] = self.src_port_op
        if self.src_port_begin:
            self.proposed["src_port_begin"] = self.src_port_begin
        if self.src_port_end:
            self.proposed["src_port_end"] = self.src_port_end
        if self.src_port_pool_name:
            self.proposed["src_port_pool_name"] = self.src_port_pool_name
        if self.dest_port_op:
            self.proposed["dest_port_op"] = self.dest_port_op
        if self.dest_port_begin:
            self.proposed["dest_port_begin"] = self.dest_port_begin
        if self.dest_port_end:
            self.proposed["dest_port_end"] = self.dest_port_end
        if self.dest_port_pool_name:
            self.proposed["dest_port_pool_name"] = self.dest_port_pool_name
        if self.frag_type:
            self.proposed["frag_type"] = self.frag_type
        if self.precedence:
            self.proposed["precedence"] = self.precedence
        if self.tos:
            self.proposed["tos"] = self.tos
        if self.dscp:
            self.proposed["dscp"] = self.dscp
        if self.icmp_name:
            self.proposed["icmp_name"] = self.icmp_name
        if self.icmp_type:
            self.proposed["icmp_type"] = self.icmp_type
        if self.icmp_code:
            self.proposed["icmp_code"] = self.icmp_code
        if self.ttl_expired:
            self.proposed["ttl_expired"] = self.ttl_expired
        if self.vrf_name:
            self.proposed["vrf_name"] = self.vrf_name
        if self.syn_flag:
            self.proposed["syn_flag"] = self.syn_flag
        if self.tcp_flag_mask:
            self.proposed["tcp_flag_mask"] = self.tcp_flag_mask
        self.proposed["established"] = self.established
        if self.time_range:
            self.proposed["time_range"] = self.time_range
        if self.rule_description:
            self.proposed["rule_description"] = self.rule_description
        if self.igmp_type:
            self.proposed["igmp_type"] = self.igmp_type
        self.proposed["log_flag"] = self.log_flag

    def get_existing(self):
        """ Get existing state """

        self.existing["acl_info"] = self.cur_acl_cfg["acl_info"]
        self.existing["adv_rule_info"] = self.cur_advance_rule_cfg[
            "adv_rule_info"]

    def get_end_state(self):
        """ Get end state """

        self.check_acl_args()
        self.end_state["acl_info"] = self.cur_acl_cfg["acl_info"]

        self.check_advance_rule_args()
        self.end_state["adv_rule_info"] = self.cur_advance_rule_cfg[
            "adv_rule_info"]

    def merge_acl(self):
        """ Merge acl operation """

        conf_str = CE_MERGE_ACL_HEADER % self.acl_name

        if self.acl_type:
            conf_str += "<aclType>%s</aclType>" % self.acl_type
        if self.acl_num:
            conf_str += "<aclNumber>%s</aclNumber>" % self.acl_num
        if self.acl_step:
            conf_str += "<aclStep>%s</aclStep>" % self.acl_step
        if self.acl_description:
            conf_str += "<aclDescription>%s</aclDescription>" % self.acl_description

        conf_str += CE_MERGE_ACL_TAIL

        recv_xml = self.netconf_set_config(conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Merge acl failed.')

        if self.acl_name.isdigit():
            cmd = "acl number %s" % self.acl_name
        else:
            if self.acl_type and not self.acl_num:
                cmd = "acl name %s %s" % (self.acl_name, self.acl_type.lower())
            elif self.acl_type and self.acl_num:
                cmd = "acl name %s number %s" % (self.acl_name, self.acl_num)
            elif not self.acl_type and self.acl_num:
                cmd = "acl name %s number %s" % (self.acl_name, self.acl_num)
        self.updates_cmd.append(cmd)

        if self.acl_description:
            cmd = "description %s" % self.acl_description
            self.updates_cmd.append(cmd)

        if self.acl_step:
            cmd = "step %s" % self.acl_step
            self.updates_cmd.append(cmd)

        self.changed = True

    def delete_acl(self):
        """ Delete acl operation """

        conf_str = CE_DELETE_ACL_HEADER % self.acl_name

        if self.acl_type:
            conf_str += "<aclType>%s</aclType>" % self.acl_type
        if self.acl_num:
            conf_str += "<aclNumber>%s</aclNumber>" % self.acl_num
        if self.acl_step:
            conf_str += "<aclStep>%s</aclStep>" % self.acl_step
        if self.acl_description:
            conf_str += "<aclDescription>%s</aclDescription>" % self.acl_description

        conf_str += CE_DELETE_ACL_TAIL

        recv_xml = self.netconf_set_config(conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Delete acl failed.')

        if self.acl_description:
            cmd = "undo description"
            self.updates_cmd.append(cmd)

        if self.acl_step:
            cmd = "undo step"
            self.updates_cmd.append(cmd)

        if self.acl_name.isdigit():
            cmd = "undo acl number %s" % self.acl_name
        else:
            cmd = "undo acl name %s" % self.acl_name
        self.updates_cmd.append(cmd)

        self.changed = True

    def merge_adv_rule(self):
        """ Merge advance rule operation """

        conf_str = CE_MERGE_ACL_ADVANCE_RULE_HEADER % (
            self.acl_name, self.rule_name)

        if self.rule_id:
            conf_str += "<aclRuleID>%s</aclRuleID>" % self.rule_id
        if self.rule_action:
            conf_str += "<aclAction>%s</aclAction>" % self.rule_action
        if self.protocol:
            conf_str += "<aclProtocol>%s</aclProtocol>" % self.protocol_num
        if self.source_ip:
            conf_str += "<aclSourceIp>%s</aclSourceIp>" % self.source_ip
        if self.src_wild:
            conf_str += "<aclSrcWild>%s</aclSrcWild>" % self.src_wild
        if self.src_pool_name:
            conf_str += "<aclSPoolName>%s</aclSPoolName>" % self.src_pool_name
        if self.dest_ip:
            conf_str += "<aclDestIp>%s</aclDestIp>" % self.dest_ip
        if self.dest_wild:
            conf_str += "<aclDestWild>%s</aclDestWild>" % self.dest_wild
        if self.dest_pool_name:
            conf_str += "<aclDPoolName>%s</aclDPoolName>" % self.dest_pool_name
        if self.src_port_op:
            conf_str += "<aclSrcPortOp>%s</aclSrcPortOp>" % self.src_port_op
        if self.src_port_begin:
            conf_str += "<aclSrcPortBegin>%s</aclSrcPortBegin>" % self.src_port_begin
        if self.src_port_end:
            conf_str += "<aclSrcPortEnd>%s</aclSrcPortEnd>" % self.src_port_end
        if self.src_port_pool_name:
            conf_str += "<aclSPortPoolName>%s</aclSPortPoolName>" % self.src_port_pool_name
        if self.dest_port_op:
            conf_str += "<aclDestPortOp>%s</aclDestPortOp>" % self.dest_port_op
        if self.dest_port_begin:
            conf_str += "<aclDestPortB>%s</aclDestPortB>" % self.dest_port_begin
        if self.dest_port_end:
            conf_str += "<aclDestPortE>%s</aclDestPortE>" % self.dest_port_end
        if self.dest_port_pool_name:
            conf_str += "<aclDPortPoolName>%s</aclDPortPoolName>" % self.dest_port_pool_name
        if self.frag_type:
            conf_str += "<aclFragType>%s</aclFragType>" % self.frag_type
        if self.precedence:
            conf_str += "<aclPrecedence>%s</aclPrecedence>" % self.precedence
        if self.tos:
            conf_str += "<aclTos>%s</aclTos>" % self.tos
        if self.dscp:
            conf_str += "<aclDscp>%s</aclDscp>" % self.dscp
        if self.icmp_name:
            conf_str += "<aclIcmpName>%s</aclIcmpName>" % self.icmp_name
        if self.icmp_type:
            conf_str += "<aclIcmpType>%s</aclIcmpType>" % self.icmp_type
        if self.icmp_code:
            conf_str += "<aclIcmpCode>%s</aclIcmpCode>" % self.icmp_code
        conf_str += "<aclTtlExpired>%s</aclTtlExpired>" % str(self.ttl_expired).lower()
        if self.vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % self.vrf_name
        if self.syn_flag:
            conf_str += "<aclSynFlag>%s</aclSynFlag>" % self.syn_flag
        if self.tcp_flag_mask:
            conf_str += "<aclTcpFlagMask>%s</aclTcpFlagMask>" % self.tcp_flag_mask
        if self.protocol == "tcp":
            conf_str += "<aclEstablished>%s</aclEstablished>" % str(self.established).lower()
        if self.time_range:
            conf_str += "<aclTimeName>%s</aclTimeName>" % self.time_range
        if self.rule_description:
            conf_str += "<aclRuleDescription>%s</aclRuleDescription>" % self.rule_description
        if self.igmp_type:
            conf_str += "<aclIgmpType>%s</aclIgmpType>" % self.igmp_type_num
        conf_str += "<aclLogFlag>%s</aclLogFlag>" % str(self.log_flag).lower()

        conf_str += CE_MERGE_ACL_ADVANCE_RULE_TAIL

        recv_xml = self.netconf_set_config(conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Merge acl base rule failed.')

        if self.rule_action and self.protocol:
            cmd = "rule"
            if self.rule_id:
                cmd += " %s" % self.rule_id
            cmd += " %s" % self.rule_action
            cmd += " %s" % self.protocol
            if self.dscp:
                cmd += " dscp %s" % self.dscp
            if self.tos:
                cmd += " tos %s" % self.tos
            if self.tos:
                cmd += " tos %s" % self.tos
            if self.source_ip and self.src_wild:
                cmd += " source %s %s" % (self.source_ip, self.src_wild)
            if self.src_pool_name:
                cmd += " source-pool %s" % self.src_pool_name
            if self.src_port_op:
                cmd += " source-port"
                if self.src_port_op == "lt":
                    cmd += " lt %s" % self.src_port_end
                elif self.src_port_op == "eq":
                    cmd += " eq %s" % self.src_port_begin
                elif self.src_port_op == "gt":
                    cmd += " gt %s" % self.src_port_begin
                elif self.src_port_op == "range":
                    cmd += " range %s %s" % (self.src_port_begin,
                                             self.src_port_end)
            if self.src_port_pool_name:
                cmd += " source-port-pool %s" % self.src_port_pool_name
            if self.dest_ip and self.dest_wild:
                cmd += " destination %s %s" % (self.dest_ip, self.dest_wild)
            if self.dest_pool_name:
                cmd += " destination-pool %s" % self.dest_pool_name
            if self.dest_port_op:
                cmd += " destination-port"
                if self.dest_port_op == "lt":
                    cmd += " lt %s" % self.dest_port_end
                elif self.dest_port_op == "eq":
                    cmd += " eq %s" % self.dest_port_begin
                elif self.dest_port_op == "gt":
                    cmd += " gt %s" % self.dest_port_begin
                elif self.dest_port_op == "range":
                    cmd += " range %s %s" % (self.dest_port_begin,
                                             self.dest_port_end)
            if self.dest_port_pool_name:
                cmd += " destination-port-pool %s" % self.dest_port_pool_name
            if self.frag_type == "fragment":
                cmd += " fragment-type fragment"
            if self.precedence:
                cmd += " precedence %s" % self.precedence_name[self.precedence]

            if self.protocol == "icmp":
                if self.icmp_name:
                    cmd += " icmp-type %s" % self.icmp_name
                elif self.icmp_type and self.icmp_code:
                    cmd += " icmp-type %s %s" % (self.icmp_type, self.icmp_code)
                elif self.icmp_type:
                    cmd += " icmp-type %s" % self.icmp_type

            if self.time_range:
                cmd += " time-range %s" % self.time_range
            if self.vrf_name:
                cmd += " vpn-instance %s" % self.vrf_name
            if self.ttl_expired:
                cmd += " ttl-expired"
            if self.log_flag:
                cmd += " logging"
            self.updates_cmd.append(cmd)

        if self.rule_description:
            cmd = "rule %s description %s" % (
                self.rule_id, self.rule_description)
            self.updates_cmd.append(cmd)

        self.changed = True

    def delete_adv_rule(self):
        """ Delete advance rule operation """

        conf_str = CE_DELETE_ACL_ADVANCE_RULE_HEADER % (
            self.acl_name, self.rule_name)

        if self.rule_id:
            conf_str += "<aclRuleID>%s</aclRuleID>" % self.rule_id
        if self.rule_action:
            conf_str += "<aclAction>%s</aclAction>" % self.rule_action
        if self.protocol:
            conf_str += "<aclProtocol>%s</aclProtocol>" % self.protocol_num
        if self.source_ip:
            conf_str += "<aclSourceIp>%s</aclSourceIp>" % self.source_ip
        if self.src_wild:
            conf_str += "<aclSrcWild>%s</aclSrcWild>" % self.src_wild
        if self.src_pool_name:
            conf_str += "<aclSPoolName>%s</aclSPoolName>" % self.src_pool_name
        if self.dest_ip:
            conf_str += "<aclDestIp>%s</aclDestIp>" % self.dest_ip
        if self.dest_wild:
            conf_str += "<aclDestWild>%s</aclDestWild>" % self.dest_wild
        if self.dest_pool_name:
            conf_str += "<aclDPoolName>%s</aclDPoolName>" % self.dest_pool_name
        if self.src_port_op:
            conf_str += "<aclSrcPortOp>%s</aclSrcPortOp>" % self.src_port_op
        if self.src_port_begin:
            conf_str += "<aclSrcPortBegin>%s</aclSrcPortBegin>" % self.src_port_begin
        if self.src_port_end:
            conf_str += "<aclSrcPortEnd>%s</aclSrcPortEnd>" % self.src_port_end
        if self.src_port_pool_name:
            conf_str += "<aclSPortPoolName>%s</aclSPortPoolName>" % self.src_port_pool_name
        if self.dest_port_op:
            conf_str += "<aclDestPortOp>%s</aclDestPortOp>" % self.dest_port_op
        if self.dest_port_begin:
            conf_str += "<aclDestPortB>%s</aclDestPortB>" % self.dest_port_begin
        if self.dest_port_end:
            conf_str += "<aclDestPortE>%s</aclDestPortE>" % self.dest_port_end
        if self.dest_port_pool_name:
            conf_str += "<aclDPortPoolName>%s</aclDPortPoolName>" % self.dest_port_pool_name
        if self.frag_type:
            conf_str += "<aclFragType>%s</aclFragType>" % self.frag_type
        if self.precedence:
            conf_str += "<aclPrecedence>%s</aclPrecedence>" % self.precedence
        if self.tos:
            conf_str += "<aclTos>%s</aclTos>" % self.tos
        if self.dscp:
            conf_str += "<aclDscp>%s</aclDscp>" % self.dscp
        if self.icmp_name:
            conf_str += "<aclIcmpName>%s</aclIcmpName>" % self.icmp_name
        if self.icmp_type:
            conf_str += "<aclIcmpType>%s</aclIcmpType>" % self.icmp_type
        if self.icmp_code:
            conf_str += "<aclIcmpCode>%s</aclIcmpCode>" % self.icmp_code
        conf_str += "<aclTtlExpired>%s</aclTtlExpired>" % str(self.ttl_expired).lower()
        if self.vrf_name:
            conf_str += "<vrfName>%s</vrfName>" % self.vrf_name
        if self.syn_flag:
            conf_str += "<aclSynFlag>%s</aclSynFlag>" % self.syn_flag
        if self.tcp_flag_mask:
            conf_str += "<aclTcpFlagMask>%s</aclTcpFlagMask>" % self.tcp_flag_mask
        if self.protocol == "tcp":
            conf_str += "<aclEstablished>%s</aclEstablished>" % str(self.established).lower()
        if self.time_range:
            conf_str += "<aclTimeName>%s</aclTimeName>" % self.time_range
        if self.rule_description:
            conf_str += "<aclRuleDescription>%s</aclRuleDescription>" % self.rule_description
        if self.igmp_type:
            conf_str += "<aclIgmpType>%s</aclIgmpType>" % self.igmp_type
        conf_str += "<aclLogFlag>%s</aclLogFlag>" % str(self.log_flag).lower()

        conf_str += CE_DELETE_ACL_ADVANCE_RULE_TAIL

        recv_xml = self.netconf_set_config(conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Delete acl base rule failed.')

        if self.rule_description:
            if self.acl_name.isdigit():
                cmd = "acl number %s" % self.acl_name
            else:
                cmd = "acl name %s" % self.acl_name
            self.updates_cmd.append(cmd)

            cmd = "undo rule %s description" % self.rule_id
            self.updates_cmd.append(cmd)

        if self.rule_id:
            if self.acl_name.isdigit():
                cmd = "acl number %s" % self.acl_name
            else:
                cmd = "acl name %s" % self.acl_name
            self.updates_cmd.append(cmd)

            cmd = "undo rule %s" % self.rule_id
            self.updates_cmd.append(cmd)
        elif self.rule_action and self.protocol:
            if self.acl_name.isdigit():
                cmd = "acl number %s" % self.acl_name
            else:
                cmd = "acl name %s" % self.acl_name
            self.updates_cmd.append(cmd)

            cmd = "undo rule"
            cmd += " %s" % self.rule_action
            cmd += " %s" % self.protocol
            if self.dscp:
                cmd += " dscp %s" % self.dscp
            if self.tos:
                cmd += " tos %s" % self.tos
            if self.tos:
                cmd += " tos %s" % self.tos
            if self.source_ip and self.src_mask:
                cmd += " source %s %s" % (self.source_ip, self.src_mask)
            if self.src_pool_name:
                cmd += " source-pool %s" % self.src_pool_name
            if self.src_port_op:
                cmd += " source-port"
                if self.src_port_op == "lt":
                    cmd += " lt %s" % self.src_port_end
                elif self.src_port_op == "eq":
                    cmd += " eq %s" % self.src_port_begin
                elif self.src_port_op == "gt":
                    cmd += " gt %s" % self.src_port_begin
                elif self.src_port_op == "range":
                    cmd += " range %s %s" % (self.src_port_begin,
                                             self.src_port_end)
            if self.src_port_pool_name:
                cmd += " source-port-pool %s" % self.src_port_pool_name
            if self.dest_ip and self.dest_mask:
                cmd += " destination %s %s" % (self.dest_ip, self.dest_mask)
            if self.dest_pool_name:
                cmd += " destination-pool %s" % self.dest_pool_name
            if self.dest_port_op:
                cmd += " destination-port"
                if self.dest_port_op == "lt":
                    cmd += " lt %s" % self.dest_port_end
                elif self.dest_port_op == "eq":
                    cmd += " eq %s" % self.dest_port_begin
                elif self.dest_port_op == "gt":
                    cmd += " gt %s" % self.dest_port_begin
                elif self.dest_port_op == "range":
                    cmd += " range %s %s" % (self.dest_port_begin,
                                             self.dest_port_end)
            if self.dest_port_pool_name:
                cmd += " destination-port-pool %s" % self.dest_port_pool_name
            if self.frag_type == "fragment":
                cmd += " fragment-type fragment"
            if self.precedence:
                cmd += " precedence %s" % self.precedence_name[self.precedence]
            if self.time_range:
                cmd += " time-range %s" % self.time_range
            if self.vrf_name:
                cmd += " vpn-instance %s" % self.vrf_name
            if self.ttl_expired:
                cmd += " ttl-expired"
            if self.log_flag:
                cmd += " logging"
            self.updates_cmd.append(cmd)

        self.changed = True

    def work(self):
        """ Main work function """

        self.check_acl_args()
        self.check_advance_rule_args()
        self.get_proposed()
        self.get_existing()

        if self.state == "present":
            if self.cur_acl_cfg["need_cfg"]:
                self.merge_acl()
            if self.cur_advance_rule_cfg["need_cfg"]:
                self.merge_adv_rule()

        elif self.state == "absent":
            if self.cur_advance_rule_cfg["need_cfg"]:
                self.delete_adv_rule()

        elif self.state == "delete_acl":
            if self.cur_acl_cfg["need_cfg"]:
                self.delete_acl()

        self.get_end_state()

        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        self.results['updates'] = self.updates_cmd

        self.module.exit_json(**self.results)


def main():
    """ Module main """

    argument_spec = dict(
        state=dict(choices=['present', 'absent',
                            'delete_acl'], default='present'),
        acl_name=dict(type='str', required=True),
        acl_num=dict(type='str'),
        acl_step=dict(type='str'),
        acl_description=dict(type='str'),
        rule_name=dict(type='str'),
        rule_id=dict(type='str'),
        rule_action=dict(choices=['permit', 'deny']),
        protocol=dict(choices=['ip', 'icmp', 'igmp',
                               'ipinip', 'tcp', 'udp', 'gre', 'ospf']),
        source_ip=dict(type='str'),
        src_mask=dict(type='str'),
        src_pool_name=dict(type='str'),
        dest_ip=dict(type='str'),
        dest_mask=dict(type='str'),
        dest_pool_name=dict(type='str'),
        src_port_op=dict(choices=['lt', 'eq', 'gt', 'range']),
        src_port_begin=dict(type='str'),
        src_port_end=dict(type='str'),
        src_port_pool_name=dict(type='str'),
        dest_port_op=dict(choices=['lt', 'eq', 'gt', 'range']),
        dest_port_begin=dict(type='str'),
        dest_port_end=dict(type='str'),
        dest_port_pool_name=dict(type='str'),
        frag_type=dict(choices=['fragment', 'clear_fragment']),
        precedence=dict(type='str'),
        tos=dict(type='str'),
        dscp=dict(type='str'),
        icmp_name=dict(choices=['unconfiged', 'echo', 'echo-reply', 'fragmentneed-DFset', 'host-redirect',
                                'host-tos-redirect', 'host-unreachable', 'information-reply', 'information-request',
                                'net-redirect', 'net-tos-redirect', 'net-unreachable', 'parameter-problem',
                                'port-unreachable', 'protocol-unreachable', 'reassembly-timeout', 'source-quench',
                                'source-route-failed', 'timestamp-reply', 'timestamp-request', 'ttl-exceeded',
                                'address-mask-reply', 'address-mask-request', 'custom']),
        icmp_type=dict(type='str'),
        icmp_code=dict(type='str'),
        ttl_expired=dict(required=False, default=False, type='bool'),
        vrf_name=dict(type='str'),
        syn_flag=dict(type='str'),
        tcp_flag_mask=dict(type='str'),
        established=dict(required=False, default=False, type='bool'),
        time_range=dict(type='str'),
        rule_description=dict(type='str'),
        igmp_type=dict(choices=['host-query', 'mrouter-adver', 'mrouter-solic', 'mrouter-termi', 'mtrace-resp',
                                'mtrace-route', 'v1host-report', 'v2host-report', 'v2leave-group', 'v3host-report']),
        log_flag=dict(required=False, default=False, type='bool')
    )

    argument_spec.update(ce_argument_spec)
    module = AdvanceAcl(argument_spec=argument_spec)
    module.work()


if __name__ == '__main__':
    main()
