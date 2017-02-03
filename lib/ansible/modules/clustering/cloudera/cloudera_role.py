#!/usr/bin/python
#
# (c) 2017, Serghei Anicheev <serghei.anicheev@gmail.com>
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


DOCUMENTATION = '''
---
module: cloudera_role
author: "Serghei Anicheev (@sanicheev) <serghei.anicheev@gmail.com>"
version_added: '2.2.0.2'
short_description: Cloudera Manager role.
description:
    - This module can create and configure Cloudera Manager role or update role_config_group.
options:
    host:
        description:
            - Cloudera Manager API host.
        required: true
    port:
        description:
            - Cloudera Manager API port.
        required: false
        default: 7180
    username:
        description:
            - Username to connect to Cloudera Manager API.
        required: false
        default: admin
    password:
        description:
            - Password to connect to Cloudera Manager API.
        required: false
        default: admin
    api_version:
        description:
            - Cloudera API version(Older API versions cannot use calls like 'configure_for_kerberos' for example).
        required: false
        default: 12
    use_tls:
        description:
            - Enable TLS(In this case port 7183 should be used!).
        required: false
        default: false
    cluster_name:
        description:
            - Cloudera cluster name to create service in. This parameter should be present for non-mgmt role types.
        default: MyCluster    .
        required: false
    service_type:
        description:
            - Service type to create role in.
        required: false
        default: MGMT        
    role_type:
        description:
            - Role type to create or search role_config_group in.
        required: true
    role_name:
        description:
            - Role name to create. This should be present for state: 'create'.
        required: false    
    role_host:    
        description:
            - Host(hostname as listed in cluster) to apply role on.
        required: false    
    configuration_file:
        description:
            - Path to the configuration file to use for the desired role. Should be in JSON format only!. If configuration file is inaccessible warning message will be shown.
        required: false
    state:
        description:
            - Action to apply on desired role_type.
        required: false
        default: 'create'
        choices: ['create', 'update_role_group']        
'''

EXAMPLES = '''
# Create ACTIVITYMONITOR role and configure it.
- name: Create ACTIVITYMONITOR role
  cloudera_role:
    host: 123.123.123.123
    username: admin
    password: admin
    service_type: MGMT
    role_name: ACTIVITYMONITOR
    role_type: ACTIVITYMONITOR
    role_host: 123.123.123.124
    configuration_file: 'activitymonitor.conf'
    state: create

# Create RESOURCEMANAGER role
- name: Create RESOURCEMANAGER role
  cloudera_role:
    host: 123.123.123.123
    username: admin
    password: admin
    cluster_name: MyCluster
    service_type: YARN
    role_name: RESOURCEMANAGER
    role_type: RESOURCEMANAGER
    role_host: 123.123.123.125
    state: create

# Update JOURNALNODE role_config_group
- name: Update JOURNALNODE role_config_group
  cloudera_role:
    host: 123.123.123.123
    username: admin
    password: admin
    cluster_name: MyCluster
    service_type: HDFS
    role_type: JOURNALNODE
    configuration_file: 'journalnode.conf'
    state: update_role_group
'''

def create_role(module, cloudera, service_obj, role_name, role_type, role_host, configuration_file):
    cloudera.validate_role_type(service_obj, role_type)
    role_changed = False
    configuration_changed = False
    role = filter(lambda role: role.name == role_name, service_obj.get_all_roles())
    if len(role) != 0:
        module.log('Role with name - %s already exists' % role_name)
    else:
        service_obj.create_role(role_name, role_type, role_host)
        role_changed = True
        configuration_changed = update_role_config_group(cloudera, service_obj, role_type, configuration_file)
    result = role_changed | configuration_changed
    return result

def update_role_config_group(cloudera, service_obj, role_type, configuration_file):
    configuration_changed = False
    service_name = service_obj.name
    if configuration_file is not None:
        config_group = service_obj.get_role_config_group("{0}-{1}-BASE".format(service_name, role_type))
        current_config = config_group.get_config()
        configuration_changed = cloudera.update_config(config_group, current_config, configuration_file)
    return configuration_changed

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(required=True, type='str'),
            port=dict(default=7180, type='int'),
            username=dict(default='admin', type='str'),
            password=dict(default='admin', no_log=True, type='str'),
            api_version=dict(default=12, type='int'),
            use_tls=dict(default=False, type='bool'),
            cluster_name=dict(default='MyCluster', required=False, type='str'),
            service_type=dict(required=False, type='str', default='MGMT'),
            role_name=dict(required=False, type='str'),
            role_type=dict(required=True, type='str'),
            role_host=dict(required=False, type='str'),
            configuration_file=dict(required=False, type='path'),
            state=dict(default='create', choices=['create', 'update_role_group'])
        ),
        supports_check_mode=True,
    )

    host = module.params['host']
    port = module.params['port']
    username = module.params['username']
    password = module.params['password']
    api_version = module.params['api_version']
    use_tls = module.params['use_tls']
    cluster_name = module.params['cluster_name']
    service_type = module.params['service_type'].upper()
    role_name = module.params['role_name']
    role_type = module.params['role_type'].upper()
    role_host = module.params['role_host']
    configuration_file = module.params['configuration_file']
    state = module.params['state']
    changed=False

    if module.check_mode:
        module.exit_json(changed=True)

    cloudera = Cloudera(module, host, port, username, password, api_version, use_tls)
    connection = cloudera.connect()

    if state == 'create' and service_type == 'MGMT':
        cloudera_manager = cloudera.cloudera_manager(connection)
        service = cloudera_manager.get_service()
        changed = create_role(module, cloudera, service, role_name, role_type, role_host, configuration_file)
    else:
        cluster = cloudera.get_cluster(connection, cluster_name)
        cloudera.validate_service_type(cluster, service_type)
        service = cluster.get_service(service_type)
        if state == 'update_role_group':
            changed = update_role_config_group(cloudera, service, role_type, configuration_file)
        else:
            changed = create_role(module, cloudera, service, role_name, role_type, role_host, configuration_file)

    module.exit_json(changed=changed)

if __name__ == '__main__':
    from ansible.module_utils.basic import *
    from ansible.module_utils.cloudera import *
    main()
