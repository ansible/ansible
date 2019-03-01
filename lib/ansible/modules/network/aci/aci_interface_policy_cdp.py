#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: my_sample_module

short_description: This is my sample module

version_added: "2.4"

description:
    - "This is my longer description explaining my sample module"

options:
    name:
        description:
            - This is the message to send to the sample module
        required: true
    new:
        description:
            - Control to demo if the result of this module is changed or not
        required: false

extends_documentation_fragment:
    - azure

author:
    - Your Name (@yourhandle)
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  my_new_test_module:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_new_test_module:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_new_test_module:
    name: fail me
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
message:
    description: The output message that the sample module generates
'''
from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec

from ansible.module_utils.basic import AnsibleModule


def main():
#    run_module()
    argument_spec = aci_argument_spec()
    argument_spec.update(
        cdp_policy=dict(type='str', required=False, aliases=['cdp_interface', 'name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        cdp_enabled=dict(type='bool'),  
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['cdp_policy']],
            ['state', 'present', ['cdp_policy']],
        ],
    )
    #module.fail_json(msg="Parameters", params=module.params)

    aci = ACIModule(module)

    cdp = module.params['cdp_policy']
    description = module.params['description']
    admin_state = aci.boolean(module.params['cdp_enabled'], 'enabled', 'disabled')
    state = module.params['state']


    aci.construct_url(
        root_class=dict(
            aci_class='cdpIfPol',
            aci_rn='infra/cdpIfP-{0}'.format(cdp),
            module_object=cdp,
            target_filter={'name': cdp},
        ),
    )

    aci.get_existing()

    if state == 'present':
        aci.payload(
            aci_class='cdpIfPol',
            class_config=dict(
                name=cdp,
                descr=description,
                adminSt=admin_state,
            ),
        )

        aci.get_diff(aci_class='cdpIfPol')

        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    aci.exit_json()


if __name__ == '__main__':
    main()