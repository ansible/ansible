#!/usr/bin/python
# -*- coding: utf-8 -*-

#  Copyright (c) 2018 Citrix Systems
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: citrix_adm_mpsuser
short_description: Manage Citrix ADM users.
description: Manage Citrix ADM users.

version_added: "2.8.0"

author:
    - George Nikolopoulos (@giorgos-nikolopoulos)

options:

    session_timeout:
        description:
            - "Session timeout for the user."
        type: str

    name:
        description:
            - "User Name."
            - "Minimum length = 1"
            - "Maximum length = 128"
        type: str

    session_timeout_unit:
        description:
            - "Session timeout unit for the user."
        type: str

    external_authentication:
        description:
            - "Enable external authentication."
        type: bool

    enable_session_timeout:
        description:
            - "Enables session timeout for user."
        type: bool

    tenant_id:
        description:
            - "Tenant Id of the system users."
            - "Minimum length = 1"
            - "Maximum length = 128"
        type: str

    password:
        description:
            - "Password."
            - "Minimum length = 1"
            - "Maximum length = 128"
        type: str

    id:
        description:
            - "Id is system generated key for all the system users."
        type: str

    groups:
        description:
            - "Groups to which user belongs."
        type: list


extends_documentation_fragment: netscaler
'''

EXAMPLES = '''
- name: Setup mpsuser
  delegate_to: localhost
  citrix_adm_mpsuser:
    mas_ip: 192.168.1.1
    mas_user: nsroot
    mas_pass: nsroot

    state: present

    name: test_mpsuser
    password: 123456

    session_timeout: 10
    session_timeout_unit: Minutes
    external_authentication: false
    enable_session_timeout: true
    groups:
      - test_mpsgroup
'''

RETURN = '''
loglines:
    description: list of logged messages by the module
    returned: always
    type: list
    sample: ['message 1', 'message 2']

msg:
    description: Message detailing the failure reason
    returned: failure
    type: str
    sample: "Action does not exist"

mpsuser:
    description: Dictionary containing the attributes of the created mpsuser
    returned: success
    type: dict
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netscaler.netscaler import MASResourceConfig, NitroException, netscaler_common_arguments, log, loglines


class ModuleExecutor(object):

    def __init__(self, module):
        self.module = module
        self.main_nitro_class = 'mpsuser'

        # Dictionary containing attribute information
        # for each NITRO object utilized by this module
        self.attribute_config = {
            'mpsuser': {
                'attributes_list': [
                    'session_timeout',
                    'name',
                    'session_timeout_unit',
                    'external_authentication',
                    'enable_session_timeout',
                    'tenant_id',
                    'password',
                    'id',
                    'groups',
                ],
                'transforms': {
                    'enable_session_timeout': lambda v: "true" if v else "false",
                    'external_authentication': lambda v: "true" if v else "false",
                },
                'get_id_attributes': [
                    'name',
                    'id',
                ],
                'delete_id_attributes': [
                    'name',
                    'id',
                ],
            },

        }

        self.module_result = dict(
            changed=False,
            failed=False,
            loglines=loglines,
        )

    def main_object_exists(self, config):
        try:
            main_object_exists = config.exists(
                get_id_attributes=self.attribute_config[self.main_nitro_class]['get_id_attributes'],
                use_filter=True,
            )
        except NitroException as e:
            raise

        return main_object_exists

    def get_main_config(self):
        config = MASResourceConfig(
            module=self.module,
            resource=self.main_nitro_class,
            attribute_values_dict=self.module.params,
            attributes_list=self.attribute_config[self.main_nitro_class]['attributes_list'],
            transforms=self.attribute_config[self.main_nitro_class]['transforms'],
            api_path='nitro/v2/config',
        )

        return config

    def update_or_create(self):
        # Check if main object exists
        config = self.get_main_config()

        if not self.main_object_exists(config):
            self.module_result['changed'] = True
            if not self.module.check_mode:
                config.create()
        else:
            if not config.values_subset_of_actual(skip_attributes=['password']):
                self.module_result['changed'] = True
                if not self.module.check_mode:
                    config.update(id_attribute='id')

        # Return the actual object
        config.get_actual_instance(
            get_id_attributes=self.attribute_config[self.main_nitro_class]['get_id_attributes'],
            success_codes=[None, 0],
            use_filter=True
        )
        self.module_result.update(dict(mpsuser=config.actual_dict))

    def delete(self):
        # Check if main object exists
        config = self.get_main_config()

        if self.main_object_exists(config):
            self.module_result['changed'] = True
            if not self.module.check_mode:
                config.delete(delete_id_attributes=self.attribute_config[self.main_nitro_class]['delete_id_attributes'])

    def main(self):
        try:

            if self.module.params['state'] == 'present':
                self.update_or_create()
            elif self.module.params['state'] == 'absent':
                self.delete()

            self.module.exit_json(**self.module_result)

        except NitroException as e:
            msg = "nitro exception errorcode=%s, message=%s, severity=%s" % (str(e.errorcode), e.message, e.severity)
            self.module.fail_json(msg=msg, **self.module_result)
        except Exception as e:
            msg = 'Exception %s: %s' % (type(e), str(e))
            self.module.fail_json(msg=msg, **self.module_result)


def main():

    argument_spec = dict()

    module_specific_arguments = dict(
        session_timeout=dict(
            type='str'
        ),
        name=dict(
            type='str'
        ),
        session_timeout_unit=dict(
            type='str'
        ),
        external_authentication=dict(
            type='bool'
        ),
        enable_session_timeout=dict(
            type='bool'
        ),
        tenant_id=dict(
            type='str'
        ),
        password=dict(
            type='str'
        ),
        id=dict(
            type='str'
        ),
        groups=dict(
            type='list'
        ),
    )

    # Add the no_log option for password
    module_specific_arguments['password'].update(dict(no_log=True))

    argument_spec.update(netscaler_common_arguments)
    argument_spec.update(module_specific_arguments)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    executor = ModuleExecutor(module=module)
    executor.main()


if __name__ == '__main__':
    main()
