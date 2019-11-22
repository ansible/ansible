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
module: fortios_report_theme
short_description: Report themes configuration in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify report feature and theme category.
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
    report_theme:
        description:
            - Report themes configuration
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
            bullet_list_style:
                description:
                    - Bullet list style.
                type: str
            column_count:
                description:
                    - Report page column count.
                type: str
                choices:
                    - 1
                    - 2
                    - 3
            default_html_style:
                description:
                    - Default HTML report style.
                type: str
            default_pdf_style:
                description:
                    - Default PDF report style.
                type: str
            graph_chart_style:
                description:
                    - Graph chart style.
                type: str
            heading1_style:
                description:
                    - Report heading style.
                type: str
            heading2_style:
                description:
                    - Report heading style.
                type: str
            heading3_style:
                description:
                    - Report heading style.
                type: str
            heading4_style:
                description:
                    - Report heading style.
                type: str
            hline_style:
                description:
                    - Horizontal line style.
                type: str
            image_style:
                description:
                    - Image style.
                type: str
            name:
                description:
                    - Report theme name.
                required: true
                type: str
            normal_text_style:
                description:
                    - Normal text style.
                type: str
            numbered_list_style:
                description:
                    - Numbered list style.
                type: str
            page_footer_style:
                description:
                    - Report page footer style.
                type: str
            page_header_style:
                description:
                    - Report page header style.
                type: str
            page_orient:
                description:
                    - Report page orientation.
                type: str
                choices:
                    - portrait
                    - landscape
            page_style:
                description:
                    - Report page style.
                type: str
            report_subtitle_style:
                description:
                    - Report subtitle style.
                type: str
            report_title_style:
                description:
                    - Report title style.
                type: str
            table_chart_caption_style:
                description:
                    - Table chart caption style.
                type: str
            table_chart_even_row_style:
                description:
                    - Table chart even row style.
                type: str
            table_chart_head_style:
                description:
                    - Table chart head row style.
                type: str
            table_chart_odd_row_style:
                description:
                    - Table chart odd row style.
                type: str
            table_chart_style:
                description:
                    - Table chart style.
                type: str
            toc_heading1_style:
                description:
                    - Table of contents heading style.
                type: str
            toc_heading2_style:
                description:
                    - Table of contents heading style.
                type: str
            toc_heading3_style:
                description:
                    - Table of contents heading style.
                type: str
            toc_heading4_style:
                description:
                    - Table of contents heading style.
                type: str
            toc_title_style:
                description:
                    - Table of contents title style.
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
  - name: Report themes configuration
    fortios_report_theme:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      report_theme:
        bullet_list_style: "<your_own_value>"
        column_count: "1"
        default_html_style: "<your_own_value>"
        default_pdf_style: "<your_own_value>"
        graph_chart_style: "<your_own_value>"
        heading1_style: "<your_own_value>"
        heading2_style: "<your_own_value>"
        heading3_style: "<your_own_value>"
        heading4_style: "<your_own_value>"
        hline_style: "<your_own_value>"
        image_style: "<your_own_value>"
        name: "default_name_14"
        normal_text_style: "<your_own_value>"
        numbered_list_style: "<your_own_value>"
        page_footer_style: "<your_own_value>"
        page_header_style: "<your_own_value>"
        page_orient: "portrait"
        page_style: "<your_own_value>"
        report_subtitle_style: "<your_own_value>"
        report_title_style: "<your_own_value>"
        table_chart_caption_style: "<your_own_value>"
        table_chart_even_row_style: "<your_own_value>"
        table_chart_head_style: "<your_own_value>"
        table_chart_odd_row_style: "<your_own_value>"
        table_chart_style: "<your_own_value>"
        toc_heading1_style: "<your_own_value>"
        toc_heading2_style: "<your_own_value>"
        toc_heading3_style: "<your_own_value>"
        toc_heading4_style: "<your_own_value>"
        toc_title_style: "<your_own_value>"
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


def filter_report_theme_data(json):
    option_list = ['bullet_list_style', 'column_count', 'default_html_style',
                   'default_pdf_style', 'graph_chart_style', 'heading1_style',
                   'heading2_style', 'heading3_style', 'heading4_style',
                   'hline_style', 'image_style', 'name',
                   'normal_text_style', 'numbered_list_style', 'page_footer_style',
                   'page_header_style', 'page_orient', 'page_style',
                   'report_subtitle_style', 'report_title_style', 'table_chart_caption_style',
                   'table_chart_even_row_style', 'table_chart_head_style', 'table_chart_odd_row_style',
                   'table_chart_style', 'toc_heading1_style', 'toc_heading2_style',
                   'toc_heading3_style', 'toc_heading4_style', 'toc_title_style']
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


def report_theme(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['report_theme'] and data['report_theme']:
        state = data['report_theme']['state']
    else:
        state = True
    report_theme_data = data['report_theme']
    filtered_data = underscore_to_hyphen(filter_report_theme_data(report_theme_data))

    if state == "present":
        return fos.set('report',
                       'theme',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('report',
                          'theme',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_report(data, fos):

    if data['report_theme']:
        resp = report_theme(data, fos)

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
        "report_theme": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "bullet_list_style": {"required": False, "type": "str"},
                "column_count": {"required": False, "type": "str",
                                 "choices": ["1", "2", "3"]},
                "default_html_style": {"required": False, "type": "str"},
                "default_pdf_style": {"required": False, "type": "str"},
                "graph_chart_style": {"required": False, "type": "str"},
                "heading1_style": {"required": False, "type": "str"},
                "heading2_style": {"required": False, "type": "str"},
                "heading3_style": {"required": False, "type": "str"},
                "heading4_style": {"required": False, "type": "str"},
                "hline_style": {"required": False, "type": "str"},
                "image_style": {"required": False, "type": "str"},
                "name": {"required": True, "type": "str"},
                "normal_text_style": {"required": False, "type": "str"},
                "numbered_list_style": {"required": False, "type": "str"},
                "page_footer_style": {"required": False, "type": "str"},
                "page_header_style": {"required": False, "type": "str"},
                "page_orient": {"required": False, "type": "str",
                                "choices": ["portrait", "landscape"]},
                "page_style": {"required": False, "type": "str"},
                "report_subtitle_style": {"required": False, "type": "str"},
                "report_title_style": {"required": False, "type": "str"},
                "table_chart_caption_style": {"required": False, "type": "str"},
                "table_chart_even_row_style": {"required": False, "type": "str"},
                "table_chart_head_style": {"required": False, "type": "str"},
                "table_chart_odd_row_style": {"required": False, "type": "str"},
                "table_chart_style": {"required": False, "type": "str"},
                "toc_heading1_style": {"required": False, "type": "str"},
                "toc_heading2_style": {"required": False, "type": "str"},
                "toc_heading3_style": {"required": False, "type": "str"},
                "toc_heading4_style": {"required": False, "type": "str"},
                "toc_title_style": {"required": False, "type": "str"}

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
