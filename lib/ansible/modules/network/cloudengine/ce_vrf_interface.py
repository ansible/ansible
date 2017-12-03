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
module: ce_vrf_interface
version_added: "2.4"
short_description: Manages interface specific VPN configuration on HUAWEI CloudEngine switches.
description:
    - Manages interface specific VPN configuration of HUAWEI CloudEngine switches.
author: Zhijin Zhou (@CloudEngine-Ansible)
notes:
    - Ensure that a VPN instance has been created and the IPv4 address family has been enabled for the VPN instance.
options:
    vrf:
        description:
            - VPN instance, the length of vrf name is 1 ~ 31, i.e. "test", but can not be C(_public_).
        required: true
    vpn_interface:
        description:
            - An interface that can binding VPN instance, i.e. 40GE1/0/22, Vlanif10.
              Must be fully qualified interface name.
              Interface types, such as 10GE, 40GE, 100GE, LoopBack, MEth, Tunnel, Vlanif....
        required: true
    state:
        description:
            - Manage the state of the resource.
        required: false
        choices: ['present','absent']
        default: present
'''

EXAMPLES = '''
- name: VRF interface test
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

  - name: "Configure a VPN instance for the interface"
    ce_vrf_interface:
      vpn_interface: 40GE1/0/2
      vrf: test
      state: present
      provider: "{{ cli }}"

  - name: "Disable the association between a VPN instance and an interface"
    ce_vrf_interface:
      vpn_interface: 40GE1/0/2
      vrf: test
      state: absent
      provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {
                "state": "present",
                "vpn_interface": "40GE2/0/17",
                "vrf": "jss"
             }
existing:
    description: k/v pairs of existing attributes on the interface
    returned: verbose mode
    type: dict
    sample: {
                "vpn_interface": "40GE2/0/17",
                "vrf": null
            }
end_state:
    description: k/v pairs of end attributes on the interface
    returned: verbose mode
    type: dict
    sample: {
                "vpn_interface": "40GE2/0/17",
                "vrf": "jss"
            }
updates:
    description: command list sent to the device
    returned: always
    type: list
    sample: [
                "ip binding vpn-instance jss",
            ]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


from xml.etree import ElementTree
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import ce_argument_spec, get_nc_config, set_nc_config

CE_NC_GET_VRF = """
<filter type="subtree">
  <l3vpn xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <l3vpncomm>
      <l3vpnInstances>
        <l3vpnInstance>
          <vrfName>%s</vrfName>
        </l3vpnInstance>
      </l3vpnInstances>
    </l3vpncomm>
  </l3vpn>
</filter>
"""

CE_NC_GET_VRF_INTERFACE = """
<filter type="subtree">
  <l3vpn xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <l3vpncomm>
      <l3vpnInstances>
        <l3vpnInstance>
          <vrfName></vrfName>
          <l3vpnIfs>
            <l3vpnIf>
              <ifName></ifName>
            </l3vpnIf>
          </l3vpnIfs>
        </l3vpnInstance>
      </l3vpnInstances>
    </l3vpncomm>
  </l3vpn>
</filter>
"""

CE_NC_MERGE_VRF_INTERFACE = """
<config>
  <l3vpn xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <l3vpncomm>
      <l3vpnInstances>
        <l3vpnInstance>
          <vrfName>%s</vrfName>
          <l3vpnIfs>
            <l3vpnIf operation="merge">
              <ifName>%s</ifName>
            </l3vpnIf>
          </l3vpnIfs>
        </l3vpnInstance>
      </l3vpnInstances>
    </l3vpncomm>
  </l3vpn>
</config>
"""

CE_NC_GET_INTF = """
<filter type="subtree">
  <ifm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <interfaces>
      <interface>
        <ifName>%s</ifName>
        <isL2SwitchPort></isL2SwitchPort>
      </interface>
    </interfaces>
  </ifm>
</filter>
"""

CE_NC_DEL_INTF_VPN = """
<config>
  <l3vpn xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <l3vpncomm>
      <l3vpnInstances>
        <l3vpnInstance>
          <vrfName>%s</vrfName>
          <l3vpnIfs>
            <l3vpnIf operation="delete">
              <ifName>%s</ifName>
            </l3vpnIf>
          </l3vpnIfs>
        </l3vpnInstance>
      </l3vpnInstances>
    </l3vpncomm>
  </l3vpn>
</config>
"""


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
        iftype = 'stack-Port'
    elif interface.upper().startswith('NULL'):
        iftype = 'null'
    else:
        return None

    return iftype.lower()


class VrfInterface(object):
    """Manange vpn instance"""

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # vpn instance info
        self.vrf = self.module.params['vrf']
        self.vpn_interface = self.module.params['vpn_interface']
        self.vpn_interface = self.vpn_interface.upper().replace(' ', '')
        self.state = self.module.params['state']
        self.intf_info = dict()
        self.intf_info['isL2SwitchPort'] = None
        self.intf_info['vrfName'] = None
        self.conf_exist = False

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def init_module(self):
        """init_module"""

        required_one_of = [("vrf", "vpn_interface")]
        self.module = AnsibleModule(
            argument_spec=self.spec, required_one_of=required_one_of, supports_check_mode=True)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_update_cmd(self):
        """ get  updated command"""

        if self.conf_exist:
            return

        if self.state == 'absent':
            self.updates_cmd.append(
                "undo ip binding vpn-instance %s" % self.vrf)
            return

        if self.vrf != self.intf_info['vrfName']:
            self.updates_cmd.append("ip binding vpn-instance %s" % self.vrf)

        return

    def check_params(self):
        """Check all input params"""

        if not self.is_vrf_exist():
            self.module.fail_json(
                msg='Error: The VPN instance is not existed.')

        if self.state == 'absent':
            if self.vrf != self.intf_info['vrfName']:
                self.module.fail_json(
                    msg='Error: The VPN instance is not bound to the interface.')

        if self.intf_info['isL2SwitchPort'] == 'true':
            self.module.fail_json(
                msg='Error: L2Switch Port can not binding a VPN instance.')

        # interface type check
        if self.vpn_interface:
            intf_type = get_interface_type(self.vpn_interface)
            if not intf_type:
                self.module.fail_json(
                    msg='Error: interface name of %s'
                        ' is error.' % self.vpn_interface)

        # vrf check
        if self.vrf == '_public_':
            self.module.fail_json(
                msg='Error: The vrf name _public_ is reserved.')
        if len(self.vrf) < 1 or len(self.vrf) > 31:
            self.module.fail_json(
                msg='Error: The vrf name length must be between 1 and 31.')

    def get_interface_vpn_name(self, vpninfo, vpn_name):
        """ get vpn instance name"""

        l3vpn_if = vpninfo.findall("l3vpnIf")
        for l3vpn_ifinfo in l3vpn_if:
            for ele in l3vpn_ifinfo:
                if ele.tag in ['ifName']:
                    if ele.text == self.vpn_interface:
                        self.intf_info['vrfName'] = vpn_name

    def get_interface_vpn(self):
        """ get the VPN instance associated with the interface"""

        xml_str = CE_NC_GET_VRF_INTERFACE
        con_obj = get_nc_config(self.module, xml_str)
        if "<data/>" in con_obj:
            return

        xml_str = con_obj.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

        # get global vrf interface info
        root = ElementTree.fromstring(xml_str)
        vpns = root.findall(
            "data/l3vpn/l3vpncomm/l3vpnInstances/l3vpnInstance")
        if vpns:
            for vpnele in vpns:
                vpn_name = None
                for vpninfo in vpnele:
                    if vpninfo.tag == 'vrfName':
                        vpn_name = vpninfo.text

                    if vpninfo.tag == 'l3vpnIfs':
                        self.get_interface_vpn_name(vpninfo, vpn_name)

        return

    def is_vrf_exist(self):
        """ judge whether the VPN instance is existed"""

        conf_str = CE_NC_GET_VRF % self.vrf
        con_obj = get_nc_config(self.module, conf_str)
        if "<data/>" in con_obj:
            return False

        return True

    def get_intf_conf_info(self):
        """ get related configuration of the interface"""

        conf_str = CE_NC_GET_INTF % self.vpn_interface
        con_obj = get_nc_config(self.module, conf_str)
        if "<data/>" in con_obj:
            return

        # get interface base info
        xml_str = con_obj.replace('\r', '').replace('\n', '').\
            replace('xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"', "").\
            replace('xmlns="http://www.huawei.com/netconf/vrp"', "")

        root = ElementTree.fromstring(xml_str)
        interface = root.find("data/ifm/interfaces/interface")
        if interface:
            for eles in interface:
                if eles.tag in ["isL2SwitchPort"]:
                    self.intf_info[eles.tag] = eles.text

        self.get_interface_vpn()
        return

    def get_existing(self):
        """get existing config"""

        self.existing = dict(vrf=self.intf_info['vrfName'],
                             vpn_interface=self.vpn_interface)

    def get_proposed(self):
        """get_proposed"""

        self.proposed = dict(vrf=self.vrf,
                             vpn_interface=self.vpn_interface,
                             state=self.state)

    def get_end_state(self):
        """get_end_state"""

        self.intf_info['vrfName'] = None
        self.get_intf_conf_info()

        self.end_state = dict(vrf=self.intf_info['vrfName'],
                              vpn_interface=self.vpn_interface)

    def show_result(self):
        """ show result"""

        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        if self.changed:
            self.results['updates'] = self.updates_cmd
        else:
            self.results['updates'] = list()

        self.module.exit_json(**self.results)

    def judge_if_config_exist(self):
        """ judge whether configuration has existed"""

        if self.state == 'absent':
            return False

        delta = set(self.proposed.items()).difference(
            self.existing.items())
        delta = dict(delta)
        if len(delta) == 1 and delta['state']:
            return True

        return False

    def config_interface_vrf(self):
        """ configure VPN instance of the interface"""

        if not self.conf_exist and self.state == 'present':

            xml_str = CE_NC_MERGE_VRF_INTERFACE % (
                self.vrf, self.vpn_interface)
            ret_xml = set_nc_config(self.module, xml_str)
            self.check_response(ret_xml, "VRF_INTERFACE_CONFIG")
            self.changed = True
        elif self.state == 'absent':
            xml_str = CE_NC_DEL_INTF_VPN % (self.vrf, self.vpn_interface)
            ret_xml = set_nc_config(self.module, xml_str)
            self.check_response(ret_xml, "DEL_VRF_INTERFACE_CONFIG")
            self.changed = True

    def work(self):
        """excute task"""

        self.get_intf_conf_info()
        self.check_params()
        self.get_existing()
        self.get_proposed()
        self.conf_exist = self.judge_if_config_exist()

        self.config_interface_vrf()

        self.get_update_cmd()
        self.get_end_state()
        self.show_result()


def main():
    """main"""

    argument_spec = dict(
        vrf=dict(required=True, type='str'),
        vpn_interface=dict(required=True, type='str'),
        state=dict(choices=['absent', 'present'],
                   default='present', required=False),
    )
    argument_spec.update(ce_argument_spec)
    vrf_intf = VrfInterface(argument_spec)
    vrf_intf.work()

if __name__ == '__main__':
    main()
