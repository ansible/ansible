#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
# Copyright 2018 Fortinet, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# the lib use python logging can get it if the following is set in your
# Ansible config.

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_system_sdn_connector
short_description: Configure connection to SDN Connector.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure system feature and sdn_connector category.
      Examples includes all options and need to be adjusted to datasources before usage.
      Tested with FOS v6.0.2
version_added: "2.8"
author:
    - Miguel Angel Munoz (@mamunozgonzalez)
    - Nicolas Thomas (@thomnico)
notes:
    - Requires fortiosapi library developed by Fortinet
    - Run as a local_action in your playbook
requirements:
    - fortiosapi>=0.9.8
options:
    host:
       description:
            - FortiOS or FortiGate ip address.
       required: true
    username:
        description:
            - FortiOS or FortiGate username.
        required: true
    password:
        description:
            - FortiOS or FortiGate password.
        default: ""
    vdom:
        description:
            - Virtual domain, among those defined previously. A vdom is a
              virtual instance of the FortiGate that can be configured and
              used as a different unit.
        default: root
    https:
        description:
            - Indicates if the requests towards FortiGate must use HTTPS
              protocol
        type: bool
        default: false
    system_sdn_connector:
        description:
            - Configure connection to SDN Connector.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            access-key:
                description:
                    - AWS access key ID.
            azure-region:
                description:
                    - Azure server region.
                choices:
                    - global
                    - china
                    - germany
                    - usgov
            client-id:
                description:
                    - Azure client ID (application ID).
            client-secret:
                description:
                    - Azure client secret (application key).
            compartment-id:
                description:
                    - Compartment ID.
            external-ip:
                description:
                    - Configure GCP external IP.
                suboptions:
                    name:
                        description:
                            - External IP name.
                        required: true
            gcp-project:
                description:
                    - GCP project name.
            key-passwd:
                description:
                    - Private key password.
            name:
                description:
                    - SDN connector name.
                required: true
            nic:
                description:
                    - Configure Azure network interface.
                suboptions:
                    ip:
                        description:
                            - Configure IP configuration.
                        suboptions:
                            name:
                                description:
                                    - IP configuration name.
                                required: true
                            public-ip:
                                description:
                                    - Public IP name.
                    name:
                        description:
                            - Network interface name.
                        required: true
            oci-cert:
                description:
                    - OCI certificate. Source certificate.local.name.
            oci-fingerprint:
                description:
                    - OCI pubkey fingerprint.
            oci-region:
                description:
                    - OCI server region.
                choices:
                    - phoenix
                    - ashburn
                    - frankfurt
                    - london
            password:
                description:
                    - Password of the remote SDN connector as login credentials.
            private-key:
                description:
                    - Private key of GCP service account.
            region:
                description:
                    - AWS region name.
            resource-group:
                description:
                    - Azure resource group.
            route:
                description:
                    - Configure GCP route.
                suboptions:
                    name:
                        description:
                            - Route name.
                        required: true
            route-table:
                description:
                    - Configure Azure route table.
                suboptions:
                    name:
                        description:
                            - Route table name.
                        required: true
                    route:
                        description:
                            - Configure Azure route.
                        suboptions:
                            name:
                                description:
                                    - Route name.
                                required: true
                            next-hop:
                                description:
                                    - Next hop address.
            secret-key:
                description:
                    - AWS secret access key.
            server:
                description:
                    - Server address of the remote SDN connector.
            server-port:
                description:
                    - Port number of the remote SDN connector.
            service-account:
                description:
                    - GCP service account email.
            status:
                description:
                    - Enable/disable connection to the remote SDN connector.
                choices:
                    - disable
                    - enable
            subscription-id:
                description:
                    - Azure subscription ID.
            tenant-id:
                description:
                    - Tenant ID (directory ID).
            type:
                description:
                    - Type of SDN connector.
                choices:
                    - aci
                    - aws
                    - azure
                    - nsx
                    - nuage
                    - oci
                    - gcp
            update-interval:
                description:
                    - Dynamic object update interval (0 - 3600 sec, 0 means disabled, default = 60).
            use-metadata-iam:
                description:
                    - Enable/disable using IAM role from metadata to call API.
                choices:
                    - disable
                    - enable
            user-id:
                description:
                    - User ID.
            username:
                description:
                    - Username of the remote SDN connector as login credentials.
            vpc-id:
                description:
                    - AWS VPC ID.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure connection to SDN Connector.
    fortios_system_sdn_connector:
      host:  "{{  host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{  vdom }}"
      system_sdn_connector:
        state: "present"
        access-key: "<your_own_value>"
        azure-region: "global"
        client-id: "<your_own_value>"
        client-secret: "<your_own_value>"
        compartment-id: "<your_own_value>"
        external-ip:
         -
            name: "default_name_9"
        gcp-project: "<your_own_value>"
        key-passwd: "<your_own_value>"
        name: "default_name_12"
        nic:
         -
            ip:
             -
                name: "default_name_15"
                public-ip: "<your_own_value>"
            name: "default_name_17"
        oci-cert: "<your_own_value> (source certificate.local.name)"
        oci-fingerprint: "<your_own_value>"
        oci-region: "phoenix"
        password: "<your_own_value>"
        private-key: "<your_own_value>"
        region: "<your_own_value>"
        resource-group: "<your_own_value>"
        route:
         -
            name: "default_name_26"
        route-table:
         -
            name: "default_name_28"
            route:
             -
                name: "default_name_30"
                next-hop: "<your_own_value>"
        secret-key: "<your_own_value>"
        server: "192.168.100.40"
        server-port: "34"
        service-account: "<your_own_value>"
        status: "disable"
        subscription-id: "<your_own_value>"
        tenant-id: "<your_own_value>"
        type: "aci"
        update-interval: "40"
        use-metadata-iam: "disable"
        user-id: "<your_own_value>"
        username: "<your_own_value>"
        vpc-id: "<your_own_value>"
'''

RETURN = '''
build:
  description: Build number of the fortigate image
  returned: always
  type: str
  sample: '1547'
http_method:
  description: Last method used to provision the content into FortiGate
  returned: always
  type: str
  sample: 'PUT'
http_status:
  description: Last result given by FortiGate on last operation applied
  returned: always
  type: str
  sample: "200"
mkey:
  description: Master key (id) used in the last call to FortiGate
  returned: success
  type: str
  sample: "key1"
name:
  description: Name of the table used to fulfill the request
  returned: always
  type: str
  sample: "urlfilter"
path:
  description: Path of the table used to fulfill the request
  returned: always
  type: str
  sample: "webfilter"
revision:
  description: Internal revision number
  returned: always
  type: str
  sample: "17.0.2.10658"
serial:
  description: Serial number of the unit
  returned: always
  type: str
  sample: "FGVMEVYYQT3AB5352"
status:
  description: Indication of the operation's result
  returned: always
  type: str
  sample: "success"
vdom:
  description: Virtual domain used
  returned: always
  type: str
  sample: "root"
version:
  description: Version of the FortiGate
  returned: always
  type: str
  sample: "v5.6.3"

'''

from ansible.module_utils.basic import AnsibleModule

fos = None


def login(data):
    host = data['host']
    username = data['username']
    password = data['password']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password)


def filter_system_sdn_connector_data(json):
    option_list = ['access-key', 'azure-region', 'client-id',
                   'client-secret', 'compartment-id', 'external-ip',
                   'gcp-project', 'key-passwd', 'name',
                   'nic', 'oci-cert', 'oci-fingerprint',
                   'oci-region', 'password', 'private-key',
                   'region', 'resource-group', 'route',
                   'route-table', 'secret-key', 'server',
                   'server-port', 'service-account', 'status',
                   'subscription-id', 'tenant-id', 'type',
                   'update-interval', 'use-metadata-iam', 'user-id',
                   'username', 'vpc-id']
    dictionary = {}

    for attribute in option_list:
        if attribute in json:
            dictionary[attribute] = json[attribute]

    return dictionary


def system_sdn_connector(data, fos):
    vdom = data['vdom']
    system_sdn_connector_data = data['system_sdn_connector']
    filtered_data = filter_system_sdn_connector_data(system_sdn_connector_data)
    if system_sdn_connector_data['state'] == "present":
        return fos.set('system',
                       'sdn-connector',
                       data=filtered_data,
                       vdom=vdom)

    elif system_sdn_connector_data['state'] == "absent":
        return fos.delete('system',
                          'sdn-connector',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_system(data, fos):
    login(data)

    methodlist = ['system_sdn_connector']
    for method in methodlist:
        if data[method]:
            resp = eval(method)(data, fos)
            break

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": "False"},
        "system_sdn_connector": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "access-key": {"required": False, "type": "str"},
                "azure-region": {"required": False, "type": "str",
                                 "choices": ["global", "china", "germany",
                                             "usgov"]},
                "client-id": {"required": False, "type": "str"},
                "client-secret": {"required": False, "type": "str"},
                "compartment-id": {"required": False, "type": "str"},
                "external-ip": {"required": False, "type": "list",
                                "options": {
                                    "name": {"required": True, "type": "str"}
                                }},
                "gcp-project": {"required": False, "type": "str"},
                "key-passwd": {"required": False, "type": "str"},
                "name": {"required": True, "type": "str"},
                "nic": {"required": False, "type": "list",
                        "options": {
                            "ip": {"required": False, "type": "list",
                                   "options": {
                                       "name": {"required": True, "type": "str"},
                                       "public-ip": {"required": False, "type": "str"}
                                   }},
                            "name": {"required": True, "type": "str"}
                        }},
                "oci-cert": {"required": False, "type": "str"},
                "oci-fingerprint": {"required": False, "type": "str"},
                "oci-region": {"required": False, "type": "str",
                               "choices": ["phoenix", "ashburn", "frankfurt",
                                           "london"]},
                "password": {"required": False, "type": "str"},
                "private-key": {"required": False, "type": "str"},
                "region": {"required": False, "type": "str"},
                "resource-group": {"required": False, "type": "str"},
                "route": {"required": False, "type": "list",
                          "options": {
                              "name": {"required": True, "type": "str"}
                          }},
                "route-table": {"required": False, "type": "list",
                                "options": {
                                    "name": {"required": True, "type": "str"},
                                    "route": {"required": False, "type": "list",
                                              "options": {
                                                  "name": {"required": True, "type": "str"},
                                                  "next-hop": {"required": False, "type": "str"}
                                              }}
                                }},
                "secret-key": {"required": False, "type": "str"},
                "server": {"required": False, "type": "str"},
                "server-port": {"required": False, "type": "int"},
                "service-account": {"required": False, "type": "str"},
                "status": {"required": False, "type": "str",
                           "choices": ["disable", "enable"]},
                "subscription-id": {"required": False, "type": "str"},
                "tenant-id": {"required": False, "type": "str"},
                "type": {"required": False, "type": "str",
                         "choices": ["aci", "aws", "azure",
                                     "nsx", "nuage", "oci",
                                     "gcp"]},
                "update-interval": {"required": False, "type": "int"},
                "use-metadata-iam": {"required": False, "type": "str",
                                     "choices": ["disable", "enable"]},
                "user-id": {"required": False, "type": "str"},
                "username": {"required": False, "type": "str"},
                "vpc-id": {"required": False, "type": "str"}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)
    try:
        from fortiosapi import FortiOSAPI
    except ImportError:
        module.fail_json(msg="fortiosapi module is required")

    global fos
    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_system(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
