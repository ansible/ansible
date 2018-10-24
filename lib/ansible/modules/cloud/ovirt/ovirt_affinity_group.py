#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ovirt_affinity_group
short_description: Module to manage affinity groups in oVirt/RHV
version_added: "2.3"
author:
- Ondra Machacek (@machacekondra)
description:
    - "This module manage affinity groups in oVirt/RHV. It can also manage assignments
       of those groups to VMs."
options:
    name:
        description:
            - Name of the affinity group to manage.
        required: true
    state:
        description:
            - Should the affinity group be present or absent.
        choices: [ absent, present ]
        default: present
    cluster:
        description:
            - Name of the cluster of the affinity group.
    description:
        description:
            - Description of the affinity group.
    host_enforcing:
        description:
            - If I(yes) VM cannot start on host if it does not satisfy the C(host_rule).
            - This parameter is support since oVirt/RHV 4.1 version.
        type: bool
    host_rule:
        description:
            - If I(positive) I(all) VMs in this group should run on the this host.
            - If I(negative) I(no) VMs in this group should run on the this host.
            - This parameter is support since oVirt/RHV 4.1 version.
        choices: [ negative, positive ]
    vm_enforcing:
        description:
            - If I(yes) VM cannot start if it does not satisfy the C(vm_rule).
        type: bool
    vm_rule:
        description:
            - If I(positive) I(all) VMs in this group should run on the host defined by C(host_rule).
            - If I(negative) I(no) VMs in this group should run on the host defined by C(host_rule).
            - If I(disabled) this affinity group doesn't take effect.
        choices: [ disabled, negative, positive ]
    vms:
        description:
            - List of the VMs names, which should have assigned this affinity group.
    hosts:
        description:
            - List of the hosts names, which should have assigned this affinity group.
            - This parameter is support since oVirt/RHV 4.1 version.
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

- name: Create(if not exists) and assign affinity group to VMs vm1 and vm2 and host host1
  ovirt_affinity_group:
    name: mygroup
    cluster: mycluster
    vm_enforcing: true
    vm_rule: positive
    host_enforcing: true
    host_rule: positive
    vms:
      - vm1
      - vm2
    hosts:
      - host1

- name: Detach VMs from affinity group and disable VM rule
  ovirt_affinity_group:
    name: mygroup
    cluster: mycluster
    vm_enforcing: false
    vm_rule: disabled
    host_enforcing: true
    host_rule: positive
    vms: []
    hosts:
      - host1
      - host2

- name: Remove affinity group
  ovirt_affinity_group:
    state: absent
    cluster: mycluster
    name: mygroup
'''

RETURN = '''
id:
    description: ID of the affinity group which is managed
    returned: On success if affinity group is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
affinity_group:
    description: "Dictionary of all the affinity group attributes. Affinity group attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/affinity_group."
    returned: On success if affinity group is found.
    type: str
'''

import traceback

try:
    import ovirtsdk4.types as otypes
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    BaseModule,
    check_sdk,
    check_support,
    create_connection,
    get_id_by_name,
    equal,
    engine_supported,
    ovirt_full_argument_spec,
    search_by_name,
)


class AffinityGroupsModule(BaseModule):

    def __init__(self, vm_ids, host_ids, *args, **kwargs):
        super(AffinityGroupsModule, self).__init__(*args, **kwargs)
        self._vm_ids = vm_ids
        self._host_ids = host_ids

    def update_vms(self, affinity_group):
        """
        This method iterate via the affinity VM assignnments and datech the VMs
        which should not be attached to affinity and attach VMs which should be
        attached to affinity.
        """
        assigned_vms = self.assigned_vms(affinity_group)
        to_remove = [vm for vm in assigned_vms if vm not in self._vm_ids]
        to_add = [vm for vm in self._vm_ids if vm not in assigned_vms]
        ag_service = self._service.group_service(affinity_group.id)
        for vm in to_remove:
            ag_service.vms_service().vm_service(vm).remove()
        for vm in to_add:
            # API return <action> element instead of VM element, so we
            # need to WA this issue, for oVirt/RHV versions having this bug:
            try:
                ag_service.vms_service().add(otypes.Vm(id=vm))
            except ValueError as ex:
                if 'complete' not in str(ex):
                    raise ex

    def post_create(self, affinity_group):
        self.update_vms(affinity_group)

    def post_update(self, affinity_group):
        self.update_vms(affinity_group)

    def build_entity(self):
        affinity_group = otypes.AffinityGroup(
            name=self._module.params['name'],
            description=self._module.params['description'],
            positive=(
                self._module.params['vm_rule'] == 'positive'
            ) if self._module.params['vm_rule'] is not None else None,
            enforcing=(
                self._module.params['vm_enforcing']
            ) if self._module.params['vm_enforcing'] is not None else None,
        )

        # Those attributes are Supported since 4.1:
        if not engine_supported(self._connection, '4.1'):
            return affinity_group

        affinity_group.hosts_rule = otypes.AffinityRule(
            positive=(
                self.param('host_rule') == 'positive'
            ) if self.param('host_rule') is not None else None,
            enforcing=self.param('host_enforcing'),
        ) if (
            self.param('host_enforcing') is not None or
            self.param('host_rule') is not None
        ) else None

        affinity_group.vms_rule = otypes.AffinityRule(
            positive=(
                self.param('vm_rule') == 'positive'
            ) if self.param('vm_rule') is not None else None,
            enforcing=self.param('vm_enforcing'),
            enabled=(
                self.param('vm_rule') in ['negative', 'positive']
            ) if self.param('vm_rule') is not None else None,
        ) if (
            self.param('vm_enforcing') is not None or
            self.param('vm_rule') is not None
        ) else None

        affinity_group.hosts = [
            otypes.Host(id=host_id) for host_id in self._host_ids
        ] if self._host_ids is not None else None

        return affinity_group

    def assigned_vms(self, affinity_group):
        if getattr(affinity_group.vms, 'href', None):
            return sorted([
                vm.id for vm in self._connection.follow_link(affinity_group.vms)
            ])
        else:
            return sorted([vm.id for vm in affinity_group.vms])

    def update_check(self, entity):
        assigned_vms = self.assigned_vms(entity)
        do_update = (
            equal(self.param('description'), entity.description) and equal(self.param('vm_enforcing'), entity.enforcing) and equal(
                self.param('vm_rule') == 'positive' if self.param('vm_rule') else None,
                entity.positive
            ) and equal(self._vm_ids, assigned_vms)
        )
        # Following attributes is supported since 4.1,
        # so return if it doesn't exist:
        if not engine_supported(self._connection, '4.1'):
            return do_update

        # Following is supported since 4.1:
        return do_update and (
            equal(
                self.param('host_rule') == 'positive' if self.param('host_rule') else None,
                entity.hosts_rule.positive) and equal(self.param('host_enforcing'), entity.hosts_rule.enforcing) and equal(
                self.param('vm_rule') in ['negative', 'positive'] if self.param('vm_rule') else None,
                entity.vms_rule.enabled) and equal(self._host_ids, sorted([host.id for host in entity.hosts]))
        )


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(type='str', default='present', choices=['absent', 'present']),
        cluster=dict(type='str', required=True),
        name=dict(type='str', required=True),
        description=dict(type='str'),
        vm_enforcing=dict(type='bool'),
        vm_rule=dict(type='str', choices=['disabled', 'negative', 'positive']),
        host_enforcing=dict(type='bool'),
        host_rule=dict(type='str', choices=['negative', 'positive']),
        vms=dict(type='list'),
        hosts=dict(type='list'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    check_sdk(module)
    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        # Check if unsupported parameters were passed:
        supported_41 = ('host_enforcing', 'host_rule', 'hosts')
        if not check_support(
            version='4.1',
            connection=connection,
            module=module,
            params=supported_41,
        ):
            module.fail_json(
                msg='Following parameters are supported since 4.1: {params}'.format(
                    params=supported_41,
                )
            )
        clusters_service = connection.system_service().clusters_service()
        vms_service = connection.system_service().vms_service()
        hosts_service = connection.system_service().hosts_service()
        cluster_name = module.params['cluster']
        cluster = search_by_name(clusters_service, cluster_name)
        if cluster is None:
            raise Exception("Cluster '%s' was not found." % cluster_name)
        cluster_service = clusters_service.cluster_service(cluster.id)
        affinity_groups_service = cluster_service.affinity_groups_service()

        # Fetch VM ids which should be assigned to affinity group:
        vm_ids = sorted([
            get_id_by_name(vms_service, vm_name)
            for vm_name in module.params['vms']
        ]) if module.params['vms'] is not None else None
        # Fetch host ids which should be assigned to affinity group:
        host_ids = sorted([
            get_id_by_name(hosts_service, host_name)
            for host_name in module.params['hosts']
        ]) if module.params['hosts'] is not None else None

        affinity_groups_module = AffinityGroupsModule(
            connection=connection,
            module=module,
            service=affinity_groups_service,
            vm_ids=vm_ids,
            host_ids=host_ids,
        )

        state = module.params['state']
        if state == 'present':
            ret = affinity_groups_module.create()
        elif state == 'absent':
            ret = affinity_groups_module.remove()

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
