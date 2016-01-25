#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Cumulus Networks <ce-ceng@cumulusnetworks.com>
#
# This file is part of Ansible
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: cl_quagga_ospf
version_added: "2.1"
author: "Cumulus Networks (@CumulusNetworks)"
short_description: Configure basic OSPFv2 parameters and interfaces using Quagga
description:
    - Configures basic OSPFv2 global parameters such as
      router id and bandwidth cost, or OSPFv2 interface configuration like
      point-to-point settings or enabling OSPFv2 on an interface. Configuration
      is applied to single OSPFv2 instance. Multiple OSPFv2 instance
      configuration is currently not supported. It requires Quagga version
      0.99.22 and higher with the non-modal Quagga CLI developed by Cumulus
      Linux. For more details go to the Routing User Guide at
      http://docs.cumulusnetworks.com/ and Quagga Docs at
      http://www.nongnu.org/quagga/
options:
    router_id:
        description:
            - Set the OSPFv2 router id
        required: true
    reference_bandwidth:
        description:
            - Set the OSPFv2 auto cost reference bandwidth
        default: 40000
    saveconfig:
        description:
            - Boolean. Issue write memory to save the config
        choices: ['yes', 'no']
        default: ['no']
    interface:
        description:
            - define the name the interface to apply OSPFv2 services.
    point2point:
        description:
            - Boolean. enable OSPFv2 point2point on the interface
        choices: ['yes', 'no']
        require_together:
            - with interface option
    area:
        description:
            - defines the area the interface is in
        required_together:
            - with interface option
    cost:
        description:
            - define ospf cost.
        required_together:
            - with interface option
    passive:
        description:
            - make OSPFv2 interface passive
        choices: ['yes', 'no']
        required_together:
            - with interface option
    state:
        description:
            - Describes if OSPFv2 should be present on a particular interface.
              Module currently does not check that interface is not associated
              with a bond or bridge. User will have to manually clear the
              configuration of the interface from the bond or bridge. This will
              be implemented in a later release
        choices: [ 'present', 'absent']
        default: 'present'
        required_together:
            - with interface option
requirements:  ['Cumulus Linux Quagga non-modal CLI, Quagga version 0.99.22 and higher']
'''
EXAMPLES = '''
Example playbook entries using the cl_quagga_ospf module

    tasks:
    - name: configure ospf router_id
        cl_quagga_ospf: router_id=10.1.1.1
    - name: enable OSPFv2 on swp1 and set it be a point2point OSPF
      interface with a cost of 65535
        cl_quagga_ospf: interface=swp1 point2point=yes cost=65535
    - name: enable ospf on swp1-5
        cl_quagga_ospf: interface={{ item }}
        with_sequence: start=1 end=5 format=swp%d
    - name: disable ospf on swp1
        cl_quagga_ospf: interface=swp1 state=absent
'''

RETURN = '''
changed:
    description: whether the interface was changed
    returned: changed
    type: bool
    sample: True
msg:
    description: human-readable report of success or failure
    returned: always
    type: string
    sample: "interface bond0 config updated"
'''


def run_cl_cmd(module, cmd, check_rc=True, split_lines=True):
    try:
        (rc, out, err) = module.run_command(cmd, check_rc=check_rc)
    except Exception, e:
        module.fail_json(msg=e.strerror)
    # trim last line as it is always empty
    if split_lines:
        ret = out.splitlines()
    else:
        ret = out
    return ret


def check_dsl_dependencies(module, input_options,
                           dependency, _depend_value):
    for _param in input_options:
        if module.params.get(_param):
            if not module.params.get(dependency):
                _param_output = module.params.get(_param)
                _msg = "incorrect syntax. " + _param + " must have an interface option." + \
                    " Example 'cl_quagga_ospf: " + dependency + "=" + _depend_value + " " + \
                    _param + "=" + _param_output + "'"
                module.fail_json(msg=_msg)


def has_interface_config(module):
    if module.params.get('interface') is not None:
        return True
    else:
        return False


def get_running_config(module):
    running_config = run_cl_cmd(module, '/usr/bin/vtysh -c "show run"')
    got_global_config = False
    got_interface_config = False
    module.interface_config = {}
    module.global_config = []
    for line in running_config:
        line = line.lower().strip()
        # ignore the '!' lines or blank lines
        if len(line.strip()) <= 1:
            if got_global_config:
                got_global_config = False
            if got_interface_config:
                got_interface_config = False
            continue
        # begin capturing global config
        m0 = re.match('router\s+ospf', line)
        if m0:
            got_global_config = True
            continue
        m1 = re.match('^interface\s+(\w+)', line)
        if m1:
            module.ifacename = m1.group(1)
            module.interface_config[module.ifacename] = []
            got_interface_config = True
            continue
        if got_interface_config:
            module.interface_config[module.ifacename].append(line)
            continue
        if got_global_config:
            m3 = re.match('\s*passive-interface\s+(\w+)', line)
            if m3:
                ifaceconfig = module.interface_config.get(m3.group(1))
                if ifaceconfig:
                    ifaceconfig.append('passive-interface')
            else:
                module.global_config.append(line)
            continue


def get_config_line(module, stmt, ifacename=None):
    if ifacename:
        pass
    else:
        for i in module.global_config:
            if re.match(stmt, i):
                return i
    return None


def update_router_id(module):
    router_id_stmt = 'ospf router-id '
    actual_router_id_stmt = get_config_line(module, router_id_stmt)
    router_id_stmt = 'ospf router-id ' + module.params.get('router_id')
    if router_id_stmt != actual_router_id_stmt:
        cmd_line = "/usr/bin/cl-ospf router-id set %s" %\
                   (module.params.get('router_id'))
        run_cl_cmd(module, cmd_line)
        module.exit_msg += 'router-id updated '
        module.has_changed = True


def update_reference_bandwidth(module):
    bandwidth_stmt = 'auto-cost reference-bandwidth'
    actual_bandwidth_stmt = get_config_line(module, bandwidth_stmt)
    bandwidth_stmt = bandwidth_stmt + ' ' + \
        module.params.get('reference_bandwidth')
    if bandwidth_stmt != actual_bandwidth_stmt:
        cmd_line = "/usr/bin/cl-ospf auto-cost set reference-bandwidth %s" %\
                   (module.params.get('reference_bandwidth'))
        run_cl_cmd(module, cmd_line)
        module.exit_msg += 'reference bandwidth updated '
        module.has_changed = True


def add_global_ospf_config(module):
    module.has_changed = False
    get_running_config(module)
    if module.params.get('router_id'):
        update_router_id(module)
    if module.params.get('reference_bandwidth'):
        update_reference_bandwidth(module)
    if module.has_changed is False:
        module.exit_msg = 'No change in OSPFv2 global config'
    module.exit_json(msg=module.exit_msg, changed=module.has_changed)


def check_ip_addr_show(module):
    cmd_line = "/sbin/ip addr show %s" % (module.params.get('interface'))
    result = run_cl_cmd(module, cmd_line)
    for _line in result:
        m0 = re.match('\s+inet\s+\w+', _line)
        if m0:
            return True
    return False


def get_interface_addr_config(module):
    ifacename = module.params.get('interface')
    cmd_line = "/sbin/ifquery --format json %s" % (ifacename)
    int_config = run_cl_cmd(module, cmd_line, True, False)
    ifquery_obj = json.loads(int_config)[0]
    iface_has_address = False
    if 'address' in ifquery_obj.get('config'):
        for addr in ifquery_obj.get('config').get('address'):
            try:
                socket.inet_aton(addr.split('/')[0])
                iface_has_address = True
                break
            except socket.error:
                pass
    else:
        iface_has_address = check_ip_addr_show(module)
        if iface_has_address is False:
            _msg = "interface %s does not have an IP configured. " +\
                "Required for OSPFv2 to work"
            module.fail_json(msg=_msg)
    # for test purposes only
    return iface_has_address


def enable_or_disable_ospf_on_int(module):
    ifacename = module.params.get('interface')
    _state = module.params.get('state')
    iface_config = module.interface_config.get(ifacename)
    if iface_config is None:
        _msg = "%s is not found in Quagga config. " % (ifacename) + \
            "Check that %s is active in kernel" % (ifacename)
        module.fail_json(msg=_msg)
        return False  # for test purposes
    found_area = None
    for i in iface_config:
        m0 = re.search('ip\s+ospf\s+area\s+([0-9.]+)', i)
        if m0:
            found_area = m0.group(1)
            break
    if _state == 'absent':
        for i in iface_config:
            if found_area:
                cmd_line = '/usr/bin/cl-ospf clear %s area' % \
                    (ifacename)
                run_cl_cmd(module, cmd_line)
                module.has_changed = True
                module.exit_msg += "OSPFv2 now disabled on %s " % (ifacename)
        return False
    area_id = module.params.get('area')
    if found_area != area_id:
        cmd_line = '/usr/bin/cl-ospf interface set %s area %s' % \
            (ifacename, area_id)
        run_cl_cmd(module, cmd_line)
        module.has_changed = True
        module.exit_msg += "OSPFv2 now enabled on %s area %s " % \
            (ifacename, area_id)
    return True


def update_point2point(module):
    ifacename = module.params.get('interface')
    point2point = module.params.get('point2point')
    iface_config = module.interface_config.get(ifacename)
    found_point2point = None
    for i in iface_config:
        m0 = re.search('ip\s+ospf\s+network\s+point-to-point', i)
        if m0:
            found_point2point = True
            break
    if point2point:
        if not found_point2point:
            cmd_line = '/usr/bin/cl-ospf interface set %s network point-to-point' % \
                (ifacename)
            run_cl_cmd(module, cmd_line)
            module.has_changed = True
            module.exit_msg += 'OSPFv2 point2point set on %s ' % (ifacename)
    else:
        if found_point2point:
            cmd_line = '/usr/bin/cl-ospf interface clear %s network' % \
                (ifacename)
            run_cl_cmd(module, cmd_line)
            module.has_changed = True
            module.exit_msg += 'OSPFv2 point2point removed on %s ' % \
                (ifacename)


def update_passive(module):
    ifacename = module.params.get('interface')
    passive = module.params.get('passive')
    iface_config = module.interface_config.get(ifacename)
    found_passive = None
    for i in iface_config:
        m0 = re.search('passive-interface', i)
        if m0:
            found_passive = True
            break
    if passive:
        if not found_passive:
            cmd_line = '/usr/bin/cl-ospf interface set %s passive' % \
                (ifacename)
            run_cl_cmd(module, cmd_line)
            module.has_changed = True
            module.exit_msg += '%s is now OSPFv2 passive ' % (ifacename)
    else:
        if found_passive:
            cmd_line = '/usr/bin/cl-ospf interface clear %s passive' % \
                (ifacename)
            run_cl_cmd(module, cmd_line)
            module.has_changed = True
            module.exit_msg += '%s is no longer OSPFv2 passive ' % \
                (ifacename)


def update_cost(module):
    ifacename = module.params.get('interface')
    cost = module.params.get('cost')
    iface_config = module.interface_config.get(ifacename)
    found_cost = None
    for i in iface_config:
        m0 = re.search('ip\s+ospf\s+cost\s+(\d+)', i)
        if m0:
            found_cost = m0.group(1)
            break

    if cost != found_cost and cost is not None:
        cmd_line = '/usr/bin/cl-ospf interface set %s cost %s' % \
            (ifacename, cost)
        run_cl_cmd(module, cmd_line)
        module.has_changed = True
        module.exit_msg += 'OSPFv2 cost on %s changed to %s ' % \
            (ifacename, cost)
    elif cost is None and found_cost is not None:
        cmd_line = '/usr/bin/cl-ospf interface clear %s cost' % \
            (ifacename)
        run_cl_cmd(module, cmd_line)
        module.has_changed = True
        module.exit_msg += 'OSPFv2 cost on %s changed to default ' % \
            (ifacename)


def config_ospf_interface_config(module):
    enable_int_defaults(module)
    module.has_changed = False
    # get all ospf related config from quagga both globally and iface based
    get_running_config(module)
    # if interface does not have ipv4 address module should fail
    get_interface_addr_config(module)
    # if ospf should be enabled, continue to check for the remaining attrs
    if enable_or_disable_ospf_on_int(module):
        # update ospf point-to-point setting if needed
        update_point2point(module)
        # update ospf interface cost if needed
        update_cost(module)
        # update ospf interface passive setting
        update_passive(module)


def saveconfig(module):
    if module.params.get('saveconfig') is True and\
            module.has_changed:
        run_cl_cmd(module, '/usr/bin/vtysh -c "wr mem"')
        module.exit_msg += 'Saving Config '


def enable_int_defaults(module):
    if not module.params.get('area'):
        module.params['area'] = '0.0.0.0'
    if not module.params.get('state'):
        module.params['state'] = 'present'


def check_if_ospf_is_running(module):
    if not os.path.exists('/var/run/quagga/ospfd.pid'):
        _msg = 'OSPFv2 process is not running. Unable to execute command'
        module.fail_json(msg=_msg)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            reference_bandwidth=dict(type='str',
                                     default='40000'),
            router_id=dict(type='str'),
            interface=dict(type='str'),
            cost=dict(type='str'),
            area=dict(type='str'),
            state=dict(type='str',
                       choices=['present', 'absent']),
            point2point=dict(type='bool', choices=BOOLEANS),
            saveconfig=dict(type='bool', choices=BOOLEANS, default=False),
            passive=dict(type='bool', choices=BOOLEANS)
        ),
        mutually_exclusive=[['reference_bandwidth', 'interface'],
                            ['router_id', 'interface']]
    )
    check_if_ospf_is_running(module)

    check_dsl_dependencies(module, ['cost', 'state', 'area',
                                    'point2point', 'passive'],
                           'interface', 'swp1')
    module.has_changed = False
    module.exit_msg = ''
    if has_interface_config(module):
        config_ospf_interface_config(module)
    else:
        # Set area to none before applying global config
        module.params['area'] = None
        add_global_ospf_config(module)
    saveconfig(module)
    if module.has_changed:
        module.exit_json(msg=module.exit_msg, changed=module.has_changed)
    else:
        module.exit_json(msg='no change', changed=False)

# import module snippets
from ansible.module_utils.basic import *
import re
import os
import socket
# incompatible with ansible 1.4.4 - ubuntu 12.04 version
# from ansible.module_utils.urls import *


if __name__ == '__main__':
    main()
