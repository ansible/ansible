#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2017, sookido
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: zabbix_template
short_description: create/delete/dump zabbix template
description:
    - create/delete/dump zabbix template
version_added: "2.5"
author:
    - "@sookido"
    - "Logan Vig (@logan2211)"
requirements:
    - "python >= 2.6"
    - "zabbix-api >= 0.5.3"
options:
    template_name:
        description:
            - Name of zabbix template.
            - It isn't required if and only if template_content is defined for import.
        required: false
    template_content:
        description:
            - Content of the template to be added.
            - It is required in import conditions when template_name is ignored. 
        required: false
    template_type:
        description:
            - The file format of the template to be imported.
        required: false
        choices: [json, xml]
        default: "json"
    template_groups:
        description:
            - List of template groups to create or delete.
        required: false
    link_templates:
        description:
            - List of templates linked to the template.
        required: false
    clear_templates:
        description:
            - List of templates cleared from the template.
            - see templates_clear in https://www.zabbix.com/documentation/3.0/manual/api/reference/template/update
        required: false
    macros:
        description:
            - List of templates macro
        required: false
    state:
        description:
            - state present create/update template, absent delete template
        required: false
        choices: [present, absent, dump]
        default: "present"

extends_documentation_fragment:
    - zabbix
'''

EXAMPLES = '''
---
# Creates a new zabbix template from linked template
- name: Create Zabbix template using linked template
  local_action:
    module: zabbix_template
    server_url: http://127.0.0.1
    login_user: username
    login_password: password
    template_name: ExampleHost
    template_json: "{'zabbix_export': {}}"
    template_groups:
      - Role
      - Role2
    link_templates:
      - Example template1
      - Example template2
    clear_templates:
      - Example template3
      - Example template4
    macros:
      - macro: '{$EXAMPLE_MACRO1}'
        value: 30000
      - macro: '{$EXAMPLE_MACRO2}'
        value: 3
      - macro: '{$EXAMPLE_MACRO3}'
        value: 'Example'
    state: present

# Create a new template from a json config definition
- name: Import Zabbix json template configuration
  local_action:
    module: zabbix_template
    server_url: http://127.0.0.1
    login_user: username
    login_password: password
    template_content: "{{ lookup('file', 'zabbix_apache2.json') }}"
    template_type: json
    template_groups:
      - Webservers
    state: present

# Import a template from Ansible variable dict
- name: Import Zabbix Template
  zabbix_template:
    login_user: username
    login_password: password
    server_url: http://127.0.0.1
    template_name: Test Template
    template_json:
      zabbix_export:
        version: '3.2'
        templates:
          - name: Template for Testing
            description: 'Testing template import'
            template: Test Template
            groups:
              - name: Templates
            applications:
              - name: Test Application
    template_groups: Templates
    state: present

# Add a macro to a template
- name: Set a macro on the Zabbix template
  local_action:
    module: zabbix_template
    server_url: http://127.0.0.1
    login_user: username
    login_password: password
    template_name: Template
    macros:
      - macro: '{$TEST_MACRO}'
        value: 'Example'
    state: present

# Remove a template
- name: Delete Zabbix template
  local_action:
    module: zabbix_template
    server_url: http://127.0.0.1
    login_user: username
    login_password: password
    template_name: Template
    state: absent

# Export template json definition
- name: Dump Zabbix template
  local_action:
    module: zabbix_template
    server_url: http://127.0.0.1
    login_user: username
    login_password: password
    template_name: Template
    template_type: xml
    state: dump
  register: template_dump
'''

RETURN = '''
template_content:
  description: The dump of the template
  returned: when state is dump
  type: string
  sample: {
        "zabbix_export":{
            "date":"2017-11-29T16:37:24Z",
            "templates":[{
                "templates":[],
                "description":"",
                "httptests":[],
                "screens":[],
                "applications":[],
                "discovery_rules":[],
                "groups":[{"name":"Templates"}],
                "name":"Test Template",
                "items":[],
                "macros":[],
                "template":"test"
            }],
            "version":"3.2",
            "groups":[{
                "name":"Templates"
            }]
        }
    }
'''

import json
import traceback

import sys
import xml.etree.ElementTree as ET
from tempfile import NamedTemporaryFile
import subprocess

from distutils.version import LooseVersion
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

try:
    from zabbix_api import ZabbixAPI, ZabbixAPIException

    HAS_ZABBIX_API = True
except ImportError:
    HAS_ZABBIX_API = False


class Template(object):

    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx
        self._important_configuration_keys = {'graphs', 'templates', 'triggers', 'value_maps'}

    # check if host group exists
    def check_host_group_exist(self, group_names):
        for group_name in group_names:
            result = self._zapi.hostgroup.get({'filter': {'name': group_name}})
            if not result:
                self._module.fail_json(msg="HostGroup not found: %s" %
                                       group_name)
        return True

    # get group ids by group names
    def get_group_ids_by_group_names(self, group_names):
        group_ids = []
        if group_names is None or len(group_names) == 0:
            return group_ids
        if self.check_host_group_exist(group_names):
            group_list = self._zapi.hostgroup.get(
                {'output': 'extend',
                 'filter': {'name': group_names}})
            for group in group_list:
                group_id = group['groupid']
                group_ids.append({'groupid': group_id})
        return group_ids

    def get_template_ids(self, template_list):
        template_ids = []
        if template_list is None or len(template_list) == 0:
            return template_ids
        for template in template_list:
            template_list = self._zapi.template.get(
                {'output': 'extend',
                 'filter': {'host': template}})
            if len(template_list) < 1:
                continue
            else:
                template_id = template_list[0]['templateid']
                template_ids.append(template_id)
        return template_ids

    def add_template(self, template_name, template_content, template_type, group_ids, child_template_ids, macros):
        if self._module.check_mode:
            self._module.exit_json(changed=True)
        self._zapi.template.create({'host': template_name,
                                    'groups': group_ids,
                                    'templates': child_template_ids,
                                    'macros': macros})

        self.import_template(template_content, template_type)

    def update_template(self, templateids, input_template, template_type,
                        group_ids, child_template_ids,
                        clear_template_ids, macros,
                        existing_template=None):
        changed = False
        template_changes = {}
        if group_ids is not None:
            template_changes.update({'groups': group_ids})
            changed = True
        if child_template_ids is not None:
            template_changes.update({'templates': child_template_ids})
            changed = True
        if macros is not None:
            template_changes.update({'macros': macros})
            changed = True
        do_import = False
        if input_template:
            if template_type == 'json':
                parsed_template_json = self.load_json_template(input_template)
                if self.diff_json_template(parsed_template_json, existing_template):
                    do_import = True
                    changed = True
            else:
                a = self.diff_xml_template(input_template, existing_template)
                # self._module.fail_json(msg=str(a))
                if self.diff_xml_template(input_template, existing_template):
                    do_import = True
                    changed = True

        if self._module.check_mode:
            self._module.exit_json(changed=changed)

        if template_changes:
            template_changes.update({
                'templateid': templateids,
                'templates_clear': clear_template_ids
            })
            self._zapi.template.update(template_changes)

        if do_import:
            self.import_template(input_template, template_type)

        return changed

    def delete_template(self, templateids):
        if self._module.check_mode:
            self._module.exit_json(changed=True)
        self._zapi.template.delete(templateids)

    def ordered_json(self, obj):
        # Deep sort json dicts for comparison
        if isinstance(obj, dict):
            return sorted((k, self.ordered_json(v)) for k, v in obj.items())
        if isinstance(obj, list):
            return sorted(self.ordered_json(x) for x in obj)
        else:
            return obj

    def dump_template(self, template_ids, template_type):
        if self._module.check_mode:
            self._module.exit_json(changed=True)
        try:
            dump = self._zapi.configuration.export({
                'format': template_type,
                'options': {'templates': template_ids}
            })

            if template_type == 'json':
                return self.load_json_template(dump)
            return dump

        except ZabbixAPIException as e:
            self._module.fail_json(msg='Unable to export template: %s' % e)

    def diff_json_template(self, template_json_a, template_json_b):
        # Compare 2 zabbix templates and return True if they differ.
        template_json_a = self.get_filtered_json(template_json_a)
        template_json_b = self.get_filtered_json(template_json_b)
        if self.ordered_json(template_json_a) == self.ordered_json(template_json_b):
            return False
        return True

    def get_filtered_json(self, template_json):
        # Filter the template json to contain only the keys we will update
        unwanted_keys = set(template_json['zabbix_export']) - self._important_configuration_keys
        for unwanted_key in unwanted_keys:
            del template_json['zabbix_export'][unwanted_key]
        return template_json

    def load_json_template(self, template_json):
        try:
            return json.loads(template_json)
        except ValueError as e:
            self._module.fail_json(
                msg='Invalid JSON provided',
                details=to_native(e),
                exception=traceback.format_exc()
            )

    @staticmethod
    def xml_attribute_to_str(k, v):
        return "{}=\"{}\"".format(k, v)

    def xml_node_to_str(self, n):
        attrs = sorted(n.attrib.items())
        astr = " ".join(self.xml_attribute_to_str(k, v) for k, v in attrs)
        s = n.tag
        if astr:
            s += " " + astr
        return s

    def node_key(self, n):
        return self.xml_node_to_str(n)

    @staticmethod
    def indent(s, level):
        return "  " * level + s

    def write_sorted(self, stream, node, level=0):
        children = node.getchildren()
        text = (node.text or "").strip()
        tail = (node.tail or "").strip()

        if children or text:
            children.sort(key=self.node_key)

            stream.write(self.indent("<" + self.xml_node_to_str(node) + ">\n", level))

            if text:
                stream.write(self.indent(text + "\n", level))

            for child in children:
                self.write_sorted(stream, child, level + 1)

            stream.write(self.indent("</" + node.tag + ">\n", level))
        else:
            stream.write(self.indent("<" + self.xml_node_to_str(node) + "/>\n", level))

        if tail:
            stream.write(self.indent(tail + "\n", level))

    if sys.version_info < (3, 0):
        # Python 2
        import codecs

        def unicode_writer(self, fp):
            return self.codecs.getwriter('utf-8')(fp)
    else:
        # Python 3
        @staticmethod
        def unicode_writer(fp):
            return fp

    def get_filtered_xml(self, input_xml_template):
        input_xml_template = input_xml_template.replace("\n", "").replace("\t", "").strip()
        root = ET.fromstring(input_xml_template)

        # Removing unimportant tags from xml.
        for child in root[:]:
            if child.tag not in self._important_configuration_keys:
                root.remove(child)

        return root

    def diff_xml_template(self, input_xml_template, existing_template, diffargs=["-u"]):
        tmp1 = self.unicode_writer(NamedTemporaryFile('w', delete=False))
        self.write_sorted(tmp1, self.get_filtered_xml(input_xml_template))
        tmp1.flush()

        tmp2 = self.unicode_writer(NamedTemporaryFile('w', delete=False))
        self.write_sorted(tmp2, self.get_filtered_xml(existing_template))
        tmp2.flush()

        args = ["diff"]
        args += diffargs
        args += [tmp1.name, tmp2.name]

        return subprocess.call(args)

    def import_template(self, template_content, template_type):
        # rules schema latest version
        update_rules = {
            'applications': {
                'createMissing': True,
                'deleteMissing': True
            },
            'discoveryRules': {
                'createMissing': True,
                'updateExisting': True,
                'deleteMissing': True
            },
            'graphs': {
                'createMissing': True,
                'updateExisting': True,
                'deleteMissing': True
            },
            'httptests': {
                'createMissing': True,
                'updateExisting': True,
                'deleteMissing': True
            },
            'items': {
                'createMissing': True,
                'updateExisting': True,
                'deleteMissing': True
            },
            'templates': {
                'createMissing': True,
                'updateExisting': True
            },
            'templateScreens': {
                'createMissing': True,
                'updateExisting': True,
                'deleteMissing': True
            },
            'triggers': {
                'createMissing': True,
                'updateExisting': True,
                'deleteMissing': True
            },
            'valueMaps': {
                'createMissing': True,
                'updateExisting': True
            }
        }

        try:
            # old api version support here
            api_version = self._zapi.api_version()
            # updateExisting for application removed from zabbix api after 3.2
            if LooseVersion(api_version).version[:2] <= LooseVersion(
                    '3.2').version:
                update_rules['applications']['updateExisting'] = True

            self._zapi.configuration.import_({
                'format': template_type,
                'source': template_content,
                'rules': update_rules
            })
        except ZabbixAPIException as e:
            self._module.fail_json(
                msg='Unable to import template',
                details=to_native(e),
                exception=traceback.format_exc()
            )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False,
                                     default=None, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
            template_name=dict(type='str', required=False),
            template_content=dict(type='str', required=False),
            template_type=dict(type='str', required=False, default="json", choices=['json', 'xml']),
            template_groups=dict(type='list', required=False),
            link_templates=dict(type='list', required=False),
            clear_templates=dict(type='list', required=False),
            macros=dict(type='list', required=False),
            state=dict(default="present", choices=['present', 'absent',
                                                   'dump']),
            timeout=dict(type='int', default=10)
        ),
        supports_check_mode=True
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg="Missing required zabbix-api module " +
                             "(check docs or install with: " +
                             "pip install zabbix-api)")

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    validate_certs = module.params['validate_certs']
    template_name = module.params['template_name']
    template_content = module.params['template_content']
    template_type = module.params['template_type']
    template_groups = module.params['template_groups']
    link_templates = module.params['link_templates']
    clear_templates = module.params['clear_templates']
    template_macros = module.params['macros']
    state = module.params['state']
    timeout = module.params['timeout']

    zbx = None

    # Login to zabbix
    try:
        zbx = ZabbixAPI(server_url, timeout=timeout,
                        user=http_login_user, passwd=http_login_password, validate_certs=validate_certs)
        zbx.login(login_user, login_password)
    except ZabbixAPIException as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    template = Template(module, zbx)

    # Taking the name of template.
    if template_name is None:
        if template_content is None:
            module.fail_json(msg="Missing template name or template_content")
        else:
            if template_type is None:
                module.fail_json(msg="Missing template type: it could be json or xml ")
            elif template_type == 'json':
                template_name = \
                    template.load_json_template(template_content)["zabbix_export"]['templates'][0]['template']
            elif template_type == 'xml':
                root = ET.fromstring(template_content)
                for child in root:
                    if child.tag == 'templates':
                        root = child
                for child in root:
                    if child.tag == 'template':
                        root = child
                for child in root:
                    if child.tag == 'name':
                        template_name = child.text

    template_ids = template.get_template_ids([template_name])
    existing_template = None
    if template_ids:
        existing_template = template.dump_template(template_ids, template_type)
    existing_template_json = None
    if template_ids:
        existing_template_json = template.dump_template(template_ids, 'json')

    # Delete template
    if state == "absent":
        # if template not found. no change, no fail
        if not template_ids:
            module.exit_json(changed=False,
                             msg="Template not found. " +
                                 "No changed: %s" % template_name)
        template.delete_template(template_ids)
        module.exit_json(changed=True,
                         result="Successfully delete template %s" %
                         template_name)

    elif state == "dump":
        if not template_ids:
            module.fail_json(msg='Template not found: %s' % template_name)
        module.exit_json(changed=False, template_content=existing_template)

    elif state == "present":
        child_template_ids = None
        if link_templates is not None:
            child_template_ids = template.get_template_ids(link_templates)

        clear_template_ids = []
        if clear_templates is not None:
            clear_template_ids = template.get_template_ids(clear_templates)

        group_ids = None
        if template_groups is not None:
            # If the template exists, compare the already set groups
            existing_groups = None
            if existing_template_json:
                existing_groups = \
                    set(list(group['name'] for group in existing_template_json['zabbix_export']['groups']))
            if not existing_groups or set(template_groups) != existing_groups:
                group_ids = template.get_group_ids_by_group_names(template_groups)

        macros = None
        if template_macros is not None:
            existing_macros = None
            if existing_template_json:
                existing_macros = set(existing_template_json['zabbix_export']['templates'][0]['macros'])
            if not existing_macros or set(template_macros) != existing_macros:
                macros = template_macros

        if not template_ids:
            if template_content:
                template.add_template(template_name, template_content, template_type, group_ids,
                                      child_template_ids, macros)
                module.exit_json(changed=True,
                                 result="Successfully added template: %s" %
                                 template_name)

        else:
            changed = template.update_template(template_ids[0], template_content, template_type,
                                               group_ids, child_template_ids,
                                               clear_template_ids, macros,
                                               existing_template)

            module.exit_json(changed=changed,
                             result="Successfully updated template: %s" %
                             template_name)


if __name__ == '__main__':
    main()
