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
module: fortios_report_chart
short_description: Report chart widget configuration in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify report feature and chart category.
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
    report_chart:
        description:
            - Report chart widget configuration.
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
            background:
                description:
                    - Chart background.
                type: str
            category:
                description:
                    - Category.
                type: str
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
            category_series:
                description:
                    - Category series of pie chart.
                type: dict
                suboptions:
                    databind:
                        description:
                            - Category series value expression.
                        type: str
                    font_size:
                        description:
                            - Font size of category-series title.
                        type: int
            color_palette:
                description:
                    - Color palette (system will pick color automatically by default).
                type: str
            column:
                description:
                    - Table column definition.
                type: list
                suboptions:
                    detail_unit:
                        description:
                            - Detail unit of column.
                        type: str
                    detail_value:
                        description:
                            - Detail value of column.
                        type: str
                    footer_unit:
                        description:
                            - Footer unit of column.
                        type: str
                    footer_value:
                        description:
                            - Footer value of column.
                        type: str
                    header_value:
                        description:
                            - Display name of table header.
                        type: str
                    id:
                        description:
                            - ID.
                        required: true
                        type: int
                    mapping:
                        description:
                            - Show detail in certain display value for certain condition.
                        type: list
                        suboptions:
                            displayname:
                                description:
                                    - Display name.
                                type: str
                            id:
                                description:
                                    - id
                                required: true
                                type: int
                            op:
                                description:
                                    - Comparison operator.
                                type: str
                                choices:
                                    - none
                                    - greater
                                    - greater-equal
                                    - less
                                    - less-equal
                                    - equal
                                    - between
                            value_type:
                                description:
                                    - Value type.
                                type: str
                                choices:
                                    - integer
                                    - string
                            value1:
                                description:
                                    - Value 1.
                                type: str
                            value2:
                                description:
                                    - Value 2.
                                type: str
            comments:
                description:
                    - Comment.
                type: str
            dataset:
                description:
                    - Bind dataset to chart.
                type: str
            dimension:
                description:
                    - Dimension.
                type: str
                choices:
                    - 2D
                    - 3D
            drill_down_charts:
                description:
                    - Drill down charts.
                type: list
                suboptions:
                    chart_name:
                        description:
                            - Drill down chart name.
                        type: str
                    id:
                        description:
                            - Drill down chart ID.
                        required: true
                        type: int
                    status:
                        description:
                            - Enable/disable this drill down chart.
                        type: str
                        choices:
                            - enable
                            - disable
            favorite:
                description:
                    - Favorite.
                type: str
                choices:
                    - no
                    - yes
            graph_type:
                description:
                    - Graph type.
                type: str
                choices:
                    - none
                    - bar
                    - pie
                    - line
                    - flow
            legend:
                description:
                    - Enable/Disable Legend area.
                type: str
                choices:
                    - enable
                    - disable
            legend_font_size:
                description:
                    - Font size of legend area.
                type: int
            name:
                description:
                    - Chart Widget Name
                required: true
                type: str
            period:
                description:
                    - Time period.
                type: str
                choices:
                    - last24h
                    - last7d
            policy:
                description:
                    - Used by monitor policy.
                type: int
            style:
                description:
                    - Style.
                type: str
                choices:
                    - auto
                    - manual
            title:
                description:
                    - Chart title.
                type: str
            title_font_size:
                description:
                    - Font size of chart title.
                type: int
            type:
                description:
                    - Chart type.
                type: str
                choices:
                    - graph
                    - table
            value_series:
                description:
                    - Value series of pie chart.
                type: dict
                suboptions:
                    databind:
                        description:
                            - Value series value expression.
                        type: str
            x_series:
                description:
                    - X-series of chart.
                type: dict
                suboptions:
                    caption:
                        description:
                            - X-series caption.
                        type: str
                    caption_font_size:
                        description:
                            - X-series caption font size.
                        type: int
                    databind:
                        description:
                            - X-series value expression.
                        type: str
                    font_size:
                        description:
                            - X-series label font size.
                        type: int
                    is_category:
                        description:
                            - X-series represent category or not.
                        type: str
                        choices:
                            - yes
                            - no
                    label_angle:
                        description:
                            - X-series label angle.
                        type: str
                        choices:
                            - 45-degree
                            - vertical
                            - horizontal
                    scale_direction:
                        description:
                            - Scale increase or decrease.
                        type: str
                        choices:
                            - decrease
                            - increase
                    scale_format:
                        description:
                            - Date/time format.
                        type: str
                        choices:
                            - YYYY-MM-DD-HH-MM
                            - YYYY-MM-DD HH
                            - YYYY-MM-DD
                            - YYYY-MM
                            - YYYY
                            - HH-MM
                            - MM-DD
                    scale_step:
                        description:
                            - Scale step.
                        type: int
                    scale_unit:
                        description:
                            - Scale unit.
                        type: str
                        choices:
                            - minute
                            - hour
                            - day
                            - month
                            - year
                    unit:
                        description:
                            - X-series unit.
                        type: str
            y_series:
                description:
                    - Y-series of chart.
                type: dict
                suboptions:
                    caption:
                        description:
                            - Y-series caption.
                        type: str
                    caption_font_size:
                        description:
                            - Y-series caption font size.
                        type: int
                    databind:
                        description:
                            - Y-series value expression.
                        type: str
                    extra_databind:
                        description:
                            - Extra Y-series value.
                        type: str
                    extra_y:
                        description:
                            - Allow another Y-series value
                        type: str
                        choices:
                            - enable
                            - disable
                    extra_y_legend:
                        description:
                            - Extra Y-series legend type/name.
                        type: str
                    font_size:
                        description:
                            - Y-series label font size.
                        type: int
                    group:
                        description:
                            - Y-series group option.
                        type: str
                    label_angle:
                        description:
                            - Y-series label angle.
                        type: str
                        choices:
                            - 45-degree
                            - vertical
                            - horizontal
                    unit:
                        description:
                            - Y-series unit.
                        type: str
                    y_legend:
                        description:
                            - First Y-series legend type/name.
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
  - name: Report chart widget configuration.
    fortios_report_chart:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      report_chart:
        background: "<your_own_value>"
        category: "misc"
        category_series:
            databind: "<your_own_value>"
            font_size: "7"
        color_palette: "<your_own_value>"
        column:
         -
            detail_unit: "<your_own_value>"
            detail_value: "<your_own_value>"
            footer_unit: "<your_own_value>"
            footer_value: "<your_own_value>"
            header_value: "<your_own_value>"
            id:  "15"
            mapping:
             -
                displayname: "<your_own_value>"
                id:  "18"
                op: "none"
                value_type: "integer"
                value1: "<your_own_value>"
                value2: "<your_own_value>"
        comments: "<your_own_value>"
        dataset: "<your_own_value>"
        dimension: "2D"
        drill_down_charts:
         -
            chart_name: "<your_own_value>"
            id:  "28"
            status: "enable"
        favorite: "no"
        graph_type: "none"
        legend: "enable"
        legend_font_size: "33"
        name: "default_name_34"
        period: "last24h"
        policy: "36"
        style: "auto"
        title: "<your_own_value>"
        title_font_size: "39"
        type: "graph"
        value_series:
            databind: "<your_own_value>"
        x_series:
            caption: "<your_own_value>"
            caption_font_size: "45"
            databind: "<your_own_value>"
            font_size: "47"
            is_category: "yes"
            label_angle: "45-degree"
            scale_direction: "decrease"
            scale_format: "YYYY-MM-DD-HH-MM"
            scale_step: "52"
            scale_unit: "minute"
            unit: "<your_own_value>"
        y_series:
            caption: "<your_own_value>"
            caption_font_size: "57"
            databind: "<your_own_value>"
            extra_databind: "<your_own_value>"
            extra_y: "enable"
            extra_y_legend: "<your_own_value>"
            font_size: "62"
            group: "<your_own_value>"
            label_angle: "45-degree"
            unit: "<your_own_value>"
            y_legend: "<your_own_value>"
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


def filter_report_chart_data(json):
    option_list = ['background', 'category', 'category_series',
                   'color_palette', 'column', 'comments',
                   'dataset', 'dimension', 'drill_down_charts',
                   'favorite', 'graph_type', 'legend',
                   'legend_font_size', 'name', 'period',
                   'policy', 'style', 'title',
                   'title_font_size', 'type', 'value_series',
                   'x_series', 'y_series']
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


def report_chart(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['report_chart'] and data['report_chart']:
        state = data['report_chart']['state']
    else:
        state = True
    report_chart_data = data['report_chart']
    filtered_data = underscore_to_hyphen(filter_report_chart_data(report_chart_data))

    if state == "present":
        return fos.set('report',
                       'chart',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('report',
                          'chart',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_report(data, fos):

    if data['report_chart']:
        resp = report_chart(data, fos)

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
        "report_chart": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "background": {"required": False, "type": "str"},
                "category": {"required": False, "type": "str",
                             "choices": ["misc", "traffic", "event",
                                         "virus", "webfilter", "attack",
                                         "spam", "dlp", "app-ctrl",
                                         "vulnerability"]},
                "category_series": {"required": False, "type": "dict",
                                    "options": {
                                        "databind": {"required": False, "type": "str"},
                                        "font_size": {"required": False, "type": "int"}
                                    }},
                "color_palette": {"required": False, "type": "str"},
                "column": {"required": False, "type": "list",
                           "options": {
                               "detail_unit": {"required": False, "type": "str"},
                               "detail_value": {"required": False, "type": "str"},
                               "footer_unit": {"required": False, "type": "str"},
                               "footer_value": {"required": False, "type": "str"},
                               "header_value": {"required": False, "type": "str"},
                               "id": {"required": True, "type": "int"},
                               "mapping": {"required": False, "type": "list",
                                           "options": {
                                               "displayname": {"required": False, "type": "str"},
                                               "id": {"required": True, "type": "int"},
                                               "op": {"required": False, "type": "str",
                                                      "choices": ["none", "greater", "greater-equal",
                                                                  "less", "less-equal", "equal",
                                                                  "between"]},
                                               "value_type": {"required": False, "type": "str",
                                                              "choices": ["integer", "string"]},
                                               "value1": {"required": False, "type": "str"},
                                               "value2": {"required": False, "type": "str"}
                                           }}
                           }},
                "comments": {"required": False, "type": "str"},
                "dataset": {"required": False, "type": "str"},
                "dimension": {"required": False, "type": "str",
                              "choices": ["2D", "3D"]},
                "drill_down_charts": {"required": False, "type": "list",
                                      "options": {
                                          "chart_name": {"required": False, "type": "str"},
                                          "id": {"required": True, "type": "int"},
                                          "status": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]}
                                      }},
                "favorite": {"required": False, "type": "str",
                             "choices": ["no", "yes"]},
                "graph_type": {"required": False, "type": "str",
                               "choices": ["none", "bar", "pie",
                                           "line", "flow"]},
                "legend": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]},
                "legend_font_size": {"required": False, "type": "int"},
                "name": {"required": True, "type": "str"},
                "period": {"required": False, "type": "str",
                           "choices": ["last24h", "last7d"]},
                "policy": {"required": False, "type": "int"},
                "style": {"required": False, "type": "str",
                          "choices": ["auto", "manual"]},
                "title": {"required": False, "type": "str"},
                "title_font_size": {"required": False, "type": "int"},
                "type": {"required": False, "type": "str",
                         "choices": ["graph", "table"]},
                "value_series": {"required": False, "type": "dict",
                                 "options": {
                                     "databind": {"required": False, "type": "str"}
                                 }},
                "x_series": {"required": False, "type": "dict",
                             "options": {
                                 "caption": {"required": False, "type": "str"},
                                 "caption_font_size": {"required": False, "type": "int"},
                                 "databind": {"required": False, "type": "str"},
                                 "font_size": {"required": False, "type": "int"},
                                 "is_category": {"required": False, "type": "str",
                                                 "choices": ["yes", "no"]},
                                 "label_angle": {"required": False, "type": "str",
                                                 "choices": ["45-degree", "vertical", "horizontal"]},
                                 "scale_direction": {"required": False, "type": "str",
                                                     "choices": ["decrease", "increase"]},
                                 "scale_format": {"required": False, "type": "str",
                                                  "choices": ["YYYY-MM-DD-HH-MM", "YYYY-MM-DD HH", "YYYY-MM-DD",
                                                              "YYYY-MM", "YYYY", "HH-MM",
                                                              "MM-DD"]},
                                 "scale_step": {"required": False, "type": "int"},
                                 "scale_unit": {"required": False, "type": "str",
                                                "choices": ["minute", "hour", "day",
                                                            "month", "year"]},
                                 "unit": {"required": False, "type": "str"}
                             }},
                "y_series": {"required": False, "type": "dict",
                             "options": {
                                 "caption": {"required": False, "type": "str"},
                                 "caption_font_size": {"required": False, "type": "int"},
                                 "databind": {"required": False, "type": "str"},
                                 "extra_databind": {"required": False, "type": "str"},
                                 "extra_y": {"required": False, "type": "str",
                                             "choices": ["enable", "disable"]},
                                 "extra_y_legend": {"required": False, "type": "str"},
                                 "font_size": {"required": False, "type": "int"},
                                 "group": {"required": False, "type": "str"},
                                 "label_angle": {"required": False, "type": "str",
                                                 "choices": ["45-degree", "vertical", "horizontal"]},
                                 "unit": {"required": False, "type": "str"},
                                 "y_legend": {"required": False, "type": "str"}
                             }}

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
