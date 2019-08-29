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
module: fortios_firewall_profile_protocol_options
short_description: Configure protocol options in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify firewall feature and profile_protocol_options category.
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
    firewall_profile_protocol_options:
        description:
            - Configure protocol options.
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
            comment:
                description:
                    - Optional comments.
                type: str
            dns:
                description:
                    - Configure DNS protocol options.
                type: dict
                suboptions:
                    ports:
                        description:
                            - Ports to scan for content (1 - 65535).
                        type: int
                    status:
                        description:
                            - Enable/disable the active status of scanning for this protocol.
                        type: str
                        choices:
                            - enable
                            - disable
            ftp:
                description:
                    - Configure FTP protocol options.
                type: dict
                suboptions:
                    comfort_amount:
                        description:
                            - Amount of data to send in a transmission for client comforting (1 - 10240 bytes).
                        type: int
                    comfort_interval:
                        description:
                            - Period of time between start, or last transmission, and the next client comfort transmission of data (1 - 900 sec).
                        type: int
                    inspect_all:
                        description:
                            - Enable/disable the inspection of all ports for the protocol.
                        type: str
                        choices:
                            - enable
                            - disable
                    options:
                        description:
                            - One or more options that can be applied to the session.
                        type: str
                        choices:
                            - clientcomfort
                            - oversize
                            - splice
                            - bypass-rest-command
                            - bypass-mode-command
                    oversize_limit:
                        description:
                            - Maximum in-memory file size that can be scanned (1 - 383 MB).
                        type: int
                    ports:
                        description:
                            - Ports to scan for content (1 - 65535).
                        type: int
                    scan_bzip2:
                        description:
                            - Enable/disable scanning of BZip2 compressed files.
                        type: str
                        choices:
                            - enable
                            - disable
                    status:
                        description:
                            - Enable/disable the active status of scanning for this protocol.
                        type: str
                        choices:
                            - enable
                            - disable
                    uncompressed_nest_limit:
                        description:
                            - Maximum nested levels of compression that can be uncompressed and scanned (2 - 100).
                        type: int
                    uncompressed_oversize_limit:
                        description:
                            - Maximum in-memory uncompressed file size that can be scanned (0 - 383 MB, 0 = unlimited).
                        type: int
            http:
                description:
                    - Configure HTTP protocol options.
                type: dict
                suboptions:
                    block_page_status_code:
                        description:
                            - Code number returned for blocked HTTP pages (non-FortiGuard only) (100 - 599).
                        type: int
                    comfort_amount:
                        description:
                            - Amount of data to send in a transmission for client comforting (1 - 10240 bytes).
                        type: int
                    comfort_interval:
                        description:
                            - Period of time between start, or last transmission, and the next client comfort transmission of data (1 - 900 sec).
                        type: int
                    fortinet_bar:
                        description:
                            - Enable/disable Fortinet bar on HTML content.
                        type: str
                        choices:
                            - enable
                            - disable
                    fortinet_bar_port:
                        description:
                            - Port for use by Fortinet Bar (1 - 65535).
                        type: int
                    http_policy:
                        description:
                            - Enable/disable HTTP policy check.
                        type: str
                        choices:
                            - disable
                            - enable
                    inspect_all:
                        description:
                            - Enable/disable the inspection of all ports for the protocol.
                        type: str
                        choices:
                            - enable
                            - disable
                    options:
                        description:
                            - One or more options that can be applied to the session.
                        type: str
                        choices:
                            - clientcomfort
                            - servercomfort
                            - oversize
                            - chunkedbypass
                    oversize_limit:
                        description:
                            - Maximum in-memory file size that can be scanned (1 - 383 MB).
                        type: int
                    ports:
                        description:
                            - Ports to scan for content (1 - 65535).
                        type: int
                    post_lang:
                        description:
                            - ID codes for character sets to be used to convert to UTF-8 for banned words and DLP on HTTP posts (maximum of 5 character sets).
                        type: str
                        choices:
                            - jisx0201
                            - jisx0208
                            - jisx0212
                            - gb2312
                            - ksc5601-ex
                            - euc-jp
                            - sjis
                            - iso2022-jp
                            - iso2022-jp-1
                            - iso2022-jp-2
                            - euc-cn
                            - ces-gbk
                            - hz
                            - ces-big5
                            - euc-kr
                            - iso2022-jp-3
                            - iso8859-1
                            - tis620
                            - cp874
                            - cp1252
                            - cp1251
                    range_block:
                        description:
                            - Enable/disable blocking of partial downloads.
                        type: str
                        choices:
                            - disable
                            - enable
                    retry_count:
                        description:
                            - Number of attempts to retry HTTP connection (0 - 100).
                        type: int
                    scan_bzip2:
                        description:
                            - Enable/disable scanning of BZip2 compressed files.
                        type: str
                        choices:
                            - enable
                            - disable
                    status:
                        description:
                            - Enable/disable the active status of scanning for this protocol.
                        type: str
                        choices:
                            - enable
                            - disable
                    streaming_content_bypass:
                        description:
                            - Enable/disable bypassing of streaming content from buffering.
                        type: str
                        choices:
                            - enable
                            - disable
                    strip_x_forwarded_for:
                        description:
                            - Enable/disable stripping of HTTP X-Forwarded-For header.
                        type: str
                        choices:
                            - disable
                            - enable
                    switching_protocols:
                        description:
                            - Bypass from scanning, or block a connection that attempts to switch protocol.
                        type: str
                        choices:
                            - bypass
                            - block
                    uncompressed_nest_limit:
                        description:
                            - Maximum nested levels of compression that can be uncompressed and scanned (2 - 100).
                        type: int
                    uncompressed_oversize_limit:
                        description:
                            - Maximum in-memory uncompressed file size that can be scanned (0 - 383 MB, 0 = unlimited).
                        type: int
            imap:
                description:
                    - Configure IMAP protocol options.
                type: dict
                suboptions:
                    inspect_all:
                        description:
                            - Enable/disable the inspection of all ports for the protocol.
                        type: str
                        choices:
                            - enable
                            - disable
                    options:
                        description:
                            - One or more options that can be applied to the session.
                        type: str
                        choices:
                            - fragmail
                            - oversize
                    oversize_limit:
                        description:
                            - Maximum in-memory file size that can be scanned (1 - 383 MB).
                        type: int
                    ports:
                        description:
                            - Ports to scan for content (1 - 65535).
                        type: int
                    scan_bzip2:
                        description:
                            - Enable/disable scanning of BZip2 compressed files.
                        type: str
                        choices:
                            - enable
                            - disable
                    status:
                        description:
                            - Enable/disable the active status of scanning for this protocol.
                        type: str
                        choices:
                            - enable
                            - disable
                    uncompressed_nest_limit:
                        description:
                            - Maximum nested levels of compression that can be uncompressed and scanned (2 - 100).
                        type: int
                    uncompressed_oversize_limit:
                        description:
                            - Maximum in-memory uncompressed file size that can be scanned (0 - 383 MB, 0 = unlimited).
                        type: int
            mail_signature:
                description:
                    - Configure Mail signature.
                type: dict
                suboptions:
                    signature:
                        description:
                            - Email signature to be added to outgoing email (if the signature contains spaces, enclose with quotation marks).
                        type: str
                    status:
                        description:
                            - Enable/disable adding an email signature to SMTP email messages as they pass through the FortiGate.
                        type: str
                        choices:
                            - disable
                            - enable
            mapi:
                description:
                    - Configure MAPI protocol options.
                type: dict
                suboptions:
                    options:
                        description:
                            - One or more options that can be applied to the session.
                        type: str
                        choices:
                            - fragmail
                            - oversize
                    oversize_limit:
                        description:
                            - Maximum in-memory file size that can be scanned (1 - 383 MB).
                        type: int
                    ports:
                        description:
                            - Ports to scan for content (1 - 65535).
                        type: int
                    scan_bzip2:
                        description:
                            - Enable/disable scanning of BZip2 compressed files.
                        type: str
                        choices:
                            - enable
                            - disable
                    status:
                        description:
                            - Enable/disable the active status of scanning for this protocol.
                        type: str
                        choices:
                            - enable
                            - disable
                    uncompressed_nest_limit:
                        description:
                            - Maximum nested levels of compression that can be uncompressed and scanned (2 - 100).
                        type: int
                    uncompressed_oversize_limit:
                        description:
                            - Maximum in-memory uncompressed file size that can be scanned (0 - 383 MB, 0 = unlimited).
                        type: int
            name:
                description:
                    - Name.
                required: true
                type: str
            nntp:
                description:
                    - Configure NNTP protocol options.
                type: dict
                suboptions:
                    inspect_all:
                        description:
                            - Enable/disable the inspection of all ports for the protocol.
                        type: str
                        choices:
                            - enable
                            - disable
                    options:
                        description:
                            - One or more options that can be applied to the session.
                        type: str
                        choices:
                            - oversize
                            - splice
                    oversize_limit:
                        description:
                            - Maximum in-memory file size that can be scanned (1 - 383 MB).
                        type: int
                    ports:
                        description:
                            - Ports to scan for content (1 - 65535).
                        type: int
                    scan_bzip2:
                        description:
                            - Enable/disable scanning of BZip2 compressed files.
                        type: str
                        choices:
                            - enable
                            - disable
                    status:
                        description:
                            - Enable/disable the active status of scanning for this protocol.
                        type: str
                        choices:
                            - enable
                            - disable
                    uncompressed_nest_limit:
                        description:
                            - Maximum nested levels of compression that can be uncompressed and scanned (2 - 100).
                        type: int
                    uncompressed_oversize_limit:
                        description:
                            - Maximum in-memory uncompressed file size that can be scanned (0 - 383 MB, 0 = unlimited).
                        type: int
            oversize_log:
                description:
                    - Enable/disable logging for antivirus oversize file blocking.
                type: str
                choices:
                    - disable
                    - enable
            pop3:
                description:
                    - Configure POP3 protocol options.
                type: dict
                suboptions:
                    inspect_all:
                        description:
                            - Enable/disable the inspection of all ports for the protocol.
                        type: str
                        choices:
                            - enable
                            - disable
                    options:
                        description:
                            - One or more options that can be applied to the session.
                        type: str
                        choices:
                            - fragmail
                            - oversize
                    oversize_limit:
                        description:
                            - Maximum in-memory file size that can be scanned (1 - 383 MB).
                        type: int
                    ports:
                        description:
                            - Ports to scan for content (1 - 65535).
                        type: int
                    scan_bzip2:
                        description:
                            - Enable/disable scanning of BZip2 compressed files.
                        type: str
                        choices:
                            - enable
                            - disable
                    status:
                        description:
                            - Enable/disable the active status of scanning for this protocol.
                        type: str
                        choices:
                            - enable
                            - disable
                    uncompressed_nest_limit:
                        description:
                            - Maximum nested levels of compression that can be uncompressed and scanned (2 - 100).
                        type: int
                    uncompressed_oversize_limit:
                        description:
                            - Maximum in-memory uncompressed file size that can be scanned (0 - 383 MB, 0 = unlimited).
                        type: int
            replacemsg_group:
                description:
                    - Name of the replacement message group to be used Source system.replacemsg-group.name.
                type: str
            rpc_over_http:
                description:
                    - Enable/disable inspection of RPC over HTTP.
                type: str
                choices:
                    - enable
                    - disable
            smtp:
                description:
                    - Configure SMTP protocol options.
                type: dict
                suboptions:
                    inspect_all:
                        description:
                            - Enable/disable the inspection of all ports for the protocol.
                        type: str
                        choices:
                            - enable
                            - disable
                    options:
                        description:
                            - One or more options that can be applied to the session.
                        type: str
                        choices:
                            - fragmail
                            - oversize
                            - splice
                    oversize_limit:
                        description:
                            - Maximum in-memory file size that can be scanned (1 - 383 MB).
                        type: int
                    ports:
                        description:
                            - Ports to scan for content (1 - 65535).
                        type: int
                    scan_bzip2:
                        description:
                            - Enable/disable scanning of BZip2 compressed files.
                        type: str
                        choices:
                            - enable
                            - disable
                    server_busy:
                        description:
                            - Enable/disable SMTP server busy when server not available.
                        type: str
                        choices:
                            - enable
                            - disable
                    status:
                        description:
                            - Enable/disable the active status of scanning for this protocol.
                        type: str
                        choices:
                            - enable
                            - disable
                    uncompressed_nest_limit:
                        description:
                            - Maximum nested levels of compression that can be uncompressed and scanned (2 - 100).
                        type: int
                    uncompressed_oversize_limit:
                        description:
                            - Maximum in-memory uncompressed file size that can be scanned (0 - 383 MB, 0 = unlimited).
                        type: int
            switching_protocols_log:
                description:
                    - Enable/disable logging for HTTP/HTTPS switching protocols.
                type: str
                choices:
                    - disable
                    - enable
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
  - name: Configure protocol options.
    fortios_firewall_profile_protocol_options:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      firewall_profile_protocol_options:
        comment: "Optional comments."
        dns:
            ports: "5"
            status: "enable"
        ftp:
            comfort_amount: "8"
            comfort_interval: "9"
            inspect_all: "enable"
            options: "clientcomfort"
            oversize_limit: "12"
            ports: "13"
            scan_bzip2: "enable"
            status: "enable"
            uncompressed_nest_limit: "16"
            uncompressed_oversize_limit: "17"
        http:
            block_page_status_code: "19"
            comfort_amount: "20"
            comfort_interval: "21"
            fortinet_bar: "enable"
            fortinet_bar_port: "23"
            http_policy: "disable"
            inspect_all: "enable"
            options: "clientcomfort"
            oversize_limit: "27"
            ports: "28"
            post_lang: "jisx0201"
            range_block: "disable"
            retry_count: "31"
            scan_bzip2: "enable"
            status: "enable"
            streaming_content_bypass: "enable"
            strip_x_forwarded_for: "disable"
            switching_protocols: "bypass"
            uncompressed_nest_limit: "37"
            uncompressed_oversize_limit: "38"
        imap:
            inspect_all: "enable"
            options: "fragmail"
            oversize_limit: "42"
            ports: "43"
            scan_bzip2: "enable"
            status: "enable"
            uncompressed_nest_limit: "46"
            uncompressed_oversize_limit: "47"
        mail_signature:
            signature: "<your_own_value>"
            status: "disable"
        mapi:
            options: "fragmail"
            oversize_limit: "53"
            ports: "54"
            scan_bzip2: "enable"
            status: "enable"
            uncompressed_nest_limit: "57"
            uncompressed_oversize_limit: "58"
        name: "default_name_59"
        nntp:
            inspect_all: "enable"
            options: "oversize"
            oversize_limit: "63"
            ports: "64"
            scan_bzip2: "enable"
            status: "enable"
            uncompressed_nest_limit: "67"
            uncompressed_oversize_limit: "68"
        oversize_log: "disable"
        pop3:
            inspect_all: "enable"
            options: "fragmail"
            oversize_limit: "73"
            ports: "74"
            scan_bzip2: "enable"
            status: "enable"
            uncompressed_nest_limit: "77"
            uncompressed_oversize_limit: "78"
        replacemsg_group: "<your_own_value> (source system.replacemsg-group.name)"
        rpc_over_http: "enable"
        smtp:
            inspect_all: "enable"
            options: "fragmail"
            oversize_limit: "84"
            ports: "85"
            scan_bzip2: "enable"
            server_busy: "enable"
            status: "enable"
            uncompressed_nest_limit: "89"
            uncompressed_oversize_limit: "90"
        switching_protocols_log: "disable"
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


def filter_firewall_profile_protocol_options_data(json):
    option_list = ['comment', 'dns', 'ftp',
                   'http', 'imap', 'mail_signature',
                   'mapi', 'name', 'nntp',
                   'oversize_log', 'pop3', 'replacemsg_group',
                   'rpc_over_http', 'smtp', 'switching_protocols_log']
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


def firewall_profile_protocol_options(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['firewall_profile_protocol_options'] and data['firewall_profile_protocol_options']:
        state = data['firewall_profile_protocol_options']['state']
    else:
        state = True
    firewall_profile_protocol_options_data = data['firewall_profile_protocol_options']
    filtered_data = underscore_to_hyphen(filter_firewall_profile_protocol_options_data(firewall_profile_protocol_options_data))

    if state == "present":
        return fos.set('firewall',
                       'profile-protocol-options',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('firewall',
                          'profile-protocol-options',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_firewall(data, fos):

    if data['firewall_profile_protocol_options']:
        resp = firewall_profile_protocol_options(data, fos)

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
        "firewall_profile_protocol_options": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "comment": {"required": False, "type": "str"},
                "dns": {"required": False, "type": "dict",
                        "options": {
                            "ports": {"required": False, "type": "int"},
                            "status": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]}
                        }},
                "ftp": {"required": False, "type": "dict",
                        "options": {
                            "comfort_amount": {"required": False, "type": "int"},
                            "comfort_interval": {"required": False, "type": "int"},
                            "inspect_all": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                            "options": {"required": False, "type": "str",
                                        "choices": ["clientcomfort", "oversize", "splice",
                                                    "bypass-rest-command", "bypass-mode-command"]},
                            "oversize_limit": {"required": False, "type": "int"},
                            "ports": {"required": False, "type": "int"},
                            "scan_bzip2": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                            "status": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                            "uncompressed_nest_limit": {"required": False, "type": "int"},
                            "uncompressed_oversize_limit": {"required": False, "type": "int"}
                        }},
                "http": {"required": False, "type": "dict",
                         "options": {
                             "block_page_status_code": {"required": False, "type": "int"},
                             "comfort_amount": {"required": False, "type": "int"},
                             "comfort_interval": {"required": False, "type": "int"},
                             "fortinet_bar": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                             "fortinet_bar_port": {"required": False, "type": "int"},
                             "http_policy": {"required": False, "type": "str",
                                             "choices": ["disable", "enable"]},
                             "inspect_all": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                             "options": {"required": False, "type": "str",
                                         "choices": ["clientcomfort", "servercomfort", "oversize",
                                                     "chunkedbypass"]},
                             "oversize_limit": {"required": False, "type": "int"},
                             "ports": {"required": False, "type": "int"},
                             "post_lang": {"required": False, "type": "str",
                                           "choices": ["jisx0201", "jisx0208", "jisx0212",
                                                       "gb2312", "ksc5601-ex", "euc-jp",
                                                       "sjis", "iso2022-jp", "iso2022-jp-1",
                                                       "iso2022-jp-2", "euc-cn", "ces-gbk",
                                                       "hz", "ces-big5", "euc-kr",
                                                       "iso2022-jp-3", "iso8859-1", "tis620",
                                                       "cp874", "cp1252", "cp1251"]},
                             "range_block": {"required": False, "type": "str",
                                             "choices": ["disable", "enable"]},
                             "retry_count": {"required": False, "type": "int"},
                             "scan_bzip2": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                             "status": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                             "streaming_content_bypass": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]},
                             "strip_x_forwarded_for": {"required": False, "type": "str",
                                                       "choices": ["disable", "enable"]},
                             "switching_protocols": {"required": False, "type": "str",
                                                     "choices": ["bypass", "block"]},
                             "uncompressed_nest_limit": {"required": False, "type": "int"},
                             "uncompressed_oversize_limit": {"required": False, "type": "int"}
                         }},
                "imap": {"required": False, "type": "dict",
                         "options": {
                             "inspect_all": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                             "options": {"required": False, "type": "str",
                                         "choices": ["fragmail", "oversize"]},
                             "oversize_limit": {"required": False, "type": "int"},
                             "ports": {"required": False, "type": "int"},
                             "scan_bzip2": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                             "status": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                             "uncompressed_nest_limit": {"required": False, "type": "int"},
                             "uncompressed_oversize_limit": {"required": False, "type": "int"}
                         }},
                "mail_signature": {"required": False, "type": "dict",
                                   "options": {
                                       "signature": {"required": False, "type": "str"},
                                       "status": {"required": False, "type": "str",
                                                  "choices": ["disable", "enable"]}
                                   }},
                "mapi": {"required": False, "type": "dict",
                         "options": {
                             "options": {"required": False, "type": "str",
                                         "choices": ["fragmail", "oversize"]},
                             "oversize_limit": {"required": False, "type": "int"},
                             "ports": {"required": False, "type": "int"},
                             "scan_bzip2": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                             "status": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                             "uncompressed_nest_limit": {"required": False, "type": "int"},
                             "uncompressed_oversize_limit": {"required": False, "type": "int"}
                         }},
                "name": {"required": True, "type": "str"},
                "nntp": {"required": False, "type": "dict",
                         "options": {
                             "inspect_all": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                             "options": {"required": False, "type": "str",
                                         "choices": ["oversize", "splice"]},
                             "oversize_limit": {"required": False, "type": "int"},
                             "ports": {"required": False, "type": "int"},
                             "scan_bzip2": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                             "status": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                             "uncompressed_nest_limit": {"required": False, "type": "int"},
                             "uncompressed_oversize_limit": {"required": False, "type": "int"}
                         }},
                "oversize_log": {"required": False, "type": "str",
                                 "choices": ["disable", "enable"]},
                "pop3": {"required": False, "type": "dict",
                         "options": {
                             "inspect_all": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                             "options": {"required": False, "type": "str",
                                         "choices": ["fragmail", "oversize"]},
                             "oversize_limit": {"required": False, "type": "int"},
                             "ports": {"required": False, "type": "int"},
                             "scan_bzip2": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                             "status": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                             "uncompressed_nest_limit": {"required": False, "type": "int"},
                             "uncompressed_oversize_limit": {"required": False, "type": "int"}
                         }},
                "replacemsg_group": {"required": False, "type": "str"},
                "rpc_over_http": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "smtp": {"required": False, "type": "dict",
                         "options": {
                             "inspect_all": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                             "options": {"required": False, "type": "str",
                                         "choices": ["fragmail", "oversize", "splice"]},
                             "oversize_limit": {"required": False, "type": "int"},
                             "ports": {"required": False, "type": "int"},
                             "scan_bzip2": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                             "server_busy": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                             "status": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                             "uncompressed_nest_limit": {"required": False, "type": "int"},
                             "uncompressed_oversize_limit": {"required": False, "type": "int"}
                         }},
                "switching_protocols_log": {"required": False, "type": "str",
                                            "choices": ["disable", "enable"]}

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

            is_error, has_changed, result = fortios_firewall(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_firewall(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
