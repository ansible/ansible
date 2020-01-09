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
module: ce_snmp_target_host
version_added: "2.4"
short_description: Manages SNMP target host configuration on HUAWEI CloudEngine switches.
description:
    - Manages SNMP target host configurations on HUAWEI CloudEngine switches.
author:
    - wangdezhuang (@QijunPan)
notes:
    - This module requires the netconf system service be enabled on the remote device being managed.
    - Recommended connection is C(netconf).
    - This module also works with C(local) connections for legacy playbooks.
options:
    version:
        description:
            - Version(s) Supported by SNMP Engine.
        choices: ['none', 'v1', 'v2c', 'v3', 'v1v2c', 'v1v3', 'v2cv3', 'all']
    connect_port:
        description:
            - Udp port used by SNMP agent to connect the Network management.
    host_name:
        description:
            - Unique name to identify target host entry.
    address:
        description:
            - Network Address.
    notify_type:
        description:
            - To configure notify type as trap or inform.
        choices: ['trap','inform']
    vpn_name:
        description:
            - VPN instance Name.
    recv_port:
        description:
            - UDP Port number used by network management to receive alarm messages.
    security_model:
        description:
            - Security Model.
        choices: ['v1','v2c', 'v3']
    security_name:
        description:
            - Security Name.
    security_name_v3:
        description:
            - Security Name V3.
    security_level:
        description:
            - Security level indicating whether to use authentication and encryption.
        choices: ['noAuthNoPriv','authentication', 'privacy']
    is_public_net:
        description:
            - To enable or disable Public Net-manager for target Host.
        default: no_use
        choices: ['no_use','true','false']
    interface_name:
        description:
            - Name of the interface to send the trap message.
'''

EXAMPLES = '''

- name: CloudEngine snmp target host test
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

  - name: "Config SNMP version"
    ce_snmp_target_host:
      state: present
      version: v2cv3
      provider: "{{ cli }}"

  - name: "Config SNMP target host"
    ce_snmp_target_host:
      state: present
      host_name: test1
      address: 1.1.1.1
      notify_type: trap
      vpn_name: js
      security_model: v2c
      security_name: wdz
      provider: "{{ cli }}"
'''

RETURN = '''
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"address": "10.135.182.158", "host_name": "test2",
             "notify_type": "trap", "security_level": "authentication",
             "security_model": "v3", "security_name_v3": "wdz",
             "state": "present", "vpn_name": "js"}
existing:
    description: k/v pairs of existing aaa server
    returned: always
    type: dict
    sample: {}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"target host info": [{"address": "10.135.182.158", "domain": "snmpUDPDomain",
                                   "nmsName": "test2", "notifyType": "trap",
                                   "securityLevel": "authentication", "securityModel": "v3",
                                   "securityNameV3": "wdz", "vpnInstanceName": "js"}]}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["snmp-agent target-host host-name test2 trap address udp-domain 10.135.182.158 vpn-instance js params securityname wdz v3 authentication"]
'''

from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config, \
    ce_argument_spec, load_config, check_ip_addr

# get snmp version
CE_GET_SNMP_VERSION = """
    <filter type="subtree">
      <snmp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <engine>
          <version></version>
        </engine>
      </snmp>
    </filter>
"""
# merge snmp version
CE_MERGE_SNMP_VERSION = """
    <config>
      <snmp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <engine operation="merge">
          <version>%s</version>
        </engine>
      </snmp>
    </config>
"""

# get snmp target host
CE_GET_SNMP_TARGET_HOST_HEADER = """
    <filter type="subtree">
      <snmp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <targetHosts>
          <targetHost>
            <nmsName></nmsName>
"""
CE_GET_SNMP_TARGET_HOST_TAIL = """
          </targetHost>
        </targetHosts>
      </snmp>
    </filter>
"""

# merge snmp target host
CE_MERGE_SNMP_TARGET_HOST_HEADER = """
    <config>
      <snmp xmlns="http://www.huawei.com/netconf/vrp" format-version="1.0" content-version="1.0">
        <targetHosts>
          <targetHost operation="merge">
            <nmsName>%s</nmsName>
"""
CE_MERGE_SNMP_TARGET_HOST_TAIL = """
          </targetHost>
        </targetHosts>
      </snmp>
    </config>
"""

# create snmp target host
CE_CREATE_SNMP_TARGET_HOST_HEADER = """
    <config>
      <snmp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <targetHosts>
          <targetHost operation="create">
            <nmsName>%s</nmsName>
"""
CE_CREATE_SNMP_TARGET_HOST_TAIL = """
          </targetHost>
        </targetHosts>
      </snmp>
    </config>
"""

# delete snmp target host
CE_DELETE_SNMP_TARGET_HOST_HEADER = """
    <config>
      <snmp xmlns="http://www.huawei.com/netconf/vrp" format-version="1.0" content-version="1.0">
        <targetHosts>
          <targetHost operation="delete">
            <nmsName>%s</nmsName>
"""
CE_DELETE_SNMP_TARGET_HOST_TAIL = """
          </targetHost>
        </targetHosts>
      </snmp>
    </config>
"""

# get snmp listen port
CE_GET_SNMP_PORT = """
    <filter type="subtree">
      <snmp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <systemCfg>
          <snmpListenPort></snmpListenPort>
        </systemCfg>
      </snmp>
    </filter>
"""

# merge snmp listen port
CE_MERGE_SNMP_PORT = """
    <config>
      <snmp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <systemCfg operation="merge">
          <snmpListenPort>%s</snmpListenPort>
        </systemCfg>
      </snmp>
    </config>
"""


INTERFACE_TYPE = ['ethernet', 'eth-trunk', 'tunnel', 'null', 'loopback',
                  'vlanif', '100ge', '40ge', 'mtunnel', '10ge', 'ge', 'meth', 'vbdif', 'nve']


class SnmpTargetHost(object):
    """ Manages SNMP target host configuration """

    def __init__(self, **kwargs):
        """ Class init """

        # module
        argument_spec = kwargs["argument_spec"]
        self.spec = argument_spec
        required_together = [("address", "notify_type"), ("address", "notify_type")]
        required_if = [
            ["security_model", "v1", ["security_name"]],
            ["security_model", "v2c", ["security_name"]],
            ["security_model", "v3", ["security_name_v3"]]
        ]
        self.module = AnsibleModule(
            argument_spec=argument_spec,
            required_together=required_together,
            required_if=required_if,
            supports_check_mode=True
        )

        # module args
        self.state = self.module.params['state']
        self.version = self.module.params['version']
        self.connect_port = self.module.params['connect_port']
        self.host_name = self.module.params['host_name']
        self.domain = "snmpUDPDomain"
        self.address = self.module.params['address']
        self.notify_type = self.module.params['notify_type']
        self.vpn_name = self.module.params['vpn_name']
        self.recv_port = self.module.params['recv_port']
        self.security_model = self.module.params['security_model']
        self.security_name = self.module.params['security_name']
        self.security_name_v3 = self.module.params['security_name_v3']
        self.security_level = self.module.params['security_level']
        self.is_public_net = self.module.params['is_public_net']
        self.interface_name = self.module.params['interface_name']

        # config
        self.cur_cli_cfg = dict()
        self.cur_netconf_cfg = dict()
        self.end_netconf_cfg = dict()

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

    def check_cli_args(self):
        """ Check invalid cli args """

        if self.connect_port:
            if int(self.connect_port) != 161 and (int(self.connect_port) > 65535 or int(self.connect_port) < 1025):
                self.module.fail_json(
                    msg='Error: The value of connect_port %s is out of [161, 1025 - 65535].' % self.connect_port)

    def check_netconf_args(self, result):
        """ Check invalid netconf args """

        need_cfg = True
        same_flag = True
        delete_flag = False
        result["target_host_info"] = []

        if self.host_name:

            if len(self.host_name) > 32 or len(self.host_name) < 1:
                self.module.fail_json(
                    msg='Error: The len of host_name is out of [1 - 32].')

            if self.vpn_name and self.is_public_net != 'no_use':
                if self.is_public_net == "true":
                    self.module.fail_json(
                        msg='Error: Do not support vpn_name and is_public_net at the same time.')

            conf_str = CE_GET_SNMP_TARGET_HOST_HEADER

            if self.domain:
                conf_str += "<domain></domain>"

            if self.address:
                if not check_ip_addr(ipaddr=self.address):
                    self.module.fail_json(
                        msg='Error: The host address [%s] is invalid.' % self.address)
                conf_str += "<address></address>"

            if self.notify_type:
                conf_str += "<notifyType></notifyType>"

            if self.vpn_name:
                if len(self.vpn_name) > 31 or len(self.vpn_name) < 1:
                    self.module.fail_json(
                        msg='Error: The len of vpn_name is out of [1 - 31].')
                conf_str += "<vpnInstanceName></vpnInstanceName>"

            if self.recv_port:
                if int(self.recv_port) > 65535 or int(self.recv_port) < 0:
                    self.module.fail_json(
                        msg='Error: The value of recv_port is out of [0 - 65535].')
                conf_str += "<portNumber></portNumber>"

            if self.security_model:
                conf_str += "<securityModel></securityModel>"

            if self.security_name:
                if len(self.security_name) > 32 or len(self.security_name) < 1:
                    self.module.fail_json(
                        msg='Error: The len of security_name is out of [1 - 32].')
                conf_str += "<securityName></securityName>"

            if self.security_name_v3:
                if len(self.security_name_v3) > 32 or len(self.security_name_v3) < 1:
                    self.module.fail_json(
                        msg='Error: The len of security_name_v3 is out of [1 - 32].')
                conf_str += "<securityNameV3></securityNameV3>"

            if self.security_level:
                conf_str += "<securityLevel></securityLevel>"

            if self.is_public_net != 'no_use':
                conf_str += "<isPublicNet></isPublicNet>"

            if self.interface_name:
                if len(self.interface_name) > 63 or len(self.interface_name) < 1:
                    self.module.fail_json(
                        msg='Error: The len of interface_name is out of [1 - 63].')

                find_flag = False
                for item in INTERFACE_TYPE:
                    if item in self.interface_name.lower():
                        find_flag = True
                        break
                if not find_flag:
                    self.module.fail_json(
                        msg='Error: Please input full name of interface_name.')

                conf_str += "<interface-name></interface-name>"

            conf_str += CE_GET_SNMP_TARGET_HOST_TAIL
            recv_xml = self.netconf_get_config(conf_str=conf_str)

            if "<data/>" in recv_xml:
                if self.state == "present":
                    same_flag = False
                else:
                    delete_flag = False
            else:
                xml_str = recv_xml.replace('\r', '').replace('\n', '').\
                    replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                    replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

                root = ElementTree.fromstring(xml_str)
                target_host_info = root.findall(
                    "snmp/targetHosts/targetHost")
                if target_host_info:
                    for tmp in target_host_info:
                        tmp_dict = dict()
                        for site in tmp:
                            if site.tag in ["nmsName", "domain", "address", "notifyType", "vpnInstanceName",
                                            "portNumber", "securityModel", "securityName", "securityNameV3",
                                            "securityLevel", "isPublicNet", "interface-name"]:
                                tmp_dict[site.tag] = site.text

                        result["target_host_info"].append(tmp_dict)

                if result["target_host_info"]:
                    for tmp in result["target_host_info"]:

                        same_flag = True

                        if "nmsName" in tmp.keys():
                            if tmp["nmsName"] != self.host_name:
                                same_flag = False
                            else:
                                delete_flag = True

                        if "domain" in tmp.keys():
                            if tmp["domain"] != self.domain:
                                same_flag = False

                        if "address" in tmp.keys():
                            if tmp["address"] != self.address:
                                same_flag = False

                        if "notifyType" in tmp.keys():
                            if tmp["notifyType"] != self.notify_type:
                                same_flag = False

                        if "vpnInstanceName" in tmp.keys():
                            if tmp["vpnInstanceName"] != self.vpn_name:
                                same_flag = False

                        if "portNumber" in tmp.keys():
                            if tmp["portNumber"] != self.recv_port:
                                same_flag = False

                        if "securityModel" in tmp.keys():
                            if tmp["securityModel"] != self.security_model:
                                same_flag = False

                        if "securityName" in tmp.keys():
                            if tmp["securityName"] != self.security_name:
                                same_flag = False

                        if "securityNameV3" in tmp.keys():
                            if tmp["securityNameV3"] != self.security_name_v3:
                                same_flag = False

                        if "securityLevel" in tmp.keys():
                            if tmp["securityLevel"] != self.security_level:
                                same_flag = False

                        if "isPublicNet" in tmp.keys():
                            if tmp["isPublicNet"] != self.is_public_net:
                                same_flag = False

                        if "interface-name" in tmp.keys():
                            if tmp.get("interface-name") is not None:
                                if tmp["interface-name"].lower() != self.interface_name.lower():
                                    same_flag = False
                            else:
                                same_flag = False

                        if same_flag:
                            break

        if self.state == "present":
            need_cfg = True
            if same_flag:
                need_cfg = False
        else:
            need_cfg = False
            if delete_flag:
                need_cfg = True

        result["need_cfg"] = need_cfg

    def cli_load_config(self, commands):
        """ Load configure by cli """

        if not self.module.check_mode:
            load_config(self.module, commands)

    def get_snmp_version(self):
        """ Get snmp version """

        version = None
        conf_str = CE_GET_SNMP_VERSION
        recv_xml = self.netconf_get_config(conf_str=conf_str)

        if "<data/>" in recv_xml:
            pass

        else:
            xml_str = recv_xml.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

            root = ElementTree.fromstring(xml_str)
            version_info = root.find("snmp/engine")
            if version_info:
                for site in version_info:
                    if site.tag in ["version"]:
                        version = site.text

        return version

    def xml_get_connect_port(self):
        """ Get connect port by xml """
        tmp_cfg = None
        conf_str = CE_GET_SNMP_PORT
        recv_xml = self.netconf_get_config(conf_str=conf_str)
        if "<data/>" in recv_xml:
            pass
        else:
            xml_str = recv_xml.replace('\r', '').replace('\n', '').\
                replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
                replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

            root = ElementTree.fromstring(xml_str)
            snmp_port_info = root.findall("snmp/systemCfg/snmpListenPort")

            if snmp_port_info:
                tmp_cfg = snmp_port_info[0].text
            return tmp_cfg

    def get_proposed(self):
        """ Get proposed state """

        self.proposed["state"] = self.state

        if self.version:
            self.proposed["version"] = self.version
        if self.connect_port:
            self.proposed["connect_port"] = self.connect_port
        if self.host_name:
            self.proposed["host_name"] = self.host_name
        if self.address:
            self.proposed["address"] = self.address
        if self.notify_type:
            self.proposed["notify_type"] = self.notify_type
        if self.vpn_name:
            self.proposed["vpn_name"] = self.vpn_name
        if self.recv_port:
            self.proposed["recv_port"] = self.recv_port
        if self.security_model:
            self.proposed["security_model"] = self.security_model
        if self.security_name:
            self.proposed["security_name"] = "******"
        if self.security_name_v3:
            self.proposed["security_name_v3"] = self.security_name_v3
        if self.security_level:
            self.proposed["security_level"] = self.security_level
        if self.is_public_net != 'no_use':
            self.proposed["is_public_net"] = self.is_public_net
        if self.interface_name:
            self.proposed["interface_name"] = self.interface_name

    def get_existing(self):
        """ Get existing state """

        if self.version:
            version = self.get_snmp_version()
            if version:
                self.cur_cli_cfg["version"] = version
                self.existing["version"] = version

        if self.connect_port:
            tmp_cfg = self.xml_get_connect_port()
            if tmp_cfg:
                self.cur_cli_cfg["connect port"] = tmp_cfg
                self.existing["connect port"] = tmp_cfg

        if self.host_name:
            self.existing["target host info"] = self.cur_netconf_cfg[
                "target_host_info"]

    def get_end_state(self):
        """ Get end state """

        if self.version:
            version = self.get_snmp_version()
            if version:
                self.end_state["version"] = version

        if self.connect_port:
            tmp_cfg = self.xml_get_connect_port()
            if tmp_cfg:
                self.end_state["connect port"] = tmp_cfg

        if self.host_name:
            self.end_state["target host info"] = self.end_netconf_cfg[
                "target_host_info"]
        if self.existing == self.end_state:
            self.changed = False
            self.updates_cmd = list()

    def config_version_cli(self):
        """ Config version by cli """

        if "disable" in self.cur_cli_cfg["version"]:
            cmd = "snmp-agent sys-info version %s" % self.version
            self.updates_cmd.append(cmd)

            cmds = list()
            cmds.append(cmd)

            self.cli_load_config(cmds)
            self.changed = True

        else:
            if self.version != self.cur_cli_cfg["version"]:
                cmd = "snmp-agent sys-info version  %s disable" % self.cur_cli_cfg[
                    "version"]
                self.updates_cmd.append(cmd)
                cmd = "snmp-agent sys-info version  %s" % self.version
                self.updates_cmd.append(cmd)

                cmds = list()
                cmds.append(cmd)

                self.cli_load_config(cmds)
                self.changed = True

    def undo_config_version_cli(self):
        """ Undo config version by cli """

        if "disable" in self.cur_cli_cfg["version"]:
            pass
        else:
            cmd = "snmp-agent sys-info version  %s disable" % self.cur_cli_cfg[
                "version"]

            cmds = list()
            cmds.append(cmd)

            self.updates_cmd.append(cmd)
            self.cli_load_config(cmds)
            self.changed = True

    def config_connect_port_xml(self):
        """ Config connect port by xml """

        if "connect port" in self.cur_cli_cfg.keys():
            if self.cur_cli_cfg["connect port"] == self.connect_port:
                pass
            else:
                cmd = "snmp-agent udp-port %s" % self.connect_port

                cmds = list()
                cmds.append(cmd)

                self.updates_cmd.append(cmd)
                conf_str = CE_MERGE_SNMP_PORT % self.connect_port
                self.netconf_set_config(conf_str=conf_str)
                self.changed = True
        else:
            cmd = "snmp-agent udp-port %s" % self.connect_port

            cmds = list()
            cmds.append(cmd)

            self.updates_cmd.append(cmd)
            conf_str = CE_MERGE_SNMP_PORT % self.connect_port
            self.netconf_set_config(conf_str=conf_str)
            self.changed = True

    def undo_config_connect_port_cli(self):
        """ Undo config connect port by cli """

        if "connect port" in self.cur_cli_cfg.keys():
            if not self.cur_cli_cfg["connect port"]:
                pass
            else:
                cmd = "undo snmp-agent udp-port"

                cmds = list()
                cmds.append(cmd)

                self.updates_cmd.append(cmd)
                connect_port = "161"
                conf_str = CE_MERGE_SNMP_PORT % connect_port
                self.netconf_set_config(conf_str=conf_str)
                self.changed = True

    def merge_snmp_target_host(self):
        """ Merge snmp target host operation """

        conf_str = CE_MERGE_SNMP_TARGET_HOST_HEADER % self.host_name

        if self.domain:
            conf_str += "<domain>%s</domain>" % self.domain
        if self.address:
            conf_str += "<address>%s</address>" % self.address
        if self.notify_type:
            conf_str += "<notifyType>%s</notifyType>" % self.notify_type
        if self.vpn_name:
            conf_str += "<vpnInstanceName>%s</vpnInstanceName>" % self.vpn_name
        if self.recv_port:
            conf_str += "<portNumber>%s</portNumber>" % self.recv_port
        if self.security_model:
            conf_str += "<securityModel>%s</securityModel>" % self.security_model
        if self.security_name:
            conf_str += "<securityName>%s</securityName>" % self.security_name
        if self.security_name_v3:
            conf_str += "<securityNameV3>%s</securityNameV3>" % self.security_name_v3
        if self.security_level:
            conf_str += "<securityLevel>%s</securityLevel>" % self.security_level
        if self.is_public_net != 'no_use':
            conf_str += "<isPublicNet>%s</isPublicNet>" % self.is_public_net
        if self.interface_name:
            conf_str += "<interface-name>%s</interface-name>" % self.interface_name

        conf_str += CE_MERGE_SNMP_TARGET_HOST_TAIL

        recv_xml = self.netconf_set_config(conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Merge snmp target host failed.')

        cmd = "snmp-agent target-host host-name %s " % self.host_name
        cmd += "%s " % self.notify_type
        cmd += "address udp-domain %s " % self.address

        if self.recv_port:
            cmd += "udp-port %s " % self.recv_port
        if self.interface_name:
            cmd += "source %s " % self.interface_name
        if self.vpn_name:
            cmd += "vpn-instance %s " % self.vpn_name
        if self.is_public_net == "true":
            cmd += "public-net "
        if self.security_model in ["v1", "v2c"] and self.security_name:
            cmd += "params securityname %s %s " % (
                "******", self.security_model)
        if self.security_model == "v3" and self.security_name_v3:
            cmd += "params securityname %s %s " % (
                self.security_name_v3, self.security_model)
            if self.security_level and self.security_level in ["authentication", "privacy"]:
                cmd += "%s" % self.security_level

        self.changed = True
        self.updates_cmd.append(cmd)

    def delete_snmp_target_host(self):
        """ Delete snmp target host operation """

        conf_str = CE_DELETE_SNMP_TARGET_HOST_HEADER % self.host_name

        if self.domain:
            conf_str += "<domain>%s</domain>" % self.domain
        if self.address:
            conf_str += "<address>%s</address>" % self.address
        if self.notify_type:
            conf_str += "<notifyType>%s</notifyType>" % self.notify_type
        if self.vpn_name:
            conf_str += "<vpnInstanceName>%s</vpnInstanceName>" % self.vpn_name
        if self.recv_port:
            conf_str += "<portNumber>%s</portNumber>" % self.recv_port
        if self.security_model:
            conf_str += "<securityModel>%s</securityModel>" % self.security_model
        if self.security_name:
            conf_str += "<securityName>%s</securityName>" % self.security_name
        if self.security_name_v3:
            conf_str += "<securityNameV3>%s</securityNameV3>" % self.security_name_v3
        if self.security_level:
            conf_str += "<securityLevel>%s</securityLevel>" % self.security_level
        if self.is_public_net != 'no_use':
            conf_str += "<isPublicNet>%s</isPublicNet>" % self.is_public_net
        if self.interface_name:
            conf_str += "<interface-name>%s</interface-name>" % self.interface_name

        conf_str += CE_DELETE_SNMP_TARGET_HOST_TAIL

        recv_xml = self.netconf_set_config(conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Delete snmp target host failed.')

        if not self.address:
            cmd = "undo snmp-agent target-host host-name %s " % self.host_name
        else:
            if self.notify_type == "trap":
                cmd = "undo snmp-agent target-host trap address udp-domain %s " % self.address
            else:
                cmd = "undo snmp-agent target-host inform address udp-domain %s " % self.address
            if self.recv_port:
                cmd += "udp-port %s " % self.recv_port
            if self.interface_name:
                cmd += "source %s " % self.interface_name
            if self.vpn_name:
                cmd += "vpn-instance %s " % self.vpn_name
            if self.is_public_net == "true":
                cmd += "public-net "
            if self.security_model in ["v1", "v2c"] and self.security_name:
                cmd += "params securityname %s" % "******"
            if self.security_model == "v3" and self.security_name_v3:
                cmd += "params securityname %s" % self.security_name_v3

        self.changed = True
        self.updates_cmd.append(cmd)

    def merge_snmp_version(self):
        """ Merge snmp version operation """

        conf_str = CE_MERGE_SNMP_VERSION % self.version
        recv_xml = self.netconf_set_config(conf_str=conf_str)

        if "<ok/>" not in recv_xml:
            self.module.fail_json(msg='Error: Merge snmp version failed.')

        if self.version == "none":
            cmd = "snmp-agent sys-info version %s disable" % self.cur_cli_cfg[
                "version"]
            self.updates_cmd.append(cmd)
        elif self.version == "v1v2c":
            cmd = "snmp-agent sys-info version v1"
            self.updates_cmd.append(cmd)
            cmd = "snmp-agent sys-info version v2c"
            self.updates_cmd.append(cmd)
        elif self.version == "v1v3":
            cmd = "snmp-agent sys-info version v1"
            self.updates_cmd.append(cmd)
            cmd = "snmp-agent sys-info version v3"
            self.updates_cmd.append(cmd)
        elif self.version == "v2cv3":
            cmd = "snmp-agent sys-info version v2c"
            self.updates_cmd.append(cmd)
            cmd = "snmp-agent sys-info version v3"
            self.updates_cmd.append(cmd)
        else:
            cmd = "snmp-agent sys-info version %s" % self.version
            self.updates_cmd.append(cmd)

        self.changed = True

    def work(self):
        """ Main work function """

        self.check_cli_args()
        self.check_netconf_args(self.cur_netconf_cfg)
        self.get_proposed()
        self.get_existing()

        if self.state == "present":
            if self.version:
                if self.version != self.cur_cli_cfg["version"]:
                    self.merge_snmp_version()
            if self.connect_port:
                self.config_connect_port_xml()
            if self.cur_netconf_cfg["need_cfg"]:
                self.merge_snmp_target_host()

        else:
            if self.connect_port:
                self.undo_config_connect_port_cli()
            if self.cur_netconf_cfg["need_cfg"]:
                self.delete_snmp_target_host()

        self.check_netconf_args(self.end_netconf_cfg)
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
        state=dict(choices=['present', 'absent'], default='present'),
        version=dict(choices=['none', 'v1', 'v2c', 'v3',
                              'v1v2c', 'v1v3', 'v2cv3', 'all']),
        connect_port=dict(type='str'),
        host_name=dict(type='str'),
        address=dict(type='str'),
        notify_type=dict(choices=['trap', 'inform']),
        vpn_name=dict(type='str'),
        recv_port=dict(type='str'),
        security_model=dict(choices=['v1', 'v2c', 'v3']),
        security_name=dict(type='str', no_log=True),
        security_name_v3=dict(type='str'),
        security_level=dict(
            choices=['noAuthNoPriv', 'authentication', 'privacy']),
        is_public_net=dict(type='str', default='no_use', choices=['no_use', 'true', 'false']),
        interface_name=dict(type='str')
    )

    argument_spec.update(ce_argument_spec)
    module = SnmpTargetHost(argument_spec=argument_spec)
    module.work()


if __name__ == '__main__':
    main()
