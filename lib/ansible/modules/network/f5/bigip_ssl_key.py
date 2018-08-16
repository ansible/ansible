#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
module: bigip_ssl_key
short_description: Import/Delete SSL keys from BIG-IP
description:
  - This module will import/delete SSL keys on a BIG-IP. Keys can be imported
    from key files on the local disk, in PEM format.
version_added: 2.5
options:
  content:
    description:
      - Sets the contents of a key directly to the specified value. This is
        used with lookup plugins or for anything with formatting or templating.
        This must be provided when C(state) is C(present).
    aliases:
      - key_content
  state:
    description:
      - When C(present), ensures that the key is uploaded to the device. When
        C(absent), ensures that the key is removed from the device. If the key
        is currently in use, the module will not be able to remove the key.
    default: present
    choices:
      - present
      - absent
  name:
    description:
      - The name of the key.
    required: True
  passphrase:
    description:
      - Passphrase on key.
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
    version_added: 2.5
notes:
  - This module does not behave like other modules that you might include in
    roles where referencing files or templates first looks in the role's
    files or templates directory. To have it behave that way, use the Ansible
    file or template lookup (see Examples). The lookups behave as expected in
    a role context.
extends_documentation_fragment: f5
requirements:
  - BIG-IP >= v12
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Use a file lookup to import key
  bigip_ssl_key:
    name: key-name
    server: lb.mydomain.com
    user: admin
    password: secret
    state: present
    content: "{{ lookup('file', '/path/to/key.key') }}"
  delegate_to: localhost

- name: Delete key
  bigip_ssl_key:
    name: key-name
    server: lb.mydomain.com
    user: admin
    password: secret
    state: absent
  delegate_to: localhost
'''

RETURN = r'''
key_filename:
  description:
    - The name of the SSL certificate key. The C(key_filename) and
      C(cert_filename) will be similar to each other, however the
      C(key_filename) will have a C(.key) extension.
  returned: created
  type: string
  sample: cert1.key
key_checksum:
  description: SHA1 checksum of the key that was provided.
  returned: changed and created
  type: string
  sample: cf23df2207d99a74fbe169e3eba035e633b65d94
key_source_path:
  description: Path on BIG-IP where the source of the key is stored
  returned: created
  type: string
  sample: /var/config/rest/downloads/cert1.key
'''

import hashlib
import os
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import f5_argument_spec
    try:
        from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False
except ImportError:
    from ansible.module_utils.network.f5.bigip import HAS_F5SDK
    from ansible.module_utils.network.f5.bigip import F5Client
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import cleanup_tokens
    from ansible.module_utils.network.f5.common import f5_argument_spec
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class Parameters(AnsibleF5Parameters):
    download_path = '/var/config/rest/downloads'

    api_map = {
        'sourcePath': 'key_source_path'
    }

    updatables = ['key_source_path']

    returnables = ['key_filename', 'key_checksum', 'key_source_path']

    api_attributes = ['passphrase', 'sourcePath']

    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result

    def _get_hash(self, content):
        k = hashlib.sha1()
        s = StringIO(content)
        while True:
            data = s.read(1024)
            if not data:
                break
            k.update(data.encode('utf-8'))
        return k.hexdigest()

    @property
    def key_filename(self):
        if self.name.endswith('.key'):
            return self.name
        else:
            return self.name + '.key'

    @property
    def key_checksum(self):
        if self.content is None:
            return None
        return self._get_hash(self.content)

    @property
    def key_source_path(self):
        result = 'file://' + os.path.join(
            self.download_path,
            self.key_filename
        )
        return result

    @property
    def checksum(self):
        if self._values['checksum'] is None:
            return None
        pattern = r'SHA1:\d+:(?P<value>[\w+]{40})'
        matches = re.match(pattern, self._values['checksum'])
        if matches:
            return matches.group('value')
        else:
            return None


class Changes(Parameters):
    pass


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.have = None
        self.want = Parameters(params=self.module.params)
        self.changes = Changes()

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        try:
            if state == "present":
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        changes = self.changes.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        return result

    def _set_changed_options(self):
        changed = {}
        try:
            for key in Parameters.returnables:
                if getattr(self.want, key) is not None:
                    changed[key] = getattr(self.want, key)
            if changed:
                self.changes = Changes(params=changed)
        except Exception:
            pass

    def _update_changed_options(self):
        changed = {}
        try:
            for key in Parameters.updatables:
                if getattr(self.want, key) is not None:
                    attr1 = getattr(self.want, key)
                    attr2 = getattr(self.have, key)
                    if attr1 != attr2:
                        changed[key] = attr1
                if self.want.key_checksum != self.have.checksum:
                    changed['key_checksum'] = self.want.key_checksum
            if changed:
                self.changes = Changes(params=changed)
                return True
        except Exception:
            pass
        return False

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def update_on_device(self):
        content = StringIO(self.want.content)
        self.client.api.shared.file_transfer.uploads.upload_stringio(
            content, self.want.key_filename
        )
        resource = self.client.api.tm.sys.file.ssl_keys.ssl_key.load(
            name=self.want.key_filename,
            partition=self.want.partition
        )
        resource.update()

    def exists(self):
        result = self.client.api.tm.sys.file.ssl_keys.ssl_key.exists(
            name=self.want.key_filename,
            partition=self.want.partition
        )
        return result

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def create(self):
        if self.want.content is None:
            return False
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def read_current_from_device(self):
        resource = self.client.api.tm.sys.file.ssl_keys.ssl_key.load(
            name=self.want.key_filename,
            partition=self.want.partition
        )
        result = resource.attrs
        return Parameters(params=result)

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def create_on_device(self):
        content = StringIO(self.want.content)
        self.client.api.shared.file_transfer.uploads.upload_stringio(
            content, self.want.key_filename
        )
        self.client.api.tm.sys.file.ssl_keys.ssl_key.create(
            sourcePath=self.want.key_source_path,
            name=self.want.key_filename,
            partition=self.want.partition
        )

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        resource = self.client.api.tm.sys.file.ssl_keys.ssl_key.load(
            name=self.want.key_filename,
            partition=self.want.partition
        )
        resource.delete()

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the key")
        return True


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(
                required=True
            ),
            content=dict(
                aliases=['key_content']
            ),
            passphrase=dict(
                no_log=True
            ),
            state=dict(
                required=False,
                default='present',
                choices=['absent', 'present']
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
        supports_check_mode=spec.supports_check_mode
    )
    if not HAS_F5SDK:
        module.fail_json(msg="The python f5-sdk module is required")

    try:
        client = F5Client(**module.params)
        mm = ModuleManager(module=module, client=client)
        results = mm.exec_module()
        cleanup_tokens(client)
        module.exit_json(**results)
    except F5ModuleError as ex:
        cleanup_tokens(client)
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
