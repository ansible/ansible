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
module: fortios_system_cluster_sync
short_description: Configure FortiGate Session Life Support Protocol (FGSP) session synchronization in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify system feature and cluster_sync category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.5
version_added: "2.9"
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
    state:
        description:
            - Indicates whether to create or remove the object.
        type: str
        required: true
        choices:
            - present
            - absent
    system_cluster_sync:
        description:
            - Configure FortiGate Session Life Support Protocol (FGSP) session synchronization.
        default: null
        type: dict
        suboptions:
            down_intfs_before_sess_sync:
                description:
                    - List of interfaces to be turned down before session synchronization is complete.
                type: list
                suboptions:
                    name:
                        description:
                            - Interface name. Source system.interface.name.
                        required: true
                        type: str
            hb_interval:
                description:
                    - Heartbeat interval (1 - 10 sec).
                type: int
            hb_lost_threshold:
                description:
                    - Lost heartbeat threshold (1 - 10).
                type: int
            peerip:
                description:
                    - IP address of the interface on the peer unit that is used for the session synchronization link.
                type: str
            peervd:
                description:
                    - VDOM that contains the session synchronization link interface on the peer unit. Usually both peers would have the same peervd. Source
                       system.vdom.name.
                type: str
            session_sync_filter:
                description:
                    - Add one or more filters if you only want to synchronize some sessions. Use the filter to configure the types of sessions to synchronize.
                type: dict
                suboptions:
                    custom_service:
                        description:
                            - Only sessions using these custom services are synchronized. Use source and destination port ranges to define these custom
                              services.
                        type: list
                        suboptions:
                            dst_port_range:
                                description:
                                    - Custom service destination port range.
                                type: str
                            id:
                                description:
                                    - Custom service ID.
                                required: true
                                type: int
                            src_port_range:
                                description:
                                    - Custom service source port range.
                                type: str
                    dstaddr:
                        description:
                            - Only sessions to this IPv4 address are synchronized. You can only enter one address. To synchronize sessions for multiple
                               destination addresses, add multiple filters.
                        type: str
                    dstaddr6:
                        description:
                            - Only sessions to this IPv6 address are synchronized. You can only enter one address. To synchronize sessions for multiple
                               destination addresses, add multiple filters.
                        type: str
                    dstintf:
                        description:
                            - Only sessions to this interface are synchronized. You can only enter one interface name. To synchronize sessions to multiple
                               destination interfaces, add multiple filters. Source system.interface.name.
                        type: str
                    srcaddr:
                        description:
                            - Only sessions from this IPv4 address are synchronized. You can only enter one address. To synchronize sessions from multiple
                               source addresses, add multiple filters.
                        type: str
                    srcaddr6:
                        description:
                            - Only sessions from this IPv6 address are synchronized. You can only enter one address. To synchronize sessions from multiple
                               source addresses, add multiple filters.
                        type: str
                    srcintf:
                        description:
                            - Only sessions from this interface are synchronized. You can only enter one interface name. To synchronize sessions for multiple
                               source interfaces, add multiple filters. Source system.interface.name.
                        type: str
            slave_add_ike_routes:
                description:
                    - Enable/disable IKE route announcement on the backup unit.
                type: str
                choices:
                    - enable
                    - disable
            sync_id:
                description:
                    - Sync ID.
                type: int
            syncvd:
                description:
                    - Sessions from these VDOMs are synchronized using this session synchronization configuration.
                type: list
                suboptions:
                    name:
                        description:
                            - VDOM name. Source system.vdom.name.
                        required: true
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
  - name: Configure FortiGate Session Life Support Protocol (FGSP) session synchronization.
    fortios_system_cluster_sync:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      system_cluster_sync:
        down_intfs_before_sess_sync:
         -
            name: "default_name_4 (source system.interface.name)"
        hb_interval: "5"
        hb_lost_threshold: "6"
        peerip: "<your_own_value>"
        peervd: "<your_own_value> (source system.vdom.name)"
        session_sync_filter:
            custom_service:
             -
                dst_port_range: "<your_own_value>"
                id:  "12"
                src_port_range: "<your_own_value>"
            dstaddr: "<your_own_value>"
            dstaddr6: "<your_own_value>"
            dstintf: "<your_own_value> (source system.interface.name)"
            srcaddr: "<your_own_value>"
            srcaddr6: "<your_own_value>"
            srcintf: "<your_own_value> (source system.interface.name)"
        slave_add_ike_routes: "enable"
        sync_id: "21"
        syncvd:
         -
            name: "default_name_23 (source system.vdom.name)"
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


def filter_system_cluster_sync_data(json):
    option_list = ['down_intfs_before_sess_sync', 'hb_interval', 'hb_lost_threshold',
                   'peerip', 'peervd', 'session_sync_filter',
                   'slave_add_ike_routes', 'sync_id', 'syncvd']
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


def system_cluster_sync(data, fos):
    vdom = data['vdom']
    state = data['state']
    system_cluster_sync_data = data['system_cluster_sync']
    filtered_data = underscore_to_hyphen(filter_system_cluster_sync_data(system_cluster_sync_data))

    if state == "present":
        return fos.set('system',
                       'cluster-sync',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('system',
                          'cluster-sync',
                          mkey=filtered_data['sync-id'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_system(data, fos):

    if data['system_cluster_sync']:
        resp = system_cluster_sync(data, fos)

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
        "state": {"required": True, "type": "str",
                  "choices": ["present", "absent"]},
        "system_cluster_sync": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "down_intfs_before_sess_sync": {"required": False, "type": "list",
                                                "options": {
                                                    "name": {"required": True, "type": "str"}
                                                }},
                "hb_interval": {"required": False, "type": "int"},
                "hb_lost_threshold": {"required": False, "type": "int"},
                "peerip": {"required": False, "type": "str"},
                "peervd": {"required": False, "type": "str"},
                "session_sync_filter": {"required": False, "type": "dict",
                                        "options": {
                                            "custom_service": {"required": False, "type": "list",
                                                               "options": {
                                                                   "dst_port_range": {"required": False, "type": "str"},
                                                                   "id": {"required": True, "type": "int"},
                                                                   "src_port_range": {"required": False, "type": "str"}
                                                               }},
                                            "dstaddr": {"required": False, "type": "str"},
                                            "dstaddr6": {"required": False, "type": "str"},
                                            "dstintf": {"required": False, "type": "str"},
                                            "srcaddr": {"required": False, "type": "str"},
                                            "srcaddr6": {"required": False, "type": "str"},
                                            "srcintf": {"required": False, "type": "str"}
                                        }},
                "slave_add_ike_routes": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "sync_id": {"required": False, "type": "int"},
                "syncvd": {"required": False, "type": "list",
                           "options": {
                               "name": {"required": True, "type": "str"}
                           }}

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
