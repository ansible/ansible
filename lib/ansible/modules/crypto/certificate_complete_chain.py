#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: certificate_complete_chain
author: "Felix Fontein (@felixfontein)"
version_added: "2.7"
short_description: Complete certificate chain given a set of untrusted and root certificates
description:
    - "This module completes a given chain of certificates in PEM format by finding
       intermediate certificates from a given set of certificates, until it finds a root
       certificate in another given set of certificates."
    - "This can for example be used to find the root certificate for a certificate chain
       returned by M(acme_certificate)."
    - "Note that this module does I(not) check for validity of the chains. It only
       checks that issuer and subject match, and that the signature is correct. It
       ignores validity dates and key usage completely. If you need to verify that a
       generated chain is valid, please use C(openssl verify ...)."
requirements:
    - "cryptography >= 1.5"
options:
    input_chain:
        description:
            - A concatenated set of certificates in PEM format forming a chain.
            - The module will try to complete this chain.
        type: str
        required: yes
    root_certificates:
        description:
            - "A list of filenames or directories."
            - "A filename is assumed to point to a file containing one or more certificates
               in PEM format. All certificates in this file will be added to the set of
               root certificates."
            - "If a directory name is given, all files in the directory and its
               subdirectories will be scanned and tried to be parsed as concatenated
               certificates in PEM format."
            - "Symbolic links will be followed."
        type: list
        elements: path
        required: yes
    intermediate_certificates:
        description:
            - "A list of filenames or directories."
            - "A filename is assumed to point to a file containing one or more certificates
               in PEM format. All certificates in this file will be added to the set of
               root certificates."
            - "If a directory name is given, all files in the directory and its
               subdirectories will be scanned and tried to be parsed as concatenated
               certificates in PEM format."
            - "Symbolic links will be followed."
        type: list
        elements: path
        default: []
'''


EXAMPLES = '''
# Given a leaf certificate for www.ansible.com and one or more intermediate
# certificates, finds the associated root certificate.
- name: Find root certificate
  certificate_complete_chain:
    input_chain: "{{ lookup('file', '/etc/ssl/csr/www.ansible.com-fullchain.pem') }}"
    root_certificates:
    - /etc/ca-certificates/
  register: www_ansible_com
- name: Write root certificate to disk
  copy:
    dest: /etc/ssl/csr/www.ansible.com-root.pem
    content: "{{ www_ansible_com.root }}"

# Given a leaf certificate for www.ansible.com, and a list of intermediate
# certificates, finds the associated root certificate.
- name: Find root certificate
  certificate_complete_chain:
    input_chain: "{{ lookup('file', '/etc/ssl/csr/www.ansible.com.pem') }}"
    intermediate_certificates:
    - /etc/ssl/csr/www.ansible.com-chain.pem
    root_certificates:
    - /etc/ca-certificates/
  register: www_ansible_com
- name: Write complete chain to disk
  copy:
    dest: /etc/ssl/csr/www.ansible.com-completechain.pem
    content: "{{ ''.join(www_ansible_com.complete_chain) }}"
- name: Write root chain (intermediates and root) to disk
  copy:
    dest: /etc/ssl/csr/www.ansible.com-rootchain.pem
    content: "{{ ''.join(www_ansible_com.chain) }}"
'''


RETURN = '''
root:
    description:
        - "The root certificate in PEM format."
    returned: success
    type: str
chain:
    description:
        - "The chain added to the given input chain. Includes the root certificate."
        - "Returned as a list of PEM certificates."
    returned: success
    type: list
complete_chain:
    description:
        - "The completed chain, including leaf, all intermediates, and root."
        - "Returned as a list of PEM certificates."
    returned: success
    type: list
'''

import os
import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_bytes

CRYPTOGRAPHY_IMP_ERR = None
try:
    import cryptography
    import cryptography.hazmat.backends
    import cryptography.hazmat.primitives.serialization
    import cryptography.hazmat.primitives.asymmetric.rsa
    import cryptography.hazmat.primitives.asymmetric.ec
    import cryptography.hazmat.primitives.asymmetric.padding
    import cryptography.hazmat.primitives.hashes
    import cryptography.hazmat.primitives.asymmetric.utils
    import cryptography.x509
    import cryptography.x509.oid
    from distutils.version import LooseVersion
    HAS_CRYPTOGRAPHY = (LooseVersion(cryptography.__version__) >= LooseVersion('1.5'))
    _cryptography_backend = cryptography.hazmat.backends.default_backend()
except ImportError as dummy:
    CRYPTOGRAPHY_IMP_ERR = traceback.format_exc()
    HAS_CRYPTOGRAPHY = False


class Certificate(object):
    '''
    Stores PEM with parsed certificate.
    '''
    def __init__(self, pem, cert):
        if not (pem.endswith('\n') or pem.endswith('\r')):
            pem = pem + '\n'
        self.pem = pem
        self.cert = cert


def is_parent(module, cert, potential_parent):
    '''
    Tests whether the given certificate has been issued by the potential parent certificate.
    '''
    # Check issuer
    if cert.cert.issuer != potential_parent.cert.subject:
        return False
    # Check signature
    public_key = potential_parent.cert.public_key()
    try:
        if isinstance(public_key, cryptography.hazmat.primitives.asymmetric.rsa.RSAPublicKey):
            public_key.verify(
                cert.cert.signature,
                cert.cert.tbs_certificate_bytes,
                cryptography.hazmat.primitives.asymmetric.padding.PKCS1v15(),
                cert.cert.signature_hash_algorithm
            )
        elif isinstance(public_key, cryptography.hazmat.primitives.asymmetric.ec.EllipticCurvePublicKey):
            public_key.verify(
                cert.cert.signature,
                cert.cert.tbs_certificate_bytes,
                cryptography.hazmat.primitives.asymmetric.ec.ECDSA(cert.cert.signature_hash_algorithm),
            )
        else:
            # Unknown public key type
            module.warn('Unknown public key type "{0}"'.format(public_key))
            return False
        return True
    except cryptography.exceptions.InvalidSignature as dummy:
        return False
    except Exception as e:
        module.fail_json(msg='Unknown error on signature validation: {0}'.format(e))


def parse_PEM_list(module, text, source, fail_on_error=True):
    '''
    Parse concatenated PEM certificates. Return list of ``Certificate`` objects.
    '''
    result = []
    lines = text.splitlines(True)
    current = None
    for line in lines:
        if line.strip():
            if line.startswith('-----BEGIN '):
                current = [line]
            elif current is not None:
                current.append(line)
                if line.startswith('-----END '):
                    cert_pem = ''.join(current)
                    current = None
                    # Try to load PEM certificate
                    try:
                        cert = cryptography.x509.load_pem_x509_certificate(to_bytes(cert_pem), _cryptography_backend)
                        result.append(Certificate(cert_pem, cert))
                    except Exception as e:
                        msg = 'Cannot parse certificate #{0} from {1}: {2}'.format(len(result) + 1, source, e)
                        if fail_on_error:
                            module.fail_json(msg=msg)
                        else:
                            module.warn(msg)
    return result


def load_PEM_list(module, path, fail_on_error=True):
    '''
    Load concatenated PEM certificates from file. Return list of ``Certificate`` objects.
    '''
    try:
        with open(path, "rb") as f:
            return parse_PEM_list(module, f.read().decode('utf-8'), source=path, fail_on_error=fail_on_error)
    except Exception as e:
        msg = 'Cannot read certificate file {0}: {1}'.format(path, e)
        if fail_on_error:
            module.fail_json(msg=msg)
        else:
            module.warn(msg)
            return []


class CertificateSet(object):
    '''
    Stores a set of certificates. Allows to search for parent (issuer of a certificate).
    '''

    def __init__(self, module):
        self.module = module
        self.certificates = set()
        self.certificate_by_issuer = dict()

    def _load_file(self, path):
        certs = load_PEM_list(self.module, path, fail_on_error=False)
        for cert in certs:
            self.certificates.add(cert)
            self.certificate_by_issuer[cert.cert.subject] = cert

    def load(self, path):
        '''
        Load lists of PEM certificates from a file or a directory.
        '''
        b_path = to_bytes(path, errors='surrogate_or_strict')
        if os.path.isdir(b_path):
            for directory, dummy, files in os.walk(b_path, followlinks=True):
                for file in files:
                    self._load_file(os.path.join(directory, file))
        else:
            self._load_file(b_path)

    def find_parent(self, cert):
        '''
        Search for the parent (issuer) of a certificate. Return ``None`` if none was found.
        '''
        potential_parent = self.certificate_by_issuer.get(cert.cert.issuer)
        if potential_parent is not None:
            if is_parent(self.module, cert, potential_parent):
                return potential_parent
        return None


def format_cert(cert):
    '''
    Return human readable representation of certificate for error messages.
    '''
    return str(cert.cert)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            input_chain=dict(type='str', required=True),
            root_certificates=dict(type='list', required=True, elements='path'),
            intermediate_certificates=dict(type='list', default=[], elements='path'),
        ),
        supports_check_mode=True,
    )

    if not HAS_CRYPTOGRAPHY:
        module.fail_json(msg=missing_required_lib('cryptography >= 1.5'), exception=CRYPTOGRAPHY_IMP_ERR)

    # Load chain
    chain = parse_PEM_list(module, module.params['input_chain'], source='input chain')
    if len(chain) == 0:
        module.fail_json(msg='Input chain must contain at least one certificate')

    # Check chain
    for i, parent in enumerate(chain):
        if i > 0:
            if not is_parent(module, chain[i - 1], parent):
                module.fail_json(msg=('Cannot verify input chain: certificate #{2}: {3} is not issuer ' +
                                      'of certificate #{0}: {1}').format(i, format_cert(chain[i - 1]), i + 1, format_cert(parent)))

    # Load intermediate certificates
    intermediates = CertificateSet(module)
    for path in module.params['intermediate_certificates']:
        intermediates.load(path)

    # Load root certificates
    roots = CertificateSet(module)
    for path in module.params['root_certificates']:
        roots.load(path)

    # Try to complete chain
    current = chain[-1]
    completed = []
    while current:
        root = roots.find_parent(current)
        if root:
            completed.append(root)
            break
        intermediate = intermediates.find_parent(current)
        if intermediate:
            completed.append(intermediate)
            current = intermediate
        else:
            module.fail_json(msg='Cannot complete chain. Stuck at certificate {0}'.format(format_cert(current)))

    # Return results
    complete_chain = chain + completed
    module.exit_json(
        changed=False,
        root=complete_chain[-1].pem,
        chain=[cert.pem for cert in completed],
        complete_chain=[cert.pem for cert in complete_chain],
    )


if __name__ == "__main__":
    main()
