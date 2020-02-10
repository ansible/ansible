#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, sookido
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: zabbix_template
short_description: Create/update/delete/dump Zabbix template
description:
    - This module allows you to create, modify, delete and dump Zabbix templates.
    - Multiple templates can be created or modified at once if passing JSON or XML to module.
version_added: "2.5"
author:
    - "sookido (@sookido)"
    - "Logan Vig (@logan2211)"
    - "Dusan Matejka (@D3DeFi)"
requirements:
    - "python >= 2.6"
    - "zabbix-api >= 0.5.4"
options:
    template_name:
        description:
            - Name of Zabbix template.
            - Required when I(template_json) or I(template_xml) are not used.
            - Mutually exclusive with I(template_json) and I(template_xml).
        required: false
        type: str
    template_json:
        description:
            - JSON dump of templates to import.
            - Multiple templates can be imported this way.
            - Mutually exclusive with I(template_name) and I(template_xml).
        required: false
        type: json
    template_xml:
        description:
            - XML dump of templates to import.
            - Multiple templates can be imported this way.
            - You are advised to pass XML structure matching the structure used by your version of Zabbix server.
            - Custom XML structure can be imported as long as it is valid, but may not yield consistent idempotent
              results on subsequent runs.
            - Mutually exclusive with I(template_name) and I(template_json).
        required: false
        version_added: '2.9'
        type: str
    template_groups:
        description:
            - List of host groups to add template to when template is created.
            - Replaces the current host groups the template belongs to if the template is already present.
            - Required when creating a new template with C(state=present) and I(template_name) is used.
              Not required when updating an existing template.
        required: false
        type: list
        elements: str
    link_templates:
        description:
            - List of template names to be linked to the template.
            - Templates that are not specified and are linked to the existing template will be only unlinked and not
              cleared from the template.
        required: false
        type: list
        elements: str
    clear_templates:
        description:
            - List of template names to be unlinked and cleared from the template.
            - This option is ignored if template is being created for the first time.
        required: false
        type: list
        elements: str
    macros:
        description:
            - List of user macros to create for the template.
            - Macros that are not specified and are present on the existing template will be replaced.
            - See examples on how to pass macros.
        required: false
        type: list
        elements: dict
        suboptions:
            name:
                description:
                    - Name of the macro.
                    - Must be specified in {$NAME} format.
                type: str
            value:
                description:
                    - Value of the macro.
                type: str
    dump_format:
        description:
            - Format to use when dumping template with C(state=dump).
        required: false
        choices: [json, xml]
        default: "json"
        version_added: '2.9'
        type: str
    state:
        description:
            - Required state of the template.
            - On C(state=present) template will be created/imported or updated depending if it is already present.
            - On C(state=dump) template content will get dumped into required format specified in I(dump_format).
            - On C(state=absent) template will be deleted.
        required: false
        choices: [present, absent, dump]
        default: "present"
        type: str

extends_documentation_fragment:
    - zabbix
'''

EXAMPLES = r'''
---
- name: Create a new Zabbix template linked to groups, macros and templates
  local_action:
    module: zabbix_template
    server_url: http://127.0.0.1
    login_user: username
    login_password: password
    template_name: ExampleHost
    template_groups:
      - Role
      - Role2
    link_templates:
      - Example template1
      - Example template2
    macros:
      - macro: '{$EXAMPLE_MACRO1}'
        value: 30000
      - macro: '{$EXAMPLE_MACRO2}'
        value: 3
      - macro: '{$EXAMPLE_MACRO3}'
        value: 'Example'
    state: present

- name: Unlink and clear templates from the existing Zabbix template
  local_action:
    module: zabbix_template
    server_url: http://127.0.0.1
    login_user: username
    login_password: password
    template_name: ExampleHost
    clear_templates:
      - Example template3
      - Example template4
    state: present

- name: Import Zabbix templates from JSON
  local_action:
    module: zabbix_template
    server_url: http://127.0.0.1
    login_user: username
    login_password: password
    template_json: "{{ lookup('file', 'zabbix_apache2.json') }}"
    state: present

- name: Import Zabbix templates from XML
  local_action:
    module: zabbix_template
    server_url: http://127.0.0.1
    login_user: username
    login_password: password
    template_xml: "{{ lookup('file', 'zabbix_apache2.json') }}"
    state: present

- name: Import Zabbix template from Ansible dict variable
  zabbix_template:
    login_user: username
    login_password: password
    server_url: http://127.0.0.1
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
    state: present

- name: Configure macros on the existing Zabbix template
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

- name: Delete Zabbix template
  local_action:
    module: zabbix_template
    server_url: http://127.0.0.1
    login_user: username
    login_password: password
    template_name: Template
    state: absent

- name: Dump Zabbix template as JSON
  local_action:
    module: zabbix_template
    server_url: http://127.0.0.1
    login_user: username
    login_password: password
    template_name: Template
    state: dump
  register: template_dump

- name: Dump Zabbix template as XML
  local_action:
    module: zabbix_template
    server_url: http://127.0.0.1
    login_user: username
    login_password: password
    template_name: Template
    dump_format: xml
    state: dump
  register: template_dump
'''

RETURN = r'''
---
template_json:
  description: The JSON dump of the template
  returned: when state is dump
  type: str
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

template_xml:
  description: dump of the template in XML representation
  returned: when state is dump and dump_format is xml
  type: str
  sample: |-
    <?xml version="1.0" ?>
    <zabbix_export>
        <version>4.2</version>
        <date>2019-07-12T13:37:26Z</date>
        <groups>
            <group>
                <name>Templates</name>
            </group>
        </groups>
        <templates>
            <template>
                <template>test</template>
                <name>Test Template</name>
                <description/>
                <groups>
                    <group>
                        <name>Templates</name>
                    </group>
                </groups>
                <applications/>
                <items/>
                <discovery_rules/>
                <httptests/>
                <macros/>
                <templates/>
                <screens/>
                <tags/>
            </template>
        </templates>
    </zabbix_export>
'''


import atexit
import json
import traceback
import xml.etree.ElementTree as ET

from distutils.version import LooseVersion
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native

try:
    from zabbix_api import ZabbixAPI, ZabbixAPIException

    HAS_ZABBIX_API = True
except ImportError:
    ZBX_IMP_ERR = traceback.format_exc()
    HAS_ZABBIX_API = False


class Template(object):
    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx

    # check if host group exists
    def check_host_group_exist(self, group_names):
        for group_name in group_names:
            result = self._zapi.hostgroup.get({'filter': {'name': group_name}})
            if not result:
                self._module.fail_json(msg="Hostgroup not found: %s" %
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

    def add_template(self, template_name, group_ids, link_template_ids, macros):
        if self._module.check_mode:
            self._module.exit_json(changed=True)

        self._zapi.template.create({'host': template_name, 'groups': group_ids, 'templates': link_template_ids,
                                    'macros': macros})

    def check_template_changed(self, template_ids, template_groups, link_templates, clear_templates,
                               template_macros, template_content, template_type):
        """Compares template parameters to already existing values if any are found.

        template_json - JSON structures are compared as deep sorted dictionaries,
        template_xml - XML structures are compared as strings, but filtered and formatted first,
        If none above is used, all the other arguments are compared to their existing counterparts
        retrieved from Zabbix API."""
        changed = False
        # Compare filtered and formatted XMLs strings for any changes. It is expected that provided
        # XML has same structure as Zabbix uses (e.g. it was optimally exported via Zabbix GUI or API)
        if template_content is not None and template_type == 'xml':
            existing_template = self.dump_template(template_ids, template_type='xml')

            if self.filter_xml_template(template_content) != self.filter_xml_template(existing_template):
                changed = True

            return changed

        existing_template = self.dump_template(template_ids, template_type='json')
        # Compare JSON objects as deep sorted python dictionaries
        if template_content is not None and template_type == 'json':
            parsed_template_json = self.load_json_template(template_content)
            if self.diff_template(parsed_template_json, existing_template):
                changed = True

            return changed

        # If neither template_json or template_xml were used, user provided all parameters via module options
        if template_groups is not None:
            existing_groups = [g['name'] for g in existing_template['zabbix_export']['groups']]

            if set(template_groups) != set(existing_groups):
                changed = True

        # Check if any new templates would be linked or any existing would be unlinked
        exist_child_templates = [t['name'] for t in existing_template['zabbix_export']['templates'][0]['templates']]
        if link_templates is not None:
            if set(link_templates) != set(exist_child_templates):
                changed = True

        # Mark that there will be changes when at least one existing template will be unlinked
        if clear_templates is not None:
            for t in clear_templates:
                if t in exist_child_templates:
                    changed = True
                    break

        if 'macros' not in existing_template['zabbix_export']['templates'][0]:
            existing_template['zabbix_export']['templates'][0]['macros'] = []

        if template_macros is not None:
            existing_macros = existing_template['zabbix_export']['templates'][0]['macros']
            if template_macros != existing_macros:
                changed = True

        return changed

    def update_template(self, template_ids, group_ids, link_template_ids, clear_template_ids, template_macros):
        template_changes = {}
        if group_ids is not None:
            template_changes.update({'groups': group_ids})

        if link_template_ids is not None:
            template_changes.update({'templates': link_template_ids})

        if clear_template_ids is not None:
            template_changes.update({'templates_clear': clear_template_ids})

        if template_macros is not None:
            template_changes.update({'macros': template_macros})

        if template_changes:
            # If we got here we know that only one template was provided via template_name
            template_changes.update({'templateid': template_ids[0]})
            self._zapi.template.update(template_changes)

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

    def dump_template(self, template_ids, template_type='json'):
        if self._module.check_mode:
            self._module.exit_json(changed=True)

        try:
            dump = self._zapi.configuration.export({'format': template_type, 'options': {'templates': template_ids}})
            if template_type == 'xml':
                return str(ET.tostring(ET.fromstring(dump.encode('utf-8')), encoding='utf-8'))
            else:
                return self.load_json_template(dump)

        except ZabbixAPIException as e:
            self._module.fail_json(msg='Unable to export template: %s' % e)

    def diff_template(self, template_json_a, template_json_b):
        # Compare 2 zabbix templates and return True if they differ.
        template_json_a = self.filter_template(template_json_a)
        template_json_b = self.filter_template(template_json_b)
        if self.ordered_json(template_json_a) == self.ordered_json(template_json_b):
            return False
        return True

    def filter_template(self, template_json):
        # Filter the template json to contain only the keys we will update
        keep_keys = set(['graphs', 'templates', 'triggers', 'value_maps'])
        unwanted_keys = set(template_json['zabbix_export']) - keep_keys
        for unwanted_key in unwanted_keys:
            del template_json['zabbix_export'][unwanted_key]

        # Versions older than 2.4 do not support description field within template
        desc_not_supported = False
        if LooseVersion(self._zapi.api_version()).version[:2] < LooseVersion('2.4').version:
            desc_not_supported = True

        # Filter empty attributes from template object to allow accurate comparison
        for template in template_json['zabbix_export']['templates']:
            for key in list(template.keys()):
                if not template[key] or (key == 'description' and desc_not_supported):
                    template.pop(key)

        return template_json

    def filter_xml_template(self, template_xml):
        """Filters out keys from XML template that may wary between exports (e.g date or version) and
        keys that are not imported via this module.

        It is advised that provided XML template exactly matches XML structure used by Zabbix"""
        # Strip last new line and convert string to ElementTree
        parsed_xml_root = self.load_xml_template(template_xml.strip())
        keep_keys = ['graphs', 'templates', 'triggers', 'value_maps']

        # Remove unwanted XML nodes
        for node in list(parsed_xml_root):
            if node.tag not in keep_keys:
                parsed_xml_root.remove(node)

        # Filter empty attributes from template objects to allow accurate comparison
        for template in list(parsed_xml_root.find('templates')):
            for element in list(template):
                if element.text is None and len(list(element)) == 0:
                    template.remove(element)

        # Filter new lines and indentation
        xml_root_text = list(line.strip() for line in ET.tostring(parsed_xml_root).split('\n'))
        return ''.join(xml_root_text)

    def load_json_template(self, template_json):
        try:
            return json.loads(template_json)
        except ValueError as e:
            self._module.fail_json(msg='Invalid JSON provided', details=to_native(e), exception=traceback.format_exc())

    def load_xml_template(self, template_xml):
        try:
            return ET.fromstring(template_xml)
        except ET.ParseError as e:
            self._module.fail_json(msg='Invalid XML provided', details=to_native(e), exception=traceback.format_exc())

    def import_template(self, template_content, template_type='json'):
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
            'templateLinkage': {
                'createMissing': True
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
            if LooseVersion(api_version).version[:2] <= LooseVersion('3.2').version:
                update_rules['applications']['updateExisting'] = True

            import_data = {'format': template_type, 'source': template_content, 'rules': update_rules}
            self._zapi.configuration.import_(import_data)
        except ZabbixAPIException as e:
            self._module.fail_json(msg='Unable to import template', details=to_native(e),
                                   exception=traceback.format_exc())


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False, default=None, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
            template_name=dict(type='str', required=False),
            template_json=dict(type='json', required=False),
            template_xml=dict(type='str', required=False),
            template_groups=dict(type='list', required=False),
            link_templates=dict(type='list', required=False),
            clear_templates=dict(type='list', required=False),
            macros=dict(type='list', required=False),
            dump_format=dict(type='str', required=False, default='json', choices=['json', 'xml']),
            state=dict(type='str', default="present", choices=['present', 'absent', 'dump']),
            timeout=dict(type='int', default=10)
        ),
        required_one_of=[
            ['template_name', 'template_json', 'template_xml']
        ],
        mutually_exclusive=[
            ['template_name', 'template_json', 'template_xml']
        ],
        required_if=[
            ['state', 'absent', ['template_name']],
            ['state', 'dump', ['template_name']]
        ],
        supports_check_mode=True
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg=missing_required_lib('zabbix-api', url='https://pypi.org/project/zabbix-api/'), exception=ZBX_IMP_ERR)

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    validate_certs = module.params['validate_certs']
    template_name = module.params['template_name']
    template_json = module.params['template_json']
    template_xml = module.params['template_xml']
    template_groups = module.params['template_groups']
    link_templates = module.params['link_templates']
    clear_templates = module.params['clear_templates']
    template_macros = module.params['macros']
    dump_format = module.params['dump_format']
    state = module.params['state']
    timeout = module.params['timeout']

    zbx = None
    try:
        zbx = ZabbixAPI(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password,
                        validate_certs=validate_certs)
        zbx.login(login_user, login_password)
        atexit.register(zbx.logout)
    except ZabbixAPIException as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    template = Template(module, zbx)

    # Identify template names for IDs retrieval
    # Template names are expected to reside in ['zabbix_export']['templates'][*]['template'] for both data types
    template_content, template_type = None, None
    if template_json is not None:
        template_type = 'json'
        template_content = template_json
        json_parsed = template.load_json_template(template_content)
        template_names = list(t['template'] for t in json_parsed['zabbix_export']['templates'])

    elif template_xml is not None:
        template_type = 'xml'
        template_content = template_xml
        xml_parsed = template.load_xml_template(template_content)
        template_names = list(t.find('template').text for t in list(xml_parsed.find('templates')))

    else:
        template_names = [template_name]

    template_ids = template.get_template_ids(template_names)

    if state == "absent":
        if not template_ids:
            module.exit_json(changed=False, msg="Template not found. No changed: %s" % template_name)

        template.delete_template(template_ids)
        module.exit_json(changed=True, result="Successfully deleted template %s" % template_name)

    elif state == "dump":
        if not template_ids:
            module.fail_json(msg='Template not found: %s' % template_name)

        if dump_format == 'json':
            module.exit_json(changed=False, template_json=template.dump_template(template_ids, template_type='json'))
        elif dump_format == 'xml':
            module.exit_json(changed=False, template_xml=template.dump_template(template_ids, template_type='xml'))

    elif state == "present":
        # Load all subelements for template that were provided by user
        group_ids = None
        if template_groups is not None:
            group_ids = template.get_group_ids_by_group_names(template_groups)

        link_template_ids = None
        if link_templates is not None:
            link_template_ids = template.get_template_ids(link_templates)

        clear_template_ids = None
        if clear_templates is not None:
            clear_template_ids = template.get_template_ids(clear_templates)

        if template_macros is not None:
            # Zabbix configuration.export does not differentiate python types (numbers are returned as strings)
            for macroitem in template_macros:
                for key in macroitem:
                    macroitem[key] = str(macroitem[key])

        if not template_ids:
            # Assume new templates are being added when no ID's were found
            if template_content is not None:
                template.import_template(template_content, template_type)
                module.exit_json(changed=True, result="Template import successful")

            else:
                if group_ids is None:
                    module.fail_json(msg='template_groups are required when creating a new Zabbix template')

                template.add_template(template_name, group_ids, link_template_ids, template_macros)
                module.exit_json(changed=True, result="Successfully added template: %s" % template_name)

        else:
            changed = template.check_template_changed(template_ids, template_groups, link_templates, clear_templates,
                                                      template_macros, template_content, template_type)

            if module.check_mode:
                module.exit_json(changed=changed)

            if changed:
                if template_type is not None:
                    template.import_template(template_content, template_type)
                else:
                    template.update_template(template_ids, group_ids, link_template_ids, clear_template_ids,
                                             template_macros)

            module.exit_json(changed=changed, result="Template successfully updated")


if __name__ == '__main__':
    main()
