#!/usr/bin/python

# https://github.com/ansible/ansible/issues/21185

# Copyright: (c) 2018, Dusty Mabe <dusty@dustymabe.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


# Most of this module was inspired by the command module
# ./lib/ansible/modules/commands/command.py

import shlex

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import b

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: rpm_ostree

short_description: A module for a few rpm-ostree operations

version_added: "2.X"

description:
    - "A module for a few rpm-ostree operations"

options:
    name:
        description:
            - This is the message to send to the sample module
        required: true
    state:
    install:
        description:
            - Packages to install on the system
    new:
        description:
            - Control to demo if the result of this module is changed or not
        required: false

author:
    - Dusty Mabe <dusty@dustymabe.com>
'''

EXAMPLES = '''
# pass in a message and have changed true
- name: Test with a message and changed output
  rpm-ostree:
    name: hello world
    new: true
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
message:
    description: The output message that the sample module generates
'''

from ansible.module_utils.basic import AnsibleModule

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        reboot=dict(type='bool', required=False, default=False),
        name=dict(aliases=['pkg'], type='list', required=True),
        state=dict(default='present',
                   choices=['absent', 'present',
                            'installed', 'removed', 'latest']),
                            
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
#   result['original_message'] = module.params['name']
#   result['message'] = 'goodbye'

    if module.params['state'] in ['installed', 'present']:
        action = 'install'
    elif module.params['state'] in ['absent', 'removed']:
        action = 'uninstall'
    
    cmd = "rpm-ostree {} --allow-inactive --idempotent --unchanged-exit-77 {}"
    cmd = cmd.format(action, ' '.join(module.params['name']))
    cmd = shlex.split(cmd)
    rc, out, err = module.run_command(cmd, encoding=None)
    if out is None:
        out = b('')
    if err is None:
        err = b('')
    result.update(dict(
        rc     = rc,
        cmd    = cmd,
        stdout = out.rstrip(b("\r\n")),
        stderr = err.rstrip(b("\r\n")),
    ))

    # A few possible options:
    #     - rc=0  - succeeded in making a change
    #     - rc=77 - no change was needed
    #     - rc=?  - error
    if rc == 0:
        result['changed'] = True
    elif rc == 77:
        result['changed'] = False
        result['rc'] = 0
    else: 
        module.fail_json(msg='non-zero return code', **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
