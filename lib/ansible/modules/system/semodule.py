#!/usr/bin/python
# Copyright: (c) 2019, Philip Bove <phil@bove.online>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: semodule
short_description: Manage selinux policy modules
description:
  - Use this module to manage selinux policy modules from Type Enforcement files
version_added: "2.9"
options:
  src:
    description:
      - File name of Type Enforcement file to apply to system
    type: path
  state:
    description:
      - State of policy module in system
    type: str
    choices: ["present", "absent"]
    default: "present"
  force:
    description:
      - Force operation to happen even if uneeded
    choices: [True, False]
    default: False
    type: bool
requirements:
  - policycoreutils
  - checkpolicy
author:
  - Philip Bove (@bandit145)
'''

EXAMPLES = '''
# install policy module from type enforcement file
- semodule:
    src: policy.te

# force install policy module even if already existing on target system
- semodule:
    src: policy.te
    force: true

# remove policy module
- semodule:
    src: policy.te
    state: absent
'''

RETURN = '''
# standard return values
'''

REQUIREMENTS = [
    'semodule',
    'checkmodule',
    'semodule_package'
]

from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.semodule as semodule
import os


def get_semodule_info(module):
    rc, stdout, stderr = module.run_command(['semodule', '-l'])
    if rc != 0:
        module.fail_json(msg='semodule command failed')
    return stdout


def ensure(module, policy_def):
    changed = False
    apply_te_file(module, policy_def)
    end_pol = semodule.parse_pol_info(policy_def['name'], get_semodule_info(module))
    changed = True
    module.exit_json(changed=changed)


def check_run_fail(run, module):
    if run[0] != 0:
        module.fail_json(msg=run[2])


def apply_te_file(module, policy_def):
    chk_module_out = module.run_command(['checkmodule', '-M', '-m', module.params['src'], '-o', policy_def['name'] + '.mod'])
    check_run_fail(chk_module_out, module)
    semod_package_out = module.run_command(['semodule_package', '-o', policy_def['name'] + '.pp', '-m', policy_def['name'] + '.mod'])
    check_run_fail(semod_package_out, module)
    semodule_out = module.run_command(['semodule', '-i', policy_def['name'] + '.pp'])
    check_run_fail(semodule_out, module)


def check_requirements(module):
    if os.getuid() != 0:
        module.fail_json(msg='This module can only be run elevated')
    for req in REQUIREMENTS:
        rc, stdout, stderr = module.run_command(['which', req])
        if rc != 0:
            module.fail_json(msg='missing the {name} utility which is required to run this module'.format(name=req))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            src=dict(type='path', required=True),
            force=dict(type='bool', required=False, choices=[True, False]),
            state=dict(type='str', default='present', choices=['present', 'latest', 'absent'])
        ),
        supports_check_mode=True
    )
    check_requirements(module)
    try:
        te_info = semodule.read_te_file(module.params['src'])
    except IndexError:
        module.fail_json(msg='Module is missing module definition line')
    policy_def = semodule.parse_module_info(te_info)
    ensure(module, policy_def)


if __name__ == '__main__':
    main()
