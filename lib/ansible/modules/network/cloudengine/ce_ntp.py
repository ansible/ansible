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

DOCUMENTATION = '''
---
module: ce_ntp
version_added: "2.2"
short_description: Manages core NTP configuration.
description:
    - Manages core NTP configuration.
extends_documentation_fragment: CloudEngine
author:
    - author: Zhou Zhijin (@CloudEngine-Ansible)
options:
    server or peer:
        description:
            - Network address of NTP server or peer.
        required: true
        default: null
    key_id:
        description:
            - Authentication key identifier to use with
              given NTP server or peer.
        required: false
        default: null
    is_preferred:
        description:
            - Makes given NTP server or peer the preferred
              NTP server or peer for the device.
        required: false
        default: null
        choices: ['true', 'false']
    vpn_name:
        description:
            - Makes the device communicate with the given
              NTP server or peer over a specific vpn.
        required: false
        default: null
    source_int:
        description:
            - Local source interface from which NTP messages are sent.
              Must be fully qualified interface name, i.e. 40GE1/0/22, vlanif10.
        required: false
        default: null
    state:
        description:
            - Manage the state of the resource.
        required: false
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
# Set NTP Server with parameters
- ce_ntp: server=192.8.2.6 [vpn_name=js | source_int=vlanif4001 | is_preferred=true | key_id=32]
# Set NTP Peer with parameters
- ce_ntp: peer=192.8.2.6 [vpn_name=js | source_int=vlanif4001 | is_preferred=true | key_id=32]
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"server": "2.2.2.2",        "key_id": "48",
             "is_preferred": "true",     "vpn_name":"js"
             "source_int": "vlanif4002", "state":"present"}
existing:
    description:
        - k/v pairs of existing ntp server/peer
    type: dict
    sample: {"server": "2.2.2.2",        "key_id": "32",
            "is_preferred": "false",     "vpn_name":"js"
            "source_int": "vlanif4002"}
end_state:
    description: k/v pairs of ntp info after module execution
    returned: always
    type: dict
    sample: {"server": "2.2.2.2",        "key_id": "48",
             "is_preferred": "true",     "vpn_name":"js"
             "source_int": "vlanif4002"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["ntp server 2.2.2.2 authentication-keyid 48 source-interface vlanif4002 vpn-instance js preferred"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

import re
import datetime
import copy
from ansible.module_utils.network import NetworkModule
from ansible.module_utils.cloudengine import get_netconf
from xml.etree import ElementTree

HAS_NCCLIENT = False
try:
    from ncclient.operations.rpc import RPCError
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False

CE_NC_GET_NTP_CONFIG = """
<filter type="subtree">
  <ntp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <ntpUCastCfgs>
      <ntpUCastCfg>
        <addrFamily></addrFamily>
        <vpnName></vpnName>
        <ifName></ifName>
        <ipv4Addr></ipv4Addr>
        <ipv6Addr></ipv6Addr>
        <type></type>
        <isPreferred></isPreferred>
        <keyId></keyId>
      </ntpUCastCfg>
    </ntpUCastCfgs>
  </ntp>
</filter>
"""

CE_NC_MERGE_NTP_CONFIG = """
<config>
  <ntp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <ntpUCastCfgs>
      <ntpUCastCfg operation="merge">
        <addrFamily>%s</addrFamily>
        <ipv4Addr>%s</ipv4Addr>
        <ipv6Addr>%s</ipv6Addr>
        <type>%s</type>
        <vpnName>%s</vpnName>
        <keyId>%s</keyId>
        <isPreferred>%s</isPreferred>
        <ifName>%s</ifName>
        <neid>0-0</neid>
      </ntpUCastCfg>
    </ntpUCastCfgs>
  </ntp>
</config>
"""

CE_NC_DELETE_NTP_CONFIG = """
<config>
  <ntp xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <ntpUCastCfgs>
      <ntpUCastCfg operation="delete">
        <addrFamily>%s</addrFamily>
        <ipv4Addr>%s</ipv4Addr>
        <ipv6Addr>%s</ipv6Addr>
        <type>%s</type>
        <vpnName>%s</vpnName>
        <neid>0-0</neid>
      </ntpUCastCfg>
    </ntpUCastCfgs>
  </ntp>
</config>
"""


class CE_NTP(object):
    """CE_NTP"""

    def __init__(self, argument_spec):
        self.start_time = datetime.datetime.now()
        self.end_time = None
        self.spec = argument_spec
        self.module = None
        self.netconf = None
        self.init_module()

        # ntp configration info
        self.server = self.module.params['server'] or None
        self.peer = self.module.params['peer'] or None
        self.key_id = self.module.params['key_id']
        self.is_preferred = self.module.params['is_preferred']
        self.vpn_name = self.module.params['vpn_name']
        self.interface = self.module.params['source_int'] or ""
        self.state = self.module.params['state']
        self.ntp_conf = dict()
        self.conf_exsit = False
        self.ip_ver = 'IPv4'

        # host info
        self.host = self.module.params['host']
        self.username = self.module.params['username']
        self.port = self.module.params['port']

        if self.server:
            self.peer_type = 'Server'
            self.address = self.server
        elif self.peer:
            self.peer_type = 'Peer'
            self.address = self.peer
        else:
            self.peer_type = None
            self.address = None

        self.check_params()

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = list()
        self.end_state = list()

        # init netconf connect
        self.init_netconf()
        self.init_data()

    def init_data(self):
        """ init_data"""
        if self.interface is not None:
            self.interface = self.interface.lower()

        if not self.key_id:
            self.key_id = ""

        if not self.is_preferred:
            self.is_preferred = 'false'

    def init_module(self):
        """ init_module"""
        self.mutually_exclusive = [('server', 'peer')]

        self.module = NetworkModule(argument_spec=self.spec, supports_check_mode=True,
                                    mutually_exclusive=self.mutually_exclusive)

    def init_netconf(self):
        """ init_netconf"""

        if HAS_NCCLIENT:
            self.netconf = get_netconf(host=self.host, port=self.port,
                                       username=self.username,
                                       password=self.module.params['password'])
        else:
            self.module.fail_json(
                msg='Error: No ncclient package, please install it.')

    def check_ipaddr_validate(self):
        """ check_ipaddr_validate"""
        rule1 = '(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.'
        rule2 = '(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])'
        ipv4_regex = '%s%s%s%s%s%s' % ('^', rule1, rule1, rule1, rule2, '$')
        ipv6_regex = '^(?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4}$'

        flag = False
        if bool(re.match(ipv4_regex, self.address)):
            flag = True
            self.ip_ver = "IPv4"
            if not self.ntp_ucast_ipv4_validate():
                flag = False

        if bool(re.match(ipv6_regex, self.address)):
            flag = True
            self.ip_ver = "IPv6"

        if not flag:
            if self.peer_type == "Server":
                self.module.fail_json(msg='Illegal server ip-address.')
            else:
                self.module.fail_json(msg='Illegal peer ip-address.')

    def ntp_ucast_ipv4_validate(self):
        """ntp_ucast_ipv4_validate"""
        m = re.findall(r'(.*)\.(.*)\.(.*)\.(.*)', self.address)
        if not m:
            self.module.fail_json(msg='Match ip-address fail.')

        value = ((long(m[0][0])) * 0x1000000) + (long(m[0][1])
                * 0x10000) + (long(m[0][2]) * 0x100) + (long(m[0][3]))
        if (value & (0xff000000) == 0x7f000000) or (value & (0xF0000000) == 0xF0000000) \
                or (value & (0xF0000000) == 0xE0000000) or (value == 0):
            return False
        return True

    def check_params(self):
        """Check all input params"""
        if not self.server and not self.peer:
            self.module.fail_json(
                msg='Please supply the server or peer parameter')

        if self.vpn_name:
            if (len(self.vpn_name) < 1) or (len(self.vpn_name) > 31):
                self.module.fail_json(
                    msg='VPN name length is beetween 1 and 31.')

        if self.address:
            self.check_ipaddr_validate()

    def check_response(self, con_obj, xml_name):
        """Check if response message is already succeed."""

        xml_str = con_obj.xml
        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def netconf_get_config(self, xml_str):
        """ netconf get config """

        try:
            con_obj = self.netconf.get_config(filter=xml_str)
        except RPCError as err:
            self.module.fail_json(msg='Error: %s' % err.message)

        return con_obj

    def netconf_set_config(self, xml_str, xml_name):
        """ netconf set config """

        try:
            con_obj = self.netconf.set_config(config=xml_str)
            self.check_response(con_obj, xml_name)
        except RPCError as err:
            self.module.fail_json(msg='Error: %s' % err.message)

        return con_obj

    def set_ntp(self, *args):

        if self.state == 'present':
            if self.ip_ver == 'IPv4':
                xml_str = CE_NC_MERGE_NTP_CONFIG % (
                    args[0], args[1], '::', args[2], args[3], args[4], args[5], args[6])
            elif self.ip_ver == 'IPv6':
                xml_str = CE_NC_MERGE_NTP_CONFIG % (
                    args[0], '0.0.0.0', args[1], args[2], args[3], args[4], args[5], args[6])
            self.netconf_set_config(xml_str, "NTP_CORE_CONFIG")
        else:
            if self.ip_ver == 'IPv4':
                xml_str = CE_NC_DELETE_NTP_CONFIG % (
                    args[0], args[1], '::', args[2], args[3])
            elif self.ip_ver == 'IPv6':
                xml_str = CE_NC_DELETE_NTP_CONFIG % (
                    args[0], '0.0.0.0', args[1], args[2], args[3])
            self.netconf_set_config(xml_str, "UNDO_NTP_CORE_CONFIG")

    def config_ntp(self):
        """config ntp"""
        if self.state == "present":
            if self.address and not self.conf_exsit:
                self.set_ntp(self.ip_ver, self.address, self.peer_type,
                             self.vpn_name, self.key_id, self.is_preferred, self.interface)
                self.changed = True
        else:
            if self.address:
                self.set_ntp(self.ip_ver, self.address,
                             self.peer_type, self.vpn_name, '', '', '')
                self.changed = True

    def show_result(self):
        """show_result"""
        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        if self.changed:
            self.results['updates'] = self.updates_cmd
        else:
            self.results['updates'] = list()

        self.end_time = datetime.datetime.now()
        self.results['execute_time'] = str(self.end_time - self.start_time)

        self.module.exit_json(**self.results)

    def get_ntp_exist_config(self):
        """get ntp existed config"""
        ntp_config = list()
        conf_str = CE_NC_GET_NTP_CONFIG
        con_obj = self.netconf_get_config(conf_str)

        if "<data/>" in con_obj.xml:
            return ntp_config

        xml_str = con_obj.xml.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

        # get all ntp config info
        root = ElementTree.fromstring(xml_str)
        ntpsite = root.findall("data/ntp/ntpUCastCfgs/ntpUCastCfg")
        for nexthop in ntpsite:
            ntp_dict = dict()
            for ele in nexthop:
                if ele.tag in ["addrFamily", "vpnName", "ifName", "ipv4Addr",
                               "ipv6Addr", "type", "isPreferred", "keyId"]:
                    ntp_dict[ele.tag] = ele.text

            ipAddr = ntp_dict['ipv6Addr']
            if ntp_dict['addrFamily'] == "IPv4":
                ipAddr = ntp_dict['ipv4Addr']
            if ntp_dict['ifName'] == None:
                ntp_dict['ifName'] = ""

            if self.state == "present":
                cur_ntp_cfg = dict(vpn_name=ntp_dict['vpnName'], source_int=ntp_dict['ifName'].lower(), address=ipAddr,
                                   peer_type=ntp_dict['type'], prefer=ntp_dict['isPreferred'], key_id=ntp_dict['keyId'])
                exp_ntp_cfg = dict(vpn_name=self.vpn_name, source_int=self.interface.lower(), address=self.address,
                                   peer_type=self.peer_type, prefer=self.is_preferred, key_id=self.key_id)
                if cmp(cur_ntp_cfg, exp_ntp_cfg) == 0:
                    self.conf_exsit = True

            vpnName = ntp_dict['vpnName']
            if ntp_dict['vpnName'] == "_public_":
                vpnName = None

            ifName = ntp_dict['ifName']
            if ifName == "":
                ifName = None
            if self.peer_type == 'Server':
                ntp_config.append(dict(vpn_name=vpnName,
                                       source_int=ifName, server=ipAddr,
                                       is_preferred=ntp_dict['isPreferred'], key_id=ntp_dict['keyId']))
            else:
                ntp_config.append(dict(vpn_name=vpnName,
                                       source_int=ifName, peer=ipAddr,
                                       is_preferred=ntp_dict['isPreferred'], key_id=ntp_dict['keyId']))

        return ntp_config

    def get_existing(self):
        """get existing info"""
        if self.address:
            self.existing = self.get_ntp_exist_config()

    def get_proposed(self):
        """get proposed info"""
        if self.address:
            vpnName = self.vpn_name
            if vpnName == "_public_":
                vpnName = None

            ifName = self.interface
            if ifName == "":
                ifName = None

            keyId = self.key_id
            if keyId == "":
                keyId = None
            if self.peer_type == 'Server':
                self.proposed = dict(state=self.state, vpn_name=vpnName,
                                     source_int=ifName, server=self.address,
                                     is_preferred=self.is_preferred, key_id=keyId)
            else:
                self.proposed = dict(state=self.state, vpn_name=vpnName,
                                     source_int=ifName, peer=self.address,
                                     is_preferred=self.is_preferred, key_id=keyId)

    def get_end_state(self):
        """get end state info"""
        if self.address:
            self.end_state = self.get_ntp_exist_config()

    def get_update_cmd(self):
        """get_update_cmd"""
        if self.conf_exsit:
            return

        cli_str = ""
        if self.state == "present":
            if self.address:
                if self.peer_type == 'Server':
                    if self.ip_ver == "IPv4":
                        cli_str = "%s %s" % (
                            "ntp unicast-server", self.address)
                    else:
                        cli_str = "%s %s" % (
                            "ntp unicast-server ipv6", self.address)
                elif self.peer_type == 'Peer':
                    if self.ip_ver == "IPv4":
                        cli_str = "%s %s" % ("ntp unicast-peer", self.address)
                    else:
                        cli_str = "%s %s" % (
                            "ntp unicast-peer ipv6", self.address)

                if self.key_id:
                    cli_str = "%s %s %s" % (
                        cli_str, "authentication-keyid", self.key_id)
                if self.interface:
                    cli_str = "%s %s %s" % (
                        cli_str, "source-interface", self.interface)
                if (self.vpn_name) and (self.vpn_name != '_public_'):
                    cli_str = "%s %s %s" % (
                        cli_str, "vpn-instance", self.vpn_name)
                if self.is_preferred == "true":
                    cli_str = "%s %s" % (cli_str, "preferred")
        else:
            if self.address:
                if self.peer_type == 'Server':
                    if self.ip_ver == "IPv4":
                        cli_str = "%s %s" % (
                            "undo ntp unicast-server", self.address)
                    else:
                        cli_str = "%s %s" % (
                            "undo ntp unicast-server ipv6", self.address)
                elif self.peer_type == 'Peer':
                    if self.ip_ver == "IPv4":
                        cli_str = "%s %s" % (
                            "undo ntp unicast-peer", self.address)
                    else:
                        cli_str = "%s %s" % (
                            "undo ntp unicast-peer ipv6", self.address)
                if (self.vpn_name) and (self.vpn_name != '_public_'):
                    cli_str = "%s %s" % (cli_str, self.vpn_name)

        self.updates_cmd.append(cli_str)

    def work(self):
        """work"""
        self.get_existing()
        self.get_proposed()
        self.get_update_cmd()

        self.config_ntp()

        self.get_end_state()
        self.show_result()


def main():
    """ main"""
    argument_spec = dict(
        server=dict(type='str'),
        peer=dict(type='str'),
        key_id=dict(type='str'),
        is_preferred=dict(type='str', choices=['true', 'false']),
        vpn_name=dict(type='str', default='_public_'),
        source_int=dict(type='str'),
        state=dict(choices=['absent', 'present'], default='present'),
    )

    ntp_obj = CE_NTP(argument_spec)
    ntp_obj.work()

if __name__ == '__main__':
    main()
