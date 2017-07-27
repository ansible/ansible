#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, Yanis Guenane <yanis+ansible@guenane.org>
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: openssl_csr
author: "Yanis Guenane (@Spredzy)"
version_added: "2.4"
short_description: Generate OpenSSL Certificate Signing Request (CSR)
description:
    - "This module allows one to (re)generates OpenSSL certificate signing requests.
       It uses the pyOpenSSL python library to interact with openssl. This module support
       the subjectAltName extension. Note: At least one of commonName or subjectAltName must
       be specified. This module uses file common arguments to specify generated file permissions."
requirements:
    - "python-pyOpenSSL"
options:
    state:
        required: false
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the certificate signing request should exist or not, taking action if the state is different from what is stated.
    digest:
        required: false
        default: "sha256"
        description:
            - Digest used when signing the certificate signing request with the private key
    privatekey_path:
        required: true
        description:
            - Path to the privatekey to use when signing the certificate signing request
    privatekey_passphrase:
        required: false
        description:
            - The passphrase for the privatekey.
        version_added: "2.4"
    version:
        required: false
        default: 3
        description:
            - Version of the certificate signing request
    force:
        required: false
        default: False
        choices: [ True, False ]
        description:
            - Should the certificate signing request be forced regenerated by this ansible module
    path:
        required: true
        description:
            - Name of the folder in which the generated OpenSSL certificate signing request will be written
    countryName:
        required: false
        aliases: [ 'C' ]
        description:
            - countryName field of the certificate signing request subject
    stateOrProvinceName:
        required: false
        aliases: [ 'ST' ]
        description:
            - stateOrProvinceName field of the certificate signing request subject
    localityName:
        required: false
        aliases: [ 'L' ]
        description:
            - localityName field of the certificate signing request subject
    organizationName:
        required: false
        aliases: [ 'O' ]
        description:
            - organizationName field of the certificate signing request subject
    organizationalUnitName:
        required: false
        aliases: [ 'OU' ]
        description:
            - organizationalUnitName field of the certificate signing request subject
    commonName:
        required: false
        aliases: [ 'CN' ]
        description:
            - commonName field of the certificate signing request subject
    emailAddress:
        required: false
        aliases: [ 'E' ]
        description:
            - emailAddress field of the certificate signing request subject
    subjectAltName:
        required: false
        description:
            - SAN extension to attach to the certificate signing request
            - This can either be a 'comma separated string' or a YAML list.
    keyUsage:
        required: false
        description:
            - This defines the purpose (e.g. encipherment, signature, certificate signing)
              of the key contained in the certificate.
            - This can either be a 'comma separated string' or a YAML list.
    extendedKeyUsage:
        required: false
        aliases: [ 'extKeyUsage' ]
        description:
            - Additional restrictions (e.g. client authentication, server authentication)
              on the allowed purposes for which the public key may be used.
            - This can either be a 'comma separated string' or a YAML list.

notes:
    - "If the certificate signing request already exists it will be checked whether subjectAltName,
       keyUsage and extendedKeyUsage only contain the requested values and if the request was signed
       by the given private key"
'''


EXAMPLES = '''
# Generate an OpenSSL Certificate Signing Request
- openssl_csr:
    path: /etc/ssl/csr/www.ansible.com.csr
    privatekey_path: /etc/ssl/private/ansible.com.pem
    commonName: www.ansible.com

# Generate an OpenSSL Certificate Signing Request with a
# passphrase protected private key
- openssl_csr:
    path: /etc/ssl/csr/www.ansible.com.csr
    privatekey_path: /etc/ssl/private/ansible.com.pem
    privatekey_passphrase: ansible
    commonName: www.ansible.com

# Generate an OpenSSL Certificate Signing Request with Subject information
- openssl_csr:
    path: /etc/ssl/csr/www.ansible.com.csr
    privatekey_path: /etc/ssl/private/ansible.com.pem
    countryName: FR
    organizationName: Ansible
    emailAddress: jdoe@ansible.com
    commonName: www.ansible.com

# Generate an OpenSSL Certificate Signing Request with subjectAltName extension
- openssl_csr:
    path: /etc/ssl/csr/www.ansible.com.csr
    privatekey_path: /etc/ssl/private/ansible.com.pem
    subjectAltName: 'DNS:www.ansible.com,DNS:m.ansible.com'

# Force re-generate an OpenSSL Certificate Signing Request
- openssl_csr:
    path: /etc/ssl/csr/www.ansible.com.csr
    privatekey_path: /etc/ssl/private/ansible.com.pem
    force: True
    commonName: www.ansible.com

# Generate an OpenSSL Certificate Signing Request with special key usages
- openssl_csr:
    path: /etc/ssl/csr/www.ansible.com.csr
    privatekey_path: /etc/ssl/private/ansible.com.pem
    commonName: www.ansible.com
    keyUsage:
      - digitlaSignature
      - keyAgreement
    extKeyUsage:
      - clientAuth
'''


RETURN = '''
csr:
    description: Path to the generated Certificate Signing Request
    returned: changed or success
    type: string
    sample: /etc/ssl/csr/www.ansible.com.csr
subject:
    description: A dictionnary of the subject attached to the CSR
    returned: changed or success
    type: list
    sample: {'CN': 'www.ansible.com', 'O': 'Ansible'}
subjectAltName:
    description: The alternative names this CSR is valid for
    returned: changed or success
    type: list
    sample: [ 'DNS:www.ansible.com', 'DNS:m.ansible.com' ]
keyUsage:
    description: Purpose for which the public key may be used
    returned: changed or success
    type: list
    sample: [ 'digitalSignature', 'keyAgreement' ]
extendedKeyUsage:
    description: Additional restriction on the public key purposes
    returned: changed or success
    type: list
    sample: [ 'clientAuth' ]
'''

import os

from ansible.module_utils import crypto as crypto_utils
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

try:
    from OpenSSL import crypto
except ImportError:
    pyopenssl_found = False
else:
    pyopenssl_found = True


class CertificateSigningRequestError(crypto_utils.OpenSSLObjectError):
    pass


class CertificateSigningRequest(crypto_utils.OpenSSLObject):

    def __init__(self, module):
        super(CertificateSigningRequest, self).__init__(
            module.params['path'],
            module.params['state'],
            module.params['force'],
            module.check_mode
        )
        self.digest = module.params['digest']
        self.privatekey_path = module.params['privatekey_path']
        self.privatekey_passphrase = module.params['privatekey_passphrase']
        self.version = module.params['version']
        self.subjectAltName = module.params['subjectAltName']
        self.keyUsage = module.params['keyUsage']
        self.extendedKeyUsage = module.params['extendedKeyUsage']
        self.request = None
        self.privatekey = None

        self.subject = {
            'C': module.params['countryName'],
            'ST': module.params['stateOrProvinceName'],
            'L': module.params['localityName'],
            'O': module.params['organizationName'],
            'OU': module.params['organizationalUnitName'],
            'CN': module.params['commonName'],
            'emailAddress': module.params['emailAddress'],
        }

        if not self.subjectAltName:
            self.subjectAltName = ['DNS:%s' % self.subject['CN']]

        self.subject = dict((k, v) for k, v in self.subject.items() if v)

    def generate(self, module):
        '''Generate the certificate signing request.'''

        if not self.check(module, perms_required=False) or self.force:
            req = crypto.X509Req()
            req.set_version(self.version)
            subject = req.get_subject()
            for (key, value) in self.subject.items():
                if value is not None:
                    setattr(subject, key, value)

            altnames = ', '.join(self.subjectAltName)
            extensions = [crypto.X509Extension(b"subjectAltName", False, altnames.encode('ascii'))]

            if self.keyUsage:
                usages = ', '.join(self.keyUsage)
                extensions.append(crypto.X509Extension(b"keyUsage", False, usages.encode('ascii')))

            if self.extendedKeyUsage:
                usages = ', '.join(self.extendedKeyUsage)
                extensions.append(crypto.X509Extension(b"extendedKeyUsage", False, usages.encode('ascii')))

            req.add_extensions(extensions)

            req.set_pubkey(self.privatekey)
            req.sign(self.privatekey, self.digest)
            self.request = req

            try:
                csr_file = open(self.path, 'wb')
                csr_file.write(crypto.dump_certificate_request(crypto.FILETYPE_PEM, self.request))
                csr_file.close()
            except (IOError, OSError) as exc:
                raise CertificateSigningRequestError(exc)

            self.changed = True

        file_args = module.load_file_common_arguments(module.params)
        if module.set_fs_attributes_if_different(file_args, False):
            self.changed = True

    def check(self, module, perms_required=True):
        """Ensure the resource is in its desired state."""
        state_and_perms = super(CertificateSigningRequest, self).check(module, perms_required)

        self.privatekey = crypto_utils.load_privatekey(self.privatekey_path, self.privatekey_passphrase)

        def _check_subject(csr):
            subject = csr.get_subject()
            for (key, value) in self.subject.items():
                if getattr(subject, key, None) != value:
                    return False

            return True

        def _check_subjectAltName(extensions):
            altnames_ext = next((ext.__str__() for ext in extensions if ext.get_short_name() == b'subjectAltName'), '')
            altnames = [altname.strip() for altname in altnames_ext.split(',')]
            # apperently openssl returns 'IP address' not 'IP' as specifier when converting the subjectAltName to string
            # although it won't accept this specifier when generating the CSR. (https://github.com/openssl/openssl/issues/4004)
            altnames = [name if not name.startswith('IP Address:') else "IP:" + name.split(':', 1)[1] for name in altnames]
            if self.subjectAltName:
                if set(altnames) != set(self.subjectAltName):
                    return False
            else:
                if altnames:
                    return False

            return True

        def _check_keyUsage_(extensions, extName, expected, long):
            usages_ext = [str(ext) for ext in extensions if ext.get_short_name() == extName]
            if (not usages_ext and expected) or (usages_ext and not expected):
                return False
            elif not usages_ext and not expected:
                return True
            else:
                current = [usage.strip() for usage in usages_ext[0].split(',')]
                expected = [long[usage] if usage in long else usage for usage in expected]
                return current == expected

        def _check_keyUsage(extensions):
            return _check_keyUsage_(extensions, b'keyUsage', self.keyUsage, crypto_utils.keyUsageLong)

        def _check_extenededKeyUsage(extensions):
            return _check_keyUsage_(extensions, b'extendedKeyUsage', self.extendedKeyUsage, crypto_utils.extendedKeyUsageLong)

        def _check_extensions(csr):
            extensions = csr.get_extensions()
            return _check_subjectAltName(extensions) and _check_keyUsage(extensions) and _check_extenededKeyUsage(extensions)

        def _check_signature(csr, privatekey):
            try:
                return csr.verify(privatekey)
            except crypto.Error:
                return False

        if not state_and_perms:
            return False

        csr = crypto_utils.load_certificate_request(self.path)

        return _check_subject(csr) and _check_extensions(csr) and _check_signature(csr, self.privatekey)

    def dump(self):
        '''Serialize the object into a dictionary.'''

        result = {
            'privatekey': self.privatekey_path,
            'filename': self.path,
            'subject': self.subject,
            'subjectAltName': self.subjectAltName,
            'keyUsage': self.keyUsage,
            'extendedKeyUsage': self.extendedKeyUsage,
            'changed': self.changed
        }

        return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            digest=dict(default='sha256', type='str'),
            privatekey_path=dict(require=True, type='path'),
            privatekey_passphrase=dict(type='str', no_log=True),
            version=dict(default='3', type='int'),
            force=dict(default=False, type='bool'),
            path=dict(required=True, type='path'),
            countryName=dict(aliases=['C'], type='str'),
            stateOrProvinceName=dict(aliases=['ST'], type='str'),
            localityName=dict(aliases=['L'], type='str'),
            organizationName=dict(aliases=['O'], type='str'),
            organizationalUnitName=dict(aliases=['OU'], type='str'),
            commonName=dict(aliases=['CN'], type='str'),
            emailAddress=dict(aliases=['E'], type='str'),
            subjectAltName=dict(aliases=['subjectAltName'], type='list'),
            keyUsage=dict(type='list'),
            extendedKeyUsage=dict(aliases=['extKeyUsage'], type='list'),
        ),
        add_file_common_args=True,
        supports_check_mode=True,
        required_one_of=[['commonName', 'subjectAltName']],
    )

    if not pyopenssl_found:
        module.fail_json(msg='the python pyOpenSSL module is required')

    base_dir = os.path.dirname(module.params['path'])
    if not os.path.isdir(base_dir):
        module.fail_json(name=base_dir, msg='The directory %s does not exist or the file is not a directory' % base_dir)

    csr = CertificateSigningRequest(module)

    if module.params['state'] == 'present':

        if module.check_mode:
            result = csr.dump()
            result['changed'] = module.params['force'] or not csr.check(module)
            module.exit_json(**result)

        try:
            csr.generate(module)
        except (CertificateSigningRequestError, crypto_utils.OpenSSLObjectError) as exc:
            module.fail_json(msg=to_native(exc))

    else:

        if module.check_mode:
            result = csr.dump()
            result['changed'] = os.path.exists(module.params['path'])
            module.exit_json(**result)

        try:
            csr.remove()
        except (CertificateSigningRequestError, crypto_utils.OpenSSLObjectError) as exc:
            module.fail_json(msg=to_native(exc))

    result = csr.dump()

    module.exit_json(**result)


if __name__ == "__main__":
    main()
