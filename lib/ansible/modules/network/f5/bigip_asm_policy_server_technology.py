#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_asm_policy_server_technology
short_description: Manages Server Technology on ASM policy
description:
  - Manages Server Technology on ASM policy.
version_added: 2.8
options:
  name:
    description:
      - Specifies the name of the server technology to apply on or remove from the ASM policy.
    type: str
    required: True
    choices:
      - jQuery
      - Java Servlets/JSP
      - ASP
      - WebDAV
      - IIS
      - Front Page Server Extensions (FPSE)
      - ASP.NET
      - Microsoft Windows
      - Unix/Linux
      - Macromedia ColdFusion
      - WordPress
      - Apache Tomcat
      - Apache/NCSA HTTP Server
      - Outlook Web Access
      - PHP
      - Microsoft SQL Server
      - Oracle
      - MySQL
      - Lotus Domino
      - BEA Systems WebLogic Server
      - Macromedia JRun
      - Novell
      - Cisco
      - SSI (Server Side Includes)
      - Proxy Servers
      - CGI
      - Sybase/ASE
      - IBM DB2
      - PostgreSQL
      - XML
      - Apache Struts
      - Elasticsearch
      - JBoss
      - Citrix
      - Node.js
      - Django
      - MongoDB
      - Ruby
      - JavaServer Faces (JSF)
      - Joomla
      - Jetty
  policy_name:
    description:
      - Specifies the name of an existing ASM policy to add or remove server technology.
    type: str
    required: True
  state:
    description:
      - When C(present), ensures that the resource exists.
      - When C(absent), ensures the resource is removed.
    type: str
    default: present
    choices:
      - present
      - absent
  partition:
    description:
      - This parameter is only used when identifying ASM policy.
    type: str
    default: Common
notes:
  - This module is primarily used as a component of configuring ASM policy in Ansible Galaxy ASM Policy Role.
  - Requires BIG-IP >= 13.0.0
extends_documentation_fragment: f5
author:
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Add Server Technology to ASM Policy
  bigip_asm_policy_server_technology:
    name: Joomla
    policy_name: FooPolicy
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
- name: Remove Server Technology from ASM Policy
  bigip_asm_policy_server_technology:
    name: Joomla
    policy_name: FooPolicy
    state: absent
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
policy_name:
  description: The name of the ASM policy
  returned: changed
  type: str
  sample: FooPolicy
name:
  description: The name of Server Technology added/removed on ASM policy
  returned: changed
  type: str
  sample: Joomla
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from distutils.version import LooseVersion

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.icontrol import tmos_version
    from library.module_utils.network.f5.icontrol import module_provisioned
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.icontrol import tmos_version
    from ansible.module_utils.network.f5.icontrol import module_provisioned


class Parameters(AnsibleF5Parameters):
    api_map = {

    }

    api_attributes = [

    ]

    returnables = [
        'policy_name',
        'name'

    ]

    updatables = [

    ]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    pass


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class UsableChanges(Changes):
    pass


class ReportableChanges(Changes):
    pass


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = Changes(params=changed)

    def exec_module(self):
        if not module_provisioned(self.client, 'asm'):
            raise F5ModuleError(
                "ASM must be provisioned to use this module."
            )
        if self.version_is_less_than_13():
            raise F5ModuleError(
                "This module requires TMOS version 13.x and above."
            )

        changed = False
        result = dict()
        state = self.want.state

        if state == "present":
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def version_is_less_than_13(self):
        version = tmos_version(self.client)
        if LooseVersion(version) < LooseVersion('13.0.0'):
            return True
        else:
            return False

    def present(self):
        if self.exists():
            return False
        else:
            return self.create()

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        return True

    def create(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def exists(self):
        policy_id = self._get_policy_id()
        server_link = self._get_server_tech_link()
        uri = 'https://{0}:{1}/mgmt/tm/asm/policies/{2}/server-technologies/'.format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            policy_id,
        )
        resp = self.client.api.get(uri)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'items' in response and response['items'] != []:
            for st in response['items']:
                if st['serverTechnologyReference']['link'] == server_link:
                    self.want.tech_id = st['id']
                    return True
        return False

    def _get_policy_id(self):
        policy_id = None
        uri = "https://{0}:{1}/mgmt/tm/asm/policies/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        query = "?$filter=contains(name,'{0}')+and+contains(partition,'{1}')&$select=name,id".format(
            self.want.policy_name, self.want.partition
        )
        resp = self.client.api.get(uri + query)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'items' in response and response['items'] != []:
            policy_id = response['items'][0]['id']

        if not policy_id:
            raise F5ModuleError(
                "The policy with the name {0} does not exist".format(self.want.policy_name)
            )
        return policy_id

    def _get_server_tech_link(self):
        link = None
        uri = "https://{0}:{1}/mgmt/tm/asm/server-technologies/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        query = "?$filter=contains(serverTechnologyName,'{0}')".format(self.want.name)
        resp = self.client.api.get(uri + query)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 409, 404]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

        if 'items' in response:
            link = response['items'][0]['selfLink']
            return link
        return link

    def create_on_device(self):
        policy_id = self._get_policy_id()

        uri = "https://{0}:{1}/mgmt/tm/asm/policies/{2}/server-technologies/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            policy_id
        )

        params = dict(serverTechnologyReference={'link': self._get_server_tech_link()})
        resp = self.client.api.post(uri, json=params)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 409]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return True

    def remove_from_device(self):
        policy_id = self._get_policy_id()
        tech_id = self.want.tech_id
        uri = 'https://{0}:{1}/mgmt/tm/asm/policies/{2}/server-technologies/{3}'.format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            policy_id,
            tech_id,
        )
        response = self.client.api.delete(uri)
        if response.status in [200, 201]:
            return True
        raise F5ModuleError(response.content)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.tech = [
            'jQuery',
            'Java Servlets/JSP',
            'ASP',
            'WebDAV',
            'IIS',
            'Front Page Server Extensions (FPSE)',
            'ASP.NET',
            'Microsoft Windows',
            'Unix/Linux',
            'Macromedia ColdFusion',
            'WordPress',
            'Apache Tomcat',
            'Apache/NCSA HTTP Server',
            'Outlook Web Access',
            'PHP',
            'Microsoft SQL Server',
            'Oracle',
            'MySQL',
            'Lotus Domino',
            'BEA Systems WebLogic Server',
            'Macromedia JRun',
            'Novell',
            'Cisco',
            'SSI (Server Side Includes)',
            'Proxy Servers',
            'CGI',
            'Sybase/ASE',
            'IBM DB2',
            'PostgreSQL',
            'XML',
            'Apache Struts',
            'Elasticsearch',
            'JBoss',
            'Citrix',
            'Node.js',
            'Django',
            'MongoDB',
            'Ruby',
            'JavaServer Faces (JSF)',
            'Joomla',
            'Jetty'
        ]
        argument_spec = dict(
            policy_name=dict(
                required=True
            ),
            name=dict(
                choices=self.tech,
                required=True
            ),
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            )

        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
