#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, 2018 Kairo Araujo <kairo@kairo.eti.br>
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
- Kairo Araujo (@kairoaraujo)
module: aix_devices
short_description: Manages AIX devices
description:
- This module discovers, defines, removes and modifies attributes of AIX devices.
version_added: '2.8'
options:
  attributes:
    description:
    - A list of device attributes.
    type: dict
  device:
    description:
    - The name of the device.
    - C(all) is valid to rescan C(available) all devices (AIX cfgmgr command).
    type: str
    required: true
  force:
    description:
    - Forces action.
    type: bool
    default: no
  recursive:
    description:
    - Removes or defines a device and children devices.
    type: bool
    default: no
  state:
    description:
    - Controls the device state.
    - C(available) (alias C(present)) rescan a specific device or all devices (when C(device) is not specified).
    - C(removed) (alias C(absent) removes a device.
    - C(defined) changes device to Defined state.
    type: str
    choices: [ available, defined, removed ]
    default: available
'''

EXAMPLES = r'''
- name: Scan new devices
  aix_devices:
    device: all
    state: available

- name: Scan new virtual devices (vio0)
  aix_devices:
    device: vio0
    state: available

- name: Removing IP alias to en0
  aix_devices:
    device: en0
    attributes:
      delalias4: 10.0.0.100,255.255.255.0

- name: Removes ent2
  aix_devices:
    device: ent2
    state: removed

- name: Put device en2 in Defined
  aix_devices:
    device: en2
    state: defined

- name: Removes ent4 (inexistent).
  aix_devices:
    device: ent4
    state: removed

- name: Put device en4 in Defined (inexistent)
  aix_devices:
    device: en4
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
    state: removed

- name: Changes en1 mtu to 9000 and disables arp.
  aix_devices:
    device: en1
    attributes:
      mtu: 900
      arp: off
    state: available

- name: Configure IP, netmask and set en1 up.
  aix_devices:
    device: en1
    attributes:
      netaddr: 192.168.0.100
      netmask: 255.255.255.0
      state: up
    state: available

- name: Adding IP alias to en0
  aix_devices:
    device: en0
    attributes:
      alias4: 10.0.0.100,255.255.255.0
    state: available
'''

RETURN = r''' # '''

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
    rc, lsdev_out, err = module.run_command(["%s" % lsdev_cmd, '-C', '-l', "%s" % device])

    if rc != 0:
        module.fail_json(msg="Failed to run lsdev", rc=rc, err=err)

    if lsdev_out:
        device_state = lsdev_out.split()[1]
        return True, device_state

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
    lsattr_cmd = module.get_bin_path('lsattr', True)
    rc, lsattr_out, err = module.run_command(["%s" % lsattr_cmd, '-El', "%s" % device, '-a', "%s" % attr])

    hidden_attrs = ['delalias4', 'delalias6']

    if rc == 255:

        if attr in hidden_attrs:
            current_param = ''
        else:
            current_param = None

        return current_param

    elif rc != 0:
        module.fail_json(msg="Failed to run lsattr: %s" % err, rc=rc, err=err)

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
        rc, cfgmgr_out, err = module.run_command(["%s" % cfgmgr_cmd, "%s" % device])
        changed = True
        msg = cfgmgr_out

    return changed, msg


def change_device_attr(module, attributes, device, force):
    """ Change AIX device attribute. """

    attr_changed = []
    attr_not_changed = []
    attr_invalid = []
    chdev_cmd = module.get_bin_path('chdev', True)

    for attr in list(attributes.keys()):
        new_param = attributes[attr]
        current_param = _check_device_attr(module, device, attr)

        if current_param is None:
            attr_invalid.append(attr)

        elif current_param != new_param:
            if force:
                cmd = ["%s" % chdev_cmd, '-l', "%s" % device, '-a', "%s=%s" % (attr, attributes[attr]), "%s" % force]
            else:
                cmd = ["%s" % chdev_cmd, '-l', "%s" % device, '-a', "%s=%s" % (attr, attributes[attr])]

            if not module.check_mode:
                rc, chdev_out, err = module.run_command(cmd)
                if rc != 0:
                    module.exit_json(msg="Failed to run chdev.", rc=rc, err=err)

            attr_changed.append(attributes[attr])
        else:
            attr_not_changed.append(attributes[attr])

    if len(attr_changed) > 0:
        changed = True
        attr_changed_msg = "Attributes changed: %s. " % ','.join(attr_changed)
    else:
        changed = False
        attr_changed_msg = ''

    if len(attr_not_changed) > 0:
        attr_not_changed_msg = "Attributes already set: %s. " % ','.join(attr_not_changed)
    else:
        attr_not_changed_msg = ''

    if len(attr_invalid) > 0:
        attr_invalid_msg = "Invalid attributes: %s " % ', '.join(attr_invalid)
    else:
        attr_invalid_msg = ''

    msg = "%s%s%s" % (attr_changed_msg, attr_not_changed_msg, attr_invalid_msg)

    return changed, msg


def remove_device(module, device, force, recursive, state):
    """ Puts device in defined state or removes device. """

    state_opt = {
        'removed': '-d',
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
        if state:
            rc, rmdev_out, err = module.run_command(["%s" % rmdev_cmd, "-l", "%s" % device, "%s" % recursive, "%s" % force])
        else:
            rc, rmdev_out, err = module.run_command(["%s" % rmdev_cmd, "-l", "%s" % device, "%s" % recursive])

        if rc != 0:
            module.fail_json(msg="Failed to run rmdev", rc=rc, err=err)

        msg = rmdev_out

    return changed, msg


def main():

    module = AnsibleModule(
        argument_spec=dict(
            attributes=dict(type='dict'),
            device=dict(type='str'),
            force=dict(type='bool', default=False),
            recursive=dict(type='bool', default=False),
            state=dict(type='str', default='available', choices=['available', 'defined', 'removed']),
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
    )

    if state == 'available' or state == 'present':
        if attributes:
            # change attributes on device
            device_status, device_state = _check_device(module, device)
            if device_status:
                result['changed'], result['msg'] = change_device_attr(module, attributes, device, force)
            else:
                result['msg'] = "Device %s does not exist." % device

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

    elif state == 'removed' or state == 'absent' or state == 'defined':
        if not device:
            result['msg'] = "device is required to removed or defined state."

        else:
            # Remove device
            check_device, device_state = _check_device(module, device)
            if check_device:
                if state == 'defined' and device_state == 'Defined':
                    result['changed'] = False
                    result['msg'] = 'Device %s already in Defined' % device

                else:
                    result['changed'], result['msg'] = remove_device(module, device, force, recursive, state)

            else:
                result['msg'] = "Device %s does not exist." % device

    else:
        result['msg'] = "Unexpected state %s." % state
        module.fail_json(**result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
