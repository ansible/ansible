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
module: bigip_file_copy
short_description: Manage files in datastores on a BIG-IP
description:
  - Manages files on a variety of datastores on a BIG-IP.
version_added: 2.8
options:
  name:
    description:
      - The name of the file as it should reside on the BIG-IP.
      - If this is not specified, then the filename provided in the C(source)
        parameter is used instead.
    type: str
  source:
    description:
      - Specifies the path of the file to upload.
      - This parameter is required if C(state) is C(present).
    type: path
    aliases:
      - src
  datastore:
    description:
      - Specifies the datastore to put the file in.
      - There are several different datastores and each of them allows files
        to be exposed in different ways.
      - When C(external-monitor), the specified file will be stored as
        an external monitor file and be available for use in external monitors
      - When C(ifile), the specified file will be stored as an iFile.
      - When C(lw4o6-table), the specified file will be store as an Lightweight 4
        over 6 (lw4o6) tunnel binding table, which include an IPv6 address for the
        lwB4, public IPv4 address, and restricted port set.
    type: str
    choices:
      - external-monitor
      - ifile
      - lw4o6-table
    default: ifile
  force:
    description:
      - Force overwrite a file.
      - By default, files will only be overwritten if the SHA of the file is different
        for the given filename. This parameter can be used to force overwrite the file
        even if it already exists and its SHA matches.
      - The C(lw4o6-table) datastore does not keep checksums of its file. Therefore, you
        would need to provide this argument to update any of these files.
    type: bool
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
  state:
    description:
      - When C(present), ensures that the resource exists.
      - When C(absent), ensures the resource is removed.
    type: str
    choices:
      - present
      - absent
    default: present
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Upload a file as an iFile
  bigip_file_copy:
    name: foo
    source: /path/to/file.txt
    datastore: ifile
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

# Upload a directory of files
- name: Recursively upload web related files in /var/tmp/project
  find:
    paths: /var/tmp/project
    patterns: "^.*?\\.(?:html|?:css|?:js)$"
  register: f

- name: Upload a directory of files as a set of iFiles
  bigip_file_copy:
    source: "{{ f.path }}"
    datastore: ifile
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
    loop: f
  delegate_to: localhost
# End upload a directory of files

- name: Upload a file to use in an external monitor
  bigip_file_copy:
    source: /path/to/files/external.sh
    datastore: external-monitor
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
# only common fields returned
'''

import hashlib
import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.icontrol import upload_file
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.icontrol import upload_file


class Parameters(AnsibleF5Parameters):
    api_map = {

    }

    api_attributes = [

    ]

    returnables = [

    ]

    updatables = [
        'checksum',
    ]


class ApiParameters(Parameters):
    @property
    def checksum(self):
        """Returns a plain checksum value without the leading extra characters

        Values are stored in the REST as the following.

            ``"checksum": "SHA1:77002:b84015799949ac4acad87b81691455242a31e894"``

        Returns:
            string: The parsed SHA1 checksum.
        """
        if self._values['checksum'] is None:
            return None
        return str(self._values['checksum'].split(':')[2])


class ModuleParameters(Parameters):
    @property
    def checksum(self):
        """Return SHA1 checksum of the file on disk

        Returns:
            string: The SHA1 checksum of the file.

        References:
            - https://stackoverflow.com/a/22058673/661215
        """
        if self._values['datastore'] == 'lw4o6-table':
            return None

        sha1 = hashlib.sha1()
        with open(self._values['source'], 'rb') as f:
            while True:
                data = f.read(4096)
                if not data:
                    break
                sha1.update(data)
        return sha1.hexdigest()

    @property
    def name(self):
        if self._values['name'] is not None:
            return self._values['name']
        if self._values['source'] is None:
            return None
        return os.path.basename(self._values['source'])


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


class BaseManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = UsableChanges(params=changed)

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = Parameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                if isinstance(change, dict):
                    changed.update(change)
                else:
                    changed[k] = change
        if changed:
            self.changes = UsableChanges(params=changed)
            return True
        return False

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def exec_module(self):
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

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update() and not self.want.force:
            return False
        if self.module.check_mode:
            return True
        self.remove_from_device()
        self.upload_to_device()
        self.create_on_device()
        self.remove_uploaded_file_from_device(self.want.name)
        return True

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        return True

    def create(self):
        if self.module.check_mode:
            return True
        self.upload_to_device()
        self.create_on_device()
        self.remove_uploaded_file_from_device(self.want.name)
        return True

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def upload_to_device(self):
        url = 'https://{0}:{1}/mgmt/shared/file-transfer/uploads'.format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        try:
            upload_file(self.client, url, self.want.source, self.want.name)
        except F5ModuleError:
            raise F5ModuleError(
                "Failed to upload the file."
            )

    def remove_uploaded_file_from_device(self, name):
        filepath = '/var/config/rest/downloads/{0}'.format(name)
        params = {
            "command": "run",
            "utilCmdArgs": filepath
        }
        uri = "https://{0}:{1}/mgmt/tm/util/unix-rm".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
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


class IFileManager(BaseManager):
    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['source-path'] = 'file:/var/config/rest/downloads/{0}'.format(self.want.name)
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/sys/file/ifile/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
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

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/file/ifile/{2}".format(
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

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/file/ifile/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
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
        return ApiParameters(params=response)

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/file/ifile/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)


class ExternalMonitorManager(BaseManager):
    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['source-path'] = 'file:/var/config/rest/downloads/{0}'.format(self.want.name)
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/sys/file/external-monitor/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
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

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/file/external-monitor/{2}".format(
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

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/file/external-monitor/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
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
        return ApiParameters(params=response)

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/file/external-monitor/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)


class Lw4o6Manager(BaseManager):
    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['source-path'] = 'file:/var/config/rest/downloads/{0}'.format(self.want.name)
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/sys/file/lwtunneltbl/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
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

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/file/lwtunneltbl/{2}".format(
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

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/file/lwtunneltbl/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
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
        return ApiParameters(params=response)

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/file/lwtunneltbl/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.kwargs = kwargs

    def exec_module(self):
        if self.module.params['datastore'] == 'ifile':
            manager = self.get_manager('v1')
        elif self.module.params['datastore'] == 'external-monitor':
            manager = self.get_manager('v2')
        elif self.module.params['datastore'] == 'lw4o6-table':
            manager = self.get_manager('v3')
        else:
            raise F5ModuleError(
                "Unknown datastore specified."
            )
        return manager.exec_module()

    def get_manager(self, type):
        if type == 'v1':
            return IFileManager(**self.kwargs)
        elif type == 'v2':
            return ExternalMonitorManager(**self.kwargs)
        elif type == 'v3':
            return Lw4o6Manager(**self.kwargs)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(),
            source=dict(
                type='path',
                aliases=['src'],
            ),
            datastore=dict(
                choices=[
                    'external-monitor',
                    'ifile',
                    'lw4o6-table',
                ],
                default='ifile'
            ),
            force=dict(type='bool', default='no'),
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
        self.required_if = [
            ['state', 'present', ['source']]
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        required_if=spec.required_if,
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
