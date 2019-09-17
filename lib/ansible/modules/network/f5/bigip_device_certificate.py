#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_device_certificate
short_description: Manage self-signed device certificates
description:
  - Module used to create and/or renew self-signed device certificates for BIG-IP.
version_added: 2.9
options:
  days_valid:
    description:
      - Specifies the interval for which the self-signed certificate is valid.
      - "The maximum value is 25 years: C(9125) days"
    type: int
    required: True
  cert_name:
    description:
      - Specifies the full name of the certificate file.
      - If the name is not default C(server.crt), the module will configure C(httpd) to use them
        prior to restarting the C(httpd) daemon.
    type: str
    default: server.crt
  key_name:
    description:
      - Specifies the full name of the key file.
      - If the name is not default C(server.key), the module will configure C(httpd) to use them
        prior to restarting the C(httpd) daemon.
    type: str
    default: server.key
  key_size:
    description:
      - Specifies the desired key size in bits.
      - Mandatory option when generating a new certificate.
    type: int
    choices:
      - 512
      - 1024
      - 2048
      - 4096
    default: 2048
  issuer:
    description:
      - Certificate properties, required when generating new certificates.
    suboptions:
      country:
        description:
         - Specifies the Country name attribute for the certificate.
        type: str
      state:
        description:
          - Specifies the State or Province attribute for the certificate.
        type: str
      locality:
        description:
          - Specifies the city or town name for the certificate.
        type: str
      organization:
        description:
          - Specifies the Organization attribute for the certificate.
        type: str
      division:
        description:
          - Specifies the department name attribute for the certificate.
        type: str
      common_name:
        description:
          - Specifies Common Name attribute for the certificate.
        type: str
      email:
        description:
          - "Specifies the domain administrator's email address."
        type: str
    type: dict
  add_to_trusted:
    description:
      - Specified if the certificate should be added to the trusted client and server certificate files.
    type: bool
    default: no
  new_cert:
    description:
      - Specified if the module should generate new certificate.
      - When C(yes) the device certificate and key will be replaced
    type: bool
    default: no
  force:
    description:
      - When C(yes), will update or overwrite the existing certificate when it is not expired device.
      - When C(no), the certificate will only be updated/overwritten if expired.
      - Generally should be C(yes) only in cases where you need to update certificate that is about to expire.
      - This option is also needed when generating new certificate to replace non expired one.
    type: bool
    default: no
  transport:
    description:
      - Configures the transport connection to use when connecting to the
        remote device.
      - This module currently supports only connectivity to the device over cli (ssh).
    required: True
    choices:
        - cli
    default: cli
extends_documentation_fragment: f5
author:
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Update expired certificate
  bigip_device_certificate:
    days_valid: 365
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
      transport: cli
      server_port: 22
  delegate_to: localhost

- name: Update expired certificate non-default names
  bigip_device_certificate:
    days_valid: 60
    cert_name: custom.crt
    key_name: custom.key
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
      transport: cli
      server_port: 22
  delegate_to: localhost

- name: Force update not expired certificate
  bigip_device_certificate:
    days_valid: 365
    force: yes
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
      transport: cli
      server_port: 22
  delegate_to: localhost

- name: Create a new certificate to replace expired certificate
  bigip_device_certificate:
    days_valid: 365
    new_cert: yes
    issuer:
      country: US
      state: WA
      common_name: foobar.foo.local
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
      transport: cli
      server_port: 22
  delegate_to: localhost

- name: Force create a new custom named certificate to replace not expired certificate
  bigip_device_certificate:
    days_valid: 365
    cert_name: custom.crt
    key_name: custom.key
    new_cert: yes
    force: yes
    issuer:
      country: US
      state: WA
      common_name: foobar.foo.local
    key_size: 2048
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
      transport: cli
      server_port: 22
  delegate_to: localhost
'''

RETURN = r'''
days_valid:
  description: The interval for which the self-signed certificate is valid.
  returned: changed
  type: int
  sample: 365
issuer:
  description: Specifies certificate properties.
  type: complex
  returned: changed
  contains:
    country:
      description: The Country name attribute of the certificate.
      returned: changed
      type: str
      sample: US
    state:
      description: The State or Province attribute of the certificate.
      returned: changed
      type: str
      sample: WA
    locality:
      description: The city or town name attribute of the certificate.
      returned: changed
      type: str
      sample: Seattle
    organization:
      description: The Organization attribute of the certificate.
      returned: changed
      type: str
      sample: F5
    division:
      description: The department name attribute of the certificate.
      returned: changed
      type: str
      sample: IT
    common_name:
      description: The Common Name attribute of the certificate.
      returned: changed
      type: str
      sample: foo.bar.local
    email:
      description: "The domain administrator's email address."
      returned: changed
      type: str
      sample: admin@foo.bar.local
cert_name:
  description: The full name of the certificate file.
  returned: changed
  type: str
  sample: common.crt
key_name:
  description: The full name of the key file.
  returned: changed
  type: str
  sample: common.key
key_size:
  description: The desired key size in bits.
  returned: changed
  type: int
  sample: 2048
'''
import os
import ssl
from datetime import datetime

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import exec_command


try:
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import is_cli
except ImportError:
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import is_cli


class Parameters(AnsibleF5Parameters):
    returnables = [
        'days_valid',
        'issuer',
        'key_size',
        'cert_name',
        'key_name',
    ]

    updatables = [
        'days_valid',
    ]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    issuer_map = {
        'country': 'C',
        'state': 'ST',
        'locality': 'L',
        'organization': 'O',
        'division': 'OU',
        'common_name': 'CN',
        'email': 'emailAddress'
    }

    @property
    def issuer(self):
        if self._values['issuer'] is None:
            return None
        filtered = dict((self.issuer_map[k], v) for k, v in self._values['issuer'].items() if v is not None)
        to_parse = ['{0}={1}'.format(k, v) for k, v in filtered.items()]
        result = '/' + '/'.join(to_parse) + '/'
        return result

    @property
    def days_valid(self):
        if 1 <= self._values['days_valid'] <= 9125:
            return self._values['days_valid']
        raise F5ModuleError(
            "Valid 'days_valid' must be in range 1 - 9125 days."
        )


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
    issuer_map = {
        'C': 'country',
        'ST': 'state',
        'L': 'locality',
        'O': 'organization',
        'OU': 'division',
        'CN': 'common_name',
        'emailAddress': 'email'
    }

    @property
    def issuer(self):
        if self._values['issuer'] is None:
            return None
        to_dict = [tuple(item.split('=')) for item in self._values['issuer'].strip('/').split('/')]
        result = dict((self.issuer_map[k], v) for k, v in to_dict)
        return result


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

    def exec_module(self):
        if not is_cli(self.module):
            raise F5ModuleError('Module can only be run via SSH, set the transport property to CLI')

        result = dict()

        changed = self.present()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        return result

    def present(self):
        if self.expired():
            if self.want.new_cert:
                self.create()
                return True
            self.update()
            return True
        if self.want.force and self.want.new_cert:
            self.create()
            return True
        if self.want.force:
            self.update()
            return True
        return False

    def create(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.generate_new()
        return True

    def update(self):
        self._update_changed_options()
        if self.module.check_mode:
            return True
        self.update_certificate()
        if self.want.cert_name != 'server.crt' or self.want.key_name != 'server.key':
            self.configure_new_cert()
        self.restart_daemon()
        if self.want.add_to_trusted:
            self.copy_files_to_trusted()
        return True

    def expired(self):
        self.have = self.read_current_certificate()
        current_epoch = int(datetime.now().timestamp())
        if current_epoch > self.have.epoch:
            return True
        return False

    def generate_new(self):
        self.generate_cert_key()
        if self.want.cert_name != 'server.crt' or self.want.key_name != 'server.key':
            self.configure_new_cert()
        self.restart_daemon()
        if self.want.add_to_trusted:
            self.copy_files_to_trusted()
        return True

    def generate_cert_key(self):
        cmd = 'openssl req -x509 -nodes -days {3} -newkey rsa:{4} -keyout {0}/ssl.key/{2} ' \
              '-out {0}/ssl.crt/{1} -subj "{5}"'.format('/config/httpd/conf', self.want.cert_name, self.want.key_name,
                                                        self.want.days_valid, self.want.key_size, self.want.issuer)
        rc, out, err = exec_command(self.module, cmd)
        if rc != 0:
            raise F5ModuleError(err)

    def create_csr(self):
        cmd = 'openssl x509 -x509toreq -in {0}/ssl.crt/{1} -out {0}/ssl.csr/{3}.csr -signkey {0}/ssl.key/{2}'.format(
            '/config/httpd/conf', self.want.cert_name, self.want.key_name, os.path.splitext(self.want.cert_name)[0]
        )

        rc, out, err = exec_command(self.module, cmd)
        if rc != 0:
            raise F5ModuleError(err)

    def update_certificate(self):
        self.create_csr()
        cmd = 'openssl x509 -req -in {0}/ssl.csr/{3}.csr -signkey {0}/ssl.key/{2} -days {4} -out {0}/ssl.crt/{1}'.\
            format('/config/httpd/conf', self.want.cert_name, self.want.key_name,
                   os.path.splitext(self.want.cert_name)[0], self.want.days_valid)
        rc, out, err = exec_command(self.module, cmd)
        if rc != 0:
            raise F5ModuleError(err)

    def configure_new_cert(self):
        cmd1 = 'tmsh modify sys httpd ssl-certkeyfile /config/httpd/conf/ssl.key/{1}' \
               'ssl-certfile /config/httpd/conf/ssl.crt/{0}'.format(self.want.cert_name, self.want.key_name)

        cmd2 = 'tmsh save /sys config partitions all'

        rc, out, err = exec_command(self.module, cmd1)
        if rc != 0:
            raise F5ModuleError(err)

        rc, out, err = exec_command(self.module, cmd2)
        if rc != 0:
            raise F5ModuleError(err)

    def restart_daemon(self):
        cmd = 'tmsh restart /sys service httpd'
        rc, out, err = exec_command(self.module, cmd)
        if rc != 0:
            raise F5ModuleError(err)

    def copy_files_to_trusted(self):
        cmd1 = 'cat /config/httpd/conf/ssl.crt/{0} >> /config/big3d/client.crt'.format(self.want.cert_name)
        cmd2 = 'cat /config/httpd/conf/ssl.crt/{0} >> /config/gtm/server.crt'.format(self.want.cert_name)
        rc, out, err = exec_command(self.module, cmd1)
        if rc != 0:
            raise F5ModuleError(err)
        rc, out, err = exec_command(self.module, cmd2)
        if rc != 0:
            raise F5ModuleError(err)

    def read_current_certificate(self):
        result = dict()
        command = 'openssl x509 -in /config/httpd/conf/ssl.crt/{0} -dates -issuer -noout'.format(self.want.cert_name)
        rc, out, err = exec_command(self.module, command)
        if rc == 0:
            result['epoch'] = self._parse_cert_date(out)
        return ApiParameters(params=result)

    def _parse_cert_date(self, to_parse):
        c_time = to_parse.split('\n')[1].split('=')[1]
        result = ssl.cert_time_to_seconds(c_time)
        return result


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            key_size=dict(
                type='int',
                choices=[512, 1024, 2048, 4096],
                default=2048
            ),
            cert_name=dict(
                default='server.crt'
            ),
            key_name=dict(
                default='server.key'
            ),
            days_valid=dict(
                type='int',
                required=True
            ),
            issuer=dict(
                type='dict',
                options=dict(
                    country=dict(),
                    state=dict(),
                    locality=dict(),
                    organization=dict(),
                    division=dict(),
                    common_name=dict(),
                    email=dict(),
                ),
                required_one_of=[
                    ['country', 'state', 'locality', 'organization', 'division', 'common_name', 'email']
                ]
            ),

            add_to_trusted=dict(
                type='bool',
                default='no'
            ),
            new_cert=dict(
                type='bool',
                default='no'
            ),
            force=dict(
                type='bool',
                default='no'
            ),
            transport=dict(
                type='str',
                default='cli',
                choices=['cli']
            ),
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.required_if = [
            ['new_cert', 'yes', ['days_valid', 'issuer', 'key_size']]
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
