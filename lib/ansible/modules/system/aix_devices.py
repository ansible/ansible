#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Kairo Araujo <kairo@kairo.eti.br>
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
author:
  - Kairo Araujo (@kairoaraujo)
module: aix_devices
short_description: Manages AIX devices.
description:
  - This module discovery, defines, removes and modifies attributes of AIX
    devices.
version_added: "2.5"
options:
  attributes:
    description:
      - Specifies attributes to device separated by comma.
      - If attribute has comma, explicit list using
        [ "parameter=value,with,comma", "parameter=foobar" ]. See alias
        example.
  device:
    description:
      - Device name.
      - C(all) is valid to rescan C(present) all devices (AIX cfgmgr command).
    required: true
  force:
    description:
      - Forces action.
    type: bool
    default: "no"
  recursive:
    description:
      - Removes or defines a device and children devices.
    type: bool
    default: "no"
  state:
    description:
      - Controls the device state.
      - C(present) rescan a specific device or all devices (when C(device) is
        not specified).
      - C(absent) removes a device.
      - C(defined) changes device to Defined state.
    choices: [present, absent, defined]
    default: present
    required: true
'''

EXAMPLES = '''
- name: Scan new devices.
  aix_devices:
    device: all
    state: present

- name: Scan new virtual devices.
  aix_devices:
    device: vio0
    state: present

- name: Removes ent0.
  aix_devices:
    device: ent0
    state: absent

- name: Put device en0 in Defined
  aix_devices:
    device: en0
    state: defined

- name: Put vscsi1 and children devices in Defined state.
  aix_devices:
    device: vscsi1
    recursive: yes
    state: defined

- name: Removes vscsi1 and children devices.
  aix_devices:
    device: vscsi1
    recursive: yes
    state: absent

- name: Changes en1 mtu to 9000 and disables arp.
  aix_devices:
    device: en1
    attributes: mtu=900,arp=off
    state: present

- name: Configure IP, netmask and set en1 up.
  aix_devices:
    device: en1
    attributes: netaddr=192.168.0.100,netmask=255.255.255.0,state=up
    state: present

- name: Adding IP alias to en0
  aix_devices:
    device: en0
    attributes: [
        "alias4=10.0.0.100,255.255.255.0"
        ]
    state: present
'''

RETURN = '''
changed:
  description: Return changed for aix_device actions as true or false.
  returned: always
  type: boolean
  version_added: "2.5"
msg:
  description: Return message regarding the action.
  returned: always
  type: string
  version_added: "2.5"
'''

from ansible.module_utils.basic import AnsibleModule


def _check_device(module, device):
    """
    Check if device already exists and the state.
    Args:
        module: Ansible module.
        device: device to be checked.

    Returns: bool, device state

    """
    lsdev_cmd = module.get_bin_path('lsdev', True)
    rc, lsdev_out, err = module.run_command("%s -C -l %s" % (lsdev_cmd, device))

    if rc != 0:
        module.fail_json(msg="Failed to run lsdev", rc=rc, err=err)

    if lsdev_out:
        device_state = lsdev_out.split()[1]
        return True, device_state

    else:
        device_state = None
        return False, device_state


def _check_device_attr(module, device, attr):
    """

    Args:
        module: Ansible module.
        device: device to check attributes.
        attr: attribute to be checked.

    Returns:

    """
    lsattr_cmd = module.get_bin_path("lsattr", True)
    rc, lsattr_out, err = module.run_command("%s -El %s -a %s" % (lsattr_cmd, device, attr))

    hide_attrs = ['delalias4', 'delalias6']

    if rc == 255:

        if attr in hide_attrs:
            current_param = ''
        else:
            current_param = None

        return current_param

    elif rc != 0:
        module.fail_json(msg="Failed to run lsattr.", rc=rc, err=err)

    else:
        current_param = lsattr_out.split()[1]

        return current_param


def discover_device(module, device):
    """ Discover AIX devices."""
    cfgmgr_cmd = module.get_bin_path('cfgmgr', True)

    if device is not None:
        device = "-l %s" % device

    else:
        device = ''

    changed = True
    msg = ''
    if not module.check_mode:
        rc, cfgmgr_out, err = module.run_command("%s %s" % (cfgmgr_cmd, device))
        changed = True
        msg = cfgmgr_out

    return changed, msg


def change_device_attr(module, attributes, device, force):
    """ Change AIX device attribute. """
    chdev_cmd = module.get_bin_path('chdev', True)
    attr_changed = []
    attr_not_changed = []
    attr_invalid = []

    for attr in attributes:
        new_param = attr.split('=')[1]
        current_param = _check_device_attr(module, device, attr.split('=')[0])

        if current_param is None:
            attr_invalid.append(attr)

        elif current_param != new_param:
            if not module.check_mode:
                rc, chdev_out, err = module.run_command("%s -l %s %s -a %s" % (chdev_cmd, device, force, attr))
                if rc != 0:
                    module.exit_json(msg="Failed to run chdev.", rc=rc, err=err)
                else:
                    attr_changed.append(attr)
        else:
            attr_not_changed.append(attr)

    changed = True
    msg = ''
    if not module.check_mode:
        if len(attr_changed) > 0:
            changed = True
            attr_changed_msg = 'Attributes changed: %s. ' % ','.join(attr_changed)
        else:
            changed = False
            attr_changed_msg = ''

        if len(attr_not_changed) > 0:
            attr_not_changed_msg = 'Attributes already set: %s. ' % ','.join(attr_not_changed)

        else:
            attr_not_changed_msg = ''

        if len(attr_invalid) > 0:
            attr_invalid_msg = 'Invalid attributes: %s ' % ', '.join(attr_invalid)
        else:
            attr_invalid_msg = ''

        msg = '%s%s%s' % (attr_changed_msg, attr_not_changed_msg, attr_invalid_msg)

    return changed, msg


def remove_device(module, device, force, recursive, state):
    """ Puts device in defined state or removes device. """

    state_opt = {
        'absent': '-d',
        'defined': ''
    }

    recursive_opt = {
        True: '-R',
        False: ''
    }

    recursive = recursive_opt[recursive]
    state = state_opt[state]

    changed = True
    msg = ''
    rmdev_cmd = module.get_bin_path('rmdev', True)

    if not module.check_mode:
        rc, rmdev_out, err = module.run_command('%s -l %s %s %s' % (rmdev_cmd, device, state, recursive))
        if rc != 0:
            module.fail_json(msg='Failed to run rmdev', rc=rc, err=err)
        else:
            changed = True
            msg = rmdev_out

    return changed, msg


def main():

    module = AnsibleModule(
        argument_spec=dict(
            attributes=dict(type='list'),
            device=dict(type='str'),
            force=dict(type='bool', default=False),
            recursive=dict(type='bool', default=False),
            state=dict(choices=['absent', 'present', 'defined'], default='present'),
        ),
        supports_check_mode=True,
    )

    force_opt = {
        True: '-f',
        False: '',
    }

    attributes = module.params['attributes']
    device = module.params['device']
    force = force_opt[module.params['force']]
    recursive = module.params['recursive']
    state = module.params['state']

    result = dict(
        changed=False,
        msg='',
        state=state
    )

    if state == 'present':
        if attributes:
            # validate attributes
            for attr in attributes:
                if len(attr.split('=')) < 2:
                    module.fail_json(msg="attributes format is attribute_name=value.", err="Attribute in wrong format %s" % attr)

            # change attributes on device
            device_status, device_state = _check_device(module, device)
            if device_status:
                result['changed'], result['msg'] = change_device_attr(module, attributes, device, force)
            else:
                result['msg'] = "Device %s does not exist." % device

            module.exit_json(**result)

        else:
            # discovery devices (cfgmgr)
            if device and device != 'all':
                device_status, device_state = _check_device(module, device)
                if device_status:
                    # run cfgmgr on specific device
                    result['changed'], result['msg'] = discover_device(module, device)

                else:
                    result['msg'] = "Device %s does not exist." % device

            else:
                result['changed'], result['msg'] = discover_device(module, device)

            module.exit_json(**result)

    elif state == 'absent' or state == 'defined':
        if not device:
            result['msg'] = "device is required to absent or defined state."

            module.exit_json(**result)

        else:
            # remove device
            check_device, device_state = _check_device(module, device)
            if check_device:
                if state == 'defined' and device_state == 'Defined':
                    result['changed'] = False
                    result['msg'] = 'Device %s already in Defined' % device

                else:
                    result['changed'], result['msg'] = remove_device(module, device, force, recursive, state)

            else:
                result['msg'] = "Device %s does not exist." % device

            module.exit_json(**result)

    else:
        result['msg'] = "Unexpected state %s." % state
        module.fail_json(**result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
