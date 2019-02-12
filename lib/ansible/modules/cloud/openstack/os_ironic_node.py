#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2015, Hewlett-Packard Development Company, L.P.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_ironic_node
short_description: Activate/Deactivate Bare Metal Resources from OpenStack
author: "Monty Taylor (@emonty)"
extends_documentation_fragment: openstack
version_added: "2.0"
description:
    - Deploy to nodes controlled by Ironic.
options:
    state:
      description:
        - Indicates desired state of the resource
      choices: ['present', 'absent']
      default: present
    deploy:
      description:
       - Indicates if the resource should be deployed. Allows for deployment
         logic to be disengaged and control of the node power or maintenance
         state to be changed.
      type: bool
      default: 'yes'
    uuid:
      description:
        - globally unique identifier (UUID) to be given to the resource.
    ironic_url:
      description:
        - If noauth mode is utilized, this is required to be set to the
          endpoint URL for the Ironic API.  Use with "auth" and "auth_type"
          settings set to None.
    config_drive:
      description:
        - A configdrive file or HTTP(S) URL that will be passed along to the
          node.
    instance_info:
      description:
        - Definition of the instance information which is used to deploy
          the node.  This information is only required when an instance is
          set to present.
      suboptions:
        image_source:
          description:
            - An HTTP(S) URL where the image can be retrieved from.
        image_checksum:
          description:
            - The checksum of image_source.
        image_disk_format:
          description:
            - The type of image that has been requested to be deployed.
    power:
      description:
        - A setting to allow power state to be asserted allowing nodes
          that are not yet deployed to be powered on, and nodes that
          are deployed to be powered off.
      choices: ['present', 'absent']
      default: present
    maintenance:
      description:
        - A setting to allow the direct control if a node is in
          maintenance mode.
      type: bool
      default: 'no'
    maintenance_reason:
      description:
        - A string expression regarding the reason a node is in a
          maintenance mode.
    wait:
      description:
        - A boolean value instructing the module to wait for node
          activation or deactivation to complete before returning.
      type: bool
      default: 'no'
      version_added: "2.1"
    timeout:
      description:
        - An integer value representing the number of seconds to
          wait for the node activation or deactivation to complete.
      version_added: "2.1"
    availability_zone:
      description:
        - Ignored. Present for backwards compatibility
'''

EXAMPLES = '''
# Activate a node by booting an image with a configdrive attached
os_ironic_node:
  cloud: "openstack"
  uuid: "d44666e1-35b3-4f6b-acb0-88ab7052da69"
  state: present
  power: present
  deploy: True
  maintenance: False
  config_drive: "http://192.168.1.1/host-configdrive.iso"
  instance_info:
    image_source: "http://192.168.1.1/deploy_image.img"
    image_checksum: "356a6b55ecc511a20c33c946c4e678af"
    image_disk_format: "qcow"
  delegate_to: localhost
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def _choose_id_value(module):
    if module.params['uuid']:
        return module.params['uuid']
    if module.params['name']:
        return module.params['name']
    return None


# TODO(TheJulia): Change this over to use the machine patch method
# in shade once it is available.
def _prepare_instance_info_patch(instance_info):
    patch = []
    patch.append({
        'op': 'replace',
        'path': '/instance_info',
        'value': instance_info
    })
    return patch


def _is_true(value):
    true_values = [True, 'yes', 'Yes', 'True', 'true', 'present', 'on']
    if value in true_values:
        return True
    return False


def _is_false(value):
    false_values = [False, None, 'no', 'No', 'False', 'false', 'absent', 'off']
    if value in false_values:
        return True
    return False


def _check_set_maintenance(module, cloud, node):
    if _is_true(module.params['maintenance']):
        if _is_false(node['maintenance']):
            cloud.set_machine_maintenance_state(
                node['uuid'],
                True,
                reason=module.params['maintenance_reason'])
            module.exit_json(changed=True, msg="Node has been set into "
                                               "maintenance mode")
        else:
            # User has requested maintenance state, node is already in the
            # desired state, checking to see if the reason has changed.
            if (str(node['maintenance_reason']) not in
                    str(module.params['maintenance_reason'])):
                cloud.set_machine_maintenance_state(
                    node['uuid'],
                    True,
                    reason=module.params['maintenance_reason'])
                module.exit_json(changed=True, msg="Node maintenance reason "
                                                   "updated, cannot take any "
                                                   "additional action.")
    elif _is_false(module.params['maintenance']):
        if node['maintenance'] is True:
            cloud.remove_machine_from_maintenance(node['uuid'])
            return True
    else:
        module.fail_json(msg="maintenance parameter was set but a valid "
                             "the value was not recognized.")
    return False


def _check_set_power_state(module, cloud, node):
    if 'power on' in str(node['power_state']):
        if _is_false(module.params['power']):
            # User has requested the node be powered off.
            cloud.set_machine_power_off(node['uuid'])
            module.exit_json(changed=True, msg="Power requested off")
    if 'power off' in str(node['power_state']):
        if (_is_false(module.params['power']) and
                _is_false(module.params['state'])):
            return False
        if (_is_false(module.params['power']) and
                _is_false(module.params['state'])):
            module.exit_json(
                changed=False,
                msg="Power for node is %s, node must be reactivated "
                    "OR set to state absent"
            )
        # In the event the power has been toggled on and
        # deployment has been requested, we need to skip this
        # step.
        if (_is_true(module.params['power']) and
                _is_false(module.params['deploy'])):
            # Node is powered down when it is not awaiting to be provisioned
            cloud.set_machine_power_on(node['uuid'])
            return True
    # Default False if no action has been taken.
    return False


def main():
    argument_spec = openstack_full_argument_spec(
        uuid=dict(required=False),
        name=dict(required=False),
        instance_info=dict(type='dict', required=False),
        config_drive=dict(required=False),
        ironic_url=dict(required=False),
        state=dict(required=False, default='present'),
        maintenance=dict(required=False),
        maintenance_reason=dict(required=False),
        power=dict(required=False, default='present'),
        deploy=dict(required=False, default=True),
        wait=dict(type='bool', required=False, default=False),
        timeout=dict(required=False, type='int', default=1800),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if (module.params['auth_type'] in [None, 'None'] and
            module.params['ironic_url'] is None):
        module.fail_json(msg="Authentication appears disabled, Please "
                             "define an ironic_url parameter")

    if (module.params['ironic_url'] and
            module.params['auth_type'] in [None, 'None']):
        module.params['auth'] = dict(
            endpoint=module.params['ironic_url']
        )

    node_id = _choose_id_value(module)

    if not node_id:
        module.fail_json(msg="A uuid or name value must be defined "
                             "to use this module.")
    sdk, cloud = openstack_cloud_from_module(module)
    try:
        node = cloud.get_machine(node_id)

        if node is None:
            module.fail_json(msg="node not found")

        uuid = node['uuid']
        instance_info = module.params['instance_info']
        changed = False
        wait = module.params['wait']
        timeout = module.params['timeout']

        # User has reqeusted desired state to be in maintenance state.
        if module.params['state'] == 'maintenance':
            module.params['maintenance'] = True

        if node['provision_state'] in [
                'cleaning',
                'deleting',
                'wait call-back']:
            module.fail_json(msg="Node is in %s state, cannot act upon the "
                                 "request as the node is in a transition "
                                 "state" % node['provision_state'])
        # TODO(TheJulia) This is in-development code, that requires
        # code in the shade library that is still in development.
        if _check_set_maintenance(module, cloud, node):
            if node['provision_state'] in 'active':
                module.exit_json(changed=True,
                                 result="Maintenance state changed")
            changed = True
            node = cloud.get_machine(node_id)

        if _check_set_power_state(module, cloud, node):
            changed = True
            node = cloud.get_machine(node_id)

        if _is_true(module.params['state']):
            if _is_false(module.params['deploy']):
                module.exit_json(
                    changed=changed,
                    result="User request has explicitly disabled "
                           "deployment logic"
                )

            if 'active' in node['provision_state']:
                module.exit_json(
                    changed=changed,
                    result="Node already in an active state."
                )

            if instance_info is None:
                module.fail_json(
                    changed=changed,
                    msg="When setting an instance to present, "
                        "instance_info is a required variable.")

            # TODO(TheJulia): Update instance info, however info is
            # deployment specific. Perhaps consider adding rebuild
            # support, although there is a known desire to remove
            # rebuild support from Ironic at some point in the future.
            patch = _prepare_instance_info_patch(instance_info)
            cloud.set_node_instance_info(uuid, patch)
            cloud.validate_node(uuid)
            if not wait:
                cloud.activate_node(uuid, module.params['config_drive'])
            else:
                cloud.activate_node(
                    uuid,
                    configdrive=module.params['config_drive'],
                    wait=wait,
                    timeout=timeout)
            # TODO(TheJulia): Add more error checking..
            module.exit_json(changed=changed, result="node activated")

        elif _is_false(module.params['state']):
            if node['provision_state'] not in "deleted":
                cloud.purge_node_instance_info(uuid)
                if not wait:
                    cloud.deactivate_node(uuid)
                else:
                    cloud.deactivate_node(
                        uuid,
                        wait=wait,
                        timeout=timeout)

                module.exit_json(changed=True, result="deleted")
            else:
                module.exit_json(changed=False, result="node not found")
        else:
            module.fail_json(msg="State must be present, absent, "
                                 "maintenance, off")

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
