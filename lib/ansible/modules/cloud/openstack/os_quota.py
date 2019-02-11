#!/usr/bin/python
# Copyright (c) 2016 Pason System Corporation
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_quota
short_description: Manage OpenStack Quotas
extends_documentation_fragment: openstack
version_added: "2.3"
author: "Michael Gale (@mgale) <gale.michael@gmail.com>"
description:
    - Manage OpenStack Quotas. Quotas can be created,
      updated or deleted using this module. A quota will be updated
      if matches an existing project and is present.
options:
    name:
        description:
            - Name of the OpenStack Project to manage.
        required: true
    state:
        description:
            - A value of present sets the quota and a value of absent resets the quota to system defaults.
        default: present
    backup_gigabytes:
        description: Maximum size of backups in GB's.
    backups:
        description: Maximum number of backups allowed.
    cores:
        description: Maximum number of CPU's per project.
    fixed_ips:
        description: Number of fixed IP's to allow.
    floating_ips:
        description: Number of floating IP's to allow in Compute.
        aliases: ['compute_floating_ips']
    floatingip:
        description: Number of floating IP's to allow in Network.
        aliases: ['network_floating_ips']
    gigabytes:
        description: Maximum volume storage allowed for project.
    gigabytes_lvm:
        description: Maximum size in GB's of individual lvm volumes.
    injected_file_size:
        description: Maximum file size in bytes.
    injected_files:
        description: Number of injected files to allow.
    injected_path_size:
        description: Maximum path size.
    instances:
        description: Maximum number of instances allowed.
    key_pairs:
        description: Number of key pairs to allow.
    loadbalancer:
        description: Number of load balancers to allow.
        version_added: "2.4"
    network:
        description: Number of networks to allow.
    per_volume_gigabytes:
        description: Maximum size in GB's of individual volumes.
    pool:
        description: Number of load balancer pools to allow.
        version_added: "2.4"
    port:
        description: Number of Network ports to allow, this needs to be greater than the instances limit.
    properties:
        description: Number of properties to allow.
    ram:
        description: Maximum amount of ram in MB to allow.
    rbac_policy:
        description: Number of policies to allow.
    router:
        description: Number of routers to allow.
    security_group_rule:
        description: Number of rules per security group to allow.
    security_group:
        description: Number of security groups to allow.
    server_group_members:
        description: Number of server group members to allow.
    server_groups:
        description: Number of server groups to allow.
    snapshots:
        description: Number of snapshots to allow.
    snapshots_lvm:
        description: Number of LVM snapshots to allow.
    subnet:
        description: Number of subnets to allow.
    subnetpool:
        description: Number of subnet pools to allow.
    volumes:
        description: Number of volumes to allow.
    volumes_lvm:
        description: Number of LVM volumes to allow.
    availability_zone:
      description:
        - Ignored. Present for backwards compatibility


requirements:
    - "python >= 2.7"
    - "openstacksdk >= 0.13.0"
'''

EXAMPLES = '''
# List a Project Quota
- os_quota:
    cloud: mycloud
    name: demoproject

# Set a Project back to the defaults
- os_quota:
    cloud: mycloud
    name: demoproject
    state: absent

# Update a Project Quota for cores
- os_quota:
    cloud: mycloud
    name: demoproject
    cores: 100

# Update a Project Quota
- os_quota:
    name: demoproject
    cores: 1000
    volumes: 20
    volumes_type:
      - volume_lvm: 10

# Complete example based on list of projects
- name: Update quotas
  os_quota:
    name: "{{ item.name }}"
    backup_gigabytes: "{{ item.backup_gigabytes }}"
    backups: "{{ item.backups }}"
    cores: "{{ item.cores }}"
    fixed_ips: "{{ item.fixed_ips }}"
    floating_ips: "{{ item.floating_ips }}"
    floatingip: "{{ item.floatingip }}"
    gigabytes: "{{ item.gigabytes }}"
    injected_file_size: "{{ item.injected_file_size }}"
    injected_files: "{{ item.injected_files }}"
    injected_path_size: "{{ item.injected_path_size }}"
    instances: "{{ item.instances }}"
    key_pairs: "{{ item.key_pairs }}"
    loadbalancer: "{{ item.loadbalancer }}"
    per_volume_gigabytes: "{{ item.per_volume_gigabytes }}"
    pool: "{{ item.pool }}"
    port: "{{ item.port }}"
    properties: "{{ item.properties }}"
    ram: "{{ item.ram }}"
    security_group_rule: "{{ item.security_group_rule }}"
    security_group: "{{ item.security_group }}"
    server_group_members: "{{ item.server_group_members }}"
    server_groups: "{{ item.server_groups }}"
    snapshots: "{{ item.snapshots }}"
    volumes: "{{ item.volumes }}"
    volumes_types:
      volumes_lvm: "{{ item.volumes_lvm }}"
    snapshots_types:
      snapshots_lvm: "{{ item.snapshots_lvm }}"
    gigabytes_types:
      gigabytes_lvm: "{{ item.gigabytes_lvm }}"
  with_items:
    - "{{ projects }}"
  when: item.state == "present"
'''

RETURN = '''
openstack_quotas:
    description: Dictionary describing the project quota.
    returned: Regardless if changes where made or not
    type: complex
    contains:
        openstack_quotas: {
            compute: {
                cores: 150,
                fixed_ips: -1,
                floating_ips: 10,
                injected_file_content_bytes: 10240,
                injected_file_path_bytes: 255,
                injected_files: 5,
                instances: 100,
                key_pairs: 100,
                metadata_items: 128,
                ram: 153600,
                security_group_rules: 20,
                security_groups: 10,
                server_group_members: 10,
                server_groups: 10
            },
            network: {
                floatingip: 50,
                loadbalancer: 10,
                network: 10,
                pool: 10,
                port: 160,
                rbac_policy: 10,
                router: 10,
                security_group: 10,
                security_group_rule: 100,
                subnet: 10,
                subnetpool: -1
            },
            volume: {
                backup_gigabytes: 1000,
                backups: 10,
                gigabytes: 1000,
                gigabytes_lvm: -1,
                per_volume_gigabytes: -1,
                snapshots: 10,
                snapshots_lvm: -1,
                volumes: 10,
                volumes_lvm: -1
            }
        }

'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def _get_volume_quotas(cloud, project):

    return cloud.get_volume_quotas(project)


def _get_network_quotas(cloud, project):

    return cloud.get_network_quotas(project)


def _get_compute_quotas(cloud, project):

    return cloud.get_compute_quotas(project)


def _get_quotas(sdk, module, cloud, project):

    quota = {}
    try:
        quota['volume'] = _get_volume_quotas(cloud, project)
    except sdk.exceptions.NotFoundException:
        module.warn("No public endpoint for volumev2 service was found. Ignoring volume quotas.")

    try:
        quota['network'] = _get_network_quotas(cloud, project)
    except sdk.exceptions.NotFoundException:
        module.warn("No public endpoint for network service was found. Ignoring network quotas.")

    quota['compute'] = _get_compute_quotas(cloud, project)

    for quota_type in quota.keys():
        quota[quota_type] = _scrub_results(quota[quota_type])

    return quota


def _scrub_results(quota):

    filter_attr = [
        'HUMAN_ID',
        'NAME_ATTR',
        'human_id',
        'request_ids',
        'x_openstack_request_ids',
    ]

    for attr in filter_attr:
        if attr in quota:
            del quota[attr]

    return quota


def _system_state_change_details(module, project_quota_output):

    quota_change_request = {}
    changes_required = False

    for quota_type in project_quota_output.keys():
        for quota_option in project_quota_output[quota_type].keys():
            if quota_option in module.params and module.params[quota_option] is not None:
                if project_quota_output[quota_type][quota_option] != module.params[quota_option]:
                    changes_required = True

                    if quota_type not in quota_change_request:
                        quota_change_request[quota_type] = {}

                    quota_change_request[quota_type][quota_option] = module.params[quota_option]

    return (changes_required, quota_change_request)


def _system_state_change(module, project_quota_output):
    """
    Determine if changes are required to the current project quota.

    This is done by comparing the current project_quota_output against
    the desired quota settings set on the module params.
    """

    changes_required, quota_change_request = _system_state_change_details(
        module,
        project_quota_output
    )

    if changes_required:
        return True
    else:
        return False


def main():

    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        state=dict(default='present', choices=['absent', 'present']),
        backup_gigabytes=dict(required=False, type='int', default=None),
        backups=dict(required=False, type='int', default=None),
        cores=dict(required=False, type='int', default=None),
        fixed_ips=dict(required=False, type='int', default=None),
        floating_ips=dict(required=False, type='int', default=None, aliases=['compute_floating_ips']),
        floatingip=dict(required=False, type='int', default=None, aliases=['network_floating_ips']),
        gigabytes=dict(required=False, type='int', default=None),
        gigabytes_types=dict(required=False, type='dict', default={}),
        injected_file_size=dict(required=False, type='int', default=None),
        injected_files=dict(required=False, type='int', default=None),
        injected_path_size=dict(required=False, type='int', default=None),
        instances=dict(required=False, type='int', default=None),
        key_pairs=dict(required=False, type='int', default=None),
        loadbalancer=dict(required=False, type='int', default=None),
        network=dict(required=False, type='int', default=None),
        per_volume_gigabytes=dict(required=False, type='int', default=None),
        pool=dict(required=False, type='int', default=None),
        port=dict(required=False, type='int', default=None),
        project=dict(required=False, type='int', default=None),
        properties=dict(required=False, type='int', default=None),
        ram=dict(required=False, type='int', default=None),
        rbac_policy=dict(required=False, type='int', default=None),
        router=dict(required=False, type='int', default=None),
        security_group_rule=dict(required=False, type='int', default=None),
        security_group=dict(required=False, type='int', default=None),
        server_group_members=dict(required=False, type='int', default=None),
        server_groups=dict(required=False, type='int', default=None),
        snapshots=dict(required=False, type='int', default=None),
        snapshots_types=dict(required=False, type='dict', default={}),
        subnet=dict(required=False, type='int', default=None),
        subnetpool=dict(required=False, type='int', default=None),
        volumes=dict(required=False, type='int', default=None),
        volumes_types=dict(required=False, type='dict', default={})
    )

    module = AnsibleModule(argument_spec,
                           supports_check_mode=True
                           )

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        cloud_params = dict(module.params)

        # In order to handle the different volume types we update module params after.
        dynamic_types = [
            'gigabytes_types',
            'snapshots_types',
            'volumes_types',
        ]

        for dynamic_type in dynamic_types:
            for k, v in module.params[dynamic_type].items():
                module.params[k] = int(v)

        # Get current quota values
        project_quota_output = _get_quotas(
            sdk, module, cloud, cloud_params['name'])
        changes_required = False

        if module.params['state'] == "absent":
            # If a quota state is set to absent we should assume there will be changes.
            # The default quota values are not accessible so we can not determine if
            # no changes will occur or not.
            if module.check_mode:
                module.exit_json(changed=True)

            # Calling delete_network_quotas when a quota has not been set results
            # in an error, according to the sdk docs it should return the
            # current quota.
            # The following error string is returned:
            # network client call failed: Quota for tenant 69dd91d217e949f1a0b35a4b901741dc could not be found.
            neutron_msg1 = "network client call failed: Quota for tenant"
            neutron_msg2 = "could not be found"

            for quota_type in project_quota_output.keys():
                quota_call = getattr(cloud, 'delete_%s_quotas' % (quota_type))
                try:
                    quota_call(cloud_params['name'])
                except sdk.exceptions.OpenStackCloudException as e:
                    error_msg = str(e)
                    if error_msg.find(neutron_msg1) > -1 and error_msg.find(neutron_msg2) > -1:
                        pass
                    else:
                        module.fail_json(msg=str(e), extra_data=e.extra_data)

            project_quota_output = _get_quotas(
                sdk, module, cloud, cloud_params['name'])
            changes_required = True

        elif module.params['state'] == "present":
            if module.check_mode:
                module.exit_json(changed=_system_state_change(module, project_quota_output))

            changes_required, quota_change_request = _system_state_change_details(
                module,
                project_quota_output
            )

            if changes_required:
                for quota_type in quota_change_request.keys():
                    quota_call = getattr(cloud, 'set_%s_quotas' % (quota_type))
                    quota_call(cloud_params['name'], **quota_change_request[quota_type])

                # Get quota state post changes for validation
                project_quota_update = _get_quotas(
                    sdk, module, cloud, cloud_params['name'])

                if project_quota_output == project_quota_update:
                    module.fail_json(msg='Could not apply quota update')

                project_quota_output = project_quota_update

        module.exit_json(changed=changes_required,
                         openstack_quotas=project_quota_output
                         )

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)


if __name__ == '__main__':
    main()
