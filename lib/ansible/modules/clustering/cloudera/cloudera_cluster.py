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
module: cloudera_cluster
author: "Serghei Anicheev (@sanicheev) <serghei.anicheev@gmail.com>"
version_added: '2.2.0.2'
short_description: Manage Cloudera cluster.
description:
    - This module can create/delete Cloudera cluster.
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
    cdh_version:
        description:
            - CDH version to use
        required: false
        default: CDH5
    use_tls:
        description:
            - Enable TLS(In this case port 7183 should be used!).
        required: false
        default: false
    cluster_name:
        description:
            - Cloudera cluster name to use.
        required: true
    state:
        description:
          - The desired action to perform with the cluster.
        required: false
        default: create
        choices: ['create', 'delete']
'''

EXAMPLES = '''
# Create Cloudera cluster
- name: Create Cloudera cluster
  cloudera_cluster:
    host: 123.123.123.123
    username: admin
    password: admin
    cluster_name: MyCluster
    state: create

# Delete Cloudera cluster
- name: Delete Cloudera cluster
  cloudera_cluster:
    host: 123.123.123.123
    username: admin
    password: admin
    cluster_name: MyCluster
    state: delete
'''

def create_cluster(connection, cluster_name, cdh_version):
    connection.create_cluster(cluster_name, version=cdh_version).wait()

def delete_cluster(connection, cluster_name):
    connection.delete_cluster(cluster_name).wait()

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(required=True, type='str'),
            port=dict(default=7180, type='int'),
            username=dict(default='admin', type='str'),
            password=dict(default='admin', no_log=True, type='str'),
            api_version=dict(default=12, type='int'),
            cdh_version=dict(default='CDH5', type='str'),
            use_tls=dict(default=False, type='bool'),
            cluster_name=dict(required=True, type='str'),
            state=dict(default='create', choices=['create', 'delete'])
        ),
        supports_check_mode=True
    )

    host = module.params['host']
    port = module.params['port']
    username = module.params['username']
    password = module.params['password']
    api_version = module.params['api_version']
    cdh_version = module.params['cdh_version']
    use_tls = module.params['use_tls']
    cluster_name = module.params['cluster_name']
    state = module.params['state']
    changed=False

    if module.check_mode:
        module.exit_json(changed=True)

    cloudera = Cloudera(module, host, port, username, password, api_version, use_tls)
    connection = cloudera.connect()
    cluster = cloudera.get_cluster(connection, cluster_name)

    if state == 'create':
        if cluster:
            module.log('Cluster with name - %s already exists! Nothing to do!' % cluster_name)
            changed = False
        else:
            create_cluster(connection, cluster_name, cdh_version)
            changed = True
    elif state == 'delete':
        if cluster:
            delete_cluster(connection, cluster_name).wait()
            changed = True
        else:
            module.log('Cluster with name - %s does not exists! Nothing to do!' % cluster_name)
            changed = False

    module.exit_json(changed=changed)

if __name__ == '__main__':
    from ansible.module_utils.basic import *
    from ansible.module_utils.cloudera import *
    main()
