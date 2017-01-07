#!/usr/bin/python
#coding: utf-8 -*-

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

# pylint: disable=C0111

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: openvswitch_bridge
version_added: 1.4
author: "David Stygstra (@stygstra)"
short_description: Manage Open vSwitch bridges
requirements: [ ovs-vsctl ]
description:
    - Manage Open vSwitch bridges
options:
    bridge:
        required: true
        description:
            - Name of bridge or fake bridge to manage
    parent:
        version_added: "2.3"
        required: false
        default: None
        description:
            - Bridge parent of the fake bridge to manage
    vlan:
        version_added: "2.3"
        required: false
        default: None
        description:
            - The VLAN id of the fake bridge to manage (must be between 0 and 4095)
    state:
        required: false
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the bridge should exist
    timeout:
        required: false
        default: 5
        description:
            - How long to wait for ovs-vswitchd to respond
    external_ids:
        version_added: 2.0
        required: false
        default: None
        description:
            - A dictionary of external-ids. Omitting this parameter is a No-op.
              To  clear all external-ids pass an empty value.
    fail_mode:
        version_added: 2.0
        default: None
        required: false
        choices : [secure, standalone]
        description:
            - Set bridge fail-mode. The default value (None) is a No-op.
    set:
        version_added: 2.3
        required: false
        default: None
        description:
            - Set a single property on a bridge.
'''

EXAMPLES = '''
# Create a bridge named br-int
- openvswitch_bridge:
    bridge: br-int
    state: present

# Create a fake bridge named br-int within br-parent on the VLAN 405
- openvswitch_bridge:
    bridge: br-int
    parent: br-parent
    vlan: 405
    state: present

# Create an integration bridge
- openvswitch_bridge:
    bridge: br-int
    state: present
    fail_mode: secure
  args:
    external_ids:
      bridge-id: br-int
'''

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


class OVSBridge(object):
    """ Interface to ovs-vsctl. """
    def __init__(self, module):
        self.module = module
        self.bridge = module.params['bridge']
        self.parent = module.params['parent']
        self.vlan = module.params['vlan']
        self.state = module.params['state']
        self.timeout = module.params['timeout']
        self.fail_mode = module.params['fail_mode']
        self.set_opt = module.params.get('set', None)

        if self.parent:
            if self.vlan is None:
                self.module.fail_json(msg='VLAN id must be set when parent is defined')
            elif self.vlan < 0 or self.vlan > 4095:
                self.module.fail_json(msg='Invalid VLAN ID (must be between 0 and 4095)')

    def _vsctl(self, command):
        '''Run ovs-vsctl command'''
        return self.module.run_command(['ovs-vsctl', '-t',
                                        str(self.timeout)] + command)

    def exists(self):
        '''Check if the bridge already exists'''
        rtc, _, err = self._vsctl(['br-exists', self.bridge])
        if rtc == 0:  # See ovs-vsctl(8) for status codes
            return True
        if rtc == 2:
            return False
        self.module.fail_json(msg=err)

    def set(self, set_opt):
        """ Set attributes on a bridge. """
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
        '''Create the bridge'''
        cmd = ['add-br', self.bridge]
        if self.parent and self.vlan: # Add fake bridge
            cmd += [self.parent, self.vlan]

        if self.set and self.set_opt:
            cmd += ["--", "set"]
            cmd += self.set_opt.split(" ")

        rtc, _, err = self._vsctl(cmd)
        if rtc != 0:
            self.module.fail_json(msg=err)
        if self.fail_mode:
            self.set_fail_mode()

    def delete(self):
        '''Delete the bridge'''
        rtc, _, err = self._vsctl(['del-br', self.bridge])
        if rtc != 0:
            self.module.fail_json(msg=err)

    def check(self):
        '''Run check mode'''
        changed = False

        # pylint: disable=W0703
        try:
            if self.state == 'present' and self.exists():
                if (self.fail_mode and
                   (self.fail_mode != self.get_fail_mode())):
                    changed = True

                ##
                # Check if external ids would change.
                current_external_ids = self.get_external_ids()
                exp_external_ids = self.module.params['external_ids']
                if exp_external_ids is not None:
                    for (key, value) in exp_external_ids:
                        if ((key in current_external_ids) and
                           (value != current_external_ids[key])):
                            changed = True

                    ##
                    # Check if external ids would be removed.
                    for (key, value) in current_external_ids.items():
                        if key not in exp_external_ids:
                            changed = True

            elif self.state == 'absent' and self.exists():
                changed = True
            elif self.state == 'present' and not self.exists():
                changed = True
        except Exception:
            earg = get_exception()
            self.module.fail_json(msg=str(earg))

        # pylint: enable=W0703
        self.module.exit_json(changed=changed)

    def run(self):
        '''Make the necessary changes'''
        changed = False
        # pylint: disable=W0703

        try:
            if self.state == 'absent':
                if self.exists():
                    self.delete()
                    changed = True
            elif self.state == 'present':

                if not self.exists():
                    self.add()
                    changed = True

                ##
                # If the -- set changed check here and make changes
                # but this only makes sense when state=present.
                if (not changed):
                    changed = self.set(self.set_opt) or changed

                current_fail_mode = self.get_fail_mode()
                if self.fail_mode and (self.fail_mode != current_fail_mode):
                    self.module.log( "changing fail mode %s to %s" % (current_fail_mode, self.fail_mode))
                    self.set_fail_mode()
                    changed = True

                current_external_ids = self.get_external_ids()

                ##
                # Change and add existing external ids.
                exp_external_ids = self.module.params['external_ids']
                if exp_external_ids is not None:
                    for (key, value) in exp_external_ids.items():
                        if ((value != current_external_ids.get(key, None)) and
                           self.set_external_id(key, value)):
                            changed = True

                    ##
                    # Remove current external ids that are not passed in.
                    for (key, value) in current_external_ids.items():
                        if ((key not in exp_external_ids) and
                           self.set_external_id(key, None)):
                            changed = True

        except Exception:
            earg = get_exception()
            self.module.fail_json(msg=str(earg))
        # pylint: enable=W0703
        self.module.exit_json(changed=changed)

    def get_external_ids(self):
        """ Return the bridge's external ids as a dict. """
        results = {}
        if self.exists():
            rtc, out, err = self._vsctl(['br-get-external-id', self.bridge])
            if rtc != 0:
                self.module.fail_json(msg=err)
            lines = out.split("\n")
            lines = [item.split("=") for item in lines if len(item) > 0]
            for item in lines:
                results[item[0]] = item[1]

        return results

    def set_external_id(self, key, value):
        """ Set external id. """
        if self.exists():
            cmd = ['br-set-external-id', self.bridge, key]
            if value:
                cmd += [value]

            (rtc, _, err) = self._vsctl(cmd)
            if rtc != 0:
                self.module.fail_json(msg=err)
            return True
        return False

    def get_fail_mode(self):
        """ Get failure mode. """
        value = ''
        if self.exists():
            rtc, out, err = self._vsctl(['get-fail-mode', self.bridge])
            if rtc != 0:
                self.module.fail_json(msg=err)
            value = out.strip("\n")
        return value

    def set_fail_mode(self):
        """ Set failure mode. """

        if self.exists():
            (rtc, _, err) = self._vsctl(['set-fail-mode', self.bridge,
                                         self.fail_mode])
            if rtc != 0:
                self.module.fail_json(msg=err)


# pylint: disable=E0602
def main():
    """ Entry point. """
    module = AnsibleModule(
        argument_spec={
            'bridge': {'required': True},
            'parent': {'default': None},
            'vlan': {'default': None, 'type': 'int'},
            'state': {'default': 'present', 'choices': ['present', 'absent']},
            'timeout': {'default': 5, 'type': 'int'},
            'external_ids': {'default': None, 'type': 'dict'},
            'fail_mode': {'default': None},
            'set': {'required': False, 'default': None}
        },
        supports_check_mode=True,
    )

    bridge = OVSBridge(module)
    if module.check_mode:
        bridge.check()
    else:
        bridge.run()

# pylint: disable=W0614
# pylint: disable=W0401
# pylint: disable=W0622

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.pycompat24 import get_exception

if __name__ == '__main__':
    main()
