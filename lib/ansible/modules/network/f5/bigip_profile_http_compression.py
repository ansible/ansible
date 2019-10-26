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
module: bigip_profile_http_compression
short_description: Manage HTTP compression profiles on a BIG-IP
description:
  - Manage HTTP compression profiles on a BIG-IP.
version_added: 2.7
options:
  name:
    description:
      - Specifies the name of the compression profile.
    type: str
    required: True
  parent:
    description:
      - Specifies the profile from which this profile inherits settings.
      - When creating a new profile, if this parameter is not specified, the default
        is the system-supplied C(httpcompression) profile.
    type: str
  description:
    description:
      - Description of the HTTP compression profile.
    type: str
  buffer_size:
    description:
      - Maximum number of compressed bytes that the system buffers before inserting
        a Content-Length header (which specifies the compressed size) into the response.
      - When creating a new profile, if this parameter is not specified, the default
        is provided by the parent profile.
    type: int
  gzip_level:
    description:
      - Specifies the degree to which the system compresses the content.
      - Higher compression levels cause the compression process to be slower.
      - Valid values are between 1 (least compression and fastest) to 9 (most
        compression and slowest).
    type: int
    choices:
      - 1
      - 2
      - 3
      - 4
      - 5
      - 6
      - 7
      - 8
      - 9
  gzip_memory_level:
    description:
      - Number of kilobytes of memory that the system uses for internal compression
        buffers when compressing a server response.
    type: int
    choices:
      - 1
      - 2
      - 4
      - 8
      - 16
      - 32
      - 64
      - 128
      - 256
  gzip_window_size:
    description:
      - Number of kilobytes in the window size that the system uses when compressing
        a server response.
    type: int
    choices:
      - 1
      - 2
      - 4
      - 8
      - 16
      - 32
      - 64
      - 128
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
  state:
    description:
      - When C(present), ensures that the profile exists.
      - When C(absent), ensures the profile is removed.
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
- name: Create an HTTP compression profile
  bigip_profile_http_compression:
    name: profile1
    description: Custom HTTP Compression Profile
    buffer_size: 131072
    gzip_level: 6
    gzip_memory_level: 16k
    gzip_window_size: 64k
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
description:
  description: The new description of the resource.
  returned: changed
  type: str
  sample: My custom profile
buffer_size:
  description: The new buffer size of the profile.
  returned: changed
  type: int
  sample: 4096
gzip_memory_level:
  description: The new GZIP memory level, in KB, of the profile.
  returned: changed
  type: int
  sample: 16
gzip_level:
  description: The new GZIP level of the profile. Smaller is less compression.
  returned: changed
  type: int
  sample: 2
gzip_window_size:
  description: The new GZIP window size, in KB, of the profile.
  returned: changed
  type: int
  sample: 64
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name


class Parameters(AnsibleF5Parameters):
    api_map = {
        'bufferSize': 'buffer_size',
        'defaultsFrom': 'parent',
        'gzipMemoryLevel': 'gzip_memory_level',
        'gzipLevel': 'gzip_level',
        'gzipWindowSize': 'gzip_window_size',
    }

    api_attributes = [
        'description',
        'bufferSize',
        'defaultsFrom',
        'gzipMemoryLevel',
        'gzipLevel',
        'gzipWindowSize',
    ]

    returnables = [
        'description',
        'buffer_size',
        'gzip_memory_level',
        'gzip_level',
        'gzip_window_size',
    ]

    updatables = [
        'description',
        'buffer_size',
        'gzip_memory_level',
        'gzip_level',
        'gzip_window_size',
    ]


class ApiParameters(Parameters):
    @property
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']

    @property
    def gzip_memory_level(self):
        if self._values['gzip_memory_level'] is None:
            return None
        return self._values['gzip_memory_level'] / 1024

    @property
    def gzip_window_size(self):
        if self._values['gzip_window_size'] is None:
            return None
        return self._values['gzip_window_size'] / 1024


class ModuleParameters(Parameters):
    @property
    def parent(self):
        if self._values['parent'] is None:
            return None
        result = fq_name(self.partition, self._values['parent'])
        return result


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
    @property
    def gzip_memory_level(self):
        if self._values['gzip_memory_level'] is None:
            return None
        return self._values['gzip_memory_level'] * 1024

    @property
    def gzip_window_size(self):
        if self._values['gzip_window_size'] is None:
            return None
        return self._values['gzip_window_size'] * 1024


class ReportableChanges(Changes):
    @property
    def gzip_memory_level(self):
        if self._values['gzip_memory_level'] is None:
            return None
        return self._values['gzip_memory_level'] / 1024

    @property
    def gzip_window_size(self):
        if self._values['gzip_window_size'] is None:
            return None
        return self._values['gzip_window_size'] / 1024


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

    @property
    def parent(self):
        if self.want.parent != self.have.parent:
            raise F5ModuleError(
                "The parent profile cannot be changed"
            )


class ModuleManager(object):
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

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/http-compression/{2}".format(
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

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

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

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/http-compression/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403, 404]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/http-compression/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 404]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/http-compression/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.delete(uri)
        if resp.status == 200:
            return True
        raise F5ModuleError(resp.content)

    def read_current_from_device(self):  # lgtm [py/similar-function]
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/http-compression/{2}".format(
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


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(required=True),
            parent=dict(),
            buffer_size=dict(type='int'),
            description=dict(),
            gzip_level=dict(
                type='int',
                choices=[1, 2, 3, 4, 5, 6, 7, 8, 9]
            ),
            gzip_memory_level=dict(
                type='int',
                choices=[1, 2, 4, 8, 16, 32, 64, 128, 256]
            ),
            gzip_window_size=dict(
                type='int',
                choices=[1, 2, 4, 8, 16, 32, 64, 128]
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
