#!/usr/bin/python
# Copyright 2016 Sam Yaple
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_keystone_service
short_description: Manage OpenStack Identity services
extends_documentation_fragment: openstack
author: "Sam Yaple (@SamYaple)"
version_added: "2.2"
description:
    - Create, update, or delete OpenStack Identity service. If a service
      with the supplied name already exists, it will be updated with the
      new description and enabled attributes.
options:
   name:
     description:
        - Name of the service
     required: true
   description:
     description:
        - Description of the service
   enabled:
     description:
        - Is the service enabled
     type: bool
     default: 'yes'
   service_type:
     description:
        - The type of service
     required: true
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
requirements:
    - "python >= 2.7"
    - "openstacksdk"
'''

EXAMPLES = '''
# Create a service for glance
- os_keystone_service:
     cloud: mycloud
     state: present
     name: glance
     service_type: image
     description: OpenStack Image Service
# Delete a service
- os_keystone_service:
     cloud: mycloud
     state: absent
     name: glance
     service_type: image
'''

RETURN = '''
service:
    description: Dictionary describing the service.
    returned: On success when I(state) is 'present'
    type: complex
    contains:
        id:
            description: Service ID.
            type: str
            sample: "3292f020780b4d5baf27ff7e1d224c44"
        name:
            description: Service name.
            type: str
            sample: "glance"
        service_type:
            description: Service type.
            type: str
            sample: "image"
        description:
            description: Service description.
            type: str
            sample: "OpenStack Image Service"
        enabled:
            description: Service status.
            type: bool
            sample: True
id:
    description: The service ID.
    returned: On success when I(state) is 'present'
    type: str
    sample: "3292f020780b4d5baf27ff7e1d224c44"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def _needs_update(module, service):
    if service.enabled != module.params['enabled']:
        return True
    if service.description is not None and \
       service.description != module.params['description']:
        return True
    return False


def _system_state_change(module, service):
    state = module.params['state']
    if state == 'absent' and service:
        return True

    if state == 'present':
        if service is None:
            return True
        return _needs_update(module, service)

    return False


def main():
    argument_spec = openstack_full_argument_spec(
        description=dict(default=None),
        enabled=dict(default=True, type='bool'),
        name=dict(required=True),
        service_type=dict(required=True),
        state=dict(default='present', choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    description = module.params['description']
    enabled = module.params['enabled']
    name = module.params['name']
    state = module.params['state']
    service_type = module.params['service_type']

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        services = cloud.search_services(name_or_id=name,
                                         filters=dict(type=service_type))

        if len(services) > 1:
            module.fail_json(msg='Service name %s and type %s are not unique' %
                             (name, service_type))
        elif len(services) == 1:
            service = services[0]
        else:
            service = None

        if module.check_mode:
            module.exit_json(changed=_system_state_change(module, service))

        if state == 'present':
            if service is None:
                service = cloud.create_service(name=name, description=description,
                                               type=service_type, enabled=True)
                changed = True
            else:
                if _needs_update(module, service):
                    service = cloud.update_service(
                        service.id, name=name, type=service_type, enabled=enabled,
                        description=description)
                    changed = True
                else:
                    changed = False
            module.exit_json(changed=changed, service=service, id=service.id)

        elif state == 'absent':
            if service is None:
                changed = False
            else:
                cloud.delete_service(service.id)
                changed = True
            module.exit_json(changed=changed)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
