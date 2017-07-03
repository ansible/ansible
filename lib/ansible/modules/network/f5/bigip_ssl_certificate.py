#!/usr/bin/python
#
# Copyright 2017 F5 Networks Inc.
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

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.0'
}

DOCUMENTATION = '''
module: bigip_ssl_certificate
short_description: Import/Delete certificates from BIG-IP.
description:
  - This module will import/delete SSL certificates on BIG-IP LTM.
    Certificates can be imported from certificate and key files on the local
    disk, in PEM format.
version_added: 2.2
options:
  cert_content:
    description:
      - When used instead of 'cert_src', sets the contents of a certificate directly
        to the specified value. This is used with lookup plugins or for anything
        with formatting or templating. Either one of C(key_src),
        C(key_content), C(cert_src) or C(cert_content) must be provided when
        C(state) is C(present).
  key_content:
    description:
      - When used instead of 'key_src', sets the contents of a certificate key
        directly to the specified value. This is used with lookup plugins or for
        anything with formatting or templating. Either one of C(key_src),
        C(key_content), C(cert_src) or C(cert_content) must be provided when
        C(state) is C(present).
  state:
    description:
      - Certificate and key state. This determines if the provided certificate
        and key is to be made C(present) on the device or C(absent).
    default: present
    choices:
      - present
      - absent
  name:
    description:
      - SSL Certificate Name.  This is the cert/key pair name used
        when importing a certificate/key into the F5. It also
        determines the filenames of the objects on the LTM
        (:Partition:name.cer_11111_1 and :Partition_name.key_11111_1).
    required: True
  cert_src:
    description:
      - This is the local filename of the certificate. Either one of C(key_src),
        C(key_content), C(cert_src) or C(cert_content) must be provided when
        C(state) is C(present).
  key_src:
    description:
      - This is the local filename of the private key. Either one of C(key_src),
        C(key_content), C(cert_src) or C(cert_content) must be provided when
        C(state) is C(present).
  passphrase:
    description:
      - Passphrase on certificate private key
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install f5-sdk.
  - This module does not behave like other modules that you might include in
    roles where referencing files or templates first looks in the role's
    files or templates directory. To have it behave that way, use the Ansible
    file or template lookup (see Examples). The lookups behave as expected in
    a role context.
extends_documentation_fragment: f5
requirements:
    - f5-sdk >= 1.5.0
    - BIG-IP >= v12
author:
    - Tim Rupp (@caphrim007)
'''

EXAMPLES = '''
- name: Import PEM Certificate from local disk
  bigip_ssl_certificate:
      name: "certificate-name"
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
      state: "present"
      cert_src: "/path/to/cert.crt"
      key_src: "/path/to/key.key"
  delegate_to: localhost

- name: Use a file lookup to import PEM Certificate
  bigip_ssl_certificate:
      name: "certificate-name"
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
      state: "present"
      cert_content: "{{ lookup('file', '/path/to/cert.crt') }}"
      key_content: "{{ lookup('file', '/path/to/key.key') }}"
  delegate_to: localhost

- name: "Delete Certificate"
  bigip_ssl_certificate:
      name: "certificate-name"
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
      state: "absent"
  delegate_to: localhost
'''

RETURN = '''
cert_name:
    description: The name of the certificate that the user provided
    returned: created
    type: string
    sample: "cert1"
key_filename:
    description:
        - The name of the SSL certificate key. The C(key_filename) and
          C(cert_filename) will be similar to each other, however the
          C(key_filename) will have a C(.key) extension.
    returned: created
    type: string
    sample: "cert1.key"
key_checksum:
    description: SHA1 checksum of the key that was provided.
    returned: changed and created
    type: string
    sample: "cf23df2207d99a74fbe169e3eba035e633b65d94"
key_source_path:
    description: Path on BIG-IP where the source of the key is stored
    returned: created
    type: string
    sample: "/var/config/rest/downloads/cert1.key"
cert_filename:
    description:
        - The name of the SSL certificate. The C(cert_filename) and
          C(key_filename) will be similar to each other, however the
          C(cert_filename) will have a C(.crt) extension.
    returned: created
    type: string
    sample: "cert1.crt"
cert_checksum:
    description: SHA1 checksum of the cert that was provided.
    returned: changed and created
    type: string
    sample: "f7ff9e8b7bb2e09b70935a5d785e0cc5d9d0abf0"
cert_source_path:
    description: Path on BIG-IP where the source of the certificate is stored.
    returned: created
    type: string
    sample: "/var/config/rest/downloads/cert1.crt"
'''


import hashlib
import os
import re

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from ansible.module_utils.f5_utils import (
    AnsibleF5Client,
    AnsibleF5Parameters,
    HAS_F5SDK,
    F5ModuleError,
    iControlUnexpectedHTTPError,
    iteritems
)


class Parameters(AnsibleF5Parameters):
    def __init__(self, params=None):
        super(Parameters, self).__init__(params)
        self._values['__warnings'] = []

    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result

    def api_params(self):
        result = {}
        for api_attribute in self.api_attributes:
            if self.api_map is not None and api_attribute in self.api_map:
                result[api_attribute] = getattr(self, self.api_map[api_attribute])
            else:
                result[api_attribute] = getattr(self, api_attribute)
        result = self._filter_params(result)
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
    def checksum(self):
        if self._values['checksum'] is None:
            return None
        pattern = r'SHA1:\d+:(?P<value>[\w+]{40})'
        matches = re.match(pattern, self._values['checksum'])
        if matches:
            return matches.group('value')
        else:
            return None


class KeyParameters(Parameters):
    api_map = {
        'sourcePath': 'key_source_path'
    }

    updatables = ['key_source_path']

    returnables = ['key_filename', 'key_checksum', 'key_source_path']

    api_attributes = ['passphrase', 'sourcePath']

    @property
    def key_filename(self):
        fname, fext = os.path.splitext(self.name)
        if fext == '':
            return fname + '.key'
        else:
            return self.name

    @property
    def key_checksum(self):
        if self.key_content is None:
            return None
        return self._get_hash(self.key_content)

    @property
    def key_src(self):
        if self._values['key_src'] is None:
            return None

        self._values['__warnings'].append(
            dict(
                msg="The key_src param is deprecated",
                version='2.4'
            )
        )

        try:
            with open(self._values['key_src']) as fh:
                self.key_content = fh.read()
        except IOError:
            raise F5ModuleError(
                "The specified 'key_src' does not exist"
            )

    @property
    def key_source_path(self):
        result = 'file://' + os.path.join(
            BaseManager.download_path,
            self.key_filename
        )
        return result


class CertParameters(Parameters):
    api_map = {
        'sourcePath': 'cert_source_path'
    }

    updatables = ['cert_source_path']

    returnables = ['cert_filename', 'cert_checksum', 'cert_source_path']

    api_attributes = ['sourcePath']

    @property
    def cert_checksum(self):
        if self.cert_content is None:
            return None
        return self._get_hash(self.cert_content)

    @property
    def cert_filename(self):
        fname, fext = os.path.splitext(self.name)
        if fext == '':
            return fname + '.crt'
        else:
            return self.name

    @property
    def cert_src(self):
        if self._values['cert_src'] is None:
            return None

        self._values['__warnings'].append(
            dict(
                msg="The cert_src param is deprecated",
                version='2.4'
            )
        )

        try:
            with open(self._value['cert_src']) as fh:
                self.cert_content = fh.read()
        except IOError:
            raise F5ModuleError(
                "The specified 'cert_src' does not exist"
            )

    @property
    def cert_source_path(self):
        result = 'file://' + os.path.join(
            BaseManager.download_path,
            self.cert_filename
        )
        return result


class ModuleManager(object):
    def __init__(self, client):
        self.client = client

    def exec_module(self):
        manager1 = self.get_manager('certificate')
        manager2 = self.get_manager('key')
        result = self.execute_managers([manager1, manager2])
        return result

    def execute_managers(self, managers):
        results = dict(changed=False)
        for manager in managers:
            result = manager.exec_module()
            for k, v in iteritems(result):
                if k == 'changed':
                    if v is True:
                        results['changed'] = True
                else:
                    results[k] = v
        return results

    def get_manager(self, type):
        if type == 'certificate':
            return CertificateManager(self.client)
        elif type == 'key':
            return KeyManager(self.client)


class BaseManager(object):
    download_path = '/var/config/rest/downloads'

    def __init__(self, client):
        self.client = client
        self.have = None

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
        self._announce_deprecations()
        return result

    def _announce_deprecations(self):
        warnings = []
        if self.want:
            warnings += self.want._values.get('__warnings', [])
        if self.have:
            warnings += self.have._values.get('__warnings', [])
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

    def create(self):
        self._set_changed_options()
        if self.client.check_mode:
            return True
        self.create_on_device()
        return True

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.client.check_mode:
            return True
        self.update_on_device()
        return True

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove(self):
        if self.client.check_mode:
            return True
        self.remove_from_device()
        return True


class CertificateManager(BaseManager):
    def __init__(self, client):
        super(CertificateManager, self).__init__(client)
        self.want = CertParameters(self.client.module.params)
        self.changes = CertParameters()

    def _set_changed_options(self):
        changed = {}
        try:
            for key in CertParameters.returnables:
                if getattr(self.want, key) is not None:
                    changed[key] = getattr(self.want, key)
            if changed:
                self.changes = CertParameters(changed)
        except Exception:
            pass

    def _update_changed_options(self):
        changed = {}
        try:
            for key in CertParameters.updatables:
                if getattr(self.want, key) is not None:
                    attr1 = getattr(self.want, key)
                    attr2 = getattr(self.have, key)
                    if attr1 != attr2:
                        changed[key] = attr1
                if self.want.cert_checksum != self.have.checksum:
                    changed['cert_checksum'] = self.want.cert_checksum
            if changed:
                self.changes = CertParameters(changed)
                return True
        except Exception:
            pass
        return False

    def exists(self):
        result = self.client.api.tm.sys.file.ssl_certs.ssl_cert.exists(
            name=self.want.cert_filename,
            partition=self.want.partition
        )
        return result

    def present(self):
        if self.want.cert_content is None:
            return False
        return super(CertificateManager, self).present()

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def update_on_device(self):
        content = StringIO(self.want.cert_content)
        self.client.api.shared.file_transfer.uploads.upload_stringio(
            content, self.want.cert_filename
        )
        resource = self.client.api.tm.sys.file.ssl_certs.ssl_cert.load(
            name=self.want.cert_filename,
            partition=self.want.partition
        )
        resource.update()

    def create_on_device(self):
        content = StringIO(self.want.cert_content)
        self.client.api.shared.file_transfer.uploads.upload_stringio(
            content, self.want.cert_filename
        )
        self.client.api.tm.sys.file.ssl_certs.ssl_cert.create(
            sourcePath=self.want.cert_source_path,
            name=self.want.cert_filename,
            partition=self.want.partition
        )

    def read_current_from_device(self):
        resource = self.client.api.tm.sys.file.ssl_certs.ssl_cert.load(
            name=self.want.cert_filename,
            partition=self.want.partition
        )
        result = resource.attrs
        return CertParameters(result)

    def remove_from_device(self):
        resource = self.client.api.tm.sys.file.ssl_certs.ssl_cert.load(
            name=self.want.cert_filename,
            partition=self.want.partition
        )
        resource.delete()

    def remove(self):
        result = super(CertificateManager, self).remove()
        if self.exists() and not self.client.check_mode:
            raise F5ModuleError("Failed to delete the certificate")
        return result


class KeyManager(BaseManager):
    def __init__(self, client):
        super(KeyManager, self).__init__(client)
        self.want = KeyParameters(self.client.module.params)
        self.changes = KeyParameters()

    def _set_changed_options(self):
        changed = {}
        try:
            for key in KeyParameters.returnables:
                if getattr(self.want, key) is not None:
                    changed[key] = getattr(self.want, key)
            if changed:
                self.changes = Parameters(changed)
        except Exception:
            pass

    def _update_changed_options(self):
        changed = {}
        try:
            for key in CertParameters.updatables:
                if getattr(self.want, key) is not None:
                    attr1 = getattr(self.want, key)
                    attr2 = getattr(self.have, key)
                    if attr1 != attr2:
                        changed[key] = attr1
                if self.want.key_checksum != self.have.checksum:
                    changed['key_checksum'] = self.want.key_checksum
            if changed:
                self.changes = CertParameters(changed)
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
        content = StringIO(self.want.key_content)
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
        if self.want.key_content is None:
            return False
        return super(KeyManager, self).present()

    def read_current_from_device(self):
        resource = self.client.api.tm.sys.file.ssl_keys.ssl_key.load(
            name=self.want.key_filename,
            partition=self.want.partition
        )
        result = resource.attrs
        return KeyParameters(result)

    def create_on_device(self):
        content = StringIO(self.want.key_content)
        self.client.api.shared.file_transfer.uploads.upload_stringio(
            content, self.want.key_filename
        )
        self.client.api.tm.sys.file.ssl_keys.ssl_key.create(
            sourcePath=self.want.key_source_path,
            name=self.want.key_filename,
            partition=self.want.partition
        )

    def remove_from_device(self):
        resource = self.client.api.tm.sys.file.ssl_keys.ssl_key.load(
            name=self.want.key_filename,
            partition=self.want.partition
        )
        resource.delete()

    def remove(self):
        result = super(KeyManager, self).remove()
        if self.exists() and not self.client.check_mode:
            raise F5ModuleError("Failed to delete the key")
        return result


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.argument_spec = dict(
            name=dict(
                required=True
            ),
            cert_content=dict(),
            cert_src=dict(
                type='path',
                removed_in_version='2.4'
            ),
            key_content=dict(),
            key_src=dict(
                type='path',
                removed_in_version='2.4'
            ),
            passphrase=dict(
                no_log=True
            ),
            state=dict(
                required=False,
                default='present',
                choices=['absent', 'present']
            )
        )
        self.mutually_exclusive = [
            ['key_content', 'key_src'],
            ['cert_content', 'cert_src']
        ]
        self.f5_product_name = 'bigip'


def main():
    if not HAS_F5SDK:
        raise F5ModuleError("The python f5-sdk module is required")

    spec = ArgumentSpec()

    client = AnsibleF5Client(
        argument_spec=spec.argument_spec,
        mutually_exclusive=spec.mutually_exclusive,
        supports_check_mode=spec.supports_check_mode,
        f5_product_name=spec.f5_product_name
    )

    try:
        mm = ModuleManager(client)
        results = mm.exec_module()
        client.module.exit_json(**results)
    except F5ModuleError as e:
        client.module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
