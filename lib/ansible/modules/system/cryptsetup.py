#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, Alexander Bulimov <lazywolf0@gmail.com>
# Based on lvol module by Jeroen Hoekx <jeroen.hoekx@dsquare.be>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: cryptsetup

short_description: manage plain dm-crypt and LUKS encrypted volumes

version_added: "2.4"

description:
    - "Ensure an encrypted volume is in desired state"

options:
    name:
        description:
            - Name of the volume in /dev/mapper
        required: false
    device:
        description:
            - Path of the block device
        required: false
    state:
        description:
            - State of the volume. absent/closed and present/open are synonyms.
        choices:
            - absent
            - present
            - open
            - closed
            - formatted
        default: open
        required: false
    type:
        description:
            - Type of the volume.
        choices:
            - plain
            - luks
            - loopaes
            - tcrypt
        default: luks
        required: false
    passphrase:
        description:
            - Passphrase to en-/decrypt device. Either this or keyfile is required to open/format.
        required: false
    keyfile:
        description:
            - Path of keyfile to en-/decrypt device. Either this or passphraes is required to open/format.
        required: false

author:
    - Tim Dittler (@t2d)
'''

EXAMPLES = '''
- name: Encrypt a block device
  cryptsetup:
    device: /dev/sdb

- name: Open an encrypted block device
  cryptsetup:
    name: test_crypt
    device: /dev/sdb
    type: tcrypt
    passphrase: "{{ secret_from_vault }}"
'''

from ansible.module_utils.basic import AnsibleModule


def is_present(module, name):
    cmd = ["cryptsetup", "status", name]
    rc, out, err = module.run_command(cmd)

    if rc == 0:
        return True
    elif rc == 4:
        return False
    else:
        module.fail_json(msg=err, changed=False)


def open_device(module):
    device = module.params['device']
    name = module.params['name']
    keyfile = module.params['keyfile']
    passphrase = module.params['passphrase']
    type = module.params['type']

    # check if device is present
    present = is_present(module, name)

    if present:
        return False

    # device not present
    if module.check_mode:
        return True

    # open the device
    if keyfile:
        cmd = ["cryptsetup", "open", device, name, "--type", type, "--key-file", keyfile]
    else:
        cmd = ["cryptsetup", "open", device, name, "--type", type]

    rc, out, err = module.run_command(cmd, data=passphrase)

    if rc == 0:
        return True
    else:
        module.fail_json(msg=err, changed=False)


def format_device(module):
    device = module.params['device']
    keyfile = module.params['keyfile']
    passphrase = module.params['passphrase']

    # check if device is already formatted
    cmd = ['cryptsetup', 'isLuks', device]
    rc, out, err = module.run_command(cmd)

    if rc == 0:
        # everything already okay
        return False

    if module.check_mode:
        # we don't want actual changes
        if rc != 0:
            return True

    # format the device
    if keyfile:
        cmd = ['cryptsetup', 'luksFormat', device, '--key-file', keyfile]
    else:
        cmd = ['cryptsetup', 'luksFormat', device]

    rc, out, err = module.run_command(cmd, data=passphrase)

    if rc == 0:
        return True
    else:
        module.fail_json(msg=err, changed=False)


def close_device(module):
    name = module.params['name']

    # check if device is present
    present = is_present(module, name)

    if not present:
        return False

    if module.check_mode:
        return True

    # close the device
    cmd = ['cryptsetup', 'close', name]
    rc, out, err = module.run_command(cmd)

    if rc == 0:
        return True
    else:
        module.fail_json(msg=err, changed=False)


def main():
    STATES = [
        'present',
        'absent',
        'open',
        'closed',
        'formatted'
    ]

    TYPES = [
        'plain',
        'luks',
        'loopaes',
        'tcrypt'
    ]

    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        name=dict(type='str', required=False),
        device=dict(type='str', required=False),
        state=dict(type='str', required=False, default="open", choices=STATES),
        type=dict(type='str', required=False, default="luks", choices=TYPES),
        passphrase=dict(type='str', required=False, no_log=True),
        keyfile=dict(type='str', required=False),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # switch on state
    if module.params["state"] in ['absent', 'closed']:
        if not module.params["name"]:
            module.fail_json(msg="Please provide device name!", **result)
        result['changed'] = close_device(module)

    if module.params["state"] in ['formatted', 'open', 'present']:
        # check args
        if not module.params["device"]:
            module.fail_json(msg="Please provide device!", **result)
        if not (module.params["passphrase"] or module.params["keyfile"]):
            module.fail_json(msg="Please provide either passphrase or keyfile!", **result)

        if module.params['state'] == 'formatted':
            result['changed'] = format_device(module)
        else:
            result['changed'] = open_device(module)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


if __name__ == '__main__':
    main()
