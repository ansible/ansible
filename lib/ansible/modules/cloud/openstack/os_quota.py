#!/usr/bin/python
# Copyright (c) 2016 Pason System Corporation
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

import sys

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False


DOCUMENTATION = '''
---
module: os_quota
short_description: Manage OpenStack Quotas
extends_documentation_fragment: openstack
version_added: "2.3"
author: "Michael Gale (gale.michael@gmail.com)"
description:
    - Manage OpenStack Quotas. Quotas can be created,
      updated or deleted using this module. A auota will be updated
      if matches an existing project and is present.
options:
    name:
        description:
            - Name for the project
        required: true
    backup_gigabytes:
        required: False
        default: None
        description: Maximum size of backups
    backups:
        required: False
        default: None
        description: Max number of backups allows
    cores:
        required: False
        default: None
        description: Max number of CPU's per project
    fixed_ips:
        required: False
        default: None
        description: Number of fixed IP's to allow
    floating_ips:
        required: False
        default: None
        description: Number of floating IP's to allow
    gigabytes:
        required: False
        default: None
        description: Max volume storage for project
    gigabytes_lvm:
        required: False
        default: None
        description: Max size of individual lvm volumes
    injected_file_size:
        required: False
        default: None
        description: Max file size
    injected_files:
        required: False
        default: None
        description: Number of injected files to allow
    injected_path_size:
        required: False
        default: None
        description: Max file size
    instances:
        required: False
        default: None
        description: Maximum number of instances
    key_pairs:
        required: False
        default: None
        description: Number of key pairs to allow
    network:
        required: False
        default: None
        description: Number of networks to allow
    per_volume_gigabytes:
        required: False
        default: None
        description: Max size of individual volumes
    port:
        required: False
        default: None
        description: Number of Network ports to allow, should be greater than instances.
    project:
        required: False
        default: None
        description: Project name
    properties:
        required: False
        default: None
        description: Number of properties to allow
    ram:
        required: False
        default: None
        description: Maximum amount of ram
    rbac_policy:
        required: False
        default: None
        description: Number of polcies to allow
    router:
        required: False
        default: None
        description: Number of routers to allow
    secgroup_rules:
        required: False
        default: None
        description: Number of rules per security group to allow
    secgroups:
        required: False
        default: None
        description: Number of security groups to allow
    server_group_members:
        required: False
        default: None
        description: Number of server group members to allow
    server_groups:
        required: False
        default: None
        description: Number of server groups to allow
    snapshots:
        required: False
        default: None
        description: Number of snapshots to allow
    snapshots_lvm:
        required: False
        default: None
        description: Number of LVM snapshots to allow
    subnet:
        required: False
        default: None
        description: Number of subnets to allow
    subnetpool:
        required: False
        default: None
        description: Number of subnet pools to allow
    volumes:
        required: False
        default: None
        description: Number of volumes to allow
    volumes_lvm:
        required: False
        default: None
        description: Number of LVM volumes to allow


requirements:
    - "python >= 2.6"
    - "shade > 1.9.0"
'''

EXAMPLES = '''
# List a Project Quota
- os_quota:
    cloud: mycloud
    name: demoproject

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
    gigabytes: "{{ item.gigabytes }}"
    injected_file_size: "{{ item.injected_file_size }}"
    injected_files: "{{ item.injected_files }}"
    injected_path_size: "{{ item.injected_path_size }}"
    instances: "{{ item.instances }}"
    port: "{{ item.port }}"
    key_pairs: "{{ item.key_pairs }}"
    per_volume_gigabytes: "{{ item.per_volume_gigabytes }}"
    properties: "{{ item.properties }}"
    ram: "{{ item.ram }}"
    secgroup_rules: "{{ item.secgroup_rules }}"
    secgroups: "{{ item.secgroups }}"
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
    returned: Regardless if changes where made or note
    type: dictionary
    contains example:
    "openstack_quotas": {
        "compute": {
            "cores": 150,
            "fixed_ips": -1,
            "floating_ips": 10,
            "injected_file_content_bytes": 10240,
            "injected_file_path_bytes": 255,
            "injected_files": 5,
            "instances": 100,
            "key_pairs": 100,
            "metadata_items": 128,
            "ram": 153600,
            "security_group_rules": 20,
            "security_groups": 10,
            "server_group_members": 10,
            "server_groups": 10
        },
        "network": {
            "floatingip": 50,
            "network": 10,
            "port": 160,
            "rbac_policy": 10,
            "router": 10,
            "security_group": 10,
            "security_group_rule": 100,
            "subnet": 10,
            "subnetpool": -1
        },
        "volume": {
            "backup_gigabytes": 1000,
            "backups": 10,
            "gigabytes": 1000,
            "gigabytes_lvm": -1,
            "per_volume_gigabytes": -1,
            "snapshots": 10,
            "snapshots_lvm": -1,
            "volumes": 10,
            "volumes_lvm": -1
        }
    }

'''

def _get_volume_quotas(cloud, project):

    return cloud.get_volume_quotas(project)

def _get_network_quotas(cloud, project):

    return cloud.get_network_quotas(project)

def _get_compute_quotas(cloud, project):

    return cloud.get_compute_quotas(project)

def _get_quotas(cloud, project):

    quota = {}
    quota['volume'] = _get_volume_quotas(cloud, project)
    quota['network'] = _get_network_quotas(cloud, project)
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
        backup_gigabytes=dict(required=False, type='int', default=None),
        backups=dict(required=False, type='int', default=None),
        cores=dict(required=False, type='int', default=None),
        fixed_ips=dict(required=False, type='int', default=None),
        floating_ips=dict(required=False, type='int', default=None),
        gigabytes=dict(required=False, type='int', default=None),
        gigabytes_types=dict(required=False, type='dict', default={}),
        injected_file_size=dict(required=False, type='int', default=None),
        injected_files=dict(required=False, type='int', default=None),
        injected_path_size=dict(required=False, type='int', default=None),
        instances=dict(required=False, type='int', default=None),
        key_pairs=dict(required=False, type='int', default=None),
        network=dict(required=False, type='int', default=None),
        per_volume_gigabytes=dict(required=False, type='int', default=None),
        port=dict(required=False, type='int', default=None),
        project=dict(required=False, type='int', default=None),
        properties=dict(required=False, type='int', default=None),
        ram=dict(required=False, type='int', default=None),
        rbac_policy=dict(required=False, type='int', default=None),
        router=dict(required=False, type='int', default=None),
        secgroup_rules=dict(required=False, type='int', default=None),
        secgroups=dict(required=False, type='int', default=None),
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

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    try:
        cloud_params = dict(module.params)
        cloud = shade.operator_cloud(**cloud_params)

        #In order to handle the different volume types we update module params after.
        dynamic_types = [
            'gigabytes_types',
            'snapshots_types',
            'volumes_types',
        ]

        for dynamic_type in dynamic_types:
            for k, v in module.params[dynamic_type].iteritems():
                module.params[k] = int(v)

        #Get current quota values
        project_quota_output = _get_quotas(cloud, cloud_params['name'])

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

            #Get quota state post changes for validation
            project_quota_update = _get_quotas(cloud, cloud_params['name'])

            if project_quota_output == project_quota_update:
                module.fail_json(msg='Could not apply quota update')

            project_quota_output = project_quota_update

        module.exit_json(changed=changes_required,
            openstack_quotas=project_quota_output
        )

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
