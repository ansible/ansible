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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: cloudera_oozie_ha
author: "Serghei Anicheev (@sanicheev) <serghei.anicheev@gmail.com>"
version_added: '2.2.0.2'
short_description: Cloudera Manager enable HA for OOZIE.
description:
    - This module will enable HA for OOZIE. Please take in consideration that ZOOKEEPER service should be up and running!
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
            - Cloudera cluster name to search for OOZIE service type in.   .
        required: true
    load_balancer_host:
        description:
            - Hostname where secondary Load Balancer will be created. Host MUST BE in cluster!
        required: true
    load_balancer_port:
        description:
            - Port number to use for Load Balancer.
        required: false
        default: 21054
    oozie_hosts:
        description:
            - List of hostnames where additional OOZIE roles will be applied. They MUST be in cluster!
            - 123.123.123.124
            - 123.123.123.125
    state:
        description:
            - Enable OOZIE HA state.
        required: false
        default: 'enable_oozie_ha'
        choices: ['enable_oozie_ha']
'''

EXAMPLES = '''
# Enable OOZIE HA
- name: Enable OOZIE HA
  cloudera_oozie_ha:
    host: 123.123.123.123
    port: 7180
    username: admin
    password: admin
    cluster_name: MyCluster
    load_balancer_host: "123.123.123.124"
    load_balancer_port: 21054
    oozie_hosts:
      - "123.123.123.125"
      - "123.123.123.126"
    state: "enable_oozie_ha"
'''

def enable_oozie_ha(cloudera, connection, cluster_name, load_balancer_host, load_balancer_port, oozie_hosts):
    cluster = connection.get_cluster(cluster_name)
    service = cloudera.get_service_by_type(cluster, 'OOZIE')
    oozie_host_ids = []
    for oozie_host in oozie_hosts:
        host_id = cloudera.get_hostid_by_hostname(connection, oozie_host)
        oozie_host_ids.append(host_id)
    zookeeper_service_name = cloudera.get_service_by_type(cluster, 'ZOOKEEPER').name
    load_balancer_info = "%s:%s" % (load_balancer_host, load_balancer_port)
    service.enable_oozie_ha(new_oozie_server_host_ids=oozie_host_ids, zk_service_name=zookeeper_service_name, load_balancer_host_port=load_balancer_info).wait()
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
            load_balancer_host=dict(required=True, type='str'),
            load_balancer_port=dict(default=21054, type='int'),
            oozie_hosts=dict(required=True, type='list'),
            state=dict(default='enable_oozie_ha', choices=['enable_oozie_ha'])
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
    load_balancer_host = module.params['load_balancer_host']
    load_balancer_port = module.params['load_balancer_port']
    oozie_hosts = module.params['oozie_hosts']
    state = module.params['state']
    changed=False

    cloudera = Cloudera(module, host, port, username, password, api_version, use_tls)
    connection = cloudera.connect()

    if module.check_mode:
        module.exit_json(changed=True)

    elif state == 'enable_oozie_ha':
        changed = enable_oozie_ha(cloudera, connection, cluster_name, load_balancer_host, load_balancer_port, oozie_hosts)

    module.exit_json(changed=changed)

if __name__ == '__main__':
    from ansible.module_utils.basic import *
    from ansible.module_utils.cloudera import *
    main()
