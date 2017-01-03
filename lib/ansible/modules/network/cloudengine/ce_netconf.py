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

module: ce_netconf
version_added: "2.2"
short_description: Run arbitrary netconf command on CloudEngine devices.
description:
    - Sends an arbitrary netconf command to a CloudEngine node and returns
    the results read from the device.
extends_documentation_fragment: cloudengine
author:
    - JackyGao2016 (@CloudEngine-Ansible)
notes:
    - The rpc parameter is always required.
options:
    rpc:
        description:
            - the type of rpc.
        required: true
        default: none
        choices: ['get', 'edit-config', 'execute-action', 'execute-cli']
    cfg_xml:
        description:
            - the config xml string.
        required: true
        default: none
'''

EXAMPLES = '''
# netconf get operation
  - name: "netconf get operation"
    ce_netconf:
        rpc:  get
        cfg_xml:  "<filter type=\"subtree\"><vlan xmlns=\"http://www.huawei.com/netconf/vrp\" content-version=\"1.0\" format-version=\"1.0\"><vlans><vlan><vlanId>10</vlanId><vlanif><ifName></ifName><cfgBand></cfgBand><dampTime></dampTime></vlanif></vlan></vlans></vlan></filter>"
        host:  {{inventory_hostname}}
        port:  {{ansible_ssh_port}}
        username:  {{username}}
        password:  {{password}}

# netconf edit-config operation
  - name: "netconf edit-config operation"
    ce_netconf:
        rpc:  edit-config
        cfg_xml:  "<config><aaa xmlns=\"http://www.huawei.com/netconf/vrp\" content-version=\"1.0\" format-version=\"1.0\"><authenticationSchemes><authenticationScheme operation=\"create\"><authenSchemeName>default_wdz</authenSchemeName><firstAuthenMode>local</firstAuthenMode><secondAuthenMode>invalid</secondAuthenMode></authenticationScheme></authenticationSchemes></aaa></config>"
        host:  {{inventory_hostname}}
        port:  {{ansible_ssh_port}}
        username:  {{username}}
        password:  {{password}}

# netconf execute-action operation
  - name: "netconf execute-action operation"
    ce_netconf:
        rpc:  execute-action
        cfg_xml:  "<action><l2mc xmlns=\"http://www.huawei.com/netconf/vrp\" content-version=\"1.0\" format-version=\"1.0\"><l2McResetAllVlanStatis><addrFamily>ipv4unicast</addrFamily></l2McResetAllVlanStatis></l2mc></action>"
        host:  {{inventory_hostname}}
        port:  {{ansible_ssh_port}}
        username:  {{username}}
        password:  {{password}}

# netconf execute-cli operation
  - name: "netconf execute-cli operation"
    ce_netconf:
        rpc:  execute-cli
        cfg_xml:  "<cmd><id>1</id><cmdline>display current-configuration</cmdline></cmd>"
        host:  {{inventory_hostname}}
        port:  {{ansible_ssh_port}}
        username:  {{username}}
        password:  {{password}}
'''

RETURN = '''
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"result": ["ok"]}
execute_time:
    description: the module execute time
    returned: always
    type: string
    sample: "0:00:03.380753"
'''

import datetime
from ansible.module_utils.network import NetworkModule
from ansible.module_utils.cloudengine import get_netconf

HAS_NCCLIENT = False
try:
    from ncclient.operations.rpc import RPCError
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False


def main():
    """ main """

    start_time = datetime.datetime.now()

    argument_spec = dict(
        host=dict(required=True),
        username=dict(required=True),
        password=dict(required=True),
        rpc=dict(choices=['get', 'edit-config',
                          'execute-action', 'execute-cli'], default=None),
        cfg_xml=dict(required=True)
    )

    if not HAS_NCCLIENT:
        raise Exception("the ncclient library is required")

    module = NetworkModule(argument_spec=argument_spec,
                        supports_check_mode=True)

    host = module.params['host']
    port = module.params['port']
    username = module.params['username']
    password = module.params['password']
    rpc = module.params['rpc']
    cfg_xml = module.params['cfg_xml']

    if not rpc or not cfg_xml:
        module.fail_json(msg='please input rpc and cfg_xml.')

    netconf = get_netconf(host=host, port=port,
                          username=username, password=password)

    changed = False
    end_state = dict()

    if not netconf:
        module.fail_json(msg='ce_netconf start failed.')

    if rpc == "get":

        try:
            response = netconf.get_config(filter=cfg_xml)
        except RPCError as e:
            module.fail_json(msg='Error: %s' % e.message)

        if "<data/>" in response.xml:
            module.fail_json(msg='rpc get failed.')

        tmp1 = response.xml.split(r"<data>")
        tmp2 = tmp1[1].split(r"</data>")
        result = tmp2[0].split("\n")

        end_state["result"] = result

    elif rpc == "edit-config":

        try:
            response = netconf.set_config(config=cfg_xml)
        except RPCError as e:
            module.fail_json(msg='Error: %s' % e.message)

        if "<ok/>" not in response.xml:
            module.fail_json(msg='merge local user info failed.')

        changed = True
        end_state["result"] = "ok"

    elif rpc == "execute-action":

        try:
            response = netconf.execute_action(action=cfg_xml)
        except RPCError as e:
            module.fail_json(msg='Error: %s' % e.message)

        if "<ok/>" not in response.xml:
            module.fail_json(msg='merge local user info failed.')

        changed = True
        end_state["result"] = "ok"

    elif rpc == "execute-cli":

        try:
            response = netconf.execute_cli(command=cfg_xml)
        except RPCError as e:
            module.fail_json(msg='Error: %s' % e.message)

        if "<data/>" in response.xml:
            module.fail_json(msg='rpc execute-cli failed.')

        tmp1 = response.xml.split(r"<data>")
        tmp2 = tmp1[1].split(r"</data>")
        result = tmp2[0].split("\n")

        end_state["result"] = result

    else:
        module.fail_json(msg='please input correct rpc.')

    results = dict()
    results['changed'] = changed
    results['end_state'] = end_state

    end_time = datetime.datetime.now()
    results['execute_time'] = str(end_time - start_time)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
