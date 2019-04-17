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
module: fortios_report_layout
short_description: Report layout configuration in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify report feature and layout category.
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
    report_layout:
        description:
            - Report layout configuration.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            body-item:
                description:
                    - Configure report body item.
                suboptions:
                    chart:
                        description:
                            - Report item chart name.
                    chart-options:
                        description:
                            - Report chart options.
                        choices:
                            - include-no-data
                            - hide-title
                            - show-caption
                    column:
                        description:
                            - Report section column number.
                    content:
                        description:
                            - Report item text content.
                    description:
                        description:
                            - Description.
                    drill-down-items:
                        description:
                            - Control how drill down charts are shown.
                    drill-down-types:
                        description:
                            - Control whether keys from the parent being combined or not.
                    hide:
                        description:
                            - Enable/disable hide item in report.
                        choices:
                            - enable
                            - disable
                    id:
                        description:
                            - Report item ID.
                        required: true
                    img-src:
                        description:
                            - Report item image file name.
                    list:
                        description:
                            - Configure report list item.
                        suboptions:
                            content:
                                description:
                                    - List entry content.
                            id:
                                description:
                                    - List entry ID.
                                required: true
                    list-component:
                        description:
                            - Report item list component.
                        choices:
                            - bullet
                            - numbered
                    misc-component:
                        description:
                            - Report item miscellaneous component.
                        choices:
                            - hline
                            - page-break
                            - column-break
                            - section-start
                    parameters:
                        description:
                            - Parameters.
                        suboptions:
                            id:
                                description:
                                    - ID.
                                required: true
                            name:
                                description:
                                    - Field name that match field of parameters defined in dataset.
                            value:
                                description:
                                    - Value to replace corresponding field of parameters defined in dataset.
                    style:
                        description:
                            - Report item style.
                    table-caption-style:
                        description:
                            - Table chart caption style.
                    table-column-widths:
                        description:
                            - Report item table column widths.
                    table-even-row-style:
                        description:
                            - Table chart even row style.
                    table-head-style:
                        description:
                            - Table chart head style.
                    table-odd-row-style:
                        description:
                            - Table chart odd row style.
                    text-component:
                        description:
                            - Report item text component.
                        choices:
                            - text
                            - heading1
                            - heading2
                            - heading3
                    title:
                        description:
                            - Report section title.
                    top-n:
                        description:
                            - Value of top.
                    type:
                        description:
                            - Report item type.
                        choices:
                            - text
                            - image
                            - chart
                            - misc
            cutoff-option:
                description:
                    - Cutoff-option is either run-time or custom.
                choices:
                    - run-time
                    - custom
            cutoff-time:
                description:
                    - "Custom cutoff time to generate report [hh:mm]."
            day:
                description:
                    - Schedule days of week to generate report.
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
            email-recipients:
                description:
                    - Email recipients for generated reports.
            email-send:
                description:
                    - Enable/disable sending emails after reports are generated.
                choices:
                    - enable
                    - disable
            format:
                description:
                    - Report format.
                choices:
                    - pdf
            max-pdf-report:
                description:
                    - Maximum number of PDF reports to keep at one time (oldest report is overwritten).
            name:
                description:
                    - Report layout name.
                required: true
            options:
                description:
                    - Report layout options.
                choices:
                    - include-table-of-content
                    - auto-numbering-heading
                    - view-chart-as-heading
                    - show-html-navbar-before-heading
                    - dummy-option
            page:
                description:
                    - Configure report page.
                suboptions:
                    column-break-before:
                        description:
                            - Report page auto column break before heading.
                        choices:
                            - heading1
                            - heading2
                            - heading3
                    footer:
                        description:
                            - Configure report page footer.
                        suboptions:
                            footer-item:
                                description:
                                    - Configure report footer item.
                                suboptions:
                                    content:
                                        description:
                                            - Report item text content.
                                    description:
                                        description:
                                            - Description.
                                    id:
                                        description:
                                            - Report item ID.
                                        required: true
                                    img-src:
                                        description:
                                            - Report item image file name.
                                    style:
                                        description:
                                            - Report item style.
                                    type:
                                        description:
                                            - Report item type.
                                        choices:
                                            - text
                                            - image
                            style:
                                description:
                                    - Report footer style.
                    header:
                        description:
                            - Configure report page header.
                        suboptions:
                            header-item:
                                description:
                                    - Configure report header item.
                                suboptions:
                                    content:
                                        description:
                                            - Report item text content.
                                    description:
                                        description:
                                            - Description.
                                    id:
                                        description:
                                            - Report item ID.
                                        required: true
                                    img-src:
                                        description:
                                            - Report item image file name.
                                    style:
                                        description:
                                            - Report item style.
                                    type:
                                        description:
                                            - Report item type.
                                        choices:
                                            - text
                                            - image
                            style:
                                description:
                                    - Report header style.
                    options:
                        description:
                            - Report page options.
                        choices:
                            - header-on-first-page
                            - footer-on-first-page
                    page-break-before:
                        description:
                            - Report page auto page break before heading.
                        choices:
                            - heading1
                            - heading2
                            - heading3
                    paper:
                        description:
                            - Report page paper.
                        choices:
                            - a4
                            - letter
            schedule-type:
                description:
                    - Report schedule type.
                choices:
                    - demand
                    - daily
                    - weekly
            style-theme:
                description:
                    - Report style theme.
            subtitle:
                description:
                    - Report subtitle.
            time:
                description:
                    - "Schedule time to generate report [hh:mm]."
            title:
                description:
                    - Report title.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Report layout configuration.
    fortios_report_layout:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      report_layout:
        state: "present"
        body-item:
         -
            chart: "<your_own_value>"
            chart-options: "include-no-data"
            column: "6"
            content: "<your_own_value>"
            description: "<your_own_value>"
            drill-down-items: "<your_own_value>"
            drill-down-types: "<your_own_value>"
            hide: "enable"
            id:  "12"
            img-src: "<your_own_value>"
            list:
             -
                content: "<your_own_value>"
                id:  "16"
            list-component: "bullet"
            misc-component: "hline"
            parameters:
             -
                id:  "20"
                name: "default_name_21"
                value: "<your_own_value>"
            style: "<your_own_value>"
            table-caption-style: "<your_own_value>"
            table-column-widths: "<your_own_value>"
            table-even-row-style: "<your_own_value>"
            table-head-style: "<your_own_value>"
            table-odd-row-style: "<your_own_value>"
            text-component: "text"
            title: "<your_own_value>"
            top-n: "31"
            type: "text"
        cutoff-option: "run-time"
        cutoff-time: "<your_own_value>"
        day: "sunday"
        description: "<your_own_value>"
        email-recipients: "<your_own_value>"
        email-send: "enable"
        format: "pdf"
        max-pdf-report: "40"
        name: "default_name_41"
        options: "include-table-of-content"
        page:
            column-break-before: "heading1"
            footer:
                footer-item:
                 -
                    content: "<your_own_value>"
                    description: "<your_own_value>"
                    id:  "49"
                    img-src: "<your_own_value>"
                    style: "<your_own_value>"
                    type: "text"
                style: "<your_own_value>"
            header:
                header-item:
                 -
                    content: "<your_own_value>"
                    description: "<your_own_value>"
                    id:  "58"
                    img-src: "<your_own_value>"
                    style: "<your_own_value>"
                    type: "text"
                style: "<your_own_value>"
            options: "header-on-first-page"
            page-break-before: "heading1"
            paper: "a4"
        schedule-type: "demand"
        style-theme: "<your_own_value>"
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


def filter_report_layout_data(json):
    option_list = ['body-item', 'cutoff-option', 'cutoff-time',
                   'day', 'description', 'email-recipients',
                   'email-send', 'format', 'max-pdf-report',
                   'name', 'options', 'page',
                   'schedule-type', 'style-theme', 'subtitle',
                   'time', 'title']
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


def report_layout(data, fos):
    vdom = data['vdom']
    report_layout_data = data['report_layout']
    flattened_data = flatten_multilists_attributes(report_layout_data)
    filtered_data = filter_report_layout_data(flattened_data)
    if report_layout_data['state'] == "present":
        return fos.set('report',
                       'layout',
                       data=filtered_data,
                       vdom=vdom)

    elif report_layout_data['state'] == "absent":
        return fos.delete('report',
                          'layout',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_report(data, fos):
    login(data)

    if data['report_layout']:
        resp = report_layout(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "report_layout": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "body-item": {"required": False, "type": "list",
                              "options": {
                                  "chart": {"required": False, "type": "str"},
                                  "chart-options": {"required": False, "type": "str",
                                                    "choices": ["include-no-data", "hide-title", "show-caption"]},
                                  "column": {"required": False, "type": "int"},
                                  "content": {"required": False, "type": "str"},
                                  "description": {"required": False, "type": "str"},
                                  "drill-down-items": {"required": False, "type": "str"},
                                  "drill-down-types": {"required": False, "type": "str"},
                                  "hide": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                                  "id": {"required": True, "type": "int"},
                                  "img-src": {"required": False, "type": "str"},
                                  "list": {"required": False, "type": "list",
                                           "options": {
                                               "content": {"required": False, "type": "str"},
                                               "id": {"required": True, "type": "int"}
                                           }},
                                  "list-component": {"required": False, "type": "str",
                                                     "choices": ["bullet", "numbered"]},
                                  "misc-component": {"required": False, "type": "str",
                                                     "choices": ["hline", "page-break", "column-break",
                                                                 "section-start"]},
                                  "parameters": {"required": False, "type": "list",
                                                 "options": {
                                                     "id": {"required": True, "type": "int"},
                                                     "name": {"required": False, "type": "str"},
                                                     "value": {"required": False, "type": "str"}
                                                 }},
                                  "style": {"required": False, "type": "str"},
                                  "table-caption-style": {"required": False, "type": "str"},
                                  "table-column-widths": {"required": False, "type": "str"},
                                  "table-even-row-style": {"required": False, "type": "str"},
                                  "table-head-style": {"required": False, "type": "str"},
                                  "table-odd-row-style": {"required": False, "type": "str"},
                                  "text-component": {"required": False, "type": "str",
                                                     "choices": ["text", "heading1", "heading2",
                                                                 "heading3"]},
                                  "title": {"required": False, "type": "str"},
                                  "top-n": {"required": False, "type": "int"},
                                  "type": {"required": False, "type": "str",
                                           "choices": ["text", "image", "chart",
                                                       "misc"]}
                              }},
                "cutoff-option": {"required": False, "type": "str",
                                  "choices": ["run-time", "custom"]},
                "cutoff-time": {"required": False, "type": "str"},
                "day": {"required": False, "type": "str",
                        "choices": ["sunday", "monday", "tuesday",
                                    "wednesday", "thursday", "friday",
                                    "saturday"]},
                "description": {"required": False, "type": "str"},
                "email-recipients": {"required": False, "type": "str"},
                "email-send": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "format": {"required": False, "type": "str",
                           "choices": ["pdf"]},
                "max-pdf-report": {"required": False, "type": "int"},
                "name": {"required": True, "type": "str"},
                "options": {"required": False, "type": "str",
                            "choices": ["include-table-of-content", "auto-numbering-heading", "view-chart-as-heading",
                                        "show-html-navbar-before-heading", "dummy-option"]},
                "page": {"required": False, "type": "dict",
                         "options": {
                             "column-break-before": {"required": False, "type": "str",
                                                     "choices": ["heading1", "heading2", "heading3"]},
                             "footer": {"required": False, "type": "dict",
                                        "options": {
                                            "footer-item": {"required": False, "type": "list",
                                                            "options": {
                                                                "content": {"required": False, "type": "str"},
                                                                "description": {"required": False, "type": "str"},
                                                                "id": {"required": True, "type": "int"},
                                                                "img-src": {"required": False, "type": "str"},
                                                                "style": {"required": False, "type": "str"},
                                                                "type": {"required": False, "type": "str",
                                                                         "choices": ["text", "image"]}
                                                            }},
                                            "style": {"required": False, "type": "str"}
                                        }},
                             "header": {"required": False, "type": "dict",
                                        "options": {
                                            "header-item": {"required": False, "type": "list",
                                                            "options": {
                                                                "content": {"required": False, "type": "str"},
                                                                "description": {"required": False, "type": "str"},
                                                                "id": {"required": True, "type": "int"},
                                                                "img-src": {"required": False, "type": "str"},
                                                                "style": {"required": False, "type": "str"},
                                                                "type": {"required": False, "type": "str",
                                                                         "choices": ["text", "image"]}
                                                            }},
                                            "style": {"required": False, "type": "str"}
                                        }},
                             "options": {"required": False, "type": "str",
                                         "choices": ["header-on-first-page", "footer-on-first-page"]},
                             "page-break-before": {"required": False, "type": "str",
                                                   "choices": ["heading1", "heading2", "heading3"]},
                             "paper": {"required": False, "type": "str",
                                       "choices": ["a4", "letter"]}
                         }},
                "schedule-type": {"required": False, "type": "str",
                                  "choices": ["demand", "daily", "weekly"]},
                "style-theme": {"required": False, "type": "str"},
                "subtitle": {"required": False, "type": "str"},
                "time": {"required": False, "type": "str"},
                "title": {"required": False, "type": "str"}

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
