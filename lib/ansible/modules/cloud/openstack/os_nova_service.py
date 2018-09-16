#!/usr/bin/python

# Copyright (c) 2018, VEXXHOST, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_nova_service
short_description: Manage Nova services
author: "Mohammed Naser (@_mnaser)"
extends_documentation_fragment: openstack
version_added: "2.8"
description:
  - Manage OpenStack Nova services (requires admin API)
options:
  host:
    description:
      - Host which runs the service to be managed (i.e. kvm10)
    required: true
  binary:
    description:
      - The binary which will be managed (i.e. nova-compute)
    required: true
  state:
    description:
      - Should the resource be enabled or disabled.
    choices: [enabled, disabled]
    required: true
  availability_zone:
    description:
      - Ignored. Present for backwards compatibility
'''

EXAMPLES = '''
# Disable a compute node for maintenance
- os_nova_service:
    cloud: sjc1
    host: kvm542
    binary: nova-compute
    state: disabled

# Enable a compute node post-maintenance
- os_keypair:
    cloud: sjc1
    host: kvm542
    binary: nova-compute
    state: enabled
'''

RETURN = '''
id:
  description: Service UUID.
  returned: success
  type: string
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def _system_state_change(module, service):
    state = module.params['state']
    return state != service.status


def main():
    argument_spec = openstack_full_argument_spec(
        host=dict(required=True),
        binary=dict(required=True),
        state=dict(required=True,
                   choices=['enabled', 'disabled']),
    )

    module_kwargs = openstack_module_kwargs()

    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    host = module.params['host']
    binary = module.params['binary']
    state = module.params['state']

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        services = [s for s in cloud.compute.services()
                    if s.host == host and s.binary == binary]

        if len(services) > 1:
            module.fail_json(msg="Found multiple services matching both host "
                                 "%s and binary %s" % (host, binary))

        if len(services) == 0:
            module.fail_json(msg="Failed to find service matching host %s "
                                 "and binary %s" % (host, binary))

        # We're absolutely sure we have the right one.
        service = services[0]
        changed = _system_state_change(module, service)

        if not module.check_mode and changed:
            if state == 'disabled':
                cloud.compute.disable_service(service, host, binary)
            elif state == 'enabled':
                cloud.compute.enable_service(service, host, binary)

        module.exit_json(changed=changed, id=service.id)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
