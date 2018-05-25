#!/usr/bin/python

# Copyright: (c) 2017, VEXXHOST, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: os_keystone_endpoint
short_description: Manage OpenStack Identity service endpoints
extends_documentation_fragment: openstack
author:
    - Mohammed Naser (@mnaser)
    - Alberto Murillo (@albertomurillo)
version_added: "2.5"
description:
    - Create, update, or delete OpenStack Identity service endpoints. If a
      service with the same combination of I(service), I(interface) and I(region)
      exist, the I(url) and I(state) (C(present) or C(absent)) will be updated.
options:
   service:
     description:
        - Name or id of the service.
     required: true
   interface:
     description:
        - Interface of the service.
     choices: [admin, public, internal]
     required: true
   url:
     description:
        - URL of the service.
     required: true
   region:
     description:
        - Region that the service belongs to. Note that I(region_name) is used for authentication.
   enabled:
     description:
        - Is the service enabled.
     default: True
   state:
     description:
       - Should the resource be C(present) or C(absent).
     choices: [present, absent]
     default: present
requirements:
    - openstacksdk >= 0.13.0
'''

EXAMPLES = '''
- name: Create a service for glance
  os_keystone_endpoint:
     cloud: mycloud
     service: glance
     endpoint_interface: public
     url: http://controller:9292
     region: RegionOne
     state: present

- name: Delete a service for nova
  os_keystone_endpoint:
     cloud: mycloud
     service: nova
     endpoint_interface: public
     region: RegionOne
     state: absent
'''

RETURN = '''
endpoint:
    description: Dictionary describing the endpoint.
    returned: On success when I(state) is C(present)
    type: complex
    contains:
        id:
            description: Endpoint ID.
            type: string
            sample: 3292f020780b4d5baf27ff7e1d224c44
        region:
            description: Region Name.
            type: string
            sample: RegionOne
        service_id:
            description: Service ID.
            type: string
            sample: b91f1318f735494a825a55388ee118f3
        interface:
            description: Endpoint Interface.
            type: string
            sample: public
        url:
            description: Service URL.
            type: string
            sample: http://controller:9292
        enabled:
            description: Service status.
            type: boolean
            sample: True
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def _needs_update(module, endpoint):
    if endpoint.enabled != module.params['enabled']:
        return True
    if endpoint.url != module.params['url']:
        return True
    return False


def _system_state_change(module, endpoint):
    state = module.params['state']
    if state == 'absent' and endpoint:
        return True

    if state == 'present':
        if endpoint is None:
            return True
        return _needs_update(module, endpoint)

    return False


def main():
    argument_spec = openstack_full_argument_spec(
        service=dict(type='str', required=True),
        endpoint_interface=dict(type='str', required=True, choices=['admin', 'public', 'internal']),
        url=dict(type='str', required=True),
        region=dict(type='str'),
        enabled=dict(type='bool', default=True),
        state=dict(type='str', default='present', choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    service_name_or_id = module.params['service']
    interface = module.params['endpoint_interface']
    url = module.params['url']
    region = module.params['region']
    enabled = module.params['enabled']
    state = module.params['state']

    sdk, cloud = openstack_cloud_from_module(module)
    try:

        service = cloud.get_service(service_name_or_id)
        if service is None:
            module.fail_json(msg='Service %s does not exist' % service_name_or_id)

        filters = dict(service_id=service.id, interface=interface)
        if region is not None:
            filters['region'] = region
        endpoints = cloud.search_endpoints(filters=filters)

        if len(endpoints) > 1:
            module.fail_json(msg='Service %s, interface %s and region %s are '
                                 'not unique' %
                                 (service_name_or_id, interface, region))
        elif len(endpoints) == 1:
            endpoint = endpoints[0]
        else:
            endpoint = None

        if module.check_mode:
            module.exit_json(changed=_system_state_change(module, endpoint))

        if state == 'present':
            if endpoint is None:
                result = cloud.create_endpoint(service_name_or_id=service,
                                               url=url, interface=interface,
                                               region=region, enabled=enabled)
                endpoint = result[0]
                changed = True
            else:
                if _needs_update(module, endpoint):
                    endpoint = cloud.update_endpoint(
                        endpoint.id, url=url, enabled=enabled)
                    changed = True
                else:
                    changed = False
            module.exit_json(changed=changed, endpoint=endpoint)

        elif state == 'absent':
            if endpoint is None:
                changed = False
            else:
                cloud.delete_endpoint(endpoint.id)
                changed = True
            module.exit_json(changed=changed)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
