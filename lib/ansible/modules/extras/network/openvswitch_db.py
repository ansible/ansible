#!/usr/bin/python
# coding: utf-8 -*-

# pylint: disable=C0111

#
# (c) 2015, Mark Hamilton <mhamilton@vmware.com>
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

DOCUMENTATION = """
---
module: openvswitch_db
author: "Mark Hamilton (mhamilton@vmware.com)"
version_added: 2.0
short_description: Configure open vswitch database.
requirements: [ "ovs-vsctl >= 2.3.3" ]
description:
    - Set column values in record in database table.
options:
    table:
        required: true
        description:
            - Identifies the table in the database.
    record:
        required: true
        description:
            - Identifies the recoard in the table.
    column:
        required: true
        description:
            - Identifies the column in the record.
    key:
        required: true
        description:
            - Identifies the key in the record column
    value:
        required: true
        description:
            - Expected value for the table, record, column and key.
    timeout:
        required: false
        default: 5
        description:
            - How long to wait for ovs-vswitchd to respond
"""

EXAMPLES = '''
# Increase the maximum idle time to 50 seconds before pruning unused kernel
# rules.
- openvswitch_db: table=open_vswitch record=. col=other_config key=max-idle
                  value=50000

# Disable in band copy
- openvswitch_db: table=Bridge record=br-int col=other_config
                  key=disable-in-band value=true
'''


def cmd_run(module, cmd, check_rc=True):
    """ Log and run ovs-vsctl command. """
    return module.run_command(cmd.split(" "), check_rc=check_rc)


def params_set(module):
    """ Implement the ovs-vsctl set commands. """

    changed = False

    ##
    # Place in params dictionary in order to support the string format below.
    module.params["ovs-vsctl"] = module.get_bin_path("ovs-vsctl", True)

    fmt = "%(ovs-vsctl)s -t %(timeout)s get %(table)s %(record)s " \
          "%(col)s:%(key)s"

    cmd = fmt % module.params

    (_, output, _) = cmd_run(module, cmd, False)
    if module.params['value'] not in output:
        fmt = "%(ovs-vsctl)s -t %(timeout)s set %(table)s %(record)s " \
              "%(col)s:%(key)s=%(value)s"
        cmd = fmt % module.params
        ##
        # Check if flow exists and is the same.
        (rtc, _, err) = cmd_run(module, cmd)
        if rtc != 0:
            module.fail_json(msg=err)
        changed = True
    module.exit_json(changed=changed)


# pylint: disable=E0602
def main():
    """ Entry point for ansible module. """
    module = AnsibleModule(
        argument_spec={
            'table': {'required': True},
            'record': {'required': True},
            'col': {'required': True},
            'key': {'required': True},
            'value': {'required': True},
            'timeout': {'default': 5, 'type': 'int'},
        },
        supports_check_mode=True,
    )

    params_set(module)


# pylint: disable=W0614
# pylint: disable=W0401
# pylint: disable=W0622

# import module snippets
from ansible.module_utils.basic import *
main()
