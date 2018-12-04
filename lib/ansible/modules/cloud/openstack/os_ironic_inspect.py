#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2015-2016, Hewlett Packard Enterprise Development Company LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_ironic_inspect
short_description: Explicitly triggers baremetal node introspection in ironic.
extends_documentation_fragment: openstack
author: "Julia Kreger (@juliakreger)"
version_added: "2.1"
description:
    - Requests Ironic to set a node into inspect state in order to collect metadata regarding the node.
      This command may be out of band or in-band depending on the ironic driver configuration.
      This is only possible on nodes in 'manageable' and 'available' state.
options:
    mac:
      description:
        - unique mac address that is used to attempt to identify the host.
    uuid:
      description:
        - globally unique identifier (UUID) to identify the host.
    name:
      description:
        - unique name identifier to identify the host in Ironic.
    ironic_url:
      description:
        - If noauth mode is utilized, this is required to be set to the endpoint URL for the Ironic API.
          Use with "auth" and "auth_type" settings set to None.
    timeout:
      description:
        - A timeout in seconds to tell the role to wait for the node to complete introspection if wait is set to True.
      default: 1200
    availability_zone:
      description:
        - Ignored. Present for backwards compatibility

requirements: ["openstacksdk"]
'''

RETURN = '''
ansible_facts:
    description: Dictionary of new facts representing discovered properties of the node..
    returned: changed
    type: complex
    contains:
        memory_mb:
            description: Amount of node memory as updated in the node properties
            type: string
            sample: "1024"
        cpu_arch:
            description: Detected CPU architecture type
            type: string
            sample: "x86_64"
        local_gb:
            description: Total size of local disk storage as updaed in node properties.
            type: string
            sample: "10"
        cpus:
            description: Count of cpu cores defined in the updated node properties.
            type: string
            sample: "1"
'''

EXAMPLES = '''
# Invoke node inspection
- os_ironic_inspect:
    name: "testnode1"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def _choose_id_value(module):
    if module.params['uuid']:
        return module.params['uuid']
    if module.params['name']:
        return module.params['name']
    return None


def main():
    argument_spec = openstack_full_argument_spec(
        auth_type=dict(required=False),
        uuid=dict(required=False),
        name=dict(required=False),
        mac=dict(required=False),
        ironic_url=dict(required=False),
        timeout=dict(default=1200, type='int', required=False),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if (module.params['auth_type'] in [None, 'None'] and
            module.params['ironic_url'] is None):
        module.fail_json(msg="Authentication appears to be disabled, "
                             "Please define an ironic_url parameter")

    if (module.params['ironic_url'] and
            module.params['auth_type'] in [None, 'None']):
        module.params['auth'] = dict(
            endpoint=module.params['ironic_url']
        )

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        if module.params['name'] or module.params['uuid']:
            server = cloud.get_machine(_choose_id_value(module))
        elif module.params['mac']:
            server = cloud.get_machine_by_mac(module.params['mac'])
        else:
            module.fail_json(msg="The worlds did not align, "
                                 "the host was not found as "
                                 "no name, uuid, or mac was "
                                 "defined.")
        if server:
            cloud.inspect_machine(server['uuid'], module.params['wait'])
            # TODO(TheJulia): diff properties, ?and ports? and determine
            # if a change occurred.  In theory, the node is always changed
            # if introspection is able to update the record.
            module.exit_json(changed=True,
                             ansible_facts=server['properties'])

        else:
            module.fail_json(msg="node not found.")

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
