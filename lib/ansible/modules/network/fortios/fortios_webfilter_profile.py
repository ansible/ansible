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
module: fortios_webfilter_profile
short_description: Configure Web filter profiles in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify webfilter feature and profile category.
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
    webfilter_profile:
        description:
            - Configure Web filter profiles.
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
            extended_log:
                description:
                    - Enable/disable extended logging for web filtering.
                type: str
                choices:
                    - enable
                    - disable
            ftgd_wf:
                description:
                    - FortiGuard Web Filter settings.
                type: dict
                suboptions:
                    exempt_quota:
                        description:
                            - Do not stop quota for these categories.
                        type: str
                    filters:
                        description:
                            - FortiGuard filters.
                        type: list
                        suboptions:
                            action:
                                description:
                                    - Action to take for matches.
                                type: str
                                choices:
                                    - block
                                    - authenticate
                                    - monitor
                                    - warning
                            auth_usr_grp:
                                description:
                                    - Groups with permission to authenticate.
                                type: str
                                suboptions:
                                    name:
                                        description:
                                            - User group name. Source user.group.name.
                                        required: true
                                        type: str
                            category:
                                description:
                                    - Categories and groups the filter examines.
                                type: int
                            id:
                                description:
                                    - ID number.
                                required: true
                                type: int
                            log:
                                description:
                                    - Enable/disable logging.
                                type: str
                                choices:
                                    - enable
                                    - disable
                            override_replacemsg:
                                description:
                                    - Override replacement message.
                                type: str
                            warn_duration:
                                description:
                                    - Duration of warnings.
                                type: str
                            warning_duration_type:
                                description:
                                    - Re-display warning after closing browser or after a timeout.
                                type: str
                                choices:
                                    - session
                                    - timeout
                            warning_prompt:
                                description:
                                    - Warning prompts in each category or each domain.
                                type: str
                                choices:
                                    - per-domain
                                    - per-category
                    max_quota_timeout:
                        description:
                            - Maximum FortiGuard quota used by single page view in seconds (excludes streams).
                        type: int
                    options:
                        description:
                            - Options for FortiGuard Web Filter.
                        type: str
                        choices:
                            - error-allow
                            - rate-server-ip
                            - connect-request-bypass
                            - ftgd-disable
                    ovrd:
                        description:
                            - Allow web filter profile overrides.
                        type: str
                    quota:
                        description:
                            - FortiGuard traffic quota settings.
                        type: list
                        suboptions:
                            category:
                                description:
                                    - FortiGuard categories to apply quota to (category action must be set to monitor).
                                type: str
                            duration:
                                description:
                                    - Duration of quota.
                                type: str
                            id:
                                description:
                                    - ID number.
                                required: true
                                type: int
                            override_replacemsg:
                                description:
                                    - Override replacement message.
                                type: str
                            type:
                                description:
                                    - Quota type.
                                type: str
                                choices:
                                    - time
                                    - traffic
                            unit:
                                description:
                                    - Traffic quota unit of measurement.
                                type: str
                                choices:
                                    - B
                                    - KB
                                    - MB
                                    - GB
                            value:
                                description:
                                    - Traffic quota value.
                                type: int
                    rate_crl_urls:
                        description:
                            - Enable/disable rating CRL by URL.
                        type: str
                        choices:
                            - disable
                            - enable
                    rate_css_urls:
                        description:
                            - Enable/disable rating CSS by URL.
                        type: str
                        choices:
                            - disable
                            - enable
                    rate_image_urls:
                        description:
                            - Enable/disable rating images by URL.
                        type: str
                        choices:
                            - disable
                            - enable
                    rate_javascript_urls:
                        description:
                            - Enable/disable rating JavaScript by URL.
                        type: str
                        choices:
                            - disable
                            - enable
            https_replacemsg:
                description:
                    - Enable replacement messages for HTTPS.
                type: str
                choices:
                    - enable
                    - disable
            inspection_mode:
                description:
                    - Web filtering inspection mode.
                type: str
                choices:
                    - proxy
                    - flow-based
            log_all_url:
                description:
                    - Enable/disable logging all URLs visited.
                type: str
                choices:
                    - enable
                    - disable
            name:
                description:
                    - Profile name.
                required: true
                type: str
            options:
                description:
                    - Options.
                type: str
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
                type: dict
                suboptions:
                    ovrd_cookie:
                        description:
                            - Allow/deny browser-based (cookie) overrides.
                        type: str
                        choices:
                            - allow
                            - deny
                    ovrd_dur:
                        description:
                            - Override duration.
                        type: str
                    ovrd_dur_mode:
                        description:
                            - Override duration mode.
                        type: str
                        choices:
                            - constant
                            - ask
                    ovrd_scope:
                        description:
                            - Override scope.
                        type: str
                        choices:
                            - user
                            - user-group
                            - ip
                            - browser
                            - ask
                    ovrd_user_group:
                        description:
                            - User groups with permission to use the override.
                        type: str
                        suboptions:
                            name:
                                description:
                                    - User group name. Source user.group.name.
                                required: true
                                type: str
                    profile:
                        description:
                            - Web filter profile with permission to create overrides.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Web profile. Source webfilter.profile.name.
                                required: true
                                type: str
                    profile_attribute:
                        description:
                            - Profile attribute to retrieve from the RADIUS server.
                        type: str
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
                    profile_type:
                        description:
                            - Override profile type.
                        type: str
                        choices:
                            - list
                            - radius
            ovrd_perm:
                description:
                    - Permitted override types.
                type: str
                choices:
                    - bannedword-override
                    - urlfilter-override
                    - fortiguard-wf-override
                    - contenttype-check-override
            post_action:
                description:
                    - Action taken for HTTP POST traffic.
                type: str
                choices:
                    - normal
                    - block
            replacemsg_group:
                description:
                    - Replacement message group. Source system.replacemsg-group.name.
                type: str
            web:
                description:
                    - Web content filtering settings.
                type: dict
                suboptions:
                    blacklist:
                        description:
                            - Enable/disable automatic addition of URLs detected by FortiSandbox to blacklist.
                        type: str
                        choices:
                            - enable
                            - disable
                    bword_table:
                        description:
                            - Banned word table ID. Source webfilter.content.id.
                        type: int
                    bword_threshold:
                        description:
                            - Banned word score threshold.
                        type: int
                    content_header_list:
                        description:
                            - Content header list. Source webfilter.content-header.id.
                        type: int
                    keyword_match:
                        description:
                            - Search keywords to log when match is found.
                        type: str
                        suboptions:
                            pattern:
                                description:
                                    - Pattern/keyword to search for.
                                required: true
                                type: str
                    log_search:
                        description:
                            - Enable/disable logging all search phrases.
                        type: str
                        choices:
                            - enable
                            - disable
                    safe_search:
                        description:
                            - Safe search type.
                        type: str
                        choices:
                            - url
                            - header
                    urlfilter_table:
                        description:
                            - URL filter table ID. Source webfilter.urlfilter.id.
                        type: int
                    whitelist:
                        description:
                            - FortiGuard whitelist settings.
                        type: str
                        choices:
                            - exempt-av
                            - exempt-webcontent
                            - exempt-activex-java-cookie
                            - exempt-dlp
                            - exempt-rangeblock
                            - extended-log-others
                    youtube_restrict:
                        description:
                            - YouTube EDU filter level.
                        type: str
                        choices:
                            - none
                            - strict
                            - moderate
            web_content_log:
                description:
                    - Enable/disable logging logging blocked web content.
                type: str
                choices:
                    - enable
                    - disable
            web_extended_all_action_log:
                description:
                    - Enable/disable extended any filter action logging for web filtering.
                type: str
                choices:
                    - enable
                    - disable
            web_filter_activex_log:
                description:
                    - Enable/disable logging ActiveX.
                type: str
                choices:
                    - enable
                    - disable
            web_filter_applet_log:
                description:
                    - Enable/disable logging Java applets.
                type: str
                choices:
                    - enable
                    - disable
            web_filter_command_block_log:
                description:
                    - Enable/disable logging blocked commands.
                type: str
                choices:
                    - enable
                    - disable
            web_filter_cookie_log:
                description:
                    - Enable/disable logging cookie filtering.
                type: str
                choices:
                    - enable
                    - disable
            web_filter_cookie_removal_log:
                description:
                    - Enable/disable logging blocked cookies.
                type: str
                choices:
                    - enable
                    - disable
            web_filter_js_log:
                description:
                    - Enable/disable logging Java scripts.
                type: str
                choices:
                    - enable
                    - disable
            web_filter_jscript_log:
                description:
                    - Enable/disable logging JScripts.
                type: str
                choices:
                    - enable
                    - disable
            web_filter_referer_log:
                description:
                    - Enable/disable logging referrers.
                type: str
                choices:
                    - enable
                    - disable
            web_filter_unknown_log:
                description:
                    - Enable/disable logging unknown scripts.
                type: str
                choices:
                    - enable
                    - disable
            web_filter_vbs_log:
                description:
                    - Enable/disable logging VBS scripts.
                type: str
                choices:
                    - enable
                    - disable
            web_ftgd_err_log:
                description:
                    - Enable/disable logging rating errors.
                type: str
                choices:
                    - enable
                    - disable
            web_ftgd_quota_usage:
                description:
                    - Enable/disable logging daily quota usage.
                type: str
                choices:
                    - enable
                    - disable
            web_invalid_domain_log:
                description:
                    - Enable/disable logging invalid domain names.
                type: str
                choices:
                    - enable
                    - disable
            web_url_log:
                description:
                    - Enable/disable logging URL filtering.
                type: str
                choices:
                    - enable
                    - disable
            wisp:
                description:
                    - Enable/disable web proxy WISP.
                type: str
                choices:
                    - enable
                    - disable
            wisp_algorithm:
                description:
                    - WISP server selection algorithm.
                type: str
                choices:
                    - primary-secondary
                    - round-robin
                    - auto-learning
            wisp_servers:
                description:
                    - WISP servers.
                type: list
                suboptions:
                    name:
                        description:
                            - Server name. Source web-proxy.wisp.name.
                        required: true
                        type: str
            youtube_channel_filter:
                description:
                    - YouTube channel filter.
                type: list
                suboptions:
                    channel_id:
                        description:
                            - YouTube channel ID to be filtered.
                        type: str
                    comment:
                        description:
                            - Comment.
                        type: str
                    id:
                        description:
                            - ID.
                        required: true
                        type: int
            youtube_channel_status:
                description:
                    - YouTube channel filter status.
                type: str
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
   ssl_verify: "False"
  tasks:
  - name: Configure Web filter profiles.
    fortios_webfilter_profile:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      webfilter_profile:
        comment: "Optional comments."
        extended_log: "enable"
        ftgd_wf:
            exempt_quota: "<your_own_value>"
            filters:
             -
                action: "block"
                auth_usr_grp:
                 -
                    name: "default_name_10 (source user.group.name)"
                category: "11"
                id:  "12"
                log: "enable"
                override_replacemsg: "<your_own_value>"
                warn_duration: "<your_own_value>"
                warning_duration_type: "session"
                warning_prompt: "per-domain"
            max_quota_timeout: "18"
            options: "error-allow"
            ovrd: "<your_own_value>"
            quota:
             -
                category: "<your_own_value>"
                duration: "<your_own_value>"
                id:  "24"
                override_replacemsg: "<your_own_value>"
                type: "time"
                unit: "B"
                value: "28"
            rate_crl_urls: "disable"
            rate_css_urls: "disable"
            rate_image_urls: "disable"
            rate_javascript_urls: "disable"
        https_replacemsg: "enable"
        inspection_mode: "proxy"
        log_all_url: "enable"
        name: "default_name_36"
        options: "activexfilter"
        override:
            ovrd_cookie: "allow"
            ovrd_dur: "<your_own_value>"
            ovrd_dur_mode: "constant"
            ovrd_scope: "user"
            ovrd_user_group:
             -
                name: "default_name_44 (source user.group.name)"
            profile:
             -
                name: "default_name_46 (source webfilter.profile.name)"
            profile_attribute: "User-Name"
            profile_type: "list"
        ovrd_perm: "bannedword-override"
        post_action: "normal"
        replacemsg_group: "<your_own_value> (source system.replacemsg-group.name)"
        web:
            blacklist: "enable"
            bword_table: "54 (source webfilter.content.id)"
            bword_threshold: "55"
            content_header_list: "56 (source webfilter.content-header.id)"
            keyword_match:
             -
                pattern: "<your_own_value>"
            log_search: "enable"
            safe_search: "url"
            urlfilter_table: "61 (source webfilter.urlfilter.id)"
            whitelist: "exempt-av"
            youtube_restrict: "none"
        web_content_log: "enable"
        web_extended_all_action_log: "enable"
        web_filter_activex_log: "enable"
        web_filter_applet_log: "enable"
        web_filter_command_block_log: "enable"
        web_filter_cookie_log: "enable"
        web_filter_cookie_removal_log: "enable"
        web_filter_js_log: "enable"
        web_filter_jscript_log: "enable"
        web_filter_referer_log: "enable"
        web_filter_unknown_log: "enable"
        web_filter_vbs_log: "enable"
        web_ftgd_err_log: "enable"
        web_ftgd_quota_usage: "enable"
        web_invalid_domain_log: "enable"
        web_url_log: "enable"
        wisp: "enable"
        wisp_algorithm: "primary-secondary"
        wisp_servers:
         -
            name: "default_name_83 (source web-proxy.wisp.name)"
        youtube_channel_filter:
         -
            channel_id: "<your_own_value>"
            comment: "Comment."
            id:  "87"
        youtube_channel_status: "disable"
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


def filter_webfilter_profile_data(json):
    option_list = ['comment', 'extended_log', 'ftgd_wf',
                   'https_replacemsg', 'inspection_mode', 'log_all_url',
                   'name', 'options', 'override',
                   'ovrd_perm', 'post_action', 'replacemsg_group',
                   'web', 'web_content_log', 'web_extended_all_action_log',
                   'web_filter_activex_log', 'web_filter_applet_log', 'web_filter_command_block_log',
                   'web_filter_cookie_log', 'web_filter_cookie_removal_log', 'web_filter_js_log',
                   'web_filter_jscript_log', 'web_filter_referer_log', 'web_filter_unknown_log',
                   'web_filter_vbs_log', 'web_ftgd_err_log', 'web_ftgd_quota_usage',
                   'web_invalid_domain_log', 'web_url_log', 'wisp',
                   'wisp_algorithm', 'wisp_servers', 'youtube_channel_filter',
                   'youtube_channel_status']
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


def webfilter_profile(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['webfilter_profile'] and data['webfilter_profile']:
        state = data['webfilter_profile']['state']
    else:
        state = True
    webfilter_profile_data = data['webfilter_profile']
    filtered_data = underscore_to_hyphen(filter_webfilter_profile_data(webfilter_profile_data))

    if state == "present":
        return fos.set('webfilter',
                       'profile',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('webfilter',
                          'profile',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_webfilter(data, fos):

    if data['webfilter_profile']:
        resp = webfilter_profile(data, fos)

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
        "webfilter_profile": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "comment": {"required": False, "type": "str"},
                "extended_log": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "ftgd_wf": {"required": False, "type": "dict",
                            "options": {
                                "exempt_quota": {"required": False, "type": "str"},
                                "filters": {"required": False, "type": "list",
                                            "options": {
                                                "action": {"required": False, "type": "str",
                                                           "choices": ["block", "authenticate", "monitor",
                                                                       "warning"]},
                                                "auth_usr_grp": {"required": False, "type": "str",
                                                                 "options": {
                                                                     "name": {"required": True, "type": "str"}
                                                                 }},
                                                "category": {"required": False, "type": "int"},
                                                "id": {"required": True, "type": "int"},
                                                "log": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                                "override_replacemsg": {"required": False, "type": "str"},
                                                "warn_duration": {"required": False, "type": "str"},
                                                "warning_duration_type": {"required": False, "type": "str",
                                                                          "choices": ["session", "timeout"]},
                                                "warning_prompt": {"required": False, "type": "str",
                                                                   "choices": ["per-domain", "per-category"]}
                                            }},
                                "max_quota_timeout": {"required": False, "type": "int"},
                                "options": {"required": False, "type": "str",
                                            "choices": ["error-allow", "rate-server-ip", "connect-request-bypass",
                                                        "ftgd-disable"]},
                                "ovrd": {"required": False, "type": "str"},
                                "quota": {"required": False, "type": "list",
                                          "options": {
                                              "category": {"required": False, "type": "str"},
                                              "duration": {"required": False, "type": "str"},
                                              "id": {"required": True, "type": "int"},
                                              "override_replacemsg": {"required": False, "type": "str"},
                                              "type": {"required": False, "type": "str",
                                                       "choices": ["time", "traffic"]},
                                              "unit": {"required": False, "type": "str",
                                                       "choices": ["B", "KB", "MB",
                                                                   "GB"]},
                                              "value": {"required": False, "type": "int"}
                                          }},
                                "rate_crl_urls": {"required": False, "type": "str",
                                                  "choices": ["disable", "enable"]},
                                "rate_css_urls": {"required": False, "type": "str",
                                                  "choices": ["disable", "enable"]},
                                "rate_image_urls": {"required": False, "type": "str",
                                                    "choices": ["disable", "enable"]},
                                "rate_javascript_urls": {"required": False, "type": "str",
                                                         "choices": ["disable", "enable"]}
                            }},
                "https_replacemsg": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "inspection_mode": {"required": False, "type": "str",
                                    "choices": ["proxy", "flow-based"]},
                "log_all_url": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "name": {"required": True, "type": "str"},
                "options": {"required": False, "type": "str",
                            "choices": ["activexfilter", "cookiefilter", "javafilter",
                                        "block-invalid-url", "jscript", "js",
                                        "vbs", "unknown", "intrinsic",
                                        "wf-referer", "wf-cookie", "per-user-bwl"]},
                "override": {"required": False, "type": "dict",
                             "options": {
                                 "ovrd_cookie": {"required": False, "type": "str",
                                                 "choices": ["allow", "deny"]},
                                 "ovrd_dur": {"required": False, "type": "str"},
                                 "ovrd_dur_mode": {"required": False, "type": "str",
                                                   "choices": ["constant", "ask"]},
                                 "ovrd_scope": {"required": False, "type": "str",
                                                "choices": ["user", "user-group", "ip",
                                                            "browser", "ask"]},
                                 "ovrd_user_group": {"required": False, "type": "str",
                                                     "options": {
                                                         "name": {"required": True, "type": "str"}
                                                     }},
                                 "profile": {"required": False, "type": "list",
                                             "options": {
                                                 "name": {"required": True, "type": "str"}
                                             }},
                                 "profile_attribute": {"required": False, "type": "str",
                                                       "choices": ["User-Name", "NAS-IP-Address", "Framed-IP-Address",
                                                                   "Framed-IP-Netmask", "Filter-Id", "Login-IP-Host",
                                                                   "Reply-Message", "Callback-Number", "Callback-Id",
                                                                   "Framed-Route", "Framed-IPX-Network", "Class",
                                                                   "Called-Station-Id", "Calling-Station-Id", "NAS-Identifier",
                                                                   "Proxy-State", "Login-LAT-Service", "Login-LAT-Node",
                                                                   "Login-LAT-Group", "Framed-AppleTalk-Zone", "Acct-Session-Id",
                                                                   "Acct-Multi-Session-Id"]},
                                 "profile_type": {"required": False, "type": "str",
                                                  "choices": ["list", "radius"]}
                             }},
                "ovrd_perm": {"required": False, "type": "str",
                              "choices": ["bannedword-override", "urlfilter-override", "fortiguard-wf-override",
                                          "contenttype-check-override"]},
                "post_action": {"required": False, "type": "str",
                                "choices": ["normal", "block"]},
                "replacemsg_group": {"required": False, "type": "str"},
                "web": {"required": False, "type": "dict",
                        "options": {
                            "blacklist": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                            "bword_table": {"required": False, "type": "int"},
                            "bword_threshold": {"required": False, "type": "int"},
                            "content_header_list": {"required": False, "type": "int"},
                            "keyword_match": {"required": False, "type": "str",
                                              "options": {
                                                  "pattern": {"required": True, "type": "str"}
                                              }},
                            "log_search": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                            "safe_search": {"required": False, "type": "str",
                                            "choices": ["url", "header"]},
                            "urlfilter_table": {"required": False, "type": "int"},
                            "whitelist": {"required": False, "type": "str",
                                          "choices": ["exempt-av", "exempt-webcontent", "exempt-activex-java-cookie",
                                                      "exempt-dlp", "exempt-rangeblock", "extended-log-others"]},
                            "youtube_restrict": {"required": False, "type": "str",
                                                 "choices": ["none", "strict", "moderate"]}
                        }},
                "web_content_log": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "web_extended_all_action_log": {"required": False, "type": "str",
                                                "choices": ["enable", "disable"]},
                "web_filter_activex_log": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "web_filter_applet_log": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "web_filter_command_block_log": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                "web_filter_cookie_log": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "web_filter_cookie_removal_log": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                "web_filter_js_log": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "web_filter_jscript_log": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "web_filter_referer_log": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "web_filter_unknown_log": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "web_filter_vbs_log": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "web_ftgd_err_log": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "web_ftgd_quota_usage": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "web_invalid_domain_log": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "web_url_log": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "wisp": {"required": False, "type": "str",
                         "choices": ["enable", "disable"]},
                "wisp_algorithm": {"required": False, "type": "str",
                                   "choices": ["primary-secondary", "round-robin", "auto-learning"]},
                "wisp_servers": {"required": False, "type": "list",
                                 "options": {
                                     "name": {"required": True, "type": "str"}
                                 }},
                "youtube_channel_filter": {"required": False, "type": "list",
                                           "options": {
                                               "channel_id": {"required": False, "type": "str"},
                                               "comment": {"required": False, "type": "str"},
                                               "id": {"required": True, "type": "int"}
                                           }},
                "youtube_channel_status": {"required": False, "type": "str",
                                           "choices": ["disable", "blacklist", "whitelist"]}

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

            is_error, has_changed, result = fortios_webfilter(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_webfilter(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
