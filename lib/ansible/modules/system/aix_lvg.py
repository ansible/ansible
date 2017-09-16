#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Kairo Araujo <kairo@kairo.eti.br>
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
author: Kairo Araujo (@kairoaraujo)
module: aix_lvg
short_description: Configure LVM volume groups for AIX.
description:
  - This module creates, removes or resize volume groups on AIX LVM.
version_added: "2.5"
options:
  vg:
    description:
      - Volume group name.
    required: true
  pvs:
    description:
      - List of comma-separated devices to use as physical devices in this
        volume group. Required when creating or extending (C(present) state)
        the volume group. If not informed reducing (C(absent) state) the volume
        group will be removed.
    required: false
  pp_size:
    description:
      - Size of the physical partition in megabytes.
    required: false
  vg_type:
    description:
      - Volume group type.
    choices: [normal, big, scalable]
    default: normal
    required: false
  state:
    description:
      - Control if the volume group exists and volume group AIX state varyonvg
        C(varyon) or varyoffvg C(varyoff).
    choices: [ present, absent, varyon, varyoff ]
    default: present
    required: false
  force:
    description:
      - Forces volume group creation.
    choices: ["yes", "no"]
    default: "no"
notes:
  - AIX will permit remove VG only if all LV/Filesystems aren't busy.
  - Module does not modify PP size for already present volume group.
'''

EXAMPLES = '''
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

RETURN = '''
changed:
  description: Return changed for aix_lvg actions as true or false.
  returned: always
  type: boolean
  version_added: 2.5
msg:
  description: Return message regarding the action.
  returned: always
  type: string
  version_added: 2.5
'''

from ansible.module_utils.basic import AnsibleModule

# Command option parameters
vg_opt = {
    'normal': '',
    'big': '-B',
    'scalable': '-S',
}

force_opt = {
    True: '-f',
    False: ''
}


def _validate_pv(module, vg, pvs):
    """
    Function to validate if the physical volume (PV) is not already in use by
    another volume group or Oracle ASM.

    :param module: Ansible module argument spec.
    :param vg: Volume group name.
    :param pvs: Physical volume list.
    :return: [bool, message] or module.fail_json for errors.
    """

    lspv_cmd = module.get_bin_path("lspv", True)
    rc, current_lspv, err = module.run_command("%s" % lspv_cmd)
    if rc != 0:
        module.fail_json(
            msg="Failed executing lspv command.", rc=rc, err=err)

    for pv in pvs:
        # get pv list
        lspv_list = {}
        for line in current_lspv.splitlines():
            pv_data = line.split()
            lspv_list[pv_data[0]] = pv_data[2]

        # check if pv exists and is free
        if pv in lspv_list.keys():
            if lspv_list[pv] == 'None':
                # disk None, looks free
                # check if PV is not already in use by Oracle ASM
                lquerypv_cmd = module.get_bin_path("lquerypv", True)
                rc, current_lquerypv, err = module.run_command(
                    "%s -h /dev/%s 20 10" % (lquerypv_cmd, pv))
                if rc != 0:
                    module.fail_json(
                        msg="Failed executing lquerypv command.", rc=rc,
                        err=err)

                if 'ORCLDISK' in current_lquerypv:
                    module.fail_json(
                        "Physical volume %s is already used by Oracle ASM."
                        % pv)

                msg = "Physical volume %s is ok to be used." % pv
                return True, msg

            # check if PV is already in use for the same vg
            elif vg == lspv_list[pv]:
                msg = ("Physical volume %s is already used by volume group %s."
                       % (pv, lspv_list[pv]))
                return False, msg
            else:
                module.fail_json(
                    msg="Physical volume %s is in use by another volume group "
                        "%s." % (pv, lspv_list[pv]))

        else:
            module.fail_json(msg="Physical volume %s doesn't exist." % pv)


def _validate_vg(module, vg):
    """
    Check the current state of volume group.

    :param module: Ansible module argument spec.
    :param vg: Volume Group name.
    :return: True (VG in varyon state) or False (VG in varyoff state) or
             None (VG does not exist), message.
    """
    lsvg_cmd = module.get_bin_path("lsvg", True)
    rc, current_active_vgs, err = module.run_command("%s -o" % lsvg_cmd)
    if rc != 0:
        module.fail_json(msg="Failed executing %s command." % lsvg_cmd)

    rc, current_all_vgs, err = module.run_command("%s" % lsvg_cmd)
    if rc != 0:
        module.fail_json(msg="Failed executing %s command." % lsvg_cmd)

    if vg in current_all_vgs and vg not in current_active_vgs:
        msg = "Volume group %s is in varyoff state." % vg
        return False, msg
    elif vg in current_active_vgs:
        msg = "Volume group %s is in varyon state." % vg
        return True, msg
    else:
        msg = "Volume group %s does not exist." % vg
        return None, msg


def create_extend_vg(module, vg, pvs, pp_size, vg_type, force, vg_validation):
    """ creates or extend a volume group"""

    # validate if PV are not already in use
    pv_state, msg = _validate_pv(module, vg, pvs)
    if not pv_state:
        module.exit_json(changed=False, msg=msg)

    vg_state, msg = vg_validation
    if vg_state is False:
        # volume group is varyoff
        module.exit_json(
            changed=False, msg=msg)
    elif vg_state is True:
        # volume group extension
        extendvg_cmd = module.get_bin_path("extendvg", True)
        rc, _, err = module.run_command(
            "%s %s %s" % (extendvg_cmd, vg, " ".join(pvs)))
        if rc == 0:
            module.exit_json(
                changed=True, msg="Volume group %s extended." % vg)
        else:
            module.exit_json(
                changed=False, msg="Extending volume group %s has failed." % vg,
                rc=rc, err=err)
    elif vg_state is None:
        # volume group creation
        mkvg_cmd = module.get_bin_path("mkvg", True)
        rc, _, err = module.run_command(
            "%s %s %s %s -y %s %s" % (
                mkvg_cmd, vg_opt[vg_type], pp_size, force_opt[force],
                vg, ' '.join(pvs)))

        if rc == 0:
            module.exit_json(changed=True, msg="Volume group %s created." % vg)
        else:
            module.exit_json(
                changed=False, msg="Creating volume group %s failed." % vg,
                rc=rc, err=err)


def reduce_vg(module, vg, pvs, vg_validation):

    vg_state, msg = vg_validation

    if vg_state is False:
        module.exit_json(
            changed=False, msg=msg)

    if pvs is None:
        # Remove VG if pvs are note informed
        # Remark: AIX will permit remove only if the VG has not LVs
        lsvg_cmd = module.get_bin_path("lsvg", True)
        rc, current_pvs, err = module.run_command("%s -p %s" % (lsvg_cmd, vg))
        if rc != 0:
            module.fail_json(msg="Failing to execute %s command." % lsvg_cmd)

        pvs_to_remove = []
        for line in current_pvs.splitlines()[2:]:
            pvs_to_remove.append(line.split()[0])

        reduce_msg = "Volume group %s removed." % vg
    else:
        pvs_to_remove = pvs
        reduce_msg = (
            "Physical volume(s) %s removed from Volume group %s." % (
                " ".join(pvs_to_remove), vg))

    if len(pvs_to_remove) > 0:
        reducevg_cmd = module.get_bin_path("reducevg", True)
        rc, _, err = module.run_command(
            "%s -df %s %s" % (reducevg_cmd, vg, " ".join(pvs_to_remove)))

        if rc == 0:
            module.exit_json(changed=True, msg=reduce_msg)
        else:
            module.exit_json(
                changed=False, msg="Unable to remove %s." % vg, rc=rc, err=err)


def state_vg(module, vg, state, vg_validation):

    vg_state, msg = vg_validation

    if vg_state is None:
        module.fail_json(msg=msg)

    if state == 'varyon':
        if vg_state is False:
            varyonvg_cmd = module.get_bin_path("varyonvg", True)
            rc, varyonvg_out, err = module.run_command(
                "%s %s" % (varyonvg_cmd, vg))
            if rc != 0:
                module.exit_json(changed=False, rc=rc, err=err)
            else:
                module.exit_json(
                    changed=True, msg="Varyon volume group %s completed" % vg)
        else:
            module.exit_json(
                changed=False, msg=msg)

    elif state == 'varyoff':
        if vg_state is True:
            varyonvg_cmd = module.get_bin_path("varyoffvg", True)
            rc, varyonvg_out, err = module.run_command(
                "%s %s" % (varyonvg_cmd, vg))
            if rc != 0:
                module.exit_json(changed=False, msg=err)
            else:
                module.exit_json(
                    changed=True, msg="Varyoff volume group %s completed" % vg)

        else:
            module.exit_json(
                changed=False, msg=msg)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            vg=dict(required=True),
            pvs=dict(type="list", default=None),
            pp_size=dict(type="int", default=None),
            vg_type=dict(choices=["normal", "big", "scalable"],
                         default="normal"),
            state=dict(choices=["absent", "present", "varyon", "varyoff"],
                       default="present"),
            force=dict(type="bool", default=False)
        ))

    vg = module.params["vg"]
    state = module.params["state"]
    pp_size = module.params["pp_size"]
    vg_type = module.params["vg_type"]
    pvs = module.params["pvs"]
    force = module.params["force"]

    if pp_size is None:
        pp_size = ""
    else:
        pp_size = "-s %s" % pp_size

    vg_validation = _validate_vg(module, vg)

    if state == 'present':
        if not pvs:
            module.fail_json(msg='pvs is required to state "present".')
        else:
            create_extend_vg(module, vg, pvs, pp_size, vg_type, force,
                             vg_validation)

    elif state == 'absent':
        reduce_vg(module, vg, pvs, vg_validation)

    elif state == 'varyon' or 'varyoff':
        state_vg(module, vg, state, vg_validation)

if __name__ == '__main__':
    main()
