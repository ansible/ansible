#!/usr/bin/python
#
# (c) 2016, Kevin Coming (@waffie1)
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

DOCUMENTATION = '''
module: bigip_ssl_certificate
short_description: Import/Delete certificates from BIG-IP
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
    required: false
  key_content:
    description:
      - When used instead of 'key_src', sets the contents of a certificate key
        directly to the specified value. This is used with lookup plugins or for
        anything with formatting or templating. Either one of C(key_src),
        C(key_content), C(cert_src) or C(cert_content) must be provided when
        C(state) is C(present).
    required: false
  state:
    description:
      - Certificate and key state. This determines if the provided certificate
        and key is to be made C(present) on the device or C(absent).
    required: true
    default: present
    choices:
      - present
      - absent
  partition:
    description:
      - BIG-IP partition to use when adding/deleting certificate.
    required: false
    default: Common
  name:
    description:
      - SSL Certificate Name.  This is the cert/key pair name used
        when importing a certificate/key into the F5. It also
        determines the filenames of the objects on the LTM
        (:Partition:name.cer_11111_1 and :Partition_name.key_11111_1).
    required: true
  cert_src:
    description:
      - This is the local filename of the certificate. Either one of C(key_src),
        C(key_content), C(cert_src) or C(cert_content) must be provided when
        C(state) is C(present).
    required: false
  key_src:
    description:
      - This is the local filename of the private key. Either one of C(key_src),
        C(key_content), C(cert_src) or C(cert_content) must be provided when
        C(state) is C(present).
    required: false
  passphrase:
    description:
      - Passphrase on certificate private key
    required: false
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install f5-sdk.
  - Requires the netaddr Python package on the host.
  - If you use this module, you will not be able to remove the certificates
    and keys that are managed, via the web UI. You can only remove them via
    tmsh or these modules.
extends_documentation_fragment: f5
requirements:
    - f5-sdk >= 1.5.0
    - BigIP >= v12
author:
    - Kevin Coming (@waffie1)
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
    description: >
        The name of the SSL certificate. The C(cert_name) and
        C(key_name) will be equal to each other.
    returned:
        - created
        - changed
        - deleted
    type: string
    sample: "cert1"
key_name:
    description: >
        The name of the SSL certificate key. The C(key_name) and
        C(cert_name) will be equal to each other.
    returned:
        - created
        - changed
        - deleted
    type: string
    sample: "key1"
partition:
    description: Partition in which the cert/key was created
    returned:
        - changed
        - created
        - deleted
    type: string
    sample: "Common"
key_checksum:
    description: SHA1 checksum of the key that was provided
    return:
        - changed
        - created
    type: string
    sample: "cf23df2207d99a74fbe169e3eba035e633b65d94"
cert_checksum:
    description: SHA1 checksum of the cert that was provided
    return:
        - changed
        - created
    type: string
    sample: "f7ff9e8b7bb2e09b70935a5d785e0cc5d9d0abf0"
'''


try:
    from f5.bigip.contexts import TransactionContextManager
    from f5.bigip import ManagementRoot
    from icontrol.session import iControlUnexpectedHTTPError
    HAS_F5SDK = True
except ImportError:
    HAS_F5SDK = False


import hashlib
import StringIO


class BigIpSslCertificate(object):
    def __init__(self, *args, **kwargs):
        if not HAS_F5SDK:
            raise F5ModuleError("The python f5-sdk module is required")

        required_args = ['key_content', 'key_src', 'cert_content', 'cert_src']

        ksource = kwargs['key_src']
        if ksource:
            with open(ksource) as f:
                kwargs['key_content'] = f.read()

        csource = kwargs['cert_src']
        if csource:
            with open(csource) as f:
                kwargs['cert_content'] = f.read()

        if kwargs['state'] == 'present':
            if not any(kwargs[k] is not None for k in required_args):
                raise F5ModuleError(
                    "Either 'key_content', 'key_src', 'cert_content' or "
                    "'cert_src' must be provided"
                )

        # This is the remote BIG-IP path from where it will look for certs
        # to install.
        self.dlpath = '/var/config/rest/downloads'

        # The params that change in the module
        self.cparams = dict()

        # Stores the params that are sent to the module
        self.params = kwargs
        self.api = ManagementRoot(kwargs['server'],
                                  kwargs['user'],
                                  kwargs['password'],
                                  port=kwargs['server_port'])

    def exists(self):
        cert = self.cert_exists()
        key = self.key_exists()

        if cert and key:
            return True
        else:
            return False

    def get_hash(self, content):
        k = hashlib.sha1()
        s = StringIO.StringIO(content)
        while True:
            data = s.read(1024)
            if not data:
                break
            k.update(data)
        return k.hexdigest()

    def present(self):
        current = self.read()
        changed = False
        do_key = False
        do_cert = False
        chash = None
        khash = None

        check_mode = self.params['check_mode']
        name = self.params['name']
        partition = self.params['partition']
        cert_content = self.params['cert_content']
        key_content = self.params['key_content']
        passphrase = self.params['passphrase']

        # Technically you dont need to provide us with anything in the form
        # of content for your cert, but that's kind of illogical, so we just
        # return saying you didn't "do" anything if you left the cert and keys
        # empty.
        if not cert_content and not key_content:
            return False

        if key_content is not None:
            if 'key_checksum' in current:
                khash = self.get_hash(key_content)
                if khash not in current['key_checksum']:
                    do_key = "update"
            else:
                do_key = "create"

        if cert_content is not None:
            if 'cert_checksum' in current:
                chash = self.get_hash(cert_content)
                if chash not in current['cert_checksum']:
                    do_cert = "update"
            else:
                do_cert = "create"

        if do_cert or do_key:
            changed = True
            params = dict()
            params['cert_name'] = name
            params['key_name'] = name
            params['partition'] = partition
            if khash:
                params['key_checksum'] = khash
            if chash:
                params['cert_checksum'] = chash
            self.cparams = params

            if check_mode:
                return changed

        if not do_cert and not do_key:
            return False

        tx = self.api.tm.transactions.transaction
        with TransactionContextManager(tx) as api:
            if do_cert:
                # Upload the content of a certificate as a StringIO object
                cstring = StringIO.StringIO(cert_content)
                filename = "%s.crt" % (name)
                filepath = os.path.join(self.dlpath, filename)
                api.shared.file_transfer.uploads.upload_stringio(
                    cstring,
                    filename
                )

            if do_cert == "update":
                # Install the certificate
                params = {
                    'name': name,
                    'partition': partition
                }
                cert = api.tm.sys.file.ssl_certs.ssl_cert.load(**params)

                # This works because, while the source path is the same,
                # calling update causes the file to be re-read
                cert.update()
                changed = True
            elif do_cert == "create":
                # Install the certificate
                params = {
                    'sourcePath': "file://" + filepath,
                    'name': name,
                    'partition': partition
                }
                api.tm.sys.file.ssl_certs.ssl_cert.create(**params)
                changed = True

            if do_key:
                # Upload the content of a certificate key as a StringIO object
                kstring = StringIO.StringIO(key_content)
                filename = "%s.key" % (name)
                filepath = os.path.join(self.dlpath, filename)
                api.shared.file_transfer.uploads.upload_stringio(
                    kstring,
                    filename
                )

            if do_key == "update":
                # Install the key
                params = {
                    'name': name,
                    'partition': partition
                }
                key = api.tm.sys.file.ssl_keys.ssl_key.load(**params)

                params = dict()

                if passphrase:
                    params['passphrase'] = passphrase
                else:
                    params['passphrase'] = None

                key.update(**params)
                changed = True
            elif do_key == "create":
                # Install the key
                params = {
                    'sourcePath': "file://" + filepath,
                    'name': name,
                    'partition': partition
                }
                if passphrase:
                    params['passphrase'] = self.params['passphrase']
                else:
                    params['passphrase'] = None

                api.tm.sys.file.ssl_keys.ssl_key.create(**params)
                changed = True
        return changed

    def key_exists(self):
        return self.api.tm.sys.file.ssl_keys.ssl_key.exists(
            name=self.params['name'],
            partition=self.params['partition']
        )

    def cert_exists(self):
        return self.api.tm.sys.file.ssl_certs.ssl_cert.exists(
            name=self.params['name'],
            partition=self.params['partition']
        )

    def read(self):
        p = dict()
        name = self.params['name']
        partition = self.params['partition']

        if self.key_exists():
            key = self.api.tm.sys.file.ssl_keys.ssl_key.load(
                name=name,
                partition=partition
            )
            if hasattr(key, 'checksum'):
                p['key_checksum'] = str(key.checksum)

        if self.cert_exists():
            cert = self.api.tm.sys.file.ssl_certs.ssl_cert.load(
                name=name,
                partition=partition
            )
            if hasattr(cert, 'checksum'):
                p['cert_checksum'] = str(cert.checksum)

        p['name'] = name
        return p

    def flush(self):
        result = dict()
        state = self.params['state']

        try:
            if state == "present":
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        result.update(**self.cparams)
        result.update(dict(changed=changed))
        return result

    def absent(self):
        changed = False

        if self.exists():
            changed = self.delete()

        return changed

    def delete(self):
        changed = False

        check_mode = self.params['check_mode']

        delete_cert = self.cert_exists()
        delete_key = self.key_exists()

        if not delete_cert and not delete_key:
            return changed

        if check_mode:
            params = dict()
            params['cert_name'] = name
            params['key_name'] = name
            params['partition'] = partition
            self.cparams = params
            return True

        tx = self.api.tm.transactions.transaction
        with TransactionContextManager(tx) as api:
            if delete_cert:
                # Delete the certificate
                c = api.tm.sys.file.ssl_certs.ssl_cert.load(
                    name=self.params['name'],
                    partition=self.params['partition']
                )
                c.delete()
                changed = True

            if delete_key:
                # Delete the certificate key
                k = self.api.tm.sys.file.ssl_keys.ssl_key.load(
                    name=self.params['name'],
                    partition=self.params['partition']
                )
                k.delete()
                changed = True
        return changed


def main():
    argument_spec = f5_argument_spec()

    meta_args = dict(
        name=dict(type='str', required=True),
        cert_content=dict(type='str', default=None),
        cert_src=dict(type='path', default=None),
        key_content=dict(type='str', default=None),
        key_src=dict(type='path', default=None),
        passphrase=dict(type='str', default=None, no_log=True)
    )

    argument_spec.update(meta_args)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ['key_content', 'key_src'],
            ['cert_content', 'cert_src']
        ]
    )

    try:
        obj = BigIpSslCertificate(check_mode=module.check_mode,
                                  **module.params)
        result = obj.flush()
        module.exit_json(**result)
    except F5ModuleError as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.basic import *
from ansible.module_utils.f5 import *

if __name__ == '__main__':
    main()
