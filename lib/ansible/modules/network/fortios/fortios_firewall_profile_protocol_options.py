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
#
# the lib use python logging can get it if the following is set in your
# Ansible config.

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_firewall_profile_protocol_options
short_description: Configure protocol options in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall feature and profile_protocol_options category.
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
        default: true
    firewall_profile_protocol_options:
        description:
            - Configure protocol options.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            comment:
                description:
                    - Optional comments.
            dns:
                description:
                    - Configure DNS protocol options.
                suboptions:
                    ports:
                        description:
                            - Ports to scan for content (1 - 65535, default = 53).
                    status:
                        description:
                            - Enable/disable the active status of scanning for this protocol.
                        choices:
                            - enable
                            - disable
            ftp:
                description:
                    - Configure FTP protocol options.
                suboptions:
                    comfort-amount:
                        description:
                            - Amount of data to send in a transmission for client comforting (1 - 10240 bytes, default = 1).
                    comfort-interval:
                        description:
                            - Period of time between start, or last transmission, and the next client comfort transmission of data (1 - 900 sec, default = 10).
                    inspect-all:
                        description:
                            - Enable/disable the inspection of all ports for the protocol.
                        choices:
                            - enable
                            - disable
                    options:
                        description:
                            - One or more options that can be applied to the session.
                        choices:
                            - clientcomfort
                            - oversize
                            - splice
                            - bypass-rest-command
                            - bypass-mode-command
                    oversize-limit:
                        description:
                            - Maximum in-memory file size that can be scanned (1 - 383 MB, default = 10).
                    ports:
                        description:
                            - Ports to scan for content (1 - 65535, default = 21).
                    scan-bzip2:
                        description:
                            - Enable/disable scanning of BZip2 compressed files.
                        choices:
                            - enable
                            - disable
                    status:
                        description:
                            - Enable/disable the active status of scanning for this protocol.
                        choices:
                            - enable
                            - disable
                    uncompressed-nest-limit:
                        description:
                            - Maximum nested levels of compression that can be uncompressed and scanned (2 - 100, default = 12).
                    uncompressed-oversize-limit:
                        description:
                            - Maximum in-memory uncompressed file size that can be scanned (0 - 383 MB, 0 = unlimited, default = 10).
            http:
                description:
                    - Configure HTTP protocol options.
                suboptions:
                    block-page-status-code:
                        description:
                            - Code number returned for blocked HTTP pages (non-FortiGuard only) (100 - 599, default = 403).
                    comfort-amount:
                        description:
                            - Amount of data to send in a transmission for client comforting (1 - 10240 bytes, default = 1).
                    comfort-interval:
                        description:
                            - Period of time between start, or last transmission, and the next client comfort transmission of data (1 - 900 sec, default = 10).
                    fortinet-bar:
                        description:
                            - Enable/disable Fortinet bar on HTML content.
                        choices:
                            - enable
                            - disable
                    fortinet-bar-port:
                        description:
                            - Port for use by Fortinet Bar (1 - 65535, default = 8011).
                    http-policy:
                        description:
                            - Enable/disable HTTP policy check.
                        choices:
                            - disable
                            - enable
                    inspect-all:
                        description:
                            - Enable/disable the inspection of all ports for the protocol.
                        choices:
                            - enable
                            - disable
                    options:
                        description:
                            - One or more options that can be applied to the session.
                        choices:
                            - clientcomfort
                            - servercomfort
                            - oversize
                            - chunkedbypass
                    oversize-limit:
                        description:
                            - Maximum in-memory file size that can be scanned (1 - 383 MB, default = 10).
                    ports:
                        description:
                            - Ports to scan for content (1 - 65535, default = 80).
                    post-lang:
                        description:
                            - ID codes for character sets to be used to convert to UTF-8 for banned words and DLP on HTTP posts (maximum of 5 character sets).
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
                    range-block:
                        description:
                            - Enable/disable blocking of partial downloads.
                        choices:
                            - disable
                            - enable
                    retry-count:
                        description:
                            - Number of attempts to retry HTTP connection (0 - 100, default = 0).
                    scan-bzip2:
                        description:
                            - Enable/disable scanning of BZip2 compressed files.
                        choices:
                            - enable
                            - disable
                    status:
                        description:
                            - Enable/disable the active status of scanning for this protocol.
                        choices:
                            - enable
                            - disable
                    streaming-content-bypass:
                        description:
                            - Enable/disable bypassing of streaming content from buffering.
                        choices:
                            - enable
                            - disable
                    strip-x-forwarded-for:
                        description:
                            - Enable/disable stripping of HTTP X-Forwarded-For header.
                        choices:
                            - disable
                            - enable
                    switching-protocols:
                        description:
                            - Bypass from scanning, or block a connection that attempts to switch protocol.
                        choices:
                            - bypass
                            - block
                    uncompressed-nest-limit:
                        description:
                            - Maximum nested levels of compression that can be uncompressed and scanned (2 - 100, default = 12).
                    uncompressed-oversize-limit:
                        description:
                            - Maximum in-memory uncompressed file size that can be scanned (0 - 383 MB, 0 = unlimited, default = 10).
            imap:
                description:
                    - Configure IMAP protocol options.
                suboptions:
                    inspect-all:
                        description:
                            - Enable/disable the inspection of all ports for the protocol.
                        choices:
                            - enable
                            - disable
                    options:
                        description:
                            - One or more options that can be applied to the session.
                        choices:
                            - fragmail
                            - oversize
                    oversize-limit:
                        description:
                            - Maximum in-memory file size that can be scanned (1 - 383 MB, default = 10).
                    ports:
                        description:
                            - Ports to scan for content (1 - 65535, default = 143).
                    scan-bzip2:
                        description:
                            - Enable/disable scanning of BZip2 compressed files.
                        choices:
                            - enable
                            - disable
                    status:
                        description:
                            - Enable/disable the active status of scanning for this protocol.
                        choices:
                            - enable
                            - disable
                    uncompressed-nest-limit:
                        description:
                            - Maximum nested levels of compression that can be uncompressed and scanned (2 - 100, default = 12).
                    uncompressed-oversize-limit:
                        description:
                            - Maximum in-memory uncompressed file size that can be scanned (0 - 383 MB, 0 = unlimited, default = 10).
            mail-signature:
                description:
                    - Configure Mail signature.
                suboptions:
                    signature:
                        description:
                            - Email signature to be added to outgoing email (if the signature contains spaces, enclose with quotation marks).
                    status:
                        description:
                            - Enable/disable adding an email signature to SMTP email messages as they pass through the FortiGate.
                        choices:
                            - disable
                            - enable
            mapi:
                description:
                    - Configure MAPI protocol options.
                suboptions:
                    options:
                        description:
                            - One or more options that can be applied to the session.
                        choices:
                            - fragmail
                            - oversize
                    oversize-limit:
                        description:
                            - Maximum in-memory file size that can be scanned (1 - 383 MB, default = 10).
                    ports:
                        description:
                            - Ports to scan for content (1 - 65535, default = 135).
                    scan-bzip2:
                        description:
                            - Enable/disable scanning of BZip2 compressed files.
                        choices:
                            - enable
                            - disable
                    status:
                        description:
                            - Enable/disable the active status of scanning for this protocol.
                        choices:
                            - enable
                            - disable
                    uncompressed-nest-limit:
                        description:
                            - Maximum nested levels of compression that can be uncompressed and scanned (2 - 100, default = 12).
                    uncompressed-oversize-limit:
                        description:
                            - Maximum in-memory uncompressed file size that can be scanned (0 - 383 MB, 0 = unlimited, default = 10).
            name:
                description:
                    - Name.
                required: true
            nntp:
                description:
                    - Configure NNTP protocol options.
                suboptions:
                    inspect-all:
                        description:
                            - Enable/disable the inspection of all ports for the protocol.
                        choices:
                            - enable
                            - disable
                    options:
                        description:
                            - One or more options that can be applied to the session.
                        choices:
                            - oversize
                            - splice
                    oversize-limit:
                        description:
                            - Maximum in-memory file size that can be scanned (1 - 383 MB, default = 10).
                    ports:
                        description:
                            - Ports to scan for content (1 - 65535, default = 119).
                    scan-bzip2:
                        description:
                            - Enable/disable scanning of BZip2 compressed files.
                        choices:
                            - enable
                            - disable
                    status:
                        description:
                            - Enable/disable the active status of scanning for this protocol.
                        choices:
                            - enable
                            - disable
                    uncompressed-nest-limit:
                        description:
                            - Maximum nested levels of compression that can be uncompressed and scanned (2 - 100, default = 12).
                    uncompressed-oversize-limit:
                        description:
                            - Maximum in-memory uncompressed file size that can be scanned (0 - 383 MB, 0 = unlimited, default = 10).
            oversize-log:
                description:
                    - Enable/disable logging for antivirus oversize file blocking.
                choices:
                    - disable
                    - enable
            pop3:
                description:
                    - Configure POP3 protocol options.
                suboptions:
                    inspect-all:
                        description:
                            - Enable/disable the inspection of all ports for the protocol.
                        choices:
                            - enable
                            - disable
                    options:
                        description:
                            - One or more options that can be applied to the session.
                        choices:
                            - fragmail
                            - oversize
                    oversize-limit:
                        description:
                            - Maximum in-memory file size that can be scanned (1 - 383 MB, default = 10).
                    ports:
                        description:
                            - Ports to scan for content (1 - 65535, default = 110).
                    scan-bzip2:
                        description:
                            - Enable/disable scanning of BZip2 compressed files.
                        choices:
                            - enable
                            - disable
                    status:
                        description:
                            - Enable/disable the active status of scanning for this protocol.
                        choices:
                            - enable
                            - disable
                    uncompressed-nest-limit:
                        description:
                            - Maximum nested levels of compression that can be uncompressed and scanned (2 - 100, default = 12).
                    uncompressed-oversize-limit:
                        description:
                            - Maximum in-memory uncompressed file size that can be scanned (0 - 383 MB, 0 = unlimited, default = 10).
            replacemsg-group:
                description:
                    - Name of the replacement message group to be used Source system.replacemsg-group.name.
            rpc-over-http:
                description:
                    - Enable/disable inspection of RPC over HTTP.
                choices:
                    - enable
                    - disable
            smtp:
                description:
                    - Configure SMTP protocol options.
                suboptions:
                    inspect-all:
                        description:
                            - Enable/disable the inspection of all ports for the protocol.
                        choices:
                            - enable
                            - disable
                    options:
                        description:
                            - One or more options that can be applied to the session.
                        choices:
                            - fragmail
                            - oversize
                            - splice
                    oversize-limit:
                        description:
                            - Maximum in-memory file size that can be scanned (1 - 383 MB, default = 10).
                    ports:
                        description:
                            - Ports to scan for content (1 - 65535, default = 25).
                    scan-bzip2:
                        description:
                            - Enable/disable scanning of BZip2 compressed files.
                        choices:
                            - enable
                            - disable
                    server-busy:
                        description:
                            - Enable/disable SMTP server busy when server not available.
                        choices:
                            - enable
                            - disable
                    status:
                        description:
                            - Enable/disable the active status of scanning for this protocol.
                        choices:
                            - enable
                            - disable
                    uncompressed-nest-limit:
                        description:
                            - Maximum nested levels of compression that can be uncompressed and scanned (2 - 100, default = 12).
                    uncompressed-oversize-limit:
                        description:
                            - Maximum in-memory uncompressed file size that can be scanned (0 - 383 MB, 0 = unlimited, default = 10).
            switching-protocols-log:
                description:
                    - Enable/disable logging for HTTP/HTTPS switching protocols.
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
  tasks:
  - name: Configure protocol options.
    fortios_firewall_profile_protocol_options:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      firewall_profile_protocol_options:
        state: "present"
        comment: "Optional comments."
        dns:
            ports: "5"
            status: "enable"
        ftp:
            comfort-amount: "8"
            comfort-interval: "9"
            inspect-all: "enable"
            options: "clientcomfort"
            oversize-limit: "12"
            ports: "13"
            scan-bzip2: "enable"
            status: "enable"
            uncompressed-nest-limit: "16"
            uncompressed-oversize-limit: "17"
        http:
            block-page-status-code: "19"
            comfort-amount: "20"
            comfort-interval: "21"
            fortinet-bar: "enable"
            fortinet-bar-port: "23"
            http-policy: "disable"
            inspect-all: "enable"
            options: "clientcomfort"
            oversize-limit: "27"
            ports: "28"
            post-lang: "jisx0201"
            range-block: "disable"
            retry-count: "31"
            scan-bzip2: "enable"
            status: "enable"
            streaming-content-bypass: "enable"
            strip-x-forwarded-for: "disable"
            switching-protocols: "bypass"
            uncompressed-nest-limit: "37"
            uncompressed-oversize-limit: "38"
        imap:
            inspect-all: "enable"
            options: "fragmail"
            oversize-limit: "42"
            ports: "43"
            scan-bzip2: "enable"
            status: "enable"
            uncompressed-nest-limit: "46"
            uncompressed-oversize-limit: "47"
        mail-signature:
            signature: "<your_own_value>"
            status: "disable"
        mapi:
            options: "fragmail"
            oversize-limit: "53"
            ports: "54"
            scan-bzip2: "enable"
            status: "enable"
            uncompressed-nest-limit: "57"
            uncompressed-oversize-limit: "58"
        name: "default_name_59"
        nntp:
            inspect-all: "enable"
            options: "oversize"
            oversize-limit: "63"
            ports: "64"
            scan-bzip2: "enable"
            status: "enable"
            uncompressed-nest-limit: "67"
            uncompressed-oversize-limit: "68"
        oversize-log: "disable"
        pop3:
            inspect-all: "enable"
            options: "fragmail"
            oversize-limit: "73"
            ports: "74"
            scan-bzip2: "enable"
            status: "enable"
            uncompressed-nest-limit: "77"
            uncompressed-oversize-limit: "78"
        replacemsg-group: "<your_own_value> (source system.replacemsg-group.name)"
        rpc-over-http: "enable"
        smtp:
            inspect-all: "enable"
            options: "fragmail"
            oversize-limit: "84"
            ports: "85"
            scan-bzip2: "enable"
            server-busy: "enable"
            status: "enable"
            uncompressed-nest-limit: "89"
            uncompressed-oversize-limit: "90"
        switching-protocols-log: "disable"
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


def filter_firewall_profile_protocol_options_data(json):
    option_list = ['comment', 'dns', 'ftp',
                   'http', 'imap', 'mail-signature',
                   'mapi', 'name', 'nntp',
                   'oversize-log', 'pop3', 'replacemsg-group',
                   'rpc-over-http', 'smtp', 'switching-protocols-log']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_profile_protocol_options(data, fos):
    vdom = data['vdom']
    firewall_profile_protocol_options_data = data['firewall_profile_protocol_options']
    filtered_data = filter_firewall_profile_protocol_options_data(firewall_profile_protocol_options_data)
    if firewall_profile_protocol_options_data['state'] == "present":
        return fos.set('firewall',
                       'profile-protocol-options',
                       data=filtered_data,
                       vdom=vdom)

    elif firewall_profile_protocol_options_data['state'] == "absent":
        return fos.delete('firewall',
                          'profile-protocol-options',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_firewall(data, fos):
    login(data)

    methodlist = ['firewall_profile_protocol_options']
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
        "https": {"required": False, "type": "bool", "default": True},
        "firewall_profile_protocol_options": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
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
                            "comfort-amount": {"required": False, "type": "int"},
                            "comfort-interval": {"required": False, "type": "int"},
                            "inspect-all": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                            "options": {"required": False, "type": "str",
                                        "choices": ["clientcomfort", "oversize", "splice",
                                                    "bypass-rest-command", "bypass-mode-command"]},
                            "oversize-limit": {"required": False, "type": "int"},
                            "ports": {"required": False, "type": "int"},
                            "scan-bzip2": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                            "status": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                            "uncompressed-nest-limit": {"required": False, "type": "int"},
                            "uncompressed-oversize-limit": {"required": False, "type": "int"}
                        }},
                "http": {"required": False, "type": "dict",
                         "options": {
                             "block-page-status-code": {"required": False, "type": "int"},
                             "comfort-amount": {"required": False, "type": "int"},
                             "comfort-interval": {"required": False, "type": "int"},
                             "fortinet-bar": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                             "fortinet-bar-port": {"required": False, "type": "int"},
                             "http-policy": {"required": False, "type": "str",
                                             "choices": ["disable", "enable"]},
                             "inspect-all": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                             "options": {"required": False, "type": "str",
                                         "choices": ["clientcomfort", "servercomfort", "oversize",
                                                     "chunkedbypass"]},
                             "oversize-limit": {"required": False, "type": "int"},
                             "ports": {"required": False, "type": "int"},
                             "post-lang": {"required": False, "type": "str",
                                           "choices": ["jisx0201", "jisx0208", "jisx0212",
                                                       "gb2312", "ksc5601-ex", "euc-jp",
                                                       "sjis", "iso2022-jp", "iso2022-jp-1",
                                                       "iso2022-jp-2", "euc-cn", "ces-gbk",
                                                       "hz", "ces-big5", "euc-kr",
                                                       "iso2022-jp-3", "iso8859-1", "tis620",
                                                       "cp874", "cp1252", "cp1251"]},
                             "range-block": {"required": False, "type": "str",
                                             "choices": ["disable", "enable"]},
                             "retry-count": {"required": False, "type": "int"},
                             "scan-bzip2": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                             "status": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                             "streaming-content-bypass": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]},
                             "strip-x-forwarded-for": {"required": False, "type": "str",
                                                       "choices": ["disable", "enable"]},
                             "switching-protocols": {"required": False, "type": "str",
                                                     "choices": ["bypass", "block"]},
                             "uncompressed-nest-limit": {"required": False, "type": "int"},
                             "uncompressed-oversize-limit": {"required": False, "type": "int"}
                         }},
                "imap": {"required": False, "type": "dict",
                         "options": {
                             "inspect-all": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                             "options": {"required": False, "type": "str",
                                         "choices": ["fragmail", "oversize"]},
                             "oversize-limit": {"required": False, "type": "int"},
                             "ports": {"required": False, "type": "int"},
                             "scan-bzip2": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                             "status": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                             "uncompressed-nest-limit": {"required": False, "type": "int"},
                             "uncompressed-oversize-limit": {"required": False, "type": "int"}
                         }},
                "mail-signature": {"required": False, "type": "dict",
                                   "options": {
                                       "signature": {"required": False, "type": "str"},
                                       "status": {"required": False, "type": "str",
                                                  "choices": ["disable", "enable"]}
                                   }},
                "mapi": {"required": False, "type": "dict",
                         "options": {
                             "options": {"required": False, "type": "str",
                                         "choices": ["fragmail", "oversize"]},
                             "oversize-limit": {"required": False, "type": "int"},
                             "ports": {"required": False, "type": "int"},
                             "scan-bzip2": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                             "status": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                             "uncompressed-nest-limit": {"required": False, "type": "int"},
                             "uncompressed-oversize-limit": {"required": False, "type": "int"}
                         }},
                "name": {"required": True, "type": "str"},
                "nntp": {"required": False, "type": "dict",
                         "options": {
                             "inspect-all": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                             "options": {"required": False, "type": "str",
                                         "choices": ["oversize", "splice"]},
                             "oversize-limit": {"required": False, "type": "int"},
                             "ports": {"required": False, "type": "int"},
                             "scan-bzip2": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                             "status": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                             "uncompressed-nest-limit": {"required": False, "type": "int"},
                             "uncompressed-oversize-limit": {"required": False, "type": "int"}
                         }},
                "oversize-log": {"required": False, "type": "str",
                                 "choices": ["disable", "enable"]},
                "pop3": {"required": False, "type": "dict",
                         "options": {
                             "inspect-all": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                             "options": {"required": False, "type": "str",
                                         "choices": ["fragmail", "oversize"]},
                             "oversize-limit": {"required": False, "type": "int"},
                             "ports": {"required": False, "type": "int"},
                             "scan-bzip2": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                             "status": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                             "uncompressed-nest-limit": {"required": False, "type": "int"},
                             "uncompressed-oversize-limit": {"required": False, "type": "int"}
                         }},
                "replacemsg-group": {"required": False, "type": "str"},
                "rpc-over-http": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "smtp": {"required": False, "type": "dict",
                         "options": {
                             "inspect-all": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                             "options": {"required": False, "type": "str",
                                         "choices": ["fragmail", "oversize", "splice"]},
                             "oversize-limit": {"required": False, "type": "int"},
                             "ports": {"required": False, "type": "int"},
                             "scan-bzip2": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                             "server-busy": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                             "status": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                             "uncompressed-nest-limit": {"required": False, "type": "int"},
                             "uncompressed-oversize-limit": {"required": False, "type": "int"}
                         }},
                "switching-protocols-log": {"required": False, "type": "str",
                                            "choices": ["disable", "enable"]}

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

    is_error, has_changed, result = fortios_firewall(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
