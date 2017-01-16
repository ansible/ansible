#!/usr/bin/python
# Copyright 2017 VEXXHOST, Inc.
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

from distutils.version import StrictVersion

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: os_keystone_endpoint
short_description: Manage OpenStack Identity service endpoints
extends_documentation_fragment: openstack
author: "Mohammed Naser (@mnaser)"
version_added: "2.3"
description:
    - Create, update, or delete OpenStack Identity service endpoints.  If a
      service with the same combination of service and interface and region
      exist, the URL and state (enabled or disabled) will be updated.
options:
   service:
     description:
        - Name of the service
     required: true
   interface:
     description:
        - Interface of the service
     choices: [admin, public, internal]
     required: true
   url:
     description:
        - URL of the service
     required: true
   region:
     description:
        - Region that the service belongs to (`region_name` is used for auth.)
     required: true
   enabled:
     description:
        - Is the service enabled
     required: false
     default: True
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
requirements:
    - "python >= 2.6"
    - "shade"
'''

EXAMPLES = '''
# Create a service for glance
- os_keystone_endpoint:
     cloud: mycloud
     state: present
     service: glance
     interface: public
     url: http://controller:9292
     region: RegionOne
# Delete a service
- os_keystone_endpoint:
     cloud: mycloud
     state: absent
     name: image
     interface: public
     region: RegionOne
'''

RETURN = '''
endpoint:
    description: Dictionary describing the endpoint.
    returned: On success when I(state) is 'present'
    type: dictionary
    contains:
        id:
            description: Endpoint ID.
            type: string
            sample: "3292f020780b4d5baf27ff7e1d224c44"
        region:
            description: Region Name
            type: string
            sample: "RegionOne"
        service:
            description: Service ID
            type: string
            sample: "b91f1318f735494a825a55388ee118f3"
        interface:
            description: Endpoint Interface
            type: string
            sample: "public"
        url:
            description: Service URL
            type: string
            sample: "http://controller:9292"
        enabled:
            description: Service status.
            type: boolean
            sample: True
id:
    description: The endpoint ID.
    returned: On success when I(state) is 'present'
    type: string
    sample: "3292f020780b4d5baf27ff7e1d224c44"
'''


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
        service=dict(required=True),
        interface=dict(required=True, choices=['admin', 'public', 'internal']),
        url=dict(required=True),
        region=dict(required=True),
        enabled=dict(default=True, type='bool'),
        state=dict(default='present', choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')
    if StrictVersion(shade.__version__) < StrictVersion('1.1.0'):
        module.fail_json(msg="To utilize this module, the installed version of"
                             "the shade library MUST be >=1.1.0")

    service_name = module.params['service']
    interface = module.params['interface']
    url = module.params['url']
    region = module.params['region']
    enabled = module.params['enabled']
    state = module.params['state']

    try:
        cloud = shade.operator_cloud(**module.params)

        service = cloud.get_service(service_name)
        endpoints = cloud.search_endpoints(filters=dict(region=region,
                                                        service_id=service.id,
                                                        interface=interface))

        if len(endpoints) > 1:
            module.fail_json(msg='Service %s, interface %s and region %s are ' \
                                 'not unique' % \
                                 (service_name, interface, region))
        elif len(endpoints) == 1:
            endpoint = endpoints[0]
        else:
            endpoint = None

        if module.check_mode:
            module.exit_json(changed=_system_state_change(module, endpoint))

        if state == 'present':
            if endpoint is None:
                result = cloud.create_endpoint(service_name_or_id=service.id,
                    url=url, interface=interface, region=region, enabled=True)
                endpoint = result[0]
                changed = True
            else:
                if _needs_update(module, endpoint):
                    endpoint = cloud.update_endpoint(
                        endpoint.id, url=url, enabled=enabled)
                    changed = True
                else:
                    changed = False
            module.exit_json(changed=changed, endpoint=endpoint, id=endpoint.id)

        elif state == 'absent':
            if endpoint is None:
                changed=False
            else:
                cloud.delete_endpoint(endpoint.id)
                changed=True
            module.exit_json(changed=changed)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
