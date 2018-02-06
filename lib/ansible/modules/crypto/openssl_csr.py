#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, Yanis Guenane <yanis+ansible@guenane.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: openssl_csr
author: "Yanis Guenane (@Spredzy)"
version_added: "2.4"
short_description: Generate OpenSSL Certificate Signing Request (CSR)
description:
    - "This module allows one to (re)generate OpenSSL certificate signing requests.
       It uses the pyOpenSSL python library to interact with openssl. This module supports
       the subjectAltName, keyUsage, extendedKeyUsage, basicConstraints and OCSP Must Staple
       extensions."
requirements:
    - "python-pyOpenSSL >= 0.15"
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
    version:
        required: false
        default: 1
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
            - Name of the file into which the generated OpenSSL certificate signing request will be written
    subject:
        required: false
        description:
            - Key/value pairs that will be present in the subject name field of the certificate signing request.
            - If you need to specify more than one value with the same key, use a list as value.
        version_added: '2.5'
    country_name:
        required: false
        aliases: [ 'C', 'countryName' ]
        description:
            - countryName field of the certificate signing request subject
    state_or_province_name:
        required: false
        aliases: [ 'ST', 'stateOrProvinceName' ]
        description:
            - stateOrProvinceName field of the certificate signing request subject
    locality_name:
        required: false
        aliases: [ 'L', 'localityName' ]
        description:
            - localityName field of the certificate signing request subject
    organization_name:
        required: false
        aliases: [ 'O', 'organizationName' ]
        description:
            - organizationName field of the certificate signing request subject
    organizational_unit_name:
        required: false
        aliases: [ 'OU', 'organizationalUnitName' ]
        description:
            - organizationalUnitName field of the certificate signing request subject
    common_name:
        required: false
        aliases: [ 'CN', 'commonName' ]
        description:
            - commonName field of the certificate signing request subject
    email_address:
        required: false
        aliases: [ 'E', 'emailAddress' ]
        description:
            - emailAddress field of the certificate signing request subject
    subject_alt_name:
        required: false
        aliases: [ 'subjectAltName' ]
        description:
            - SAN extension to attach to the certificate signing request
            - This can either be a 'comma separated string' or a YAML list.
    subject_alt_name_critical:
        required: false
        aliases: [ 'subjectAltName_critical' ]
        description:
            - Should the subjectAltName extension be considered as critical
    key_usage:
        required: false
        aliases: [ 'keyUsage' ]
        description:
            - This defines the purpose (e.g. encipherment, signature, certificate signing)
              of the key contained in the certificate.
            - This can either be a 'comma separated string' or a YAML list.
    key_usage_critical:
        required: false
        aliases: [ 'keyUsage_critical' ]
        description:
            - Should the keyUsage extension be considered as critical
    extended_key_usage:
        required: false
        aliases: [ 'extKeyUsage', 'extendedKeyUsage' ]
        description:
            - Additional restrictions (e.g. client authentication, server authentication)
              on the allowed purposes for which the public key may be used.
            - This can either be a 'comma separated string' or a YAML list.
    extended_key_usage_critical:
        required: false
        aliases: [ 'extKeyUsage_critical', 'extendedKeyUsage_critical' ]
        description:
            - Should the extkeyUsage extension be considered as critical
    basic_constraints:
        required: false
        aliases: ['basicConstraints']
        description:
            - Indicates basic constraints, such as if the certificate is a CA.
        version_added: 2.5
    basic_constraints_critical:
        required: false
        aliases: [ 'basicConstraints_critical' ]
        description:
            - Should the basicConstraints extension be considered as critical
        version_added: 2.5
    ocsp_must_staple:
        required: false
        aliases: ['ocspMustStaple']
        description:
            - Indicates that the certificate should contain the OCSP Must Staple
              extension (U(https://tools.ietf.org/html/rfc7633)).
        version_added: 2.5
    ocsp_must_staple_critical:
        required: false
        aliases: [ 'ocspMustStaple_critical' ]
        description:
            - Should the OCSP Must Staple extension be considered as critical
            - "Warning: according to the RFC, this extension should not be marked
               as critical, as old clients not knowing about OCSP Must Staple
               are required to reject such certificates
               (see U(https://tools.ietf.org/html/rfc7633#section-4))."
        version_added: 2.5
extends_documentation_fragment: files

notes:
    - "If the certificate signing request already exists it will be checked whether subjectAltName,
       keyUsage, extendedKeyUsage and basicConstraints only contain the requested values, whether
       OCSP Must Staple is as requested, and if the request was signed by the given private key."
'''


EXAMPLES = '''
# Generate an OpenSSL Certificate Signing Request
- openssl_csr:
    path: /etc/ssl/csr/www.ansible.com.csr
    privatekey_path: /etc/ssl/private/ansible.com.pem
    common_name: www.ansible.com

# Generate an OpenSSL Certificate Signing Request with a
# passphrase protected private key
- openssl_csr:
    path: /etc/ssl/csr/www.ansible.com.csr
    privatekey_path: /etc/ssl/private/ansible.com.pem
    privatekey_passphrase: ansible
    common_name: www.ansible.com

# Generate an OpenSSL Certificate Signing Request with Subject information
- openssl_csr:
    path: /etc/ssl/csr/www.ansible.com.csr
    privatekey_path: /etc/ssl/private/ansible.com.pem
    country_name: FR
    organization_name: Ansible
    email_address: jdoe@ansible.com
    common_name: www.ansible.com

# Generate an OpenSSL Certificate Signing Request with subjectAltName extension
- openssl_csr:
    path: /etc/ssl/csr/www.ansible.com.csr
    privatekey_path: /etc/ssl/private/ansible.com.pem
    subject_alt_name: 'DNS:www.ansible.com,DNS:m.ansible.com'

# Force re-generate an OpenSSL Certificate Signing Request
- openssl_csr:
    path: /etc/ssl/csr/www.ansible.com.csr
    privatekey_path: /etc/ssl/private/ansible.com.pem
    force: True
    common_name: www.ansible.com

# Generate an OpenSSL Certificate Signing Request with special key usages
- openssl_csr:
    path: /etc/ssl/csr/www.ansible.com.csr
    privatekey_path: /etc/ssl/private/ansible.com.pem
    common_name: www.ansible.com
    key_usage:
      - digitalSignature
      - keyAgreement
    extended_key_usage:
      - clientAuth

# Generate an OpenSSL Certificate Signing Request with OCSP Must Staple
- openssl_csr:
    path: /etc/ssl/csr/www.ansible.com.csr
    privatekey_path: /etc/ssl/private/ansible.com.pem
    common_name: www.ansible.com
    ocsp_must_staple: true
'''


RETURN = '''
privatekey:
    description: Path to the TLS/SSL private key the CSR was generated for
    returned: changed or success
    type: string
    sample: /etc/ssl/private/ansible.com.pem
filename:
    description: Path to the generated Certificate Signing Request
    returned: changed or success
    type: string
    sample: /etc/ssl/csr/www.ansible.com.csr
subject:
    description: A list of the subject tuples attached to the CSR
    returned: changed or success
    type: list
    sample: "[('CN', 'www.ansible.com'), ('O', 'Ansible')]"
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
basicConstraints:
    description: Indicates if the certificate belongs to a CA
    returned: changed or success
    type: list
    sample: ['CA:TRUE', 'pathLenConstraint:0']
ocsp_must_staple:
    description: Indicates whether the certificate has the OCSP
                 Must Staple feature enabled
    returned: changed or success
    type: bool
    sample: false
'''

import os

from ansible.module_utils import crypto as crypto_utils
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native, to_bytes

try:
    import OpenSSL
    from OpenSSL import crypto
except ImportError:
    pyopenssl_found = False
else:
    pyopenssl_found = True
    if OpenSSL.SSL.OPENSSL_VERSION_NUMBER >= 0x10100000:
        # OpenSSL 1.1.0 or newer
        MUST_STAPLE_NAME = b"tlsfeature"
        MUST_STAPLE_VALUE = b"status_request"
    else:
        # OpenSSL 1.0.x or older
        MUST_STAPLE_NAME = b"1.3.6.1.5.5.7.1.24"
        MUST_STAPLE_VALUE = b"DER:30:03:02:01:05"


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
        self.subjectAltName_critical = module.params['subjectAltName_critical']
        self.keyUsage = module.params['keyUsage']
        self.keyUsage_critical = module.params['keyUsage_critical']
        self.extendedKeyUsage = module.params['extendedKeyUsage']
        self.extendedKeyUsage_critical = module.params['extendedKeyUsage_critical']
        self.basicConstraints = module.params['basicConstraints']
        self.basicConstraints_critical = module.params['basicConstraints_critical']
        self.ocspMustStaple = module.params['ocspMustStaple']
        self.ocspMustStaple_critical = module.params['ocspMustStaple_critical']
        self.request = None
        self.privatekey = None

        self.subject = [
            ('C', module.params['countryName']),
            ('ST', module.params['stateOrProvinceName']),
            ('L', module.params['localityName']),
            ('O', module.params['organizationName']),
            ('OU', module.params['organizationalUnitName']),
            ('CN', module.params['commonName']),
            ('emailAddress', module.params['emailAddress']),
        ]

        if module.params['subject']:
            self.subject = self.subject + crypto_utils.parse_name_field(module.params['subject'])
        self.subject = [(entry[0], entry[1]) for entry in self.subject if entry[1]]

        if not self.subjectAltName:
            for sub in self.subject:
                if OpenSSL._util.lib.OBJ_txt2nid(to_bytes(sub[0])) == 13:  # 13 is the NID for "commonName"
                    self.subjectAltName = ['DNS:%s' % sub[1]]
                    break

    def generate(self, module):
        '''Generate the certificate signing request.'''

        if not self.check(module, perms_required=False) or self.force:
            req = crypto.X509Req()
            req.set_version(self.version - 1)
            subject = req.get_subject()
            for entry in self.subject:
                if entry[1] is not None:
                    # Workaround for https://github.com/pyca/pyopenssl/issues/165
                    nid = OpenSSL._util.lib.OBJ_txt2nid(to_bytes(entry[0]))
                    OpenSSL._util.lib.X509_NAME_add_entry_by_NID(subject._name, nid, OpenSSL._util.lib.MBSTRING_UTF8, to_bytes(entry[1]), -1, -1, 0)

            extensions = []
            if self.subjectAltName:
                altnames = ', '.join(self.subjectAltName)
                extensions.append(crypto.X509Extension(b"subjectAltName", self.subjectAltName_critical, altnames.encode('ascii')))

            if self.keyUsage:
                usages = ', '.join(self.keyUsage)
                extensions.append(crypto.X509Extension(b"keyUsage", self.keyUsage_critical, usages.encode('ascii')))

            if self.extendedKeyUsage:
                usages = ', '.join(self.extendedKeyUsage)
                extensions.append(crypto.X509Extension(b"extendedKeyUsage", self.extendedKeyUsage_critical, usages.encode('ascii')))

            if self.basicConstraints:
                usages = ', '.join(self.basicConstraints)
                extensions.append(crypto.X509Extension(b"basicConstraints", self.basicConstraints_critical, usages.encode('ascii')))

            if self.ocspMustStaple:
                extensions.append(crypto.X509Extension(MUST_STAPLE_NAME, self.ocspMustStaple_critical, MUST_STAPLE_VALUE))

            if extensions:
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
            subject = [(OpenSSL._util.lib.OBJ_txt2nid(to_bytes(sub[0])), to_bytes(sub[1])) for sub in self.subject]
            current_subject = [(OpenSSL._util.lib.OBJ_txt2nid(to_bytes(sub[0])), to_bytes(sub[1])) for sub in csr.get_subject().get_components()]
            if not set(subject) == set(current_subject):
                return False

            return True

        def _check_subjectAltName(extensions):
            altnames_ext = next((ext for ext in extensions if ext.get_short_name() == b'subjectAltName'), '')
            altnames = [altname.strip() for altname in str(altnames_ext).split(',')]
            # apperently openssl returns 'IP address' not 'IP' as specifier when converting the subjectAltName to string
            # although it won't accept this specifier when generating the CSR. (https://github.com/openssl/openssl/issues/4004)
            altnames = [name if not name.startswith('IP Address:') else "IP:" + name.split(':', 1)[1] for name in altnames]
            if self.subjectAltName:
                if set(altnames) != set(self.subjectAltName) or altnames_ext.get_critical() != self.subjectAltName_critical:
                    return False
            else:
                if altnames:
                    return False

            return True

        def _check_keyUsage_(extensions, extName, expected, critical):
            usages_ext = [ext for ext in extensions if ext.get_short_name() == extName]
            if (not usages_ext and expected) or (usages_ext and not expected):
                return False
            elif not usages_ext and not expected:
                return True
            else:
                current = [OpenSSL._util.lib.OBJ_txt2nid(to_bytes(usage.strip())) for usage in str(usages_ext[0]).split(',')]
                expected = [OpenSSL._util.lib.OBJ_txt2nid(to_bytes(usage)) for usage in expected]
                return set(current) == set(expected) and usages_ext[0].get_critical() == critical

        def _check_keyUsage(extensions):
            return _check_keyUsage_(extensions, b'keyUsage', self.keyUsage, self.keyUsage_critical)

        def _check_extenededKeyUsage(extensions):
            return _check_keyUsage_(extensions, b'extendedKeyUsage', self.extendedKeyUsage, self.extendedKeyUsage_critical)

        def _check_basicConstraints(extensions):
            return _check_keyUsage_(extensions, b'basicConstraints', self.basicConstraints, self.basicConstraints_critical)

        def _check_ocspMustStaple(extensions):
            oms_ext = [ext for ext in extensions if ext.get_short_name() == MUST_STAPLE_NAME and str(ext) == MUST_STAPLE_VALUE]
            if OpenSSL.SSL.OPENSSL_VERSION_NUMBER < 0x10100000:
                # Older versions of libssl don't know about OCSP Must Staple
                oms_ext.extend([ext for ext in extensions if ext.get_short_name() == b'UNDEF' and ext.get_data() == b'\x30\x03\x02\x01\x05'])
            if self.ocspMustStaple:
                return len(oms_ext) > 0 and oms_ext[0].get_critical() == self.ocspMustStaple_critical
            else:
                return len(oms_ext) == 0

        def _check_extensions(csr):
            extensions = csr.get_extensions()
            return (_check_subjectAltName(extensions) and _check_keyUsage(extensions) and
                    _check_extenededKeyUsage(extensions) and _check_basicConstraints(extensions) and
                    _check_ocspMustStaple(extensions))

        def _check_signature(csr):
            try:
                return csr.verify(self.privatekey)
            except crypto.Error:
                return False

        if not state_and_perms:
            return False

        csr = crypto_utils.load_certificate_request(self.path)

        return _check_subject(csr) and _check_extensions(csr) and _check_signature(csr)

    def dump(self):
        '''Serialize the object into a dictionary.'''

        result = {
            'privatekey': self.privatekey_path,
            'filename': self.path,
            'subject': self.subject,
            'subjectAltName': self.subjectAltName,
            'keyUsage': self.keyUsage,
            'extendedKeyUsage': self.extendedKeyUsage,
            'basicConstraints': self.basicConstraints,
            'ocspMustStaple': self.ocspMustStaple,
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
            version=dict(default='1', type='int'),
            force=dict(default=False, type='bool'),
            path=dict(required=True, type='path'),
            subject=dict(type='dict'),
            countryName=dict(aliases=['C', 'country_name'], type='str'),
            stateOrProvinceName=dict(aliases=['ST', 'state_or_province_name'], type='str'),
            localityName=dict(aliases=['L', 'locality_name'], type='str'),
            organizationName=dict(aliases=['O', 'organization_name'], type='str'),
            organizationalUnitName=dict(aliases=['OU', 'organizational_unit_name'], type='str'),
            commonName=dict(aliases=['CN', 'common_name'], type='str'),
            emailAddress=dict(aliases=['E', 'email_address'], type='str'),
            subjectAltName=dict(aliases=['subject_alt_name'], type='list'),
            subjectAltName_critical=dict(aliases=['subject_alt_name_critical'], default=False, type='bool'),
            keyUsage=dict(aliases=['key_usage'], type='list'),
            keyUsage_critical=dict(aliases=['key_usage_critical'], default=False, type='bool'),
            extendedKeyUsage=dict(aliases=['extKeyUsage', 'extended_key_usage'], type='list'),
            extendedKeyUsage_critical=dict(aliases=['extKeyUsage_critical', 'extended_key_usage_critical'], default=False, type='bool'),
            basicConstraints=dict(aliases=['basic_constraints'], type='list'),
            basicConstraints_critical=dict(aliases=['basic_constraints_critical'], default=False, type='bool'),
            ocspMustStaple=dict(aliases=['ocsp_must_staple'], default=False, type='bool'),
            ocspMustStaple_critical=dict(aliases=['ocsp_must_staple_critical'], default=False, type='bool'),
        ),
        add_file_common_args=True,
        supports_check_mode=True,
    )

    if not pyopenssl_found:
        module.fail_json(msg='the python pyOpenSSL module is required')

    try:
        getattr(crypto.X509Req, 'get_extensions')
    except AttributeError:
        module.fail_json(msg='You need to have PyOpenSSL>=0.15 to generate CSRs')

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
