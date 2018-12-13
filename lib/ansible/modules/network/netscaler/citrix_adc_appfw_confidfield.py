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
module: citrix_adc_appfw_confidfield
short_description: Configuration for configured confidential form fields resource.
description: Configuration for configured confidential form fields resource.

version_added: "2.8.0"

author:
    - George Nikolopoulos (@giorgos-nikolopoulos)
    - Sumanth Lingappa (@sumanth-lingappa)

options:

    fieldname:
        description:
            - "Name of the form field to designate as confidential."
        type: str

    url:
        description:
            - "URL of the web page that contains the web form."
        type: str

    isregex:
        choices:
            - 'REGEX'
            - 'NOTREGEX'
        description:
            - "Method of specifying the form field name. Available settings function as follows:"
            - "* REGEX. Form field is a regular expression."
            - "* NOTREGEX. Form field is a literal string."
        type: str

    comment:
        description:
            - "Any comments to preserve information about the form field designation."
        type: str


    disabled:
        description:
            - When set to C(true) the server state will be set to C(disabled).
            - When set to C(false) the server state will be set to C(enabled).
        type: bool
        default: false

extends_documentation_fragment: netscaler
'''

EXAMPLES = '''
- hosts: citrix_adc

  gather_facts: False
  tasks:
    - name: Setup confidential field id
      delegate_to: localhost
      citrix_adc_appfw_confidfield:
        nitro_user: nsroot
        nitro_pass: nsroot
        nsip: 192.168.1.2
        state: present
        fieldname: confidfield_integration_test
        url: 'HTTP.REQ.HOSTNAME.DOMAIN.EQ("blog.example.com")'
        isregex: REGEX
        comment: 'conf id field comment'
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
'''

import copy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netscaler.netscaler import NitroResourceConfig, NitroException, netscaler_common_arguments, log, loglines


class ModuleExecutor(object):

    def __init__(self, module):
        self.module = module
        self.main_nitro_class = 'appfwconfidfield'

        # Dictionary containing attribute information
        # for each NITRO object utilized by this module
        self.attibute_config = {
            'appfwconfidfield': {
                'attributes_list': [
                    'fieldname',
                    'url',
                    'isregex',
                    'comment',
                    'state',
                ],
                'transforms': {
                    'state': lambda v: v.upper(),
                },
                'get_id_attributes': [
                    'fieldname',
                    'url',
                ],
                'delete_id_attributes': [
                    'fieldname',
                    'url',
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
            main_object_exists = config.exists(get_id_attributes=self.attibute_config[self.main_nitro_class]['get_id_attributes'])
        except NitroException as e:
            if e.errorcode == 3168:
                return False
            else:
                raise

        return main_object_exists

    def get_main_config(self):
        manipulated_values_dict = copy.deepcopy(self.module.params)

        # We do not want the state module param to be interpreted as the appfwconfidfield parameter value
        if 'state' in manipulated_values_dict:
            del manipulated_values_dict['state']

        # Instead the disabled argument defines what the actual 'state' attribute should be
        disabled_value = manipulated_values_dict.get('disabled')
        if disabled_value is not None:
            if disabled_value:
                manipulated_values_dict['state'] = 'DISABLED'
            else:
                manipulated_values_dict['state'] = 'ENABLED'

        config = NitroResourceConfig(
            module=self.module,
            resource=self.main_nitro_class,
            attribute_values_dict=manipulated_values_dict,
            attributes_list=self.attibute_config[self.main_nitro_class]['attributes_list'],
            transforms=self.attibute_config[self.main_nitro_class]['transforms'],
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
            if not config.values_subgroup_of_actual():
                self.module_result['changed'] = True
                if not self.module.check_mode:
                    config.update(id_attribute='fieldname')

    def delete(self):
        # Check if main object exists
        config = self.get_main_config()

        if self.main_object_exists(config):
            self.module_result['changed'] = True
            if not self.module.check_mode:
                config.delete(delete_id_attributes=self.attibute_config[self.main_nitro_class]['delete_id_attributes'])

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

        fieldname=dict(type='str'),

        url=dict(type='str'),

        isregex=dict(
            type='str',
            choices=[
                'REGEX',
                'NOTREGEX',
            ]
        ),
        comment=dict(type='str'),

        disabled=dict(
            type='bool',
            default=False,
        ),
    )

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
