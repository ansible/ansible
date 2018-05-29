#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Victor Carceler
# Written by Victor Carceler <vcarceler@iespuigcastellar.xeill.net>


# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: snap

short_description: Manages snaps

version_added: "2.4"

description:
    - "Manages snaps packages."

options:
    name:
        description:
            - Snap's name.
        required: true
    state:
        description:
            - Control to demo if the result of this module is changed or not
        required: false
        default: present
        choices: [ absent, present ]
    classic:
        description:
            - Confinement boolean. Some snaps need --classic option.
        type: bool
        required: false
        default: no
        choices: [ no, yes ]

author:
    - Victor Carceler (vcarceler@iespuigcastellar.xeill.net)
'''

EXAMPLES = '''
# Install VLC
- name: Install VLC
  snap:
    name: vlc

# Remove VLC
- name: Remove VLC
  snap:
    name: vlc
    state: absent

# Classic confinement
- name: Install some snap with option --classic
  snap:
    name: some-snap
    classic: yes
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
message:
    description: The output message that the sample module generates
'''

from ansible.module_utils.basic import AnsibleModule

def info_snap(module, name):
    # snap info returns 0 if the snap exists, 1 if not
    snap_path = module.get_bin_path("snap", True)
    cmd = "%s info %s" % (snap_path, name)
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)

    return rc, stdout, stderr

def installed_snap(module, name):
    snap_path = module.get_bin_path("snap", True)
    cmd = "%s list %s" % (snap_path, name)
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)

    return rc, stdout, stderr

def install_snap(module, name):
    classic = ''
    if module.params['classic']:
        classic = '--classic'

    snap_path = module.get_bin_path("snap", True)
    cmd = "%s install %s %s" % (snap_path, name, classic)
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)

    return rc, stdout, stderr

def remove_snap(module, name):
    snap_path = module.get_bin_path("snap", True)
    cmd = "%s remove %s" % (snap_path, name)
    rc, stdout, stderr = module.run_command(cmd, check_rc=False)

    return rc, stdout, stderr

def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', required=False, default='present', choices=['absent', 'present']),
        classic=dict(type='bool', required=False, default=False)
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

    # Test if snap exists
    rc, out, err = info_snap(module, module.params['name'])
    if module._diff:
        diff = parse_diff(out)
    else:
        diff = {}
    if rc:
        # Unknown snap.
        result['message'] = err
        #result['original_message'] = "'snap info %s'" % (module.params['name'])
        #module.fail_json(msg=err, **result)
        module.fail_json(msg=err)

    # Install or remove snap?
    if module.params['state'] == 'present':
        rc, out, err = installed_snap(module, module.params['name'])
        if rc == 0:
            result['message'] = "snap %s already installed." % (module.params['name'])
            module.exit_json(**result)

        rc, out, err = install_snap(module, module.params['name'])
        if rc == 0:
            # Installed :-)
            result['message'] = out
            result['changed'] = True
            module.exit_json(**result)
        else:
            # Something wrong :-(
            result['message'] = err
            module.fail_json(**result)

    elif module.params['state'] == 'absent':
        rc, out, err = installed_snap(module, module.params['name'])
        if rc != 0:
            result['message'] = "snap %s not installed." % (module.params['name'])
            module.exit_json(**result)

        rc, out, err = remove_snap(module, module.params['name'])
        if rc == 0:
            # Removed :-)
            result['message'] = out
            result['changed'] = True
            module.exit_json(**result)
        else:
            # Something wrong :-(
            result['message'] = err
            module.fail_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
