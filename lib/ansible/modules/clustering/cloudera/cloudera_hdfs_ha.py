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
module: cloudera_hdfs_ha
author: "Serghei Anicheev (@sanicheev) <serghei.anicheev@gmail.com>"
version_added: '2.2.0.2'
short_description: Cloudera Manager enable HA for HDFS.
description:
    - This module will enable HA for HDFS. Please take in consideration that ZOOKEEPER service should be up and running!
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
            - Cloudera cluster name to search for HDFS service type in.
        required: true
    active_role_name:
        description:
            - Role name of currently existing NAMENODE type.
        required: true
    standby_host_role_type:
        description:
            - Role type in HDFS service. It will be used to find host ID where this role has been applied. Default is SECONDARYNAMENODE.
        required: false
        default: SECONDARYNAMENODE
    nameservice:
        description:
            - Nameservice for HDFS HA
        required: false
        default: HDFS-HA-NAMESERVICE
    jns:
        description:
            - Journal node list.
              'journal_role_name' - role name which will be used when creating JOURNALNODE role type on specific host.
              'host' is a hostname where journal role will be applied. This 'host' MUST BE in cluster.
        required: true
    standby_role_name:
        description:
            - Role name to use for NAMENODE-STANDBY role type.
        required: false
        default: NAMENODE-STANDBY
    state:
        description:
            - Enable HDFS HA state.
        required: false
        default: 'enable_hdfs_ha'
        choices: ['enable_hdfs_ha']
'''

EXAMPLES = '''
# Enable HDFS HA
- name: Enable HDFS HA
  cloudera_hdfs_ha:
    host: 123.123.123.123
    port: 7180
    username: admin
    password: admin
    cluster_name: MyCluster
    active_role_name: "NAMENODE"
    standby_host_role_type: "SECONDARYNAMENODE"
    nameservice: "HDFS-HA-NAMESERVICE"
    jns:
      - { 'journal_role_name': 'JOURNALNODE1', 'host': "123.123.123.124" }
      - { 'journal_role_name': 'JOURNALNODE2', 'host': "123.123.123.125" }
      - { 'journal_role_name': 'JOURNALNODE3', 'host': "123.123.123.126" }
    standby_role_name: "NAMENODE-STANDBY"
    state: "enable_hdfs_ha"
'''
def compose_journal_nodes_info(cloudera, connection, jns):
    journal_nodes_info = []
    for journal_node in jns:
        host_id = cloudera.get_hostid_by_hostname(connection, journal_node['host'])
        entry = { 'jnHostId': host_id, 'jnName': journal_node['journal_role_name'] }
        journal_nodes_info.append(entry)
    return journal_nodes_info

def enable_hdfs_ha(cloudera, connection, cluster_name, active_role_name, standby_host_role_type, nameservice, jns, standby_role_name):
    cluster = connection.get_cluster(cluster_name)
    service = cloudera.get_service_by_type(cluster, 'HDFS')
    standby_host_id = cloudera.get_hostid_by_role_type(service, standby_host_role_type)[0]
    zookeeper_service_name = cloudera.get_service_by_type(cluster, 'ZOOKEEPER').name
    journal_nodes_info = compose_journal_nodes_info(cloudera, connection, jns)
    service.enable_nn_ha(
        active_name=active_role_name, standby_host_id=standby_host_id, nameservice=nameservice, jns=journal_nodes_info,
        standby_name=standby_role_name, zk_service_name=zookeeper_service_name
    ).wait()
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
            active_role_name=dict(default='NAMENODE', type='str'),
            standby_host_role_type=dict(default='SECONDARYNAMENODE', type='str'),
            nameservice=dict(default='HDFS-HA-NAMESERVICE', type='str'),
            jns=dict(default=None, type='list'),
            standby_role_name=dict(default='NAMENODE-STANDBY', type='str'),
            state=dict(default='enable_hdfs_ha', choices=['enable_hdfs_ha'])
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
    active_role_name = module.params['active_role_name']
    standby_host_role_type = module.params['standby_host_role_type']
    nameservice = module.params['nameservice']
    jns = module.params['jns']
    standby_role_name = module.params['standby_role_name']
    state = module.params['state']
    changed=False

    cloudera = Cloudera(module, host, port, username, password, api_version, use_tls)
    connection = cloudera.connect()

    if module.check_mode:
        module.exit_json(changed=True)

    if state == 'enable_hdfs_ha':
        changed = enable_hdfs_ha(cloudera, connection, cluster_name, active_role_name, standby_host_role_type, nameservice, jns, standby_role_name)

    module.exit_json(changed=changed)

if __name__ == '__main__':
    from ansible.module_utils.basic import *
    from ansible.module_utils.cloudera import *
    main()
