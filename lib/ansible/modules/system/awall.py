#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ted Trask <ttrask01@yahoo.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: awall
short_description: Manage awall policies
version_added: "2.4"
author: Ted Trask (@tdtrask) <ttrask01@yahoo.com>
description:
  - This modules allows for enable/disable/activate of I(awall) policies.
  - Alpine Wall (I(awall)) generates a firewall configuration from the enabled policy files
    and activates the configuration on the system.
options:
  name:
    description:
      - One or more policy names.
    type: list
  state:
    description:
      - Whether the policies should be enabled or disabled.
    type: str
    choices: [ disabled, enabled ]
    default: enabled
  activate:
    description:
      - Activate the new firewall rules.
      - Can be run with other steps or on its own.
    type: bool
    default: no
'''

EXAMPLES = r'''
- name: Enable "foo" and "bar" policy
  awall:
    name: [ foo bar ]
    state: enabled

- name: Disable "foo" and "bar" policy and activate new rules
  awall:
    name:
    - foo
    - bar
    state: disabled
    activate: no

- name: Activate currently enabled firewall rules
  awall:
    activate: yes
'''

RETURN = ''' # '''

import re
from ansible.module_utils.basic import AnsibleModule


def activate(module):
    cmd = "%s activate --force" % (AWALL_PATH)
    rc, stdout, stderr = module.run_command(cmd)
    if rc == 0:
        return True
    else:
        module.fail_json(msg="could not activate new rules", stdout=stdout, stderr=stderr)


def is_policy_enabled(module, name):
    cmd = "%s list" % (AWALL_PATH)
    rc, stdout, stderr = module.run_command(cmd)
    if re.search(r"^%s\s+enabled" % name, stdout, re.MULTILINE):
        return True
    return False


def enable_policy(module, names, act):
    policies = []
    for name in names:
        if not is_policy_enabled(module, name):
            policies.append(name)
    if not policies:
        module.exit_json(changed=False, msg="policy(ies) already enabled")
    names = " ".join(policies)
    if module.check_mode:
        cmd = "%s list" % (AWALL_PATH)
    else:
        cmd = "%s enable %s" % (AWALL_PATH, names)
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        module.fail_json(msg="failed to enable %s" % names, stdout=stdout, stderr=stderr)
    if act and not module.check_mode:
        activate(module)
    module.exit_json(changed=True, msg="enabled awall policy(ies): %s" % names)


def disable_policy(module, names, act):
    policies = []
    for name in names:
        if is_policy_enabled(module, name):
            policies.append(name)
    if not policies:
        module.exit_json(changed=False, msg="policy(ies) already disabled")
    names = " ".join(policies)
    if module.check_mode:
        cmd = "%s list" % (AWALL_PATH)
    else:
        cmd = "%s disable %s" % (AWALL_PATH, names)
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        module.fail_json(msg="failed to disable %s" % names, stdout=stdout, stderr=stderr)
    if act and not module.check_mode:
        activate(module)
    module.exit_json(changed=True, msg="disabled awall policy(ies): %s" % names)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='enabled', choices=['disabled', 'enabled']),
            name=dict(type='list'),
            activate=dict(type='bool', default=False),
        ),
        required_one_of=[['name', 'activate']],
        supports_check_mode=True,
    )

    global AWALL_PATH
    AWALL_PATH = module.get_bin_path('awall', required=True)

    p = module.params

    if p['name']:
        if p['state'] == 'enabled':
            enable_policy(module, p['name'], p['activate'])
        elif p['state'] == 'disabled':
            disable_policy(module, p['name'], p['activate'])

    if p['activate']:
        if not module.check_mode:
            activate(module)
        module.exit_json(changed=True, msg="activated awall rules")

    module.fail_json(msg="no action defined")


if __name__ == '__main__':
    main()
