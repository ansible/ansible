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
module: bigip_asm_policy_import
short_description: Manage BIG-IP ASM policy imports
description:
   - Manage BIG-IP ASM policies policy imports.
version_added: 2.8
options:
  name:
    description:
      - The ASM policy to create or override.
    type: str
    required: True
  inline:
    description:
      - When specified the ASM policy is created from a provided string.
      - Content needs to be provided in a valid XML format otherwise the operation will fail.
    type: str
  source:
    description:
      - Full path to a policy file to be imported into the BIG-IP ASM.
      - Policy files exported from newer versions of BIG-IP cannot be imported into older
        versions of BIG-IP. The opposite, however, is true; you can import older into
        newer.
      - The file format can be binary of XML.
    type: path
  force:
    description:
      - When set to C(yes) any existing policy with the same name will be overwritten by the new import.
      - Works for both inline and file imports, if the policy does not exist this setting is ignored.
    default: no
    type: bool
  partition:
    description:
      - Device partition to create policy on.
    type: str
    default: Common
extends_documentation_fragment: f5
author:
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Import ASM policy
  bigip_asm_policy_import:
    name: new_asm_policy
    file: /root/asm_policy.xml
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Import ASM policy inline
  bigip_asm_policy_import:
    name: foo-policy4
    inline: <xml>content</xml>
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Override existing ASM policy
  bigip_asm_policy:
    name: new_asm_policy
    file: /root/asm_policy_new.xml
    force: yes
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost
'''

RETURN = r'''
source:
  description: Local path to an ASM policy file.
  returned: changed
  type: str
  sample: /root/some_policy.xml
inline:
  description: Contents of policy as an inline string
  returned: changed
  type: str
  sample: <xml>foobar contents</xml>
name:
  description: Name of the ASM policy to be created/overwritten
  returned: changed
  type: str
  sample: Asm_APP1_Transparent
force:
  description: Set when overwriting an existing policy
  returned: changed
  type: bool
  sample: yes
'''

import os
import time
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.icontrol import upload_file
    from library.module_utils.network.f5.icontrol import module_provisioned
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.icontrol import upload_file
    from ansible.module_utils.network.f5.icontrol import module_provisioned


class Parameters(AnsibleF5Parameters):
    updatables = []

    returnables = [
        'name',
        'inline',
        'source',
        'force'
    ]

    api_attributes = [
        'file',
        'name',
    ]

    api_map = {
        'file': 'inline',
        'filename': 'source',
    }


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


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            return self.__default(param)

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.changes = UsableChanges()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = UsableChanges(params=changed)

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def exec_module(self):
        if not module_provisioned(self.client, 'asm'):
            raise F5ModuleError(
                "ASM must be provisioned to use this module."
            )

        result = dict()

        changed = self.policy_import()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def policy_import(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True
        if self.exists():
            if self.want.force is False:
                return False
        if self.want.inline:
            task = self.inline_import()
            self.wait_for_task(task)
            return True

        self.import_file_to_device()
        self.remove_temp_policy_from_device()
        return True

    def exists(self):
        uri = 'https://{0}:{1}/mgmt/tm/asm/policies/'.format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )

        query = "?$filter=contains(name,'{0}')+and+contains(partition,'{1}')&$select=name,partition".format(
            self.want.name, self.want.partition
        )
        resp = self.client.api.get(uri + query)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'items' in response and response['items'] != []:
            return True
        return False

    def upload_file_to_device(self, content, name):
        url = 'https://{0}:{1}/mgmt/shared/file-transfer/uploads'.format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        try:
            upload_file(self.client, url, content, name)
        except F5ModuleError:
            raise F5ModuleError(
                "Failed to upload the file."
            )

    def _get_policy_link(self):
        uri = 'https://{0}:{1}/mgmt/tm/asm/policies/'.format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )

        query = "?$filter=contains(name,'{0}')+and+contains(partition,'{1}')&$select=name,partition".format(
            self.want.name, self.want.partition
        )
        resp = self.client.api.get(uri + query)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        policy_link = response['items'][0]['selfLink']
        return policy_link

    def inline_import(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/asm/tasks/import-policy/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )

        if self.want.force:
            params.update(dict(policyReference={'link': self._get_policy_link()}))
            params.pop('name')

        resp = self.client.api.post(uri, json=params)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return response['id']

    def wait_for_task(self, task_id):
        uri = "https://{0}:{1}/mgmt/tm/asm/tasks/import-policy/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            task_id
        )
        while True:
            resp = self.client.api.get(uri)

            try:
                response = resp.json()
            except ValueError as ex:
                raise F5ModuleError(str(ex))

            if 'code' in response and response['code'] == 400:
                if 'message' in response:
                    raise F5ModuleError(response['message'])
                else:
                    raise F5ModuleError(resp.content)

            if response['status'] in ['COMPLETED', 'FAILURE']:
                break
            time.sleep(1)

        if response['status'] == 'FAILURE':
            raise F5ModuleError(
                'Failed to import ASM policy.'
            )
        if response['status'] == 'COMPLETED':
            return True

    def import_file_to_device(self):
        name = os.path.split(self.want.source)[1]
        self.upload_file_to_device(self.want.source, name)
        time.sleep(2)

        full_name = fq_name(self.want.partition, self.want.name)

        if self.want.force:
            cmd = 'tmsh load asm policy {0} file /var/config/rest/downloads/{1} overwrite'.format(full_name, name)
        else:
            cmd = 'tmsh load asm policy {0} file /var/config/rest/downloads/{1}'.format(full_name, name)

        uri = "https://{0}:{1}/mgmt/tm/util/bash/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        args = dict(
            command='run',
            utilCmdArgs='-c "{0}"'.format(cmd)
        )
        resp = self.client.api.post(uri, json=args)

        try:
            response = resp.json()
            if 'commandResult' in response:
                if 'Unexpected Error' in response['commandResult']:
                    raise F5ModuleError(response['commandResult'])
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return True

    def remove_temp_policy_from_device(self):
        name = os.path.split(self.want.source)[1]
        tpath_name = '/var/config/rest/downloads/{0}'.format(name)
        uri = "https://{0}:{1}/mgmt/tm/util/unix-rm/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        args = dict(
            command='run',
            utilCmdArgs=tpath_name
        )
        resp = self.client.api.post(uri, json=args)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(
                required=True,
            ),
            source=dict(type='path'),
            inline=dict(),
            force=dict(
                type='bool',
                default='no'
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.mutually_exclusive = [
            ['source', 'inline']
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        mutually_exclusive=spec.mutually_exclusive
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
