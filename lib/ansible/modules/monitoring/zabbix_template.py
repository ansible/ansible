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
short_description: create/delete zabbix template
description:
    - create/delete zabbix template
version_added: "2.5"
author:
    - "@sookido"
requirements:
    - "python >= 2.6"
    - "zabbix-api >= 0.5.3"
options:
    template_name:
        description:
            - Name of zabbix template
        required: true
    template_groups:
        description:
            - List of template groups to create or delete.
        required: true
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
        choices: [ present, absent]
        default: "present"

extends_documentation_fragment:
    - zabbix
'''

EXAMPLES = '''
---
- name: create templates
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
'''

RETURN = '''
#defaults
'''


from ansible.module_utils.basic import AnsibleModule
try:
    from zabbix_api import ZabbixAPI

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

    def add_template(self, template_name, group_ids,
                     child_template_ids, macros):
        if self._module.check_mode:
            self._module.exit_json(changed=True)
        self._zapi.template.create({'host': template_name,
                                    'groups': group_ids,
                                    'templates': child_template_ids,
                                    'macros': macros})

    def update_template(self, templateids,
                        group_ids, child_template_ids,
                        clear_template_ids, macros):
        if self._module.check_mode:
            self._module.exit_json(changed=True)
        self._zapi.template.update(
            {'templateid': templateids, 'groups': group_ids,
             'templates': child_template_ids,
             'templates_clear': clear_template_ids,
             'macros': macros})

    def delete_template(self, templateids):
        if self._module.check_mode:
            self._module.exit_json(changed=True)
        self._zapi.template.delete(templateids)


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
            template_name=dict(type='str', required=True),
            template_groups=dict(type='list', required=True),
            link_templates=dict(type='list', required=False),
            clear_templates=dict(type='list', required=False),
            macros=dict(type='list', required=False),
            state=dict(default="present", choices=['present', 'absent']),
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
    template_groups = module.params['template_groups']
    link_templates = module.params['link_templates']
    clear_templates = module.params['clear_templates']
    macros = module.params['macros']
    state = module.params['state']
    timeout = module.params['timeout']

    zbx = None

    # login to zabbix
    try:
        zbx = ZabbixAPI(server_url, timeout=timeout,
                        user=http_login_user, passwd=http_login_password, validate_certs=validate_certs)
        zbx.login(login_user, login_password)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    template = Template(module, zbx)
    template_ids = template.get_template_ids([template_name])

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

    child_template_ids = []
    if link_templates:
        child_template_ids = template.get_template_ids(link_templates)

    clear_template_ids = []
    if clear_templates:
        clear_template_ids = template.get_template_ids(clear_templates)

    group_ids = template.get_group_ids_by_group_names(template_groups)
    if not group_ids:
        module.fail_json(msg='Template groups not found: %s' %
                         str(template_groups))

    if not template_ids:
        template.add_template(template_name, group_ids,
                              child_template_ids, macros)
        module.exit_json(changed=True,
                         result="Successfully added template: %s" %
                         template_name)
    else:
        template.update_template(template_ids[0], group_ids,
                                 child_template_ids, clear_template_ids,
                                 macros)
        module.exit_json(changed=True,
                         result="Successfully updateed template: %s" %
                         template_name)


if __name__ == '__main__':
    main()
