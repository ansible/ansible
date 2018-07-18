#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule
try:
    from storops import VNXSystem
    from storops.exception import VNXCredentialError, VNXStorageGroupError, \
        VNXAluAlreadyAttachedError, VNXAttachAluError, VNXDetachAluNotFoundError
    HAS_LIB = True
except:
    HAS_LIB = False


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: emc_vnx_sg_member

short_description: Manage storage group member

version_added: "2.7"

description:
    - "This module manages the members of an existing storage group"

extends_documentation_fragment:
  - emc.emc_vnx

options:
    name:
        description:
            - Name of the Storage group to manage
        required: true
    lunid:
        description:
            - Lun id to be added
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
    description: LUNID that hosts attached to the storage group will see
'''


def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        sp_address=dict(type='str', required=True),
        sp_user=dict(type='str', required=False, default='sysadmin'),
        sp_password=dict(type='str', required=False, default='sysadmin'),
        lunid=dict(type='int', required=True),
        state=dict(default='present', choices=['present', 'absent']),
    )

    result = dict(
        changed=False,
        hluid=None
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
                    except VNXAluAlreadyAttachedError:
                        result['hluid'] = sg.get_hlu(alu)
                        pass
                    except (VNXAttachAluError, VNXStorageGroupError) as e:
                        module.fail_json(msg='Error attaching {}: '
                                             '{} '.format(alu, str(e)),
                                         **result)
                else:
                    result['hluid'] = sg.get_hlu(alu)
            if module.params['state'] == 'absent' and sg.has_alu(alu):
                try:
                    sg.detach_alu(alu)
                except VNXDetachAluNotFoundError:
                    # being not attached when using absent is OK
                    pass
                except VNXStorageGroupError as e:
                    module.fail_json(msg='Error detaching alu {}: '
                                         '{} '.format(alu, str(e)),
                                     **result)
        else:
                module.fail_json(msg='No such storage group named '
                                     '{}'.format(module.params['name']),
                                     **result)
    except VNXCredentialError as e:
            module.fail_json(msg='{}'.format(str(e)), **result)

    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
