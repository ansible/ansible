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
    choices: [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
    default: 32
    required: false
  vg_type:
    description:
      - Volume group type.
    choices: [normal, big, scalable]
    default: normal
    required: false
  state:
    description:
      - Control if the volume group exists.
    choices: [ present, absent ]
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

# vg mode parameter
vg_mode = {
    'normal': '',
    'big': '-B',
    'scalable': '-S',
}

# force parameter
force_mode = {
    True: '-f',
    False: ''
}


def _validate_pv(module, pvname):
    """
    Function to validate if the physical volume (PV) is not already in use by
    another volume group or Oracle ASM

    :param module: Ansible module argument spec
    :param pvname: Physical Volume name
    :return: [True, message]
    """

    lspv_cmd = module.get_bin_path('lspv', True)
    rc, current_lspv, err = module.run_command('%s ' % lspv_cmd)
    if rc != 0:
        module.fail_json(msg="Failed executing lspv command.", rc=rc,
                         err=err)

    # check if PV is not already for another volume group
    for line in current_lspv.splitlines():
        if line.startswith(pvname):
            if line.split()[-1] != 'None':
                module.fail_json(msg="Physical Volume %s already in use." %
                                     pvname)

    lquerypv_cmd = module.get_bin_path('lquerypv', True)
    rc, current_lquerypv, err = module.run_command('%s -h /dev/%s 20 10' %
                                                   (lquerypv_cmd, pvname))
    if rc != 0:
        module.fail_json(msg="Failed executing lquerypv command.", rc=rc,
                         err=err)

    # check if PV is not already in use by Oracle ASM
    if "ORCLDISK" in current_lquerypv:
        msg = "PV %s is already used by Oracle ASM" % pvname

        return False, msg

    msg = "PV is ok to be used"

    return True, msg


def create_extend_vg(module, vg, pvs, pp_size, vg_type, force):
    """ creates or extend a volume group"""

    # validate if PV are not already in use
    for pv in pvs:
        pv_test_result = _validate_pv(module, pv)
        if not pv_test_result[0]:
            module.fail_json(msg=pv_test_result[1])

    # perform action creation or extension
    # if vg doesn't exist, it will create
    # if vg already exists, it will try to extend using the PVs
    lsvg_cmd = module.get_bin_path('lsvg', True)
    rc, current_vgs, err = module.run_command('%s' % lsvg_cmd)
    if rc != 0:
        module.fail_json(msg='Failed executing %s command' % lsvg_cmd)

    if vg in current_vgs:
        # volume group extension
        extendvg_cmd = module.get_bin_path('extendvg', True)
        rc, _, err = module.run_command('%s %s %s' % (extendvg_cmd, vg,
                                                      ' '.join(pvs)))
        if rc == 0:
            module.exit_json(changed=True, msg="Volume group %s extended."
                                               % vg)
        else:
            module.exit_json(changed=False, msg='Extending volume group %s '
                                                'has failed'
                                                % vg, rc=rc, err=err)

    else:
        # volume group creation
        mkvg_cmd = module.get_bin_path('mkvg', True)
        rc, _, err = module.run_command('%s %s -s %s %s -y %s %s'
                                        % (mkvg_cmd, vg_mode[vg_type], pp_size,
                                           force_mode[force], vg, ' '.join(pvs)
                                           ))
        if rc == 0:
            module.exit_json(changed=True, msg="Volume group %s created" % vg)
        else:
            module.exit_json(changed=False, msg='Creating volume group %s '
                                                'failed' % vg, rc=rc, err=err)


def reduce_vg(module, vg, pvs):

    if pvs is None:
        # Remove VG if pvs are note informed
        # Remark: AIX will permit remove only if the VG has not LVs
        lsvg_cmd = module.get_bin_path('lsvg', True)
        rc, current_pvs, err = module.run_command('%s -p %s' % (lsvg_cmd, vg))
        if rc != 0:
            module.fail_json(msg='Failing to execute %s command' % lsvg_cmd)

        pvs_to_remove = []
        for line in current_pvs.splitlines()[2:]:
                pvs_to_remove.append(line.split()[0])

        reduce_msg = "Volume group %s removed" % vg

    else:
        pvs_to_remove = pvs
        reduce_msg = ("PV(s) %s removed from Volume group %s" %
                      (' '.join(pvs_to_remove), vg))

    if len(pvs_to_remove) > 0:
        reducevg_cmd = module.get_bin_path('reducevg', True)
        rc, _, err = module.run_command('%s -df %s %s'
                                        % (reducevg_cmd, vg,
                                           ' '.join(pvs_to_remove)))

        if rc == 0:
            module.exit_json(changed=True, msg=reduce_msg)
        else:
            module.exit_json(changed=False, msg='Unable to remove %s' % vg,
                             rc=rc, err=err)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            vg=dict(required=True),
            pvs=dict(type="list", default=None),
            pp_size=dict(type="int", choices=[1, 2, 4, 8, 16, 32, 64, 128, 256,
                                              512, 1024], default=32),
            vg_type=dict(choices=["normal", "big", "scalable"],
                         default="normal"),
            state=dict(choices=["absent", "present"], default="present"),
            force=dict(type="bool", default=False)
        ),
        supports_check_mode=True,
    )

    vg = module.params['vg']
    state = module.params['state']
    pp_size = module.params['pp_size']
    vg_type = module.params['vg_type']
    pvs = module.params['pvs']
    force = module.params['force']

    if state == 'present':

        if not pvs:
            module.fail_json(msg="pvs is required to state 'present' ")

        else:
            create_extend_vg(module, vg, pvs, pp_size, vg_type, force)

    if state == 'absent':
        reduce_vg(module, vg, pvs)

if __name__ == '__main__':
    main()
