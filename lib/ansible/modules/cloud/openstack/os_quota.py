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
version_added: "2.0"
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
    backups:
        required: False
        default: None
    cores:
        required: False
        default: None
    fixed_ips:
        required: False
        default: None
    floating_ips:
        required: False
        default: None
    gigabytes:
        required: False
        default: None
    gigabytes_lvm:
        required: False
        default: None
    injected_file_size:
        required: False
        default: None
    injected_files:
        required: False
        default: None
    injected_path_size:
        required: False
        default: None
    instances:
        required: False
        default: None
    key_pairs:
        required: False
        default: None
    network:
        required: False
        default: None
    per_volume_gigabytes:
        required: False
        default: None
    port:
        required: False
        default: None
    project:
        required: False
        default: None
    properties:
        required: False
        default: None
    ram:
        required: False
        default: None
    rbac_policy:
        required: False
        default: None
    router:
        required: False
        default: None
    secgroup_rules:
        required: False
        default: None
    secgroups:
        required: False
        default: None
    server_group_members:
        required: False
        default: None
    server_groups:
        required: False
        default: None
    snapshots:
        required: False
        default: None
    snapshots_lvm:
        required: False
        default: None
    subnet:
        required: False
        default: None
    subnetpool:
        required: False
        default: None
    volumes:
        required: False
        default: None
    volumes_lvm:
        required: False
        default: None


requirements:
    - "python >= 2.6"
    - "shade > 1.9.0"
'''


EXAMPLES = '''
# List a Project Quotas
- os_quota:
    cloud: mycloud
    name: demoproject
    cores: 100

# Update a Project Quotas
- os_quota:
    name: demoproject
    cores: 1000
    volumes: 20
    volumes_type:
      - volume_lvm: 10
'''


RETURN = '''
openstack_quotas:
    description: Dictionary describing the quota.
    returned: 
'''


def exit_hostvars(module, cloud, project_quota, changed=True):
    module.exit_json(changed=changed, ansible_facts=dict(
        openstack_quotas=project_quota))

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


    module = AnsibleModule(argument_spec)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    try:
        cloud_params = dict(module.params)
        cloud = shade.operator_cloud(**cloud_params)

        #In order to handle the different volume types we updated module params after.
        dynamic_types = [
            'gigabytes_types',
            'snapshots_types',
            'volumes_types',
        ]

        #import epdb
        #epdb.serve()
        for dynamic_type in dynamic_types:
            for k, v in module.params[dynamic_type].iteritems():
                module.params[k] = int(v)

        #Get current quota values
        project_quota_output = _get_quotas(cloud, cloud_params['name'])

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


        if changes_required:
            for quota_type in quota_change_request.keys():
                quota_call = getattr(cloud, 'set_%s_quotas' % (quota_type))
                quota_call(cloud_params['name'], **quota_change_request[quota_type])

            #Get latest quota state
            project_quota_update = _get_quotas(cloud, cloud_params['name'])

            if project_quota_output == project_quota_update:
                module.fail_json(msg='Could not apply quota update')

            project_quota_output = project_quota_update

        exit_hostvars(module,cloud, project_quota_output, changed=changes_required)
        
    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)


# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
