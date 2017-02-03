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
module: cloudera_service
author: "Serghei Anicheev (@sanicheev) <serghei.anicheev@gmail.com>"
version_added: '2.2.0.2'
short_description: Cloudera Manager service.
description:
    - This module can create and configure Cloudera Manager role.
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
            - Cloudera cluster name to create service in. This parameter should be present for non-mgmt service types.
        default: MyCluster    .
        required: false
    service_type:
        description:
            - Service type to create.
        required: true
    configuration_file:
        description:
            - Path to the configuration file to use for the desired service. Should be in JSON format only!.
            - If configuration file is inaccessible warning message will be shown.
        required: false
    state:
        description:
            - Action to apply on desired service_type.
        required: false
        default: 'create'
        choices: ['create']
'''

EXAMPLES = '''
# Create Cloudera management service and configure it.
- name: Create MGMT service
  cloudera_service:
    host: 123.123.123.123
    username: admin
    password: admin
    service_type: MGMT
    configuration_file: 'service.conf'
    state: create

# Create Zookeeper service and configure i
- name: Create Zookeeper service
  cloudera_service:
    host: 123.123.123.123
    username: admin
    password: admin
    cluster_name: MyCluster
    service_type: ZOOKEEPER
    configuration_file: 'service.conf'
    state: create
'''

def create_mgmt_service(cloudera, connection, service_type, configuration_file):
    cloudera_manager = cloudera.cloudera_manager(connection)
    service_changed = False
    configuration_changed = False
    if configuration_file is not None:
        current_config = cloudera_manager.get_config()
        configuration_changed = cloudera.update_config(cloudera_manager, current_config, configuration_file)
    try:
        cloudera_manager.get_service()
    except:
        service_info = cloudera.get_service_setup_info(service_type, service_type)
        cloudera_manager.create_mgmt_service(service_info)
        service_changed = True
    result = service_changed | configuration_changed
    return resul

def create_general_service(cloudera, connection, cluster_name, service_type, configuration_file):
    cluster = cloudera.get_cluster(connection, cluster_name)
    cloudera.validate_service_type(cluster, service_type)
    if cluster is None:
        raise Exception('No cluster found with name - %s' % cluster_name)
    service_changed = False
    configuration_changed = False
    try:
        cluster.get_service(service_type)
    except:
        cluster.create_service(service_type, service_type)
        service_changed = True
    if configuration_file is not None:
        service = cluster.get_service(service_type)
        current_config = service.get_config()[0]
        configuration_changed = cloudera.update_config(service, current_config, configuration_file)
    result = service_changed | configuration_changed
    return resul

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
            service_type=dict(required=True, type='str'),
            configuration_file=dict(required=False, default=None, type='path'),
            state=dict(default='create', choices=['create'])
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
    configuration_file = module.params['configuration_file']
    state = module.params['state']
    changed=False

    if module.check_mode:
        module.exit_json(changed=True)

    cloudera = Cloudera(module, host, port, username, password, api_version, use_tls)
    connection = cloudera.connect()

    if state == 'create':
        if service_type == 'MGMT':
            changed = create_mgmt_service(cloudera, connection, service_type, configuration_file)
        else:
            changed = create_general_service(cloudera, connection, cluster_name, service_type, configuration_file)

    module.exit_json(changed=changed)

if __name__ == '__main__':
    from ansible.module_utils.basic import *
    from ansible.module_utils.cloudera import *
    main()
