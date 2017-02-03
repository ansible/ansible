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
module: cloudera_kerberos
author: "Serghei Anicheev (@sanicheev) <serghei.anicheev@gmail.com>"
version_added: '2.2.0.2'
short_description: Cloudera Manager configure kerberos.
description:
    - This module is used to configure all services to use kerberos.
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
            - Cloudera cluster name to kerberize services in.
        default: MyCluster    .
        required: false
    kdc_user:
        description:
            - Username to use during generation of admin principal
        required: false
        default: Administrator
    kdc_password:
        description:
            - Password to use during generation of admin principal
        required: true
    state:
        description:
            - Kerberize services in cluster.
        required: false
        default: 'kerberize'
        choices: ['kerberize']
'''

EXAMPLES = '''
# Prepare all services in cluster for kerberos
- name: Kerberize all services in the cluster
  cloudera_kerberos:
    host: 123.123.123.123
    username: admin
    password: admin
    cluster_name: MyCluster
    kdc_user: Administrator@MY.REALM
    kdc_password: secre
    state: "kerberize"
'''

def kerberize(cloudera, connection, cluster_name, kdc_user, kdc_password):
    cluster = connection.get_cluster(cluster_name)
    cloudera_manager = connection.get_cloudera_manager()
    cloudera_manager_service = cloudera_manager.get_service()
    cluster.stop().wait()
    cloudera_manager_service.stop().wait()
    cloudera_manager.import_admin_credentials(kdc_user, kdc_password).wait()
    cluster.configure_for_kerberos().wait()
    cluster.deploy_client_config().wait()
    cluster.deploy_cluster_client_config().wait()
    cloudera_manager_service.start().wait()
    cluster.start().wait()
    return True

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(required=True, type='str'),
            port=dict(default=7180, type='int'),
            username=dict(default='admin', type='str'),
            password=dict(default='admin', no_log=True, type='str'),
            api_version=dict(default=12, type='int'),
            use_tls=dict(default=False, type='bool'),
            cluster_name=dict(required=True, type='str'),
            kdc_user=dict(default='Administrator', required=False, type='str'),
            kdc_password=dict(required=True, no_log=True, type='str'),
            state=dict(default='kerberize', choices=['kerberize'])
        ),
        supports_check_mode=True
    )

    host = module.params['host']
    port = module.params['port']
    username = module.params['username']
    password = module.params['password']
    api_version = module.params['api_version']
    use_tls = module.params['use_tls']
    cluster_name = module.params['cluster_name']
    kdc_user = module.params['kdc_user']
    kdc_password = module.params['kdc_password']
    state = module.params['state']
    changed=False

    if module.check_mode:
        module.exit_json(changed=True)

    cloudera = Cloudera(module, host, port, username, password, api_version, use_tls)
    connection = cloudera.connect()

    if state == 'kerberize':
        changed = kerberize(cloudera, connection, cluster_name, kdc_user, kdc_password)

    module.exit_json(changed=changed)

if __name__ == '__main__':
    from ansible.module_utils.basic import *
    from ansible.module_utils.cloudera import *
    main()
