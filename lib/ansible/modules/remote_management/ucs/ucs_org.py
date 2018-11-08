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
  - Examples can be used with the L(UCS Platform Emulator,https://communities.cisco.com/ucspe).

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
        - The name of the orgranization.
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


def run_module():
    argument_spec = ucs_argument_spec
    argument_spec.update(
        org_name=dict(type='str', aliases=['name']),
        parent_org_path=dict(type='str', default='root'),
        description=dict(type='str', aliases=['descr'], default=''),
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

    try:
        mo_exists = False
        props_match = False

        parent_org_dn = 'org-' + module.params['parent_org_path'].replace('/', '/org-')
        dn = parent_org_dn + '/org-' + module.params['org_name']

        mo = ucs.login_handle.query_dn(dn)
        if mo:
            mo_exists = True

        if module.params['state'] == 'absent':
            if mo_exists:
                if not module.check_mode:
                    ucs.login_handle.remove_mo(mo)
                    ucs.login_handle.commit()
                changed = True
        else:
            if mo_exists:
                # check top-level mo props
                kwargs = dict(descr=module.params['description'])
                if mo.check_prop_match(**kwargs):
                    props_match = True

            if not props_match:
                if not module.check_mode:
                    # update/add mo
                    mo = OrgOrg(parent_mo_or_dn=parent_org_dn,
                                name=module.params['org_name'],
                                descr=module.params['description'])
                    ucs.login_handle.add_mo(mo, modify_present=True)
                    ucs.login_handle.commit()
                changed = True

    except Exception as e:
        err = True
        ucs.result['msg'] = "setup error: %s " % str(e)

    ucs.result['changed'] = changed
    if err:
        module.fail_json(**ucs.result)
    module.exit_json(**ucs.result)


def main():
    run_module()


if __name__ == '__main__':
    main()
