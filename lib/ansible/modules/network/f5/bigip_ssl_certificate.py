#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_ssl_certificate
short_description: Import/Delete certificates from BIG-IP
description:
  - This module will import/delete SSL certificates on BIG-IP LTM.
    Certificates can be imported from certificate and key files on the local
    disk, in PEM format.
version_added: 2.2
options:
  content:
    description:
      - Sets the contents of a certificate directly to the specified value.
        This is used with lookup plugins or for anything with formatting or
      - C(content) must be provided when C(state) is C(present).
    type: str
    aliases: ['cert_content']
  state:
    description:
      - Certificate state. This determines if the provided certificate
        and key is to be made C(present) on the device or C(absent).
    type: str
    choices:
      - present
      - absent
    default: present
  name:
    description:
      - SSL Certificate Name. This is the cert name used when importing a certificate
        into the F5. It also determines the filenames of the objects on the LTM.
    type: str
    required: True
  issuer_cert:
    description:
      - Issuer certificate used for OCSP monitoring.
      - This parameter is only valid on versions of BIG-IP 13.0.0 or above.
    type: str
    version_added: 2.5
  partition:
    description:
      - Device partition to manage resources on.
    type: str
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
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Use a file lookup to import PEM Certificate
  bigip_ssl_certificate:
    name: certificate-name
    state: present
    content: "{{ lookup('file', '/path/to/cert.crt') }}"
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Use a file lookup to import CA certificate chain
  bigip_ssl_certificate:
    name: ca-chain-name
    state: present
    content: "{{ lookup('file', '/path/to/ca-chain.crt') }}"
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Delete Certificate
  bigip_ssl_certificate:
    name: certificate-name
    state: absent
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost
'''

RETURN = r'''
cert_name:
  description: The name of the certificate that the user provided
  returned: created
  type: str
  sample: cert1
filename:
  description:
    - The name of the SSL certificate.
  returned: created
  type: str
  sample: cert1.crt
checksum:
  description: SHA1 checksum of the cert that was provided.
  returned: changed and created
  type: str
  sample: f7ff9e8b7bb2e09b70935a5d785e0cc5d9d0abf0
source_path:
  description: Path on BIG-IP where the source of the certificate is stored.
  returned: created
  type: str
  sample: /var/config/rest/downloads/cert1.crt
'''

import hashlib
import os
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.icontrol import upload_file
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.icontrol import upload_file

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class Parameters(AnsibleF5Parameters):
    download_path = '/var/config/rest/downloads'

    api_map = {
        'sourcePath': 'source_path',
        'issuerCert': 'issuer_cert',
    }

    updatables = [
        'content',
        'issuer_cert',
        'source_path',
    ]

    returnables = [
        'filename',
        'checksum',
        'source_path',
        'issuer_cert',
    ]

    api_attributes = [
        'issuerCert',
        'sourcePath',
    ]


class ApiParameters(Parameters):
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

    @property
    def filename(self):
        return self._values['name']


class ModuleParameters(Parameters):
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
    def issuer_cert(self):
        if self._values['issuer_cert'] is None:
            return None
        name = fq_name(self.partition, self._values['issuer_cert'])
        if name.endswith('.crt'):
            return name
        else:
            return name + '.crt'

    @property
    def checksum(self):
        if self.content is None:
            return None
        return self._get_hash(self.content)

    @property
    def filename(self):
        if self.name.endswith('.crt'):
            return self.name
        else:
            return self.name + '.crt'

    @property
    def source_path(self):
        result = 'file://' + os.path.join(
            self.download_path,
            self.filename
        )
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


class ReportableChanges(Changes):
    pass


class UsableChanges(Changes):
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
            result = self.__default(param)
            return result

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1

    @property
    def source_path(self):
        if self.want.source_path is None:
            return None
        if self.want.source_path == self.have.source_path:
            if self.content:
                return self.want.source_path
        if self.want.source_path != self.have.source_path:
            return self.want.source_path

    @property
    def content(self):
        if self.want.checksum != self.have.checksum:
            result = dict(
                checksum=self.want.checksum,
                content=self.want.content
            )
            return result


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

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
            self.module.deprecate(
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
        if self.module.check_mode:
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
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        return True

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

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/file/ssl-cert/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.filename)
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

    def update_on_device(self):
        content = StringIO(self.want.content)
        self.upload_file_to_device(content, self.want.filename)
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/sys/file/ssl-cert/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.filename)
        )
        resp = self.client.api.put(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def create_on_device(self):
        content = StringIO(self.want.content)
        self.upload_file_to_device(content, self.want.filename)
        uri = "https://{0}:{1}/mgmt/tm/sys/file/ssl-cert/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        params = dict(
            sourcePath=self.want.source_path,
            name=self.want.filename,
            partition=self.want.partition
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

        # This needs to be done because of the way that BIG-IP creates certificates.
        #
        # The extra params (such as OCSP and issuer stuff) are not available in the
        # payload. In a nutshell, the available resource attributes *change* after
        # a create so that *more* are available.
        params = self.want.api_params()
        if params:
            uri = "https://{0}:{1}/mgmt/tm/sys/file/ssl-cert/{2}".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                transform_name(self.want.partition, self.want.filename)
            )
            resp = self.client.api.put(uri, json=params)
            try:
                response = resp.json()
            except ValueError as ex:
                raise F5ModuleError(str(ex))

            if 'code' in response and response['code'] == 400:
                if 'message' in response:
                    raise F5ModuleError(response['message'])
                else:
                    raise F5ModuleError(resp.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/file/ssl-cert/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.filename)
        )

        query = '?expandSubcollections=true'
        resp = self.client.api.get(uri + query)

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
        uri = "https://{0}:{1}/mgmt/tm/sys/file/ssl-cert/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.filename)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(
                required=True
            ),
            content=dict(aliases=['cert_content']),
            state=dict(
                default='present',
                choices=['absent', 'present']
            ),
            issuer_cert=dict(),
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

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
