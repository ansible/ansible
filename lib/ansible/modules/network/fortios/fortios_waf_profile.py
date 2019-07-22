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
module: fortios_waf_profile
short_description: Web application firewall configuration in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify waf feature and profile category.
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
    waf_profile:
        description:
            - Web application firewall configuration.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            address-list:
                description:
                    - Black address list and white address list.
                suboptions:
                    blocked-address:
                        description:
                            - Blocked address.
                        suboptions:
                            name:
                                description:
                                    - Address name. Source firewall.address.name firewall.addrgrp.name.
                                required: true
                    blocked-log:
                        description:
                            - Enable/disable logging on blocked addresses.
                        choices:
                            - enable
                            - disable
                    severity:
                        description:
                            - Severity.
                        choices:
                            - high
                            - medium
                            - low
                    status:
                        description:
                            - Status.
                        choices:
                            - enable
                            - disable
                    trusted-address:
                        description:
                            - Trusted address.
                        suboptions:
                            name:
                                description:
                                    - Address name. Source firewall.address.name firewall.addrgrp.name.
                                required: true
            comment:
                description:
                    - Comment.
            constraint:
                description:
                    - WAF HTTP protocol restrictions.
                suboptions:
                    content-length:
                        description:
                            - HTTP content length in request.
                        suboptions:
                            action:
                                description:
                                    - Action.
                                choices:
                                    - allow
                                    - block
                            length:
                                description:
                                    - Length of HTTP content in bytes (0 to 2147483647).
                            log:
                                description:
                                    - Enable/disable logging.
                                choices:
                                    - enable
                                    - disable
                            severity:
                                description:
                                    - Severity.
                                choices:
                                    - high
                                    - medium
                                    - low
                            status:
                                description:
                                    - Enable/disable the constraint.
                                choices:
                                    - enable
                                    - disable
                    exception:
                        description:
                            - HTTP constraint exception.
                        suboptions:
                            address:
                                description:
                                    - Host address. Source firewall.address.name firewall.addrgrp.name.
                            content-length:
                                description:
                                    - HTTP content length in request.
                                choices:
                                    - enable
                                    - disable
                            header-length:
                                description:
                                    - HTTP header length in request.
                                choices:
                                    - enable
                                    - disable
                            hostname:
                                description:
                                    - Enable/disable hostname check.
                                choices:
                                    - enable
                                    - disable
                            id:
                                description:
                                    - Exception ID.
                                required: true
                            line-length:
                                description:
                                    - HTTP line length in request.
                                choices:
                                    - enable
                                    - disable
                            malformed:
                                description:
                                    - Enable/disable malformed HTTP request check.
                                choices:
                                    - enable
                                    - disable
                            max-cookie:
                                description:
                                    - Maximum number of cookies in HTTP request.
                                choices:
                                    - enable
                                    - disable
                            max-header-line:
                                description:
                                    - Maximum number of HTTP header line.
                                choices:
                                    - enable
                                    - disable
                            max-range-segment:
                                description:
                                    - Maximum number of range segments in HTTP range line.
                                choices:
                                    - enable
                                    - disable
                            max-url-param:
                                description:
                                    - Maximum number of parameters in URL.
                                choices:
                                    - enable
                                    - disable
                            method:
                                description:
                                    - Enable/disable HTTP method check.
                                choices:
                                    - enable
                                    - disable
                            param-length:
                                description:
                                    - Maximum length of parameter in URL, HTTP POST request or HTTP body.
                                choices:
                                    - enable
                                    - disable
                            pattern:
                                description:
                                    - URL pattern.
                            regex:
                                description:
                                    - Enable/disable regular expression based pattern match.
                                choices:
                                    - enable
                                    - disable
                            url-param-length:
                                description:
                                    - Maximum length of parameter in URL.
                                choices:
                                    - enable
                                    - disable
                            version:
                                description:
                                    - Enable/disable HTTP version check.
                                choices:
                                    - enable
                                    - disable
                    header-length:
                        description:
                            - HTTP header length in request.
                        suboptions:
                            action:
                                description:
                                    - Action.
                                choices:
                                    - allow
                                    - block
                            length:
                                description:
                                    - Length of HTTP header in bytes (0 to 2147483647).
                            log:
                                description:
                                    - Enable/disable logging.
                                choices:
                                    - enable
                                    - disable
                            severity:
                                description:
                                    - Severity.
                                choices:
                                    - high
                                    - medium
                                    - low
                            status:
                                description:
                                    - Enable/disable the constraint.
                                choices:
                                    - enable
                                    - disable
                    hostname:
                        description:
                            - Enable/disable hostname check.
                        suboptions:
                            action:
                                description:
                                    - Action.
                                choices:
                                    - allow
                                    - block
                            log:
                                description:
                                    - Enable/disable logging.
                                choices:
                                    - enable
                                    - disable
                            severity:
                                description:
                                    - Severity.
                                choices:
                                    - high
                                    - medium
                                    - low
                            status:
                                description:
                                    - Enable/disable the constraint.
                                choices:
                                    - enable
                                    - disable
                    line-length:
                        description:
                            - HTTP line length in request.
                        suboptions:
                            action:
                                description:
                                    - Action.
                                choices:
                                    - allow
                                    - block
                            length:
                                description:
                                    - Length of HTTP line in bytes (0 to 2147483647).
                            log:
                                description:
                                    - Enable/disable logging.
                                choices:
                                    - enable
                                    - disable
                            severity:
                                description:
                                    - Severity.
                                choices:
                                    - high
                                    - medium
                                    - low
                            status:
                                description:
                                    - Enable/disable the constraint.
                                choices:
                                    - enable
                                    - disable
                    malformed:
                        description:
                            - Enable/disable malformed HTTP request check.
                        suboptions:
                            action:
                                description:
                                    - Action.
                                choices:
                                    - allow
                                    - block
                            log:
                                description:
                                    - Enable/disable logging.
                                choices:
                                    - enable
                                    - disable
                            severity:
                                description:
                                    - Severity.
                                choices:
                                    - high
                                    - medium
                                    - low
                            status:
                                description:
                                    - Enable/disable the constraint.
                                choices:
                                    - enable
                                    - disable
                    max-cookie:
                        description:
                            - Maximum number of cookies in HTTP request.
                        suboptions:
                            action:
                                description:
                                    - Action.
                                choices:
                                    - allow
                                    - block
                            log:
                                description:
                                    - Enable/disable logging.
                                choices:
                                    - enable
                                    - disable
                            max-cookie:
                                description:
                                    - Maximum number of cookies in HTTP request (0 to 2147483647).
                            severity:
                                description:
                                    - Severity.
                                choices:
                                    - high
                                    - medium
                                    - low
                            status:
                                description:
                                    - Enable/disable the constraint.
                                choices:
                                    - enable
                                    - disable
                    max-header-line:
                        description:
                            - Maximum number of HTTP header line.
                        suboptions:
                            action:
                                description:
                                    - Action.
                                choices:
                                    - allow
                                    - block
                            log:
                                description:
                                    - Enable/disable logging.
                                choices:
                                    - enable
                                    - disable
                            max-header-line:
                                description:
                                    - Maximum number HTTP header lines (0 to 2147483647).
                            severity:
                                description:
                                    - Severity.
                                choices:
                                    - high
                                    - medium
                                    - low
                            status:
                                description:
                                    - Enable/disable the constraint.
                                choices:
                                    - enable
                                    - disable
                    max-range-segment:
                        description:
                            - Maximum number of range segments in HTTP range line.
                        suboptions:
                            action:
                                description:
                                    - Action.
                                choices:
                                    - allow
                                    - block
                            log:
                                description:
                                    - Enable/disable logging.
                                choices:
                                    - enable
                                    - disable
                            max-range-segment:
                                description:
                                    - Maximum number of range segments in HTTP range line (0 to 2147483647).
                            severity:
                                description:
                                    - Severity.
                                choices:
                                    - high
                                    - medium
                                    - low
                            status:
                                description:
                                    - Enable/disable the constraint.
                                choices:
                                    - enable
                                    - disable
                    max-url-param:
                        description:
                            - Maximum number of parameters in URL.
                        suboptions:
                            action:
                                description:
                                    - Action.
                                choices:
                                    - allow
                                    - block
                            log:
                                description:
                                    - Enable/disable logging.
                                choices:
                                    - enable
                                    - disable
                            max-url-param:
                                description:
                                    - Maximum number of parameters in URL (0 to 2147483647).
                            severity:
                                description:
                                    - Severity.
                                choices:
                                    - high
                                    - medium
                                    - low
                            status:
                                description:
                                    - Enable/disable the constraint.
                                choices:
                                    - enable
                                    - disable
                    method:
                        description:
                            - Enable/disable HTTP method check.
                        suboptions:
                            action:
                                description:
                                    - Action.
                                choices:
                                    - allow
                                    - block
                            log:
                                description:
                                    - Enable/disable logging.
                                choices:
                                    - enable
                                    - disable
                            severity:
                                description:
                                    - Severity.
                                choices:
                                    - high
                                    - medium
                                    - low
                            status:
                                description:
                                    - Enable/disable the constraint.
                                choices:
                                    - enable
                                    - disable
                    param-length:
                        description:
                            - Maximum length of parameter in URL, HTTP POST request or HTTP body.
                        suboptions:
                            action:
                                description:
                                    - Action.
                                choices:
                                    - allow
                                    - block
                            length:
                                description:
                                    - Maximum length of parameter in URL, HTTP POST request or HTTP body in bytes (0 to 2147483647).
                            log:
                                description:
                                    - Enable/disable logging.
                                choices:
                                    - enable
                                    - disable
                            severity:
                                description:
                                    - Severity.
                                choices:
                                    - high
                                    - medium
                                    - low
                            status:
                                description:
                                    - Enable/disable the constraint.
                                choices:
                                    - enable
                                    - disable
                    url-param-length:
                        description:
                            - Maximum length of parameter in URL.
                        suboptions:
                            action:
                                description:
                                    - Action.
                                choices:
                                    - allow
                                    - block
                            length:
                                description:
                                    - Maximum length of URL parameter in bytes (0 to 2147483647).
                            log:
                                description:
                                    - Enable/disable logging.
                                choices:
                                    - enable
                                    - disable
                            severity:
                                description:
                                    - Severity.
                                choices:
                                    - high
                                    - medium
                                    - low
                            status:
                                description:
                                    - Enable/disable the constraint.
                                choices:
                                    - enable
                                    - disable
                    version:
                        description:
                            - Enable/disable HTTP version check.
                        suboptions:
                            action:
                                description:
                                    - Action.
                                choices:
                                    - allow
                                    - block
                            log:
                                description:
                                    - Enable/disable logging.
                                choices:
                                    - enable
                                    - disable
                            severity:
                                description:
                                    - Severity.
                                choices:
                                    - high
                                    - medium
                                    - low
                            status:
                                description:
                                    - Enable/disable the constraint.
                                choices:
                                    - enable
                                    - disable
            extended-log:
                description:
                    - Enable/disable extended logging.
                choices:
                    - enable
                    - disable
            external:
                description:
                    - Disable/Enable external HTTP Inspection.
                choices:
                    - disable
                    - enable
            method:
                description:
                    - Method restriction.
                suboptions:
                    default-allowed-methods:
                        description:
                            - Methods.
                        choices:
                            - get
                            - post
                            - put
                            - head
                            - connect
                            - trace
                            - options
                            - delete
                            - others
                    log:
                        description:
                            - Enable/disable logging.
                        choices:
                            - enable
                            - disable
                    method-policy:
                        description:
                            - HTTP method policy.
                        suboptions:
                            address:
                                description:
                                    - Host address. Source firewall.address.name firewall.addrgrp.name.
                            allowed-methods:
                                description:
                                    - Allowed Methods.
                                choices:
                                    - get
                                    - post
                                    - put
                                    - head
                                    - connect
                                    - trace
                                    - options
                                    - delete
                                    - others
                            id:
                                description:
                                    - HTTP method policy ID.
                                required: true
                            pattern:
                                description:
                                    - URL pattern.
                            regex:
                                description:
                                    - Enable/disable regular expression based pattern match.
                                choices:
                                    - enable
                                    - disable
                    severity:
                        description:
                            - Severity.
                        choices:
                            - high
                            - medium
                            - low
                    status:
                        description:
                            - Status.
                        choices:
                            - enable
                            - disable
            name:
                description:
                    - WAF Profile name.
                required: true
            signature:
                description:
                    - WAF signatures.
                suboptions:
                    credit-card-detection-threshold:
                        description:
                            - The minimum number of Credit cards to detect violation.
                    custom-signature:
                        description:
                            - Custom signature.
                        suboptions:
                            action:
                                description:
                                    - Action.
                                choices:
                                    - allow
                                    - block
                                    - erase
                            case-sensitivity:
                                description:
                                    - Case sensitivity in pattern.
                                choices:
                                    - disable
                                    - enable
                            direction:
                                description:
                                    - Traffic direction.
                                choices:
                                    - request
                                    - response
                            log:
                                description:
                                    - Enable/disable logging.
                                choices:
                                    - enable
                                    - disable
                            name:
                                description:
                                    - Signature name.
                                required: true
                            pattern:
                                description:
                                    - Match pattern.
                            severity:
                                description:
                                    - Severity.
                                choices:
                                    - high
                                    - medium
                                    - low
                            status:
                                description:
                                    - Status.
                                choices:
                                    - enable
                                    - disable
                            target:
                                description:
                                    - Match HTTP target.
                                choices:
                                    - arg
                                    - arg-name
                                    - req-body
                                    - req-cookie
                                    - req-cookie-name
                                    - req-filename
                                    - req-header
                                    - req-header-name
                                    - req-raw-uri
                                    - req-uri
                                    - resp-body
                                    - resp-hdr
                                    - resp-status
                    disabled-signature:
                        description:
                            - Disabled signatures
                        suboptions:
                            id:
                                description:
                                    - Signature ID. Source waf.signature.id.
                                required: true
                    disabled-sub-class:
                        description:
                            - Disabled signature subclasses.
                        suboptions:
                            id:
                                description:
                                    - Signature subclass ID. Source waf.sub-class.id.
                                required: true
                    main-class:
                        description:
                            - Main signature class.
                        suboptions:
                            action:
                                description:
                                    - Action.
                                choices:
                                    - allow
                                    - block
                                    - erase
                            id:
                                description:
                                    - Main signature class ID. Source waf.main-class.id.
                                required: true
                            log:
                                description:
                                    - Enable/disable logging.
                                choices:
                                    - enable
                                    - disable
                            severity:
                                description:
                                    - Severity.
                                choices:
                                    - high
                                    - medium
                                    - low
                            status:
                                description:
                                    - Status.
                                choices:
                                    - enable
                                    - disable
            url-access:
                description:
                    - URL access list
                suboptions:
                    access-pattern:
                        description:
                            - URL access pattern.
                        suboptions:
                            id:
                                description:
                                    - URL access pattern ID.
                                required: true
                            negate:
                                description:
                                    - Enable/disable match negation.
                                choices:
                                    - enable
                                    - disable
                            pattern:
                                description:
                                    - URL pattern.
                            regex:
                                description:
                                    - Enable/disable regular expression based pattern match.
                                choices:
                                    - enable
                                    - disable
                            srcaddr:
                                description:
                                    - Source address. Source firewall.address.name firewall.addrgrp.name.
                    action:
                        description:
                            - Action.
                        choices:
                            - bypass
                            - permit
                            - block
                    address:
                        description:
                            - Host address. Source firewall.address.name firewall.addrgrp.name.
                    id:
                        description:
                            - URL access ID.
                        required: true
                    log:
                        description:
                            - Enable/disable logging.
                        choices:
                            - enable
                            - disable
                    severity:
                        description:
                            - Severity.
                        choices:
                            - high
                            - medium
                            - low
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Web application firewall configuration.
    fortios_waf_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      waf_profile:
        state: "present"
        address-list:
            blocked-address:
             -
                name: "default_name_5 (source firewall.address.name firewall.addrgrp.name)"
            blocked-log: "enable"
            severity: "high"
            status: "enable"
            trusted-address:
             -
                name: "default_name_10 (source firewall.address.name firewall.addrgrp.name)"
        comment: "Comment."
        constraint:
            content-length:
                action: "allow"
                length: "15"
                log: "enable"
                severity: "high"
                status: "enable"
            exception:
             -
                address: "<your_own_value> (source firewall.address.name firewall.addrgrp.name)"
                content-length: "enable"
                header-length: "enable"
                hostname: "enable"
                id:  "24"
                line-length: "enable"
                malformed: "enable"
                max-cookie: "enable"
                max-header-line: "enable"
                max-range-segment: "enable"
                max-url-param: "enable"
                method: "enable"
                param-length: "enable"
                pattern: "<your_own_value>"
                regex: "enable"
                url-param-length: "enable"
                version: "enable"
            header-length:
                action: "allow"
                length: "39"
                log: "enable"
                severity: "high"
                status: "enable"
            hostname:
                action: "allow"
                log: "enable"
                severity: "high"
                status: "enable"
            line-length:
                action: "allow"
                length: "50"
                log: "enable"
                severity: "high"
                status: "enable"
            malformed:
                action: "allow"
                log: "enable"
                severity: "high"
                status: "enable"
            max-cookie:
                action: "allow"
                log: "enable"
                max-cookie: "62"
                severity: "high"
                status: "enable"
            max-header-line:
                action: "allow"
                log: "enable"
                max-header-line: "68"
                severity: "high"
                status: "enable"
            max-range-segment:
                action: "allow"
                log: "enable"
                max-range-segment: "74"
                severity: "high"
                status: "enable"
            max-url-param:
                action: "allow"
                log: "enable"
                max-url-param: "80"
                severity: "high"
                status: "enable"
            method:
                action: "allow"
                log: "enable"
                severity: "high"
                status: "enable"
            param-length:
                action: "allow"
                length: "90"
                log: "enable"
                severity: "high"
                status: "enable"
            url-param-length:
                action: "allow"
                length: "96"
                log: "enable"
                severity: "high"
                status: "enable"
            version:
                action: "allow"
                log: "enable"
                severity: "high"
                status: "enable"
        extended-log: "enable"
        external: "disable"
        method:
            default-allowed-methods: "get"
            log: "enable"
            method-policy:
             -
                address: "<your_own_value> (source firewall.address.name firewall.addrgrp.name)"
                allowed-methods: "get"
                id:  "113"
                pattern: "<your_own_value>"
                regex: "enable"
            severity: "high"
            status: "enable"
        name: "default_name_118"
        signature:
            credit-card-detection-threshold: "120"
            custom-signature:
             -
                action: "allow"
                case-sensitivity: "disable"
                direction: "request"
                log: "enable"
                name: "default_name_126"
                pattern: "<your_own_value>"
                severity: "high"
                status: "enable"
                target: "arg"
            disabled-signature:
             -
                id:  "132 (source waf.signature.id)"
            disabled-sub-class:
             -
                id:  "134 (source waf.sub-class.id)"
            main-class:
             -
                action: "allow"
                id:  "137 (source waf.main-class.id)"
                log: "enable"
                severity: "high"
                status: "enable"
        url-access:
         -
            access-pattern:
             -
                id:  "143"
                negate: "enable"
                pattern: "<your_own_value>"
                regex: "enable"
                srcaddr: "<your_own_value> (source firewall.address.name firewall.addrgrp.name)"
            action: "bypass"
            address: "<your_own_value> (source firewall.address.name firewall.addrgrp.name)"
            id:  "150"
            log: "enable"
            severity: "high"
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


def filter_waf_profile_data(json):
    option_list = ['address-list', 'comment', 'constraint',
                   'extended-log', 'external', 'method',
                   'name', 'signature', 'url-access']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def waf_profile(data, fos):
    vdom = data['vdom']
    waf_profile_data = data['waf_profile']
    filtered_data = filter_waf_profile_data(waf_profile_data)

    if waf_profile_data['state'] == "present":
        return fos.set('waf',
                       'profile',
                       data=filtered_data,
                       vdom=vdom)

    elif waf_profile_data['state'] == "absent":
        return fos.delete('waf',
                          'profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_waf(data, fos):
    login(data, fos)

    if data['waf_profile']:
        resp = waf_profile(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "waf_profile": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "address-list": {"required": False, "type": "dict",
                                 "options": {
                                     "blocked-address": {"required": False, "type": "list",
                                                         "options": {
                                                             "name": {"required": True, "type": "str"}
                                                         }},
                                     "blocked-log": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                     "severity": {"required": False, "type": "str",
                                                  "choices": ["high", "medium", "low"]},
                                     "status": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]},
                                     "trusted-address": {"required": False, "type": "list",
                                                         "options": {
                                                             "name": {"required": True, "type": "str"}
                                                         }}
                                 }},
                "comment": {"required": False, "type": "str"},
                "constraint": {"required": False, "type": "dict",
                               "options": {
                                   "content-length": {"required": False, "type": "dict",
                                                      "options": {
                                                          "action": {"required": False, "type": "str",
                                                                     "choices": ["allow", "block"]},
                                                          "length": {"required": False, "type": "int"},
                                                          "log": {"required": False, "type": "str",
                                                                  "choices": ["enable", "disable"]},
                                                          "severity": {"required": False, "type": "str",
                                                                       "choices": ["high", "medium", "low"]},
                                                          "status": {"required": False, "type": "str",
                                                                     "choices": ["enable", "disable"]}
                                                      }},
                                   "exception": {"required": False, "type": "list",
                                                 "options": {
                                                     "address": {"required": False, "type": "str"},
                                                     "content-length": {"required": False, "type": "str",
                                                                        "choices": ["enable", "disable"]},
                                                     "header-length": {"required": False, "type": "str",
                                                                       "choices": ["enable", "disable"]},
                                                     "hostname": {"required": False, "type": "str",
                                                                  "choices": ["enable", "disable"]},
                                                     "id": {"required": True, "type": "int"},
                                                     "line-length": {"required": False, "type": "str",
                                                                     "choices": ["enable", "disable"]},
                                                     "malformed": {"required": False, "type": "str",
                                                                   "choices": ["enable", "disable"]},
                                                     "max-cookie": {"required": False, "type": "str",
                                                                    "choices": ["enable", "disable"]},
                                                     "max-header-line": {"required": False, "type": "str",
                                                                         "choices": ["enable", "disable"]},
                                                     "max-range-segment": {"required": False, "type": "str",
                                                                           "choices": ["enable", "disable"]},
                                                     "max-url-param": {"required": False, "type": "str",
                                                                       "choices": ["enable", "disable"]},
                                                     "method": {"required": False, "type": "str",
                                                                "choices": ["enable", "disable"]},
                                                     "param-length": {"required": False, "type": "str",
                                                                      "choices": ["enable", "disable"]},
                                                     "pattern": {"required": False, "type": "str"},
                                                     "regex": {"required": False, "type": "str",
                                                               "choices": ["enable", "disable"]},
                                                     "url-param-length": {"required": False, "type": "str",
                                                                          "choices": ["enable", "disable"]},
                                                     "version": {"required": False, "type": "str",
                                                                 "choices": ["enable", "disable"]}
                                                 }},
                                   "header-length": {"required": False, "type": "dict",
                                                     "options": {
                                                         "action": {"required": False, "type": "str",
                                                                    "choices": ["allow", "block"]},
                                                         "length": {"required": False, "type": "int"},
                                                         "log": {"required": False, "type": "str",
                                                                 "choices": ["enable", "disable"]},
                                                         "severity": {"required": False, "type": "str",
                                                                      "choices": ["high", "medium", "low"]},
                                                         "status": {"required": False, "type": "str",
                                                                    "choices": ["enable", "disable"]}
                                                     }},
                                   "hostname": {"required": False, "type": "dict",
                                                "options": {
                                                    "action": {"required": False, "type": "str",
                                                               "choices": ["allow", "block"]},
                                                    "log": {"required": False, "type": "str",
                                                            "choices": ["enable", "disable"]},
                                                    "severity": {"required": False, "type": "str",
                                                                 "choices": ["high", "medium", "low"]},
                                                    "status": {"required": False, "type": "str",
                                                               "choices": ["enable", "disable"]}
                                                }},
                                   "line-length": {"required": False, "type": "dict",
                                                   "options": {
                                                       "action": {"required": False, "type": "str",
                                                                  "choices": ["allow", "block"]},
                                                       "length": {"required": False, "type": "int"},
                                                       "log": {"required": False, "type": "str",
                                                               "choices": ["enable", "disable"]},
                                                       "severity": {"required": False, "type": "str",
                                                                    "choices": ["high", "medium", "low"]},
                                                       "status": {"required": False, "type": "str",
                                                                  "choices": ["enable", "disable"]}
                                                   }},
                                   "malformed": {"required": False, "type": "dict",
                                                 "options": {
                                                     "action": {"required": False, "type": "str",
                                                                "choices": ["allow", "block"]},
                                                     "log": {"required": False, "type": "str",
                                                             "choices": ["enable", "disable"]},
                                                     "severity": {"required": False, "type": "str",
                                                                  "choices": ["high", "medium", "low"]},
                                                     "status": {"required": False, "type": "str",
                                                                "choices": ["enable", "disable"]}
                                                 }},
                                   "max-cookie": {"required": False, "type": "dict",
                                                  "options": {
                                                      "action": {"required": False, "type": "str",
                                                                 "choices": ["allow", "block"]},
                                                      "log": {"required": False, "type": "str",
                                                              "choices": ["enable", "disable"]},
                                                      "max-cookie": {"required": False, "type": "int"},
                                                      "severity": {"required": False, "type": "str",
                                                                   "choices": ["high", "medium", "low"]},
                                                      "status": {"required": False, "type": "str",
                                                                 "choices": ["enable", "disable"]}
                                                  }},
                                   "max-header-line": {"required": False, "type": "dict",
                                                       "options": {
                                                           "action": {"required": False, "type": "str",
                                                                      "choices": ["allow", "block"]},
                                                           "log": {"required": False, "type": "str",
                                                                   "choices": ["enable", "disable"]},
                                                           "max-header-line": {"required": False, "type": "int"},
                                                           "severity": {"required": False, "type": "str",
                                                                        "choices": ["high", "medium", "low"]},
                                                           "status": {"required": False, "type": "str",
                                                                      "choices": ["enable", "disable"]}
                                                       }},
                                   "max-range-segment": {"required": False, "type": "dict",
                                                         "options": {
                                                             "action": {"required": False, "type": "str",
                                                                        "choices": ["allow", "block"]},
                                                             "log": {"required": False, "type": "str",
                                                                     "choices": ["enable", "disable"]},
                                                             "max-range-segment": {"required": False, "type": "int"},
                                                             "severity": {"required": False, "type": "str",
                                                                          "choices": ["high", "medium", "low"]},
                                                             "status": {"required": False, "type": "str",
                                                                        "choices": ["enable", "disable"]}
                                                         }},
                                   "max-url-param": {"required": False, "type": "dict",
                                                     "options": {
                                                         "action": {"required": False, "type": "str",
                                                                    "choices": ["allow", "block"]},
                                                         "log": {"required": False, "type": "str",
                                                                 "choices": ["enable", "disable"]},
                                                         "max-url-param": {"required": False, "type": "int"},
                                                         "severity": {"required": False, "type": "str",
                                                                      "choices": ["high", "medium", "low"]},
                                                         "status": {"required": False, "type": "str",
                                                                    "choices": ["enable", "disable"]}
                                                     }},
                                   "method": {"required": False, "type": "dict",
                                              "options": {
                                                  "action": {"required": False, "type": "str",
                                                             "choices": ["allow", "block"]},
                                                  "log": {"required": False, "type": "str",
                                                          "choices": ["enable", "disable"]},
                                                  "severity": {"required": False, "type": "str",
                                                               "choices": ["high", "medium", "low"]},
                                                  "status": {"required": False, "type": "str",
                                                             "choices": ["enable", "disable"]}
                                              }},
                                   "param-length": {"required": False, "type": "dict",
                                                    "options": {
                                                        "action": {"required": False, "type": "str",
                                                                   "choices": ["allow", "block"]},
                                                        "length": {"required": False, "type": "int"},
                                                        "log": {"required": False, "type": "str",
                                                                "choices": ["enable", "disable"]},
                                                        "severity": {"required": False, "type": "str",
                                                                     "choices": ["high", "medium", "low"]},
                                                        "status": {"required": False, "type": "str",
                                                                   "choices": ["enable", "disable"]}
                                                    }},
                                   "url-param-length": {"required": False, "type": "dict",
                                                        "options": {
                                                            "action": {"required": False, "type": "str",
                                                                       "choices": ["allow", "block"]},
                                                            "length": {"required": False, "type": "int"},
                                                            "log": {"required": False, "type": "str",
                                                                    "choices": ["enable", "disable"]},
                                                            "severity": {"required": False, "type": "str",
                                                                         "choices": ["high", "medium", "low"]},
                                                            "status": {"required": False, "type": "str",
                                                                       "choices": ["enable", "disable"]}
                                                        }},
                                   "version": {"required": False, "type": "dict",
                                               "options": {
                                                   "action": {"required": False, "type": "str",
                                                              "choices": ["allow", "block"]},
                                                   "log": {"required": False, "type": "str",
                                                           "choices": ["enable", "disable"]},
                                                   "severity": {"required": False, "type": "str",
                                                                "choices": ["high", "medium", "low"]},
                                                   "status": {"required": False, "type": "str",
                                                              "choices": ["enable", "disable"]}
                                               }}
                               }},
                "extended-log": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "external": {"required": False, "type": "str",
                             "choices": ["disable", "enable"]},
                "method": {"required": False, "type": "dict",
                           "options": {
                               "default-allowed-methods": {"required": False, "type": "str",
                                                           "choices": ["get", "post", "put",
                                                                       "head", "connect", "trace",
                                                                       "options", "delete", "others"]},
                               "log": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                               "method-policy": {"required": False, "type": "list",
                                                 "options": {
                                                     "address": {"required": False, "type": "str"},
                                                     "allowed-methods": {"required": False, "type": "str",
                                                                         "choices": ["get", "post", "put",
                                                                                     "head", "connect", "trace",
                                                                                     "options", "delete", "others"]},
                                                     "id": {"required": True, "type": "int"},
                                                     "pattern": {"required": False, "type": "str"},
                                                     "regex": {"required": False, "type": "str",
                                                               "choices": ["enable", "disable"]}
                                                 }},
                               "severity": {"required": False, "type": "str",
                                            "choices": ["high", "medium", "low"]},
                               "status": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]}
                           }},
                "name": {"required": True, "type": "str"},
                "signature": {"required": False, "type": "dict",
                              "options": {
                                  "credit-card-detection-threshold": {"required": False, "type": "int"},
                                  "custom-signature": {"required": False, "type": "list",
                                                       "options": {
                                                           "action": {"required": False, "type": "str",
                                                                      "choices": ["allow", "block", "erase"]},
                                                           "case-sensitivity": {"required": False, "type": "str",
                                                                                "choices": ["disable", "enable"]},
                                                           "direction": {"required": False, "type": "str",
                                                                         "choices": ["request", "response"]},
                                                           "log": {"required": False, "type": "str",
                                                                   "choices": ["enable", "disable"]},
                                                           "name": {"required": True, "type": "str"},
                                                           "pattern": {"required": False, "type": "str"},
                                                           "severity": {"required": False, "type": "str",
                                                                        "choices": ["high", "medium", "low"]},
                                                           "status": {"required": False, "type": "str",
                                                                      "choices": ["enable", "disable"]},
                                                           "target": {"required": False, "type": "str",
                                                                      "choices": ["arg", "arg-name", "req-body",
                                                                                  "req-cookie", "req-cookie-name", "req-filename",
                                                                                  "req-header", "req-header-name", "req-raw-uri",
                                                                                  "req-uri", "resp-body", "resp-hdr",
                                                                                  "resp-status"]}
                                                       }},
                                  "disabled-signature": {"required": False, "type": "list",
                                                         "options": {
                                                             "id": {"required": True, "type": "int"}
                                                         }},
                                  "disabled-sub-class": {"required": False, "type": "list",
                                                         "options": {
                                                             "id": {"required": True, "type": "int"}
                                                         }},
                                  "main-class": {"required": False, "type": "list",
                                                 "options": {
                                                     "action": {"required": False, "type": "str",
                                                                "choices": ["allow", "block", "erase"]},
                                                     "id": {"required": True, "type": "int"},
                                                     "log": {"required": False, "type": "str",
                                                             "choices": ["enable", "disable"]},
                                                     "severity": {"required": False, "type": "str",
                                                                  "choices": ["high", "medium", "low"]},
                                                     "status": {"required": False, "type": "str",
                                                                "choices": ["enable", "disable"]}
                                                 }}
                              }},
                "url-access": {"required": False, "type": "list",
                               "options": {
                                   "access-pattern": {"required": False, "type": "list",
                                                      "options": {
                                                          "id": {"required": True, "type": "int"},
                                                          "negate": {"required": False, "type": "str",
                                                                     "choices": ["enable", "disable"]},
                                                          "pattern": {"required": False, "type": "str"},
                                                          "regex": {"required": False, "type": "str",
                                                                    "choices": ["enable", "disable"]},
                                                          "srcaddr": {"required": False, "type": "str"}
                                                      }},
                                   "action": {"required": False, "type": "str",
                                              "choices": ["bypass", "permit", "block"]},
                                   "address": {"required": False, "type": "str"},
                                   "id": {"required": True, "type": "int"},
                                   "log": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                                   "severity": {"required": False, "type": "str",
                                                "choices": ["high", "medium", "low"]}
                               }}

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

    is_error, has_changed, result = fortios_waf(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
