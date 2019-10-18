#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
# Copyright 2019 Fortinet, Inc.
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

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_system_sdn_connector
short_description: Configure connection to SDN Connector in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify system feature and sdn_connector category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.5
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
            - FortiOS or FortiGate IP address.
        type: str
        required: false
    username:
        description:
            - FortiOS or FortiGate username.
        type: str
        required: false
    password:
        description:
            - FortiOS or FortiGate password.
        type: str
        default: ""
    vdom:
        description:
            - Virtual domain, among those defined previously. A vdom is a
              virtual instance of the FortiGate that can be configured and
              used as a different unit.
        type: str
        default: root
    https:
        description:
            - Indicates if the requests towards FortiGate must use HTTPS protocol.
        type: bool
        default: true
    ssl_verify:
        description:
            - Ensures FortiGate certificate must be verified by a proper CA.
        type: bool
        default: true
        version_added: 2.9
    state:
        description:
            - Indicates whether to create or remove the object.
              This attribute was present already in previous version in a deeper level.
              It has been moved out to this outer level.
        type: str
        required: false
        choices:
            - present
            - absent
        version_added: 2.9
    system_sdn_connector:
        description:
            - Configure connection to SDN Connector.
        default: null
        type: dict
        suboptions:
            state:
                description:
                    - B(Deprecated)
                    - Starting with Ansible 2.9 we recommend using the top-level 'state' parameter.
                    - HORIZONTALLINE
                    - Indicates whether to create or remove the object.
                type: str
                required: false
                choices:
                    - present
                    - absent
            access_key:
                description:
                    - AWS access key ID.
                type: str
            azure_region:
                description:
                    - Azure server region.
                type: str
                choices:
                    - global
                    - china
                    - germany
                    - usgov
                    - local
            client_id:
                description:
                    - Azure client ID (application ID).
                type: str
            client_secret:
                description:
                    - Azure client secret (application key).
                type: str
            compartment_id:
                description:
                    - Compartment ID.
                type: str
            external_ip:
                description:
                    - Configure GCP external IP.
                type: list
                suboptions:
                    name:
                        description:
                            - External IP name.
                        required: true
                        type: str
            gcp_project:
                description:
                    - GCP project name.
                type: str
            key_passwd:
                description:
                    - Private key password.
                type: str
            login_endpoint:
                description:
                    - Azure Stack login enpoint.
                type: str
            name:
                description:
                    - SDN connector name.
                required: true
                type: str
            nic:
                description:
                    - Configure Azure network interface.
                type: list
                suboptions:
                    ip:
                        description:
                            - Configure IP configuration.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - IP configuration name.
                                required: true
                                type: str
                            public_ip:
                                description:
                                    - Public IP name.
                                type: str
                    name:
                        description:
                            - Network interface name.
                        required: true
                        type: str
            oci_cert:
                description:
                    - OCI certificate. Source certificate.local.name.
                type: str
            oci_fingerprint:
                description:
                    - OCI pubkey fingerprint.
                type: str
            oci_region:
                description:
                    - OCI server region.
                type: str
                choices:
                    - phoenix
                    - ashburn
                    - frankfurt
                    - london
            password:
                description:
                    - Password of the remote SDN connector as login credentials.
                type: str
            private_key:
                description:
                    - Private key of GCP service account.
                type: str
            region:
                description:
                    - AWS region name.
                type: str
            resource_group:
                description:
                    - Azure resource group.
                type: str
            resource_url:
                description:
                    - Azure Stack resource URL.
                type: str
            route:
                description:
                    - Configure GCP route.
                type: list
                suboptions:
                    name:
                        description:
                            - Route name.
                        required: true
                        type: str
            route_table:
                description:
                    - Configure Azure route table.
                type: list
                suboptions:
                    name:
                        description:
                            - Route table name.
                        required: true
                        type: str
                    route:
                        description:
                            - Configure Azure route.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Route name.
                                required: true
                                type: str
                            next_hop:
                                description:
                                    - Next hop address.
                                type: str
            secret_key:
                description:
                    - AWS secret access key.
                type: str
            server:
                description:
                    - Server address of the remote SDN connector.
                type: str
            server_port:
                description:
                    - Port number of the remote SDN connector.
                type: int
            service_account:
                description:
                    - GCP service account email.
                type: str
            status:
                description:
                    - Enable/disable connection to the remote SDN connector.
                type: str
                choices:
                    - disable
                    - enable
            subscription_id:
                description:
                    - Azure subscription ID.
                type: str
            tenant_id:
                description:
                    - Tenant ID (directory ID).
                type: str
            type:
                description:
                    - Type of SDN connector.
                type: str
                choices:
                    - aci
                    - aws
                    - azure
                    - gcp
                    - nsx
                    - nuage
                    - oci
                    - openstack
            update_interval:
                description:
                    - Dynamic object update interval (0 - 3600 sec, 0 means disabled).
                type: int
            use_metadata_iam:
                description:
                    - Enable/disable using IAM role from metadata to call API.
                type: str
                choices:
                    - disable
                    - enable
            user_id:
                description:
                    - User ID.
                type: str
            username:
                description:
                    - Username of the remote SDN connector as login credentials.
                type: str
            vpc_id:
                description:
                    - AWS VPC ID.
                type: str
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
   ssl_verify: "False"
  tasks:
  - name: Configure connection to SDN Connector.
    fortios_system_sdn_connector:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      system_sdn_connector:
        access_key: "<your_own_value>"
        azure_region: "global"
        client_id: "<your_own_value>"
        client_secret: "<your_own_value>"
        compartment_id: "<your_own_value>"
        external_ip:
         -
            name: "default_name_9"
        gcp_project: "<your_own_value>"
        key_passwd: "<your_own_value>"
        login_endpoint: "<your_own_value>"
        name: "default_name_13"
        nic:
         -
            ip:
             -
                name: "default_name_16"
                public_ip: "<your_own_value>"
            name: "default_name_18"
        oci_cert: "<your_own_value> (source certificate.local.name)"
        oci_fingerprint: "<your_own_value>"
        oci_region: "phoenix"
        password: "<your_own_value>"
        private_key: "<your_own_value>"
        region: "<your_own_value>"
        resource_group: "<your_own_value>"
        resource_url: "<your_own_value>"
        route:
         -
            name: "default_name_28"
        route_table:
         -
            name: "default_name_30"
            route:
             -
                name: "default_name_32"
                next_hop: "<your_own_value>"
        secret_key: "<your_own_value>"
        server: "192.168.100.40"
        server_port: "36"
        service_account: "<your_own_value>"
        status: "disable"
        subscription_id: "<your_own_value>"
        tenant_id: "<your_own_value>"
        type: "aci"
        update_interval: "42"
        use_metadata_iam: "disable"
        user_id: "<your_own_value>"
        username: "<your_own_value>"
        vpc_id: "<your_own_value>"
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
  sample: "id"
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
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortios.fortios import FortiOSHandler
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG


def login(data, fos):
    host = data['host']
    username = data['username']
    password = data['password']
    ssl_verify = data['ssl_verify']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password, verify=ssl_verify)


def filter_system_sdn_connector_data(json):
    option_list = ['access_key', 'azure_region', 'client_id',
                   'client_secret', 'compartment_id', 'external_ip',
                   'gcp_project', 'key_passwd', 'login_endpoint',
                   'name', 'nic', 'oci_cert',
                   'oci_fingerprint', 'oci_region', 'password',
                   'private_key', 'region', 'resource_group',
                   'resource_url', 'route', 'route_table',
                   'secret_key', 'server', 'server_port',
                   'service_account', 'status', 'subscription_id',
                   'tenant_id', 'type', 'update_interval',
                   'use_metadata_iam', 'user_id', 'username',
                   'vpc_id']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def underscore_to_hyphen(data):
    if isinstance(data, list):
        for elem in data:
            elem = underscore_to_hyphen(elem)
    elif isinstance(data, dict):
        new_data = {}
        for k, v in data.items():
            new_data[k.replace('_', '-')] = underscore_to_hyphen(v)
        data = new_data

    return data


def system_sdn_connector(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['system_sdn_connector'] and data['system_sdn_connector']:
        state = data['system_sdn_connector']['state']
    else:
        state = True
    system_sdn_connector_data = data['system_sdn_connector']
    filtered_data = underscore_to_hyphen(filter_system_sdn_connector_data(system_sdn_connector_data))

    if state == "present":
        return fos.set('system',
                       'sdn-connector',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('system',
                          'sdn-connector',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_system(data, fos):

    if data['system_sdn_connector']:
        resp = system_sdn_connector(data, fos)

    return not is_successful_status(resp), \
        resp['status'] == "success", \
        resp


def main():
    fields = {
        "host": {"required": False, "type": "str"},
        "username": {"required": False, "type": "str"},
        "password": {"required": False, "type": "str", "default": "", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "ssl_verify": {"required": False, "type": "bool", "default": True},
        "state": {"required": False, "type": "str",
                  "choices": ["present", "absent"]},
        "system_sdn_connector": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "access_key": {"required": False, "type": "str"},
                "azure_region": {"required": False, "type": "str",
                                 "choices": ["global", "china", "germany",
                                             "usgov", "local"]},
                "client_id": {"required": False, "type": "str"},
                "client_secret": {"required": False, "type": "str"},
                "compartment_id": {"required": False, "type": "str"},
                "external_ip": {"required": False, "type": "list",
                                "options": {
                                    "name": {"required": True, "type": "str"}
                                }},
                "gcp_project": {"required": False, "type": "str"},
                "key_passwd": {"required": False, "type": "str"},
                "login_endpoint": {"required": False, "type": "str"},
                "name": {"required": True, "type": "str"},
                "nic": {"required": False, "type": "list",
                        "options": {
                            "ip": {"required": False, "type": "list",
                                   "options": {
                                       "name": {"required": True, "type": "str"},
                                       "public_ip": {"required": False, "type": "str"}
                                   }},
                            "name": {"required": True, "type": "str"}
                        }},
                "oci_cert": {"required": False, "type": "str"},
                "oci_fingerprint": {"required": False, "type": "str"},
                "oci_region": {"required": False, "type": "str",
                               "choices": ["phoenix", "ashburn", "frankfurt",
                                           "london"]},
                "password": {"required": False, "type": "str"},
                "private_key": {"required": False, "type": "str"},
                "region": {"required": False, "type": "str"},
                "resource_group": {"required": False, "type": "str"},
                "resource_url": {"required": False, "type": "str"},
                "route": {"required": False, "type": "list",
                          "options": {
                              "name": {"required": True, "type": "str"}
                          }},
                "route_table": {"required": False, "type": "list",
                                "options": {
                                    "name": {"required": True, "type": "str"},
                                    "route": {"required": False, "type": "list",
                                              "options": {
                                                  "name": {"required": True, "type": "str"},
                                                  "next_hop": {"required": False, "type": "str"}
                                              }}
                                }},
                "secret_key": {"required": False, "type": "str"},
                "server": {"required": False, "type": "str"},
                "server_port": {"required": False, "type": "int"},
                "service_account": {"required": False, "type": "str"},
                "status": {"required": False, "type": "str",
                           "choices": ["disable", "enable"]},
                "subscription_id": {"required": False, "type": "str"},
                "tenant_id": {"required": False, "type": "str"},
                "type": {"required": False, "type": "str",
                         "choices": ["aci", "aws", "azure",
                                     "gcp", "nsx", "nuage",
                                     "oci", "openstack"]},
                "update_interval": {"required": False, "type": "int"},
                "use_metadata_iam": {"required": False, "type": "str",
                                     "choices": ["disable", "enable"]},
                "user_id": {"required": False, "type": "str"},
                "username": {"required": False, "type": "str"},
                "vpc_id": {"required": False, "type": "str"}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)

    # legacy_mode refers to using fortiosapi instead of HTTPAPI
    legacy_mode = 'host' in module.params and module.params['host'] is not None and \
                  'username' in module.params and module.params['username'] is not None and \
                  'password' in module.params and module.params['password'] is not None

    if not legacy_mode:
        if module._socket_path:
            connection = Connection(module._socket_path)
            fos = FortiOSHandler(connection)

            is_error, has_changed, result = fortios_system(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_system(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
