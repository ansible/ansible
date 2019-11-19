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

DOCUMENTATION = """
---
module: ce_sflow
version_added: "2.4"
short_description: Manages sFlow configuration on HUAWEI CloudEngine switches.
description:
    - Configure Sampled Flow (sFlow) to monitor traffic on an interface in real time,
      detect abnormal traffic, and locate the source of attack traffic,
      ensuring stable running of the network.
author: QijunPan (@QijunPan)
notes:
    - This module requires the netconf system service be enabled on the remote device being managed.
    - Recommended connection is C(netconf).
    - This module also works with C(local) connections for legacy playbooks.
options:
    agent_ip:
        description:
            - Specifies the IPv4/IPv6 address of an sFlow agent.
    source_ip:
        description:
            - Specifies the source IPv4/IPv6 address of sFlow packets.
    collector_id:
        description:
            - Specifies the ID of an sFlow collector. This ID is used when you specify
              the collector in subsequent sFlow configuration.
        choices: ['1', '2']
    collector_ip:
        description:
            - Specifies the IPv4/IPv6 address of the sFlow collector.
    collector_ip_vpn:
        description:
            - Specifies the name of a VPN instance.
              The value is a string of 1 to 31 case-sensitive characters, spaces not supported.
              When double quotation marks are used around the string, spaces are allowed in the string.
              The value C(_public_) is reserved and cannot be used as the VPN instance name.
    collector_datagram_size:
        description:
            - Specifies the maximum length of sFlow packets sent from an sFlow agent to an sFlow collector.
              The value is an integer, in bytes. It ranges from 1024 to 8100. The default value is 1400.
    collector_udp_port:
        description:
            - Specifies the UDP destination port number of sFlow packets.
              The value is an integer that ranges from 1 to 65535. The default value is 6343.
    collector_meth:
        description:
            - Configures the device to send sFlow packets through service interfaces,
              enhancing the sFlow packet forwarding capability.
              The enhanced parameter is optional. No matter whether you configure the enhanced mode,
              the switch determines to send sFlow packets through service cards or management port
              based on the routing information on the collector.
              When the value is meth, the device forwards sFlow packets at the control plane.
              When the value is enhanced, the device forwards sFlow packets at the forwarding plane to
              enhance the sFlow packet forwarding capacity.
        choices: ['meth', 'enhanced']
    collector_description:
        description:
            - Specifies the description of an sFlow collector.
              The value is a string of 1 to 255 case-sensitive characters without spaces.
    sflow_interface:
        description:
            - Full name of interface for Flow Sampling or Counter.
              It must be a physical interface, Eth-Trunk, or Layer 2 subinterface.
    sample_collector:
        description:
            -  Indicates the ID list of the collector.
    sample_rate:
        description:
            - Specifies the flow sampling rate in the format 1/rate.
              The value is an integer and ranges from 1 to 4294967295. The default value is 8192.
    sample_length:
        description:
            - Specifies the maximum length of sampled packets.
              The value is an integer and ranges from 18 to 512, in bytes. The default value is 128.
    sample_direction:
        description:
            - Enables flow sampling in the inbound or outbound direction.
        choices: ['inbound', 'outbound', 'both']
    counter_collector:
        description:
            - Indicates the ID list of the counter collector.
    counter_interval:
        description:
            - Indicates the counter sampling interval.
              The value is an integer that ranges from 10 to 4294967295, in seconds. The default value is 20.
    export_route:
        description:
            - Configures the sFlow packets sent by the switch not to carry routing information.
        choices: ['enable', 'disable']
    rate_limit:
        description:
            - Specifies the rate of sFlow packets sent from a card to the control plane.
              The value is an integer that ranges from 100 to 1500, in pps.
    rate_limit_slot:
        description:
            - Specifies the slot where the rate of output sFlow packets is limited.
              If this parameter is not specified, the rate of sFlow packets sent from
              all cards to the control plane is limited.
              The value is an integer or a string of characters.
    forward_enp_slot:
        description:
            - Enable the Embedded Network Processor (ENP) chip function.
              The switch uses the ENP chip to perform sFlow sampling,
              and the maximum sFlow sampling interval is 65535.
              If you set the sampling interval to be larger than 65535,
              the switch automatically restores it to 65535.
              The value is an integer or 'all'.
    state:
        description:
            - Determines whether the config should be present or not
              on the device.
        default: present
        choices: ['present', 'absent']
"""

EXAMPLES = '''
---

- name: sflow module test
  hosts: ce128
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
  - name: Configuring sFlow Agent
    ce_sflow:
      agent_ip: 6.6.6.6
      provider: '{{ cli }}'

  - name: Configuring sFlow Collector
    ce_sflow:
      collector_id: 1
      collector_ip: 7.7.7.7
      collector_ip_vpn: vpn1
      collector_description: Collector1
      provider: '{{ cli }}'

  - name: Configure flow sampling.
    ce_sflow:
      sflow_interface: 10GE2/0/2
      sample_collector: 1
      sample_direction: inbound
      provider: '{{ cli }}'

  - name: Configure counter sampling.
    ce_sflow:
      sflow_interface: 10GE2/0/2
      counter_collector: 1
      counter_interval: 1000
      provider: '{{ cli }}'
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"agent_ip": "6.6.6.6", "state": "present"}
existing:
    description: k/v pairs of existing configuration
    returned: verbose mode
    type: dict
    sample: {"agent": {}}
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"agent": {"family": "ipv4", "ipv4Addr": "1.2.3.4", "ipv6Addr": null}}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["sflow agent ip 6.6.6.6"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
'''

import re
from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config, ce_argument_spec, check_ip_addr
from ansible.module_utils.network.cloudengine.ce import get_config, load_config

CE_NC_GET_SFLOW = """
<filter type="subtree">
<sflow xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <sources>
        <source>
            <family></family>
            <ipv4Addr></ipv4Addr>
            <ipv6Addr></ipv6Addr>
        </source>
    </sources>
    <agents>
        <agent>
            <family></family>
            <ipv4Addr></ipv4Addr>
            <ipv6Addr></ipv6Addr>
        </agent>
    </agents>
    <collectors>
        <collector>
            <collectorID></collectorID>
            <family></family>
            <ipv4Addr></ipv4Addr>
            <ipv6Addr></ipv6Addr>
            <vrfName></vrfName>
            <datagramSize></datagramSize>
            <port></port>
            <description></description>
            <meth></meth>
        </collector>
    </collectors>
    <samplings>
        <sampling>
            <ifName>%s</ifName>
            <collectorID></collectorID>
            <direction></direction>
            <length></length>
            <rate></rate>
        </sampling>
    </samplings>
    <counters>
        <counter>
            <ifName>%s</ifName>
            <collectorID></collectorID>
            <interval></interval>
        </counter>
    </counters>
    <exports>
        <export>
            <ExportRoute></ExportRoute>
        </export>
    </exports>
</sflow>
</filter>
"""


def is_config_exist(cmp_cfg, test_cfg):
    """is configuration exist?"""

    if not cmp_cfg or not test_cfg:
        return False

    return bool(test_cfg in cmp_cfg)


def is_valid_ip_vpn(vpname):
    """check ip vpn"""

    if not vpname:
        return False

    if vpname == "_public_":
        return False

    if len(vpname) < 1 or len(vpname) > 31:
        return False

    return True


def get_ip_version(address):
    """get ip version fast"""

    if not address:
        return None

    if address.count(':') >= 2 and address.count(":") <= 7:
        return "ipv6"
    elif address.count('.') == 3:
        return "ipv4"
    else:
        return None


def get_interface_type(interface):
    """get the type of interface, such as 10GE, ETH-TRUNK, VLANIF..."""

    if interface is None:
        return None

    if interface.upper().startswith('GE'):
        iftype = 'ge'
    elif interface.upper().startswith('10GE'):
        iftype = '10ge'
    elif interface.upper().startswith('25GE'):
        iftype = '25ge'
    elif interface.upper().startswith('4X10GE'):
        iftype = '4x10ge'
    elif interface.upper().startswith('40GE'):
        iftype = '40ge'
    elif interface.upper().startswith('100GE'):
        iftype = '100ge'
    elif interface.upper().startswith('VLANIF'):
        iftype = 'vlanif'
    elif interface.upper().startswith('LOOPBACK'):
        iftype = 'loopback'
    elif interface.upper().startswith('METH'):
        iftype = 'meth'
    elif interface.upper().startswith('ETH-TRUNK'):
        iftype = 'eth-trunk'
    elif interface.upper().startswith('VBDIF'):
        iftype = 'vbdif'
    elif interface.upper().startswith('NVE'):
        iftype = 'nve'
    elif interface.upper().startswith('TUNNEL'):
        iftype = 'tunnel'
    elif interface.upper().startswith('ETHERNET'):
        iftype = 'ethernet'
    elif interface.upper().startswith('FCOE-PORT'):
        iftype = 'fcoe-port'
    elif interface.upper().startswith('FABRIC-PORT'):
        iftype = 'fabric-port'
    elif interface.upper().startswith('STACK-PORT'):
        iftype = 'stack-port'
    elif interface.upper().startswith('NULL'):
        iftype = 'null'
    else:
        return None

    return iftype.lower()


def get_rate_limit(config):
    """get sflow management-plane export rate-limit info"""

    get = re.findall(r"sflow management-plane export rate-limit ([0-9]+) slot ([0-9]+)", config)
    if not get:
        get = re.findall(r"sflow management-plane export rate-limit ([0-9]+)", config)
        if not get:
            return None
        else:
            return dict(rate_limit=get[0])
    else:
        limit = list()
        for slot in get:
            limit.append(dict(rate_limit=slot[0], slot_id=slot[1]))
        return limit


def get_forward_enp(config):
    """get assign forward enp sflow enable slot info"""

    get = re.findall(r"assign forward enp sflow enable slot (\S+)", config)
    if not get:
        return None
    else:
        return list(get)


class Sflow(object):
    """Manages sFlow"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.__init_module__()

        # module input info
        self.agent_ip = self.module.params['agent_ip']
        self.agent_version = None
        self.source_ip = self.module.params['source_ip']
        self.source_version = None
        self.export_route = self.module.params['export_route']
        self.rate_limit = self.module.params['rate_limit']
        self.rate_limit_slot = self.module.params['rate_limit_slot']
        self.forward_enp_slot = self.module.params['forward_enp_slot']
        self.collector_id = self.module.params['collector_id']
        self.collector_ip = self.module.params['collector_ip']
        self.collector_version = None
        self.collector_ip_vpn = self.module.params['collector_ip_vpn']
        self.collector_datagram_size = self.module.params['collector_datagram_size']
        self.collector_udp_port = self.module.params['collector_udp_port']
        self.collector_meth = self.module.params['collector_meth']
        self.collector_description = self.module.params['collector_description']
        self.sflow_interface = self.module.params['sflow_interface']
        self.sample_collector = self.module.params['sample_collector'] or list()
        self.sample_rate = self.module.params['sample_rate']
        self.sample_length = self.module.params['sample_length']
        self.sample_direction = self.module.params['sample_direction']
        self.counter_collector = self.module.params['counter_collector'] or list()
        self.counter_interval = self.module.params['counter_interval']
        self.state = self.module.params['state']

        # state
        self.config = ""  # current config
        self.sflow_dict = dict()
        self.changed = False
        self.updates_cmd = list()
        self.commands = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def __init_module__(self):
        """init module"""

        required_together = [("collector_id", "collector_ip")]
        self.module = AnsibleModule(
            argument_spec=self.spec, required_together=required_together, supports_check_mode=True)

    def check_response(self, con_obj, xml_name):
        """Check if response message is already succeed"""

        xml_str = con_obj.xml
        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def netconf_set_config(self, xml_str, xml_name):
        """netconf set config"""

        rcv_xml = set_nc_config(self.module, xml_str)
        if "<ok/>" not in rcv_xml:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def cli_load_config(self, commands):
        """load config by cli"""

        if not self.module.check_mode:
            load_config(self.module, commands)

    def get_current_config(self):
        """get current configuration"""

        flags = list()
        exp = ""
        if self.rate_limit:
            exp += "assign sflow management-plane export rate-limit %s" % self.rate_limit
            if self.rate_limit_slot:
                exp += " slot %s" % self.rate_limit_slot
            exp += "$"

        if self.forward_enp_slot:
            if exp:
                exp += "|"
            exp += "assign forward enp sflow enable slot %s$" % self.forward_enp_slot

        if exp:
            exp = " | ignore-case include " + exp
            flags.append(exp)
            return get_config(self.module, flags)
        else:
            return ""

    def cli_add_command(self, command, undo=False):
        """add command to self.update_cmd and self.commands"""

        if undo and command.lower() not in ["quit", "return"]:
            cmd = "undo " + command
        else:
            cmd = command

        self.commands.append(cmd)          # set to device
        if command.lower() not in ["quit", "return"]:
            self.updates_cmd.append(cmd)   # show updates result

    def get_sflow_dict(self):
        """ sflow config dict"""

        sflow_dict = dict(source=list(), agent=dict(), collector=list(),
                          sampling=dict(), counter=dict(), export=dict())
        conf_str = CE_NC_GET_SFLOW % (
            self.sflow_interface, self.sflow_interface)

        if not self.collector_meth:
            conf_str = conf_str.replace("<meth></meth>", "")

        rcv_xml = get_nc_config(self.module, conf_str)

        if "<data/>" in rcv_xml:
            return sflow_dict

        xml_str = rcv_xml.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
        root = ElementTree.fromstring(xml_str)

        # get source info
        srcs = root.findall("data/sflow/sources/source")
        if srcs:
            for src in srcs:
                attrs = dict()
                for attr in src:
                    if attr.tag in ["family", "ipv4Addr", "ipv6Addr"]:
                        attrs[attr.tag] = attr.text
                sflow_dict["source"].append(attrs)

        # get agent info
        agent = root.find("data/sflow/agents/agent")
        if agent:
            for attr in agent:
                if attr.tag in ["family", "ipv4Addr", "ipv6Addr"]:
                    sflow_dict["agent"][attr.tag] = attr.text

        # get collector info
        collectors = root.findall("data/sflow/collectors/collector")
        if collectors:
            for collector in collectors:
                attrs = dict()
                for attr in collector:
                    if attr.tag in ["collectorID", "family", "ipv4Addr", "ipv6Addr",
                                    "vrfName", "datagramSize", "port", "description", "meth"]:
                        attrs[attr.tag] = attr.text
                sflow_dict["collector"].append(attrs)

        # get sampling info
        sample = root.find("data/sflow/samplings/sampling")
        if sample:
            for attr in sample:
                if attr.tag in ["ifName", "collectorID", "direction", "length", "rate"]:
                    sflow_dict["sampling"][attr.tag] = attr.text

        # get counter info
        counter = root.find("data/sflow/counters/counter")
        if counter:
            for attr in counter:
                if attr.tag in ["ifName", "collectorID", "interval"]:
                    sflow_dict["counter"][attr.tag] = attr.text

        # get export info
        export = root.find("data/sflow/exports/export")
        if export:
            for attr in export:
                if attr.tag == "ExportRoute":
                    sflow_dict["export"][attr.tag] = attr.text

        return sflow_dict

    def config_agent(self):
        """configures sFlow agent"""

        xml_str = ''
        if not self.agent_ip:
            return xml_str

        self.agent_version = get_ip_version(self.agent_ip)
        if not self.agent_version:
            self.module.fail_json(msg="Error: agent_ip is invalid.")

        if self.state == "present":
            if self.agent_ip != self.sflow_dict["agent"].get("ipv4Addr") \
                    and self.agent_ip != self.sflow_dict["agent"].get("ipv6Addr"):
                xml_str += '<agents><agent operation="merge">'
                xml_str += '<family>%s</family>' % self.agent_version
                if self.agent_version == "ipv4":
                    xml_str += '<ipv4Addr>%s</ipv4Addr>' % self.agent_ip
                    self.updates_cmd.append("sflow agent ip %s" % self.agent_ip)
                else:
                    xml_str += '<ipv6Addr>%s</ipv6Addr>' % self.agent_ip
                    self.updates_cmd.append("sflow agent ipv6 %s" % self.agent_ip)
                xml_str += '</agent></agents>'

        else:
            if self.agent_ip == self.sflow_dict["agent"].get("ipv4Addr") \
                    or self.agent_ip == self.sflow_dict["agent"].get("ipv6Addr"):
                xml_str += '<agents><agent operation="delete"></agent></agents>'
                self.updates_cmd.append("undo sflow agent")

        return xml_str

    def config_source(self):
        """configures the source IP address for sFlow packets"""

        xml_str = ''
        if not self.source_ip:
            return xml_str

        self.source_version = get_ip_version(self.source_ip)
        if not self.source_version:
            self.module.fail_json(msg="Error: source_ip is invalid.")

        src_dict = dict()
        for src in self.sflow_dict["source"]:
            if src.get("family") == self.source_version:
                src_dict = src
                break

        if self.state == "present":
            if self.source_ip != src_dict.get("ipv4Addr") \
                    and self.source_ip != src_dict.get("ipv6Addr"):
                xml_str += '<sources><source operation="merge">'
                xml_str += '<family>%s</family>' % self.source_version
                if self.source_version == "ipv4":
                    xml_str += '<ipv4Addr>%s</ipv4Addr>' % self.source_ip
                    self.updates_cmd.append("sflow source ip %s" % self.source_ip)
                else:
                    xml_str += '<ipv6Addr>%s</ipv6Addr>' % self.source_ip
                    self.updates_cmd.append(
                        "sflow source ipv6 %s" % self.source_ip)
                xml_str += '</source ></sources>'
        else:
            if self.source_ip == src_dict.get("ipv4Addr"):
                xml_str += '<sources><source operation="delete"><family>ipv4</family></source ></sources>'
                self.updates_cmd.append("undo sflow source ip %s" % self.source_ip)
            elif self.source_ip == src_dict.get("ipv6Addr"):
                xml_str += '<sources><source operation="delete"><family>ipv6</family></source ></sources>'
                self.updates_cmd.append("undo sflow source ipv6 %s" % self.source_ip)

        return xml_str

    def config_collector(self):
        """creates an sFlow collector and sets or modifies optional parameters for the sFlow collector"""

        xml_str = ''
        if not self.collector_id:
            return xml_str

        if self.state == "present" and not self.collector_ip:
            return xml_str

        if self.collector_ip:
            self.collector_version = get_ip_version(self.collector_ip)
            if not self.collector_version:
                self.module.fail_json(msg="Error: collector_ip is invalid.")

        # get collector dict
        exist_dict = dict()
        for collector in self.sflow_dict["collector"]:
            if collector.get("collectorID") == self.collector_id:
                exist_dict = collector
                break

        change = False
        if self.state == "present":
            if not exist_dict:
                change = True
            elif self.collector_version != exist_dict.get("family"):
                change = True
            elif self.collector_version == "ipv4" and self.collector_ip != exist_dict.get("ipv4Addr"):
                change = True
            elif self.collector_version == "ipv6" and self.collector_ip != exist_dict.get("ipv6Addr"):
                change = True
            elif self.collector_ip_vpn and self.collector_ip_vpn != exist_dict.get("vrfName"):
                change = True
            elif not self.collector_ip_vpn and exist_dict.get("vrfName") != "_public_":
                change = True
            elif self.collector_udp_port and self.collector_udp_port != exist_dict.get("port"):
                change = True
            elif not self.collector_udp_port and exist_dict.get("port") != "6343":
                change = True
            elif self.collector_datagram_size and self.collector_datagram_size != exist_dict.get("datagramSize"):
                change = True
            elif not self.collector_datagram_size and exist_dict.get("datagramSize") != "1400":
                change = True
            elif self.collector_meth and self.collector_meth != exist_dict.get("meth"):
                change = True
            elif not self.collector_meth and exist_dict.get("meth") and exist_dict.get("meth") != "meth":
                change = True
            elif self.collector_description and self.collector_description != exist_dict.get("description"):
                change = True
            elif not self.collector_description and exist_dict.get("description"):
                change = True
            else:
                pass
        else:  # absent
            # collector not exist
            if not exist_dict:
                return xml_str
            if self.collector_version and self.collector_version != exist_dict.get("family"):
                return xml_str
            if self.collector_version == "ipv4" and self.collector_ip != exist_dict.get("ipv4Addr"):
                return xml_str
            if self.collector_version == "ipv6" and self.collector_ip != exist_dict.get("ipv6Addr"):
                return xml_str
            if self.collector_ip_vpn and self.collector_ip_vpn != exist_dict.get("vrfName"):
                return xml_str
            if self.collector_udp_port and self.collector_udp_port != exist_dict.get("port"):
                return xml_str
            if self.collector_datagram_size and self.collector_datagram_size != exist_dict.get("datagramSize"):
                return xml_str
            if self.collector_meth and self.collector_meth != exist_dict.get("meth"):
                return xml_str
            if self.collector_description and self.collector_description != exist_dict.get("description"):
                return xml_str
            change = True

        if not change:
            return xml_str

        # update or delete
        if self.state == "absent":
            xml_str += '<collectors><collector operation="delete"><collectorID>%s</collectorID>' % self.collector_id
            self.updates_cmd.append("undo collector %s" % self.collector_id)
        else:
            xml_str += '<collectors><collector operation="merge"><collectorID>%s</collectorID>' % self.collector_id
            cmd = "sflow collector %s" % self.collector_id
            xml_str += '<family>%s</family>' % self.collector_version
            if self.collector_version == "ipv4":
                cmd += " ip %s" % self.collector_ip
                xml_str += '<ipv4Addr>%s</ipv4Addr>' % self.collector_ip
            else:
                cmd += " ipv6 %s" % self.collector_ip
                xml_str += '<ipv6Addr>%s</ipv6Addr>' % self.collector_ip
            if self.collector_ip_vpn:
                cmd += " vpn-instance %s" % self.collector_ip_vpn
                xml_str += '<vrfName>%s</vrfName>' % self.collector_ip_vpn
            if self.collector_datagram_size:
                cmd += " length %s" % self.collector_datagram_size
                xml_str += '<datagramSize>%s</datagramSize>' % self.collector_datagram_size
            if self.collector_udp_port:
                cmd += " udp-port %s" % self.collector_udp_port
                xml_str += '<port>%s</port>' % self.collector_udp_port
            if self.collector_description:
                cmd += " description %s" % self.collector_description
                xml_str += '<description>%s</description>' % self.collector_description
            else:
                xml_str += '<description></description>'
            if self.collector_meth:
                if self.collector_meth == "enhanced":
                    cmd += " enhanced"
                xml_str += '<meth>%s</meth>' % self.collector_meth
            self.updates_cmd.append(cmd)

        xml_str += "</collector></collectors>"

        return xml_str

    def config_sampling(self):
        """configure sflow sampling on an interface"""

        xml_str = ''
        if not self.sflow_interface:
            return xml_str

        if not self.sflow_dict["sampling"] and self.state == "absent":
            return xml_str

        self.updates_cmd.append("interface %s" % self.sflow_interface)
        if self.state == "present":
            xml_str += '<samplings><sampling operation="merge"><ifName>%s</ifName>' % self.sflow_interface
        else:
            xml_str += '<samplings><sampling operation="delete"><ifName>%s</ifName>' % self.sflow_interface

        # sample_collector
        if self.sample_collector:
            if self.sflow_dict["sampling"].get("collectorID") \
                    and self.sflow_dict["sampling"].get("collectorID") != "invalid":
                existing = self.sflow_dict["sampling"].get("collectorID").split(',')
            else:
                existing = list()

            if self.state == "present":
                diff = list(set(self.sample_collector) - set(existing))
                if diff:
                    self.updates_cmd.append(
                        "sflow sampling collector %s" % ' '.join(diff))
                    new_set = list(self.sample_collector + existing)
                    xml_str += '<collectorID>%s</collectorID>' % ','.join(list(set(new_set)))
            else:
                same = list(set(self.sample_collector) & set(existing))
                if same:
                    self.updates_cmd.append(
                        "undo sflow sampling collector %s" % ' '.join(same))
                    xml_str += '<collectorID>%s</collectorID>' % ','.join(list(set(same)))

        # sample_rate
        if self.sample_rate:
            exist = bool(self.sample_rate == self.sflow_dict["sampling"].get("rate"))
            if self.state == "present" and not exist:
                self.updates_cmd.append(
                    "sflow sampling rate %s" % self.sample_rate)
                xml_str += '<rate>%s</rate>' % self.sample_rate
            elif self.state == "absent" and exist:
                self.updates_cmd.append(
                    "undo sflow sampling rate %s" % self.sample_rate)
                xml_str += '<rate>%s</rate>' % self.sample_rate

        # sample_length
        if self.sample_length:
            exist = bool(self.sample_length == self.sflow_dict["sampling"].get("length"))
            if self.state == "present" and not exist:
                self.updates_cmd.append(
                    "sflow sampling length %s" % self.sample_length)
                xml_str += '<length>%s</length>' % self.sample_length
            elif self.state == "absent" and exist:
                self.updates_cmd.append(
                    "undo sflow sampling length %s" % self.sample_length)
                xml_str += '<length>%s</length>' % self.sample_length

        # sample_direction
        if self.sample_direction:
            direction = list()
            if self.sample_direction == "both":
                direction = ["inbound", "outbound"]
            else:
                direction.append(self.sample_direction)
            existing = list()
            if self.sflow_dict["sampling"].get("direction"):
                if self.sflow_dict["sampling"].get("direction") == "both":
                    existing = ["inbound", "outbound"]
                else:
                    existing.append(
                        self.sflow_dict["sampling"].get("direction"))

            if self.state == "present":
                diff = list(set(direction) - set(existing))
                if diff:
                    new_set = list(set(direction + existing))
                    self.updates_cmd.append(
                        "sflow sampling %s" % ' '.join(diff))
                    if len(new_set) > 1:
                        new_dir = "both"
                    else:
                        new_dir = new_set[0]
                    xml_str += '<direction>%s</direction>' % new_dir
            else:
                same = list(set(existing) & set(direction))
                if same:
                    self.updates_cmd.append("undo sflow sampling %s" % ' '.join(same))
                    if len(same) > 1:
                        del_dir = "both"
                    else:
                        del_dir = same[0]
                    xml_str += '<direction>%s</direction>' % del_dir

        if xml_str.endswith("</ifName>"):
            self.updates_cmd.pop()
            return ""

        xml_str += '</sampling></samplings>'

        return xml_str

    def config_counter(self):
        """configures sflow counter on an interface"""

        xml_str = ''
        if not self.sflow_interface:
            return xml_str

        if not self.sflow_dict["counter"] and self.state == "absent":
            return xml_str

        self.updates_cmd.append("interface %s" % self.sflow_interface)
        if self.state == "present":
            xml_str += '<counters><counter operation="merge"><ifName>%s</ifName>' % self.sflow_interface
        else:
            xml_str += '<counters><counter operation="delete"><ifName>%s</ifName>' % self.sflow_interface

        # counter_collector
        if self.counter_collector:
            if self.sflow_dict["counter"].get("collectorID") \
                    and self.sflow_dict["counter"].get("collectorID") != "invalid":
                existing = self.sflow_dict["counter"].get("collectorID").split(',')
            else:
                existing = list()

            if self.state == "present":
                diff = list(set(self.counter_collector) - set(existing))
                if diff:
                    self.updates_cmd.append("sflow counter collector %s" % ' '.join(diff))
                    new_set = list(self.counter_collector + existing)
                    xml_str += '<collectorID>%s</collectorID>' % ','.join(list(set(new_set)))
            else:
                same = list(set(self.counter_collector) & set(existing))
                if same:
                    self.updates_cmd.append(
                        "undo sflow counter collector %s" % ' '.join(same))
                    xml_str += '<collectorID>%s</collectorID>' % ','.join(list(set(same)))

        # counter_interval
        if self.counter_interval:
            exist = bool(self.counter_interval == self.sflow_dict["counter"].get("interval"))
            if self.state == "present" and not exist:
                self.updates_cmd.append(
                    "sflow counter interval %s" % self.counter_interval)
                xml_str += '<interval>%s</interval>' % self.counter_interval
            elif self.state == "absent" and exist:
                self.updates_cmd.append(
                    "undo sflow counter interval %s" % self.counter_interval)
                xml_str += '<interval>%s</interval>' % self.counter_interval

        if xml_str.endswith("</ifName>"):
            self.updates_cmd.pop()
            return ""

        xml_str += '</counter></counters>'

        return xml_str

    def config_export(self):
        """configure sflow export"""

        xml_str = ''
        if not self.export_route:
            return xml_str

        if self.export_route == "enable":
            if self.sflow_dict["export"] and self.sflow_dict["export"].get("ExportRoute") == "disable":
                xml_str = '<exports><export operation="delete"><ExportRoute>disable</ExportRoute></export></exports>'
                self.updates_cmd.append("undo sflow export extended-route-data disable")
        else:   # disable
            if not self.sflow_dict["export"] or self.sflow_dict["export"].get("ExportRoute") != "disable":
                xml_str = '<exports><export operation="create"><ExportRoute>disable</ExportRoute></export></exports>'
                self.updates_cmd.append("sflow export extended-route-data disable")

        return xml_str

    def config_assign(self):
        """configure assign"""

        # assign sflow management-plane export rate-limit rate-limit [ slot slot-id ]
        if self.rate_limit:
            cmd = "assign sflow management-plane export rate-limit %s" % self.rate_limit
            if self.rate_limit_slot:
                cmd += " slot %s" % self.rate_limit_slot
            exist = is_config_exist(self.config, cmd)
            if self.state == "present" and not exist:
                self.cli_add_command(cmd)
            elif self.state == "absent" and exist:
                self.cli_add_command(cmd, undo=True)

        # assign forward enp sflow enable slot { slot-id | all }
        if self.forward_enp_slot:
            cmd = "assign forward enp sflow enable slot %s" % self.forward_enp_slot
            exist = is_config_exist(self.config, cmd)
            if self.state == "present" and not exist:
                self.cli_add_command(cmd)
            elif self.state == "absent" and exist:
                self.cli_add_command(cmd, undo=True)

    def netconf_load_config(self, xml_str):
        """load sflow config by netconf"""

        if not xml_str:
            return

        xml_cfg = """
            <config>
            <sflow xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
            %s
            </sflow>
            </config>""" % xml_str

        self.netconf_set_config(xml_cfg, "SET_SFLOW")
        self.changed = True

    def check_params(self):
        """Check all input params"""

        # check agent_ip
        if self.agent_ip:
            self.agent_ip = self.agent_ip.upper()
            if not check_ip_addr(self.agent_ip):
                self.module.fail_json(msg="Error: agent_ip is invalid.")

        # check source_ip
        if self.source_ip:
            self.source_ip = self.source_ip.upper()
            if not check_ip_addr(self.source_ip):
                self.module.fail_json(msg="Error: source_ip is invalid.")

        # check collector
        if self.collector_id:
            # check collector_ip and collector_ip_vpn
            if self.collector_ip:
                self.collector_ip = self.collector_ip.upper()
                if not check_ip_addr(self.collector_ip):
                    self.module.fail_json(
                        msg="Error: collector_ip is invalid.")
                if self.collector_ip_vpn and not is_valid_ip_vpn(self.collector_ip_vpn):
                    self.module.fail_json(
                        msg="Error: collector_ip_vpn is invalid.")

            # check collector_datagram_size ranges from 1024 to 8100
            if self.collector_datagram_size:
                if not self.collector_datagram_size.isdigit():
                    self.module.fail_json(
                        msg="Error: collector_datagram_size is not digit.")
                if int(self.collector_datagram_size) < 1024 or int(self.collector_datagram_size) > 8100:
                    self.module.fail_json(
                        msg="Error: collector_datagram_size is not ranges from 1024 to 8100.")

            # check collector_udp_port ranges from 1 to 65535
            if self.collector_udp_port:
                if not self.collector_udp_port.isdigit():
                    self.module.fail_json(
                        msg="Error: collector_udp_port is not digit.")
                if int(self.collector_udp_port) < 1 or int(self.collector_udp_port) > 65535:
                    self.module.fail_json(
                        msg="Error: collector_udp_port is not ranges from 1 to 65535.")

            # check collector_description 1 to 255 case-sensitive characters
            if self.collector_description:
                if self.collector_description.count(" "):
                    self.module.fail_json(
                        msg="Error: collector_description should without spaces.")
                if len(self.collector_description) < 1 or len(self.collector_description) > 255:
                    self.module.fail_json(
                        msg="Error: collector_description is not ranges from 1 to 255.")

        # check sflow_interface
        if self.sflow_interface:
            intf_type = get_interface_type(self.sflow_interface)
            if not intf_type:
                self.module.fail_json(msg="Error: intf_type is invalid.")
            if intf_type not in ['ge', '10ge', '25ge', '4x10ge', '40ge', '100ge', 'eth-trunk']:
                self.module.fail_json(
                    msg="Error: interface %s is not support sFlow." % self.sflow_interface)

            # check sample_collector
            if self.sample_collector:
                self.sample_collector.sort()
                if self.sample_collector not in [["1"], ["2"], ["1", "2"]]:
                    self.module.fail_json(
                        msg="Error: sample_collector is invalid.")

            # check sample_rate ranges from 1 to 4294967295
            if self.sample_rate:
                if not self.sample_rate.isdigit():
                    self.module.fail_json(
                        msg="Error: sample_rate is not digit.")
                if int(self.sample_rate) < 1 or int(self.sample_rate) > 4294967295:
                    self.module.fail_json(
                        msg="Error: sample_rate is not ranges from 1 to 4294967295.")

            # check sample_length ranges from 18 to 512
            if self.sample_length:
                if not self.sample_length.isdigit():
                    self.module.fail_json(
                        msg="Error: sample_rate is not digit.")
                if int(self.sample_length) < 18 or int(self.sample_length) > 512:
                    self.module.fail_json(
                        msg="Error: sample_length is not ranges from 18 to 512.")

            # check counter_collector
            if self.counter_collector:
                self.counter_collector.sort()
                if self.counter_collector not in [["1"], ["2"], ["1", "2"]]:
                    self.module.fail_json(
                        msg="Error: counter_collector is invalid.")

            # counter_interval ranges from 10 to 4294967295
            if self.counter_interval:
                if not self.counter_interval.isdigit():
                    self.module.fail_json(
                        msg="Error: counter_interval is not digit.")
                if int(self.counter_interval) < 10 or int(self.counter_interval) > 4294967295:
                    self.module.fail_json(
                        msg="Error: sample_length is not ranges from 10 to 4294967295.")

        # check rate_limit ranges from 100 to 1500 and check rate_limit_slot
        if self.rate_limit:
            if not self.rate_limit.isdigit():
                self.module.fail_json(msg="Error: rate_limit is not digit.")
            if int(self.rate_limit) < 100 or int(self.rate_limit) > 1500:
                self.module.fail_json(
                    msg="Error: rate_limit is not ranges from 100 to 1500.")
            if self.rate_limit_slot and not self.rate_limit_slot.isdigit():
                self.module.fail_json(
                    msg="Error: rate_limit_slot is not digit.")

        # check forward_enp_slot
        if self.forward_enp_slot:
            self.forward_enp_slot.lower()
            if not self.forward_enp_slot.isdigit() and self.forward_enp_slot != "all":
                self.module.fail_json(
                    msg="Error: forward_enp_slot is invalid.")

    def get_proposed(self):
        """get proposed info"""

        # base config
        if self.agent_ip:
            self.proposed["agent_ip"] = self.agent_ip
        if self.source_ip:
            self.proposed["source_ip"] = self.source_ip
        if self.export_route:
            self.proposed["export_route"] = self.export_route
        if self.rate_limit:
            self.proposed["rate_limit"] = self.rate_limit
            self.proposed["rate_limit_slot"] = self.rate_limit_slot
        if self.forward_enp_slot:
            self.proposed["forward_enp_slot"] = self.forward_enp_slot
        if self.collector_id:
            self.proposed["collector_id"] = self.collector_id
            if self.collector_ip:
                self.proposed["collector_ip"] = self.collector_ip
                self.proposed["collector_ip_vpn"] = self.collector_ip_vpn
            if self.collector_datagram_size:
                self.proposed[
                    "collector_datagram_size"] = self.collector_datagram_size
            if self.collector_udp_port:
                self.proposed["collector_udp_port"] = self.collector_udp_port
            if self.collector_meth:
                self.proposed["collector_meth"] = self.collector_meth
            if self.collector_description:
                self.proposed[
                    "collector_description"] = self.collector_description

        # sample and counter config
        if self.sflow_interface:
            self.proposed["sflow_interface"] = self.sflow_interface
            if self.sample_collector:
                self.proposed["sample_collector"] = self.sample_collector
            if self.sample_rate:
                self.proposed["sample_rate"] = self.sample_rate
            if self.sample_length:
                self.proposed["sample_length"] = self.sample_length
            if self.sample_direction:
                self.proposed["sample_direction"] = self.sample_direction
            if self.counter_collector:
                self.proposed["counter_collector"] = self.counter_collector
            if self.counter_interval:
                self.proposed["counter_interval"] = self.counter_interval

        self.proposed["state"] = self.state

    def get_existing(self):
        """get existing info"""

        if self.config:
            if self.rate_limit:
                self.existing["rate_limit"] = get_rate_limit(self.config)
            if self.forward_enp_slot:
                self.existing["forward_enp_slot"] = get_forward_enp(
                    self.config)

        if not self.sflow_dict:
            return

        if self.agent_ip:
            self.existing["agent"] = self.sflow_dict["agent"]
        if self.source_ip:
            self.existing["source"] = self.sflow_dict["source"]
        if self.collector_id:
            self.existing["collector"] = self.sflow_dict["collector"]
        if self.export_route:
            self.existing["export"] = self.sflow_dict["export"]

        if self.sflow_interface:
            self.existing["sampling"] = self.sflow_dict["sampling"]
            self.existing["counter"] = self.sflow_dict["counter"]

    def get_end_state(self):
        """get end state info"""

        config = self.get_current_config()
        if config:
            if self.rate_limit:
                self.end_state["rate_limit"] = get_rate_limit(config)
            if self.forward_enp_slot:
                self.end_state["forward_enp_slot"] = get_forward_enp(config)

        sflow_dict = self.get_sflow_dict()
        if not sflow_dict:
            return

        if self.agent_ip:
            self.end_state["agent"] = sflow_dict["agent"]
        if self.source_ip:
            self.end_state["source"] = sflow_dict["source"]
        if self.collector_id:
            self.end_state["collector"] = sflow_dict["collector"]
        if self.export_route:
            self.end_state["export"] = sflow_dict["export"]

        if self.sflow_interface:
            self.end_state["sampling"] = sflow_dict["sampling"]
            self.end_state["counter"] = sflow_dict["counter"]

    def work(self):
        """worker"""

        self.check_params()
        self.sflow_dict = self.get_sflow_dict()
        self.config = self.get_current_config()
        self.get_existing()
        self.get_proposed()

        # deal present or absent
        xml_str = ''
        if self.export_route:
            xml_str += self.config_export()
        if self.agent_ip:
            xml_str += self.config_agent()
        if self.source_ip:
            xml_str += self.config_source()

        if self.state == "present":
            if self.collector_id and self.collector_ip:
                xml_str += self.config_collector()
            if self.sflow_interface:
                xml_str += self.config_sampling()
                xml_str += self.config_counter()
        else:
            if self.sflow_interface:
                xml_str += self.config_sampling()
                xml_str += self.config_counter()
            if self.collector_id:
                xml_str += self.config_collector()

        if self.rate_limit or self.forward_enp_slot:
            self.config_assign()

        if self.commands:
            self.cli_load_config(self.commands)
            self.changed = True

        if xml_str:
            self.netconf_load_config(xml_str)
            self.changed = True

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
        agent_ip=dict(required=False, type='str'),
        source_ip=dict(required=False, type='str'),
        export_route=dict(required=False, type='str',
                          choices=['enable', 'disable']),
        rate_limit=dict(required=False, type='str'),
        rate_limit_slot=dict(required=False, type='str'),
        forward_enp_slot=dict(required=False, type='str'),
        collector_id=dict(required=False, type='str', choices=['1', '2']),
        collector_ip=dict(required=False, type='str'),
        collector_ip_vpn=dict(required=False, type='str'),
        collector_datagram_size=dict(required=False, type='str'),
        collector_udp_port=dict(required=False, type='str'),
        collector_meth=dict(required=False, type='str',
                            choices=['meth', 'enhanced']),
        collector_description=dict(required=False, type='str'),
        sflow_interface=dict(required=False, type='str'),
        sample_collector=dict(required=False, type='list'),
        sample_rate=dict(required=False, type='str'),
        sample_length=dict(required=False, type='str'),
        sample_direction=dict(required=False, type='str',
                              choices=['inbound', 'outbound', 'both']),
        counter_collector=dict(required=False, type='list'),
        counter_interval=dict(required=False, type='str'),
        state=dict(required=False, default='present',
                   choices=['present', 'absent'])
    )

    argument_spec.update(ce_argument_spec)
    module = Sflow(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
