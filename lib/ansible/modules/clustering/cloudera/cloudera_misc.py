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
module: cloudera_misc
author: "Serghei Anicheev (@sanicheev) <serghei.anicheev@gmail.com>"
version_added: '2.2.0.2'
short_description: Cloudera Manager miscellaneous.
description:
    - This module can be used to run post actions for service before first run such as - 'create_sentry_database, create_yarn_job_history_dir'
      or stop,start services or re-deploy service configuration.
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
            - Cloudera cluster name to use.
        default: MyCluster
        required: false
    service_type:
        description:
            - Service type to run desired miscellaneous action.
        required: true
    force:
        description:
            - Enable this if you would like to skip service status check before running stop or start action on desired service type.
        required: false
        default: false
    state:
        description:
            - Action to apply on desired service_type.
        required: false
        default: 'start'
        choices: [ 'start', 'stop', 'restart', 'init_zk', 'init_hive', 'init_impala', 'init_sqoop', 'init_hbase',
        'init_solr', 'init_yarn', 'init_sentry', 'deploy_service_config', 'init_oozie', 'init_hdfs']
'''

EXAMPLES = '''
# Start MGMT service.
- name: Start MGMT service
  cloudera_misc:
    host: 123.123.123.123
    port: 7180
    username: admin
    password: admin
    service_type: "MGMT"
    state: "start"

# Run required action on HDFS service type before first star
- name: Init HDFS
  cloudera_misc:
    host: 123.123.123.123
    port: 7180
    username: admin
    password: admin
    cluster_name: MyCluster
    service_type: "HDFS"
    state: "init_hdfs"

# Start HDFS service and skipping any service status checks
- name: Start HDFS service
  cloudera_misc:
    host: 123.123.123.123
    username: admin
    password: admin
    cluster_name: MyCluster
    service_type: "HDFS"
    force: true
    state: "start"

# Run required action on ZOOKEEPER service type before first star
 - name: Init ZOOKEEPER
  cloudera_misc:
    host: 123.123.123.123
    port: 7180
    username: admin
    password: admin
    cluster_name: MyCluster
    service_type: "ZOOKEEPER"
    state: "init_zk"

# Re-Deploy service configuration for SENTRY service type.
 - name: Re-Deploy SENTRY service configuration
  cloudera_misc:
    host: 123.123.123.123
    port: 7180
    username: admin
    password: admin
    cluster_name: MyCluster
    service_type: "SENTRY"
    state: "deploy_service_config"
'''
import time

def process_service(service_obj, force, action):
    state = service_obj.serviceState
    changed = False
    if state == 'STARTED' and action == 'start' and not force:
        pass
    elif state == 'STOPPED' and action == 'stop' and not force:
        pass
    else:
        eval("service_obj.{0}().wait()".format(action))
        changed = True
    return changed

def get_svc(cloudera, connection, cluster_name, service_type):
    cluster = connection.get_cluster(cluster_name)
    service = cloudera.get_service_by_type(cluster, service_type)
    return service

def service_control(cloudera, connection, cluster_name, service_type, force, action='start'):
    changed = False
    if service_type == 'MGMT':
        cloudera_manager = cloudera.cloudera_manager(connection)
        mgmt_service = cloudera_manager.get_service()
        changed = process_service(mgmt_service, force, action)
    else:
        cluster = connection.get_cluster(cluster_name)
        if service_type:
            service = cloudera.get_service_by_type(cluster, service_type)
            changed = process_service(service, force, action)
        else:
            eval("cluster.{0}().wait()".format(action))
            changed = True
    return changed

def init_zk(cloudera, connection, cluster_name, service_type):
    service = get_svc(cloudera, connection, cluster_name, service_type)
    service.init_zookeeper().wait()
    return True

def deploy_service_config(cloudera, connection, cluster_name, service_type):
    service = get_svc(cloudera, connection, cluster_name, service_type)
    changed = False
    if service.clientConfigStalenessStatus != 'FRESH':
        service.deploy_client_config().wait()
        changed = True
    return changed

def init_hive(cloudera, connection, cluster_name, service_type):
    service = get_svc(cloudera, connection, cluster_name, service_type)
    service.create_hive_metastore_database().wait()
    service.create_hive_metastore_tables().wait()
    service.create_hive_warehouse().wait()
    return True

def init_impala(cloudera, connection, cluster_name, service_type):
    service = get_svc(cloudera, connection, cluster_name, service_type)
    service.create_impala_catalog_database_tables().wait()
    service.create_impala_user_dir().wait()
    return True

def init_sqoop(cloudera, connection, cluster_name, service_type):
    service = get_svc(cloudera, connection, cluster_name, service_type)
    service.create_sqoop_database_tables().wait()
    service.create_sqoop_user_dir().wait()
    return True

def init_hbase(cloudera, connection, cluster_name, service_type):
    service = get_svc(cloudera, connection, cluster_name, service_type)
    service.create_hbase_root().wait()
    return True

def init_solr(cloudera, connection, cluster_name, service_type):
    service = get_svc(cloudera, connection, cluster_name, service_type)
    service.init_solr().wait()
    service.create_solr_hdfs_home_dir().wait()
    return True

def init_yarn(cloudera, connection, cluster_name, service_type):
    service = get_svc(cloudera, connection, cluster_name, service_type)
    service.create_yarn_job_history_dir().wait()
    service.create_yarn_node_manager_remote_app_log_dir().wait()
    return True

def init_sentry(cloudera, connection, cluster_name, service_type):
    service = get_svc(cloudera, connection, cluster_name, service_type)
    service.create_sentry_database_tables().wait()
    return True

def init_oozie(cloudera, connection, cluster_name, service_type):
    service = get_svc(cloudera, connection, cluster_name, service_type)
    service.create_oozie_db().wait()
    service.install_oozie_sharelib().wait()
    return True

def init_hdfs(cloudera, connection, cluster_name, service_type):
    service = get_svc(cloudera, connection, cluster_name, service_type)
    namenode_role_name = service.get_roles_by_type('NAMENODE')[0].name
    service.format_hdfs(namenode_role_name)[0].wait()
    service.init_hdfs_shared_dir(namenode_role_name)
    service.create_hdfs_tmp().wait()
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
            cluster_name=dict(default='MyCluster', required=False, type='str'),
            service_type=dict(required=True, type='str'),
            force=dict(default=False, type='bool'),
            state=dict(default='start', choices=[
                'start', 'stop', 'restart', 'init_zk', 'init_hive', 'init_impala', 'init_sqoop', 'init_hbase', 'init_solr',
                'init_yarn', 'init_sentry', 'deploy_service_config', 'init_oozie', 'init_hdfs'
            ])
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
    service_type = module.params['service_type'].upper()
    force = module.params['force']
    state = module.params['state']
    changed=False

    cloudera = Cloudera(module, host, port, username, password, api_version, use_tls)
    connection = cloudera.connect()

    if module.check_mode:
        module.exit_json(changed=True)

    if state == 'start':
        changed = service_control(cloudera, connection, cluster_name, service_type, force, action='start')
    elif state == 'stop':
        changed = service_control(cloudera, connection, cluster_name, service_type, force, action='stop')
    elif state == 'restart':
        changed = service_control(cloudera, connection, cluster_name, service_type, force, action='restart')
    elif state == 'deploy_service_config':
        changed = deploy_service_config(cloudera, connection, cluster_name, service_type)
    elif state == 'init_zk':
        changed = init_zk(cloudera, connection, cluster_name, service_type)
    elif state == 'init_hive':
        changed = init_hive(cloudera, connection, cluster_name, service_type)
    elif state == 'init_impala':
        changed = init_impala(cloudera, connection, cluster_name, service_type)
    elif state == 'init_sqoop':
        changed = init_sqoop(cloudera, connection, cluster_name, service_type)
    elif state == 'init_hbase':
        changed = init_hbase(cloudera, connection, cluster_name, service_type)
    elif state == 'init_solr':
        changed = init_solr(cloudera, connection, cluster_name, service_type)
    elif state == 'init_yarn':
        changed = init_yarn(cloudera, connection, cluster_name, service_type)
    elif state == 'init_sentry':
        changed = init_sentry(cloudera, connection, cluster_name, service_type)
    elif state == 'init_oozie':
        changed = init_oozie(cloudera, connection, cluster_name, service_type)
    elif state == 'init_hdfs':
        changed = init_hdfs(cloudera, connection, cluster_name, service_type)
    elif state == 'deploy_service_config':
        changed = deploy_service_config(cloudera, connection, cluster_name, service_type)

    module.exit_json(changed=changed)

if __name__ == '__main__':
    from ansible.module_utils.basic import *
    from ansible.module_utils.cloudera import *
    main()
