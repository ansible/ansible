#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, sky-joker
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: zabbix_template_info
short_description: Gather information about Zabbix template
author:
    - sky-joker (@sky-joker)
version_added: '2.10'
description:
    - This module allows you to search for Zabbix template.
requirements:
    - "python >= 2.6"
    - "zabbix-api >= 0.5.4"
options:
    template_name:
        description:
            - Name of the template in Zabbix.
        required: true
        type: str
    format:
        description:
            - Format to use when dumping template.
        choices: ['json', 'xml']
        default: json
        type: str
    omit_date:
        description:
            - Removes the date field for the dumped template
        required: false
        type: bool
        default: false
extends_documentation_fragment:
  - zabbix
'''

EXAMPLES = '''
- name: Get Zabbix template as JSON
  zabbix_template_info:
    server_url: "http://zabbix.example.com/zabbix/"
    login_user: admin
    login_password: secret
    template_name: Template
    format: json
    omit_date: yes
  register: template_json

- name: Get Zabbix template as XML
  zabbix_template_info:
    server_url: "http://zabbix.example.com/zabbix/"
    login_user: admin
    login_password: secret
    template_name: Template
    format: xml
    omit_date: no
  register: template_json
'''

RETURN = '''
---
template_json:
  description: The JSON of the template
  returned: when format is json and omit_date is true
  type: str
  sample: {
            "zabbix_export": {
              "version": "4.0",
              "groups": [
                {
                  "name": "Templates"
                }
              ],
              "templates": [
                {
                  "template": "Test Template",
                  "name": "Template for Testing",
                  "description": "Testing template import",
                  "groups": [
                    {
                      "name": "Templates"
                    }
                  ],
                  "applications": [
                    {
                      "name": "Test Application"
                    }
                  ],
                  "items": [],
                  "discovery_rules": [],
                  "httptests": [],
                  "macros": [],
                  "templates": [],
                  "screens": []
                }
              ]
            }
          }

template_xml:
  description: The XML of the template
  returned: when format is xml and omit_date is false
  type: str
  sample: >-
    <zabbix_export>
        <version>4.0</version>
        <date>2019-10-27T14:49:57Z</date>
        <groups>
            <group>
                <name>Templates</name>
            </group>
        </groups>
        <templates>
            <template>
                <template>Test Template</template>
                <name>Template for Testing</name>
                <description>Testing template import</description>
                <groups>
                    <group>
                        <name>Templates</name>
                    </group>
                </groups>
                <applications>
                    <application>
                        <name>Test Application</name>
                    </application>
                </applications>
                <items />
                <discovery_rules />
                <httptests />
                <macros />
                <templates />
                <screens />
            </template>
        </templates>
    </zabbix_export>
'''

import atexit
import traceback
import json
import xml.etree.ElementTree as ET

try:
    from zabbix_api import ZabbixAPI
    from zabbix_api import Already_Exists
    from zabbix_api import ZabbixAPIException

    HAS_ZABBIX_API = True
except ImportError:
    ZBX_IMP_ERR = traceback.format_exc()
    HAS_ZABBIX_API = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native


class TemplateInfo(object):
    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx

    def get_template_id(self, template_name):
        template_id = []
        try:
            template_list = self._zapi.template.get(
                {
                    'output': 'extend',
                    'filter': {
                        'host': template_name
                    }
                }
            )
        except ZabbixAPIException as e:
            self._module.fail_json(msg='Failed to get template: %s' % e)

        if template_list:
            template_id.append(template_list[0]['templateid'])

        return template_id

    def load_json_template(self, template_json, omit_date=False):
        try:
            jsondoc = json.loads(template_json)
            # remove date field if requested
            if omit_date and 'date' in jsondoc['zabbix_export']:
                del jsondoc['zabbix_export']['date']
            return jsondoc
        except ValueError as e:
            self._module.fail_json(msg='Invalid JSON provided', details=to_native(e), exception=traceback.format_exc())

    def dump_template(self, template_id, template_type='json', omit_date=False):
        try:
            dump = self._zapi.configuration.export({'format': template_type, 'options': {'templates': template_id}})
            if template_type == 'xml':
                xmlroot = ET.fromstring(dump.encode('utf-8'))
                # remove date field if requested
                if omit_date:
                    date = xmlroot.find(".date")
                    if date is not None:
                        xmlroot.remove(date)
                return str(ET.tostring(xmlroot, encoding='utf-8').decode('utf-8'))
            else:
                return self.load_json_template(dump, omit_date)

        except ZabbixAPIException as e:
            self._module.fail_json(msg='Unable to export template: %s' % e)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False, default=None, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
            timeout=dict(type='int', default=10),
            template_name=dict(type='str', required=True),
            omit_date=dict(type='bool', required=False, default=False),
            format=dict(type='str', choices=['json', 'xml'], default='json')
        ),
        supports_check_mode=False
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg=missing_required_lib('zabbix-api', url='https://pypi.org/project/zabbix-api/'),
                         exception=ZBX_IMP_ERR)

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    validate_certs = module.params['validate_certs']
    timeout = module.params['timeout']
    template_name = module.params['template_name']
    omit_date = module.params['omit_date']
    format = module.params['format']

    try:
        zbx = ZabbixAPI(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password,
                        validate_certs=validate_certs)
        zbx.login(login_user, login_password)
        atexit.register(zbx.logout)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    template_info = TemplateInfo(module, zbx)

    template_id = template_info.get_template_id(template_name)

    if not template_id:
        module.fail_json(msg='Template not found: %s' % template_name)

    if format == 'json':
        module.exit_json(changed=False, template_json=template_info.dump_template(template_id, template_type='json', omit_date=omit_date))
    elif format == 'xml':
        module.exit_json(changed=False, template_xml=template_info.dump_template(template_id, template_type='xml', omit_date=omit_date))


if __name__ == "__main__":
    main()
