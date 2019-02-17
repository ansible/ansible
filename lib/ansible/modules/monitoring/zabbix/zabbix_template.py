#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, sookido
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: zabbix_template
short_description: Create/delete/dump Zabbix template
description:
    - Create/delete/dump Zabbix template.
version_added: "2.5"
author:
    - "sookido (@sookido)"
    - "Logan Vig (@logan2211)"
requirements:
    - "python >= 2.6"
    - "zabbix-api >= 0.5.3"
options:
    template_name:
        description:
            - Name of Zabbix template.
            - Required when I(template_json) is not used.
        required: false
    template_json:
        description:
            - JSON dump of template to import.
        required: false
    template_groups:
        description:
            - List of template groups to create or delete.
            - Required when I(template_name) is used and C(state=present).
        required: false
    link_templates:
        description:
            - List of templates linked to the template.
        required: false
    clear_templates:
        description:
            - List of templates cleared from the template.
            - See templates_clear in https://www.zabbix.com/documentation/3.0/manual/api/reference/template/update
        required: false
    macros:
        description:
            - List of template macros.
        required: false
    state:
        description:
            - 'State: present - create/update template; absent - delete template'
        required: false
        choices: [present, absent, dump]
        default: "present"

extends_documentation_fragment:
    - zabbix
'''

EXAMPLES = '''
---
# Creates a new Zabbix template from linked template
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

# Create a new template from a JSON config definition
- name: Import Zabbix JSON template configuration
  local_action:
    module: zabbix_template
    server_url: http://127.0.0.1
    login_user: username
    login_password: password
    template_name: Apache2
    template_json: "{{ lookup('file', 'zabbix_apache2.json') }}"
    template_groups:
      - Webservers
    state: present

# Import a template from Ansible variable dict
- name: Import Zabbix template
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

# Export template JSON definition
- name: Dump Zabbix template
  local_action:
    module: zabbix_template
    server_url: http://127.0.0.1
    login_user: username
    login_password: password
    template_name: Template
    state: dump
  register: template_dump
'''

RETURN = '''
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
'''

from distutils.version import LooseVersion
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import json
import traceback


try:
    from zabbix_api import ZabbixAPI, ZabbixAPIException

    HAS_ZABBIX_API = True
except ImportError:
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

    def add_template(self, template_name, template_json, group_ids,
                     child_template_ids, macros):
        if self._module.check_mode:
            self._module.exit_json(changed=True)

        if template_json:
            self.import_template(template_json, template_name)
        else:
            self._zapi.template.create({'host': template_name,
                                        'groups': group_ids,
                                        'templates': child_template_ids,
                                        'macros': macros})

    def update_template(self, templateids, template_json,
                        group_ids, child_template_ids,
                        clear_template_ids, macros,
                        existing_template_json=None):
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
        if template_json:
            parsed_template_json = self.load_json_template(template_json)
            if self.diff_template(parsed_template_json,
                                  existing_template_json):
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
            self.import_template(template_json,
                                 existing_template_json['zabbix_export']['templates'][0]['template'])

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

    def dump_template(self, template_ids):
        if self._module.check_mode:
            self._module.exit_json(changed=True)
        try:
            dump = self._zapi.configuration.export({
                'format': 'json',
                'options': {'templates': template_ids}
            })
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
            for key in template.keys():
                if not template[key] or (key == 'description' and desc_not_supported):
                    template.pop(key)

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

    def import_template(self, template_json, template_name=None):
        parsed_template_json = self.load_json_template(template_json)
        if template_name != parsed_template_json['zabbix_export']['templates'][0]['template']:
            self._module.fail_json(msg='JSON template name does not match presented name')

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
            if LooseVersion(api_version).version[:2] <= LooseVersion(
                    '3.2').version:
                update_rules['applications']['updateExisting'] = True

            self._zapi.configuration.import_({
                'format': 'json',
                'source': template_json,
                'rules': update_rules
            })
        except ZabbixAPIException as e:
            self._module.fail_json(
                msg='Unable to import JSON template',
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
            template_json=dict(type='json', required=False),
            template_groups=dict(type='list', required=False),
            link_templates=dict(type='list', required=False),
            clear_templates=dict(type='list', required=False),
            macros=dict(type='list', required=False),
            state=dict(default="present", choices=['present', 'absent',
                                                   'dump']),
            timeout=dict(type='int', default=10)
        ),
        required_one_of=[['template_name', 'template_json']],
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
    template_json = module.params['template_json']
    template_groups = module.params['template_groups']
    link_templates = module.params['link_templates']
    clear_templates = module.params['clear_templates']
    template_macros = module.params['macros']
    state = module.params['state']
    timeout = module.params['timeout']

    zbx = None

    # login to zabbix
    try:
        zbx = ZabbixAPI(server_url, timeout=timeout,
                        user=http_login_user, passwd=http_login_password, validate_certs=validate_certs)
        zbx.login(login_user, login_password)
    except ZabbixAPIException as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    template = Template(module, zbx)
    if template_json and not template_name:
        # Ensure template_name is not empty for safety check in import_template
        template_loaded = template.load_json_template(template_json)
        template_name = template_loaded['zabbix_export']['templates'][0]['template']
    elif template_name and not template_groups and state == 'present':
        module.fail_json(msg="Option template_groups is required when template_json is not used")

    template_ids = template.get_template_ids([template_name])
    existing_template_json = None
    if template_ids:
        existing_template_json = template.dump_template(template_ids)

    # delete template
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
        module.exit_json(changed=False, template_json=existing_template_json)

    elif state == "present":
        child_template_ids = None
        if link_templates is not None:
            existing_child_templates = None
            if existing_template_json:
                existing_child_templates = set(list(
                    tmpl['name'] for tmpl in existing_template_json['zabbix_export']['templates'][0]['templates']))
            if not existing_template_json or set(link_templates) != existing_child_templates:
                child_template_ids = template.get_template_ids(link_templates)

        clear_template_ids = []
        if clear_templates is not None:
            clear_template_ids = template.get_template_ids(clear_templates)

        group_ids = None
        if template_groups is not None:
            # If the template exists, compare the already set groups
            existing_groups = None
            if existing_template_json:
                existing_groups = set(list(group['name'] for group in existing_template_json['zabbix_export']['groups']))
            if not existing_groups or set(template_groups) != existing_groups:
                group_ids = template.get_group_ids_by_group_names(template_groups)

        macros = None
        if template_macros is not None:
            existing_macros = None
            # zabbix configuration.export does not differentiate python types (numbers are returned as strings)
            for macroitem in template_macros:
                for key in macroitem:
                    macroitem[key] = str(macroitem[key])

            if existing_template_json:
                existing_macros = existing_template_json['zabbix_export']['templates'][0]['macros']
            if not existing_macros or template_macros != existing_macros:
                macros = template_macros

        if not template_ids:
            template.add_template(template_name, template_json, group_ids,
                                  child_template_ids, macros)
            module.exit_json(changed=True,
                             result="Successfully added template: %s" %
                             template_name)
        else:
            changed = template.update_template(template_ids[0], template_json,
                                               group_ids, child_template_ids,
                                               clear_template_ids, macros,
                                               existing_template_json)
            module.exit_json(changed=changed,
                             result="Successfully updated template: %s" %
                             template_name)


if __name__ == '__main__':
    main()
