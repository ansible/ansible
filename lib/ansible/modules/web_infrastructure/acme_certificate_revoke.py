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
   - "Allows to revoke certificates with the ACME protocol, for example
      for certificates obtained by the M(acme_certificate) module. The
      ACME protocol is used by some Certificate Authorities such as
      L(Let's Encrypt,https://letsencrypt.org/)."
   - "Note that exactly one of C(account_key_src), C(account_key_content),
      C(private_key_src) or C(private_key_content) must be specified."
   - "Also note that in general, trying to revoke an already revoked
      certificate will lead to an error. The module tries to detect some
      common error messages (for example, the ones issued by
      L(Let's Encrypt,https://letsencrypt.org/)'s
      L(Boulder,https://github.com/letsencrypt/boulder/) software), but
      this might stop working and probably will not work for other server
      softwares."
extends_documentation_fragment:
  - acme
options:
  certificate:
    description:
      - "Path to the certificate to revoke."
    required: yes
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
      - "I(Warning): the content will be written into a temporary file, which will
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
import tempfile
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


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
            revoke_reason=dict(required=False, type='int'),
        ),
        required_one_of=(
            ['account_key_src', 'account_key_content', 'private_key_src', 'private_key_content'],
        ),
        mutually_exclusive=(
            ['account_key_src', 'account_key_content', 'private_key_src', 'private_key_content'],
        ),
        supports_check_mode=False,
    )

    if not module.params.get('validate_certs'):
        module.warn(warning='Disabling certificate validation for communications with ACME endpoint. ' +
                            'This should only be done for testing against a local ACME server for ' +
                            'development purposes, but *never* for production purposes.')

    try:
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
                            # If certificate file contains other certs appended
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
                module.exit_json(changed=False)
            raise ModuleFailException('Error revoking certificate: {0} {1}'.format(info['status'], result))
        module.exit_json(changed=True)
    except ModuleFailException as e:
        e.do_fail(module)


if __name__ == '__main__':
    main()
