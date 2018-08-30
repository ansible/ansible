#!/usr/bin/python
#
# Copyright (c) 2018, Luca 'remix_tj' Lorenzetto <lorenzetto.luca@gmail.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)


__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: emc_vnx_mv_promote

short_description: Promote mirrorview Mirror or Consistency Group on EMC VNX

version_added: "2.7"

description:
    - "This module manages promotion of a mirror view async connection."

extends_documentation_fragment:
  - emc.emc_vnx

options:
    name:
        description:
            - Name of the MirrorView Mirror or Consistency Group.
        required: true
    force:
        description:
            - Force promotion if sites are not connected (local promotion).
        type: bool
        required: false


author:
    - Luca 'remix_tj' Lorenzetto (@remixtj)
'''

EXAMPLES = '''
- name: Promote MV/A
  emc_vnx_mv_promote:
    name: mg01
    sp_user: sysadmin
    sp_password: sysadmin
    sp_address: sp1a.fqdn

- name: Promote MV/A Locally
  emc_vnx_mv_promote:
    name: mg01
    sp_user: sysadmin
    sp_password: sysadmin
    sp_address: sp1a.fqdn
    force: True
'''

RETURN = '''
promoted_mirrors:
    description: list of the mirrors that has been promoted.
    type: list
    returned: success
promoted_luns:
    description: list of the luns that have been promoted.
    type: list
    returned: success
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.storage.emc.emc_vnx import emc_vnx_argument_spec


try:
    from storops import VNXSystem
    from storops.exception import VNXCredentialError, VNXMirrorException
    HAS_LIB = True
except:
    HAS_LIB = False


def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        force=dict(type='bool', required=False, default=False)
    )

    module_args.update(emc_vnx_argument_spec)

    result = dict(
        changed=False,
        promoted_mirrors=[],
        promoted_luns=[]
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if not HAS_LIB:
        module.fail_json(msg='storops library (0.5.10 or greater) is missing.'
                         'Install with pip install storops'
                         )

    sp_user = module.params['sp_user']
    sp_address = module.params['sp_address']
    sp_password = module.params['sp_password']

    if module.params['force']:
        promote_args = dict(promote_type='local')
    else:
        promote_args = dict()
    try:
        vnx = VNXSystem(sp_address, sp_user, sp_password)
        mg = vnx.get_mirror_group_async(module.params['name'])
        if mg.existed:
            if mg.role == 'Secondary':
                try:
                    if not module.check_mode:
                        mg.promote_group(**promote_args)
                    result['changed'] = True
                except VNXMirrorException as e:
                    if module.params['force'] and \
                       'Local Promote succeeded' in str(e):
                        result['changed'] = True
                    else:
                        module.fail_json(msg='Promotion failed: '
                                             '{0}'.format(to_native(e)), **result)
            elif mg.role == 'Primary' and mg.condition == 'Normal':
                    # MV/A is already primary or promoted
                    pass
            elif mg.role == 'Primary' and mg.state == 'Local Only':
                    # MV/A promoted, but local only to this storage
                    pass
            else:
                module.fail_json(msg='Cannot promote because not connected to '
                                 'target (secondary) storage system', **result)
            result['promoted_mirrors'] = [m.mirror_name
                                          for m in mg.group_mirrors]
            result['promoted_luns'] = [m.local_lun_number
                                       for m in mg.group_mirrors]
        else:
            mm = vnx.get_mirror_view_async(module.params['name'])
            if mm.existed:
                if mm.remote_mirror_status == 'Secondary Copy':
                    try:
                        if not module.check_mode:
                            mm.promote_image(**promote_args)
                        result['changed'] = True
                    except VNXMirrorException as e:
                        module.fail_json(msg='Promotion failed: '
                                             '{0}'.format(to_native(e)), **result)
                    result['promoted_mirrors'] = module.params['name']
                    result['promoted_luns'] = [get_alu(i.logical_unit_uid, vnx)
                                               for i in mm.images
                                               if i.condition ==
                                               'Primary Image']
            else:
                module.fail_json(msg='No such replica named '
                                     '{0}'.format(module.params['name']),
                                     **result)
    except VNXCredentialError as e:
            module.fail_json(msg='{0}'.format(to_native(e)), **result)

    module.exit_json(**result)


def get_alu(wwn, vnx):
    luns = vnx.get_lun()
    alu = None
    filtered_alu = [lun.lun_id for lun in luns if luns.wwn == wwn]
    if len(filtered_alu) > 0:
        alu = next(filtered_alu)
    return alu


def main():
    run_module()


if __name__ == '__main__':
    main()
