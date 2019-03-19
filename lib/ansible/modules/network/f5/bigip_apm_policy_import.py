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
module: bigip_apm_policy_import
short_description: Manage BIG-IP APM policy or APM access profile imports
description:
   - Manage BIG-IP APM policy or APM access profile imports.
version_added: 2.8
options:
  name:
    description:
      - The name of the APM policy or APM access profile to create or override.
    type: str
    required: True
  type:
    description:
      - Specifies the type of item to export from device.
    type: str
    choices:
      - profile_access
      - access_policy
    default: profile_access
  source:
    description:
      - Full path to a file to be imported into the BIG-IP APM.
    type: path
  force:
    description:
      - When set to C(yes) any existing policy with the same name will be overwritten by the new import.
      - If policy does not exist this setting is ignored.
    default: no
    type: bool
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
notes:
  - Due to ID685681 it is not possible to execute ng_* tools via REST api on v12.x and 13.x, once this is fixed
    this restriction will be removed.
  - Requires BIG-IP >= 14.0.0
extends_documentation_fragment: f5
author:
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Import APM profile
  bigip_apm_policy_import:
    name: new_apm_profile
    source: /root/apm_profile.tar.gz
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Import APM policy
  bigip_apm_policy_import:
    name: new_apm_policy
    source: /root/apm_policy.tar.gz
    type: access_policy
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Override existing APM policy
  bigip_asm_policy:
    name: new_apm_policy
    source: /root/apm_policy.tar.gz
    force: yes
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost
'''

RETURN = r'''
source:
  description: Local path to APM policy file.
  returned: changed
  type: str
  sample: /root/some_policy.tar.gz
name:
  description: Name of the APM policy or APM access profile to be created/overwritten.
  returned: changed
  type: str
  sample: APM_policy_global
type:
  description: Set to specify type of item to export.
  returned: changed
  type: str
  sample: access_policy
force:
  description: Set when overwriting an existing policy or profile.
  returned: changed
  type: bool
  sample: yes
'''

import os
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
    from library.module_utils.network.f5.icontrol import upload_file
    from library.module_utils.network.f5.icontrol import tmos_version
    from library.module_utils.network.f5.icontrol import module_provisioned
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.icontrol import upload_file
    from ansible.module_utils.network.f5.icontrol import tmos_version
    from ansible.module_utils.network.f5.icontrol import module_provisioned


class Parameters(AnsibleF5Parameters):
    api_map = {

    }

    api_attributes = [

    ]

    returnables = [
        'name',
        'source',
        'type',

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
        if not module_provisioned(self.client, 'apm'):
            raise F5ModuleError(
                "APM must be provisioned to use this module."
            )

        if self.version_less_than_14():
            raise F5ModuleError('Due to bug ID685681 it is not possible to use this module on TMOS version below 14.x')

        result = dict()

        changed = self.policy_import()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def version_less_than_14(self):
        version = tmos_version(self.client)
        if LooseVersion(version) < LooseVersion('14.0.0'):
            return True
        return False

    def policy_import(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True
        if self.exists():
            if self.want.force is False:
                return False

        self.import_file_to_device()
        self.remove_temp_file_from_device()
        return True

    def exists(self):
        if self.want.type == 'access_policy':
            uri = "https://{0}:{1}/mgmt/tm/apm/policy/access-policy/{2}".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                transform_name(self.want.partition, self.want.name)
            )
        else:
            uri = "https://{0}:{1}/mgmt/tm/apm/profile/access/{2}".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                transform_name(self.want.partition, self.want.name)
            )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

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

    def import_file_to_device(self):
        name = os.path.split(self.want.source)[1]
        self.upload_file_to_device(self.want.source, name)

        cmd = 'ng_import -s /var/config/rest/downloads/{0} {1} -p {2}'.format(name, self.want.name, self.want.partition)

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
                raise F5ModuleError(response['commandResult'])
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return True

    def remove_temp_file_from_device(self):
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
            force=dict(
                type='bool',
                default='no'
            ),
            type=dict(
                default='profile_access',
                choices=['profile_access', 'access_policy']
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
