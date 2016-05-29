#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Yanis Guenane <yanis+ansible@guenane.org>
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

from ansible.module_utils.basic import *
from OpenSSL import crypto
from random import randint

import os


DOCUMENTATION = '''
---
module: openssl_cert
author: "Yanis Guenane (@Spredzy)"
version_added: "2.2"
short_description: Generate OpenSSL Certificates
description:
    - "This module allows one to (re)generates OpenSSL certificates. It implements a notion
       of provider (ie. 'self-signed', 'letsencrypt'), it can be further extended.
       It uses the pyOpenSSL python library to interact with openssl."
requirements:
    - "python-pyOpenSSL"
options:
    state:
        required: false
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the certificate should exist or not, , taking action if the state is different from what is stated.
    name:
        required: true
        description:
            - Name of the generated OpenSSL certificate
    provider:
        required: true
        choices: ['self-signed', 'letsencrypt' ]
        description:
            -  Name of the provider to use to generate/retrieve the OpenSSL certificate
    force:
        required: false
        default: False
        choices: [ True, False ]
        description:
            - Should the certificate be forced regnerated by this ansible module
    path:
        required: true
        description:
            - Name of the folder in which the generated OpenSSL certificate  will be written
    csr:
        required: true
        description:
            - Path to the Certificate Signing Request (CSR) needed to generate this certificate

    digest:
        required: false
        default: "sha256"
        description:
            - Digest used when signing the certifate with the private key
    privatekey:
        required: false
        description:
            - Path to the privatekey to use when signing the certificate
    notBefore:
        required: false
        default: 0
        description:
            - Number of second from now which the generated certificate will be valid from
    notAfter:
        required: false
        default: 315360000
        description:
            - Number of second from now which the generated certificate will be expired

    accountkey:
        required: false
        description:
            - Path to the accountkey
    challenge:
        required: false
        description:
            - Path to the ACME challenge directory
'''


EXAMPLES = '''
# Generate a Self Signed OpenSSL certificate
- openssl_cert: name=www.ansible.com
                path=/etc/ssl/crt
                privatekey=/etc/ssl/private/ansible.com.pem
                csr=/etc/ssl/csr/ansible.com.csr
                provider='self-signed'

# Generate a Let's Encrypt Certificate
- openssl_cert: name=www.ansible.com
                path=/etc/ssl/crt
                accountkey=/etc/ssl/private/ansible.com.pem
                csr=/etc/ssl/csr/ansible.com.csr
                challenge=/etc/ssl/challenges/ansible.com/
                provider='letsencrypt'

# Force generate a Let's Encrypt Certificate
- openssl_cert: name=www.ansible.com
                path=/etc/ssl/crt
                accountkey=/etc/ssl/private/ansible.com.pem
                csr=/etc/ssl/csr/ansible.com.csr
                challenge=/etc/ssl/challenges/ansible.com/
                force=True
                provider='letsencrypt'
'''


RETURN = '''
crt:
    description: Path to the generated Certificate
    returned:
        - changed
        - success
    type: string
    sample: /etc/ssl/crt/www.ansible.com.crt
'''

class CertificateError(Exception):
    pass

class Certificate(object):

    def __init__(self, module):
        self.state = module.params['state']
        self.name = module.params['name']
        self.force = module.params['force']
        self.path = module.params['path']
        self.provider = module.params['provider']
        self.privatekey_path = module.params['privatekey']
        self.csr_path = module.params['csr']
        self.changed = True

    @property
    def file_path(self):
        return '%s.crt' % os.path.join(self.path, self.name)

    def generate(self):
        '''Generate the certificate signing request.'''
        pass

    def remove(self):
        '''Remove the Certificate Signing Request.'''

        try:
            os.remove(self.file_path)
        except OSError:
            self.changed = False

    def dump(self):
        '''Serialize the object into a dictionnary.'''
        pass


class SelfSignedCertificate(Certificate):
    '''Generate the self-signed certificate.'''

    def __init__(self, module):
        Certificate.__init__(self, module)
        self.serial_number = randint(1000, 99999)
        self.notBefore = module.params['notBefore']
        self.notAfter = module.params['notAfter']
        self.digest = module.params['digest']
        self.request = self.load_csr()
        self.privatekey = self.load_privatekey()
        self.certificate = None

    def load_privatekey(self):
        '''Load the privatekey object from buffer.'''

        privatekey_content = open(self.privatekey_path).read()
        return crypto.load_privatekey(crypto.FILETYPE_PEM, privatekey_content)

    def load_csr(self):
        '''Load the certificate signing request object from buffer.'''

        csr_content = open(self.csr_path).read()
        return crypto.load_certificate_request(crypto.FILETYPE_PEM, csr_content)

    def generate(self):

        if not self.force and os.path.exists(self.file_path):
            self.changed = False
            return

        cert = crypto.X509()
        cert.set_serial_number(self.serial_number)
        cert.gmtime_adj_notBefore(self.notBefore)
        cert.gmtime_adj_notAfter(self.notAfter)
        cert.set_subject(self.request.get_subject())
        cert.set_version(self.request.get_version() - 1)
        cert.set_pubkey(self.request.get_pubkey())
        try:
            # NOTE: This is only available starting from pyOpennSSL > 0.15
            cert.add_extensions(self.request.get_extensions())
        except:
            pass
        cert.sign(self.privatekey, self.digest )
        self.certificate = cert

        cert_file = open(self.file_path, 'w')
        cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, self.certificate))
        cert_file.close()

    def dump(self):

        result = {
          'name': self.name,
          'changed': self.changed,
          'crt': self.file_path,
          'notBefore': self.notBefore,
          'notAfter': self.notAfter,
          'serial_number': self.serial_number,
        }

        return result


class LetsEncryptCertificate(Certificate):
    '''Retrieve Let's Encrypt certificate.'''

    def __init__(self, module):
        Certificate.__init__(self, module)
        self.accountkey = module.params['accountkey']
        self.challenge_path = module.params['challenge']


    def generate(self):

        if not self.force and os.path.exists(self.file_path):
            self.changed = False
            return

        # TODO (spredzy): Ugly part should be done directly by interacting
        # with the acme protocol through python-acme
        os.system('acme-tiny --account-key %s --csr %s --acme-dir %s > %s' %
                 (self.accountkey, self.csr_path, self.challenge_path, self.file_path))

    def dump(self):

        result = {
          'name': self.name,
          'changed': self.changed,
          'crt': self.file_path,
          'account_key': self.accountkey,
        }

        return result

def main():
    module = AnsibleModule(
        argument_spec = dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            name=dict(required=True, type='str'),
            provider=dict(required=True, choices=['self-signed', 'letsencrypt'], type='str'),
            csr=dict(require=True, type='str'),
            force=dict(default=False, type='bool'),
            path=dict(required=True, type='str'),

            # provider: self-signed
            privatekey=dict(type='str'),
            digest=dict(default='sha256', type='str'),
            notBefore=dict(default=0, type='int'),
            notAfter=dict(default=315360000, type='int'),

            # provider: letsencrypt
            accountkey=dict(type='str'),
            challenge=dict(type='str'),
        )
    )

    path = module.params['path']
    provider = module.params['provider']

    if not os.path.isdir(path):
        module.fail_json(name=path, msg='The directory %s does not exist' % path)

    if provider == 'self-signed':
        cert = SelfSignedCertificate(module)
    elif provider == 'letsencrypt':
        cert = LetsEncryptCertificate(module)

    if module.params['state'] == 'present':
        try:
            cert.generate()
        except CertificateError:
            module.fail_json(name=module.params['name'], msg='An error occured while generating the certificate')
    else:
        cert.remove()

    result = cert.dump()

    module.exit_json(**result)


if __name__ == "__main__":
    main()
