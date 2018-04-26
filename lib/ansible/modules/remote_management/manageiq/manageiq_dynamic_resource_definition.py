#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) Ahmed Bashir <ahmwag@gmail.com> @ahmbas
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: manageiq_dynamic_resource_definition

short_description: Management of dynamic resource definitions in ManageIQ.
extends_documentation_fragment: manageiq
version_added: '2.6'
author: Ahmed Bashir (@ahmbas)
description:
  - The manageiq_dynamic_resource_definition module supports adding, updating and deleting dynamic resource definitions in ManageIQ.

options:
  state:
    description:
      - absent - dynamic resource definitions should not exist, present - dynamic resource definitions should be.
    choices: ['absent', 'present']
    default: 'present'
  name:
    description:
      - The dynamic resource definition's name
  description:
    description:
      - The dynamic resource definition's description.
  properties:
    description:
      - The dynamic resource definition's properties.
    suboptions:
        attributes:
          description: dictionary of attributes consists of name and type.
        associations:
          description: dictionary with service and provider class.
        methods:
          description: list of methods to add to dynamic resource definition.
'''

EXAMPLES = '''
- name: Create a new dynamic resource definition in ManageIQ
  manageiq_dynamic_resource_definition:
    name: 'my_custom_definition'
    description: 'This is my custom definition.'
    state: 'present'
    properties:
         attributes:
           engine: string
           type: string
           size: integer
           region: string
           username: string
         associations:
           service: Service
           provider: ManageIQ::Providers::CloudManager
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      verify_ssl: False

- name: Edit a dynamic resource definition in ManageIQ
  manageiq_dynamic_resource_definition:
    name: 'my_edited_custom_definition'
    description: 'This is my edited custom definition.'
    state: 'present'
    properties:
         attributes:
           group: string
           engine: string
           type: string
           size: integer
           region: string
           username: string
         associations:
           service: Service
           provider: ManageIQ::Providers::CloudManager
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      verify_ssl: False

- name: Delete a dynamic resource definition in ManageIQ
  manageiq_dynamic_resource_definition:
    name: 'my_edited_custom_definition'
    state: 'absent'
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      verify_ssl: False
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.manageiq import ManageIQ, manageiq_argument_spec


class ManageIQDynamicResourceDefinition(object):
    """
        Object to create dynamic resource definition operations in manageiq.
    """

    def __init__(self, manageiq):
        self.manageiq = manageiq
        self.module = self.manageiq.module
        self.api_url = self.manageiq.api_url
        self.client = self.manageiq.client

    def dynamic_resource_definition(self, name):
        """ Search for dynamic resource definition by name.

        Returns:
            the dynamic resource definition, or None if not found.
        """
        return self.manageiq.find_collection_resource_by('generic_object_definitions', name=name)

    def create_definition(self, dynamic_resource_definition, name, description, properties):
        """ Creates the dynamic resource definition in manageiq.

        Returns:
            a dictionary with changes and msg.
        """
        url = '%s/generic_object_definitions' % (self.api_url)

        resource = {
            'name': name,
            'description': description,
            'properties': properties,
        }

        try:
            result = self.client.post(url, action='create', resource=resource)
        except Exception as e:
            self.module.fail_json(
                msg="failed to create dynamic resource definition %s: %s" % (name, str(e))
            )

        return dict(
            changed=True,
            msg="successfully created the dynamic resource definition %s: %s" % (name, result['results'])
        )

    def edit_definition(self, dynamic_resource_definition, name, description, properties):
        """ Edit the dynamic resource definition in manageiq.

        Returns:
            a dictionary with the changes and msg.
        """
        # Check if properties has the following keys,
        # These keys are returned from the API response even if they are empty
        # So we remove them to compare accuratley
        current_properties = dynamic_resource_definition.get('properties', {})
        current_name = dynamic_resource_definition.get('name')
        current_description = dynamic_resource_definition.get('description')
        if (
            current_name == name and
            current_description == description and
            current_properties.get('attributes', {}) == properties.get('attributes', {}) and
            current_properties.get('associations', {}) == properties.get('associations', {}) and
            current_properties.get('methods', []) == properties.get('methods', [])
        ):
            return dict(
                changed=False,
                msg="Dynamic resource definition %s is not changed." % (name)
            )

        url = '%s/generic_object_definitions/%s' % (self.api_url, dynamic_resource_definition['id'])

        resource = {
            'name': name,
            'description': description,
            'properties': properties,
        }

        try:
            result = self.client.post(url, action='edit', resource=resource)
        except Exception as e:
            self.module.fail_json(
                msg="failed to edit dynamic resource definition %s: %s" % (name, str(e))
            )

        return dict(
            changed=True,
            msg="successfully edited the dynamic resource definition %s: %s" % (name, result)
        )

    def delete_definition(self, dynamic_resource_definition):
        """ Delete the dynamic resource definition in manageiq.

        Returns:
            the name.
        """
        url = '%s/generic_object_definitions/%s' % (self.api_url, dynamic_resource_definition['id'])

        try:
            result = self.client.post(url, action='delete')
        except Exception as e:
            self.module.fail_json(
                msg="failed to delete dynamic resource definition %s: %s" % (dynamic_resource_definition.get('name'), str(e))
            )

        return dict(
            changed=True,
            msg="successfully deleted the dynamic resource definition %s" % (dynamic_resource_definition.get('name'))
        )


def main():
    argument_spec = dict(
        name=dict(required=True, type='str'),
        description=dict(type='str'),
        state=dict(choices=['absent', 'present'], default='present'),
        properties=dict(type='dict')
    )
    required_if = [('state', 'present', ('properties', ))]
    # add the manageiq connection arguments to the arguments
    argument_spec.update(manageiq_argument_spec())

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=required_if,
    )

    name = module.params['name']
    description = module.params['description']
    state = module.params['state']
    properties = module.params['properties']

    manageiq = ManageIQ(module)
    manageiq_dynamic_resource_definition = ManageIQDynamicResourceDefinition(manageiq)

    # Get definition if exists
    dynamic_resource_definition = manageiq_dynamic_resource_definition.dynamic_resource_definition(
        name
    )

    # definition should not exist
    if state == "absent":
        # if we have a definition, delete it
        if dynamic_resource_definition:
            res_args = manageiq_dynamic_resource_definition.delete_definition(
                dynamic_resource_definition
            )
        # if we do not have a definition, nothing to do
        else:
            res_args = dict(
                changed=False,
                msg="dynamic resource definition  %s: does not exist in manageiq" % (name))

    # definition shoult exist
    if state == "present":
        # if we have a definition, edit it
        if dynamic_resource_definition:
            res_args = manageiq_dynamic_resource_definition.edit_definition(
                dynamic_resource_definition, name, description, properties
            )
        # if we do not have a definition, create it
        else:
            res_args = manageiq_dynamic_resource_definition.create_definition(
                dynamic_resource_definition, name, description, properties
            )

    module.exit_json(**res_args)


if __name__ == "__main__":
    main()
