#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, David "DaviXX" CHANIAL <david.chanial@gmail.com>
# (c) 2014, James Tanner <tanner.jc@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: sysctl
short_description: Manage entries in sysctl.conf.
description:
    - This module manipulates sysctl entries and optionally performs a C(/sbin/sysctl -p) after changing them.
version_added: "1.0"
options:
    name:
        description:
            - The dot-separated path (aka I(key)) specifying the sysctl variable.
        required: true
        aliases: [ 'key' ]
    value:
        description:
            - Desired value of the sysctl key.
        aliases: [ 'val' ]
    state:
        description:
            - Whether the entry should be present or absent in the sysctl file.
        choices: [ "present", "absent" ]
        default: present
    ignoreerrors:
        description:
            - Use this option to ignore errors about unknown keys.
        type: bool
        default: 'no'
    reload:
        description:
            - If C(yes), performs a I(/sbin/sysctl -p) if the C(sysctl_file) is
              updated. If C(no), does not reload I(sysctl) even if the
              C(sysctl_file) is updated.
        type: bool
        default: 'yes'
    sysctl_file:
        description:
            - Specifies the absolute path to C(sysctl.conf), if not C(/etc/sysctl.conf).
        default: /etc/sysctl.conf
    sysctl_set:
        description:
            - Verify token value with the sysctl command and set with -w if necessary
        type: bool
        default: 'no'
        version_added: 1.5
author: "David CHANIAL (@davixx) <david.chanial@gmail.com>"
'''

EXAMPLES = '''
# Set vm.swappiness to 5 in /etc/sysctl.conf
- sysctl:
    name: vm.swappiness
    value: 5
    state: present

# Remove kernel.panic entry from /etc/sysctl.conf
- sysctl:
    name: kernel.panic
    state: absent
    sysctl_file: /etc/sysctl.conf

# Set kernel.panic to 3 in /tmp/test_sysctl.conf
- sysctl:
    name: kernel.panic
    value: 3
    sysctl_file: /tmp/test_sysctl.conf
    reload: no

# Set ip forwarding on in /proc and verify token value with the sysctl command
- sysctl:
    name: net.ipv4.ip_forward
    value: 1
    sysctl_set: yes

# Set ip forwarding on in /proc and in the sysctl file and reload if necessary
- sysctl:
    name: net.ipv4.ip_forward
    value: 1
    sysctl_set: yes
    state: present
    reload: yes
'''

# ==============================================================

import os
import tempfile

from ansible.module_utils.basic import get_platform, AnsibleModule
from ansible.module_utils.six import string_types
from ansible.module_utils.parsing.convert_bool import BOOLEANS_FALSE, BOOLEANS_TRUE
from ansible.module_utils._text import to_native


class SysctlModule(object):

    def __init__(self, module):
        self.module = module
        self.args = self.module.params

        self.sysctl_cmd = self.module.get_bin_path('sysctl', required=True)
        self.sysctl_file = self.args['sysctl_file']

        self.proc_value = None  # current token value in proc fs
        self.file_value = None  # current token value in file
        self.file_lines = []    # all lines in the file
        self.file_values = {}   # dict of token values

        self.changed = False    # will change occur
        self.set_proc = False   # does sysctl need to set value
        self.write_file = False  # does the sysctl file need to be reloaded

        self.process()

    # ==============================================================
    #   LOGIC
    # ==============================================================

    def process(self):

        self.platform = get_platform().lower()

        # Whitespace is bad
        self.args['name'] = self.args['name'].strip()
        self.args['value'] = self._parse_value(self.args['value'])

        thisname = self.args['name']

        # get the current proc fs value
        self.proc_value = self.get_token_curr_value(thisname)

        # get the currect sysctl file value
        self.read_sysctl_file()
        if thisname not in self.file_values:
            self.file_values[thisname] = None

        # update file contents with desired token/value
        self.fix_lines()

        # what do we need to do now?
        if self.file_values[thisname] is None and self.args['state'] == "present":
            self.changed = True
            self.write_file = True
        elif self.file_values[thisname] is None and self.args['state'] == "absent":
            self.changed = False
        elif self.file_values[thisname] and self.args['state'] == "absent":
            self.changed = True
            self.write_file = True
        elif self.file_values[thisname] != self.args['value']:
            self.changed = True
            self.write_file = True

        # use the sysctl command or not?
        if self.args['sysctl_set']:
            if self.proc_value is None:
                self.changed = True
            elif not self._values_is_equal(self.proc_value, self.args['value']):
                self.changed = True
                self.set_proc = True

        # Do the work
        if not self.module.check_mode:
            if self.write_file:
                self.write_sysctl()
            if self.write_file and self.args['reload']:
                self.reload_sysctl()
            if self.set_proc:
                self.set_token_value(self.args['name'], self.args['value'])

    def _values_is_equal(self, a, b):
        """Expects two string values. It will split the string by whitespace
        and compare each value. It will return True if both lists are the same,
        contain the same elements and the same order."""
        if a is None or b is None:
            return False

        a = a.split()
        b = b.split()

        if len(a) != len(b):
            return False

        return len([i for i, j in zip(a, b) if i == j]) == len(a)

    def _parse_value(self, value):
        if value is None:
            return ''
        elif isinstance(value, bool):
            if value:
                return '1'
            else:
                return '0'
        elif isinstance(value, string_types):
            if value.lower() in BOOLEANS_TRUE:
                return '1'
            elif value.lower() in BOOLEANS_FALSE:
                return '0'
            else:
                return value.strip()
        else:
            return value

    # ==============================================================
    #   SYSCTL COMMAND MANAGEMENT
    # ==============================================================

    # Use the sysctl command to find the current value
    def get_token_curr_value(self, token):
        if self.platform == 'openbsd':
            # openbsd doesn't support -e, just drop it
            thiscmd = "%s -n %s" % (self.sysctl_cmd, token)
        else:
            thiscmd = "%s -e -n %s" % (self.sysctl_cmd, token)
        rc, out, err = self.module.run_command(thiscmd)
        if rc != 0:
            return None
        else:
            return out

    # Use the sysctl command to set the current value
    def set_token_value(self, token, value):
        if len(value.split()) > 0:
            value = '"' + value + '"'
        if self.platform == 'openbsd':
            # openbsd doesn't accept -w, but since it's not needed, just drop it
            thiscmd = "%s %s=%s" % (self.sysctl_cmd, token, value)
        elif self.platform == 'freebsd':
            ignore_missing = ''
            if self.args['ignoreerrors']:
                ignore_missing = '-i'
            # freebsd doesn't accept -w, but since it's not needed, just drop it
            thiscmd = "%s %s %s=%s" % (self.sysctl_cmd, ignore_missing, token, value)
        else:
            ignore_missing = ''
            if self.args['ignoreerrors']:
                ignore_missing = '-e'
            thiscmd = "%s %s -w %s=%s" % (self.sysctl_cmd, ignore_missing, token, value)
        rc, out, err = self.module.run_command(thiscmd)
        if rc != 0:
            self.module.fail_json(msg='setting %s failed: %s' % (token, out + err))
        else:
            return rc

    # Run sysctl -p
    def reload_sysctl(self):
        # do it
        if self.platform == 'freebsd':
            # freebsd doesn't support -p, so reload the sysctl service
            rc, out, err = self.module.run_command('/etc/rc.d/sysctl reload')
        elif self.platform == 'openbsd':
            # openbsd doesn't support -p and doesn't have a sysctl service,
            # so we have to set every value with its own sysctl call
            for k, v in self.file_values.items():
                rc = 0
                if k != self.args['name']:
                    rc = self.set_token_value(k, v)
                    if rc != 0:
                        break
            if rc == 0 and self.args['state'] == "present":
                rc = self.set_token_value(self.args['name'], self.args['value'])
        else:
            # system supports reloading via the -p flag to sysctl, so we'll use that
            sysctl_args = [self.sysctl_cmd, '-p', self.sysctl_file]
            if self.args['ignoreerrors']:
                sysctl_args.insert(1, '-e')

            rc, out, err = self.module.run_command(sysctl_args)

        if rc != 0:
            self.module.fail_json(msg="Failed to reload sysctl: %s" % to_native(out) + to_native(err))

    # ==============================================================
    #   SYSCTL FILE MANAGEMENT
    # ==============================================================

    # Get the token value from the sysctl file
    def read_sysctl_file(self):

        lines = []
        if os.path.isfile(self.sysctl_file):
            try:
                with open(self.sysctl_file, "r") as read_file:
                    lines = read_file.readlines()
            except IOError as e:
                self.module.fail_json(msg="Failed to open %s: %s" % (to_native(self.sysctl_file), to_native(e)))

        for line in lines:
            line = line.strip()
            self.file_lines.append(line)

            # don't split empty lines or comments or line without equal sign
            if not line or line.startswith(("#", ";")) or "=" not in line:
                continue

            k, v = line.split('=', 1)
            k = k.strip()
            v = v.strip()
            self.file_values[k] = v.strip()

    # Fix the value in the sysctl file content
    def fix_lines(self):
        checked = []
        self.fixed_lines = []
        for line in self.file_lines:
            if not line.strip() or line.strip().startswith(("#", ";")) or "=" not in line:
                self.fixed_lines.append(line)
                continue
            tmpline = line.strip()
            k, v = tmpline.split('=', 1)
            k = k.strip()
            v = v.strip()
            if k not in checked:
                checked.append(k)
                if k == self.args['name']:
                    if self.args['state'] == "present":
                        new_line = "%s=%s\n" % (k, self.args['value'])
                        self.fixed_lines.append(new_line)
                else:
                    new_line = "%s=%s\n" % (k, v)
                    self.fixed_lines.append(new_line)

        if self.args['name'] not in checked and self.args['state'] == "present":
            new_line = "%s=%s\n" % (self.args['name'], self.args['value'])
            self.fixed_lines.append(new_line)

    # Completely rewrite the sysctl file
    def write_sysctl(self):
        # open a tmp file
        fd, tmp_path = tempfile.mkstemp('.conf', '.ansible_m_sysctl_', os.path.dirname(self.sysctl_file))
        f = open(tmp_path, "w")
        try:
            for l in self.fixed_lines:
                f.write(l.strip() + "\n")
        except IOError as e:
            self.module.fail_json(msg="Failed to write to file %s: %s" % (tmp_path, to_native(e)))
        f.flush()
        f.close()

        # replace the real one
        self.module.atomic_move(tmp_path, self.sysctl_file)


# ==============================================================
# main

def main():

    # defining module
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(aliases=['key'], required=True),
            value=dict(aliases=['val'], required=False, type='str'),
            state=dict(default='present', choices=['present', 'absent']),
            reload=dict(default=True, type='bool'),
            sysctl_set=dict(default=False, type='bool'),
            ignoreerrors=dict(default=False, type='bool'),
            sysctl_file=dict(default='/etc/sysctl.conf', type='path')
        ),
        supports_check_mode=True,
        required_if=[('state', 'present', ['value'])],
    )

    if module.params['name'] is None:
        module.fail_json(msg="name cannot be None")
    if module.params['state'] == 'present' and module.params['value'] is None:
        module.fail_json(msg="value cannot be None")

    # In case of in-line params
    if module.params['name'] == '':
        module.fail_json(msg="name cannot be blank")
    if module.params['state'] == 'present' and module.params['value'] == '':
        module.fail_json(msg="value cannot be blank")

    result = SysctlModule(module)

    module.exit_json(changed=result.changed)


if __name__ == '__main__':
    main()
