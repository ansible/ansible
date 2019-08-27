#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: ucs_org

short_description: Manages UCS Organizations for UCS Manager

description:
  - Manages UCS Organizations for UCS Manager.
  - Examples can be used with the UCS Platform Emulator U(https://cs.co/ucspe).

extends_documentation_fragment: ucs

options:
    state:
        description:
        - If C(absent), will remove organization.
        - If C(present), will create or update organization.
        choices: [absent, present]
        default: present
        type: str

    org_name:
        description:
        - The name of the organization.
        - Enter up to 16 characters.
        - "You can use any characters or spaces except the following:"
        - "` (accent mark), \ (backslash), ^ (carat), \" (double quote), = (equal sign), > (greater than), < (less than), or ' (single quote)."
        aliases: [ name ]
        type: str

    parent_org_path:
        description:
        - A forward slash / separated hierarchical path from the root organization to the parent of the organization to be added or updated.
        - UCS Manager supports a hierarchical structure of organizations up to five levels deep not including the root organization.
        - For example the parent_org_path for an organization named level5 could be root/level1/level2/level3/level4/level5
        default: root
        type: str

    description:
        description:
        - A user-defined description of the organization.
        - Enter up to 256 characters.
        - "You can use any characters or spaces except the following:"
        - "` (accent mark), \ (backslash), ^ (carat), \" (double quote), = (equal sign), > (greater than), < (less than), or ' (single quote)."
        aliases: [ descr ]
        type: str

    delegate_to:
        description:
        - Where the module will be run
        default: localhost
        type: str

requirements:
    - ucsmsdk

author:
    - John McDonough (@movinalot)
    - CiscoUcs (@CiscoUcs)
version_added: "2.8"
'''

EXAMPLES = r'''
- name: Add UCS Organization
  ucs_org:
    hostname: "{{ ucs_hostname }}"
    username: "{{ ucs_username }}"
    password: "{{ ucs_password }}"
    org_name: test
    description: testing org
    state: present
    delegate_to: localhost

- name: Update UCS Organization
  ucs_org:
    hostname: "{{ ucs_hostname }}"
    username: "{{ ucs_username }}"
    password: "{{ ucs_password }}"
    org_name: test
    description: Testing org
    state: present
    delegate_to: localhost

- name: Add UCS Organization
  ucs_org:
    hostname: "{{ ucs_hostname }}"
    username: "{{ ucs_username }}"
    password: "{{ ucs_password }}"
    org_name: level1
    parent_org_path: root
    description: level1 org
    state: present
    delegate_to: localhost

- name: Add UCS Organization
  ucs_org:
    hostname: "{{ ucs_hostname }}"
    username: "{{ ucs_username }}"
    password: "{{ ucs_password }}"
    org_name: level2
    parent_org_path: root/level1
    description: level2 org
    state: present

- name: Add UCS Organization
  ucs_org:
    hostname: "{{ ucs_hostname }}"
    username: "{{ ucs_username }}"
    password: "{{ ucs_password }}"
    org_name: level3
    parent_org_path: root/level1/level2
    description: level3 org
    state: present

- name: Remove UCS Organization
  ucs_org:
    hostname: "{{ ucs_hostname }}"
    username: "{{ ucs_username }}"
    password: "{{ ucs_password }}"
    org_name: level2
    parent_org_path: root/level1/
    state: absent
'''

RETURN = r'''
#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.ucs import UCSModule, ucs_argument_spec


def main():
    argument_spec = ucs_argument_spec
    argument_spec.update(
        org_name=dict(type='str', aliases=['name']),
        parent_org_path=dict(type='str', default='root'),
        description=dict(type='str', aliases=['descr']),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        delegate_to=dict(type='str', default='localhost'),
    )

    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'present', ['org_name']],
        ],
    )

    # UCSModule verifies ucsmsdk is present and exits on failure.
    # Imports are below for UCS object creation.
    ucs = UCSModule(module)
    from ucsmsdk.mometa.org.OrgOrg import OrgOrg

    err = False
    changed = False
    requested_state = module.params['state']

    kwargs = dict()

    if module.params['description'] is not None:
        kwargs['descr'] = module.params['description']

    try:
        parent_org_dn = 'org-' + module.params['parent_org_path'].replace('/', '/org-')
        dn = parent_org_dn + '/org-' + module.params['org_name']

        mo = ucs.login_handle.query_dn(dn)

        # Determine state change
        if mo:
            # Object exists, if it should exist has anything changed?
            if requested_state == 'present':
                # Do some or all Object properties not match, that is a change
                if not mo.check_prop_match(**kwargs):
                    changed = True

        # Object does not exist but should, that is a change
        else:
            if requested_state == 'present':
                changed = True

        # Object exists but should not, that is a change
        if mo and requested_state == 'absent':
            changed = True

        # Apply state if not check_mode
        if changed and not module.check_mode:
            if requested_state == 'absent':
                ucs.login_handle.remove_mo(mo)
            else:
                kwargs['parent_mo_or_dn'] = parent_org_dn
                kwargs['name'] = module.params['org_name']
                if module.params['description'] is not None:
                    kwargs['descr'] = module.params['description']

                mo = OrgOrg(**kwargs)
                ucs.login_handle.add_mo(mo, modify_present=True)
            ucs.login_handle.commit()

    except Exception as e:
        err = True
        ucs.result['msg'] = "setup error: %s " % str(e)

    ucs.result['changed'] = changed
    if err:
        module.fail_json(**ucs.result)

    module.exit_json(**ucs.result)


if __name__ == '__main__':
    main()
