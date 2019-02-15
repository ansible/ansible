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
module: fortios_report_style
short_description: Report style configuration in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify report feature and style category.
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
    report_style:
        description:
            - Report style configuration.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            align:
                description:
                    - Alignment.
                choices:
                    - left
                    - center
                    - right
                    - justify
            bg-color:
                description:
                    - Background color.
            border-bottom:
                description:
                    - Border bottom.
            border-left:
                description:
                    - Border left.
            border-right:
                description:
                    - Border right.
            border-top:
                description:
                    - Border top.
            column-gap:
                description:
                    - Column gap.
            column-span:
                description:
                    - Column span.
                choices:
                    - none
                    - all
            fg-color:
                description:
                    - Foreground color.
            font-family:
                description:
                    - Font family.
                choices:
                    - Verdana
                    - Arial
                    - Helvetica
                    - Courier
                    - Times
            font-size:
                description:
                    - Font size.
            font-style:
                description:
                    - Font style.
                choices:
                    - normal
                    - italic
            font-weight:
                description:
                    - Font weight.
                choices:
                    - normal
                    - bold
            height:
                description:
                    - Height.
            line-height:
                description:
                    - Text line height.
            margin-bottom:
                description:
                    - Margin bottom.
            margin-left:
                description:
                    - Margin left.
            margin-right:
                description:
                    - Margin right.
            margin-top:
                description:
                    - Margin top.
            name:
                description:
                    - Report style name.
                required: true
            options:
                description:
                    - Report style options.
                choices:
                    - font
                    - text
                    - color
                    - align
                    - size
                    - margin
                    - border
                    - padding
                    - column
            padding-bottom:
                description:
                    - Padding bottom.
            padding-left:
                description:
                    - Padding left.
            padding-right:
                description:
                    - Padding right.
            padding-top:
                description:
                    - Padding top.
            width:
                description:
                    - Width.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Report style configuration.
    fortios_report_style:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      report_style:
        state: "present"
        align: "left"
        bg-color: "<your_own_value>"
        border-bottom: "<your_own_value>"
        border-left: "<your_own_value>"
        border-right: "<your_own_value>"
        border-top: "<your_own_value>"
        column-gap: "<your_own_value>"
        column-span: "none"
        fg-color: "<your_own_value>"
        font-family: "Verdana"
        font-size: "<your_own_value>"
        font-style: "normal"
        font-weight: "normal"
        height: "<your_own_value>"
        line-height: "<your_own_value>"
        margin-bottom: "<your_own_value>"
        margin-left: "<your_own_value>"
        margin-right: "<your_own_value>"
        margin-top: "<your_own_value>"
        name: "default_name_22"
        options: "font"
        padding-bottom: "<your_own_value>"
        padding-left: "<your_own_value>"
        padding-right: "<your_own_value>"
        padding-top: "<your_own_value>"
        width: "<your_own_value>"
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


def filter_report_style_data(json):
    option_list = ['align', 'bg-color', 'border-bottom',
                   'border-left', 'border-right', 'border-top',
                   'column-gap', 'column-span', 'fg-color',
                   'font-family', 'font-size', 'font-style',
                   'font-weight', 'height', 'line-height',
                   'margin-bottom', 'margin-left', 'margin-right',
                   'margin-top', 'name', 'options',
                   'padding-bottom', 'padding-left', 'padding-right',
                   'padding-top', 'width']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def flatten_multilists_attributes(data):
    multilist_attrs = []

    for attr in multilist_attrs:
        try:
            path = "data['" + "']['".join(elem for elem in attr) + "']"
            current_val = eval(path)
            flattened_val = ' '.join(elem for elem in current_val)
            exec(path + '= flattened_val')
        except BaseException:
            pass

    return data


def report_style(data, fos):
    vdom = data['vdom']
    report_style_data = data['report_style']
    flattened_data = flatten_multilists_attributes(report_style_data)
    filtered_data = filter_report_style_data(flattened_data)
    if report_style_data['state'] == "present":
        return fos.set('report',
                       'style',
                       data=filtered_data,
                       vdom=vdom)

    elif report_style_data['state'] == "absent":
        return fos.delete('report',
                          'style',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_report(data, fos):
    login(data)

    if data['report_style']:
        resp = report_style(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "report_style": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "align": {"required": False, "type": "str",
                          "choices": ["left", "center", "right",
                                      "justify"]},
                "bg-color": {"required": False, "type": "str"},
                "border-bottom": {"required": False, "type": "str"},
                "border-left": {"required": False, "type": "str"},
                "border-right": {"required": False, "type": "str"},
                "border-top": {"required": False, "type": "str"},
                "column-gap": {"required": False, "type": "str"},
                "column-span": {"required": False, "type": "str",
                                "choices": ["none", "all"]},
                "fg-color": {"required": False, "type": "str"},
                "font-family": {"required": False, "type": "str",
                                "choices": ["Verdana", "Arial", "Helvetica",
                                            "Courier", "Times"]},
                "font-size": {"required": False, "type": "str"},
                "font-style": {"required": False, "type": "str",
                               "choices": ["normal", "italic"]},
                "font-weight": {"required": False, "type": "str",
                                "choices": ["normal", "bold"]},
                "height": {"required": False, "type": "str"},
                "line-height": {"required": False, "type": "str"},
                "margin-bottom": {"required": False, "type": "str"},
                "margin-left": {"required": False, "type": "str"},
                "margin-right": {"required": False, "type": "str"},
                "margin-top": {"required": False, "type": "str"},
                "name": {"required": True, "type": "str"},
                "options": {"required": False, "type": "str",
                            "choices": ["font", "text", "color",
                                        "align", "size", "margin",
                                        "border", "padding", "column"]},
                "padding-bottom": {"required": False, "type": "str"},
                "padding-left": {"required": False, "type": "str"},
                "padding-right": {"required": False, "type": "str"},
                "padding-top": {"required": False, "type": "str"},
                "width": {"required": False, "type": "str"}

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

    is_error, has_changed, result = fortios_report(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
