#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019 David Lundgren <dlundgren@syberisle.net>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
author:
    - David Lundgren (@dlundgren)
module: sysrc
short_description: Manage FreeBSD using sysrc
version_added: '2.10'
description:
    - Manages /etc/rc.conf for FreeBSD
options:
    name:
        description:
            - Name of variable in $dest to manage.
        type: str
        required: true
    value:
        description:
            - The value if "present"
        type: str
    state:
        description:
            - Whether the var should be present or absent in $dest.
            - append/subtract will add or remove the value from a list.
        type: str
        default: "present"
        choices: [ present, absent, append, subtract ]
    dest:
        description:
            - What file should be operated on
        type: str
        default: "/etc/rc.conf"
    delim:
        description:
            - Delimiter used in append/subtract mode
        default: " "
        type: str
    jail:
        description:
            - Name or ID of the jail to operate on
        required: false
        type: str
notes:
  - The C(name) cannot use . (periods) as sysrc doesn't support OID style names
'''

EXAMPLES = r'''
---
# enable mysql in the /etc/rc.conf
- name: Configure mysql pid file
  sysrc:
    name: mysql_pidfile
    value: "/var/run/mysqld/mysqld.pid"

# enable accf_http kld in the boot loader
- name: enable accf_http kld
  sysrc:
    name: accf_http_load
    state: present
    value: "YES"
    dest: /boot/loader.conf

# add gif0 to cloned_interfaces
- name: add gif0 interface
  sysrc:
    name: cloned_interfaces
    state: append
    value: "gif0"

# enable nginx on a jail
- name: add gif0 interface
  sysrc:
    name: nginx_enable
    value: "YES"
    jail: www
'''

RETURN = r'''
changed:
  description: Return changed for sysrc actions as true or false.
  returned: always
  type: bool
'''

from ansible.module_utils.basic import AnsibleModule
import re


class sysrc(object):
    def __init__(self, module, name, value, dest, delim, jail):
        self.module = module
        self.name = name
        self.changed = False
        self.value = value
        self.dest = dest
        self.delim = delim
        self.jail = jail
        self.sysrc = module.get_bin_path('sysrc', True)

    def has_unknown_variable(self, out, err):
        # newer versions of sysrc use stderr instead of stdout
        return err.find("unknown variable") > 0 or out.find("unknown variable") > 0

    def exists(self):
        # sysrc doesn't really use exit codes
        (rc, out, err) = self.run_sysrc(self.name)
        if self.value is None:
            regex = "%s: " % re.escape(self.name)
        else:
            regex = "%s: %s$" % (re.escape(self.name), re.escape(self.value))

        return not self.has_unknown_variable(out, err) and re.match(regex, out) is not None

    def contains(self):
        (rc, out, err) = self.run_sysrc('-n', self.name)
        if self.has_unknown_variable(out, err):
            return False

        return self.value in out.strip().split(self.delim)

    def create(self):
        if self.module.check_mode:
            self.changed = True
            return

        self.module._verbosity = 5
        (rc, out, err) = self.run_sysrc("%s=%s" % (self.name, self.value))
        if out.find("%s:" % self.name) == 0 and re.search("-> %s$" % re.escape(self.value), out) is not None:
            self.changed = True
            return True
        else:
            return False

    def destroy(self):
        if self.module.check_mode:
            self.changed = True
            return

        (rc, out, err) = self.run_sysrc('-x', self.name)
        if self.has_unknown_variable(out, err):
            return False

        self.changed = True
        return True

    def append(self):
        if self.module.check_mode:
            self.changed = True
            return

        setstring = '%s+=%s%s' % (self.name, self.delim, self.value)
        (rc, out, err) = self.run_sysrc(setstring)
        if out.find("%s:" % self.name) == 0:
            values = out.split(' -> ')[1].strip().split(self.delim)
            if self.value in values:
                self.changed = True
                return True
            else:
                return False
        else:
            return False

    def subtract(self):
        if self.module.check_mode:
            self.changed = True
            return

        setstring = '%s-=%s%s' % (self.name, self.delim, self.value)
        (rc, out, err) = self.run_sysrc(setstring)
        if out.find("%s:" % self.name) == 0:
            values = out.split(' -> ')[1].strip().split(self.delim)
            if self.value in values:
                return False
            else:
                self.changed = True
                return True
        else:
            return False

    def run_sysrc(self, *args):
        cmd = [self.sysrc, '-f', self.dest]
        if self.jail:
            cmd += ['-j', self.jail]
        cmd.extend(args)

        (rc, out, err) = self.module.run_command(cmd)
        if self.module._verbosity > 0:
            self.cmd = cmd

        if self.module._verbosity >= 4:
            self.cmd_output = out

        return (rc, out, err)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            value=dict(type='str', default=None),
            state=dict(type='str', default='present', choices=['present', 'absent', 'append', 'subtract']),
            dest=dict(type='str', default='/etc/rc.conf'),
            delim=dict(type='str', default=' '),
            jail=dict(type='str', default=None),
        ),
        supports_check_mode=True,
    )

    name = module.params.pop('name')
    # OID style names are not supported
    if not re.match('^[a-zA-Z0-9_]+$', name):
        module.fail_json(
            msg="Name may only contain alpha-numeric and underscore characters"
        )

    value = module.params.pop('value')
    state = module.params.pop('state')
    dest = module.params.pop('dest')
    delim = module.params.pop('delim')
    jail = module.params.pop('jail')
    result = dict(
        name=name,
        state=state,
        value=value,
        dest=dest,
        delim=delim,
        jail=jail
    )

    rcValue = sysrc(module, name, value, dest, delim, jail)

    if module._verbosity >= 4:
        result['existed'] = rcValue.exists()

    if state == 'present':
        not rcValue.exists() and rcValue.create()
    elif state == 'absent':
        rcValue.exists() and rcValue.destroy()
    elif state == 'append':
        not rcValue.contains() and rcValue.append()
    elif state == 'subtract':
        rcValue.contains() and rcValue.subtract()

    if module._verbosity > 0:
        result['command'] = ' '.join(rcValue.cmd)

    if module._verbosity >= 4:
        result['output'] = rcValue.cmd_output

    result['changed'] = rcValue.changed

    module.exit_json(**result)


if __name__ == '__main__':
    main()
