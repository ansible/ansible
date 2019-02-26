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
module: fortios_webfilter_profile
short_description: Configure Web filter profiles.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure webfilter feature and profile category.
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
    webfilter_profile:
        description:
            - Configure Web filter profiles.
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
            extended-log:
                description:
                    - Enable/disable extended logging for web filtering.
                choices:
                    - enable
                    - disable
            ftgd-wf:
                description:
                    - FortiGuard Web Filter settings.
                suboptions:
                    exempt-quota:
                        description:
                            - Do not stop quota for these categories.
                    filters:
                        description:
                            - FortiGuard filters.
                        suboptions:
                            action:
                                description:
                                    - Action to take for matches.
                                choices:
                                    - block
                                    - authenticate
                                    - monitor
                                    - warning
                            auth-usr-grp:
                                description:
                                    - Groups with permission to authenticate.
                                suboptions:
                                    name:
                                        description:
                                            - User group name. Source user.group.name.
                                        required: true
                            category:
                                description:
                                    - Categories and groups the filter examines.
                            id:
                                description:
                                    - ID number.
                                required: true
                            log:
                                description:
                                    - Enable/disable logging.
                                choices:
                                    - enable
                                    - disable
                            override-replacemsg:
                                description:
                                    - Override replacement message.
                            warn-duration:
                                description:
                                    - Duration of warnings.
                            warning-duration-type:
                                description:
                                    - Re-display warning after closing browser or after a timeout.
                                choices:
                                    - session
                                    - timeout
                            warning-prompt:
                                description:
                                    - Warning prompts in each category or each domain.
                                choices:
                                    - per-domain
                                    - per-category
                    max-quota-timeout:
                        description:
                            - Maximum FortiGuard quota used by single page view in seconds (excludes streams).
                    options:
                        description:
                            - Options for FortiGuard Web Filter.
                        choices:
                            - error-allow
                            - rate-server-ip
                            - connect-request-bypass
                            - ftgd-disable
                    ovrd:
                        description:
                            - Allow web filter profile overrides.
                    quota:
                        description:
                            - FortiGuard traffic quota settings.
                        suboptions:
                            category:
                                description:
                                    - FortiGuard categories to apply quota to (category action must be set to monitor).
                            duration:
                                description:
                                    - Duration of quota.
                            id:
                                description:
                                    - ID number.
                                required: true
                            override-replacemsg:
                                description:
                                    - Override replacement message.
                            type:
                                description:
                                    - Quota type.
                                choices:
                                    - time
                                    - traffic
                            unit:
                                description:
                                    - Traffic quota unit of measurement.
                                choices:
                                    - B
                                    - KB
                                    - MB
                                    - GB
                            value:
                                description:
                                    - Traffic quota value.
                    rate-crl-urls:
                        description:
                            - Enable/disable rating CRL by URL.
                        choices:
                            - disable
                            - enable
                    rate-css-urls:
                        description:
                            - Enable/disable rating CSS by URL.
                        choices:
                            - disable
                            - enable
                    rate-image-urls:
                        description:
                            - Enable/disable rating images by URL.
                        choices:
                            - disable
                            - enable
                    rate-javascript-urls:
                        description:
                            - Enable/disable rating JavaScript by URL.
                        choices:
                            - disable
                            - enable
            https-replacemsg:
                description:
                    - Enable replacement messages for HTTPS.
                choices:
                    - enable
                    - disable
            inspection-mode:
                description:
                    - Web filtering inspection mode.
                choices:
                    - proxy
                    - flow-based
            log-all-url:
                description:
                    - Enable/disable logging all URLs visited.
                choices:
                    - enable
                    - disable
            name:
                description:
                    - Profile name.
                required: true
            options:
                description:
                    - Options.
                choices:
                    - activexfilter
                    - cookiefilter
                    - javafilter
                    - block-invalid-url
                    - jscript
                    - js
                    - vbs
                    - unknown
                    - intrinsic
                    - wf-referer
                    - wf-cookie
                    - per-user-bwl
            override:
                description:
                    - Web Filter override settings.
                suboptions:
                    ovrd-cookie:
                        description:
                            - Allow/deny browser-based (cookie) overrides.
                        choices:
                            - allow
                            - deny
                    ovrd-dur:
                        description:
                            - Override duration.
                    ovrd-dur-mode:
                        description:
                            - Override duration mode.
                        choices:
                            - constant
                            - ask
                    ovrd-scope:
                        description:
                            - Override scope.
                        choices:
                            - user
                            - user-group
                            - ip
                            - browser
                            - ask
                    ovrd-user-group:
                        description:
                            - User groups with permission to use the override.
                        suboptions:
                            name:
                                description:
                                    - User group name. Source user.group.name.
                                required: true
                    profile:
                        description:
                            - Web filter profile with permission to create overrides.
                        suboptions:
                            name:
                                description:
                                    - Web profile. Source webfilter.profile.name.
                                required: true
                    profile-attribute:
                        description:
                            - Profile attribute to retrieve from the RADIUS server.
                        choices:
                            - User-Name
                            - NAS-IP-Address
                            - Framed-IP-Address
                            - Framed-IP-Netmask
                            - Filter-Id
                            - Login-IP-Host
                            - Reply-Message
                            - Callback-Number
                            - Callback-Id
                            - Framed-Route
                            - Framed-IPX-Network
                            - Class
                            - Called-Station-Id
                            - Calling-Station-Id
                            - NAS-Identifier
                            - Proxy-State
                            - Login-LAT-Service
                            - Login-LAT-Node
                            - Login-LAT-Group
                            - Framed-AppleTalk-Zone
                            - Acct-Session-Id
                            - Acct-Multi-Session-Id
                    profile-type:
                        description:
                            - Override profile type.
                        choices:
                            - list
                            - radius
            ovrd-perm:
                description:
                    - Permitted override types.
                choices:
                    - bannedword-override
                    - urlfilter-override
                    - fortiguard-wf-override
                    - contenttype-check-override
            post-action:
                description:
                    - Action taken for HTTP POST traffic.
                choices:
                    - normal
                    - block
            replacemsg-group:
                description:
                    - Replacement message group. Source system.replacemsg-group.name.
            web:
                description:
                    - Web content filtering settings.
                suboptions:
                    blacklist:
                        description:
                            - Enable/disable automatic addition of URLs detected by FortiSandbox to blacklist.
                        choices:
                            - enable
                            - disable
                    bword-table:
                        description:
                            - Banned word table ID. Source webfilter.content.id.
                    bword-threshold:
                        description:
                            - Banned word score threshold.
                    content-header-list:
                        description:
                            - Content header list. Source webfilter.content-header.id.
                    keyword-match:
                        description:
                            - Search keywords to log when match is found.
                        suboptions:
                            pattern:
                                description:
                                    - Pattern/keyword to search for.
                                required: true
                    log-search:
                        description:
                            - Enable/disable logging all search phrases.
                        choices:
                            - enable
                            - disable
                    safe-search:
                        description:
                            - Safe search type.
                        choices:
                            - url
                            - header
                    urlfilter-table:
                        description:
                            - URL filter table ID. Source webfilter.urlfilter.id.
                    whitelist:
                        description:
                            - FortiGuard whitelist settings.
                        choices:
                            - exempt-av
                            - exempt-webcontent
                            - exempt-activex-java-cookie
                            - exempt-dlp
                            - exempt-rangeblock
                            - extended-log-others
                    youtube-restrict:
                        description:
                            - YouTube EDU filter level.
                        choices:
                            - none
                            - strict
                            - moderate
            web-content-log:
                description:
                    - Enable/disable logging logging blocked web content.
                choices:
                    - enable
                    - disable
            web-extended-all-action-log:
                description:
                    - Enable/disable extended any filter action logging for web filtering.
                choices:
                    - enable
                    - disable
            web-filter-activex-log:
                description:
                    - Enable/disable logging ActiveX.
                choices:
                    - enable
                    - disable
            web-filter-applet-log:
                description:
                    - Enable/disable logging Java applets.
                choices:
                    - enable
                    - disable
            web-filter-command-block-log:
                description:
                    - Enable/disable logging blocked commands.
                choices:
                    - enable
                    - disable
            web-filter-cookie-log:
                description:
                    - Enable/disable logging cookie filtering.
                choices:
                    - enable
                    - disable
            web-filter-cookie-removal-log:
                description:
                    - Enable/disable logging blocked cookies.
                choices:
                    - enable
                    - disable
            web-filter-js-log:
                description:
                    - Enable/disable logging Java scripts.
                choices:
                    - enable
                    - disable
            web-filter-jscript-log:
                description:
                    - Enable/disable logging JScripts.
                choices:
                    - enable
                    - disable
            web-filter-referer-log:
                description:
                    - Enable/disable logging referrers.
                choices:
                    - enable
                    - disable
            web-filter-unknown-log:
                description:
                    - Enable/disable logging unknown scripts.
                choices:
                    - enable
                    - disable
            web-filter-vbs-log:
                description:
                    - Enable/disable logging VBS scripts.
                choices:
                    - enable
                    - disable
            web-ftgd-err-log:
                description:
                    - Enable/disable logging rating errors.
                choices:
                    - enable
                    - disable
            web-ftgd-quota-usage:
                description:
                    - Enable/disable logging daily quota usage.
                choices:
                    - enable
                    - disable
            web-invalid-domain-log:
                description:
                    - Enable/disable logging invalid domain names.
                choices:
                    - enable
                    - disable
            web-url-log:
                description:
                    - Enable/disable logging URL filtering.
                choices:
                    - enable
                    - disable
            wisp:
                description:
                    - Enable/disable web proxy WISP.
                choices:
                    - enable
                    - disable
            wisp-algorithm:
                description:
                    - WISP server selection algorithm.
                choices:
                    - primary-secondary
                    - round-robin
                    - auto-learning
            wisp-servers:
                description:
                    - WISP servers.
                suboptions:
                    name:
                        description:
                            - Server name. Source web-proxy.wisp.name.
                        required: true
            youtube-channel-filter:
                description:
                    - YouTube channel filter.
                suboptions:
                    channel-id:
                        description:
                            - YouTube channel ID to be filtered.
                    comment:
                        description:
                            - Comment.
                    id:
                        description:
                            - ID.
                        required: true
            youtube-channel-status:
                description:
                    - YouTube channel filter status.
                choices:
                    - disable
                    - blacklist
                    - whitelist
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure Web filter profiles.
    fortios_webfilter_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      webfilter_profile:
        state: "present"
        comment: "Optional comments."
        extended-log: "enable"
        ftgd-wf:
            exempt-quota: "<your_own_value>"
            filters:
             -
                action: "block"
                auth-usr-grp:
                 -
                    name: "default_name_10 (source user.group.name)"
                category: "11"
                id:  "12"
                log: "enable"
                override-replacemsg: "<your_own_value>"
                warn-duration: "<your_own_value>"
                warning-duration-type: "session"
                warning-prompt: "per-domain"
            max-quota-timeout: "18"
            options: "error-allow"
            ovrd: "<your_own_value>"
            quota:
             -
                category: "<your_own_value>"
                duration: "<your_own_value>"
                id:  "24"
                override-replacemsg: "<your_own_value>"
                type: "time"
                unit: "B"
                value: "28"
            rate-crl-urls: "disable"
            rate-css-urls: "disable"
            rate-image-urls: "disable"
            rate-javascript-urls: "disable"
        https-replacemsg: "enable"
        inspection-mode: "proxy"
        log-all-url: "enable"
        name: "default_name_36"
        options: "activexfilter"
        override:
            ovrd-cookie: "allow"
            ovrd-dur: "<your_own_value>"
            ovrd-dur-mode: "constant"
            ovrd-scope: "user"
            ovrd-user-group:
             -
                name: "default_name_44 (source user.group.name)"
            profile:
             -
                name: "default_name_46 (source webfilter.profile.name)"
            profile-attribute: "User-Name"
            profile-type: "list"
        ovrd-perm: "bannedword-override"
        post-action: "normal"
        replacemsg-group: "<your_own_value> (source system.replacemsg-group.name)"
        web:
            blacklist: "enable"
            bword-table: "54 (source webfilter.content.id)"
            bword-threshold: "55"
            content-header-list: "56 (source webfilter.content-header.id)"
            keyword-match:
             -
                pattern: "<your_own_value>"
            log-search: "enable"
            safe-search: "url"
            urlfilter-table: "61 (source webfilter.urlfilter.id)"
            whitelist: "exempt-av"
            youtube-restrict: "none"
        web-content-log: "enable"
        web-extended-all-action-log: "enable"
        web-filter-activex-log: "enable"
        web-filter-applet-log: "enable"
        web-filter-command-block-log: "enable"
        web-filter-cookie-log: "enable"
        web-filter-cookie-removal-log: "enable"
        web-filter-js-log: "enable"
        web-filter-jscript-log: "enable"
        web-filter-referer-log: "enable"
        web-filter-unknown-log: "enable"
        web-filter-vbs-log: "enable"
        web-ftgd-err-log: "enable"
        web-ftgd-quota-usage: "enable"
        web-invalid-domain-log: "enable"
        web-url-log: "enable"
        wisp: "enable"
        wisp-algorithm: "primary-secondary"
        wisp-servers:
         -
            name: "default_name_83 (source web-proxy.wisp.name)"
        youtube-channel-filter:
         -
            channel-id: "<your_own_value>"
            comment: "Comment."
            id:  "87"
        youtube-channel-status: "disable"
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


def filter_webfilter_profile_data(json):
    option_list = ['comment', 'extended-log', 'ftgd-wf',
                   'https-replacemsg', 'inspection-mode', 'log-all-url',
                   'name', 'options', 'override',
                   'ovrd-perm', 'post-action', 'replacemsg-group',
                   'web', 'web-content-log', 'web-extended-all-action-log',
                   'web-filter-activex-log', 'web-filter-applet-log', 'web-filter-command-block-log',
                   'web-filter-cookie-log', 'web-filter-cookie-removal-log', 'web-filter-js-log',
                   'web-filter-jscript-log', 'web-filter-referer-log', 'web-filter-unknown-log',
                   'web-filter-vbs-log', 'web-ftgd-err-log', 'web-ftgd-quota-usage',
                   'web-invalid-domain-log', 'web-url-log', 'wisp',
                   'wisp-algorithm', 'wisp-servers', 'youtube-channel-filter',
                   'youtube-channel-status']
    dictionary = {}

    for attribute in option_list:
        if attribute in json:
            dictionary[attribute] = json[attribute]

    return dictionary


def webfilter_profile(data, fos):
    vdom = data['vdom']
    webfilter_profile_data = data['webfilter_profile']
    filtered_data = filter_webfilter_profile_data(webfilter_profile_data)
    if webfilter_profile_data['state'] == "present":
        return fos.set('webfilter',
                       'profile',
                       data=filtered_data,
                       vdom=vdom)

    elif webfilter_profile_data['state'] == "absent":
        return fos.delete('webfilter',
                          'profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_webfilter(data, fos):
    login(data)

    methodlist = ['webfilter_profile']
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
        "webfilter_profile": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "comment": {"required": False, "type": "str"},
                "extended-log": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "ftgd-wf": {"required": False, "type": "dict",
                            "options": {
                                "exempt-quota": {"required": False, "type": "str"},
                                "filters": {"required": False, "type": "list",
                                            "options": {
                                                "action": {"required": False, "type": "str",
                                                           "choices": ["block", "authenticate", "monitor",
                                                                       "warning"]},
                                                "auth-usr-grp": {"required": False, "type": "str",
                                                                 "options": {
                                                                     "name": {"required": True, "type": "str"}
                                                                 }},
                                                "category": {"required": False, "type": "int"},
                                                "id": {"required": True, "type": "int"},
                                                "log": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                                "override-replacemsg": {"required": False, "type": "str"},
                                                "warn-duration": {"required": False, "type": "str"},
                                                "warning-duration-type": {"required": False, "type": "str",
                                                                          "choices": ["session", "timeout"]},
                                                "warning-prompt": {"required": False, "type": "str",
                                                                   "choices": ["per-domain", "per-category"]}
                                            }},
                                "max-quota-timeout": {"required": False, "type": "int"},
                                "options": {"required": False, "type": "str",
                                            "choices": ["error-allow", "rate-server-ip", "connect-request-bypass",
                                                        "ftgd-disable"]},
                                "ovrd": {"required": False, "type": "str"},
                                "quota": {"required": False, "type": "list",
                                          "options": {
                                              "category": {"required": False, "type": "str"},
                                              "duration": {"required": False, "type": "str"},
                                              "id": {"required": True, "type": "int"},
                                              "override-replacemsg": {"required": False, "type": "str"},
                                              "type": {"required": False, "type": "str",
                                                       "choices": ["time", "traffic"]},
                                              "unit": {"required": False, "type": "str",
                                                       "choices": ["B", "KB", "MB",
                                                                   "GB"]},
                                              "value": {"required": False, "type": "int"}
                                          }},
                                "rate-crl-urls": {"required": False, "type": "str",
                                                  "choices": ["disable", "enable"]},
                                "rate-css-urls": {"required": False, "type": "str",
                                                  "choices": ["disable", "enable"]},
                                "rate-image-urls": {"required": False, "type": "str",
                                                    "choices": ["disable", "enable"]},
                                "rate-javascript-urls": {"required": False, "type": "str",
                                                         "choices": ["disable", "enable"]}
                            }},
                "https-replacemsg": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "inspection-mode": {"required": False, "type": "str",
                                    "choices": ["proxy", "flow-based"]},
                "log-all-url": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "name": {"required": True, "type": "str"},
                "options": {"required": False, "type": "str",
                            "choices": ["activexfilter", "cookiefilter", "javafilter",
                                        "block-invalid-url", "jscript", "js",
                                        "vbs", "unknown", "intrinsic",
                                        "wf-referer", "wf-cookie", "per-user-bwl"]},
                "override": {"required": False, "type": "dict",
                             "options": {
                                 "ovrd-cookie": {"required": False, "type": "str",
                                                 "choices": ["allow", "deny"]},
                                 "ovrd-dur": {"required": False, "type": "str"},
                                 "ovrd-dur-mode": {"required": False, "type": "str",
                                                   "choices": ["constant", "ask"]},
                                 "ovrd-scope": {"required": False, "type": "str",
                                                "choices": ["user", "user-group", "ip",
                                                            "browser", "ask"]},
                                 "ovrd-user-group": {"required": False, "type": "str",
                                                     "options": {
                                                         "name": {"required": True, "type": "str"}
                                                     }},
                                 "profile": {"required": False, "type": "list",
                                             "options": {
                                                 "name": {"required": True, "type": "str"}
                                             }},
                                 "profile-attribute": {"required": False, "type": "str",
                                                       "choices": ["User-Name", "NAS-IP-Address", "Framed-IP-Address",
                                                                   "Framed-IP-Netmask", "Filter-Id", "Login-IP-Host",
                                                                   "Reply-Message", "Callback-Number", "Callback-Id",
                                                                   "Framed-Route", "Framed-IPX-Network", "Class",
                                                                   "Called-Station-Id", "Calling-Station-Id", "NAS-Identifier",
                                                                   "Proxy-State", "Login-LAT-Service", "Login-LAT-Node",
                                                                   "Login-LAT-Group", "Framed-AppleTalk-Zone", "Acct-Session-Id",
                                                                   "Acct-Multi-Session-Id"]},
                                 "profile-type": {"required": False, "type": "str",
                                                  "choices": ["list", "radius"]}
                             }},
                "ovrd-perm": {"required": False, "type": "str",
                              "choices": ["bannedword-override", "urlfilter-override", "fortiguard-wf-override",
                                          "contenttype-check-override"]},
                "post-action": {"required": False, "type": "str",
                                "choices": ["normal", "block"]},
                "replacemsg-group": {"required": False, "type": "str"},
                "web": {"required": False, "type": "dict",
                        "options": {
                            "blacklist": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                            "bword-table": {"required": False, "type": "int"},
                            "bword-threshold": {"required": False, "type": "int"},
                            "content-header-list": {"required": False, "type": "int"},
                            "keyword-match": {"required": False, "type": "str",
                                              "options": {
                                                  "pattern": {"required": True, "type": "str"}
                                              }},
                            "log-search": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                            "safe-search": {"required": False, "type": "str",
                                            "choices": ["url", "header"]},
                            "urlfilter-table": {"required": False, "type": "int"},
                            "whitelist": {"required": False, "type": "str",
                                          "choices": ["exempt-av", "exempt-webcontent", "exempt-activex-java-cookie",
                                                      "exempt-dlp", "exempt-rangeblock", "extended-log-others"]},
                            "youtube-restrict": {"required": False, "type": "str",
                                                 "choices": ["none", "strict", "moderate"]}
                        }},
                "web-content-log": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "web-extended-all-action-log": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]},
                "web-filter-activex-log": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "web-filter-applet-log": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "web-filter-command-block-log": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                "web-filter-cookie-log": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "web-filter-cookie-removal-log": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                "web-filter-js-log": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "web-filter-jscript-log": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "web-filter-referer-log": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "web-filter-unknown-log": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "web-filter-vbs-log": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "web-ftgd-err-log": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "web-ftgd-quota-usage": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "web-invalid-domain-log": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "web-url-log": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "wisp": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "wisp-algorithm": {"required": False, "type": "str",
                                   "choices": ["primary-secondary", "round-robin", "auto-learning"]},
                "wisp-servers": {"required": False, "type": "list",
                                 "options": {
                                     "name": {"required": True, "type": "str"}
                                 }},
                "youtube-channel-filter": {"required": False, "type": "list",
                                           "options": {
                                               "channel-id": {"required": False, "type": "str"},
                                               "comment": {"required": False, "type": "str"},
                                               "id": {"required": True, "type": "int"}
                                           }},
                "youtube-channel-status": {"required": False, "type": "str",
                                           "choices": ["disable", "blacklist", "whitelist"]}

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

    is_error, has_changed, result = fortios_webfilter(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
