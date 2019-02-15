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
module: fortios_report_theme
short_description: Report themes configuratio in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify report feature and theme category.
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
    report_theme:
        description:
            - Report themes configuration
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            bullet-list-style:
                description:
                    - Bullet list style.
            column-count:
                description:
                    - Report page column count.
                choices:
                    - 1
                    - 2
                    - 3
            default-html-style:
                description:
                    - Default HTML report style.
            default-pdf-style:
                description:
                    - Default PDF report style.
            graph-chart-style:
                description:
                    - Graph chart style.
            heading1-style:
                description:
                    - Report heading style.
            heading2-style:
                description:
                    - Report heading style.
            heading3-style:
                description:
                    - Report heading style.
            heading4-style:
                description:
                    - Report heading style.
            hline-style:
                description:
                    - Horizontal line style.
            image-style:
                description:
                    - Image style.
            name:
                description:
                    - Report theme name.
                required: true
            normal-text-style:
                description:
                    - Normal text style.
            numbered-list-style:
                description:
                    - Numbered list style.
            page-footer-style:
                description:
                    - Report page footer style.
            page-header-style:
                description:
                    - Report page header style.
            page-orient:
                description:
                    - Report page orientation.
                choices:
                    - portrait
                    - landscape
            page-style:
                description:
                    - Report page style.
            report-subtitle-style:
                description:
                    - Report subtitle style.
            report-title-style:
                description:
                    - Report title style.
            table-chart-caption-style:
                description:
                    - Table chart caption style.
            table-chart-even-row-style:
                description:
                    - Table chart even row style.
            table-chart-head-style:
                description:
                    - Table chart head row style.
            table-chart-odd-row-style:
                description:
                    - Table chart odd row style.
            table-chart-style:
                description:
                    - Table chart style.
            toc-heading1-style:
                description:
                    - Table of contents heading style.
            toc-heading2-style:
                description:
                    - Table of contents heading style.
            toc-heading3-style:
                description:
                    - Table of contents heading style.
            toc-heading4-style:
                description:
                    - Table of contents heading style.
            toc-title-style:
                description:
                    - Table of contents title style.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Report themes configuration
    fortios_report_theme:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      report_theme:
        state: "present"
        bullet-list-style: "<your_own_value>"
        column-count: "1"
        default-html-style: "<your_own_value>"
        default-pdf-style: "<your_own_value>"
        graph-chart-style: "<your_own_value>"
        heading1-style: "<your_own_value>"
        heading2-style: "<your_own_value>"
        heading3-style: "<your_own_value>"
        heading4-style: "<your_own_value>"
        hline-style: "<your_own_value>"
        image-style: "<your_own_value>"
        name: "default_name_14"
        normal-text-style: "<your_own_value>"
        numbered-list-style: "<your_own_value>"
        page-footer-style: "<your_own_value>"
        page-header-style: "<your_own_value>"
        page-orient: "portrait"
        page-style: "<your_own_value>"
        report-subtitle-style: "<your_own_value>"
        report-title-style: "<your_own_value>"
        table-chart-caption-style: "<your_own_value>"
        table-chart-even-row-style: "<your_own_value>"
        table-chart-head-style: "<your_own_value>"
        table-chart-odd-row-style: "<your_own_value>"
        table-chart-style: "<your_own_value>"
        toc-heading1-style: "<your_own_value>"
        toc-heading2-style: "<your_own_value>"
        toc-heading3-style: "<your_own_value>"
        toc-heading4-style: "<your_own_value>"
        toc-title-style: "<your_own_value>"
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


def filter_report_theme_data(json):
    option_list = ['bullet-list-style', 'column-count', 'default-html-style',
                   'default-pdf-style', 'graph-chart-style', 'heading1-style',
                   'heading2-style', 'heading3-style', 'heading4-style',
                   'hline-style', 'image-style', 'name',
                   'normal-text-style', 'numbered-list-style', 'page-footer-style',
                   'page-header-style', 'page-orient', 'page-style',
                   'report-subtitle-style', 'report-title-style', 'table-chart-caption-style',
                   'table-chart-even-row-style', 'table-chart-head-style', 'table-chart-odd-row-style',
                   'table-chart-style', 'toc-heading1-style', 'toc-heading2-style',
                   'toc-heading3-style', 'toc-heading4-style', 'toc-title-style']
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


def report_theme(data, fos):
    vdom = data['vdom']
    report_theme_data = data['report_theme']
    flattened_data = flatten_multilists_attributes(report_theme_data)
    filtered_data = filter_report_theme_data(flattened_data)
    if report_theme_data['state'] == "present":
        return fos.set('report',
                       'theme',
                       data=filtered_data,
                       vdom=vdom)

    elif report_theme_data['state'] == "absent":
        return fos.delete('report',
                          'theme',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_report(data, fos):
    login(data)

    if data['report_theme']:
        resp = report_theme(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "report_theme": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "bullet-list-style": {"required": False, "type": "str"},
                "column-count": {"required": False, "type": "str",
                                 "choices": ["1", "2", "3"]},
                "default-html-style": {"required": False, "type": "str"},
                "default-pdf-style": {"required": False, "type": "str"},
                "graph-chart-style": {"required": False, "type": "str"},
                "heading1-style": {"required": False, "type": "str"},
                "heading2-style": {"required": False, "type": "str"},
                "heading3-style": {"required": False, "type": "str"},
                "heading4-style": {"required": False, "type": "str"},
                "hline-style": {"required": False, "type": "str"},
                "image-style": {"required": False, "type": "str"},
                "name": {"required": True, "type": "str"},
                "normal-text-style": {"required": False, "type": "str"},
                "numbered-list-style": {"required": False, "type": "str"},
                "page-footer-style": {"required": False, "type": "str"},
                "page-header-style": {"required": False, "type": "str"},
                "page-orient": {"required": False, "type": "str",
                                "choices": ["portrait", "landscape"]},
                "page-style": {"required": False, "type": "str"},
                "report-subtitle-style": {"required": False, "type": "str"},
                "report-title-style": {"required": False, "type": "str"},
                "table-chart-caption-style": {"required": False, "type": "str"},
                "table-chart-even-row-style": {"required": False, "type": "str"},
                "table-chart-head-style": {"required": False, "type": "str"},
                "table-chart-odd-row-style": {"required": False, "type": "str"},
                "table-chart-style": {"required": False, "type": "str"},
                "toc-heading1-style": {"required": False, "type": "str"},
                "toc-heading2-style": {"required": False, "type": "str"},
                "toc-heading3-style": {"required": False, "type": "str"},
                "toc-heading4-style": {"required": False, "type": "str"},
                "toc-title-style": {"required": False, "type": "str"}

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
