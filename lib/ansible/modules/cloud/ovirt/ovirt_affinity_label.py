#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovirt_affinity_label
short_description: Module to manage affinity labels in oVirt/RHV
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "This module manage affinity labels in oVirt/RHV. It can also manage assignments
       of those labels to hosts and VMs."
options:
    name:
        description:
            - "Name of the affinity label to manage."
        required: true
    state:
        description:
            - "Should the affinity label be present or absent."
        choices: ['present', 'absent']
        default: present
    cluster:
        description:
            - "Name of the cluster where vms and hosts resides."
    vms:
        description:
            - "List of the VMs names, which should have assigned this affinity label."
    hosts:
        description:
            - "List of the hosts names, which should have assigned this affinity label."
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Create(if not exists) and assign affinity label to vms vm1 and vm2 and host host1
- ovirt_affinity_label:
    name: mylabel
    cluster: mycluster
    vms:
      - vm1
      - vm2
    hosts:
      - host1

# To detach all VMs from label
- ovirt_affinity_label:
    name: mylabel
    cluster: mycluster
    vms: []

# Remove affinity label
- ovirt_affinity_label:
    state: absent
    name: mylabel
'''

RETURN = '''
id:
    description: ID of the affinity label which is managed
    returned: On success if affinity label is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
affinity_label:
    description: "Dictionary of all the affinity label attributes. Affinity label attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/affinity_label."
    type: dict
    returned: On success if affinity label is found.
'''

import traceback

try:
    import ovirtsdk4.types as otypes
except ImportError:
    pass

from collections import defaultdict
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    BaseModule,
    check_sdk,
    create_connection,
    ovirt_full_argument_spec,
)


class AffinityLabelsModule(BaseModule):

    def build_entity(self):
        return otypes.AffinityLabel(name=self._module.params['name'])

    def post_create(self, entity):
        self.update_check(entity)

    def pre_remove(self, entity):
        self._module.params['vms'] = []
        self._module.params['hosts'] = []
        self.update_check(entity)

    def _update_label_assignments(self, entity, name, label_obj_type):
        objs_service = getattr(self._connection.system_service(), '%s_service' % name)()
        if self._module.params[name] is not None:
            objs = self._connection.follow_link(getattr(entity, name))
            objs_names = defaultdict(list)
            for obj in objs:
                labeled_entity = objs_service.service(obj.id).get()
                if self._module.params['cluster'] is None:
                    objs_names[labeled_entity.name].append(obj.id)
                elif self._connection.follow_link(labeled_entity.cluster).name == self._module.params['cluster']:
                    objs_names[labeled_entity.name].append(obj.id)

            for obj in self._module.params[name]:
                if obj not in objs_names:
                    for obj_id in objs_service.list(
                        search='name=%s and cluster=%s' % (obj, self._module.params['cluster'])
                    ):
                        label_service = getattr(self._service.service(entity.id), '%s_service' % name)()
                        if not self._module.check_mode:
                            label_service.add(**{
                                name[:-1]: label_obj_type(id=obj_id.id)
                            })
                        self.changed = True

            for obj in objs_names:
                if obj not in self._module.params[name]:
                    label_service = getattr(self._service.service(entity.id), '%s_service' % name)()
                    if not self._module.check_mode:
                        for obj_id in objs_names[obj]:
                            label_service.service(obj_id).remove()
                    self.changed = True

    def update_check(self, entity):
        self._update_label_assignments(entity, 'vms', otypes.Vm)
        self._update_label_assignments(entity, 'hosts', otypes.Host)
        return True


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent'],
            default='present',
        ),
        cluster=dict(default=None),
        name=dict(default=None, required=True),
        vms=dict(default=None, type='list'),
        hosts=dict(default=None, type='list'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('state', 'present', ['cluster']),
        ],
    )

    if module._name == 'ovirt_affinity_labels':
        module.deprecate("The 'ovirt_affinity_labels' module is being renamed 'ovirt_affinity_label'", version=2.8)

    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        affinity_labels_service = connection.system_service().affinity_labels_service()
        affinity_labels_module = AffinityLabelsModule(
            connection=connection,
            module=module,
            service=affinity_labels_service,
        )

        state = module.params['state']
        if state == 'present':
            ret = affinity_labels_module.create()
        elif state == 'absent':
            ret = affinity_labels_module.remove()

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
