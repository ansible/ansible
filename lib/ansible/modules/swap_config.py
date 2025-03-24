# -*- coding: utf-8 -*-

# Copyright: (C) 2025 Nidhi S <sinha.nidhi02@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt).

from __future__ import annotations


DOCUMENTATION = r"""
---
module: swap_config
short_description: Manage swap space on Linux systems (both swap files and logical volumes)
description: |
    This module allows for the management of swap space on Linux systems.
    It supports operations such as creating, resizing, enabling, disabling, and removing swap files or logical volumes (LVM).
    The module can handle both swap files and LVM swap logical volumes.
    Additionally, this module can optionally update the '/etc/fstab' file when adding or removing swap.
version_added: "2.19"
author: "Nidhi Sinha"
options:
    state:
        description:
            - If 'present', create the swap.
            - If 'absent', remove the swap.
            - If 'enabled', enable the swap.
            - If 'disabled', disable the swap.
            - If 'resized', resize the swap space.
        required: true
        type: str
        choices: [present, absent, enabled, disabled, resized]
    is_swapfile:
        description:
            - Defines whether the swap is a file or logical volume.
            - If True, Treat it as a swap file.
            - If False, Treat it as a logical volume (LVM).
        required: false
        type: bool
        default: no
    swap_name:
        description:
            - Name of the swap file or logical volume.
        required: true
        type: str
        aliases: ['lv_name']
    vg_name:
        description:
            - The name of the volume group (VG) for LVM swap (only used when 'is_swapfile' is 'False').
        required: false
        type: str
        default: ""
        aliases: ['volume_group']
    swap_size:
        description:
            - The size of the swap file or logical volume. The size can be specified using a string with units like 'M' for megabytes or 'G' for gigabytes.
        required: false
        type: str
        aliases: ['size']
    edit_fstab:
        description:
            - If 'True', the module will automatically update the '/etc/fstab' file to add or remove the swap entry.
            - Else, nothing to do.
        required: false
        type: bool
        default: no
        aliases: ['fstab']
notes:
  - This module does not support non-Linux systems.
"""

EXAMPLES = r"""
# Create a swap file
- name: Create swap file
  swap_config:
    state: present
    is_swapfile: true
    swap_name: /swapfile
    swap_size: 2G
    edit_fstab: true

# Enable the swap file
- name: Enable swap file
  swap_config:
    state: enabled
    is_swapfile: true
    swap_name: /swapfile

# Disable the swap file
- name: Disable swap file
  swap_config:
    state: disabled
    is_swapfile: true
    swap_name: /swapfile

# Remove the swap file
- name: Remove swap file
  swap_config:
    state: absent
    is_swapfile: true
    swap_name: /swapfile
    edit_fstab: true

# Resize a swap logical volume
- name: Resize swap logical volume
  swap_config:
    state: resized
    is_swapfile: false
    vg_name: my_vg
    swap_name: swap_lv
    swap_size: 4G
"""

RETURN = r"""
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: '/swapfile'

message:
    description: |
        A message describing the result of the operation, including details such as
        whether the swap was created, resized, enabled, disabled, or removed.
    type: str
    returned: always
    sample: '/swapfile has been successfully created.'

changed:
    description: |
        A boolean indicating whether a change was made to the system.
        This will be 'true' if the operation resulted in a change (e.g., swap created, resized, etc.).
    type: bool
    returned: always
    sample: true
"""


from ansible.module_utils.basic import AnsibleModule    # type: ignore
import os
import re


def convert_size_to_block(swap_size):
    """Convert a size string like '2G', '512M' to MB"""
    match = re.match(r"(\d+)([GgMmKk])", swap_size)
    if match:
        num = int(match.group(1))
        unit = match.group(2).upper()
        # Convert size in block
        if unit == 'G':
            return num * 1024 * 1024
        elif unit == 'M':
            return num * 1024
        elif unit == 'K':
            return num
    return 0      # Invalid


def update_fstab(is_swapfile, vg_name, swap_name, action):
    """Update the /etc/fstab file when creating or removing a swap."""
    fstab_path = '/etc/fstab'

    if is_swapfile:
        full_path = f"{swap_name}"
    else:
        full_path = f"/dev/{vg_name}/{swap_name}"
    entry = f"{full_path} none swap defaults 0 0\n"

    try:
        with open(fstab_path, 'r') as fstab:
            lines = fstab.readlines()

        if action == "add" and entry not in lines:
            # Add the swap entry to the /etc/fstsb
            with open(fstab_path, 'a') as fstab:
                fstab.write(entry)
        elif action == "remove" and entry in lines:
            with open(fstab_path, 'w') as fstab:
                lines = [line for line in lines if line != entry]
                fstab.writelines(lines)
    except IOError as e:
        raise IOError(f"Error updating fstab: {str(e)}")


def validate_swap(is_swapfile, vg_name, swap_name):
    """Check if swap or logical volume exists and handle check mode logic."""
    if is_swapfile:
        if os.path.exists(swap_name):
            return True, f"Swap file {swap_name} already exists."
        return False, f"Swap file {swap_name} does not exist."
    else:
        full_path = f"/dev/{vg_name}/{swap_name}"
        if os.path.exists(full_path):
            return True, f"Swap LV {swap_name} already exists."
        return False, f"Swap LV {swap_name} does not exist."


def create_swap(module, is_swapfile, vg_name, swap_name, swap_size, edit_fstab):
    """Function to create a swap file"""
    if module.check_mode:
        exists, msg = validate_swap(is_swapfile, vg_name, swap_name)
        if not exists:
            msg = f"Would create swap named {swap_name} size {swap_size}"
        return module.exit_json(changed=not exists, msg=msg)
    # Create the LVM swap
    try:
        # Check whether swap is present or not
        exists, msg = validate_swap(is_swapfile, vg_name, swap_name)
        if exists:
            module.fail_json(changed=not exists, msg=msg)

        if is_swapfile:
            block_count = int(convert_size_to_block(swap_size))
            if block_count == 0:
                module.fail_json(msg="Invalid swap size format. Please use 'G', 'M', or 'K'.")
            module.run_command(f"dd if=/dev/zero of=/{swap_name} bs=1024 count={block_count} status=progress")
            module.run_command(f"mkswap {swap_name}")
            os.chmod(swap_name, 0o600)
        else:
            # Run the dd command to create a LVM Swap of the required size
            module.run_command(f"lvcreate {vg_name} -n {swap_name} -L {swap_size}")
            # Format the new swap space
            module.run_command(f"mkswap /dev/{vg_name}/{swap_name}")

        # Optionally edit fstab for swap
        if edit_fstab:
            update_fstab(is_swapfile, vg_name, swap_name, "add")

        return module.exit_json(changed=True, msg=f"{swap_name} has been created of {swap_size}")
    except Exception as e:
        module.fail_json(msg=f"Failed to create swap: {str(e)}")


def enable_swap(module, is_swapfile, vg_name, swap_name):
    """Function to activate swap on logical volume"""
    if module.check_mode:
        exists, msg = validate_swap(is_swapfile, vg_name, swap_name)
        if exists:
            msg = f"Would enabled {swap_name}"
        return module.exit_json(changed=not exists, msg=msg)

    try:
        exists, msg = validate_swap(is_swapfile, vg_name, swap_name)
        if not exists:
            module.fail_json(changed=exists, msg=msg)
        if is_swapfile:
            module.run_command(f"swapon {swap_name}")
        else:
            full_path = f"/dev/{vg_name}/{swap_name}"
            module.run_command(f"swapon -a {full_path}")
        return module.exit_json(changed=True, msg=f"{swap_name} has been enabled")
    except Exception as e:
        module.fail_json(msg=f"Failed to enable swap: {str(e)}")


def disable_swap(module, is_swapfile, vg_name, swap_name):
    """Function to disable swap file"""
    if module.check_mode:
        exists, msg = validate_swap(is_swapfile, vg_name, swap_name)
        if exists:
            msg = f"Would disabled {swap_name}"
        return module.exit_json(changed=not exists, msg=msg)

    try:
        exists, msg = validate_swap(is_swapfile, vg_name, swap_name)
        if not exists:
            module.fail_json(changed=exists, msg=msg)

        if is_swapfile:
            module.run_command(f"swapoff {swap_name}")
        else:
            full_path = f"/dev/{vg_name}/{swap_name}"
            module.run_command(f"swapoff -v {full_path}")

        return module.exit_json(changed=True, msg=f"{swap_name} has been disabled")
    except Exception as e:
        module.fail_json(msg=f"Failed to disable swap: {str(e)}")


def remove_swap(module, is_swapfile, vg_name, swap_name, edit_fstab):
    """Function to remove swap volume group"""
    if module.check_mode:
        exists, msg = validate_swap(is_swapfile, vg_name, swap_name)
        if exists:
            msg = f"Would remove {swap_name}"
        return module.exit_json(changed=not exists, msg=msg)

    try:
        exists, msg = validate_swap(is_swapfile, vg_name, swap_name)
        if not exists:
            module.fail_json(changed=exists, msg=msg)
        if is_swapfile:
            os.remove(swap_name)
        else:
            full_path = f"/dev/{vg_name}/{swap_name}"
            module.run_command(f"lvremove {full_path}")
        # Optionally remove fstab for swap
        if edit_fstab:
            update_fstab(is_swapfile, vg_name, swap_name, "remove")
        return module.exit_json(changed=True, msg=f"Swap {swap_name} has been removed.")
    except Exception as e:
        module.fail_json(msg=f"Failed to remove swap: {str(e)}")


def resize_swap(module, is_swapfile, vg_name, swap_name, swap_size):
    """Function to resize swap space"""
    if module.check_mode:
        exists, msg = validate_swap(is_swapfile, vg_name, swap_name)
        if exists:
            msg = f"Would resize {swap_name} to size {swap_size}"
        return module.exit_json(changed=not exists, msg=msg)
    try:
        if is_swapfile:
            if os.path.exists(swap_name):
                module.fail_json(changed=False, msg=f"Swap file {swap_name} already exists.")
            #
            block_count = int(convert_size_to_block(swap_size))
            if block_count == 0:
                module.fail_json(msg="Invalid swap size format. Please use 'G', 'M', or 'K'.")
            module.run_command(f"dd if=/dev/zero of={swap_name} bs=1024 count={block_count} status=progress")
            module.run_command(f"mkswap {swap_name}")
            os.chmod(swap_name, 0o600)
        else:
            full_path = f"/dev/{vg_name}/{swap_name}"
            if not os.path.exists(full_path):
                module.fail_json(changed=False, msg="Swap logical volume does not exists.")
            module.run_command(f"lvresize {full_path} -L +{swap_size}")
            module.run_command(f"mkswap {full_path}")
        return module.exit_json(changed=True, msg=f"{swap_name} has been resized by {swap_size}.")
    except Exception as e:
        module.fail_json(msg=f"Failed to resize swap: {str(e)}")


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', choices=['present', 'absent', 'disabled', 'enabled', 'resized'], required=True),
            is_swapfile=dict(type='bool', default=False),
            swap_name=dict(type='str', required=True, aliases=['lv_name']),
            vg_name=dict(type='str', required=False, aliases=['volume_group'], default=''),
            swap_size=dict(type='str', required=False, aliases=['size']),
            edit_fstab=dict(type='bool', default=False, aliases=['fstab']),
        ),
        supports_check_mode=True
    )

    params = module.params
    state = params['state']
    is_swapfile = params['is_swapfile']
    swap_name = params['swap_name']
    vg_name = params['vg_name']
    swap_size = params['swap_size']
    edit_fstab = params['edit_fstab']

    if state in ['present', 'resized'] and swap_size is None:
        module.fail_json(msg="The 'swap_size' parameter is required when state is 'present' or 'resized'.")

    if state == 'present':
        # Ensure the swap is created
        create_swap(module, is_swapfile, vg_name, swap_name, swap_size, edit_fstab)
    elif state == 'enabled':
        # Enable the swap
        enable_swap(module, is_swapfile, vg_name, swap_name)
    elif state == 'disabled':
        # Disable the swap
        disable_swap(module, is_swapfile, vg_name, swap_name)
    elif state == 'absent':
        # Ensure the swap is removed
        remove_swap(module, is_swapfile, vg_name, swap_name, edit_fstab)
    elif state == 'resized':
        # Resize the swap
        resize_swap(module, is_swapfile, vg_name, swap_name, swap_size)


if __name__ == "__main__":
    main()