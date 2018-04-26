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

module: manageiq_dynamic_resource_instance

short_description: Management of dynamic resource definitions in ManageIQ.
extends_documentation_fragment: manageiq
version_added: '2.6'
author: Ahmed Bashir (@ahmbas)
description:
  - The manageiq_dynamic_resource_instance module supports adding, editing and deleting dynamic resource instances in ManageIQ.

options:
  state:
    description:
      - absent - dynamic resource instance should not exist, present - dynamic resource instance should be.
    choices: ['absent', 'present']
    default: 'present'
  name:
    description:
      - The dynamic resource instance's name.
  dynamic_resource_definition:
    description:
      - The name of the generic resource definition. Must exist in manageiq.
  property_attributes:
    description:
      - The dynamic resource instances properties. fields match the dynamic resource definition properties.
  providers:
    description:
      - list of provider names to associate instance with. Must exist in manageiq.
  services:
    description:
      - list of service names to associate instance with. Must exist in manageiq.
'''

EXAMPLES = '''
- name: Create a new dynamic resource instance in ManageIQ
  manageiq_dynamic_resource_instance:
    name: 'my_instance'
    state: 'present'
    property_attributes:
      engine: 'mysql'
      type: 'DB'
      size: 30
      region: 'default'
      username: 'masterdb'
      services:
        - service1
      providers:
        - Red Hat Virtualization
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      verify_ssl: False

- name: Edit a dynamic resource definition in ManageIQ
  manageiq_dynamic_resource_instance:
    name: 'my_instance'
    state: 'present'
    property_attributes:
      engine: 'mysql'
      type: 'DB'
      size: 30
      region: 'nova'
      username: 'masterdb'
      services:
        - service2
      providers:
        - Openstack
    manageiq_connection:
      url: 'http://127.0.0.1:3000'
      username: 'admin'
      password: 'smartvm'
      verify_ssl: False

- name: Delete a dynamic resource definition in ManageIQ
  manageiq_dynamic_resource_instance:
    name: 'my_instance'
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


class ManageIQDynamicResourceInstance(object):
    """
        Object to create dynamic resource instance operations in manageiq.
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

    def dynamic_resource_instance(self, name):
        """ Search for dynamic resource instance by name.

        Returns:
            the dynamic resource instance, or None if not found.
        """
        return self.manageiq.find_collection_resource_by('generic_objects', name=name)

    def provider(self, name):
        """ Search for provider by name.

        Returns:
            the provider, or None if not found.
        """
        return self.manageiq.find_collection_resource_by('providers', name=name)

    def service(self, name):
        """ Search for service by name.

        Returns:
            the service, or None if not found.
        """
        return self.manageiq.find_collection_resource_by('services', name=name)

    def create_instance(
        self, name, dynamic_resource_definition, property_attributes, services, providers
    ):
        """ Creates the dynamic resource instance in manageiq.

        Returns:
            a dictionary with changes and msg.
        """
        url = '%s/generic_objects' % (self.api_url)

        generic_object_definition_href = '%s/generic_object_definitions/%s' % (
            self.api_url,
            dynamic_resource_definition['id']
        )

        resource = {
            'name': name,
            # API still uses old name
            'generic_object_definition': {
                'href': generic_object_definition_href
            },
            'property_attributes': property_attributes,
            'associations': {
                'service':[
                    {
                    'href': service.get('href')
                    } for service in services
                ],
                'provider':[
                    {
                    'href': provider.get('href')
                    } for provider in providers
                ],
            },
        }

        try:
            result = self.client.post(url, action='create', resource=resource)
        except Exception as e:
            self.module.fail_json(
                msg="failed to create dynamic resource instance %s: %s" % (name, str(e))
            )

        return dict(
            changed=True,
            msg="successfully created the dynamic resource instance %s: %s" % (
                name, result['results']
            )
        )

    def edit_instance(
        self, dynamic_resource_instance, name, dynamic_resource_definition,
        property_attributes
    ):
        """ Edit the dynamic resource instance in manageiq.

        Returns:
            a dictionary with the changes and msg.
        """
        # Check if there is any changes in the instance fields
        current_name = dynamic_resource_instance.get('name')
        current_dynamic_resource_definition_id = dynamic_resource_instance.get(
            'generic_object_definition_id'
        )
        current_property_attributes = dynamic_resource_instance.get(
            'property_attributes', {}
        )

        if (
            current_name == name and
            current_dynamic_resource_definition_id == dynamic_resource_definition['id'] and
            current_property_attributes == property_attributes
        ):
            return dict(
                changed=False,
                msg="dynamic resource instance: %s is not changed." % (name)
            )

        url = '%s/generic_objects/%s' % (self.api_url, dynamic_resource_instance['id'])

        generic_object_definition_href = '%s/generic_object_definitions/%s' % (
            self.api_url,
            dynamic_resource_definition['id']
        )

        resource = {
            'name': name,
            # API still uses old name
            'generic_object_definition':{
                'href': generic_object_definition_href
            },
            'property_attributes': property_attributes
        }

        try:
            result = self.client.post(url, action='edit', resource=resource)
        except Exception as e:
            self.module.fail_json(
                msg="failed to edit dynamic resource instance %s: %s" % (name, str(e))
            )

        return dict(
            changed=True,
            msg="successfully edited the dynamic resource instance %s: %s" % (name, result)
        )

    def delete_instance(self, dynamic_resource_instance):
        """ Delete the dynamic resource instace in manageiq.

        Returns:
            the name.
        """
        url = '%s/generic_objects/%s' % (self.api_url, dynamic_resource_instance['id'])

        try:
            result = self.client.post(url, action='delete')
        except Exception as e:
            self.module.fail_json(
                msg="failed to delete dynamic resource instance %s: %s" % (
                    dynamic_resource_instance.get('name'), str(e)
                )
            )

        return dict(
            changed=True,
            msg="successfully deleted the dynamic resource instance %s" % (
                dynamic_resource_instance.get('name')
            )
        )


def main():
    argument_spec = dict(
        name=dict(required=True, type='str'),
        state=dict(choices=['absent', 'present'], default='present'),
        dynamic_resource_definition=dict(type='str'),
        property_attributes=dict(type='dict'),
        services=dict(type='list', default=[]),
        providers=dict(type='list', default=[]),
    )

    required_if = [
        (
            'state', 'present', (
                'dynamic_resource_definition', 'property_attributes',
            )
        )
    ]
    # add the manageiq connection arguments to the arguments
    argument_spec.update(manageiq_argument_spec())

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=required_if,
    )

    name = module.params['name']
    state = module.params['state']
    dynamic_resource_definition = module.params['dynamic_resource_definition']
    property_attributes = module.params['property_attributes']
    services = module.params['services']
    providers = module.params['providers']

    manageiq = ManageIQ(module)
    manageiq_dynamic_resource_instance = ManageIQDynamicResourceInstance(manageiq)

    # Check if definition exists
    dynamic_resource_definition = manageiq_dynamic_resource_instance.dynamic_resource_definition(
        dynamic_resource_definition
    )
    if not dynamic_resource_definition and state != "absent":
        module.fail_json(
            msg="Dymamic resource definition:%s does not exist." % (dynamic_resource_definition)
        )
    # Get instance if exists
    dynamic_resource_instance = manageiq_dynamic_resource_instance.dynamic_resource_instance(
        name
    )

    if state == "absent":
        # if we have a instance, delete it
        if dynamic_resource_instance:
            res_args = manageiq_dynamic_resource_instance.delete_instance(
                dynamic_resource_instance
            )
        # if we do not have a instance, nothing to do
        else:
            res_args = dict(
                changed=False,
                msg="dynamic resource instance  %s: does not exist in manageiq" % (name)
            )

    if state == "present":
        # Validate that providers and services exist
        service_objs = [
            manageiq_dynamic_resource_instance.service(service) for service in services
        ]
        provider_objs = [
            manageiq_dynamic_resource_instance.provider(provider) for provider in providers
        ]

        if not all(service_objs) and any(services):
            module.fail_json(
                msg="One or more service(s):%s do not exist in manageiq." % (services)
            )

        if not all(provider_objs) and any(providers):
            module.fail_json(
                msg="One or more provider(s):%s do not exist in manageiq." % (providers)
            )
        # if we have a instance, edit it.
        # NOTE: The manageiq API does not return the linked services or providers.
        # Hence we cannot edit those fields. If you wish to do so, you need to
        # delete the instance and recreate it again
        if dynamic_resource_instance:
            res_args = manageiq_dynamic_resource_instance.edit_instance(
                dynamic_resource_instance, name, dynamic_resource_definition,
                property_attributes
            )
        # if we do not have a instance, create it
        else:
            res_args = manageiq_dynamic_resource_instance.create_instance(
                name, dynamic_resource_definition, property_attributes,
                service_objs, provider_objs
            )

    module.exit_json(**res_args)


if __name__ == "__main__":
    main()
