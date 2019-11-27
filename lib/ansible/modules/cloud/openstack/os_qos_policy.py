#!/usr/bin/python
# coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_qos_policy
short_description: Add/Remove QoS Policy in an OpenStack cloud
extends_documentation_fragment: openstack
version_added: "2.10"
author: Daniel Speichert (@dasp)
description:
  - Add or Remove a QoS policy in an OpenStack cloud
options:
  state:
    description:
      - Indicate desired state of the resource
    choices: ['present', 'absent']
    default: present
    type: str
  name:
    description:
      - The name of the QoS policy that should be created. Although Neutron
        allows for non-unique QoS policy names, this module enforces QoS policy
        name uniqueness.
    required: true
    type: str
  description:
    description:
      - Description of created QoS policy.
    type: str
  shared:
    description:
      - Set the QoS policy as shared
    type: bool
  default:
    description:
      - Set the QoS policy as default for project
    type: bool
  project:
    description:
      - Project name or ID to create QoS policy in (admin-only)
      - Mutually exclusive with C(project_id)
    type: str
  project_id:
    description:
      - Project ID to create QoS policy in (admin-only)
      - Avoids project lookup call if ID is known
    type: str
  extra_specs:
    description:
      - Dictionary with extra key/value pairs passed to the API
    required: false
    default: {}
    type: dict
requirements:
  - "python >= 2.7"
  - "openstacksdk"
'''

EXAMPLES = '''
# Create a new (or update an existing) QoS policy
- os_qos_policy:
    state: present
    name: mark-cs1
    description: applies CS1 DSCP mark
    shared: true

# Delete a QoS policy
- os_subnet:
    state: absent
    name: mark-cs1
'''

RETURN = '''
id:
    description: Policy ID that was created or already exists
    returned: success
    type: str
    sample: 7cf120a1-f579-4e04-aa3e-ebd0cda0d988
qos_policy:
    description: The policy representation object as returned by openstacksdk
    returned: success
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, \
    openstack_module_kwargs, openstack_cloud_from_module


def _can_update(qos_policy, module):
    """Check for differences in non-updatable values"""
    project_id = module.params['project_id']

    if project_id and qos_policy['project_id'] != project_id:
        module.fail_json(msg='Cannot update project_id in existing QoS policy')


def _needs_update(qos_policy, module):
    """Check for differences in the updatable values."""

    # First check if we are trying to update something we're not allowed to
    _can_update(qos_policy, module)

    # now check for the things we are allowed to update
    name = module.params['name']
    description = module.params['description']
    shared = module.params['shared']
    default = module.params['default']
    extra_specs = module.params['extra_specs']

    if qos_policy['name'] != name:
        return True
    if description is not None and qos_policy['description'] != description:
        return True
    if shared is not None and qos_policy['shared'] != shared:
        return True
    if default is not None and qos_policy['is_default'] != default:
        return True

    for key in extra_specs:
        if key not in qos_policy:
            return True
        if qos_policy[key] != extra_specs[key]:
            return True

    return False


def _system_state_change(module, qos_policy):
    state = module.params['state']
    if state == 'present':
        if not qos_policy:
            return True
        return _needs_update(qos_policy, module)
    if state == 'absent' and qos_policy:
        return True

    return False


def main():
    argument_spec = openstack_full_argument_spec(
        state=dict(type='str', default='present', choices=['absent', 'present']),
        name=dict(type='str', required=True),
        description=dict(type='str', required=False),
        shared=dict(type='bool', required=False),
        default=dict(type='bool', required=False),
        project=dict(type='str', required=False),
        project_id=dict(type='str', required=False),
        extra_specs=dict(type='dict', default=dict()),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           mutually_exclusive=[['project', 'project_id']],
                           supports_check_mode=True,
                           **module_kwargs)

    state = module.params['state']
    name = module.params['name']
    description = module.params['description']
    shared = module.params['shared']
    default = module.params['default']
    project = module.params['project']
    project_id = module.params['project_id']
    extra_specs = module.params['extra_specs']

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        if project is not None:
            proj = cloud.get_project(project)
            if proj is None:
                module.fail_json(msg='Project %s could not be found' % project)
            project_id = proj['id']
            filters = {'tenant_id': project_id}
        elif project_id is not None:
            filters = {'tenant_id': project_id}
        else:
            filters = None

        qos_policy = cloud.get_qos_policy(name, filters=filters)

        if module.check_mode:
            module.exit_json(changed=_system_state_change(module, qos_policy))

        if state == 'present':
            if not qos_policy:
                kwargs = dict(
                    name=name,
                    description=description,
                    shared=shared,
                    default=default,
                    project_id=project_id)
                dup_args = set(kwargs.keys()) & set(extra_specs.keys())
                if dup_args:
                    raise ValueError('Duplicate key(s) {0} in extra_specs'
                                     .format(list(dup_args)))
                kwargs = dict(kwargs, **extra_specs)
                qos_policy = cloud.create_qos_policy(**kwargs)
                changed = True
            else:
                if _needs_update(qos_policy, module):
                    cloud.update_qos_policy(qos_policy['id'],
                                            name=name,
                                            description=description,
                                            shared=shared,
                                            default=default)
                    changed = True
                else:
                    changed = False
            module.exit_json(changed=changed,
                             qos_policy=qos_policy,
                             id=qos_policy['id'])

        elif state == 'absent':
            if not qos_policy:
                changed = False
            else:
                changed = True
                cloud.delete_qos_policy(qos_policy['id'])
            module.exit_json(changed=changed)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
