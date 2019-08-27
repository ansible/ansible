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
module: fortios_wanopt_webcache
short_description: Configure global Web cache settings in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify wanopt feature and webcache category.
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
    wanopt_webcache:
        description:
            - Configure global Web cache settings.
        default: null
        type: dict
        suboptions:
            always_revalidate:
                description:
                    - Enable/disable revalidation of requested cached objects, which have content on the server, before serving it to the client.
                type: str
                choices:
                    - enable
                    - disable
            cache_by_default:
                description:
                    - Enable/disable caching content that lacks explicit caching policies from the server.
                type: str
                choices:
                    - enable
                    - disable
            cache_cookie:
                description:
                    - Enable/disable caching cookies. Since cookies contain information for or about individual users, they not usually cached.
                type: str
                choices:
                    - enable
                    - disable
            cache_expired:
                description:
                    - Enable/disable caching type-1 objects that are already expired on arrival.
                type: str
                choices:
                    - enable
                    - disable
            default_ttl:
                description:
                    - Default object expiry time . This only applies to those objects that do not have an expiry time set by the web server.
                type: int
            external:
                description:
                    - Enable/disable external Web caching.
                type: str
                choices:
                    - enable
                    - disable
            fresh_factor:
                description:
                    - Frequency that the server is checked to see if any objects have expired (1 - 100). The higher the fresh factor, the less often the
                       checks occur.
                type: int
            host_validate:
                description:
                    - "Enable/disable validating Host: with original server IP."
                type: str
                choices:
                    - enable
                    - disable
            ignore_conditional:
                description:
                    - Enable/disable controlling the behavior of cache-control HTTP 1.1 header values.
                type: str
                choices:
                    - enable
                    - disable
            ignore_ie_reload:
                description:
                    - "Enable/disable ignoring the PNC-interpretation of Internet Explorer's Accept: / header."
                type: str
                choices:
                    - enable
                    - disable
            ignore_ims:
                description:
                    - Enable/disable ignoring the if-modified-since (IMS) header.
                type: str
                choices:
                    - enable
                    - disable
            ignore_pnc:
                description:
                    - Enable/disable ignoring the pragma no-cache (PNC) header.
                type: str
                choices:
                    - enable
                    - disable
            max_object_size:
                description:
                    - Maximum cacheable object size in kB (1 - 2147483 kb (2GB). All objects that exceed this are delivered to the client but not stored in
                       the web cache.
                type: int
            max_ttl:
                description:
                    - Maximum time an object can stay in the web cache without checking to see if it has expired on the server .
                type: int
            min_ttl:
                description:
                    - Minimum time an object can stay in the web cache without checking to see if it has expired on the server .
                type: int
            neg_resp_time:
                description:
                    - Time in minutes to cache negative responses or errors (0 - 4294967295).
                type: int
            reval_pnc:
                description:
                    - Enable/disable revalidation of pragma-no-cache (PNC) to address bandwidth concerns.
                type: str
                choices:
                    - enable
                    - disable
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
  - name: Configure global Web cache settings.
    fortios_wanopt_webcache:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      wanopt_webcache:
        always_revalidate: "enable"
        cache_by_default: "enable"
        cache_cookie: "enable"
        cache_expired: "enable"
        default_ttl: "7"
        external: "enable"
        fresh_factor: "9"
        host_validate: "enable"
        ignore_conditional: "enable"
        ignore_ie_reload: "enable"
        ignore_ims: "enable"
        ignore_pnc: "enable"
        max_object_size: "15"
        max_ttl: "16"
        min_ttl: "17"
        neg_resp_time: "18"
        reval_pnc: "enable"
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


def filter_wanopt_webcache_data(json):
    option_list = ['always_revalidate', 'cache_by_default', 'cache_cookie',
                   'cache_expired', 'default_ttl', 'external',
                   'fresh_factor', 'host_validate', 'ignore_conditional',
                   'ignore_ie_reload', 'ignore_ims', 'ignore_pnc',
                   'max_object_size', 'max_ttl', 'min_ttl',
                   'neg_resp_time', 'reval_pnc']
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


def wanopt_webcache(data, fos):
    vdom = data['vdom']
    wanopt_webcache_data = data['wanopt_webcache']
    filtered_data = underscore_to_hyphen(filter_wanopt_webcache_data(wanopt_webcache_data))

    return fos.set('wanopt',
                   'webcache',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_wanopt(data, fos):

    if data['wanopt_webcache']:
        resp = wanopt_webcache(data, fos)

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
        "wanopt_webcache": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "always_revalidate": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "cache_by_default": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "cache_cookie": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "cache_expired": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "default_ttl": {"required": False, "type": "int"},
                "external": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "fresh_factor": {"required": False, "type": "int"},
                "host_validate": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "ignore_conditional": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "ignore_ie_reload": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "ignore_ims": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "ignore_pnc": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "max_object_size": {"required": False, "type": "int"},
                "max_ttl": {"required": False, "type": "int"},
                "min_ttl": {"required": False, "type": "int"},
                "neg_resp_time": {"required": False, "type": "int"},
                "reval_pnc": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]}

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

            is_error, has_changed, result = fortios_wanopt(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_wanopt(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
