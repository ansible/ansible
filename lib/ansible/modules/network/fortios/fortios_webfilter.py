#!/usr/bin/python

# Copyright: (c) 2018, Fortinet, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_webfilter
short_description: Configure webfilter capabilities of FortiGate and FortiOS.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure webfilter feature. For now it
      is able to handle url and content filtering capabilities. The
      module uses FortiGate REST API internally to configure the device.

version_added: "2.6"
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
        default: "root"
    webfilter_url:
        description:
            - Container for a group of url entries that the FortiGate
              must act upon
        suboptions:
            id:
                description:
                    - Id of URL filter list.
                required: true
            name:
                description:
                    - Name of URL filter list.
                required: true
            comment:
                description:
                    - Optional comments.
            one-arm-ips-urlfilter:
                description:
                    - Enable/disable DNS resolver for one-arm IPS URL filter operation.
                choices:
                    - enable
                    - disable
                default: disable
            ip-addr-block:
                description:
                    - Enable/disable blocking URLs when the hostname appears as an IP address.
                choices:
                    - enable
                    - disable
                default: disable
            entries:
                description:
                    - URL filter entries.
                default: []
                suboptions:
                    id:
                        description:
                            - Id of URL.
                        required: true
                    url:
                        description:
                            - URL to be filtered.
                        required: true
                    type:
                        description:
                            - Filter type (simple, regex, or wildcard).
                        required: true
                        choices:
                            - simple
                            - regex
                            - wildcard
                    action:
                        description:
                            - Action to take for URL filter matches.
                        required: true
                        choices:
                            - exempt
                            - block
                            - allow
                            - monitor
                    status:
                        description:
                            - Enable/disable this URL filter.
                        required: true
                        choices:
                            - enable
                            - disable
                    exempt:
                        description:
                            - If action is set to exempt, select the security profile
                              operations that exempt URLs skip. Separate multiple
                              options with a space.
                        required: true
                        choices:
                            - av
                            - web-content
                            - activex-java-cookie
                            - dlp
                            - fortiguard
                            - range-block
                            - pass
                            - all
                    web-proxy-profile:
                        description:
                            - Web proxy profile.
                        required: true
                    referrer-host:
                        description:
                            - Referrer host name.
                        required: true
            state:
                description:
                    - Configures the intended state of this object on the FortiGate.
                      When this value is set to I(present), the object is configured
                      on the device and when this value is set to I(absent) the
                      object is removed from the device.
                required: true
                choices:
                    - absent
                    - present
    webfilter_content:
        description:
            - Container for a group of content-filtering entries that
              the FortiGate must act upon
        suboptions:
            id:
                description:
                    - Id of content-filter list.
                required: true
            name:
                description:
                    - Name of content-filter list.
            comment:
                description:
                    - Optional comments.
            entries:
                description:
                    - Content filter entries.
                default: []
                suboptions:
                    name:
                        description:
                            - Banned word.
                        required: true
                    pattern-type:
                        description:
                            - Banned word pattern type. It can be a wildcard pattern or Perl regular expression.
                        required: true
                        choices:
                            - wildcard
                            - regexp
                    status:
                        description:
                            - Enable/disable banned word.
                        required: true
                        choices:
                            - enable
                            - disable
                    lang:
                        description:
                            - Language of banned word.
                        required: true
                        choices:
                            - western
                            - simch
                            - trach
                            - japanese
                            - korean
                            - french
                            - thai
                            - spanish
                            - cyrillic
                    score:
                        description:
                            - Score, to be applied every time the word appears on a web page.
                        required: true
                    action:
                        description:
                            - Block or exempt word when a match is found.
                        required: true
                        choices:
                            - block
                            - exempt
            state:
                description:
                    - Configures the intended state of this object on the FortiGate.
                      When this value is set to I(present), the object is configured
                      on the device and when this value is set to I(absent) the
                      object is removed from the device.
                required: true
                choices:
                    - absent
                    - present
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure url to be filtered by fortigate
    fortios_webfilter:
      host:  "{{  host }}"
      username: "{{  username}}"
      password: "{{ password }}"
      vdom:  "{{  vdom }}"
      webfilter_url:
        state: "present"
        id: "1"
        name: "default"
        comment: "mycomment"
        one-arm-ips-url-filter: "disable"
        ip-addr-block: "disable"
        entries:
          - id: "1"
            url: "www.test1.com"
            type: "simple"
            action: "exempt"
            status: "enable"
            exempt: "pass"
            web-proxy-profile: ""
            referrrer-host: ""
          - id: "2"
            url: "www.test2.com"
            type: "simple"
            action: "exempt"
            status: "enable"
            exempt: "pass"
            web-proxy-profile: ""
            referrrer-host: ""


- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure web content filtering in fortigate
    fortios_webfilter:
      host:  "{{  host }}"
      username: "{{  username}}"
      password: "{{ password }}"
      vdom:  "{{  vdom }}"
      webfilter_content:
        id: "1"
        name: "default"
        comment: ""
        entries:
          - name: "1"
            pattern-type: "www.test45.com"
            status: "enable"
            lang: "western"
            score: 40
            action: "block"
          - name: "2"
            pattern-type: "www.test46.com"
            status: "enable"
            lang: "western"
            score: 42
            action: "block"
        state: "present"
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
    fos.https('off')

    fos.login(host, username, password)


def filter_wf_url_data(json):
    option_list = ['id', 'name', 'comment',
                   'one-arm-ips-urlfilter',
                   'ip-addr-block', 'entries']
    dictionary = {}

    for attribute in option_list:
        if attribute in json:
            dictionary[attribute] = json[attribute]

    return dictionary


def filter_wf_content_data(json):
    option_list = ['id', 'name', 'comment',
                   'entries']
    dictionary = {}

    for attribute in option_list:
        if attribute in json:
            dictionary[attribute] = json[attribute]

    return dictionary


def webfilter_url(data, fos):
    vdom = data['vdom']
    wf_url_data = data['webfilter_url']
    url_data = filter_wf_url_data(wf_url_data)

    if wf_url_data['state'] == "present":
        return fos.set('webfilter',
                       'urlfilter',
                       data=url_data,
                       vdom=vdom)

    elif wf_url_data['state'] == "absent":
        return fos.delete('webfilter',
                          'urlfilter',
                          mkey=url_data['id'],
                          vdom=vdom)


def webfilter_content(data, fos):
    vdom = data['vdom']
    wf_content_data = data['webfilter_content']
    content_data = filter_wf_content_data(wf_content_data)

    if wf_content_data['state'] == "present":
        return fos.set('webfilter',
                       'content',
                       data=content_data,
                       vdom=vdom)

    elif wf_content_data['state'] == "absent":
        return fos.delete('webfilter',
                          'content',
                          mkey=content_data['id'],
                          vdom=vdom)


def fortios_webfilter(data, fos):
    host = data['host']
    username = data['username']
    password = data['password']
    fos.https('off')
    fos.login(host, username, password)

    methodlist = ['webfilter_url', 'webfilter_content', 'webfilter_profile']
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
        "webfilter_url": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str"},
                "id": {"required": True, "type": "str"},
                "name": {"required": True, "type": "str"},
                "comment": {"required": False, "type": "str", "default": ""},
                "one-arm-ips-urlfilter": {"required": False, "type": "str", "default": "disable",
                                          "choices": ["enable", "disable"]},
                "ip-addr-block": {"required": False, "type": "str", "default": "disable",
                                  "choices": ["enable", "disable"]},
                "entries": {
                    "required": False, "type": "list", "default": [],
                    "options": {
                        "id": {"required": True, "type": "integer"},
                        "url": {"required": True, "type": "string"},
                        "type": {"required": True, "type": "string", "choices": ["simple", "regex", "wildcard"]},
                        "action": {"required": True, "type": "string",
                                   "choices": ["exempt", "block", "allow", "monitor"]},
                        "status": {"required": True, "type": "string", "choices": ["enable", "disable"]},
                        "exempt": {"required": True, "type": "string",
                                   "choices": ["av", "web-content", "activex-java-cookie", "dlp", "fortiguard",
                                               "range-block", "pass", "all"]},
                        "web-proxy-profile": {"required": True, "type": "string"},
                        "referrer-host": {"required": True, "type": "string"}
                    }
                }
            }
        },
        "webfilter_content": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str"},
                "id": {"required": True, "type": "str"},
                "name": {"required": True, "type": "str"},
                "comment": {"required": False, "type": "str", "default": ""},
                "entries": {
                    "required": False, "type": "list", "default": [],
                    "options": {
                        "name": {"required": True, "type": "string"},
                        "pattern-type": {"required": True, "type": "string", "choices": ["wildcard", "regexp"]},
                        "status": {"required": True, "type": "string", "choices": ["enable", "disable"]},
                        "lang": {"required": True, "type": "string",
                                 "choices": ["western", "simch", "trach", "japanese", "korean", "french", "thai",
                                             "spanish", "cyrillic"]},
                        "score": {"required": True, "type": "integer"},
                        "action": {"required": True, "type": "string", "choices": ["block", "exempt"]},
                    }
                }
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

    is_error, has_changed, result = fortios_webfilter(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
