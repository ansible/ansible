#!/usr/bin/python
# Copyright 2016 Jakub Jursa <jakub.jursa1@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_nova_host_aggregate
short_description: Manage OpenStack host aggregates
extends_documentation_fragment: openstack
author: "Jakub Jursa (@kuboj)"
version_added: "2.3"
description:
    - Create, update, or delete OpenStack host aggregates. If a aggregate
      with the supplied name already exists, it will be updated with the
      new name, new availability zone, new metadata and new list of hosts.
options:
  name:
    description: Name of the aggregate.
    required: true
  metadata:
    description: Metadata dict.
  availability_zone:
    description: Availability zone to create aggregate into.
  hosts:
    description: List of hosts to set for an aggregate.
  state:
    description: Should the resource be present or absent.
    choices: [present, absent]
    default: present
requirements:
    - "python >= 2.7"
    - "openstacksdk"
'''

EXAMPLES = '''
# Create a host aggregate
- os_nova_host_aggregate:
    cloud: mycloud
    state: present
    name: db_aggregate
    hosts:
      - host1
      - host2
    metadata:
      type: dbcluster
# Delete an aggregate
- os_nova_host_aggregate:
    cloud: mycloud
    state: absent
    name: db_aggregate
'''

RETURN = '''

'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def _needs_update(module, aggregate):
    new_metadata = (module.params['metadata'] or {})

    if module.params['availability_zone'] is not None:
        new_metadata['availability_zone'] = module.params['availability_zone']

    if ((module.params['name'] != aggregate.name) or
            (module.params['hosts'] is not None and set(module.params['hosts']) != set(aggregate.hosts)) or
            (module.params['availability_zone'] is not None and module.params['availability_zone'] != aggregate.availability_zone) or
            (module.params['metadata'] is not None and new_metadata != aggregate.metadata)):
        return True

    return False


def _system_state_change(module, aggregate):
    state = module.params['state']
    if state == 'absent' and aggregate:
        return True

    if state == 'present':
        if aggregate is None:
            return True
        return _needs_update(module, aggregate)

    return False


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        metadata=dict(required=False, default=None, type='dict'),
        availability_zone=dict(required=False, default=None),
        hosts=dict(required=False, default=None, type='list'),
        state=dict(default='present', choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    name = module.params['name']
    metadata = module.params['metadata']
    availability_zone = module.params['availability_zone']
    hosts = module.params['hosts']
    state = module.params['state']

    if metadata is not None:
        metadata.pop('availability_zone', None)

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        aggregates = cloud.search_aggregates(name_or_id=name)

        if len(aggregates) == 1:
            aggregate = aggregates[0]
        elif len(aggregates) == 0:
            aggregate = None
        else:
            raise Exception("Should not happen")

        if module.check_mode:
            module.exit_json(changed=_system_state_change(module, aggregate))

        if state == 'present':
            if aggregate is None:
                aggregate = cloud.create_aggregate(name=name,
                                                   availability_zone=availability_zone)
                if hosts:
                    for h in hosts:
                        cloud.add_host_to_aggregate(aggregate.id, h)
                if metadata:
                    cloud.set_aggregate_metadata(aggregate.id, metadata)
                changed = True
            else:
                if _needs_update(module, aggregate):
                    if availability_zone is not None:
                        aggregate = cloud.update_aggregate(aggregate.id, name=name,
                                                           availability_zone=availability_zone)
                    if metadata is not None:
                        metas = metadata
                        for i in (set(aggregate.metadata.keys()) - set(metadata.keys())):
                            if i != 'availability_zone':
                                metas[i] = None
                        cloud.set_aggregate_metadata(aggregate.id, metas)
                    if hosts is not None:
                        for i in (set(aggregate.hosts) - set(hosts)):
                            cloud.remove_host_from_aggregate(aggregate.id, i)
                        for i in (set(hosts) - set(aggregate.hosts)):
                            cloud.add_host_to_aggregate(aggregate.id, i)
                    changed = True
                else:
                    changed = False
            module.exit_json(changed=changed)

        elif state == 'absent':
            if aggregate is None:
                changed = False
            else:
                cloud.delete_aggregate(aggregate.id)
                changed = True
            module.exit_json(changed=changed)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
