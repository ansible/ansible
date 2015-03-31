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

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

# TODO FIX UUID/Add node support
DOCUMENTATION = '''
---
module: os_ironic
short_description: Create/Delete Bare Metal Resources from OpenStack
version_added: "1.10"
extends_documentation_fragment: openstack
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
          be auto-generated if not specified.
      required: false
      default: None
    driver:
      description:
        - The name of the Ironic Driver to use with this node.
      required: true
      default: None
    ironic_url:
      description:
        - If noauth mode is utilized, this is required to be set to the
          endpoint URL for the Ironic API.  Use with "auth" and "auth_plugin"
          settings set to None.
      required: false
      default: None
    driver_info:
      description:
        - Information for this server's driver. Will vary based on which
          driver is in use. Any sub-field which is populated will be validated
          during creation.
        power:
          - Information necessary to turn this server on / off. This often
            includes such things as IPMI username, password, and IP address.
          required: true
        deploy:
          - Information necessary to deploy this server directly, without
            using Nova. THIS IS NOT RECOMMENDED.
        console:
          - Information necessary to connect to this server's serial console.
            Not all drivers support this.
        management:
          - Information necessary to interact with this server's management
            interface. May be shared by power_info in some cases.
      required: true
    nics:
      description:
        - A list of network interface cards, eg, " - mac: aa:bb:cc:aa:bb:cc"
      required: true
    properties:
      description:
        - Definition of the physical characteristics of this server, used for
          scheduling purposes
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
            - size of first storage device in this machine (typically
              /dev/sda), in GB
          default: 1

requirements: ["shade"]
'''

EXAMPLES = '''
# Enroll a node with some basic properties and driver info
- os_ironic:
    cloud: "devstack"
    driver: "pxe_ipmitool"
    uuid: "a8cb6624-0d9f-4882-affc-046ebb96ec92"
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

'''


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


def main():
    argument_spec = openstack_full_argument_spec(
        uuid=dict(required=False),
        driver=dict(required=True),
        driver_info=dict(type='dict', required=True),
        nics=dict(type='list', required=True),
        properties=dict(type='dict', default={}),
        ironic_url=dict(required=False),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')
    if (module.params['auth_plugin'] == 'None' and
            module.params['ironic_url'] is None):
        module.fail_json(msg="Authentication appears disabled, Please "
                             "define an ironic_url parameter")

    if module.params['ironic_url'] and module.params['auth_plugin'] == 'None':
        module.params['auth'] = dict(endpoint=module.params['ironic_url'])
    try:
        cloud = shade.operator_cloud(**module.params)
        server = cloud.get_machine_by_uuid(module.params['uuid'])

        if module.params['state'] == 'present':
            properties = _parse_properties(module)
            driver_info = _parse_driver_info(module)
            kwargs = dict(
                uuid=module.params['uuid'],
                driver=module.params['driver'],
                properties=properties,
                driver_info=driver_info,
            )
            if server is None:
                server = cloud.register_machine(module.params['nics'],
                                                **kwargs)
                module.exit_json(changed=True, uuid=server.uuid)
            else:
                # TODO: compare properties here and update if necessary
                #       ... but the interface for that is terrible!
                module.exit_json(changed=False,
                                 result="Server already present")
        if module.params['state'] == 'absent':
            if server is not None:
                cloud.unregister_machine(module.params['nics'],
                                         module.params['uuid'])
                module.exit_json(changed=True, result="deleted")
            else:
                module.exit_json(changed=False, result="Server not found")
    except shade.OpenStackCloudException as e:
        module.fail_json(msg=e.message)


# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
main()
