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
module: fortios_report_layout
short_description: Report layout configuration in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify report feature and layout category.
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
    report_layout:
        description:
            - Report layout configuration.
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
            body_item:
                description:
                    - Configure report body item.
                type: list
                suboptions:
                    chart:
                        description:
                            - Report item chart name.
                        type: str
                    chart_options:
                        description:
                            - Report chart options.
                        type: str
                        choices:
                            - include-no-data
                            - hide-title
                            - show-caption
                    column:
                        description:
                            - Report section column number.
                        type: int
                    content:
                        description:
                            - Report item text content.
                        type: str
                    description:
                        description:
                            - Description.
                        type: str
                    drill_down_items:
                        description:
                            - Control how drill down charts are shown.
                        type: str
                    drill_down_types:
                        description:
                            - Control whether keys from the parent being combined or not.
                        type: str
                    hide:
                        description:
                            - Enable/disable hide item in report.
                        type: str
                        choices:
                            - enable
                            - disable
                    id:
                        description:
                            - Report item ID.
                        required: true
                        type: int
                    img_src:
                        description:
                            - Report item image file name.
                        type: str
                    list:
                        description:
                            - Configure report list item.
                        type: list
                        suboptions:
                            content:
                                description:
                                    - List entry content.
                                type: str
                            id:
                                description:
                                    - List entry ID.
                                required: true
                                type: int
                    list_component:
                        description:
                            - Report item list component.
                        type: str
                        choices:
                            - bullet
                            - numbered
                    misc_component:
                        description:
                            - Report item miscellaneous component.
                        type: str
                        choices:
                            - hline
                            - page-break
                            - column-break
                            - section-start
                    parameters:
                        description:
                            - Parameters.
                        type: list
                        suboptions:
                            id:
                                description:
                                    - ID.
                                required: true
                                type: int
                            name:
                                description:
                                    - Field name that match field of parameters defined in dataset.
                                type: str
                            value:
                                description:
                                    - Value to replace corresponding field of parameters defined in dataset.
                                type: str
                    style:
                        description:
                            - Report item style.
                        type: str
                    table_caption_style:
                        description:
                            - Table chart caption style.
                        type: str
                    table_column_widths:
                        description:
                            - Report item table column widths.
                        type: str
                    table_even_row_style:
                        description:
                            - Table chart even row style.
                        type: str
                    table_head_style:
                        description:
                            - Table chart head style.
                        type: str
                    table_odd_row_style:
                        description:
                            - Table chart odd row style.
                        type: str
                    text_component:
                        description:
                            - Report item text component.
                        type: str
                        choices:
                            - text
                            - heading1
                            - heading2
                            - heading3
                    title:
                        description:
                            - Report section title.
                        type: str
                    top_n:
                        description:
                            - Value of top.
                        type: int
                    type:
                        description:
                            - Report item type.
                        type: str
                        choices:
                            - text
                            - image
                            - chart
                            - misc
            cutoff_option:
                description:
                    - Cutoff-option is either run-time or custom.
                type: str
                choices:
                    - run-time
                    - custom
            cutoff_time:
                description:
                    - "Custom cutoff time to generate report [hh:mm]."
                type: str
            day:
                description:
                    - Schedule days of week to generate report.
                type: str
                choices:
                    - sunday
                    - monday
                    - tuesday
                    - wednesday
                    - thursday
                    - friday
                    - saturday
            description:
                description:
                    - Description.
                type: str
            email_recipients:
                description:
                    - Email recipients for generated reports.
                type: str
            email_send:
                description:
                    - Enable/disable sending emails after reports are generated.
                type: str
                choices:
                    - enable
                    - disable
            format:
                description:
                    - Report format.
                type: str
                choices:
                    - pdf
            max_pdf_report:
                description:
                    - Maximum number of PDF reports to keep at one time (oldest report is overwritten).
                type: int
            name:
                description:
                    - Report layout name.
                required: true
                type: str
            options:
                description:
                    - Report layout options.
                type: str
                choices:
                    - include-table-of-content
                    - auto-numbering-heading
                    - view-chart-as-heading
                    - show-html-navbar-before-heading
                    - dummy-option
            page:
                description:
                    - Configure report page.
                type: dict
                suboptions:
                    column_break_before:
                        description:
                            - Report page auto column break before heading.
                        type: str
                        choices:
                            - heading1
                            - heading2
                            - heading3
                    footer:
                        description:
                            - Configure report page footer.
                        type: dict
                        suboptions:
                            footer_item:
                                description:
                                    - Configure report footer item.
                                type: list
                                suboptions:
                                    content:
                                        description:
                                            - Report item text content.
                                        type: str
                                    description:
                                        description:
                                            - Description.
                                        type: str
                                    id:
                                        description:
                                            - Report item ID.
                                        required: true
                                        type: int
                                    img_src:
                                        description:
                                            - Report item image file name.
                                        type: str
                                    style:
                                        description:
                                            - Report item style.
                                        type: str
                                    type:
                                        description:
                                            - Report item type.
                                        type: str
                                        choices:
                                            - text
                                            - image
                            style:
                                description:
                                    - Report footer style.
                                type: str
                    header:
                        description:
                            - Configure report page header.
                        type: dict
                        suboptions:
                            header_item:
                                description:
                                    - Configure report header item.
                                type: list
                                suboptions:
                                    content:
                                        description:
                                            - Report item text content.
                                        type: str
                                    description:
                                        description:
                                            - Description.
                                        type: str
                                    id:
                                        description:
                                            - Report item ID.
                                        required: true
                                        type: int
                                    img_src:
                                        description:
                                            - Report item image file name.
                                        type: str
                                    style:
                                        description:
                                            - Report item style.
                                        type: str
                                    type:
                                        description:
                                            - Report item type.
                                        type: str
                                        choices:
                                            - text
                                            - image
                            style:
                                description:
                                    - Report header style.
                                type: str
                    options:
                        description:
                            - Report page options.
                        type: str
                        choices:
                            - header-on-first-page
                            - footer-on-first-page
                    page_break_before:
                        description:
                            - Report page auto page break before heading.
                        type: str
                        choices:
                            - heading1
                            - heading2
                            - heading3
                    paper:
                        description:
                            - Report page paper.
                        type: str
                        choices:
                            - a4
                            - letter
            schedule_type:
                description:
                    - Report schedule type.
                type: str
                choices:
                    - demand
                    - daily
                    - weekly
            style_theme:
                description:
                    - Report style theme.
                type: str
            subtitle:
                description:
                    - Report subtitle.
                type: str
            time:
                description:
                    - "Schedule time to generate report [hh:mm]."
                type: str
            title:
                description:
                    - Report title.
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
  - name: Report layout configuration.
    fortios_report_layout:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      report_layout:
        body_item:
         -
            chart: "<your_own_value>"
            chart_options: "include-no-data"
            column: "6"
            content: "<your_own_value>"
            description: "<your_own_value>"
            drill_down_items: "<your_own_value>"
            drill_down_types: "<your_own_value>"
            hide: "enable"
            id:  "12"
            img_src: "<your_own_value>"
            list:
             -
                content: "<your_own_value>"
                id:  "16"
            list_component: "bullet"
            misc_component: "hline"
            parameters:
             -
                id:  "20"
                name: "default_name_21"
                value: "<your_own_value>"
            style: "<your_own_value>"
            table_caption_style: "<your_own_value>"
            table_column_widths: "<your_own_value>"
            table_even_row_style: "<your_own_value>"
            table_head_style: "<your_own_value>"
            table_odd_row_style: "<your_own_value>"
            text_component: "text"
            title: "<your_own_value>"
            top_n: "31"
            type: "text"
        cutoff_option: "run-time"
        cutoff_time: "<your_own_value>"
        day: "sunday"
        description: "<your_own_value>"
        email_recipients: "<your_own_value>"
        email_send: "enable"
        format: "pdf"
        max_pdf_report: "40"
        name: "default_name_41"
        options: "include-table-of-content"
        page:
            column_break_before: "heading1"
            footer:
                footer_item:
                 -
                    content: "<your_own_value>"
                    description: "<your_own_value>"
                    id:  "49"
                    img_src: "<your_own_value>"
                    style: "<your_own_value>"
                    type: "text"
                style: "<your_own_value>"
            header:
                header_item:
                 -
                    content: "<your_own_value>"
                    description: "<your_own_value>"
                    id:  "58"
                    img_src: "<your_own_value>"
                    style: "<your_own_value>"
                    type: "text"
                style: "<your_own_value>"
            options: "header-on-first-page"
            page_break_before: "heading1"
            paper: "a4"
        schedule_type: "demand"
        style_theme: "<your_own_value>"
        subtitle: "<your_own_value>"
        time: "<your_own_value>"
        title: "<your_own_value>"
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


def filter_report_layout_data(json):
    option_list = ['body_item', 'cutoff_option', 'cutoff_time',
                   'day', 'description', 'email_recipients',
                   'email_send', 'format', 'max_pdf_report',
                   'name', 'options', 'page',
                   'schedule_type', 'style_theme', 'subtitle',
                   'time', 'title']
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


def report_layout(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['report_layout'] and data['report_layout']:
        state = data['report_layout']['state']
    else:
        state = True
    report_layout_data = data['report_layout']
    filtered_data = underscore_to_hyphen(filter_report_layout_data(report_layout_data))

    if state == "present":
        return fos.set('report',
                       'layout',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('report',
                          'layout',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_report(data, fos):

    if data['report_layout']:
        resp = report_layout(data, fos)

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
        "report_layout": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "body_item": {"required": False, "type": "list",
                              "options": {
                                  "chart": {"required": False, "type": "str"},
                                  "chart_options": {"required": False, "type": "str",
                                                    "choices": ["include-no-data", "hide-title", "show-caption"]},
                                  "column": {"required": False, "type": "int"},
                                  "content": {"required": False, "type": "str"},
                                  "description": {"required": False, "type": "str"},
                                  "drill_down_items": {"required": False, "type": "str"},
                                  "drill_down_types": {"required": False, "type": "str"},
                                  "hide": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                                  "id": {"required": True, "type": "int"},
                                  "img_src": {"required": False, "type": "str"},
                                  "list": {"required": False, "type": "list",
                                           "options": {
                                               "content": {"required": False, "type": "str"},
                                               "id": {"required": True, "type": "int"}
                                           }},
                                  "list_component": {"required": False, "type": "str",
                                                     "choices": ["bullet", "numbered"]},
                                  "misc_component": {"required": False, "type": "str",
                                                     "choices": ["hline", "page-break", "column-break",
                                                                 "section-start"]},
                                  "parameters": {"required": False, "type": "list",
                                                 "options": {
                                                     "id": {"required": True, "type": "int"},
                                                     "name": {"required": False, "type": "str"},
                                                     "value": {"required": False, "type": "str"}
                                                 }},
                                  "style": {"required": False, "type": "str"},
                                  "table_caption_style": {"required": False, "type": "str"},
                                  "table_column_widths": {"required": False, "type": "str"},
                                  "table_even_row_style": {"required": False, "type": "str"},
                                  "table_head_style": {"required": False, "type": "str"},
                                  "table_odd_row_style": {"required": False, "type": "str"},
                                  "text_component": {"required": False, "type": "str",
                                                     "choices": ["text", "heading1", "heading2",
                                                                 "heading3"]},
                                  "title": {"required": False, "type": "str"},
                                  "top_n": {"required": False, "type": "int"},
                                  "type": {"required": False, "type": "str",
                                           "choices": ["text", "image", "chart",
                                                       "misc"]}
                              }},
                "cutoff_option": {"required": False, "type": "str",
                                  "choices": ["run-time", "custom"]},
                "cutoff_time": {"required": False, "type": "str"},
                "day": {"required": False, "type": "str",
                        "choices": ["sunday", "monday", "tuesday",
                                    "wednesday", "thursday", "friday",
                                    "saturday"]},
                "description": {"required": False, "type": "str"},
                "email_recipients": {"required": False, "type": "str"},
                "email_send": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "format": {"required": False, "type": "str",
                           "choices": ["pdf"]},
                "max_pdf_report": {"required": False, "type": "int"},
                "name": {"required": True, "type": "str"},
                "options": {"required": False, "type": "str",
                            "choices": ["include-table-of-content", "auto-numbering-heading", "view-chart-as-heading",
                                        "show-html-navbar-before-heading", "dummy-option"]},
                "page": {"required": False, "type": "dict",
                         "options": {
                             "column_break_before": {"required": False, "type": "str",
                                                     "choices": ["heading1", "heading2", "heading3"]},
                             "footer": {"required": False, "type": "dict",
                                        "options": {
                                            "footer_item": {"required": False, "type": "list",
                                                            "options": {
                                                                "content": {"required": False, "type": "str"},
                                                                "description": {"required": False, "type": "str"},
                                                                "id": {"required": True, "type": "int"},
                                                                "img_src": {"required": False, "type": "str"},
                                                                "style": {"required": False, "type": "str"},
                                                                "type": {"required": False, "type": "str",
                                                                         "choices": ["text", "image"]}
                                                            }},
                                            "style": {"required": False, "type": "str"}
                                        }},
                             "header": {"required": False, "type": "dict",
                                        "options": {
                                            "header_item": {"required": False, "type": "list",
                                                            "options": {
                                                                "content": {"required": False, "type": "str"},
                                                                "description": {"required": False, "type": "str"},
                                                                "id": {"required": True, "type": "int"},
                                                                "img_src": {"required": False, "type": "str"},
                                                                "style": {"required": False, "type": "str"},
                                                                "type": {"required": False, "type": "str",
                                                                         "choices": ["text", "image"]}
                                                            }},
                                            "style": {"required": False, "type": "str"}
                                        }},
                             "options": {"required": False, "type": "str",
                                         "choices": ["header-on-first-page", "footer-on-first-page"]},
                             "page_break_before": {"required": False, "type": "str",
                                                   "choices": ["heading1", "heading2", "heading3"]},
                             "paper": {"required": False, "type": "str",
                                       "choices": ["a4", "letter"]}
                         }},
                "schedule_type": {"required": False, "type": "str",
                                  "choices": ["demand", "daily", "weekly"]},
                "style_theme": {"required": False, "type": "str"},
                "subtitle": {"required": False, "type": "str"},
                "time": {"required": False, "type": "str"},
                "title": {"required": False, "type": "str"}

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

            is_error, has_changed, result = fortios_report(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_report(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
