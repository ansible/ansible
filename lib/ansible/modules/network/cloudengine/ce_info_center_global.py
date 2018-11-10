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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ce_info_center_global
version_added: "2.4"
short_description: Manages outputting logs on HUAWEI CloudEngine switches.
description:
    - This module offers the ability to be output to the log buffer, log file, console, terminal, or log host on HUAWEI CloudEngine switches.
author:
    - Li Yanfeng (@CloudEngine-Ansible)
options:
    info_center_enable:
        description:
            - Whether the info-center function is enabled. The value is of the Boolean type.
        choices: ['true','false']
    packet_priority:
        description:
            - Set the priority of the syslog packet.The value is an integer ranging from 0 to 7. The default value is 0.
    suppress_enable:
        description:
            - Whether a device is enabled to suppress duplicate statistics. The value is of the Boolean type.
        choices: [ 'false', 'true' ]
    logfile_max_num:
        description:
            - Maximum number of log files of the same type. The default value is 200.
            - The value range for log files is[3, 500], for security files is [1, 3],and for operation files is [1, 7].
    logfile_max_size:
        description:
            - Maximum size (in MB) of a log file. The default value is 32.
            - The value range for log files is [4, 8, 16, 32], for security files is [1, 4],
            - and for operation files is [1, 4].
        default: 32
        choices: ['4', '8', '16', '32']
    channel_id:
        description:
            - Number for channel. The value is an integer ranging from 0 to 9. The default value is 0.
    channel_cfg_name:
        description:
            - Channel name.The value is a string of 1 to 30 case-sensitive characters. The default value is console.
        default: console
    channel_out_direct:
        description:
            - Direction of information output.
        choices: ['console','monitor','trapbuffer','logbuffer','snmp','logfile']
    filter_feature_name:
        description:
            - Feature name of the filtered log. The value is a string of 1 to 31 case-insensitive characters.
    filter_log_name:
        description:
            - Name of the filtered log. The value is a string of 1 to 63 case-sensitive characters.
    ip_type:
        description:
            - Log server address type, IPv4 or IPv6.
        choices: ['ipv4','ipv6']
    server_ip:
        description:
            - Log server address, IPv4 or IPv6 type. The value is a string of 0 to 255 characters.
              The value can be an valid IPv4 or IPv6 address.
    server_domain:
        description:
            - Server name. The value is a string of 1 to 255 case-sensitive characters.
    is_default_vpn:
        description:
            - Use the default VPN or not.
        type: bool
        default: 'no'
    vrf_name:
        description:
            - VPN name on a log server. The value is a string of 1 to 31 case-sensitive characters.
              The default value is _public_.
    level:
        description:
            - Level of logs saved on a log server.
        choices: ['emergencies','alert','critical','error','warning','notification','informational','debugging']
    server_port:
        description:
            - Number of a port sending logs.The value is an integer ranging from 1 to 65535.
              For UDP, the default value is 514. For TCP, the default value is 601. For TSL, the default value is 6514.
    facility:
        description:
            - Log record tool.
        choices: ['local0','local1','local2','local3','local4','local5','local6','local7']
    channel_name:
        description:
            - Channel name. The value is a string of 1 to 30 case-sensitive characters.
    timestamp:
        description:
            - Log server timestamp. The value is of the enumerated type and case-sensitive.
        choices: ['UTC', 'localtime']
    transport_mode:
        description:
            - Transport mode. The value is of the enumerated type and case-sensitive.
        choices: ['tcp','udp']
    ssl_policy_name:
        description:
            - SSL policy name. The value is a string of 1 to 23 case-sensitive characters.
    source_ip:
        description:
            - Log source ip address, IPv4 or IPv6 type. The value is a string of 0 to 255.
              The value can be an valid IPv4 or IPv6 address.
    state:
        description:
            - Specify desired state of the resource.
        default: present
        choices: ['present','absent']
'''
EXAMPLES = '''
- name: info center global module test
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

  - name: Config info-center enable
    ce_info_center_global:
      info_center_enable: true
      state: present
      provider: "{{ cli }}"

  - name: Config statistic-suppress enable
    ce_info_center_global:
      suppress_enable: true
      state: present
      provider: "{{ cli }}"

  - name: Config info-center syslog packet-priority 1
    ce_info_center_global:
      packet_priority: 2
      state: present
      provider: "{{ cli }}"

  - name: Config info-center channel 1 name aaa
    ce_info_center_global:
      channel_id: 1
      channel_cfg_name: aaa
      state: present
      provider: "{{ cli }}"

  - name: Config info-center logfile size 10
    ce_info_center_global:
      logfile_max_num: 10
      state: present
      provider: "{{ cli }}"

  - name: Config info-center console channel 1
    ce_info_center_global:
      channel_out_direct: console
      channel_id: 1
      state: present
      provider: "{{ cli }}"

  - name: Config info-center filter-id bymodule-alias snmp snmp_ipunlock
    ce_info_center_global:
      filter_feature_name: SNMP
      filter_log_name: SNMP_IPLOCK
      state: present
      provider: "{{ cli }}"


  - name: Config info-center max-logfile-number 16
    ce_info_center_global:
      logfile_max_size: 16
      state: present
      provider: "{{ cli }}"

  - name: Config syslog loghost domain.
    ce_info_center_global:
      server_domain: aaa
      vrf_name: aaa
      channel_id: 1
      transport_mode: tcp
      facility: local4
      server_port: 100
      level: alert
      timestamp: UTC
      state: present
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"channel_id": "1", "facility": "local4", "is_default_vpn": True, "level": "alert", "server_domain": "aaa",
    "server_port": "100", "state": "present", "timestamp": "localtime", "transport_mode": "tcp"}
existing:
    description: k/v pairs of existing rollback
    returned: always
    type: dict
    sample:
        "server_domain_info": [
            {
                "chnlId": "1",
                "chnlName": "monitor",
                "facility": "local4",
                "isBriefFmt": "false",
                "isDefaultVpn": "false",
                "level": "alert",
                "serverDomain": "aaa",
                "serverPort": "100",
                "sourceIP": "0.0.0.0",
                "sslPolicyName": "gmc",
                "timestamp": "UTC",
                "transportMode": "tcp",
                "vrfName": "aaa"
            }
        ]
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample:
        "server_domain_info": [
            {
                "chnlId": "1",
                "chnlName": "monitor",
                "facility": "local4",
                "isBriefFmt": "false",
                "isDefaultVpn": "true",
                "level": "alert",
                "serverDomain": "aaa",
                "serverPort": "100",
                "sourceIP": "0.0.0.0",
                "sslPolicyName": null,
                "timestamp": "localtime",
                "transportMode": "tcp",
                "vrfName": "_public_"
            },
            {
                "chnlId": "1",
                "chnlName": "monitor",
                "facility": "local4",
                "isBriefFmt": "false",
                "isDefaultVpn": "false",
                "level": "alert",
                "serverDomain": "aaa",
                "serverPort": "100",
                "sourceIP": "0.0.0.0",
                "sslPolicyName": "gmc",
                "timestamp": "UTC",
                "transportMode": "tcp",
                "vrfName": "aaa"
            }
        ]
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["info-center loghost domain aaa level alert port 100 facility local4 channel 1 localtime transport tcp"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import ce_argument_spec, get_nc_config, set_nc_config, check_ip_addr


CE_NC_GET_CENTER_GLOBAL_INFO_HEADER = """
<filter type="subtree">
  <syslog xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <globalParam>
"""
CE_NC_GET_CENTER_GLOBAL_INFO_TAIL = """
    </globalParam>
  </syslog>
</filter>
"""

CE_NC_MERGE_CENTER_GLOBAL_INFO_HEADER = """
<config>
  <syslog xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <globalParam operation="merge">
"""

CE_NC_MERGE_CENTER_GLOBAL_INFO_TAIL = """
    </globalParam>
  </syslog>
</config>
"""

CE_NC_GET_LOG_FILE_INFO_HEADER = """
<filter type="subtree">
  <syslog xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <icLogFileInfos>
      <icLogFileInfo>
"""
CE_NC_GET_LOG_FILE_INFO_TAIL = """
      </icLogFileInfo>
    </icLogFileInfos>
  </syslog>
</filter>
"""

CE_NC_MERGE_LOG_FILE_INFO_HEADER = """
<config>
  <syslog xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <icLogFileInfos>
      <icLogFileInfo operation="merge">
"""

CE_NC_MERGE_LOG_FILE_INFO_TAIL = """
      </icLogFileInfo>
    </icLogFileInfos>
  </syslog>
</config>
"""


CE_NC_GET_CHANNEL_INFO = """
<filter type="subtree">
  <syslog xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <icChannels>
      <icChannel>
        <icChnlId>%s</icChnlId>
        <icChnlCfgName></icChnlCfgName>
      </icChannel>
    </icChannels>
  </syslog>
</filter>
"""

CE_NC_MERGE_CHANNEL_INFO_HEADER = """
<config>
  <syslog xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <icChannels>
      <icChannel operation="merge">
"""
CE_NC_MERGE_CHANNEL_INFO_TAIL = """
      </icChannel>
    </icChannels>
  </syslog>
</config>
"""

CE_NC_GET_CHANNEL_DIRECT_INFO = """
<filter type="subtree">
  <syslog xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <icDirChannels>
      <icDirChannel>
        <icOutDirect>%s</icOutDirect>
        <icCfgChnlId></icCfgChnlId>
      </icDirChannel>
    </icDirChannels>
  </syslog>
</filter>
"""
CE_NC_MERGE_CHANNEL_DIRECT_HEADER = """
<config>
  <syslog xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <icDirChannels>
      <icDirChannel operation="merge">
"""

CE_NC_MERGE_CHANNEL_DIRECT_TAIL = """
      </icDirChannel>
    </icDirChannels>
  </syslog>
</config>
"""

CE_NC_GET_FILTER_INFO = """
<filter type="subtree">
  <syslog xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <icFilters>
      <icFilter>
        <icFeatureName></icFeatureName>
        <icFilterLogName></icFilterLogName>
      </icFilter>
    </icFilters>
  </syslog>
</filter>
"""

CE_NC_CREATE_CHANNEL_FILTER_HEADER = """
<config>
  <syslog xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <icFilters>
      <icFilter operation="create">

"""
CE_NC_CREATE_CHANNEL_FILTER_TAIL = """
     </icFilter>
    </icFilters>
  </syslog>
</config>
"""
CE_NC_DELETE_CHANNEL_FILTER_HEADER = """
<config>
  <syslog xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <icFilters>
      <icFilter operation="delete">

"""
CE_NC_DELETE_CHANNEL_FILTER_TAIL = """
     </icFilter>
    </icFilters>
  </syslog>
</config>
"""

CE_NC_GET_SERVER_IP_INFO_HEADER = """
<filter type="subtree">
  <syslog xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <syslogServers>
      <syslogServer>
        <ipType>%s</ipType>
        <serverIp>%s</serverIp>
        <vrfName>%s</vrfName>
        <isDefaultVpn>%s</isDefaultVpn>
"""
CE_NC_GET_SERVER_IP_INFO_TAIL = """
      </syslogServer>
    </syslogServers>
  </syslog>
</filter>
"""
CE_NC_MERGE_SERVER_IP_INFO_HEADER = """
<config>
  <syslog xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <syslogServers>
      <syslogServer operation="merge">
        <ipType>%s</ipType>
        <serverIp>%s</serverIp>
        <vrfName>%s</vrfName>
        <isDefaultVpn>%s</isDefaultVpn>
"""
CE_NC_MERGE_SERVER_IP_INFO_TAIL = """
      </syslogServer>
    </syslogServers>
  </syslog>
</config>
"""
CE_NC_DELETE_SERVER_IP_INFO_HEADER = """
<config>
  <syslog xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <syslogServers>
      <syslogServer operation="delete">
        <ipType>%s</ipType>
        <serverIp>%s</serverIp>
        <vrfName>%s</vrfName>
        <isDefaultVpn>%s</isDefaultVpn>
"""
CE_NC_DELETE_SERVER_IP_INFO_TAIL = """
      </syslogServer>
    </syslogServers>
  </syslog>
</config>
"""
CE_NC_GET_SERVER_DNS_INFO_HEADER = """
<filter type="subtree">
  <syslog xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <syslogDNSs>
      <syslogDNS>
"""

CE_NC_GET_SERVER_DNS_INFO_TAIL = """
      </syslogDNS>
    </syslogDNSs>
  </syslog>
</filter>
"""

CE_NC_MERGE_SERVER_DNS_INFO_HEADER = """
<config>
  <syslog xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <syslogDNSs>
      <syslogDNS operation="merge">
        <serverDomain>%s</serverDomain>
        <vrfName>%s</vrfName>
        <isDefaultVpn>%s</isDefaultVpn>
"""
CE_NC_MERGE_SERVER_DNS_INFO_TAIL = """
      </syslogDNS>
    </syslogDNSs>
  </syslog>
</config>
"""

CE_NC_DELETE_SERVER_DNS_INFO_HEADER = """
<config>
  <syslog xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <syslogDNSs>
      <syslogDNS operation="delete">
        <serverDomain>%s</serverDomain>
        <vrfName>%s</vrfName>
        <isDefaultVpn>%s</isDefaultVpn>
"""
CE_NC_DELETE_SERVER_DNS_INFO_TAIL = """
      </syslogDNS>
    </syslogDNSs>
  </syslog>
</config>
"""


def get_out_direct_default(out_direct):
    """get default out direct"""

    outdict = {"console": "1", "monitor": "2", "trapbuffer": "3",
               "logbuffer": "4", "snmp": "5", "logfile": "6"}
    channel_id_default = outdict.get(out_direct)
    return channel_id_default


def get_channel_name_default(channel_id):
    """get default out direct"""

    channel_dict = {"0": "console", "1": "monitor", "2": "loghost", "3": "trapbuffer", "4": "logbuffer",
                    "5": "snmpagent", "6": "channel6", "7": "channel7", "8": "channel8", "9": "channel9"}
    channel_name_default = channel_dict.get(channel_id)
    return channel_name_default


class InfoCenterGlobal(object):
    """
    Manages info center global configuration.
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.info_center_enable = self.module.params['info_center_enable'] or None
        self.packet_priority = self.module.params['packet_priority'] or None
        self.suppress_enable = self.module.params['suppress_enable'] or None
        self.logfile_max_num = self.module.params['logfile_max_num'] or None
        self.logfile_max_size = self.module.params['logfile_max_size'] or None
        self.channel_id = self.module.params['channel_id'] or None
        self.channel_cfg_name = self.module.params['channel_cfg_name'] or None
        self.channel_out_direct = self.module.params['channel_out_direct'] or None
        self.filter_feature_name = self.module.params['filter_feature_name'] or None
        self.filter_log_name = self.module.params['filter_log_name'] or None
        self.ip_type = self.module.params['ip_type'] or None
        self.server_ip = self.module.params['server_ip'] or None
        self.server_domain = self.module.params['server_domain'] or None
        self.is_default_vpn = self.module.params['is_default_vpn'] or None
        self.vrf_name = self.module.params['vrf_name'] or None
        self.level = self.module.params['level'] or None
        self.server_port = self.module.params['server_port'] or None
        self.facility = self.module.params['facility'] or None
        self.channel_name = self.module.params['channel_name'] or None
        self.timestamp = self.module.params['timestamp'] or None
        self.transport_mode = self.module.params['transport_mode'] or None
        self.ssl_policy_name = self.module.params['ssl_policy_name'] or None
        self.source_ip = self.module.params['source_ip'] or None
        self.state = self.module.params['state'] or None

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.existing = dict()
        self.proposed = dict()
        self.end_state = dict()

        # syslog info
        self.cur_global_info = None
        self.cur_logfile_info = None
        self.channel_info = None
        self.channel_direct_info = None
        self.filter_info = None
        self.server_ip_info = None
        self.server_domain_info = None

    def init_module(self):
        """ init module """

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def check_response(self, con_obj, xml_name):
        """Check if response message is already succeed."""

        xml_str = con_obj.xml
        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_channel_dict(self):
        """ get channel attributes dict."""

        channel_info = dict()
        # get channel info
        conf_str = CE_NC_GET_CHANNEL_INFO % self.channel_id
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return channel_info
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
        root = ElementTree.fromstring(xml_str)
        channel_info["channelInfos"] = list()
        channels = root.findall("data/syslog/icChannels/icChannel")
        if channels:
            for channel in channels:
                channel_dict = dict()
                for ele in channel:
                    if ele.tag in ["icChnlId", "icChnlCfgName"]:
                        channel_dict[ele.tag] = ele.text
                channel_info["channelInfos"].append(channel_dict)
        return channel_info

    def is_exist_channel_id_name(self, channel_id, channel_name):
        """if channel id exist"""

        if not self.channel_info:
            return False

        for id2name in self.channel_info["channelInfos"]:
            if id2name["icChnlId"] == channel_id and id2name["icChnlCfgName"] == channel_name:
                return True
        return False

    def config_merge_syslog_channel(self, channel_id, channel_name):
        """config channel id"""

        if not self.is_exist_channel_id_name(channel_id, channel_name):
            conf_str = CE_NC_MERGE_CHANNEL_INFO_HEADER
            if channel_id:
                conf_str += "<icChnlId>%s</icChnlId>" % channel_id
            if channel_name:
                conf_str += "<icChnlCfgName>%s</icChnlCfgName>" % channel_name

            conf_str += CE_NC_MERGE_CHANNEL_INFO_TAIL
            recv_xml = set_nc_config(self.module, conf_str)
            if "<ok/>" not in recv_xml:
                self.module.fail_json(
                    msg='Error: Merge syslog channel id failed.')

            self.updates_cmd.append(
                "info-center channel %s name %s" % (channel_id, channel_name))
            self.changed = True

    def delete_merge_syslog_channel(self, channel_id, channel_name):
        """delete channel id"""

        change_flag = False

        if channel_name:
            for id2name in self.channel_info["channelInfos"]:
                channel_default_name = get_channel_name_default(
                    id2name["icChnlId"])
                if id2name["icChnlId"] == channel_id and id2name["icChnlCfgName"] == channel_name:
                    channel_name = channel_default_name
                    change_flag = True

        if not channel_name:
            for id2name in self.channel_info["channelInfos"]:
                channel_default_name = get_channel_name_default(
                    id2name["icChnlId"])
                if id2name["icChnlId"] == channel_id and id2name["icChnlCfgName"] != channel_default_name:
                    channel_name = channel_default_name
                    change_flag = True
        if change_flag:
            conf_str = CE_NC_MERGE_CHANNEL_INFO_HEADER
            if channel_id:
                conf_str += "<icChnlId>%s</icChnlId>" % channel_id
            if channel_name:
                conf_str += "<icChnlCfgName>%s</icChnlCfgName>" % channel_name

            conf_str += CE_NC_MERGE_CHANNEL_INFO_TAIL
            recv_xml = set_nc_config(self.module, conf_str)
            if "<ok/>" not in recv_xml:
                self.module.fail_json(
                    msg='Error: Merge syslog channel id failed.')

            self.updates_cmd.append("undo info-center channel %s" % channel_id)
            self.changed = True

    def get_channel_direct_dict(self):
        """ get channel direct attributes dict."""

        channel_direct_info = dict()
        # get channel direct info
        conf_str = CE_NC_GET_CHANNEL_DIRECT_INFO % self.channel_out_direct
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return channel_direct_info
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
        root = ElementTree.fromstring(xml_str)
        channel_direct_info["channelDirectInfos"] = list()
        dir_channels = root.findall("data/syslog/icDirChannels/icDirChannel")
        if dir_channels:
            for ic_dir_channel in dir_channels:
                channel_direct_dict = dict()
                for ele in ic_dir_channel:
                    if ele.tag in ["icOutDirect", "icCfgChnlId"]:
                        channel_direct_dict[ele.tag] = ele.text
                channel_direct_info["channelDirectInfos"].append(
                    channel_direct_dict)
        return channel_direct_info

    def is_exist_out_direct(self, out_direct, channel_id):
        """if channel out direct exist"""

        if not self.channel_direct_info:
            return False

        for id2name in self.channel_direct_info["channelDirectInfos"]:
            if id2name["icOutDirect"] == out_direct and id2name["icCfgChnlId"] == channel_id:
                return True
        return False

    def config_merge_out_direct(self, out_direct, channel_id):
        """config out direct"""

        if not self.is_exist_out_direct(out_direct, channel_id):
            conf_str = CE_NC_MERGE_CHANNEL_DIRECT_HEADER
            if out_direct:
                conf_str += "<icOutDirect>%s</icOutDirect>" % out_direct
            if channel_id:
                conf_str += "<icCfgChnlId>%s</icCfgChnlId>" % channel_id

            conf_str += CE_NC_MERGE_CHANNEL_DIRECT_TAIL
            recv_xml = set_nc_config(self.module, conf_str)
            if "<ok/>" not in recv_xml:
                self.module.fail_json(
                    msg='Error: Merge syslog channel out direct failed.')

            self.updates_cmd.append(
                "info-center %s channel %s" % (out_direct, channel_id))
            self.changed = True

    def delete_merge_out_direct(self, out_direct, channel_id):
        """delete out direct"""

        change_flag = False
        channel_id_default = get_out_direct_default(out_direct)
        if channel_id:
            for id2name in self.channel_direct_info["channelDirectInfos"]:
                if id2name["icOutDirect"] == out_direct and id2name["icCfgChnlId"] == channel_id:
                    if channel_id != channel_id_default:
                        channel_id = channel_id_default
                        change_flag = True

        if not channel_id:
            for id2name in self.channel_direct_info["channelDirectInfos"]:
                if id2name["icOutDirect"] == out_direct and id2name["icCfgChnlId"] != channel_id_default:
                    channel_id = channel_id_default
                    change_flag = True

        if change_flag:
            conf_str = CE_NC_MERGE_CHANNEL_DIRECT_HEADER
            if out_direct:
                conf_str += "<icOutDirect>%s</icOutDirect>" % out_direct
            if channel_id:
                conf_str += "<icCfgChnlId>%s</icCfgChnlId>" % channel_id

            conf_str += CE_NC_MERGE_CHANNEL_DIRECT_TAIL
            recv_xml = set_nc_config(self.module, conf_str)
            if "<ok/>" not in recv_xml:
                self.module.fail_json(
                    msg='Error: Merge syslog channel out direct failed.')

            self.updates_cmd.append("undo info-center logfile channel")
            self.changed = True

    def get_filter_dict(self):
        """ get syslog filter attributes dict."""

        filter_info = dict()
        # get filter info
        conf_str = CE_NC_GET_FILTER_INFO
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return filter_info
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
        root = ElementTree.fromstring(xml_str)
        filter_info["filterInfos"] = list()
        ic_filters = root.findall("data/syslog/icFilters/icFilter")
        if ic_filters:
            for ic_filter in ic_filters:
                filter_dict = dict()
                for ele in ic_filter:
                    if ele.tag in ["icFeatureName", "icFilterLogName"]:
                        filter_dict[ele.tag] = ele.text
                filter_info["filterInfos"].append(filter_dict)
        return filter_info

    def is_exist_filter(self, filter_feature_name, filter_log_name):
        """if filter info exist"""

        if not self.filter_info:
            return False
        for id2name in self.filter_info["filterInfos"]:
            if id2name["icFeatureName"] == filter_feature_name and id2name["icFilterLogName"] == filter_log_name:
                return True
        return False

    def config_merge_filter(self, filter_feature_name, filter_log_name):
        """config filter"""

        if not self.is_exist_filter(filter_feature_name, filter_log_name):
            conf_str = CE_NC_CREATE_CHANNEL_FILTER_HEADER
            conf_str += "<icFilterFlag>true</icFilterFlag>"
            if filter_feature_name:
                conf_str += "<icFeatureName>%s</icFeatureName>" % filter_feature_name
            if filter_log_name:
                conf_str += "<icFilterLogName>%s</icFilterLogName>" % filter_log_name

            conf_str += CE_NC_CREATE_CHANNEL_FILTER_TAIL
            recv_xml = set_nc_config(self.module, conf_str)
            if "<ok/>" not in recv_xml:
                self.module.fail_json(msg='Error: Merge syslog filter failed.')

            self.updates_cmd.append("info-center filter-id bymodule-alias %s %s"
                                    % (filter_feature_name, filter_log_name))
            self.changed = True

    def delete_merge_filter(self, filter_feature_name, filter_log_name):
        """delete filter"""

        change_flag = False
        if self.is_exist_filter(filter_feature_name, filter_log_name):
            for id2name in self.filter_info["filterInfos"]:
                if id2name["icFeatureName"] == filter_feature_name and id2name["icFilterLogName"] == filter_log_name:
                    change_flag = True
        if change_flag:
            conf_str = CE_NC_DELETE_CHANNEL_FILTER_HEADER
            conf_str += "<icFilterFlag>true</icFilterFlag>"
            if filter_feature_name:
                conf_str += "<icFeatureName>%s</icFeatureName>" % filter_feature_name
            if filter_log_name:
                conf_str += "<icFilterLogName>%s</icFilterLogName>" % filter_log_name

            conf_str += CE_NC_DELETE_CHANNEL_FILTER_TAIL
            recv_xml = set_nc_config(self.module, conf_str)
            if "<ok/>" not in recv_xml:
                self.module.fail_json(
                    msg='Error: Merge syslog channel out direct failed.')
            self.updates_cmd.append("undo info-center filter-id bymodule-alias %s %s"
                                    % (filter_feature_name, filter_log_name))
            self.changed = True

    def get_server_ip_dict(self):
        """ get server ip attributes dict."""

        server_ip_info = dict()
        # get server ip info
        is_default_vpn = "false"
        if not self.is_default_vpn:
            self.is_default_vpn = False
        if self.is_default_vpn is True:
            is_default_vpn = "true"
        if not self.vrf_name:
            self.vrf_name = "_public_"
        conf_str = CE_NC_GET_SERVER_IP_INFO_HEADER % (
            self.ip_type, self.server_ip, self.vrf_name, is_default_vpn)
        conf_str += CE_NC_GET_SERVER_IP_INFO_TAIL
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return server_ip_info
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
        root = ElementTree.fromstring(xml_str)
        server_ip_info["serverIpInfos"] = list()
        syslog_servers = root.findall("data/syslog/syslogServers/syslogServer")
        if syslog_servers:
            for syslog_server in syslog_servers:
                server_dict = dict()
                for ele in syslog_server:
                    if ele.tag in ["ipType", "serverIp", "vrfName", "level", "serverPort", "facility", "chnlId",
                                   "chnlName", "timestamp", "transportMode", "sslPolicyName", "isDefaultVpn",
                                   "sourceIP", "isBriefFmt"]:
                        server_dict[ele.tag] = ele.text
                server_ip_info["serverIpInfos"].append(server_dict)
        return server_ip_info

    def config_merge_loghost(self):
        """config loghost ip or dns"""

        conf_str = ""
        is_default_vpn = "false"
        if self.is_default_vpn is True:
            is_default_vpn = "true"
        if self.ip_type:
            conf_str = CE_NC_MERGE_SERVER_IP_INFO_HEADER % (self.ip_type, self.server_ip, self.vrf_name,
                                                            is_default_vpn)
        elif self.server_domain:
            conf_str = CE_NC_MERGE_SERVER_DNS_INFO_HEADER % (
                self.server_domain, self.vrf_name, is_default_vpn)
        if self.level:
            conf_str += "<level>%s</level>" % self.level
        if self.server_port:
            conf_str += "<serverPort>%s</serverPort>" % self.server_port
        if self.facility:
            conf_str += "<facility>%s</facility>" % self.facility
        if self.channel_id:
            conf_str += "<chnlId>%s</chnlId>" % self.channel_id
        if self.channel_name:
            conf_str += "<chnlName>%s</chnlName>" % self.channel_name
        if self.timestamp:
            conf_str += "<timestamp>%s</timestamp>" % self.timestamp
        if self.transport_mode:
            conf_str += "<transportMode>%s</transportMode>" % self.transport_mode
        if self.ssl_policy_name:
            conf_str += "<sslPolicyName>%s</sslPolicyName>" % self.ssl_policy_name
        if self.source_ip:
            conf_str += "<sourceIP>%s</sourceIP>" % self.source_ip
        if self.ip_type:
            conf_str += CE_NC_MERGE_SERVER_IP_INFO_TAIL
        elif self.server_domain:
            conf_str += CE_NC_MERGE_SERVER_DNS_INFO_TAIL
        recv_xml = set_nc_config(self.module, conf_str)
        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Merge server loghost failed.')

        cmd = "info-center loghost"
        if self.ip_type == "ipv4" and self.server_ip:
            cmd += " %s" % self.server_ip
        if self.ip_type == "ipv6" and self.server_ip:
            cmd += " ipv6 %s" % self.server_ip
        if self.server_domain:
            cmd += " domain %s" % self.server_domain
        if self.vrf_name:
            if self.vrf_name != "_public_":
                cmd += " vpn-instance %s" % self.vrf_name
        if self.level:
            cmd += " level %s" % self.level
        if self.server_port:
            cmd += " port %s" % self.server_port
        if self.facility:
            cmd += " facility %s" % self.facility
        if self.channel_id:
            cmd += " channel %s" % self.channel_id
        if self.channel_name:
            cmd += " channel %s" % self.channel_name
        if self.timestamp:
            cmd += " %s" % self.timestamp
        if self.transport_mode:
            cmd += " transport %s" % self.transport_mode
        if self.source_ip:
            cmd += " source-ip %s" % self.source_ip
        if self.ssl_policy_name:
            cmd += " ssl-policy %s" % self.ssl_policy_name
        self.updates_cmd.append(cmd)
        self.changed = True

    def delete_merge_loghost(self):
        """delete loghost ip or dns"""

        conf_str = ""
        is_default_vpn = "false"
        if self.is_default_vpn is True:
            is_default_vpn = "true"
        if self.ip_type:
            conf_str = CE_NC_DELETE_SERVER_IP_INFO_HEADER % (self.ip_type, self.server_ip, self.vrf_name,
                                                             is_default_vpn)
        elif self.server_domain:
            conf_str = CE_NC_DELETE_SERVER_DNS_INFO_HEADER % (
                self.server_domain, self.vrf_name, is_default_vpn)
        if self.level:
            conf_str += "<level>%s</level>" % self.level
        if self.server_port:
            conf_str += "<serverPort>%s</serverPort>" % self.server_port
        if self.facility:
            conf_str += "<facility>%s</facility>" % self.facility
        if self.channel_id:
            conf_str += "<chnlId>%s</chnlId>" % self.channel_id
        if self.channel_name:
            conf_str += "<chnlName>%s</chnlName>" % self.channel_name
        if self.timestamp:
            conf_str += "<timestamp>%s</timestamp>" % self.timestamp
        if self.transport_mode:
            conf_str += "<transportMode>%s</transportMode>" % self.transport_mode
        if self.ssl_policy_name:
            conf_str += "<sslPolicyName>%s</sslPolicyName>" % self.ssl_policy_name
        if self.source_ip:
            conf_str += "<sourceIP>%s</sourceIP>" % self.source_ip
        if self.ip_type:
            conf_str += CE_NC_DELETE_SERVER_IP_INFO_TAIL
        elif self.server_domain:
            conf_str += CE_NC_DELETE_SERVER_DNS_INFO_TAIL
        recv_xml = set_nc_config(self.module, conf_str)
        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Merge server loghost failed.')

        cmd = "undo info-center loghost"
        if self.ip_type == "ipv4" and self.server_ip:
            cmd += " %s" % self.server_ip
        if self.ip_type == "ipv6" and self.server_ip:
            cmd += " ipv6 %s" % self.server_ip
        if self.server_domain:
            cmd += " domain %s" % self.server_domain
        if self.vrf_name:
            if self.vrf_name != "_public_":
                cmd += " vpn-instance %s" % self.vrf_name
        if self.level:
            cmd += " level %s" % self.level
        if self.server_port:
            cmd += " port %s" % self.server_port
        if self.facility:
            cmd += " facility %s" % self.facility
        if self.channel_id:
            cmd += " channel %s" % self.channel_id
        if self.channel_name:
            cmd += " channel %s" % self.channel_name
        if self.timestamp:
            cmd += " %s" % self.timestamp
        if self.transport_mode:
            cmd += " transport %s" % self.transport_mode
        if self.source_ip:
            cmd += " source-ip %s" % self.source_ip
        if self.ssl_policy_name:
            cmd += " ssl-policy %s" % self.ssl_policy_name
        self.updates_cmd.append(cmd)
        self.changed = True

    def get_server_domain_dict(self):
        """ get server domain attributes dict"""

        server_domain_info = dict()
        # get server domain info
        if not self.is_default_vpn:
            self.is_default_vpn = False
        if not self.vrf_name:
            self.vrf_name = "_public_"
        conf_str = CE_NC_GET_SERVER_DNS_INFO_HEADER
        conf_str += CE_NC_GET_SERVER_DNS_INFO_TAIL
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return server_domain_info
        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
        root = ElementTree.fromstring(xml_str)
        server_domain_info["serverAddressInfos"] = list()
        syslog_dnss = root.findall("data/syslog/syslogDNSs/syslogDNS")
        if syslog_dnss:
            for syslog_dns in syslog_dnss:
                dns_dict = dict()
                for ele in syslog_dns:
                    if ele.tag in ["serverDomain", "vrfName", "level", "serverPort", "facility", "chnlId",
                                   "chnlName", "timestamp", "transportMode", "sslPolicyName", "isDefaultVpn",
                                   "sourceIP", "isBriefFmt"]:
                        dns_dict[ele.tag] = ele.text
                server_domain_info["serverAddressInfos"].append(dns_dict)

        return server_domain_info

    def check_need_loghost_cfg(self):
        """ check need cfg"""

        need_cfg = False
        find_flag = False
        if self.ip_type and self.server_ip:
            if self.server_ip_info:
                for tmp in self.server_ip_info["serverIpInfos"]:
                    find_flag = True
                    if self.ip_type and tmp.get("ipType") != self.ip_type:
                        find_flag = False
                    if self.server_ip and tmp.get("serverIp") != self.server_ip:
                        find_flag = False
                    if self.vrf_name and tmp.get("vrfName") != self.vrf_name:
                        find_flag = False
                    if self.level and tmp.get("level") != self.level:
                        find_flag = False
                    if self.server_port and tmp.get("serverPort") != self.server_port:
                        find_flag = False
                    if self.facility and tmp.get("facility") != self.facility:
                        find_flag = False
                    if self.channel_id and tmp.get("chnlId") != self.channel_id:
                        find_flag = False
                    if self.channel_name and tmp.get("chnlName") != self.channel_name:
                        find_flag = False
                    if self.timestamp and tmp.get("timestamp") != self.timestamp:
                        find_flag = False
                    if self.transport_mode and tmp.get("transportMode") != self.transport_mode:
                        find_flag = False
                    if self.ssl_policy_name and tmp.get("sslPolicyName") != self.ssl_policy_name:
                        find_flag = False
                    if self.source_ip and tmp.get("sourceIP") != self.source_ip:
                        find_flag = False
                    if find_flag:
                        break
        elif self.server_domain:
            if self.server_domain_info:
                for tmp in self.server_domain_info["serverAddressInfos"]:
                    find_flag = True
                    if self.server_domain and tmp.get("serverDomain") != self.server_domain:
                        find_flag = False
                    if self.vrf_name and tmp.get("vrfName") != self.vrf_name:
                        find_flag = False
                    if self.level and tmp.get("level") != self.level:
                        find_flag = False
                    if self.server_port and tmp.get("serverPort") != self.server_port:
                        find_flag = False
                    if self.facility and tmp.get("facility") != self.facility:
                        find_flag = False
                    if self.channel_id and tmp.get("chnlId") != self.channel_id:
                        find_flag = False
                    if self.channel_name and tmp.get("chnlName") != self.channel_name:
                        find_flag = False
                    if self.timestamp and tmp.get("timestamp") != self.timestamp:
                        find_flag = False
                    if self.transport_mode and tmp.get("transportMode") != self.transport_mode:
                        find_flag = False
                    if self.ssl_policy_name and tmp.get("sslPolicyName") != self.ssl_policy_name:
                        find_flag = False
                    if self.source_ip and tmp.get("sourceIP") != self.source_ip:
                        find_flag = False
                    if find_flag:
                        break
        else:
            find_flag = False

        if self.state == "present":
            need_cfg = bool(not find_flag)
        elif self.state == "absent":
            need_cfg = bool(find_flag)
        return need_cfg

    def get_syslog_global(self):
        """get syslog global attributes"""

        cur_global_info = dict()
        conf_str = CE_NC_GET_CENTER_GLOBAL_INFO_HEADER
        if self.info_center_enable:
            conf_str += "<icEnable></icEnable>"
        if self.packet_priority:
            conf_str += "<packetPriority></packetPriority>"
        if self.suppress_enable:
            conf_str += "<suppressEnable></suppressEnable>"
        conf_str += CE_NC_GET_CENTER_GLOBAL_INFO_TAIL
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return cur_global_info
        else:
            xml_str = xml_str.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

            root = ElementTree.fromstring(xml_str)
            global_info = root.findall(
                "data/syslog/globalParam")

            if global_info:
                for tmp in global_info:
                    for site in tmp:
                        if site.tag in ["icEnable", "packetPriority", "suppressEnable"]:
                            cur_global_info[site.tag] = site.text
            return cur_global_info

    def merge_syslog_global(self):
        """config global"""

        conf_str = CE_NC_MERGE_CENTER_GLOBAL_INFO_HEADER
        if self.info_center_enable:
            conf_str += "<icEnable>%s</icEnable>" % self.info_center_enable
        if self.packet_priority:
            if self.state == "present":
                packet_priority = self.packet_priority
            else:
                packet_priority = 0
            conf_str += "<packetPriority>%s</packetPriority>" % packet_priority
        if self.suppress_enable:
            conf_str += "<suppressEnable>%s</suppressEnable>" % self.suppress_enable

        conf_str += CE_NC_MERGE_CENTER_GLOBAL_INFO_TAIL

        if self.info_center_enable == "true" and self.cur_global_info["icEnable"] != self.info_center_enable:
            cmd = "info-center enable"
            self.updates_cmd.append(cmd)
            self.changed = True
        if self.suppress_enable == "true" and self.cur_global_info["suppressEnable"] != self.suppress_enable:
            cmd = "info-center statistic-suppress enable"
            self.updates_cmd.append(cmd)
            self.changed = True
        if self.info_center_enable == "false" and self.cur_global_info["icEnable"] != self.info_center_enable:
            cmd = "undo info-center enable"
            self.updates_cmd.append(cmd)
            self.changed = True
        if self.suppress_enable == "false" and self.cur_global_info["suppressEnable"] != self.suppress_enable:
            cmd = "undo info-center statistic-suppress enable"
            self.updates_cmd.append(cmd)
            self.changed = True

        if self.state == "present":
            if self.packet_priority:
                if self.packet_priority != "0" and self.cur_global_info["packetPriority"] != self.packet_priority:
                    cmd = "info-center syslog packet-priority %s" % self.packet_priority
                    self.updates_cmd.append(cmd)
                    self.changed = True
        if self.state == "absent":
            if self.packet_priority:
                if self.packet_priority != "0" and self.cur_global_info["packetPriority"] == self.packet_priority:
                    cmd = "undo info-center syslog packet-priority %s" % self.packet_priority
                    self.updates_cmd.append(cmd)
                    self.changed = True
        if self.changed:
            recv_xml = set_nc_config(self.module, conf_str)
            if "<ok/>" not in recv_xml:
                self.module.fail_json(msg='Error: Merge syslog global failed.')

    def get_syslog_logfile(self):
        """get syslog logfile"""

        cur_logfile_info = dict()
        conf_str = CE_NC_GET_LOG_FILE_INFO_HEADER
        conf_str += "<logFileType>log</logFileType>"
        if self.logfile_max_num:
            conf_str += "<maxFileNum></maxFileNum>"
        if self.logfile_max_size:
            conf_str += "<maxFileSize></maxFileSize>"
        conf_str += CE_NC_GET_LOG_FILE_INFO_TAIL
        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return cur_logfile_info
        else:
            xml_str = xml_str.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

            root = ElementTree.fromstring(xml_str)
            logfile_info = root.findall(
                "data/syslog/icLogFileInfos/icLogFileInfo")
            if logfile_info:
                for tmp in logfile_info:
                    for site in tmp:
                        if site.tag in ["maxFileNum", "maxFileSize"]:
                            cur_logfile_info[site.tag] = site.text
            return cur_logfile_info

    def merge_syslog_logfile(self):
        """config logfile"""

        logfile_max_num = "200"
        conf_str = CE_NC_MERGE_LOG_FILE_INFO_HEADER
        if self.logfile_max_num:
            if self.state == "present":
                if self.cur_logfile_info["maxFileNum"] != self.logfile_max_num:
                    logfile_max_num = self.logfile_max_num
            else:
                if self.logfile_max_num != "200" and self.cur_logfile_info["maxFileNum"] == self.logfile_max_num:
                    logfile_max_num = "200"
            conf_str += "<maxFileNum>%s</maxFileNum>" % logfile_max_num

        if self.logfile_max_size:
            logfile_max_size = "32"
            if self.state == "present":
                if self.cur_logfile_info["maxFileSize"] != self.logfile_max_size:
                    logfile_max_size = self.logfile_max_size
            else:
                if self.logfile_max_size != "32" and self.cur_logfile_info["maxFileSize"] == self.logfile_max_size:
                    logfile_max_size = "32"
            conf_str += "<maxFileSize>%s</maxFileSize>" % logfile_max_size

        conf_str += "<logFileType>log</logFileType>"
        conf_str += CE_NC_MERGE_LOG_FILE_INFO_TAIL

        if self.state == "present":
            if self.logfile_max_num:
                if self.cur_logfile_info["maxFileNum"] != self.logfile_max_num:
                    cmd = "info-center max-logfile-number %s" % self.logfile_max_num
                    self.updates_cmd.append(cmd)
                    self.changed = True
            if self.logfile_max_size:
                if self.cur_logfile_info["maxFileSize"] != self.logfile_max_size:
                    cmd = "info-center logfile size %s" % self.logfile_max_size
                    self.updates_cmd.append(cmd)
                    self.changed = True
        if self.state == "absent":
            if self.logfile_max_num and self.logfile_max_num != "200":
                if self.cur_logfile_info["maxFileNum"] == self.logfile_max_num:
                    cmd = "undo info-center max-logfile-number"
                    self.updates_cmd.append(cmd)
                    self.changed = True
            if self.logfile_max_size and self.logfile_max_size != "32":
                if self.cur_logfile_info["maxFileSize"] == self.logfile_max_size:
                    cmd = "undo info-center logfile size"
                    self.updates_cmd.append(cmd)
                    self.changed = True

        if self.changed:
            recv_xml = set_nc_config(self.module, conf_str)
            if "<ok/>" not in recv_xml:
                self.module.fail_json(
                    msg='Error: Merge syslog logfile failed.')

    def check_params(self):
        """Check all input params"""

        # packet_priority check
        if self.packet_priority:
            if not self.packet_priority.isdigit():
                self.module.fail_json(
                    msg='Error: The parameter of packet priority is invalid.')
            if int(self.packet_priority) > 7 or int(self.packet_priority) < 0:
                self.module.fail_json(
                    msg='Error: The packet priority must be an integer between 0 and 7.')

        # logfile_max_num check
        if self.logfile_max_num:
            if not self.logfile_max_num.isdigit():
                self.module.fail_json(
                    msg='Error: The parameter of logfile_max_num is invalid.')
            if int(self.logfile_max_num) > 500 or int(self.logfile_max_num) < 3:
                self.module.fail_json(
                    msg='Error: The logfile_max_num must be an integer between 3 and 500.')

        # channel_id check
        if self.channel_id:
            if not self.channel_id.isdigit():
                self.module.fail_json(
                    msg='Error: The parameter of channel_id is invalid.')
            if int(self.channel_id) > 9 or int(self.channel_id) < 0:
                self.module.fail_json(
                    msg='Error: The channel_id must be an integer between 0 and 9.')

        # channel_cfg_name check
        if self.channel_cfg_name:
            if len(self.channel_cfg_name) > 30 \
                    or len(self.channel_cfg_name.replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: channel_cfg_name is not in the range from 1 to 30.')

        # filter_feature_name check
        if self.filter_feature_name:
            if len(self.filter_feature_name) > 31 \
                    or len(self.filter_feature_name.replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: filter_feature_name is not in the range from 1 to 31.')

        # filter_log_name check
        if self.filter_log_name:
            if len(self.filter_log_name) > 63 \
                    or len(self.filter_log_name.replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: filter_log_name is not in the range from 1 to 63.')

        # server_ip check
        if self.server_ip:
            if not check_ip_addr(self.server_ip):
                self.module.fail_json(
                    msg='Error: The %s is not a valid ip address' % self.server_ip)
        # source_ip check
        if self.source_ip:
            if not check_ip_addr(self.source_ip):
                self.module.fail_json(
                    msg='Error: The %s is not a valid ip address' % self.source_ip)

        # server_domain check
        if self.server_domain:
            if len(self.server_domain) > 255 \
                    or len(self.server_domain.replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: server_domain is not in the range from 1 to 255.')

        # vrf_name check
        if self.vrf_name:
            if len(self.vrf_name) > 31 \
                    or len(self.vrf_name.replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: vrf_name is not in the range from 1 to 31.')

        # server_port check
        if self.server_port:
            if not self.server_port.isdigit():
                self.module.fail_json(
                    msg='Error: The parameter of server_port is invalid.')
            if int(self.server_port) > 65535 or int(self.server_port) < 1:
                self.module.fail_json(
                    msg='Error: The server_port must be an integer between 1 and 65535.')

        # channel_name check
        if self.channel_name:
            if len(self.channel_name) > 31 \
                    or len(self.channel_name.replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: channel_name is not in the range from 1 to 30.')

        # ssl_policy_name check
        if self.ssl_policy_name:
            if len(self.ssl_policy_name) > 23 \
                    or len(self.ssl_policy_name.replace(' ', '')) < 1:
                self.module.fail_json(
                    msg='Error: ssl_policy_name is not in the range from 1 to 23.')

    def get_proposed(self):
        """get proposed info"""

        if self.info_center_enable:
            self.proposed["info_center_enable"] = self.info_center_enable
        if self.packet_priority:
            self.proposed["packet_priority"] = self.packet_priority
        if self.suppress_enable:
            self.proposed["suppress_enable"] = self.suppress_enable
        if self.logfile_max_num:
            self.proposed["logfile_max_num"] = self.logfile_max_num
        if self.logfile_max_size:
            self.proposed["logfile_max_size"] = self.logfile_max_size
        if self.channel_id:
            self.proposed["channel_id"] = self.channel_id
        if self.channel_cfg_name:
            self.proposed["channel_cfg_name"] = self.channel_cfg_name
        if self.channel_out_direct:
            self.proposed["channel_out_direct"] = self.channel_out_direct
        if self.filter_feature_name:
            self.proposed["filter_feature_name"] = self.filter_feature_name
        if self.filter_log_name:
            self.proposed["filter_log_name"] = self.filter_log_name
        if self.ip_type:
            self.proposed["ip_type"] = self.ip_type
        if self.server_ip:
            self.proposed["server_ip"] = self.server_ip
        if self.server_domain:
            self.proposed["server_domain"] = self.server_domain
        if self.vrf_name:
            self.proposed["vrf_name"] = self.vrf_name
        if self.level:
            self.proposed["level"] = self.level
        if self.server_port:
            self.proposed["server_port"] = self.server_port
        if self.facility:
            self.proposed["facility"] = self.facility
        if self.channel_name:
            self.proposed["channel_name"] = self.channel_name
        if self.timestamp:
            self.proposed["timestamp"] = self.timestamp
        if self.ssl_policy_name:
            self.proposed["ssl_policy_name"] = self.ssl_policy_name
        if self.transport_mode:
            self.proposed["transport_mode"] = self.transport_mode
        if self.is_default_vpn:
            self.proposed["is_default_vpn"] = self.is_default_vpn
        if self.source_ip:
            self.proposed["source_ip"] = self.source_ip
        if self.state:
            self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""

        if self.info_center_enable:
            self.existing["info_center_enable"] = self.cur_global_info[
                "icEnable"]
        if self.packet_priority:
            self.existing["packet_priority"] = self.cur_global_info[
                "packetPriority"]
        if self.suppress_enable:
            self.existing["suppress_enable"] = self.cur_global_info[
                "suppressEnable"]
        if self.logfile_max_num:
            self.existing["logfile_max_num"] = self.cur_logfile_info[
                "maxFileNum"]
        if self.logfile_max_size:
            self.existing["logfile_max_size"] = self.cur_logfile_info[
                "maxFileSize"]

        if self.channel_id and self.channel_cfg_name:
            if self.channel_info:
                self.existing["channel_id_info"] = self.channel_info[
                    "channelInfos"]
        if self.channel_out_direct and self.channel_id:
            if self.channel_direct_info:
                self.existing["channel_out_direct_info"] = self.channel_direct_info[
                    "channelDirectInfos"]
        if self.filter_feature_name and self.filter_log_name:
            if self.filter_info:
                self.existing["filter_id_info"] = self.filter_info[
                    "filterInfos"]
        if self.ip_type:
            if self.server_ip_info:
                self.existing["server_ip_info"] = self.server_ip_info[
                    "serverIpInfos"]

        if self.server_domain:
            if self.server_domain_info:
                self.existing["server_domain_info"] = self.server_domain_info[
                    "serverAddressInfos"]

    def get_end_state(self):
        """get end state info"""

        if self.info_center_enable or self.packet_priority or self.suppress_enable:
            self.cur_global_info = self.get_syslog_global()
        if self.logfile_max_num or self.logfile_max_size:
            self.cur_logfile_info = self.get_syslog_logfile()
        if self.channel_id and self.channel_cfg_name:
            self.channel_info = self.get_channel_dict()
        if self.channel_out_direct and self.channel_id:
            self.channel_direct_info = self.get_channel_direct_dict()
        if self.filter_feature_name and self.filter_log_name:
            self.filter_info = self.get_filter_dict()
        if self.ip_type:
            self.server_ip_info = self.get_server_ip_dict()
        if self.server_domain:
            self.server_domain_info = self.get_server_domain_dict()

        if self.info_center_enable:
            self.end_state[
                "info_center_enable"] = self.cur_global_info["icEnable"]
        if self.packet_priority:
            self.end_state["packet_priority"] = self.cur_global_info[
                "packetPriority"]
        if self.suppress_enable:
            self.end_state["suppress_enable"] = self.cur_global_info[
                "suppressEnable"]
        if self.logfile_max_num:
            self.end_state["logfile_max_num"] = self.cur_logfile_info[
                "maxFileNum"]
        if self.logfile_max_size:
            self.end_state["logfile_max_size"] = self.cur_logfile_info[
                "maxFileSize"]

        if self.channel_id and self.channel_cfg_name:
            if self.channel_info:
                self.end_state["channel_id_info"] = self.channel_info[
                    "channelInfos"]

        if self.channel_out_direct and self.channel_id:
            if self.channel_direct_info:
                self.end_state["channel_out_direct_info"] = self.channel_direct_info[
                    "channelDirectInfos"]

        if self.filter_feature_name and self.filter_log_name:
            if self.filter_info:
                self.end_state["filter_id_info"] = self.filter_info[
                    "filterInfos"]

        if self.ip_type:
            if self.server_ip_info:
                self.end_state["server_ip_info"] = self.server_ip_info[
                    "serverIpInfos"]

        if self.server_domain:
            if self.server_domain_info:
                self.end_state["server_domain_info"] = self.server_domain_info[
                    "serverAddressInfos"]

    def work(self):
        """worker"""

        self.check_params()
        if self.info_center_enable or self.packet_priority or self.suppress_enable:
            self.cur_global_info = self.get_syslog_global()
        if self.logfile_max_num or self.logfile_max_size:
            self.cur_logfile_info = self.get_syslog_logfile()
        if self.channel_id:
            self.channel_info = self.get_channel_dict()
        if self.channel_out_direct:
            self.channel_direct_info = self.get_channel_direct_dict()
        if self.filter_feature_name and self.filter_log_name:
            self.filter_info = self.get_filter_dict()
        if self.ip_type:
            self.server_ip_info = self.get_server_ip_dict()
        if self.server_domain:
            self.server_domain_info = self.get_server_domain_dict()
        self.get_existing()
        self.get_proposed()
        if self.info_center_enable or self.packet_priority or self.suppress_enable:
            self.merge_syslog_global()

        if self.logfile_max_num or self.logfile_max_size:
            self.merge_syslog_logfile()

        if self.server_ip:
            if not self.ip_type:
                self.module.fail_json(
                    msg='Error: ip_type and server_ip must be exist at the same time.')
        if self.ip_type:
            if not self.server_ip:
                self.module.fail_json(
                    msg='Error: ip_type and server_ip must be exist at the same time.')

        if self.ip_type or self.server_domain or self.channel_id or self.filter_feature_name:
            if self.ip_type and self.server_domain:
                self.module.fail_json(
                    msg='Error: ip_type and server_domain can not be exist at the same time.')
            if self.channel_id and self.channel_name:
                self.module.fail_json(
                    msg='Error: channel_id and channel_name can not be exist at the same time.')
            if self.ssl_policy_name:
                if self.transport_mode == "udp":
                    self.module.fail_json(
                        msg='Error: transport_mode: udp does not support ssl_policy.')
                if not self.transport_mode:
                    self.module.fail_json(
                        msg='Error: transport_mode, ssl_policy_name must be exist at the same time.')
            if self.ip_type == "ipv6":
                if self.vrf_name and self.vrf_name != "_public_":
                    self.module.fail_json(
                        msg='Error: ipType:ipv6 only support default vpn:_public_.')
            if self.is_default_vpn is True:
                if self.vrf_name:
                    if self.vrf_name != "_public_":
                        self.module.fail_json(
                            msg='Error: vrf_name should be _public_ when is_default_vpn is True.')
                else:
                    self.vrf_name = "_public_"
            else:
                if self.vrf_name == "_public_":
                    self.module.fail_json(
                        msg='Error: The default vpn value is _public_, but is_default_vpn is False.')
            if self.state == "present":
                # info-center channel channel-number name channel-name
                if self.channel_id and self.channel_cfg_name:
                    self.config_merge_syslog_channel(
                        self.channel_id, self.channel_cfg_name)
                # info-center { console | logfile | monitor | snmp | logbuffer
                # | trapbuffer } channel channel-number
                if self.channel_out_direct and self.channel_id:
                    self.config_merge_out_direct(
                        self.channel_out_direct, self.channel_id)
                # info-center filter-id bymodule-alias modname alias
                if self.filter_feature_name and self.filter_log_name:
                    self.config_merge_filter(
                        self.filter_feature_name, self.filter_log_name)
                if self.ip_type and self.server_ip:
                    if not self.vrf_name:
                        self.vrf_name = "_public_"
                    if self.check_need_loghost_cfg():
                        self.config_merge_loghost()
                if self.server_domain:
                    if not self.vrf_name:
                        self.vrf_name = "_public_"
                    if self.check_need_loghost_cfg():
                        self.config_merge_loghost()

            elif self.state == "absent":
                if self.channel_id:
                    self.delete_merge_syslog_channel(
                        self.channel_id, self.channel_cfg_name)
                if self.channel_out_direct:
                    self.delete_merge_out_direct(
                        self.channel_out_direct, self.channel_id)
                if self.filter_feature_name and self.filter_log_name:
                    self.delete_merge_filter(
                        self.filter_feature_name, self.filter_log_name)
                if self.ip_type and self.server_ip:
                    if not self.vrf_name:
                        self.vrf_name = "_public_"
                    if self.check_need_loghost_cfg():
                        self.delete_merge_loghost()
                if self.server_domain:
                    if not self.vrf_name:
                        self.vrf_name = "_public_"
                    if self.check_need_loghost_cfg():
                        self.delete_merge_loghost()

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
    """Module main"""

    argument_spec = dict(
        info_center_enable=dict(choices=['true', 'false']),
        packet_priority=dict(type='str'),
        suppress_enable=dict(choices=['true', 'false']),
        logfile_max_num=dict(type='str'),
        logfile_max_size=dict(choices=['4', '8', '16', '32']),
        channel_id=dict(type='str'),
        channel_cfg_name=dict(type='str'),
        channel_out_direct=dict(choices=['console', 'monitor',
                                         'trapbuffer', 'logbuffer', 'snmp', 'logfile']),
        filter_feature_name=dict(type='str'),
        filter_log_name=dict(type='str'),
        ip_type=dict(choices=['ipv4', 'ipv6']),
        server_ip=dict(type='str'),
        server_domain=dict(type='str'),
        is_default_vpn=dict(default=False, type='bool'),
        vrf_name=dict(type='str'),
        level=dict(choices=['emergencies', 'alert', 'critical', 'error', 'warning', 'notification',
                            'informational', 'debugging']),
        server_port=dict(type='str'),
        facility=dict(choices=['local0', 'local1', 'local2',
                               'local3', 'local4', 'local5', 'local6', 'local7']),
        channel_name=dict(type='str'),
        timestamp=dict(choices=['UTC', 'localtime']),
        transport_mode=dict(choices=['tcp', 'udp']),
        ssl_policy_name=dict(type='str'),
        source_ip=dict(type='str'),
        state=dict(choices=['present', 'absent'], default='present')

    )
    argument_spec.update(ce_argument_spec)
    module = InfoCenterGlobal(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
