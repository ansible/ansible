#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016 Michael Gruener <michael.gruener@chaosmoon.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: acme_certificate_revoke
author: "Felix Fontein (@felixfontein)"
version_added: "2.7"
short_description: Revoke certificates with the ACME protocol.
description:
   - "Allows to revoke certificates with the ACME protocol. This protocol
      is, for example, used by Let's Encrypt."
   - "Note that exactly one of C(account_key_src), C(account_key_content),
      C(private_key_src) or C(private_key_content) must be specified."
   - "To determine whether the revocation has to be executed, an OCSP
      responder check is done. If this results in an error, use the C(force)
      option to skip that check."
   - "Also note that OCSP responses do not always update immediately after
      revocation, so if you run this module twice for the same certificate,
      it can happen that the second invocation does not notice the
      certificate is already revoked and will try to revoke it another time.
      There is a check which tries to detect this and act like no change
      occured in this case, but it is very dependent on the ACME endpoint
      implementation returning a specific human-readable error message.
      This might stop working in the future and might not work with other
      ACME endpoints than L(Let's Encrypt,https://letsencrypt.org/)'s
      L(Boulder,https://github.com/letsencrypt/boulder/) server."
extends_documentation_fragment:
  - acme
options:
  certificate:
    description:
      - "Path to the certificate to revoke."
    required: yes
  intermediate_certificate:
    description:
      - "Path to the intermediate certificate, i.e. the next certificate in
         the certificate chain. This is used to check revocation status of
         the certificate using OCSP."
      - "Required if C(force) is C(no)."
    required: no
  force:
    description:
      - "Whether to force revocation."
      - "If set to C(no), the certificate will be first checked for being
         revoked by checking the OCSP responder using the URI embedded
         in the certificate. If no URI is embedded or the OCSP responder
         is not available, the module will fail if C(force) is set to
         C(no)."
    type: bool
    required: no
    default: no
  private_key_src:
    description:
      - "Path to the certificate's private key."
      - "Note that exactly one of C(account_key_src), C(account_key_content),
         C(private_key_src) or C(private_key_content) must be specified."
  private_key_content:
    description:
      - "Content of the certificate's private key."
      - "Note that exactly one of C(account_key_src), C(account_key_content),
         C(private_key_src) or C(private_key_content) must be specified."
      - "Warning: the content will be written into a temporary file, which will
         be deleted by Ansible when the module completes. Since this is an
         important private key — it can be used to change the account key,
         or to revoke your certificates without knowing their private keys
         —, this might not be acceptable."
  revoke_reason:
    description:
      - "One of the revocation reasonCodes defined in
         L(https://tools.ietf.org/html/rfc5280#section-5.3.1, Section 5.3.1 of RFC5280)."
      - "Possible values are C(0) (unspecified), C(1) (keyCompromise),
         C(2) (cACompromise), C(3) (affiliationChanged), C(4) (superseded),
         C(5) (cessationOfOperation), C(6) (certificateHold),
         C(8) (removeFromCRL), C(9) (privilegeWithdrawn),
         C(10) (aACompromise)"
'''

EXAMPLES = '''
- name: Revoke certificate with account key
  acme_certificate_revoke:
    account_key_src: /etc/pki/cert/private/account.key
    certificate: /etc/httpd/ssl/sample.com.crt

- name: Revoke certificate with certificate's private key
  acme_certificate_revoke:
    private_key_src: /etc/httpd/ssl/sample.com.key
    certificate: /etc/httpd/ssl/sample.com.crt
'''

RETURN = '''
'''

from ansible.module_utils.acme import (
    ModuleFailException, ACMEAccount, nopad_b64
)

import base64
import os
import re
import tempfile
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def _get_host_from_uri(uri):
    """Extract the hostname from an URI."""
    try:
        from urllib.parse import urlparse
    except ImportError:  # Python 2
        from urlparse import urlparse
    netloc = urlparse(uri).netloc
    i = netloc.find(':')
    return netloc[:i] if i >= 0 else netloc


def _run_openssl(module, args, acceptable_rcs=None):
    """Run OpenSSL command with given arguments."""
    if acceptable_rcs is None:
        acceptable_rcs = [0]
    openssl_bin = module.get_bin_path('openssl', True)
    openssl_cmd = [openssl_bin] + args
    rc, out, error = module.run_command(openssl_cmd, check_rc=True, encoding=None)
    if rc not in acceptable_rcs:
        msg = 'Command "{0}" returned the not acceptable return code {1}. Error output: {2}'
        raise ModuleFailException(msg.format(' '.join(openssl_cmd), rc, error.decode('utf8')))
    return out.decode('utf8')


def is_revoked_ocsp(module, certificate, intermediate_certificate):
    """Check whether the given certificate is revoked by querying OCSP.

    ``certificate`` must be a path pointing to a certificate (PEM format).
    ``intermediate_certificate`` must be a path pointing to the intermediate
    certificate, i.e. to the next certificate in the certificate chain.
    """
    # Determine OCSP URL
    ocsp_uri = _run_openssl(module, ['x509', '-in', certificate, '-noout', '-ocsp_uri']).strip()
    if not ocsp_uri:
        raise ModuleFailException('Cannot determine OCSP URI from certificate!')

    # Determine OpenSSL version
    version_string = _run_openssl(module, ['version'])
    m = re.match(r'^OpenSSL (\d+)\.(\d+)\..*', version_string)
    if not m:
        raise ModuleFailException('Cannot identify OpenSSL version from version string "{0}"!'.format(version_string))
    openssl_version = (int(m[1]), int(m[2]))

    # Get OCSP response. Note that we need to specify the Host header,
    # but that the way to specify this depends on the OpenSSL version.
    if openssl_version < (1, 1):
        host_header = ['Host', _get_host_from_uri(ocsp_uri)]
    else:
        host_header = ['Host=' + _get_host_from_uri(ocsp_uri)]
    # Compose arguments for OpenSSL
    args = ['ocsp', '-no_nonce', '-header']
    args.extend(host_header)
    args.extend(['-issuer', intermediate_certificate, '-cert', certificate, '-url', ocsp_uri, '-VAfile', intermediate_certificate])
    result = _run_openssl(module, args)

    # Interpret result
    m = re.match(r'^.*: ([a-zA-Z]+)(?:\n|\r|$)', result)
    if not m:
        m = re.match(r'^Responder Error: (.*)(?:\n|\r|$)', result)
        if m:
            raise ModuleFailException('OCSP responder error: {0}'.format(m[1]))
        raise ModuleFailException('Cannot parse OpenSSL OCSP output: {0}'.format(result))

    return m[1] == 'revoked'


def main():
    module = AnsibleModule(
        argument_spec=dict(
            account_key_src=dict(type='path', aliases=['account_key']),
            account_key_content=dict(type='str', no_log=True),
            acme_directory=dict(required=False, default='https://acme-staging.api.letsencrypt.org/directory', type='str'),
            acme_version=dict(required=False, default=1, choices=[1, 2], type='int'),
            validate_certs=dict(required=False, default=True, type='bool'),
            private_key_src=dict(type='path'),
            private_key_content=dict(type='str', no_log=True),
            certificate=dict(required=True, type='path'),
            intermediate_certificate=dict(required=False, type='path'),
            revoke_reason=dict(required=False, type='int'),
            force=dict(required=False, type='bool', default=False),
        ),
        required_one_of=(
            ['account_key_src', 'account_key_content', 'private_key_src', 'private_key_content'],
        ),
        mutually_exclusive=(
            ['account_key_src', 'account_key_content', 'private_key_src', 'private_key_content'],
        ),
        required_if=(
            # Make sure that if force is set to False, intermediate_certificate is specified
            ['force', False, ['intermediate_certificate'], True],
        ),
        supports_check_mode=True,
    )

    if not module.params.get('validate_certs'):
        module.warn(warning='Disabling certificate validation for communications with ACME endpoint. ' +
                            'This should only be done for testing against a local ACME server for ' +
                            'development purposes, but *never* for production purposes.')

    try:
        if not module.params['force']:
            # Check whether certificate is already revoked
            if is_revoked_ocsp(module, module.params.get('certificate'), module.params.get('intermediate_certificate')):
                module.exit_json(changed=False)

        # From this point on, we assume the certificate has to be revoked
        if not module.check_mode:
            account = ACMEAccount(module)
            # Load certificate
            certificate_lines = []
            try:
                with open(module.params.get('certificate'), "rt") as f:
                    header_line_count = 0
                    for line in f:
                        if line.startswith('-----'):
                            header_line_count += 1
                            if header_line_count == 2:
                                # If certificate file contains other cerst appended
                                # (like intermediate certificates), ignore these.
                                break
                            continue
                        certificate_lines.append(line.strip())
            except Exception as err:
                raise ModuleFailException("cannot load certificate file: %s" % to_native(err), exception=traceback.format_exc())
            certificate = nopad_b64(base64.b64decode(''.join(certificate_lines)))
            # Construct payload
            payload = {
                'certificate': certificate
            }
            if module.params.get('revoke_reason') is not None:
                payload['reason'] = module.params.get('revoke_reason')
            # Determine endpoint
            if module.params.get('acme_version') == 1:
                endpoint = account.directory['revoke-cert']
                payload['resource'] = 'revoke-cert'
            else:
                endpoint = account.directory['revokeCert']
            # Get hold of private key (if available) and make sure it comes from disk
            private_key = module.params.get('private_key_src')
            if module.params.get('private_key_content') is not None:
                fd, tmpsrc = tempfile.mkstemp()
                module.add_cleanup_file(tmpsrc)  # Ansible will delete the file on exit
                f = os.fdopen(fd, 'wb')
                try:
                    f.write(module.params.get('private_key_content').encode('utf-8'))
                    private_key = tmpsrc
                except Exception as err:
                    try:
                        f.close()
                    except Exception as e:
                        pass
                    raise ModuleFailException("failed to create temporary content file: %s" % to_native(err), exception=traceback.format_exc())
                f.close()
            # Revoke certificate
            if private_key:
                # Step 1: load and parse private key
                error, private_key_data = account.parse_account_key(private_key)
                if error:
                    raise ModuleFailException("error while parsing private key: %s" % error)
                # Step 2: sign revokation request with private key
                jws_header = {
                    "alg": private_key_data['alg'],
                    "jwk": private_key_data['jwk'],
                }
                result, info = account.send_signed_request(endpoint, payload, key=private_key,
                                                           key_data=private_key_data, jws_header=jws_header)
            else:
                # Step 1: get hold of account URI
                changed = account.init_account(
                    [],
                    allow_creation=False,
                    update_contact=False,
                )
                if changed:
                    raise AssertionError('Unwanted account change')
                # Step 2: sign revokation request with account key
                result, info = account.send_signed_request(endpoint, payload)
            if info['status'] != 200:
                if module.params.get('acme_version') == 1:
                    error_type = 'urn:acme:error:malformed'
                else:
                    error_type = 'urn:ietf:params:acme:error:malformed'
                if result.get('type') == error_type and result.get('detail') == 'Certificate already revoked':
                    # Fallback: boulder returns this in case the certificate was already revoked.
                    if not module.params['force']:
                        module.exit_json(changed=False)
                    raise ModuleFailException('Certificate has already been revoked.')
                raise ModuleFailException('Error revoking certificate: {0} {1}'.format(info['status'], result))
        module.exit_json(changed=True)
    except ModuleFailException as e:
        e.do_fail(module)


if __name__ == '__main__':
    main()
