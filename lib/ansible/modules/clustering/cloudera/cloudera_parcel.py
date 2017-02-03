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
module: cloudera_license
author: "Serghei Anicheev (@sanicheev) <serghei.anicheev@gmail.com>"
version_added: '2.2.0.2'
short_description: Cloudera Manager parcel.
description:
    - This module can install,distribute and activate cluster packages.
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
            - Cloudera cluster name to use.   .
        required: true
    parcel_name:
        description:
            - Parcel name to use
        required: false
        default: CDH5
    parcel_version:
        description:
            - Parcel version to use
        required: true
    state:
        description:
            - The desired action to take on selected parcel in cluster.
        required: false
        default: activate
        choices: ['activate']
'''

EXAMPLES = '''
# Distribute parcels.
- name: Distribute parcels
  cloudera_parcel:
    host: 123.123.123.123
    username: admin
    password: admin
    cluster_name: MyCluster
    parcel_name: CDH5
    parcel_version: 5.9.1-1.cdh5.9.1.p0.4
    state: activate
'''

from time import sleep

def deploy_parcel(module, cluster, parcel_name, parcel_version):
    all_parcels = cluster.get_all_parcels()
    parcel = filter(lambda parcel: parcel.product == parcel_name and parcel.version == parcel_version, all_parcels)
    changed = False
    if len(parcel) == 0:
        raise Exception('No such parcel version - %s, for parcel name - %s!' % (parcel_version, parcel_name))
    elif parcel[0].stage == 'ACTIVATED':
        module.log('Parcel %s already activated!' % parcel_version)
    else:
        parcel_obj = parcel[0]

        download = parcel_obj.start_download()
        while parcel_obj.stage != 'DOWNLOADED':
            sleep(5)
            parcel_obj = cluster.get_parcel(parcel_name, parcel_version)

        parcel_obj.start_distribution()
        while parcel_obj.stage != "DISTRIBUTED":
            sleep(5)
            parcel_obj = cluster.get_parcel(parcel_name, parcel_version)

        parcel_obj.activate()
        while parcel_obj.stage != "ACTIVATED":
            sleep(5)
            parcel_obj = cluster.get_parcel(parcel_name, parcel_version)
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
            cluster_name=dict(required=True, type='str'),
            parcel_name=dict(required=False, default='CDH5', type='str'),
            parcel_version=dict(required=True, type='str'),
            state=dict(default='activate', choices=['activate'])
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
    parcel_name = module.params['parcel_name']
    parcel_version = module.params['parcel_version']
    state = module.params['state']
    changed=False

    if module.check_mode:
        module.exit_json(changed=True)

    cloudera = Cloudera(module, host, port, username, password, api_version, use_tls)
    connection = cloudera.connect()
    cluster = cloudera.get_cluster(connection, cluster_name)

    if state == 'activate':
        changed = deploy_parcel(module, cluster, parcel_name, parcel_version)

    module.exit_json(changed=changed, state=state)

if __name__ == '__main__':
    from ansible.module_utils.basic import *
    from ansible.module_utils.cloudera import *
    main()
