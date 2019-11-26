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
module: ce_bfd_session
version_added: "2.4"
short_description: Manages BFD session configuration on HUAWEI CloudEngine devices.
description:
    - Manages BFD session configuration, creates a BFD session or deletes a specified BFD session
      on HUAWEI CloudEngine devices.
author: QijunPan (@QijunPan)
notes:
  - This module requires the netconf system service be enabled on the remote device being managed.
  - Recommended connection is C(netconf).
  - This module also works with C(local) connections for legacy playbooks.
options:
    session_name:
        description:
            - Specifies the name of a BFD session.
              The value is a string of 1 to 15 case-sensitive characters without spaces.
        required: true
    create_type:
        description:
            - BFD session creation mode, the currently created BFD session
              only supports static or static auto-negotiation mode.
        choices: ['static', 'auto']
        default: static
    addr_type:
        description:
            - Specifies the peer IP address type.
        choices: ['ipv4']
    out_if_name:
        description:
            - Specifies the type and number of the interface bound to the BFD session.
    dest_addr:
        description:
            - Specifies the peer IP address bound to the BFD session.
    src_addr:
        description:
            - Indicates the source IP address carried in BFD packets.
    local_discr:
        version_added: 2.9
        description:
            - The BFD session local identifier does not need to be configured when the mode is auto.
    remote_discr:
        version_added: 2.9
        description:
            - The BFD session remote identifier does not need to be configured when the mode is auto.
    vrf_name:
        description:
            - Specifies the name of a Virtual Private Network (VPN) instance that is bound to a BFD session.
              The value is a string of 1 to 31 case-sensitive characters, spaces not supported.
              When double quotation marks are used around the string, spaces are allowed in the string.
              The value _public_ is reserved and cannot be used as the VPN instance name.
    use_default_ip:
        description:
            - Indicates the default multicast IP address that is bound to a BFD session.
              By default, BFD uses the multicast IP address 224.0.0.184.
              You can set the multicast IP address by running the default-ip-address command.
              The value is a bool type.
        type: bool
        default: 'no'
    state:
        description:
            - Determines whether the config should be present or not on the device.
        default: present
        choices: ['present', 'absent']
"""

EXAMPLES = '''
- name: bfd session module test
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
  - name: Configuring Single-hop BFD for Detecting Faults on a Layer 2 Link
    ce_bfd_session:
      session_name: bfd_l2link
      use_default_ip: true
      out_if_name: 10GE1/0/1
      local_discr: 163
      remote_discr: 163
      provider: '{{ cli }}'

  - name: Configuring Single-Hop BFD on a VLANIF Interface
    ce_bfd_session:
      session_name: bfd_vlanif
      dest_addr: 10.1.1.6
      out_if_name: Vlanif100
      local_discr: 163
      remote_discr: 163
      provider: '{{ cli }}'

  - name: Configuring Multi-Hop BFD
    ce_bfd_session:
      session_name: bfd_multi_hop
      dest_addr: 10.1.1.1
      local_discr: 163
      remote_discr: 163
      provider: '{{ cli }}'
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {
        "addr_type": null,
        "create_type": null,
        "dest_addr": null,
        "out_if_name": "10GE1/0/1",
        "session_name": "bfd_l2link",
        "src_addr": null,
        "state": "present",
        "use_default_ip": true,
        "vrf_name": null
    }
existing:
    description: k/v pairs of existing configuration
    returned: always
    type: dict
    sample: {
        "session": {}
    }
end_state:
    description: k/v pairs of configuration after module execution
    returned: always
    type: dict
    sample: {
        "session": {
            "addrType": "IPV4",
            "createType": "SESS_STATIC",
            "destAddr": null,
            "outIfName": "10GE1/0/1",
            "sessName": "bfd_l2link",
            "srcAddr": null,
            "useDefaultIp": "true",
            "vrfName": null
        }
    }
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: [
        "bfd bfd_l2link bind peer-ip default-ip interface 10ge1/0/1"
    ]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
'''

import sys
import socket
from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, set_nc_config, ce_argument_spec, check_ip_addr


CE_NC_GET_BFD = """
    <filter type="subtree">
      <bfd xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <bfdSchGlobal>
          <bfdEnable></bfdEnable>
          <defaultIp></defaultIp>
        </bfdSchGlobal>
        <bfdCfgSessions>
          <bfdCfgSession>
            <sessName>%s</sessName>
            <createType></createType>
            <addrType></addrType>
            <outIfName></outIfName>
            <destAddr></destAddr>
            <localDiscr></localDiscr>
            <remoteDiscr></remoteDiscr>
            <srcAddr></srcAddr>
            <vrfName></vrfName>
            <useDefaultIp></useDefaultIp>
          </bfdCfgSession>
        </bfdCfgSessions>
      </bfd>
    </filter>
"""


def is_valid_ip_vpn(vpname):
    """check ip vpn"""

    if not vpname:
        return False

    if vpname == "_public_":
        return False

    if len(vpname) < 1 or len(vpname) > 31:
        return False

    return True


def check_default_ip(ipaddr):
    """check the default multicast IP address"""

    # The value ranges from 224.0.0.107 to 224.0.0.250
    if not check_ip_addr(ipaddr):
        return False

    if ipaddr.count(".") != 3:
        return False

    ips = ipaddr.split(".")
    if ips[0] != "224" or ips[1] != "0" or ips[2] != "0":
        return False

    if not ips[3].isdigit() or int(ips[3]) < 107 or int(ips[3]) > 250:
        return False

    return True


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


class BfdSession(object):
    """Manages BFD Session"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.__init_module__()

        # module input info
        self.session_name = self.module.params['session_name']
        self.create_type = self.module.params['create_type']
        self.addr_type = self.module.params['addr_type']
        self.out_if_name = self.module.params['out_if_name']
        self.dest_addr = self.module.params['dest_addr']
        self.src_addr = self.module.params['src_addr']
        self.vrf_name = self.module.params['vrf_name']
        self.use_default_ip = self.module.params['use_default_ip']
        self.state = self.module.params['state']
        self.local_discr = self.module.params['local_discr']
        self.remote_discr = self.module.params['remote_discr']
        # host info
        self.host = self.module.params['host']
        self.username = self.module.params['username']
        self.port = self.module.params['port']

        # state
        self.changed = False
        self.bfd_dict = dict()
        self.updates_cmd = list()
        self.commands = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def __init_module__(self):
        """init module"""

        mutually_exclusive = [('use_default_ip', 'dest_addr')]
        self.module = AnsibleModule(argument_spec=self.spec,
                                    mutually_exclusive=mutually_exclusive,
                                    supports_check_mode=True)

    def get_bfd_dict(self):
        """bfd config dict"""

        bfd_dict = dict()
        bfd_dict["global"] = dict()
        bfd_dict["session"] = dict()
        conf_str = CE_NC_GET_BFD % self.session_name

        xml_str = get_nc_config(self.module, conf_str)
        if "<data/>" in xml_str:
            return bfd_dict

        xml_str = xml_str.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")
        root = ElementTree.fromstring(xml_str)

        # get bfd global info
        glb = root.find("bfd/bfdSchGlobal")
        if glb:
            for attr in glb:
                bfd_dict["global"][attr.tag] = attr.text

        # get bfd session info
        sess = root.find("bfd/bfdCfgSessions/bfdCfgSession")
        if sess:
            for attr in sess:
                bfd_dict["session"][attr.tag] = attr.text

        return bfd_dict

    def is_session_match(self):
        """is bfd session match"""

        if not self.bfd_dict["session"] or not self.session_name:
            return False

        session = self.bfd_dict["session"]
        if self.session_name != session.get("sessName", ""):
            return False

        if self.create_type and self.create_type.upper() not in session.get("createType", "").upper():
            return False

        if self.addr_type and self.addr_type != session.get("addrType").lower():
            return False

        if self.dest_addr and self.dest_addr != session.get("destAddr"):
            return False

        if self.src_addr and self.src_addr != session.get("srcAddr"):
            return False

        if self.out_if_name:
            if not session.get("outIfName"):
                return False
            if self.out_if_name.replace(" ", "").lower() != session.get("outIfName").replace(" ", "").lower():
                return False

        if self.vrf_name and self.vrf_name != session.get("vrfName"):
            return False

        if str(self.use_default_ip).lower() != session.get("useDefaultIp"):
            return False

        if self.create_type == "static" and self.state == "present":
            if str(self.local_discr).lower() != session.get("localDiscr", ""):
                return False
            if str(self.remote_discr).lower() != session.get("remoteDiscr", ""):
                return False

        return True

    def config_session(self):
        """configures bfd session"""

        xml_str = ""
        cmd_list = list()
        discr = list()

        if not self.session_name:
            return xml_str

        if self.bfd_dict["global"].get("bfdEnable", "false") != "true":
            self.module.fail_json(msg="Error: Please enable BFD globally first.")

        xml_str = "<sessName>%s</sessName>" % self.session_name
        cmd_session = "bfd %s" % self.session_name

        if self.state == "present":
            if not self.bfd_dict["session"]:
                # Parameter check
                if not self.dest_addr and not self.use_default_ip:
                    self.module.fail_json(
                        msg="Error: dest_addr or use_default_ip must be set when bfd session is creating.")

                # Creates a BFD session
                if self.create_type == "auto":
                    xml_str += "<createType>SESS_%s</createType>" % self.create_type.upper()
                else:
                    xml_str += "<createType>SESS_STATIC</createType>"
                xml_str += "<linkType>IP</linkType>"
                cmd_session += " bind"
                if self.addr_type:
                    xml_str += "<addrType>%s</addrType>" % self.addr_type.upper()
                else:
                    xml_str += "<addrType>IPV4</addrType>"
                if self.dest_addr:
                    xml_str += "<destAddr>%s</destAddr>" % self.dest_addr
                    cmd_session += " peer-%s %s" % ("ipv6" if self.addr_type == "ipv6" else "ip", self.dest_addr)
                if self.use_default_ip:
                    xml_str += "<useDefaultIp>%s</useDefaultIp>" % str(self.use_default_ip).lower()
                    cmd_session += " peer-ip default-ip"
                if self.vrf_name:
                    xml_str += "<vrfName>%s</vrfName>" % self.vrf_name
                    cmd_session += " vpn-instance %s" % self.vrf_name
                if self.out_if_name:
                    xml_str += "<outIfName>%s</outIfName>" % self.out_if_name
                    cmd_session += " interface %s" % self.out_if_name.lower()
                if self.src_addr:
                    xml_str += "<srcAddr>%s</srcAddr>" % self.src_addr
                    cmd_session += " source-%s %s" % ("ipv6" if self.addr_type == "ipv6" else "ip", self.src_addr)

                if self.create_type == "auto":
                    cmd_session += " auto"
                else:
                    xml_str += "<localDiscr>%s</localDiscr>" % self.local_discr
                    discr.append("discriminator local %s" % self.local_discr)
                    xml_str += "<remoteDiscr>%s</remoteDiscr>" % self.remote_discr
                    discr.append("discriminator remote %s" % self.remote_discr)

            elif not self.is_session_match():
                # Bfd session is not match
                self.module.fail_json(msg="Error: The specified BFD configuration view has been created.")
            else:
                pass
        else:   # absent
            if not self.bfd_dict["session"]:
                self.module.fail_json(msg="Error: BFD session is not exist.")
            if not self.is_session_match():
                self.module.fail_json(msg="Error: BFD session parameter is invalid.")

        if self.state == "present":
            if xml_str.endswith("</sessName>"):
                # no config update
                return ""
            else:
                cmd_list.insert(0, cmd_session)
                cmd_list.extend(discr)
                self.updates_cmd.extend(cmd_list)
                return '<bfdCfgSessions><bfdCfgSession operation="merge">' + xml_str\
                       + '</bfdCfgSession></bfdCfgSessions>'
        else:   # absent
            cmd_list.append("undo " + cmd_session)
            self.updates_cmd.extend(cmd_list)
            return '<bfdCfgSessions><bfdCfgSession operation="delete">' + xml_str\
                   + '</bfdCfgSession></bfdCfgSessions>'

    def netconf_load_config(self, xml_str):
        """load bfd config by netconf"""

        if not xml_str:
            return

        xml_cfg = """
            <config>
            <bfd xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
            %s
            </bfd>
            </config>""" % xml_str
        set_nc_config(self.module, xml_cfg)
        self.changed = True

    def check_params(self):
        """Check all input params"""

        # check session_name
        if not self.session_name:
            self.module.fail_json(msg="Error: Missing required arguments: session_name.")

        if self.session_name:
            if len(self.session_name) < 1 or len(self.session_name) > 15:
                self.module.fail_json(msg="Error: Session name is invalid.")

        # check local_discr
        # check remote_discr

        if self.local_discr:
            if self.local_discr < 1 or self.local_discr > 16384:
                self.module.fail_json(msg="Error: Session local_discr is not ranges from 1 to 16384.")
        if self.remote_discr:
            if self.remote_discr < 1 or self.remote_discr > 4294967295:
                self.module.fail_json(msg="Error: Session remote_discr is not ranges from 1 to 4294967295.")

        if self.state == "present" and self.create_type == "static":
            if not self.local_discr:
                self.module.fail_json(msg="Error: Missing required arguments: local_discr.")
            if not self.remote_discr:
                self.module.fail_json(msg="Error: Missing required arguments: remote_discr.")

        # check out_if_name
        if self.out_if_name:
            if not get_interface_type(self.out_if_name):
                self.module.fail_json(msg="Error: Session out_if_name is invalid.")

        # check dest_addr
        if self.dest_addr:
            if not check_ip_addr(self.dest_addr):
                self.module.fail_json(msg="Error: Session dest_addr is invalid.")

        # check src_addr
        if self.src_addr:
            if not check_ip_addr(self.src_addr):
                self.module.fail_json(msg="Error: Session src_addr is invalid.")

        # check vrf_name
        if self.vrf_name:
            if not is_valid_ip_vpn(self.vrf_name):
                self.module.fail_json(msg="Error: Session vrf_name is invalid.")
            if not self.dest_addr:
                self.module.fail_json(msg="Error: vrf_name and dest_addr must set at the same time.")

        # check use_default_ip
        if self.use_default_ip and not self.out_if_name:
            self.module.fail_json(msg="Error: use_default_ip and out_if_name must set at the same time.")

    def get_proposed(self):
        """get proposed info"""

        # base config
        self.proposed["session_name"] = self.session_name
        self.proposed["create_type"] = self.create_type
        self.proposed["addr_type"] = self.addr_type
        self.proposed["out_if_name"] = self.out_if_name
        self.proposed["dest_addr"] = self.dest_addr
        self.proposed["src_addr"] = self.src_addr
        self.proposed["vrf_name"] = self.vrf_name
        self.proposed["use_default_ip"] = self.use_default_ip
        self.proposed["state"] = self.state
        self.proposed["local_discr"] = self.local_discr
        self.proposed["remote_discr"] = self.remote_discr

    def get_existing(self):
        """get existing info"""

        if not self.bfd_dict:
            return

        self.existing["session"] = self.bfd_dict.get("session")

    def get_end_state(self):
        """get end state info"""

        bfd_dict = self.get_bfd_dict()
        if not bfd_dict:
            return

        self.end_state["session"] = bfd_dict.get("session")
        if self.end_state == self.existing:
            self.changed = False

    def work(self):
        """worker"""

        self.check_params()
        self.bfd_dict = self.get_bfd_dict()
        self.get_existing()
        self.get_proposed()

        # deal present or absent
        xml_str = ''
        if self.session_name:
            xml_str += self.config_session()

        # update to device
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
        session_name=dict(required=True, type='str'),
        create_type=dict(required=False, default='static', type='str', choices=['static', 'auto']),
        addr_type=dict(required=False, type='str', choices=['ipv4']),
        out_if_name=dict(required=False, type='str'),
        dest_addr=dict(required=False, type='str'),
        src_addr=dict(required=False, type='str'),
        vrf_name=dict(required=False, type='str'),
        use_default_ip=dict(required=False, type='bool', default=False),
        state=dict(required=False, default='present', choices=['present', 'absent']),
        local_discr=dict(required=False, type='int'),
        remote_discr=dict(required=False, type='int')
    )

    argument_spec.update(ce_argument_spec)
    module = BfdSession(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
