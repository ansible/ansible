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
module: fortios_wanopt_profile
short_description: Configure WAN optimization profiles in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify wanopt feature and profile category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
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
        default: true
    wanopt_profile:
        description:
            - Configure WAN optimization profiles.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            auth-group:
                description:
                    - Optionally add an authentication group to restrict access to the WAN Optimization tunnel to peers in the authentication group. Source
                       wanopt.auth-group.name.
            cifs:
                description:
                    - Enable/disable CIFS (Windows sharing) WAN Optimization and configure CIFS WAN Optimization features.
                suboptions:
                    byte-caching:
                        description:
                            - Enable/disable byte-caching for HTTP. Byte caching reduces the amount of traffic by caching file data sent across the WAN and in
                               future serving if from the cache.
                        choices:
                            - enable
                            - disable
                    log-traffic:
                        description:
                            - Enable/disable logging.
                        choices:
                            - enable
                            - disable
                    port:
                        description:
                            - Single port number or port number range for CIFS. Only packets with a destination port number that matches this port number or
                               range are accepted by this profile.
                    prefer-chunking:
                        description:
                            - Select dynamic or fixed-size data chunking for HTTP WAN Optimization.
                        choices:
                            - dynamic
                            - fix
                    secure-tunnel:
                        description:
                            - Enable/disable securing the WAN Opt tunnel using SSL. Secure and non-secure tunnels use the same TCP port (7810).
                        choices:
                            - enable
                            - disable
                    status:
                        description:
                            - Enable/disable HTTP WAN Optimization.
                        choices:
                            - enable
                            - disable
                    tunnel-sharing:
                        description:
                            - Tunnel sharing mode for aggressive/non-aggressive and/or interactive/non-interactive protocols.
                        choices:
                            - private
                            - shared
                            - express-shared
            comments:
                description:
                    - Comment.
            ftp:
                description:
                    - Enable/disable FTP WAN Optimization and configure FTP WAN Optimization features.
                suboptions:
                    byte-caching:
                        description:
                            - Enable/disable byte-caching for HTTP. Byte caching reduces the amount of traffic by caching file data sent across the WAN and in
                               future serving if from the cache.
                        choices:
                            - enable
                            - disable
                    log-traffic:
                        description:
                            - Enable/disable logging.
                        choices:
                            - enable
                            - disable
                    port:
                        description:
                            - Single port number or port number range for FTP. Only packets with a destination port number that matches this port number or
                               range are accepted by this profile.
                    prefer-chunking:
                        description:
                            - Select dynamic or fixed-size data chunking for HTTP WAN Optimization.
                        choices:
                            - dynamic
                            - fix
                    secure-tunnel:
                        description:
                            - Enable/disable securing the WAN Opt tunnel using SSL. Secure and non-secure tunnels use the same TCP port (7810).
                        choices:
                            - enable
                            - disable
                    status:
                        description:
                            - Enable/disable HTTP WAN Optimization.
                        choices:
                            - enable
                            - disable
                    tunnel-sharing:
                        description:
                            - Tunnel sharing mode for aggressive/non-aggressive and/or interactive/non-interactive protocols.
                        choices:
                            - private
                            - shared
                            - express-shared
            http:
                description:
                    - Enable/disable HTTP WAN Optimization and configure HTTP WAN Optimization features.
                suboptions:
                    byte-caching:
                        description:
                            - Enable/disable byte-caching for HTTP. Byte caching reduces the amount of traffic by caching file data sent across the WAN and in
                               future serving if from the cache.
                        choices:
                            - enable
                            - disable
                    log-traffic:
                        description:
                            - Enable/disable logging.
                        choices:
                            - enable
                            - disable
                    port:
                        description:
                            - Single port number or port number range for HTTP. Only packets with a destination port number that matches this port number or
                               range are accepted by this profile.
                    prefer-chunking:
                        description:
                            - Select dynamic or fixed-size data chunking for HTTP WAN Optimization.
                        choices:
                            - dynamic
                            - fix
                    secure-tunnel:
                        description:
                            - Enable/disable securing the WAN Opt tunnel using SSL. Secure and non-secure tunnels use the same TCP port (7810).
                        choices:
                            - enable
                            - disable
                    ssl:
                        description:
                            - Enable/disable SSL/TLS offloading (hardware acceleration) for HTTPS traffic in this tunnel.
                        choices:
                            - enable
                            - disable
                    ssl-port:
                        description:
                            - Port on which to expect HTTPS traffic for SSL/TLS offloading.
                    status:
                        description:
                            - Enable/disable HTTP WAN Optimization.
                        choices:
                            - enable
                            - disable
                    tunnel-non-http:
                        description:
                            - Configure how to process non-HTTP traffic when a profile configured for HTTP traffic accepts a non-HTTP session. Can occur if an
                               application sends non-HTTP traffic using an HTTP destination port.
                        choices:
                            - enable
                            - disable
                    tunnel-sharing:
                        description:
                            - Tunnel sharing mode for aggressive/non-aggressive and/or interactive/non-interactive protocols.
                        choices:
                            - private
                            - shared
                            - express-shared
                    unknown-http-version:
                        description:
                            - How to handle HTTP sessions that do not comply with HTTP 0.9, 1.0, or 1.1.
                        choices:
                            - reject
                            - tunnel
                            - best-effort
            mapi:
                description:
                    - Enable/disable MAPI email WAN Optimization and configure MAPI WAN Optimization features.
                suboptions:
                    byte-caching:
                        description:
                            - Enable/disable byte-caching for HTTP. Byte caching reduces the amount of traffic by caching file data sent across the WAN and in
                               future serving if from the cache.
                        choices:
                            - enable
                            - disable
                    log-traffic:
                        description:
                            - Enable/disable logging.
                        choices:
                            - enable
                            - disable
                    port:
                        description:
                            - Single port number or port number range for MAPI. Only packets with a destination port number that matches this port number or
                               range are accepted by this profile.
                    secure-tunnel:
                        description:
                            - Enable/disable securing the WAN Opt tunnel using SSL. Secure and non-secure tunnels use the same TCP port (7810).
                        choices:
                            - enable
                            - disable
                    status:
                        description:
                            - Enable/disable HTTP WAN Optimization.
                        choices:
                            - enable
                            - disable
                    tunnel-sharing:
                        description:
                            - Tunnel sharing mode for aggressive/non-aggressive and/or interactive/non-interactive protocols.
                        choices:
                            - private
                            - shared
                            - express-shared
            name:
                description:
                    - Profile name.
                required: true
            tcp:
                description:
                    - Enable/disable TCP WAN Optimization and configure TCP WAN Optimization features.
                suboptions:
                    byte-caching:
                        description:
                            - Enable/disable byte-caching for HTTP. Byte caching reduces the amount of traffic by caching file data sent across the WAN and in
                               future serving if from the cache.
                        choices:
                            - enable
                            - disable
                    byte-caching-opt:
                        description:
                            - Select whether TCP byte-caching uses system memory only or both memory and disk space.
                        choices:
                            - mem-only
                            - mem-disk
                    log-traffic:
                        description:
                            - Enable/disable logging.
                        choices:
                            - enable
                            - disable
                    port:
                        description:
                            - Single port number or port number range for TCP. Only packets with a destination port number that matches this port number or
                               range are accepted by this profile.
                    secure-tunnel:
                        description:
                            - Enable/disable securing the WAN Opt tunnel using SSL. Secure and non-secure tunnels use the same TCP port (7810).
                        choices:
                            - enable
                            - disable
                    ssl:
                        description:
                            - Enable/disable SSL/TLS offloading.
                        choices:
                            - enable
                            - disable
                    ssl-port:
                        description:
                            - Port on which to expect HTTPS traffic for SSL/TLS offloading.
                    status:
                        description:
                            - Enable/disable HTTP WAN Optimization.
                        choices:
                            - enable
                            - disable
                    tunnel-sharing:
                        description:
                            - Tunnel sharing mode for aggressive/non-aggressive and/or interactive/non-interactive protocols.
                        choices:
                            - private
                            - shared
                            - express-shared
            transparent:
                description:
                    - Enable/disable transparent mode.
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
  tasks:
  - name: Configure WAN optimization profiles.
    fortios_wanopt_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      wanopt_profile:
        state: "present"
        auth-group: "<your_own_value> (source wanopt.auth-group.name)"
        cifs:
            byte-caching: "enable"
            log-traffic: "enable"
            port: "7"
            prefer-chunking: "dynamic"
            secure-tunnel: "enable"
            status: "enable"
            tunnel-sharing: "private"
        comments: "<your_own_value>"
        ftp:
            byte-caching: "enable"
            log-traffic: "enable"
            port: "16"
            prefer-chunking: "dynamic"
            secure-tunnel: "enable"
            status: "enable"
            tunnel-sharing: "private"
        http:
            byte-caching: "enable"
            log-traffic: "enable"
            port: "24"
            prefer-chunking: "dynamic"
            secure-tunnel: "enable"
            ssl: "enable"
            ssl-port: "28"
            status: "enable"
            tunnel-non-http: "enable"
            tunnel-sharing: "private"
            unknown-http-version: "reject"
        mapi:
            byte-caching: "enable"
            log-traffic: "enable"
            port: "36"
            secure-tunnel: "enable"
            status: "enable"
            tunnel-sharing: "private"
        name: "default_name_40"
        tcp:
            byte-caching: "enable"
            byte-caching-opt: "mem-only"
            log-traffic: "enable"
            port: "<your_own_value>"
            secure-tunnel: "enable"
            ssl: "enable"
            ssl-port: "48"
            status: "enable"
            tunnel-sharing: "private"
        transparent: "enable"
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


def login(data, fos):
    host = data['host']
    username = data['username']
    password = data['password']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password)


def filter_wanopt_profile_data(json):
    option_list = ['auth-group', 'cifs', 'comments',
                   'ftp', 'http', 'mapi',
                   'name', 'tcp', 'transparent']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def wanopt_profile(data, fos):
    vdom = data['vdom']
    wanopt_profile_data = data['wanopt_profile']
    filtered_data = filter_wanopt_profile_data(wanopt_profile_data)

    if wanopt_profile_data['state'] == "present":
        return fos.set('wanopt',
                       'profile',
                       data=filtered_data,
                       vdom=vdom)

    elif wanopt_profile_data['state'] == "absent":
        return fos.delete('wanopt',
                          'profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_wanopt(data, fos):
    login(data, fos)

    if data['wanopt_profile']:
        resp = wanopt_profile(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "wanopt_profile": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "auth-group": {"required": False, "type": "str"},
                "cifs": {"required": False, "type": "dict",
                         "options": {
                             "byte-caching": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                             "log-traffic": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                             "port": {"required": False, "type": "int"},
                             "prefer-chunking": {"required": False, "type": "str",
                                                 "choices": ["dynamic", "fix"]},
                             "secure-tunnel": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                             "status": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                             "tunnel-sharing": {"required": False, "type": "str",
                                                "choices": ["private", "shared", "express-shared"]}
                         }},
                "comments": {"required": False, "type": "str"},
                "ftp": {"required": False, "type": "dict",
                        "options": {
                            "byte-caching": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                            "log-traffic": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                            "port": {"required": False, "type": "int"},
                            "prefer-chunking": {"required": False, "type": "str",
                                                "choices": ["dynamic", "fix"]},
                            "secure-tunnel": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                            "status": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                            "tunnel-sharing": {"required": False, "type": "str",
                                               "choices": ["private", "shared", "express-shared"]}
                        }},
                "http": {"required": False, "type": "dict",
                         "options": {
                             "byte-caching": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                             "log-traffic": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                             "port": {"required": False, "type": "int"},
                             "prefer-chunking": {"required": False, "type": "str",
                                                 "choices": ["dynamic", "fix"]},
                             "secure-tunnel": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                             "ssl": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                             "ssl-port": {"required": False, "type": "int"},
                             "status": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                             "tunnel-non-http": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                             "tunnel-sharing": {"required": False, "type": "str",
                                                "choices": ["private", "shared", "express-shared"]},
                             "unknown-http-version": {"required": False, "type": "str",
                                                      "choices": ["reject", "tunnel", "best-effort"]}
                         }},
                "mapi": {"required": False, "type": "dict",
                         "options": {
                             "byte-caching": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                             "log-traffic": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                             "port": {"required": False, "type": "int"},
                             "secure-tunnel": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                             "status": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                             "tunnel-sharing": {"required": False, "type": "str",
                                                "choices": ["private", "shared", "express-shared"]}
                         }},
                "name": {"required": True, "type": "str"},
                "tcp": {"required": False, "type": "dict",
                        "options": {
                            "byte-caching": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                            "byte-caching-opt": {"required": False, "type": "str",
                                                 "choices": ["mem-only", "mem-disk"]},
                            "log-traffic": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                            "port": {"required": False, "type": "str"},
                            "secure-tunnel": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                            "ssl": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                            "ssl-port": {"required": False, "type": "int"},
                            "status": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                            "tunnel-sharing": {"required": False, "type": "str",
                                               "choices": ["private", "shared", "express-shared"]}
                        }},
                "transparent": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)
    try:
        from fortiosapi import FortiOSAPI
    except ImportError:
        module.fail_json(msg="fortiosapi module is required")

    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_wanopt(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
