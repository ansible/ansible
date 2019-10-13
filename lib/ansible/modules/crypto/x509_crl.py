#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: x509_crl
version_added: "2.10"
short_description: Generate Certificate Revocation Lists (CRLs)
description:
    - This module allows one to (re)generate or update Certificate Revocation Lists (CRLs).
    - Certificates on the revocation list can be either specified via serial number and (optionally) their issuer,
      or as a path to a certificate file in PEM format.
requirements:
    - cryptography >= 1.2
author:
    - Felix Fontein (@felixfontein)
options:
    state:
        description:
            - Whether the CRL file should exist or not, taking action if the state is different from what is stated.
        type: str
        default: present
        choices: [ absent, present ]

    mode:
        description:
            - Defines how to process entries of existing CRLs.
            - If set to C(generate), makes sure that the CRL has the exact set of revoked certificates
              as specified in I(revoked_certificates).
            - If set to C(update), makes sure that the CRL contains the revoked certificates from
              I(revoked_certificates), but can also contain other revoked certificates. If the CRL file
              already exists, all entries from the existing CRL will also be included in the new CRL.
        type: str
        default: generate
        choices: [ generate, update ]

    force:
        description:
            - Should the CRL be forced to be regenerated.
        type: bool
        default: no

    backup:
        description:
            - Create a backup file including a timestamp so you can get the original
              CRL back if you overwrote it with a new one by accident.
        type: bool
        default: no

    path:
        description:
            - Remote absolute path where the generated CRL file should be created or is already located.
        type: path
        required: yes

    privatekey_path:
        description:
            - Path to the CA's private key to use when signing the CRL.
        type: path
        required: yes

    privatekey_passphrase:
        description:
            - The passphrase for the I(privatekey_path).
            - This is required if the private key is password protected.
        type: str

    issuer:
        description:
            - Key/value pairs that will be present in the issuer name field of the CRL.
            - If you need to specify more than one value with the same key, use a list as value.
        type: dict
        required: yes

    last_update:
        description:
            - The point in time from which this CRL can be trusted.
            - Time can be specified either as relative time or as absolute timestamp.
            - Time will always be interpreted as UTC.
            - Valid format is C([+-]timespec | ASN.1 TIME) where timespec can be an integer
              + C([w | d | h | m | s]) (e.g. C(+32w1d2h).
            - Note that if using relative time this module is NOT idempotent.
        type: str
        default: "+0s"

    next_update:
        description:
            - The point in time from which a new CRL will be issued and the client has to check for it.
            - Time can be specified either as relative time or as absolute timestamp.
            - Time will always be interpreted as UTC.
            - Valid format is C([+-]timespec | ASN.1 TIME) where timespec can be an integer
              + C([w | d | h | m | s]) (e.g. C(+32w1d2h).
            - Note that if using relative time this module is NOT idempotent.
        type: str
        required: yes

    digest:
        description:
            - Digest algorithm to be used when signing the CRL.
        type: str
        default: sha256

    revoked_certificates:
        description:
            - List of certificates to be revoked.
        type: list
        elements: dict
        required: yes
        suboptions:
            path:
                description:
                    - Serial number of the certificate.
                    - If specified, I(serial_number) and I(issuer) must not be specified.
                type: path
            serial_number:
                description:
                    - Serial number of the certificate.
                    - Must be specified if I(path) is not specified.
                type: int
            revocation_date:
                description:
                    - The point in time the certificate was revoked.
                    - Time can be specified either as relative time or as absolute timestamp.
                    - Time will always be interpreted as UTC.
                    - Valid format is C([+-]timespec | ASN.1 TIME) where timespec can be an integer
                      + C([w | d | h | m | s]) (e.g. C(+32w1d2h).
                    - Note that if using relative time this module is NOT idempotent.
                type: str
                required: yes
            issuer:
                description:
                    - The certificate's issuer.
                    - "Example: C(DNS:ca.example.org)"
                    - Can only be specified if I(path) is not specified.
                type: list
                elements: str
            issuer_critical:
                description:
                    - Whether the certificate issuer extension should be critical.
                type: bool
                default: no
            reason:
                description:
                    - The value for the revocation reason extension.
                type: str
                choices:
                    - unspecified
                    - key_compromise
                    - ca_compromise
                    - affiliation_changed
                    - superseded
                    - cessation_of_operation
                    - certificate_hold
                    - privilege_withdrawn
                    - aa_compromise
                    - remove_from_crl
            reason_critical:
                description:
                    - Whether the revocation reason extension should be critical.
                type: bool
                default: no
            invalidity_date:
                description:
                    - The point in time it was known/suspected that the private key was compromised
                      or that the certificate otherwise became invalid.
                    - Time can be specified either as relative time or as absolute timestamp.
                    - Time will always be interpreted as UTC.
                    - Valid format is C([+-]timespec | ASN.1 TIME) where timespec can be an integer
                      + C([w | d | h | m | s]) (e.g. C(+32w1d2h).
                    - Note that if using relative time this module is NOT idempotent.
                type: str
            invalidity_date_critical:
                description:
                    - Whether the invalidity date extension should be critical.
                type: bool
                default: no

extends_documentation_fragment:
    - files

notes:
    - All ASN.1 TIME values should be specified following the YYYYMMDDHHMMSSZ pattern.
    - Date specified should be UTC. Minutes and seconds are mandatory.
'''

EXAMPLES = r'''
- name: Generate a CRL
  x509_crl:
    path: /etc/ssl/my-ca.crl
    privatekey_path: /etc/ssl/private/my-ca.pem
    issuer:
      CN: My CA
    last_update: "+0s"
    next_update: "+7d"
    revoked_certificates:
      - serial_number: 1234
        revocation_date: 20190331202428Z
        issuer:
          CN: My CA
      - serial_number: 2345
        revocation_date: 20191013152910Z
        reason: affiliation_changed
        invalidity_date: 20191001000000Z
      - path: /etc/ssl/crt/revoked-cert.pem
        revocation_date: 20191010010203Z
'''

RETURN = r'''
filename:
    description: Path to the generated CRL
    returned: changed or success
    type: str
    sample: /path/to/my-ca.crl
backup_file:
    description: Name of backup file created.
    returned: changed and if I(backup) is C(yes)
    type: str
    sample: /path/to/my-ca.crl.2019-03-09@11:22~
privatekey:
    description: Path to the private CA key
    returned: changed or success
    type: str
    sample: /path/to/my-ca.pem
issuer:
    description:
        - The CRL's issuer.
        - Note that for repeated values, only the last one will be returned.
    returned: success
    type: dict
    sample: '{"organizationName": "Ansible", "commonName": "ca.example.com"}'
issuer_ordered:
    description: The CRL's issuer as an ordered list of tuples.
    returned: success
    type: list
    elements: list
    sample: '[["organizationName", "Ansible"], ["commonName": "ca.example.com"]]'
last_update:
    description: The point in time from which this CRL can be trusted as ASN.1 TIME.
    returned: success
    type: str
    sample: 20190413202428Z
next_update:
    description: The point in time from which a new CRL will be issued and the client has to check for it as ASN.1 TIME.
    returned: success
    type: str
    sample: 20190413202428Z
digest:
    description: The signature algorithm used to sign the CRL.
    returned: success
    type: str
    sample: sha256WithRSAEncryption
revoked_certificates:
    description: List of certificates to be revoked.
    returned: success
    type: list
    elements: dict
    contains:
        serial_number:
            description: Serial number of the certificate.
            type: int
            sample: 1234
        revocation_date:
            description: The point in time the certificate was revoked as ASN.1 TIME.
            type: str
            sample: 20190413202428Z
        issuer:
            description: The certificate's issuer.
            type: list
            elements: str
            sample: '["DNS:ca.example.org"]'
        issuer_critical:
            description: Whether the certificate issuer extension is critical.
            type: bool
            sample: no
        reason:
            description:
                - The value for the revocation reason extension.
                - One of C(unspecified), C(key_compromise), C(ca_compromise), C(affiliation_changed), C(superseded),
                  C(cessation_of_operation), C(certificate_hold), C(privilege_withdrawn), C(aa_compromise), and
                  C(remove_from_crl).
            type: str
            sample: key_compromise
        reason_critical:
            description: Whether the revocation reason extension is critical.
            type: bool
            sample: no
        invalidity_date:
            description: |
                The point in time it was known/suspected that the private key was compromised
                or that the certificate otherwise became invalid as ASN.1 TIME.
            type: str
            sample: 20190413202428Z
        invalidity_date_critical:
            description: Whether the invalidity date extension is critical.
            type: bool
            sample: no

'''


import datetime
import os
import traceback
from distutils.version import LooseVersion

from ansible.module_utils import crypto as crypto_utils
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.basic import AnsibleModule, missing_required_lib

MINIMAL_CRYPTOGRAPHY_VERSION = '1.2'

CRYPTOGRAPHY_IMP_ERR = None
try:
    import cryptography
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.serialization import Encoding
    from cryptography.x509 import (
        CertificateRevocationListBuilder,
        RevokedCertificateBuilder,
        NameAttribute,
        Name,
        ReasonFlags,
    )
    CRYPTOGRAPHY_VERSION = LooseVersion(cryptography.__version__)

    REASON_MAP = {
        'unspecified': ReasonFlags.unspecified,
        'key_compromise': ReasonFlags.key_compromise,
        'ca_compromise': ReasonFlags.ca_compromise,
        'affiliation_changed': ReasonFlags.affiliation_changed,
        'superseded': ReasonFlags.superseded,
        'cessation_of_operation': ReasonFlags.cessation_of_operation,
        'certificate_hold': ReasonFlags.certificate_hold,
        'privilege_withdrawn': ReasonFlags.privilege_withdrawn,
        'aa_compromise': ReasonFlags.aa_compromise,
        'remove_from_crl': ReasonFlags.remove_from_crl,
    }
    REASON_MAP_INVERSE = dict()
    for k, v in REASON_MAP.items():
        REASON_MAP_INVERSE[k] = v
except ImportError:
    CRYPTOGRAPHY_IMP_ERR = traceback.format_exc()
    CRYPTOGRAPHY_FOUND = False
else:
    CRYPTOGRAPHY_FOUND = True


TIMESTAMP_FORMAT = "%Y%m%d%H%M%SZ"


class CRLError(crypto_utils.OpenSSLObjectError):
    pass


class CRL(crypto_utils.OpenSSLObject):

    def get_relative_time_option(self, input_string, input_name):
        """Return an ASN1 formatted string if a relative timespec
           or an ASN1 formatted string is provided."""
        result = to_native(input_string)
        if result is None:
            raise CRLError(
                'The timespec "%s" for %s is not valid' %
                input_string, input_name)
        if result.startswith("+") or result.startswith("-"):
            return crypto_utils.convert_relative_to_datetime(result)
        for date_fmt in ['%Y%m%d%H%M%SZ', '%Y%m%d%H%MZ', '%Y%m%d%H%M%S%z', '%Y%m%d%H%M%z']:
            try:
                return datetime.datetime.strptime(result, date_fmt)
            except ValueError:
                pass

        raise CRLError(
            'The time spec "%s" for %s is invalid' %
            (input_string, input_name)
        )

    def __init__(self, module):
        super(CRL, self).__init__(
            module.params['path'],
            module.params['state'],
            module.params['force'],
            module.check_mode
        )

        self.update = module.params['mode'] == 'update'

        self.privatekey_path = module.params['privatekey_path']
        self.privatekey_passphrase = module.params['privatekey_passphrase']

        self.issuer = crypto_utils.parse_name_field(module.params['issuer'])
        self.issuer = [(entry[0], entry[1]) for entry in self.issuer if entry[1]]

        self.last_update = self.get_relative_time_option(module.params['last_update'], 'last_update')
        self.next_update = self.get_relative_time_option(module.params['next_update'], 'next_update')

        self.digest = crypto_utils.select_message_digest(module.params['digest'])
        if self.digest is None:
            raise CRLError('The digest "{0}" is not supported'.format(module.params['digest']))

        self.revoked_certificates = []
        for i, rc in enumerate(module.params['revoked_certificates']):
            result = {
                'serial_number': None,
                'revocation_date': None,
                'issuer': None,
                'issuer_critical': False,
                'reason': None,
                'reason_critical': False,
                'invalidity_date': None,
                'invalidity_date_critical': False,
            }
            path_prefix = 'revoked_certificates[{0}].'.format(i)
            if rc['path'] is not None:
                # Load certificate from file
                if rc['serial_number'] is not None:
                    module.fail_json(
                        msg='{0}serial_number must not be specified if {0}path is specified'.format(path_prefix)
                    )
                if rc['issuer'] is not None:
                    module.fail_json(
                        msg='{0}issuer must not be specified if {0}path is specified'.format(path_prefix)
                    )
                try:
                    cert = crypto_utils.load_certificate(rc['path'], backend='cryptography')
                    try:
                        result['serial_number'] = cert.serial_number
                    except AttributeError:
                        # The property was called "serial" before cryptography 1.4
                        result['serial_number'] = cert.serial
                    try:
                        ext = cert.extensions.get_extension_for_class(x509.AuthorityKeyIdentifier)
                        if ext.value.authority_cert_issuer is not None:
                            result['issuer'] = list(ext.value.authority_cert_issuer)
                            result['issuer_critical'] = rc['issuer_critical']
                    except x509.ExtensionNotFound:
                        pass
                except Exception as e:
                    module.fail_json(
                        msg='Cannot read certificate "{1}" from {0}path: {2}'.format(path_prefix, rc['path'], to_native(e))
                    )
            else:
                # Specify serial_number (and potentially issuer) directly
                if rc['serial_number'] is None:
                    module.fail_json(
                        msg='{0}serial_number must be specified if {0}path is not specified'.format(path_prefix)
                    )
                result['serial_number'] = rc['serial_number']
                if rc['issuer']:
                    result['issuer'] = [crypto_utils.cryptography_get_name(issuer) for issuer in rc['issuer']]
                    result['issuer_critical'] = rc['issuer_critical']
            # All other options
            result['revocation_date'] = self.get_relative_time_option(
                rc['revocation_date'],
                path_prefix + 'revocation_date'
            )
            if rc['reason']:
                result['reason'] = REASON_MAP[rc['reason']]
                result['reason_critical'] = rc['reason_critical']
            if rc['invalidity_date']:
                result['invalidity_date'] = self.get_relative_time_option(
                    rc['invalidity_date'],
                    path_prefix + 'invalidity_date'
                )
                result['invalidity_date_critical'] = rc['invalidity_date_critical']
            self.revoked_certificates.append(result)

        self.module = module

        self.backup = module.params['backup']
        self.backup_file = None

        try:
            self.privatekey = crypto_utils.load_privatekey(
                self.privatekey_path,
                self.privatekey_passphrase,
                backend='cryptography'
            )
        except crypto_utils.OpenSSLBadPassphraseError as exc:
            raise CRLError(exc)

        self.crl = None
        try:
            with open(self.path, 'rb') as f:
                data = f.read()
            self.crl = x509.load_pem_x509_crl(data, default_backend())
        except Exception as dummy:
            pass

    def remove(self):
        if self.backup:
            self.backup_file = self.module.backup_local(self.path)
        super(CRL, self).remove(self.module)

    def _compress_entry(self, entry):
        return (
            entry['serial_number'],
            entry['revocation_date'],
            tuple(entry['issuer']) if entry['issuer'] is not None else None,
            entry['issuer_critical'],
            entry['reason'],
            entry['reason_critical'],
            entry['invalidity_date'],
            entry['invalidity_date_critical'],
        )

    def _decode_revoked(self, cert):
        result = {
            'serial_number': cert.serial_number,
            'revocation_date': cert.revocation_date,
            'issuer': None,
            'issuer_critical': False,
            'reason': None,
            'reason_critical': False,
            'invalidity_date': None,
            'invalidity_date_critical': False,
        }
        try:
            ext = cert.extensions.get_extension_for_class(x509.CertificateIssuer)
            result['issuer'] = list(ext.value)
            result['issuer_critical'] = ext.critical
        except x509.ExtensionNotFound:
            pass
        try:
            ext = cert.extensions.get_extension_for_class(x509.CRLReason)
            result['reason'] = ext.value.reason
            result['reason_critical'] = ext.critical
        except x509.ExtensionNotFound:
            pass
        try:
            ext = cert.extensions.get_extension_for_class(x509.InvalidityDate)
            result['invalidity_date'] = ext.value.invalidity_date
            result['invalidity_date_critical'] = ext.critical
        except x509.ExtensionNotFound:
            pass
        return result

    def check(self, perms_required=True):
        """Ensure the resource is in its desired state."""

        state_and_perms = super(CRL, self).check(self.module, perms_required)

        if not state_and_perms:
            return False

        if self.crl is None:
            return False

        if self.last_update != self.crl.last_update:
            return False
        if self.next_update != self.crl.next_update:
            return False
        if self.digest.name != self.crl.signature_hash_algorithm.name:
            return False

        want_issuer = [(crypto_utils.cryptography_name_to_oid(entry[0]), entry[1]) for entry in self.issuer]
        if want_issuer != [(sub.oid, sub.value) for sub in self.crl.issuer]:
            return False

        entries = [self._decode_revoked(cert) for cert in self.crl]
        if self.update:
            # We don't use a set so that duplicate entries are treated correctly
            old_entries = [self._compress_entry(self._decode_revoked(entry)) for entry in self.crl]
            for entry in self.revoked_certificates:
                compressed_entry = self._compress_entry(entry)
                try:
                    old_entries.remove(compressed_entry)
                except ValueError:
                    return False
        else:
            if entries != self.revoked_certificates:
                return False

        return True

    def _generate_crl(self):
        backend = default_backend()
        crl = CertificateRevocationListBuilder()

        try:
            crl = crl.issuer_name(Name([
                NameAttribute(crypto_utils.cryptography_name_to_oid(entry[0]), to_text(entry[1]))
                for entry in self.issuer
            ]))
        except ValueError as e:
            raise CRLError(e)

        crl = crl.last_update(self.last_update)
        crl = crl.next_update(self.next_update)

        if self.update and self.crl:
            new_entries = set([self._compress_entry(entry) for entry in self.revoked_certificates])
            for entry in self.crl:
                decoded_entry = self._compress_entry(self._decode_revoked(entry))
                if decoded_entry not in new_entries:
                    crl = crl.add_revoked_certificate(entry)
        for entry in self.revoked_certificates:
            revoked_cert = RevokedCertificateBuilder()
            revoked_cert = revoked_cert.serial_number(entry['serial_number'])
            revoked_cert = revoked_cert.revocation_date(entry['revocation_date'])
            if entry['issuer'] is not None:
                revoked_cert = revoked_cert.add_extension(
                    x509.CertificateIssuer([
                        crypto_utils.cryptography_get_name(name) for name in self.entry['issuer']
                    ]),
                    entry['issuer_critical']
                )
            if entry['reason'] is not None:
                revoked_cert = revoked_cert.add_extension(
                    x509.CRLReason(entry['reason']),
                    entry['reason_critical']
                )
            if entry['invalidity_date'] is not None:
                revoked_cert = revoked_cert.add_extension(
                    x509.InvalidityDate(entry['invalidity_date']),
                    entry['invalidity_date_critical']
                )
            crl = crl.add_revoked_certificate(revoked_cert.build(backend))

        self.crl = crl.sign(self.privatekey, self.digest, backend=backend)
        return self.crl.public_bytes(Encoding.PEM)

    def generate(self):
        if not self.check(perms_required=False) or self.force:
            result = self._generate_crl()
            if self.backup:
                self.backup_file = self.module.backup_local(self.path)
            crypto_utils.write_file(self.module, result)
            self.changed = True

        file_args = self.module.load_file_common_arguments(self.module.params)
        if self.module.set_fs_attributes_if_different(file_args, False):
            self.changed = True

    def _dump_revoked(self, entry):
        return {
            'serial_number': entry['serial_number'],
            'revocation_date': entry['revocation_date'].strftime(TIMESTAMP_FORMAT),
            'issuer':
                [crypto_utils.cryptography_decode_name(issuer) for issuer in entry['issuer']]
                if entry['issuer'] is not None else None,
            'issuer_critical': entry['issuer_critical'],
            'reason': REASON_MAP_INVERSE.get(entry['reason']) if entry['reason'] is not None else None,
            'reason_critical': entry['reason_critical'],
            'invalidity_date':
                entry['invalidity_date'].strftime(TIMESTAMP_FORMAT)
                if entry['invalidity_date'] is not None else None,
            'invalidity_date_critical': entry['invalidity_date_critical'],
        }

    def dump(self, check_mode=False):
        result = {
            'changed': self.changed,
            'filename': self.path,
            'privatekey': self.privatekey_path,
            'last_update': None,
            'next_update': None,
            'digest': None,
            'issuer_ordered': None,
            'issuer': None,
            'revoked_certificates': [],
        }
        if self.backup_file:
            result['backup_file'] = self.backup_file

        if check_mode:
            result['last_update'] = self.last_update.strftime(TIMESTAMP_FORMAT)
            result['next_update'] = self.next_update.strftime(TIMESTAMP_FORMAT)
            # result['digest'] = crypto_utils.cryptography_oid_to_name(self.crl.signature_algorithm_oid)
            result['digest'] = self.module.params['digest']
            result['issuer_ordered'] = self.issuer
            result['issuer'] = {}
            for k, v in self.issuer:
                result['issuer'][k] = v
            result['revoked_certificates'] = []
            for entry in self.revoked_certificates:
                result['revoked_certificates'].append(self._dump_revoked(entry))
        elif self.crl:
            result['last_update'] = self.crl.last_update.strftime(TIMESTAMP_FORMAT)
            result['next_update'] = self.crl.next_update.strftime(TIMESTAMP_FORMAT)
            result['digest'] = crypto_utils.cryptography_oid_to_name(self.crl.signature_algorithm_oid)
            issuer = []
            for attribute in self.crl.issuer:
                issuer.append([crypto_utils.cryptography_oid_to_name(attribute.oid), attribute.value])
            result['issuer_ordered'] = issuer
            result['issuer'] = {}
            for k, v in issuer:
                result['issuer'][k] = v
            result['revoked_certificates'] = []
            for cert in self.crl:
                entry = self._decode_revoked(cert)
                result['revoked_certificates'].append(self._dump_revoked(entry))

        return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            mode=dict(type='str', default='generate', choices=['generate', 'update']),
            force=dict(type='bool', default=False),
            backup=dict(type='bool', default=False),
            path=dict(type='path', required=True),
            privatekey_path=dict(type='path', required=True),
            privatekey_passphrase=dict(type='str', no_log=True),
            issuer=dict(type='dict', required=True),
            last_update=dict(type='str', default='+0s'),
            next_update=dict(type='str', required=True),
            digest=dict(type='str', default='sha256'),
            revoked_certificates=dict(
                type='list',
                elements='dict',
                required=True,
                options=dict(
                    path=dict(type='path'),
                    serial_number=dict(type='int'),
                    revocation_date=dict(type='str', required=True),
                    issuer=dict(type='list'),
                    issuer_critical=dict(type='bool', default=False),
                    reason=dict(
                        type='str',
                        choices=[
                            'unspecified', 'key_compromise', 'ca_compromise', 'affiliation_changed',
                            'superseded', 'cessation_of_operation', 'certificate_hold',
                            'privilege_withdrawn', 'aa_compromise', 'remove_from_crl'
                        ]
                    ),
                    reason_critical=dict(type='bool', default=False),
                    invalidity_date=dict(type='str'),
                    invalidity_date_critical=dict(type='bool', default=False),
                ),
            ),
        ),
        supports_check_mode=True,
        add_file_common_args=True,
    )

    if not CRYPTOGRAPHY_FOUND:
        module.fail_json(msg=missing_required_lib('cryptography >= {0}'.format(MINIMAL_CRYPTOGRAPHY_VERSION)),
                         exception=CRYPTOGRAPHY_IMP_ERR)

    try:
        crl = CRL(module)

        if module.params['state'] == 'present':
            if module.check_mode:
                result = crl.dump(check_mode=True)
                result['changed'] = module.params['force'] or not crl.check()
                module.exit_json(**result)

            crl.generate()
        else:
            if module.check_mode:
                result = crl.dump(check_mode=True)
                result['changed'] = os.path.exists(module.params['path'])
                module.exit_json(**result)

            crl.remove()

        result = crl.dump()
        module.exit_json(**result)
    except crypto_utils.OpenSSLObjectError as exc:
        module.fail_json(msg=to_native(exc))


if __name__ == "__main__":
    main()
