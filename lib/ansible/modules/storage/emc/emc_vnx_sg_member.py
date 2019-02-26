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
module: emc_vnx_sg_member

short_description: Manage storage group member on EMC VNX

version_added: "2.7"

description:
    - "This module manages the members of an existing storage group."

extends_documentation_fragment:
  - emc.emc_vnx

options:
    name:
        description:
            - Name of the Storage group to manage.
        required: true
    lunid:
        description:
            - Lun id to be added.
        required: true
    state:
        description:
        - Indicates the desired lunid state.
        - C(present) ensures specified lunid is present in the Storage Group.
        - C(absent) ensures specified lunid is absent from Storage Group.
        default: present
        choices: [ "present", "absent"]


author:
    - Luca 'remix_tj' Lorenzetto (@remixtj)
'''

EXAMPLES = '''
- name: Add lun to storage group
  emc_vnx_sg_member:
    name: sg01
    sp_address: sp1a.fqdn
    sp_user: sysadmin
    sp_password: sysadmin
    lunid: 100
    state: present

- name: Remove lun from storage group
  emc_vnx_sg_member:
    name: sg01
    sp_address: sp1a.fqdn
    sp_user: sysadmin
    sp_password: sysadmin
    lunid: 100
    state: absent
'''

RETURN = '''
hluid:
    description: LUNID that hosts attached to the storage group will see.
    type: int
    returned: success
'''

import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native
from ansible.module_utils.storage.emc.emc_vnx import emc_vnx_argument_spec

LIB_IMP_ERR = None
try:
    from storops import VNXSystem
    from storops.exception import VNXCredentialError, VNXStorageGroupError, \
        VNXAluAlreadyAttachedError, VNXAttachAluError, VNXDetachAluNotFoundError
    HAS_LIB = True
except Exception:
    LIB_IMP_ERR = traceback.format_exc()
    HAS_LIB = False


def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        lunid=dict(type='int', required=True),
        state=dict(default='present', choices=['present', 'absent']),
    )

    module_args.update(emc_vnx_argument_spec)

    result = dict(
        changed=False,
        hluid=None
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if not HAS_LIB:
        module.fail_json(msg=missing_required_lib('storops >= 0.5.10'),
                         exception=LIB_IMP_ERR)

    sp_user = module.params['sp_user']
    sp_address = module.params['sp_address']
    sp_password = module.params['sp_password']
    alu = module.params['lunid']

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    try:
        vnx = VNXSystem(sp_address, sp_user, sp_password)
        sg = vnx.get_sg(module.params['name'])
        if sg.existed:
            if module.params['state'] == 'present':
                if not sg.has_alu(alu):
                    try:
                        result['hluid'] = sg.attach_alu(alu)
                        result['changed'] = True
                    except VNXAluAlreadyAttachedError:
                        result['hluid'] = sg.get_hlu(alu)
                    except (VNXAttachAluError, VNXStorageGroupError) as e:
                        module.fail_json(msg='Error attaching {0}: '
                                             '{1} '.format(alu, to_native(e)),
                                         **result)
                else:
                    result['hluid'] = sg.get_hlu(alu)
            if module.params['state'] == 'absent' and sg.has_alu(alu):
                try:
                    sg.detach_alu(alu)
                    result['changed'] = True
                except VNXDetachAluNotFoundError:
                    # being not attached when using absent is OK
                    pass
                except VNXStorageGroupError as e:
                    module.fail_json(msg='Error detaching alu {0}: '
                                         '{1} '.format(alu, to_native(e)),
                                     **result)
        else:
            module.fail_json(msg='No such storage group named '
                                 '{0}'.format(module.params['name']),
                                 **result)
    except VNXCredentialError as e:
        module.fail_json(msg='{0}'.format(to_native(e)), **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
