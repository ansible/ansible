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

DOCUMENTATION = r'''
---
author:
- Kairo Araujo (@kairoaraujo)
module: aix_lvg
short_description: Manage LVM volume groups on AIX
description:
- This module creates, removes or resize volume groups on AIX LVM.
version_added: '2.8'
options:
  force:
    description:
    - Force volume group creation.
    type: bool
    default: no
  pp_size:
    description:
    - The size of the physical partition in megabytes.
    type: int
  pvs:
    description:
    - List of comma-separated devices to use as physical devices in this volume group.
    - Required when creating or extending (C(present) state) the volume group.
    - If not informed reducing (C(absent) state) the volume group will be removed.
    type: list
  state:
    description:
    - Control if the volume group exists and volume group AIX state varyonvg C(varyon) or varyoffvg C(varyoff).
    type: str
    choices: [ absent, present, varyoff, varyon ]
    default: present
  vg:
    description:
    - The name of the volume group.
    type: str
    required: true
  vg_type:
    description:
    - The type of the volume group.
    type: str
    choices: [ big, normal, scalable ]
    default: normal
notes:
- AIX will permit remove VG only if all LV/Filesystems are not busy.
- Module does not modify PP size for already present volume group.
'''

EXAMPLES = r'''
- name: Create a volume group datavg
  aix_lvg:
    vg: datavg
    pp_size: 128
    vg_type: scalable
    state: present

- name: Removing a volume group datavg
  aix_lvg:
    vg: datavg
    state: absent

- name: Extending rootvg
  aix_lvg:
    vg: rootvg
    pvs: hdisk1
    state: present

- name: Reducing rootvg
  aix_lvg:
    vg: rootvg
    pvs: hdisk1
    state: absent
'''

RETURN = r''' # '''

from ansible.module_utils.basic import AnsibleModule


def _validate_pv(module, vg, pvs):
    """
    Function to validate if the physical volume (PV) is not already in use by
    another volume group or Oracle ASM.

    :param module: Ansible module argument spec.
    :param vg: Volume group name.
    :param pvs: Physical volume list.
    :return: [bool, message] or module.fail_json for errors.
    """

    lspv_cmd = module.get_bin_path('lspv', True)
    rc, current_lspv, stderr = module.run_command("%s" % lspv_cmd)
    if rc != 0:
        module.fail_json(msg="Failed executing 'lspv' command.", rc=rc, stdout=current_lspv, stderr=stderr)

    for pv in pvs:
        # Get pv list.
        lspv_list = {}
        for line in current_lspv.splitlines():
            pv_data = line.split()
            lspv_list[pv_data[0]] = pv_data[2]

        # Check if pv exists and is free.
        if pv not in lspv_list.keys():
            module.fail_json(msg="Physical volume '%s' doesn't exist." % pv)

        if lspv_list[pv] == 'None':
            # Disk None, looks free.
            # Check if PV is not already in use by Oracle ASM.
            lquerypv_cmd = module.get_bin_path('lquerypv', True)
            rc, current_lquerypv, stderr = module.run_command("%s -h /dev/%s 20 10" % (lquerypv_cmd, pv))
            if rc != 0:
                module.fail_json(msg="Failed executing lquerypv command.", rc=rc, stdout=current_lquerypv, stderr=stderr)

            if 'ORCLDISK' in current_lquerypv:
                module.fail_json("Physical volume '%s' is already used by Oracle ASM." % pv)

            msg = "Physical volume '%s' is ok to be used." % pv
            return True, msg

        # Check if PV is already in use for the same vg.
        elif vg != lspv_list[pv]:
            module.fail_json(msg="Physical volume '%s' is in use by another volume group '%s'." % (pv, lspv_list[pv]))

        msg = "Physical volume '%s' is already used by volume group '%s'." % (pv, lspv_list[pv])
        return False, msg


def _validate_vg(module, vg):
    """
    Check the current state of volume group.

    :param module: Ansible module argument spec.
    :param vg: Volume Group name.
    :return: True (VG in varyon state) or False (VG in varyoff state) or
             None (VG does not exist), message.
    """
    lsvg_cmd = module.get_bin_path('lsvg', True)
    rc, current_active_vgs, err = module.run_command("%s -o" % lsvg_cmd)
    if rc != 0:
        module.fail_json(msg="Failed executing '%s' command." % lsvg_cmd)

    rc, current_all_vgs, err = module.run_command("%s" % lsvg_cmd)
    if rc != 0:
        module.fail_json(msg="Failed executing '%s' command." % lsvg_cmd)

    if vg in current_all_vgs and vg not in current_active_vgs:
        msg = "Volume group '%s' is in varyoff state." % vg
        return False, msg

    if vg in current_active_vgs:
        msg = "Volume group '%s' is in varyon state." % vg
        return True, msg

    msg = "Volume group '%s' does not exist." % vg
    return None, msg


def create_extend_vg(module, vg, pvs, pp_size, vg_type, force, vg_validation):
    """ Creates or extend a volume group. """

    # Command option parameters.
    force_opt = {
        True: '-f',
        False: ''
    }

    vg_opt = {
        'normal': '',
        'big': '-B',
        'scalable': '-S',
    }

    # Validate if PV are not already in use.
    pv_state, msg = _validate_pv(module, vg, pvs)
    if not pv_state:
        changed = False
        return changed, msg

    vg_state, msg = vg_validation
    if vg_state is False:
        changed = False
        return changed, msg

    elif vg_state is True:
        # Volume group extension.
        changed = True
        msg = ""

        if not module.check_mode:
            extendvg_cmd = module.get_bin_path('extendvg', True)
            rc, output, err = module.run_command("%s %s %s" % (extendvg_cmd, vg, ' '.join(pvs)))
            if rc != 0:
                changed = False
                msg = "Extending volume group '%s' has failed." % vg
                return changed, msg

        msg = "Volume group '%s' extended." % vg
        return changed, msg

    elif vg_state is None:
        # Volume group creation.
        changed = True
        msg = ''

        if not module.check_mode:
            mkvg_cmd = module.get_bin_path('mkvg', True)
            rc, output, err = module.run_command("%s %s %s %s -y %s %s" % (mkvg_cmd, vg_opt[vg_type], pp_size, force_opt[force], vg, ' '.join(pvs)))
            if rc != 0:
                changed = False
                msg = "Creating volume group '%s' failed." % vg
                return changed, msg

        msg = "Volume group '%s' created." % vg
        return changed, msg


def reduce_vg(module, vg, pvs, vg_validation):
    vg_state, msg = vg_validation

    if vg_state is False:
        changed = False
        return changed, msg

    elif vg_state is None:
        changed = False
        return changed, msg

    # Define pvs_to_remove (list of physical volumes to be removed).
    if pvs is None:
        # Remove VG if pvs are note informed.
        # Remark: AIX will permit remove only if the VG has not LVs.
        lsvg_cmd = module.get_bin_path('lsvg', True)
        rc, current_pvs, err = module.run_command("%s -p %s" % (lsvg_cmd, vg))
        if rc != 0:
            module.fail_json(msg="Failing to execute '%s' command." % lsvg_cmd)

        pvs_to_remove = []
        for line in current_pvs.splitlines()[2:]:
            pvs_to_remove.append(line.split()[0])

        reduce_msg = "Volume group '%s' removed." % vg
    else:
        pvs_to_remove = pvs
        reduce_msg = ("Physical volume(s) '%s' removed from Volume group '%s'." % (' '.join(pvs_to_remove), vg))

    # Reduce volume group.
    if len(pvs_to_remove) <= 0:
        changed = False
        msg = "No physical volumes to remove."
        return changed, msg

    changed = True
    msg = ''

    if not module.check_mode:
        reducevg_cmd = module.get_bin_path('reducevg', True)
        rc, stdout, stderr = module.run_command("%s -df %s %s" % (reducevg_cmd, vg, ' '.join(pvs_to_remove)))
        if rc != 0:
            module.fail_json(msg="Unable to remove '%s'." % vg, rc=rc, stdout=stdout, stderr=stderr)

    msg = reduce_msg
    return changed, msg


def state_vg(module, vg, state, vg_validation):
    vg_state, msg = vg_validation

    if vg_state is None:
        module.fail_json(msg=msg)

    if state == 'varyon':
        if vg_state is True:
            changed = False
            return changed, msg

        changed = True
        msg = ''
        if not module.check_mode:
            varyonvg_cmd = module.get_bin_path('varyonvg', True)
            rc, varyonvg_out, err = module.run_command("%s %s" % (varyonvg_cmd, vg))
            if rc != 0:
                module.fail_json(msg="Command 'varyonvg' failed.", rc=rc, err=err)

        msg = "Varyon volume group %s completed." % vg
        return changed, msg

    elif state == 'varyoff':
        if vg_state is False:
            changed = False
            return changed, msg

        changed = True
        msg = ''

        if not module.check_mode:
            varyonvg_cmd = module.get_bin_path('varyoffvg', True)
            rc, varyonvg_out, stderr = module.run_command("%s %s" % (varyonvg_cmd, vg))
            if rc != 0:
                module.fail_json(msg="Command 'varyoffvg' failed.", rc=rc, stdout=varyonvg_out, stderr=stderr)

        msg = "Varyoff volume group %s completed." % vg
        return changed, msg


def main():
    module = AnsibleModule(
        argument_spec=dict(
            force=dict(type='bool', default=False),
            pp_size=dict(type='int'),
            pvs=dict(type='list'),
            state=dict(type='str', default='present', choices=['absent', 'present', 'varyoff', 'varyon']),
            vg=dict(type='str', required=True),
            vg_type=dict(type='str', default='normal', choices=['big', 'normal', 'scalable'])
        ),
        supports_check_mode=True,
    )

    force = module.params['force']
    pp_size = module.params['pp_size']
    pvs = module.params['pvs']
    state = module.params['state']
    vg = module.params['vg']
    vg_type = module.params['vg_type']

    if pp_size is None:
        pp_size = ''
    else:
        pp_size = "-s %s" % pp_size

    vg_validation = _validate_vg(module, vg)

    if state == 'present':
        if not pvs:
            changed = False
            msg = "pvs is required to state 'present'."
            module.fail_json(msg=msg)
        else:
            changed, msg = create_extend_vg(module, vg, pvs, pp_size, vg_type, force, vg_validation)

    elif state == 'absent':
        changed, msg = reduce_vg(module, vg, pvs, vg_validation)

    elif state == 'varyon' or state == 'varyoff':
        changed, msg = state_vg(module, vg, state, vg_validation)

    else:
        changed = False
        msg = "Unexpected state"

    module.exit_json(changed=changed, msg=msg, state=state)


if __name__ == '__main__':
    main()
