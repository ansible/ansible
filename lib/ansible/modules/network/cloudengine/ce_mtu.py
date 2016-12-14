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
module: ce_mtu
version_added: "2.2"
short_description: Manages MTU settings on CloudEngine switch.
description:
    - Manages MTU settings on CloudEngine switch.
extends_documentation_fragment: CloudEngine
author:
    - Pan Qijun (@CloudEngine-Ansible)
notes:
    - Either C(sysmtu) param is required or C(interface) AND C(mtu) params are req'd.
    - C(state=absent) unconfigures a given MTU if that value is currently present.
options:
    interface:
        description:
            - Full name of interface, i.e. 40GE1/0/22.
        required: false
        default: null
    mtu:
        description:
            - MTU for a specific interface.
        required: false
        default: null
        choices:[46:9600]
    jumbo_max:
        description:
            - Maximum frame size. The default value is 9216.
        required: false
        default: null
        choices:[1536:12288]
    jumbo_min:
        description:
            - Non-jumbo frame size threshod. The default value is 1518.
        required: false
        default: null
        choices:[1518:jbfMax]
    state:
        description:
            - Specify desired state of the resource.
        required: false
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
# Config jumboframe on 40GE1/0/22
- ce_mtu:
    jumbo_max: 9000
    jumbo_min: 8000
    host: {{ inventory_hostname }}
    username: {{ un }}
    password: {{ pwd }}

# Config mtu on 40GE1/0/22 (routed interface)
- ce_mtu:
    interface: 40GE1/0/22
    mtu: 1600
    host: {{ inventory_hostname }}
    username: {{ un }}
    password: {{ pwd }}

# Config mtu on 40GE1/0/23 (switched interface)
- ce_mtu:
    interface: 40GE1/0/23
    mtu: 9216
    host: {{ inventory_hostname }}
    username: {{ un }}
    password: {{ pwd }}

# Config mtu and jumboframe on 40GE1/0/22 (routed interface)
- ce_mtu:
    interface: 40GE1/0/22
    mtu: 1601
    jumbo_max: 9001
    jumbo_min: 8001
    host: {{ inventory_hostname }}
    username: {{ un }}
    password: {{ pwd }}

# Unconfigure mtu and jumboframe on a given interface
- ce_mtu:
    interface: 40GE1/0/22
    host: {{ inventory_hostname }}
    username: {{ un }}
    password: {{ pwd }}
    state: absent
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"mtu": "1700", "jumbo_max": "9000", jumbo_min: "8000"}
existing:
    description:
        - k/v pairs of existing mtu/sysmtu on the interface/system
    type: dict
    sample: {"mtu": "1600", "jumbo_max": "9216", "jumbo_min": "1518"}
end_state:
    description: k/v pairs of mtu/sysmtu values after module execution
    returned: always
    type: dict
    sample: {"mtu": "1700", "jumbo_max": "9000", jumbo_min: "8000"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["interface 40GE1/0/23", "mtu 1700", "jumboframe enable 9000 8000"]
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
from ansible.module_utils.netcli import CommandRunner

HAS_NCCLIENT = False
try:
    from ncclient.operations.rpc import RPCError
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False
    pass

CE_NC_GET_INTF = """
<filter type="subtree">
  <ifm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <interfaces>
      <interface>
        <ifName>%s</ifName>
        <isL2SwitchPort></isL2SwitchPort>
        <ifMtu></ifMtu>
      </interface>
    </interfaces>
  </ifm>
</filter>
"""

CE_NC_XML_MERGE_INTF_MTU = """
  <ifm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <interfaces>
      <interface operation="merge">
        <ifName>%s</ifName>
        <ifMtu>%s</ifMtu>
      </interface>
    </interfaces>
  </ifm>
"""


class CE_MTU(object):
    """ CE_MTU"""

    def __init__(self, argument_spec, ):
        self.start_time = datetime.datetime.now()
        self.end_time = None
        self.spec = argument_spec
        self.module = None
        self.nc = None
        self.init_module()

        # interface info
        self.interface = self.module.params['interface']
        self.mtu = self.module.params['mtu']
        self.state = self.module.params['state']
        self.jbfMax = self.module.params['jumbo_max'] or None
        self.jbfMin = self.module.params['jumbo_min'] or None
        self.jbfConfig = list()

        # host info
        self.host = self.module.params['host']
        self.username = self.module.params['username']
        self.port = self.module.params['port']

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()
        self.intf_info = dict()         # one interface info
        self.intf_type = None           # loopback tunnel ...

        # init netconf connect
        self.init_netconf()

    def init_module(self):
        """ init_module"""

        self.module = NetworkModule(
            argument_spec=self.spec, supports_check_mode=True)

    def init_netconf(self):
        """ init_netconf"""

        if HAS_NCCLIENT:
            self.nc = get_netconf(host=self.host, port=self.port,
                                  username=self.username,
                                  password=self.module.params['password'])
        else:
            self.module.fail_json(
                msg='Error: No ncclient package, please install it.')

    def check_response(self, con_obj, xml_name):
        """Check if response message is already succeed."""

        xml_str = con_obj.xml
        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def build_config_xml(self, xmlstr):
        """ build_config_xml"""

        return '<config> ' + xmlstr + ' </config>'

    def get_interface_dict(self, ifname):
        """ get one interface attributes dict."""
        intf_info = dict()
        conf_str = CE_NC_GET_INTF % ifname
        try:
            con_obj = self.nc.get_config(filter=conf_str)
        except RPCError as e:
            self.module.fail_json(msg='Error: %s' % e.message)

        if "<data/>" in con_obj.xml:
            return intf_info

        intf = re.findall(
            r'.*<ifName>(.*)</ifName>.*\s*'
            r'<isL2SwitchPort>(.*)</isL2SwitchPort>.*\s*'
            r'<ifMtu>(.*)</ifMtu>.*', con_obj.xml)

        if intf:
            intf_info = dict(ifName=intf[0][0],
                             isL2SwitchPort=intf[0][1],
                             ifMtu=intf[0][2])

        return intf_info

    def get_interface_type(self, interface):
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

    def is_portswitch_enalbe(self, iftype):
        """"[undo] portswitch"""

        type_list = ['ge', '10ge', '25ge',
                     '4x10ge', '40ge', '100ge', 'eth-trunk']
        if iftype in type_list:
            return True
        else:
            return False

    def prase_jumboframe_para(self, configStr):
        """ prase_jumboframe_para"""

        interface_cli = "interface %s" % self.interface
        if configStr.find(interface_cli) == -1:
            self.module.fail_json(
                    msg='Interface does not exist.')
        npos1 = configStr.index(interface_cli)

        npos2 = configStr.index('#', npos1)
        configStrTmp = configStr[npos1:npos2]
        try:
            npos3 = configStrTmp.index('jumboframe enable')
        except ValueError:
            # return default vale
            return [9216, 1518]
        npos4 = configStrTmp.index('\n', npos3)

        configStrTmp = configStrTmp[npos3:npos4]
        return re.findall(r'([0-9]+)', configStrTmp)

    def excute_command(self, commands):
        """ excute_command"""

        runner = CommandRunner(self.module)
        for cmd in commands:
            try:
                runner.add_command(**cmd)
            except AddCommandError:
                exc = get_exception()
                self.module.fail_json(
                    msg='duplicate command detected: %s' % cmd)
        runner.retries = self.module.params['retries']
        runner.interval = self.module.params['interval']
        runner.match = self.module.params['match']

        try:
            runner.run()
        except FailedConditionsError:
            exc = get_exception()
            self.module.fail_json(
                msg=str(exc), failed_conditions=exc.failed_conditions)
        except FailedConditionalError:
            exc = get_exception()
            self.module.fail_json(
                msg=str(exc), failed_conditional=exc.failed_conditional)
        except NetworkError:
            exc = get_exception()
            self.module.fail_json(msg=str(exc), **exc.kwargs)

        for cmd in commands:
            try:
                output = runner.get_command(cmd['command'], cmd.get('output'))
            except ValueError:
                self.module.fail_json(
                    msg='command not executed due to check_mode, see warnings')
        return output

    def get_jumboframe_config(self):
        """ get_jumboframe_config"""

        commands = list()
        cmd = {'output': None, 'command': 'display current-configuration'}
        commands.append(cmd)
        output = self.excute_command(commands)
        return self.prase_jumboframe_para(output)

    def set_jumboframe(self):
        """ set_jumboframe"""

        if self.state == "present":
            if not self.jbfMax or not self.jbfMin:
                return

            jbfValue = self.get_jumboframe_config()
            self.jbfConfig = copy.deepcopy(jbfValue)
            if len(jbfValue) == 1:
                jbfValue.append("1518")
                self.jbfConfig.append("1518")
            if not self.jbfMax:
                return

            if (len(jbfValue) > 2) or (len(jbfValue) == 0):
                self.module.fail_json(
                    msg='Error: Get jubmoframe config value num error.')
            if (self.jbfMin is None):
                if (jbfValue[0] == self.jbfMax):
                    return
            else:
                if (jbfValue[0] == self.jbfMax) \
                        and (jbfValue[1] == self.jbfMin):
                    return
            if (jbfValue[0] != self.jbfMax):
                jbfValue[0] = self.jbfMax
            if (jbfValue[1] != self.jbfMin) and (self.jbfMin is not None):
                jbfValue[1] = self.jbfMin
            else:
                jbfValue.pop(1)
        else:
            jbfValue = self.get_jumboframe_config()
            self.jbfConfig = copy.deepcopy(jbfValue)
            if (jbfValue == [9216, 1518]):
                return
            jbfValue = [9216, 1518]

        # excute commands
        commands = list()
        cmd1 = {'output': None, 'command': 'system-view'}
        commands.append(cmd1)

        cmd2 = {'output': None, 'command': ''}
        cmd2['command'] = "interface %s" % self.interface
        commands.append(cmd2)

        if len(jbfValue) == 2:
            self.jbf_cli = "jumboframe enable %s %s" % (
                jbfValue[0], jbfValue[1])
        else:
            self.jbf_cli = "jumboframe enable %s" % (jbfValue[0])
        cmd3 = {'output': None, 'command': ''}
        cmd3['command'] = self.jbf_cli
        commands.append(cmd3)

        cmd4 = {'output': None, 'command': ''}
        cmd4['command'] = 'commit'
        commands.append(cmd4)
        self.excute_command(commands)

        self.changed = True
        if self.state == "present":
            if self.jbfMin:
                self.updates_cmd.append(
                    "jumboframe enable %s %s" % (self.jbfMax, self.jbfMin))
            else:
                self.updates_cmd.append("jumboframe enable %s" % (self.jbfMax))
        else:
            self.updates_cmd.append("undo jumboframe enable")

        return

    def merge_interface(self, ifname, mtu):
        """ Merge interface mtu."""

        xmlstr = ''
        change = False
        self.updates_cmd.append("interface %s" % ifname)
        if self.state == "present":
            if mtu and self.intf_info["ifMtu"] != mtu:
                xmlstr += CE_NC_XML_MERGE_INTF_MTU % (ifname, mtu)
                self.updates_cmd.append("mtu %s" % mtu)
                change = True
        else:
            if self.intf_info["ifMtu"] != '1500':
                xmlstr += CE_NC_XML_MERGE_INTF_MTU % (ifname, '1500')
                self.updates_cmd.append("undo mtu")
                change = True

        if not change:
            return

        conf_str = self.build_config_xml(xmlstr)

        try:
            con_obj = self.nc.set_config(config=conf_str)
            self.check_response(con_obj, "MERGE_INTF_MTU")
            self.changed = True
        except RPCError as e:
            self.module.fail_json(msg='Error: %s' % e.message)

    def IsInterfaceSupportSetJumboframe(self, interface):
        if interface is None:
            return False
        support_flag = False
        if interface.upper().startswith('GE'):
            support_flag = True
        elif interface.upper().startswith('10GE'):
            support_flag = True
        elif interface.upper().startswith('25GE'):
            support_flag = True
        elif interface.upper().startswith('4X10GE'):
            support_flag = True
        elif interface.upper().startswith('40GE'):
            support_flag = True
        elif interface.upper().startswith('100GE'):
            support_flag = True
        else:
            support_flag = False
        return support_flag

    def check_params(self):
        """Check all input params"""

        # interface type check
        if self.interface:
            self.intf_type = self.get_interface_type(self.interface)
            if not self.intf_type:
                self.module.fail_json(
                    msg='Error: Interface name of %s '
                        'is error.' % self.interface)

        if not self.intf_type:
            self.module.fail_json(
                msg='Error: Interface %s is error.')

        # mtu check mtu
        if self.mtu:
            if not self.mtu.isdigit():
                self.module.fail_json(msg='Error: Mtu is invalid.')
            # check mtu range
            if int(self.mtu) < 46 or int(self.mtu) > 9600:
                self.module.fail_json(
                    msg='Error: Mtu is not in the range from 46 to 9600.')
        # get interface info
        self.intf_info = self.get_interface_dict(self.interface)
        if not self.intf_info:
            self.module.fail_json(msg='Error: interface does not exists.')

        # check interface
        if self.intf_info['isL2SwitchPort'] == 'true':
            self.module.fail_json(msg='Error: L2Switch Port can not set mtu.')

        # check interface can set jumbo frame
        if self.state == 'present':
            if self.jbfMax:
                if not self.IsInterfaceSupportSetJumboframe(self.interface):
                    self.module.fail_json(
                        msg='Error: Interface %s does not support jumboframe set.' % self.interface)
                if not self.jbfMax.isdigit():
                    self.module.fail_json(msg='Error: Max jumboframe is not digit.')
                if (int(self.jbfMax) > 12288) or (int(self.jbfMax) < 1536):
                    self.module.fail_json(
                        msg='Error: Max jumboframe is between 1536 to 12288.')

            if self.jbfMin:
                if not self.jbfMin.isdigit():
                    self.module.fail_json(
                        msg='Error: Min jumboframe is not digit.')
                if not self.jbfMax:
                    self.module.fail_json(
                        msg='Error: please specify max jumboframe value.')
                if (int(self.jbfMin) > self.jbfMax) or (int(self.jbfMin) < 1518):
                    self.module.fail_json(
                        msg='Error: Min jumboframe is between '
                            '1518 to jumboframe max value.')

            if self.jbfMin is not None:
                if self.jbfMax is None:
                    self.module.fail_json(
                        msg='Error: please input MAX jumboframe '
                            'value.')


    def get_proposed(self):
        """ get_proposed"""

        self.proposed['state'] = self.state
        if self.interface:
            self.proposed["interface"] = self.interface

        if self.state == 'present':
            if self.mtu:
                self.proposed["mtu"] = self.mtu
            if self.jbfMax:
                if self.jbfMin:
                    self.proposed["jumboframe"] = "jumboframe enable %s %s" % (
                        self.jbfMax, self.jbfMin)
                else:
                    self.proposed[
                        "jumboframe"] = "jumboframe enable %s %s" % (self.jbfMax, 1518)

    def get_existing(self):
        """ get_existing"""

        if self.intf_info:
            self.existing["interface"] = self.intf_info["ifName"]
            self.existing["mtu"] = self.intf_info["ifMtu"]

        if self.intf_info:
            if not self.existing["interface"]:
                self.existing["interface"] = self.interface

            if len(self.jbfConfig) != 2:
                return

            self.existing["jumboframe"] = "jumboframe enable %s %s" % (
                self.jbfConfig[0], self.jbfConfig[1])

    def get_end_state(self):
        """ get_end_state"""

        if self.intf_info:
            end_info = self.get_interface_dict(self.interface)
            if end_info:
                self.end_state["interface"] = end_info["ifName"]
                self.end_state["mtu"] = end_info["ifMtu"]
        if self.intf_info:
            if not self.end_state["interface"]:
                self.end_state["interface"] = self.interface

            if self.state == 'absent':
                self.end_state["jumboframe"] = "jumboframe enable %s %s" % (
                    9216, 1518)
            elif not self.jbfMax and not self.jbfMin:
                if len(self.jbfConfig) != 2:
                    return
                self.end_state["jumboframe"] = "jumboframe enable %s %s" % (
                    self.jbfConfig[0], self.jbfConfig[1])
            elif self.jbfMin:
                self.end_state["jumboframe"] = "jumboframe enable %s %s" % (
                    self.jbfMax, self.jbfMin)
            else:
                self.end_state[
                    "jumboframe"] = "jumboframe enable %s %s" % (self.jbfMax, 1518)

    def work(self):
        """worker"""
        self.check_params()

        self.get_proposed()

        self.merge_interface(self.interface, self.mtu)
        self.set_jumboframe()

        self.get_existing()
        self.get_end_state()
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


def main():
    """ main"""

    argument_spec = dict(
        interface=dict(required=True, type='str'),
        mtu=dict(type='str'),
        state=dict(choices=['absent', 'present'],
                   default='present', required=False),
        jumbo_max=dict(type='str'),
        jumbo_min=dict(type='str'),
        commands=dict(type='list', required=False),
        wait_for=dict(type='list', aliases=['waitfor']),
        match=dict(default='all', choices=['any', 'all']),
        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int'),
    )

    interface = CE_MTU(argument_spec)
    interface.work()

if __name__ == '__main__':
    main()
