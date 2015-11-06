#!/usr/bin/python
#coding: utf-8 -*-

# pylint: disable=C0111

# (c) 2013, David Stygstra <david.stygstra@gmail.com>
#
# Portions copyright @ 2015 VMware, Inc.
#
# This file is part of Ansible
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: openvswitch_port
version_added: 1.4
author: "David Stygstra (@stygstra)"
short_description: Manage Open vSwitch ports
requirements: [ ovs-vsctl ]
description:
    - Manage Open vSwitch ports
options:
    bridge:
        required: true
        description:
            - Name of bridge to manage
    port:
        required: true
        description:
            - Name of port to manage on the bridge
    state:
        required: false
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the port should exist
    timeout:
        required: false
        default: 5
        description:
            - How long to wait for ovs-vswitchd to respond
    external_ids:
        version_added: 2.0
        required: false
        default: {}
        description:
            - Dictionary of external_ids applied to a port.
    set:
        version_added: 2.0
        required: false
        default: None
        description:
            - Set a single property on a port.
'''

EXAMPLES = '''
# Creates port eth2 on bridge br-ex
- openvswitch_port: bridge=br-ex port=eth2 state=present

# Creates port eth6 and set ofport equal to 6.
- openvswitch_port: bridge=bridge-loop port=eth6 state=present
                    set Interface eth6 ofport_request=6

# Assign interface id server1-vifeth6 and mac address 52:54:00:30:6d:11
# to port vifeth6 and setup port to be managed by a controller.
- openvswitch_port: bridge=br-int port=vifeth6 state=present
  args:
    external_ids:
      iface-id: "{{inventory_hostname}}-vifeth6"
      attached-mac: "52:54:00:30:6d:11"
      vm-id: "{{inventory_hostname}}"
      iface-status: "active"
'''

# pylint: disable=W0703


def truncate_before(value, srch):
    """ Return content of str before the srch parameters. """

    before_index = value.find(srch)
    if (before_index >= 0):
        return value[:before_index]
    else:
        return value


def _set_to_get(set_cmd, module):
    """ Convert set command to get command and set value.
    return tuple (get command, set value)
    """

    ##
    # If set has option: then we want to truncate just before that.
    set_cmd = truncate_before(set_cmd, " option:")
    get_cmd = set_cmd.split(" ")
    (key, value) = get_cmd[-1].split("=")
    module.log("get commands %s " % key)
    return (["--", "get"] + get_cmd[:-1] + [key], value)


# pylint: disable=R0902
class OVSPort(object):
    """ Interface to OVS port. """
    def __init__(self, module):
        self.module = module
        self.bridge = module.params['bridge']
        self.port = module.params['port']
        self.state = module.params['state']
        self.timeout = module.params['timeout']
        self.set_opt = module.params.get('set', None)

    def _vsctl(self, command, check_rc=True):
        '''Run ovs-vsctl command'''

        cmd = ['ovs-vsctl', '-t', str(self.timeout)] + command
        return self.module.run_command(cmd, check_rc=check_rc)

    def exists(self):
        '''Check if the port already exists'''

        (rtc, out, err) = self._vsctl(['list-ports', self.bridge])

        if rtc != 0:
            self.module.fail_json(msg=err)

        return any(port.rstrip() == self.port for port in out.split('\n'))

    def set(self, set_opt):
        """ Set attributes on a port. """
        self.module.log("set called %s" % set_opt)
        if (not set_opt):
            return False

        (get_cmd, set_value) = _set_to_get(set_opt, self.module)
        (rtc, out, err) = self._vsctl(get_cmd, False)
        if rtc != 0:
            ##
            # ovs-vsctl -t 5 -- get Interface port external_ids:key
            # returns failure if key does not exist.
            out = None
        else:
            out = out.strip("\n")
            out = out.strip('"')

        if (out == set_value):
            return False

        (rtc, out, err) = self._vsctl(["--", "set"] + set_opt.split(" "))
        if rtc != 0:
            self.module.fail_json(msg=err)

        return True

    def add(self):
        '''Add the port'''
        cmd = ['add-port', self.bridge, self.port]
        if self.set and self.set_opt:
            cmd += ["--", "set"]
            cmd += self.set_opt.split(" ")

        (rtc, _, err) = self._vsctl(cmd)
        if rtc != 0:
            self.module.fail_json(msg=err)

        return True

    def delete(self):
        '''Remove the port'''
        (rtc, _, err) = self._vsctl(['del-port', self.bridge, self.port])
        if rtc != 0:
            self.module.fail_json(msg=err)

    def check(self):
        '''Run check mode'''
        try:
            if self.state == 'absent' and self.exists():
                changed = True
            elif self.state == 'present' and not self.exists():
                changed = True
            else:
                changed = False
        except Exception, earg:
            self.module.fail_json(msg=str(earg))
        self.module.exit_json(changed=changed)

    def run(self):
        '''Make the necessary changes'''
        changed = False
        try:
            if self.state == 'absent':
                if self.exists():
                    self.delete()
                    changed = True
            elif self.state == 'present':
                ##
                # Add any missing ports.
                if (not self.exists()):
                    self.add()
                    changed = True

                ##
                # If the -- set changed check here and make changes
                # but this only makes sense when state=present.
                if (not changed):
                    changed = self.set(self.set_opt) or changed
                    items = self.module.params['external_ids'].items()
                    for (key, value) in items:
                        value = value.replace('"', '')
                        fmt_opt = "Interface %s external_ids:%s=%s"
                        external_id = fmt_opt % (self.port, key, value)
                        changed = self.set(external_id) or changed
                ##
        except Exception, earg:
            self.module.fail_json(msg=str(earg))
        self.module.exit_json(changed=changed)


# pylint: disable=E0602
def main():
    """ Entry point.  """
    module = AnsibleModule(
        argument_spec={
            'bridge': {'required': True},
            'port': {'required': True},
            'state': {'default': 'present', 'choices': ['present', 'absent']},
            'timeout': {'default': 5, 'type': 'int'},
            'set': {'required': False, 'default': None},
            'external_ids': {'default': {}, 'required': False},
        },
        supports_check_mode=True,
    )

    port = OVSPort(module)
    if module.check_mode:
        port.check()
    else:
        port.run()


# pylint: disable=W0614
# pylint: disable=W0401
# pylint: disable=W0622

# import module snippets
from ansible.module_utils.basic import *
main()
