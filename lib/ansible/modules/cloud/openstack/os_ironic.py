#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2014, Hewlett-Packard Development Company, L.P.
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_ironic
short_description: Create/Delete Bare Metal Resources from OpenStack
extends_documentation_fragment: openstack
author: "Monty Taylor (@emonty)"
version_added: "2.0"
description:
    - Create or Remove Ironic nodes from OpenStack.
options:
    state:
      description:
        - Indicates desired state of the resource
      choices: ['present', 'absent']
      default: present
    uuid:
      description:
        - globally unique identifier (UUID) to be given to the resource. Will
          be auto-generated if not specified, and name is specified.
        - Definition of a UUID will always take precedence to a name value.
      required: false
      default: None
    name:
      description:
        - unique name identifier to be given to the resource.
      required: false
      default: None
    driver:
      description:
        - The name of the Ironic Driver to use with this node.
      required: true
      default: None
    chassis_uuid:
      description:
        - Associate the node with a pre-defined chassis.
      required: false
      default: None
    ironic_url:
      description:
        - If noauth mode is utilized, this is required to be set to the
          endpoint URL for the Ironic API.  Use with "auth" and "auth_type"
          settings set to None.
      required: false
      default: None
    driver_info:
      description:
        - Information for this server's driver. Will vary based on which
          driver is in use. Any sub-field which is populated will be validated
          during creation.
      suboptions:
        power:
            description:
                - Information necessary to turn this server on / off.
                  This often includes such things as IPMI username, password, and IP address.
            required: true
        deploy:
            description:
                - Information necessary to deploy this server directly, without using Nova. THIS IS NOT RECOMMENDED.
        console:
            description:
                - Information necessary to connect to this server's serial console.  Not all drivers support this.
        management:
            description:
                - Information necessary to interact with this server's management interface. May be shared by power_info in some cases.
            required: true
    nics:
      description:
        - 'A list of network interface cards, eg, " - mac: aa:bb:cc:aa:bb:cc"'
      required: true
    properties:
      description:
        - Definition of the physical characteristics of this server, used for scheduling purposes
      suboptions:
        cpu_arch:
          description:
            - CPU architecture (x86_64, i686, ...)
          default: x86_64
        cpus:
          description:
            - Number of CPU cores this machine has
          default: 1
        ram:
          description:
            - amount of RAM this machine has, in MB
          default: 1
        disk_size:
          description:
            - size of first storage device in this machine (typically /dev/sda), in GB
          default: 1
    skip_update_of_driver_password:
      description:
        - Allows the code that would assert changes to nodes to skip the
          update if the change is a single line consisting of the password
          field.  As of Kilo, by default, passwords are always masked to API
          requests, which means the logic as a result always attempts to
          re-assert the password field.
      required: false
      default: false
    availability_zone:
      description:
        - Ignored. Present for backwards compatibility
      required: false

requirements: ["shade", "jsonpatch"]
'''

EXAMPLES = '''
# Enroll a node with some basic properties and driver info
- os_ironic:
    cloud: "devstack"
    driver: "pxe_ipmitool"
    uuid: "00000000-0000-0000-0000-000000000002"
    properties:
      cpus: 2
      cpu_arch: "x86_64"
      ram: 8192
      disk_size: 64
    nics:
      - mac: "aa:bb:cc:aa:bb:cc"
      - mac: "dd:ee:ff:dd:ee:ff"
    driver_info:
      power:
        ipmi_address: "1.2.3.4"
        ipmi_username: "admin"
        ipmi_password: "adminpass"
    chassis_uuid: "00000000-0000-0000-0000-000000000001"

'''

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

try:
    import jsonpatch
    HAS_JSONPATCH = True
except ImportError:
    HAS_JSONPATCH = False


def _parse_properties(module):
    p = module.params['properties']
    props = dict(
        cpu_arch=p.get('cpu_arch') if p.get('cpu_arch') else 'x86_64',
        cpus=p.get('cpus') if p.get('cpus') else 1,
        memory_mb=p.get('ram') if p.get('ram') else 1,
        local_gb=p.get('disk_size') if p.get('disk_size') else 1,
    )
    return props


def _parse_driver_info(module):
    p = module.params['driver_info']
    info = p.get('power')
    if not info:
        raise shade.OpenStackCloudException(
            "driver_info['power'] is required")
    if p.get('console'):
        info.update(p.get('console'))
    if p.get('management'):
        info.update(p.get('management'))
    if p.get('deploy'):
        info.update(p.get('deploy'))
    return info


def _choose_id_value(module):
    if module.params['uuid']:
        return module.params['uuid']
    if module.params['name']:
        return module.params['name']
    return None




def _choose_if_password_only(module, patch):
    if len(patch) is 1:
        if 'password' in patch[0]['path'] and module.params['skip_update_of_masked_password']:
            # Return false to abort update as the password appears
            # to be the only element in the patch.
            return False
    return True


def _exit_node_not_updated(module, server):
    module.exit_json(
        changed=False,
        result="Node not updated",
        uuid=server['uuid'],
        provision_state=server['provision_state']
    )


def main():
    argument_spec = openstack_full_argument_spec(
        uuid=dict(required=False),
        name=dict(required=False),
        driver=dict(required=False),
        driver_info=dict(type='dict', required=True),
        nics=dict(type='list', required=True),
        properties=dict(type='dict', default={}),
        ironic_url=dict(required=False),
        chassis_uuid=dict(required=False),
        skip_update_of_masked_password=dict(required=False, type='bool'),
        state=dict(required=False, default='present')
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')
    if not HAS_JSONPATCH:
        module.fail_json(msg='jsonpatch is required for this module')
    if (module.params['auth_type'] in [None, 'None'] and
            module.params['ironic_url'] is None):
        module.fail_json(msg="Authentication appears to be disabled, "
                             "Please define an ironic_url parameter")

    if (module.params['ironic_url'] and
            module.params['auth_type'] in [None, 'None']):
        module.params['auth'] = dict(
            endpoint=module.params['ironic_url']
        )

    node_id = _choose_id_value(module)

    try:
        cloud = shade.operator_cloud(**module.params)
        server = cloud.get_machine(node_id)
        if module.params['state'] == 'present':
            if module.params['driver'] is None:
                module.fail_json(msg="A driver must be defined in order "
                                     "to set a node to present.")

            properties = _parse_properties(module)
            driver_info = _parse_driver_info(module)
            kwargs = dict(
                driver=module.params['driver'],
                properties=properties,
                driver_info=driver_info,
                name=module.params['name'],
            )

            if module.params['chassis_uuid']:
                kwargs['chassis_uuid'] = module.params['chassis_uuid']

            if server is None:
                # Note(TheJulia): Add a specific UUID to the request if
                # present in order to be able to re-use kwargs for if
                # the node already exists logic, since uuid cannot be
                # updated.
                if module.params['uuid']:
                    kwargs['uuid'] = module.params['uuid']

                server = cloud.register_machine(module.params['nics'],
                                                **kwargs)
                module.exit_json(changed=True, uuid=server['uuid'],
                                 provision_state=server['provision_state'])
            else:
                # TODO(TheJulia): Presently this does not support updating
                # nics.  Support needs to be added.
                #
                # Note(TheJulia): This message should never get logged
                # however we cannot realistically proceed if neither a
                # name or uuid was supplied to begin with.
                if not node_id:
                    module.fail_json(msg="A uuid or name value "
                                         "must be defined")

                # Note(TheJulia): Constructing the configuration to compare
                # against.  The items listed in the server_config block can
                # be updated via the API.

                server_config = dict(
                    driver=server['driver'],
                    properties=server['properties'],
                    driver_info=server['driver_info'],
                    name=server['name'],
                )

                # Add the pre-existing chassis_uuid only if
                # it is present in the server configuration.
                if hasattr(server, 'chassis_uuid'):
                    server_config['chassis_uuid'] = server['chassis_uuid']

                # Note(TheJulia): If a password is defined and concealed, a
                # patch will always be generated and re-asserted.
                patch = jsonpatch.JsonPatch.from_diff(server_config, kwargs)

                if not patch:
                    _exit_node_not_updated(module, server)
                elif _choose_if_password_only(module, list(patch)):
                    # Note(TheJulia): Normally we would allow the general
                    # exception catch below, however this allows a specific
                    # message.
                    try:
                        server = cloud.patch_machine(
                            server['uuid'],
                            list(patch))
                    except Exception as e:
                        module.fail_json(msg="Failed to update node, "
                                         "Error: %s" % e.message)

                    # Enumerate out a list of changed paths.
                    change_list = []
                    for change in list(patch):
                        change_list.append(change['path'])
                    module.exit_json(changed=True,
                                     result="Node Updated",
                                     changes=change_list,
                                     uuid=server['uuid'],
                                     provision_state=server['provision_state'])

            # Return not updated by default as the conditions were not met
            # to update.
            _exit_node_not_updated(module, server)

        if module.params['state'] == 'absent':
            if not node_id:
                module.fail_json(msg="A uuid or name value must be defined "
                                     "in order to remove a node.")

            if server is not None:
                cloud.unregister_machine(module.params['nics'],
                                         server['uuid'])
                module.exit_json(changed=True, result="deleted")
            else:
                module.exit_json(changed=False, result="Server not found")

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

if __name__ == "__main__":
    main()
