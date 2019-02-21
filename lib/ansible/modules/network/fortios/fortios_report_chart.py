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
module: fortios_report_chart
short_description: Report chart widget configuration in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify report feature and chart category.
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
    report_chart:
        description:
            - Report chart widget configuration.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            background:
                description:
                    - Chart background.
            category:
                description:
                    - Category.
                choices:
                    - misc
                    - traffic
                    - event
                    - virus
                    - webfilter
                    - attack
                    - spam
                    - dlp
                    - app-ctrl
                    - vulnerability
            category-series:
                description:
                    - Category series of pie chart.
                suboptions:
                    databind:
                        description:
                            - Category series value expression.
                    font-size:
                        description:
                            - Font size of category-series title.
            color-palette:
                description:
                    - Color palette (system will pick color automatically by default).
            column:
                description:
                    - Table column definition.
                suboptions:
                    detail-unit:
                        description:
                            - Detail unit of column.
                    detail-value:
                        description:
                            - Detail value of column.
                    footer-unit:
                        description:
                            - Footer unit of column.
                    footer-value:
                        description:
                            - Footer value of column.
                    header-value:
                        description:
                            - Display name of table header.
                    id:
                        description:
                            - ID.
                        required: true
                    mapping:
                        description:
                            - Show detail in certain display value for certain condition.
                        suboptions:
                            displayname:
                                description:
                                    - Display name.
                            id:
                                description:
                                    - id
                                required: true
                            op:
                                description:
                                    - Comparision operater.
                                choices:
                                    - none
                                    - greater
                                    - greater-equal
                                    - less
                                    - less-equal
                                    - equal
                                    - between
                            value-type:
                                description:
                                    - Value type.
                                choices:
                                    - integer
                                    - string
                            value1:
                                description:
                                    - Value 1.
                            value2:
                                description:
                                    - Value 2.
            comments:
                description:
                    - Comment.
            dataset:
                description:
                    - Bind dataset to chart.
            dimension:
                description:
                    - Dimension.
                choices:
                    - 2D
                    - 3D
            drill-down-charts:
                description:
                    - Drill down charts.
                suboptions:
                    chart-name:
                        description:
                            - Drill down chart name.
                    id:
                        description:
                            - Drill down chart ID.
                        required: true
                    status:
                        description:
                            - Enable/disable this drill down chart.
                        choices:
                            - enable
                            - disable
            favorite:
                description:
                    - Favorite.
                choices:
                    - no
                    - yes
            graph-type:
                description:
                    - Graph type.
                choices:
                    - none
                    - bar
                    - pie
                    - line
                    - flow
            legend:
                description:
                    - Enable/Disable Legend area.
                choices:
                    - enable
                    - disable
            legend-font-size:
                description:
                    - Font size of legend area.
            name:
                description:
                    - Chart Widget Name
                required: true
            period:
                description:
                    - Time period.
                choices:
                    - last24h
                    - last7d
            policy:
                description:
                    - Used by monitor policy.
            style:
                description:
                    - Style.
                choices:
                    - auto
                    - manual
            title:
                description:
                    - Chart title.
            title-font-size:
                description:
                    - Font size of chart title.
            type:
                description:
                    - Chart type.
                choices:
                    - graph
                    - table
            value-series:
                description:
                    - Value series of pie chart.
                suboptions:
                    databind:
                        description:
                            - Value series value expression.
            x-series:
                description:
                    - X-series of chart.
                suboptions:
                    caption:
                        description:
                            - X-series caption.
                    caption-font-size:
                        description:
                            - X-series caption font size.
                    databind:
                        description:
                            - X-series value expression.
                    font-size:
                        description:
                            - X-series label font size.
                    is-category:
                        description:
                            - X-series represent category or not.
                        choices:
                            - yes
                            - no
                    label-angle:
                        description:
                            - X-series label angle.
                        choices:
                            - 45-degree
                            - vertical
                            - horizontal
                    scale-direction:
                        description:
                            - Scale increase or decrease.
                        choices:
                            - decrease
                            - increase
                    scale-format:
                        description:
                            - Date/time format.
                        choices:
                            - YYYY-MM-DD-HH-MM
                            - YYYY-MM-DD HH
                            - YYYY-MM-DD
                            - YYYY-MM
                            - YYYY
                            - HH-MM
                            - MM-DD
                    scale-step:
                        description:
                            - Scale step.
                    scale-unit:
                        description:
                            - Scale unit.
                        choices:
                            - minute
                            - hour
                            - day
                            - month
                            - year
                    unit:
                        description:
                            - X-series unit.
            y-series:
                description:
                    - Y-series of chart.
                suboptions:
                    caption:
                        description:
                            - Y-series caption.
                    caption-font-size:
                        description:
                            - Y-series caption font size.
                    databind:
                        description:
                            - Y-series value expression.
                    extra-databind:
                        description:
                            - Extra Y-series value.
                    extra-y:
                        description:
                            - Allow another Y-series value
                        choices:
                            - enable
                            - disable
                    extra-y-legend:
                        description:
                            - Extra Y-series legend type/name.
                    font-size:
                        description:
                            - Y-series label font size.
                    group:
                        description:
                            - Y-series group option.
                    label-angle:
                        description:
                            - Y-series label angle.
                        choices:
                            - 45-degree
                            - vertical
                            - horizontal
                    unit:
                        description:
                            - Y-series unit.
                    y-legend:
                        description:
                            - First Y-series legend type/name.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Report chart widget configuration.
    fortios_report_chart:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      report_chart:
        state: "present"
        background: "<your_own_value>"
        category: "misc"
        category-series:
            databind: "<your_own_value>"
            font-size: "7"
        color-palette: "<your_own_value>"
        column:
         -
            detail-unit: "<your_own_value>"
            detail-value: "<your_own_value>"
            footer-unit: "<your_own_value>"
            footer-value: "<your_own_value>"
            header-value: "<your_own_value>"
            id:  "15"
            mapping:
             -
                displayname: "<your_own_value>"
                id:  "18"
                op: "none"
                value-type: "integer"
                value1: "<your_own_value>"
                value2: "<your_own_value>"
        comments: "<your_own_value>"
        dataset: "<your_own_value>"
        dimension: "2D"
        drill-down-charts:
         -
            chart-name: "<your_own_value>"
            id:  "28"
            status: "enable"
        favorite: "no"
        graph-type: "none"
        legend: "enable"
        legend-font-size: "33"
        name: "default_name_34"
        period: "last24h"
        policy: "36"
        style: "auto"
        title: "<your_own_value>"
        title-font-size: "39"
        type: "graph"
        value-series:
            databind: "<your_own_value>"
        x-series:
            caption: "<your_own_value>"
            caption-font-size: "45"
            databind: "<your_own_value>"
            font-size: "47"
            is-category: "yes"
            label-angle: "45-degree"
            scale-direction: "decrease"
            scale-format: "YYYY-MM-DD-HH-MM"
            scale-step: "52"
            scale-unit: "minute"
            unit: "<your_own_value>"
        y-series:
            caption: "<your_own_value>"
            caption-font-size: "57"
            databind: "<your_own_value>"
            extra-databind: "<your_own_value>"
            extra-y: "enable"
            extra-y-legend: "<your_own_value>"
            font-size: "62"
            group: "<your_own_value>"
            label-angle: "45-degree"
            unit: "<your_own_value>"
            y-legend: "<your_own_value>"
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


def filter_report_chart_data(json):
    option_list = ['background', 'category', 'category-series',
                   'color-palette', 'column', 'comments',
                   'dataset', 'dimension', 'drill-down-charts',
                   'favorite', 'graph-type', 'legend',
                   'legend-font-size', 'name', 'period',
                   'policy', 'style', 'title',
                   'title-font-size', 'type', 'value-series',
                   'x-series', 'y-series']
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


def report_chart(data, fos):
    vdom = data['vdom']
    report_chart_data = data['report_chart']
    flattened_data = flatten_multilists_attributes(report_chart_data)
    filtered_data = filter_report_chart_data(flattened_data)
    if report_chart_data['state'] == "present":
        return fos.set('report',
                       'chart',
                       data=filtered_data,
                       vdom=vdom)

    elif report_chart_data['state'] == "absent":
        return fos.delete('report',
                          'chart',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_report(data, fos):
    login(data)

    if data['report_chart']:
        resp = report_chart(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "report_chart": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "background": {"required": False, "type": "str"},
                "category": {"required": False, "type": "str",
                             "choices": ["misc", "traffic", "event",
                                         "virus", "webfilter", "attack",
                                         "spam", "dlp", "app-ctrl",
                                         "vulnerability"]},
                "category-series": {"required": False, "type": "dict",
                                    "options": {
                                        "databind": {"required": False, "type": "str"},
                                        "font-size": {"required": False, "type": "int"}
                                    }},
                "color-palette": {"required": False, "type": "str"},
                "column": {"required": False, "type": "list",
                           "options": {
                               "detail-unit": {"required": False, "type": "str"},
                               "detail-value": {"required": False, "type": "str"},
                               "footer-unit": {"required": False, "type": "str"},
                               "footer-value": {"required": False, "type": "str"},
                               "header-value": {"required": False, "type": "str"},
                               "id": {"required": True, "type": "int"},
                               "mapping": {"required": False, "type": "list",
                                           "options": {
                                               "displayname": {"required": False, "type": "str"},
                                               "id": {"required": True, "type": "int"},
                                               "op": {"required": False, "type": "str",
                                                      "choices": ["none", "greater", "greater-equal",
                                                                  "less", "less-equal", "equal",
                                                                  "between"]},
                                               "value-type": {"required": False, "type": "str",
                                                              "choices": ["integer", "string"]},
                                               "value1": {"required": False, "type": "str"},
                                               "value2": {"required": False, "type": "str"}
                                           }}
                           }},
                "comments": {"required": False, "type": "str"},
                "dataset": {"required": False, "type": "str"},
                "dimension": {"required": False, "type": "str",
                              "choices": ["2D", "3D"]},
                "drill-down-charts": {"required": False, "type": "list",
                                      "options": {
                                          "chart-name": {"required": False, "type": "str"},
                                          "id": {"required": True, "type": "int"},
                                          "status": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]}
                                      }},
                "favorite": {"required": False, "type": "str",
                             "choices": ["no", "yes"]},
                "graph-type": {"required": False, "type": "str",
                               "choices": ["none", "bar", "pie",
                                           "line", "flow"]},
                "legend": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "legend-font-size": {"required": False, "type": "int"},
                "name": {"required": True, "type": "str"},
                "period": {"required": False, "type": "str",
                           "choices": ["last24h", "last7d"]},
                "policy": {"required": False, "type": "int"},
                "style": {"required": False, "type": "str",
                          "choices": ["auto", "manual"]},
                "title": {"required": False, "type": "str"},
                "title-font-size": {"required": False, "type": "int"},
                "type": {"required": False, "type": "str",
                         "choices": ["graph", "table"]},
                "value-series": {"required": False, "type": "dict",
                                 "options": {
                                     "databind": {"required": False, "type": "str"}
                                 }},
                "x-series": {"required": False, "type": "dict",
                             "options": {
                                 "caption": {"required": False, "type": "str"},
                                 "caption-font-size": {"required": False, "type": "int"},
                                 "databind": {"required": False, "type": "str"},
                                 "font-size": {"required": False, "type": "int"},
                                 "is-category": {"required": False, "type": "str",
                                                 "choices": ["yes", "no"]},
                                 "label-angle": {"required": False, "type": "str",
                                                 "choices": ["45-degree", "vertical", "horizontal"]},
                                 "scale-direction": {"required": False, "type": "str",
                                                     "choices": ["decrease", "increase"]},
                                 "scale-format": {"required": False, "type": "str",
                                                  "choices": ["YYYY-MM-DD-HH-MM", "YYYY-MM-DD HH", "YYYY-MM-DD",
                                                              "YYYY-MM", "YYYY", "HH-MM",
                                                              "MM-DD"]},
                                 "scale-step": {"required": False, "type": "int"},
                                 "scale-unit": {"required": False, "type": "str",
                                                "choices": ["minute", "hour", "day",
                                                            "month", "year"]},
                                 "unit": {"required": False, "type": "str"}
                             }},
                "y-series": {"required": False, "type": "dict",
                             "options": {
                                 "caption": {"required": False, "type": "str"},
                                 "caption-font-size": {"required": False, "type": "int"},
                                 "databind": {"required": False, "type": "str"},
                                 "extra-databind": {"required": False, "type": "str"},
                                 "extra-y": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                                 "extra-y-legend": {"required": False, "type": "str"},
                                 "font-size": {"required": False, "type": "int"},
                                 "group": {"required": False, "type": "str"},
                                 "label-angle": {"required": False, "type": "str",
                                                 "choices": ["45-degree", "vertical", "horizontal"]},
                                 "unit": {"required": False, "type": "str"},
                                 "y-legend": {"required": False, "type": "str"}
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

    global fos
    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_report(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
