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

DOCUMENTATION = '''
---
module: os_ironic_node
version_added: "1.10"
short_description: Activate/Deactivate Bare Metal Resources from OpenStack
extends_documentation_fragment: openstack
description:
    - Deploy to nodes controlled by Ironic.
options:
    state:
      description:
        - Indicates desired state of the resource
      choices: ['present', 'absent']
      default: present
    uuid:
      description:
        - globally unique identifier (UUID) to be given to the resource.
      required: false
      default: None
    ironic_url:
      description:
        - If noauth mode is utilized, this is required to be set to the
          endpoint URL for the Ironic API.  Use with "auth" and "auth_plugin"
          settings set to None.
      required: false
      default: None
    config_drive:
      description:
        - A configdrive file or HTTP(S) URL that will be passed along to the
          node.
      required: false
      default: None
    instance_info:
      description:
        - Definition of the instance information which is used to deploy
          the node.
        image_source:
          description:
            - An HTTP(S) URL where the image can be retrieved from.
        image_checksum:
          description:
            - The checksum of image_source.
        image_disk_format:
          description:
            - The type of image that has been requested to be deployed.
requirements: ["shade"]
'''

EXAMPLES = '''
# Activate a node by booting an image with a configdrive attached
os_ironic_node:
  cloud: "openstack"
  uuid: "d44666e1-35b3-4f6b-acb0-88ab7052da69"
  state: present
  config_drive: "http://192.168.1.1/host-configdrive.iso"
  instance_info:
    image_source: "http://192.168.1.1/deploy_image.img"
    image_checksum: "356a6b55ecc511a20c33c946c4e678af"
    image_disk_format: "qcow"
  delegate_to: localhost
'''


def _prepare_instance_info_patch(instance_info):
    patch = []
    patch.append({
        'op': 'replace',
        'path': '/instance_info',
        'value': instance_info
    })
    return patch


def main():
    argument_spec = openstack_full_argument_spec(
        uuid=dict(required=True),
        instance_info=dict(type='dict', required=True),
        config_drive=dict(required=False),
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
        instance_info = module.params['instance_info']
        uuid = module.params['uuid']
        if module.params['state'] == 'present':
            if server is None:
                module.fail_json(msg="node not found")
            else:
                # TODO: compare properties here and update if necessary
                #       ... but the interface for that is terrible!
                if server.provision_state is "active":
                    module.exit_json(
                        changed=False,
                        result="Node already in an active state"
                    )

                patch = _prepare_instance_info_patch(instance_info)
                cloud.set_node_instance_info(uuid, patch)
                cloud.validate_node(uuid)
                cloud.activate_node(uuid, module.params['config_drive'])
                # TODO: Add more error checking and a wait option.
                module.exit_json(changed=False, result="node activated")

        if module.params['state'] == 'absent':
            if server.provision_state is not "deleted":
                cloud.purge_node_instance_info(uuid)
                cloud.deactivate_node(uuid)
                module.exit_json(changed=True, result="deleted")
            else:
                module.exit_json(changed=False, result="node not found")
    except shade.OpenStackCloudException as e:
        module.fail_json(msg=e.message)


# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
main()
