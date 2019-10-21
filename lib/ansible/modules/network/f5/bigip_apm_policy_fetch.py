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
module: bigip_apm_policy_fetch
short_description: Exports the APM policy or APM access profile from remote nodes.
description:
  - Exports the apm policy or APM access profile from remote nodes.
version_added: 2.8
options:
  name:
    description:
      - The name of the APM policy or APM access profile exported to create a file on the remote device for downloading.
    type: str
    required: True
  dest:
    description:
      - A directory to save the file into.
    type: path
  file:
    description:
      - The name of the file to be created on the remote device for downloading.
    type: str
  type:
    description:
      - Specifies the type of item to export from device.
    type: str
    choices:
      - profile_access
      - access_policy
    default: profile_access
  force:
    description:
      - If C(no), the file will only be transferred if it does not exist in the the destination.
    type: bool
    default: yes
  partition:
    description:
      - Device partition to which contain APM policy or APM access profile to export.
    type: str
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
- name: Export APM access profile
  bigip_apm_policy_fetch:
    name: foobar
    file: export_foo
    dest: /root/download
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Export APM access policy
  bigip_apm_policy_fetch:
    name: foobar
    file: export_foo
    dest: /root/download
    type: access_policy
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Export APM access profile, autogenerate name
  bigip_apm_policy_fetch:
    name: foobar
    dest: /root/download
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
name:
  description: Name of the APM policy or APM access profile to be exported.
  returned: changed
  type: str
  sample: APM_policy_global
file:
  description:
    - Name of the exported file on the remote BIG-IP to download. If not
      specified, then this will be a randomly generated filename.
  returned: changed
  type: str
  sample: foobar_file
dest:
  description: Local path to download exported APM policy.
  returned: changed
  type: str
  sample: /root/downloads/profile-foobar_file.conf.tar.gz
type:
  description: Set to specify type of item to export.
  returned: changed
  type: str
  sample: access_policy
'''

import os
import tempfile

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from distutils.version import LooseVersion

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.icontrol import download_file
    from library.module_utils.network.f5.icontrol import tmos_version
    from library.module_utils.network.f5.icontrol import module_provisioned
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.icontrol import download_file
    from ansible.module_utils.network.f5.icontrol import tmos_version
    from ansible.module_utils.network.f5.icontrol import module_provisioned


class Parameters(AnsibleF5Parameters):
    api_map = {}

    api_attributes = []

    returnables = [
        'name',
        'file',
        'dest',
        'type',
        'force',
    ]

    updatables = []


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    def _item_exists(self):
        if self.type == 'access_policy':
            uri = 'https://{0}:{1}/mgmt/tm/apm/policy/access-policy/{2}'.format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                transform_name(self.partition, self.name)
            )
        else:
            uri = 'https://{0}:{1}/mgmt/tm/apm/profile/access/{2}'.format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                transform_name(self.partition, self.name)
            )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'items' in response and response['items'] != []:
            return True
        return False

    @property
    def file(self):
        if self._values['file'] is not None:
            return self._values['file']
        result = next(tempfile._get_candidate_names()) + '.tar.gz'
        self._values['file'] = result
        return result

    @property
    def fulldest(self):
        result = None
        if os.path.isdir(self.dest):
            result = os.path.join(self.dest, self.file)
        else:
            if os.path.exists(os.path.dirname(self.dest)):
                result = self.dest
            else:
                try:
                    # os.path.exists() can return false in some
                    # circumstances where the directory does not have
                    # the execute bit for the current user set, in
                    # which case the stat() call will raise an OSError
                    os.stat(os.path.dirname(result))
                except OSError as e:
                    if "permission denied" in str(e).lower():
                        raise F5ModuleError(
                            "Destination directory {0} is not accessible".format(os.path.dirname(result))
                        )
                    raise F5ModuleError(
                        "Destination directory {0} does not exist".format(os.path.dirname(result))
                    )

        if not os.access(os.path.dirname(result), os.W_OK):
            raise F5ModuleError(
                "Destination {0} not writable".format(os.path.dirname(result))
            )
        return result

    @property
    def name(self):
        if not self._item_exists():
            raise F5ModuleError('The provided {0} with the name {1} does not exist on device.'.format(
                self.type, self._values['name'])
            )
        return self._values['name']


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

        self.export()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=True))
        return result

    def version_less_than_14(self):
        version = tmos_version(self.client)
        if LooseVersion(version) < LooseVersion('14.0.0'):
            return True
        return False

    def export(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def update(self):
        if not self.want.force:
            raise F5ModuleError(
                "File '{0}' already exists.".format(self.want.fulldest)
            )
        self.execute()

    def create(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        self.execute()
        return True

    def download(self):
        self.download_from_device(self.want.fulldest)
        if os.path.exists(self.want.fulldest):
            return True
        raise F5ModuleError(
            "Failed to download the remote file."
        )

    def execute(self):
        self.download()
        self.remove_temp_file_from_device()
        return True

    def exists(self):
        if os.path.exists(self.want.fulldest):
            return True
        return False

    def create_on_device(self):
        cmd = 'ng_export -t {0} {1} {2} -p {3}'.format(
            self.want.type, self.want.name, self.want.name, self.want.partition
        )
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
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        if 'commandResult' in response:
            raise F5ModuleError('Item export command failed.')
        return True

    def _move_file_to_download(self):
        if self.want.type == 'access_policy':
            item = 'policy'
        else:
            item = 'profile'

        name = '{0}-{1}.conf.tar.gz'.format(item, self.want.name)
        move_path = '/shared/tmp/{0} {1}/{2}'.format(
            name,
            '/ts/var/rest',
            self.want.file
        )
        params = dict(
            command='run',
            utilCmdArgs=move_path
        )

        uri = "https://{0}:{1}/mgmt/tm/util/unix-mv/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )

        resp = self.client.api.post(uri, json=params)

        try:
            response = resp.json()
            if 'commandResult' in response:
                if 'cannot stat' in response['commandResult']:
                    raise F5ModuleError(response['commandResult'])
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

        return True

    def download_from_device(self, dest):
        url = 'https://{0}:{1}/mgmt/tm/asm/file-transfer/downloads/{2}'.format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.file
        )
        try:
            download_file(self.client, url, dest)
        except F5ModuleError:
            raise F5ModuleError(
                "Failed to download the file."
            )
        if os.path.exists(self.want.dest):
            return True
        return False

    def remove_temp_file_from_device(self):
        tpath_name = '/ts/var/rest/{0}'.format(self.want.file)
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
            dest=dict(
                type='path'
            ),
            type=dict(
                default='profile_access',
                choices=['profile_access', 'access_policy']
            ),
            file=dict(),
            force=dict(
                default='yes',
                type='bool'
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
