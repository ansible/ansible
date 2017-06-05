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
module: cloudera_hos
author: "Serghei Anicheev (@sanicheev) <serghei.anicheev@gmail.com>"
version_added: '2.2.0.2'
short_description: Module for Cloudera Manager hosts.
description:
    - This module can be used to provision hosts or adding them to cluster.
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
            - Cloudera cluster name to use. This parameter should be present during 'add_to_cluster' state.
        default: None    .
        required: false
    host_username:
        description:
            - Username to use for connection from Cloudera Manager to agent node during 'install'.
        required: false
        default: roo
    private_key:
        description:
            - Private ssh key to use for connection from Cloudera Manager to agent node during 'install'.
        required: false
        default: /var/lib/cloudera-scm-server/.ssh/id_rsa
    cm_repo_url:
        description:
            - Repo URL to use for the package installation
        required: false
        default: http://archive.cloudera.com/cm5/redhat/7/x86_64/cm/5/
    gpg_key_custom_url:
        description:
            - GPG key URL to validate package signatures
        required: false
        default: https://archive.cloudera.com/cm5/redhat/7/x86_64/cm/RPM-GPG-KEY-cloudera
    hostnames:
        description:
            - List of hostnames to install or add to cluster.
        required: true
    state:
        description:
            - The desired action to take upon selected hosts. You can provision them using 'install' state or add to cluster using 'add_to_cluster state'.
        required: false
        default: install
        choices: ['install', 'add_to_cluster']
'''

EXAMPLES = '''
# Install new hosts.
- name: Install new hosts
  cloudera_host:
    host: 123.123.123.123
    username: admin
    password: admin
    private_key: /home/deploy/.ssh/id_rsa
    host_names:
      - host1
      - host2
    state: install

# Add hosts to cluster
- name: Add hosts into cluster
  cloudera_host:
    host: 123.123.123.123
    username: admin
    password: admin
    cluster_name: MyCluster
    host_names:
      - host1
      - host2
    state: add_to_cluster
'''
from time import sleep

def install_hosts(cloudera, connection, host_username, private_key, cm_repo_url, gpg_key_custom_url, hostnames):
    installed_hosts = cloudera.installed_hosts_globally(connection, hostnames)
    hosts_to_install = list(set(hostnames).difference(set(installed_hosts)))
    cloudera_manager = cloudera.cloudera_manager(connection)
    changed = False
    if len(hosts_to_install) != 0:
        status = cloudera_manager.host_install(
            host_username, hosts_to_install, private_key=private_key, cm_repo_url=cm_repo_url,
            gpg_key_custom_url=gpg_key_custom_url
        )
        while status.success is None:
            sleep(5)
            status = status.fetch()
        if status.success is not True:
            raise Exception('Host install failed with error: ' + cmd.resultMessage)
        changed = True
    return changed

def add_hosts_to_cluster(module, cloudera, connection, cluster_name, hostnames):
    cluster = cloudera.get_cluster(connection, cluster_name)
    installed_hosts_not_in_cluster = cloudera.installed_hosts_not_in_cluster(connection, cluster).values()
    changed = False
    if len(installed_hosts_not_in_cluster) == 0:
        module.log('No available hosts to add into cluster - %s!' % cluster_name)
    else:
        missing_hosts = list(set(installed_hosts_not_in_cluster).intersection(set(hostnames)))
        if len(missing_hosts) != 0:
            cluster.add_hosts(missing_hosts)
        else:
            raise Exception('Hosts - %s you are trying to add have not been installed yet!' % hostnames)
        changed = True
    return changed

def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(required=True, type='str'),
            port=dict(default=7180, type='int'),
            username=dict(default='admin', type='str'),
            password=dict(default='admin', no_log=True, type='str'),
            api_version=dict(default=12, type='int'),
            use_tls=dict(default=False, type='bool'),
            cluster_name=dict(default=None, type='str', required=False),
            host_username=dict(default='root', type='str'),
            private_key=dict(default='/var/lib/cloudera-scm-server/.ssh/id_rsa', type='path'),
            cm_repo_url=dict(default='http://archive.cloudera.com/cm5/redhat/7/x86_64/cm/5/', type='str'),
            gpg_key_custom_url=dict(default='https://archive.cloudera.com/cm5/redhat/7/x86_64/cm/RPM-GPG-KEY-cloudera', type='str'),
            hostnames=dict(required=True, type='list'),
            state=dict(default='install', choices=['install', 'add_to_cluster'])
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
    host_username = module.params['host_username']
    private_key = module.params['private_key']
    cm_repo_url = module.params['cm_repo_url']
    gpg_key_custom_url = module.params['gpg_key_custom_url']
    hostnames = module.params['hostnames']
    state = module.params['state']
    changed=False

    if module.check_mode:
        module.exit_json(changed=True)

    cloudera = Cloudera(module, host, port, username, password, api_version, use_tls)
    connection = cloudera.connect()
    if state == 'install':
        changed = install_hosts(cloudera, connection, host_username, private_key, cm_repo_url, gpg_key_custom_url, hostnames)
    if state == 'add_to_cluster' and cluster_name:
        changed = add_hosts_to_cluster(module, cloudera, connection, cluster_name, hostnames)

    module.exit_json(changed=changed)

if __name__ == '__main__':
    from ansible.module_utils.basic import *
    from ansible.module_utils.cloudera import *
    main()
