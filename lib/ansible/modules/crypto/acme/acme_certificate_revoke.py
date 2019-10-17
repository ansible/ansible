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
short_description: Revoke certificates with the ACME protocol
description:
   - "Allows to revoke certificates issued by a CA supporting the
      L(ACME protocol,https://tools.ietf.org/html/rfc8555),
      such as L(Let's Encrypt,https://letsencrypt.org/)."
notes:
   - "Exactly one of C(account_key_src), C(account_key_content),
      C(private_key_src) or C(private_key_content) must be specified."
   - "Trying to revoke an already revoked certificate
      should result in an unchanged status, even if the revocation reason
      was different than the one specified here. Also, depending on the
      server, it can happen that some other error is returned if the
      certificate has already been revoked."
seealso:
  - name: The Let's Encrypt documentation
    description: Documentation for the Let's Encrypt Certification Authority.
                 Provides useful information for example on rate limits.
    link: https://letsencrypt.org/docs/
  - name: Automatic Certificate Management Environment (ACME)
    description: The specification of the ACME protocol (RFC 8555).
    link: https://tools.ietf.org/html/rfc8555
  - module: acme_inspect
    description: Allows to debug problems.
extends_documentation_fragment:
  - acme
options:
  certificate:
    description:
      - "Path to the certificate to revoke."
    type: path
    required: yes
  account_key_src:
    description:
      - "Path to a file containing the ACME account RSA or Elliptic Curve
         key."
      - "RSA keys can be created with C(openssl rsa ...). Elliptic curve keys can
         be created with C(openssl ecparam -genkey ...). Any other tool creating
         private keys in PEM format can be used as well."
      - "Mutually exclusive with C(account_key_content)."
      - "Required if C(account_key_content) is not used."
    type: path
  account_key_content:
    description:
      - "Content of the ACME account RSA or Elliptic Curve key."
      - "Note that exactly one of C(account_key_src), C(account_key_content),
         C(private_key_src) or C(private_key_content) must be specified."
      - "I(Warning): the content will be written into a temporary file, which will
         be deleted by Ansible when the module completes. Since this is an
         important private key — it can be used to change the account key,
         or to revoke your certificates without knowing their private keys
         —, this might not be acceptable."
      - "In case C(cryptography) is used, the content is not written into a
         temporary file. It can still happen that it is written to disk by
         Ansible in the process of moving the module with its argument to
         the node where it is executed."
    type: str
  private_key_src:
    description:
      - "Path to the certificate's private key."
      - "Note that exactly one of C(account_key_src), C(account_key_content),
         C(private_key_src) or C(private_key_content) must be specified."
    type: path
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
      - "In case C(cryptography) is used, the content is not written into a
         temporary file. It can still happen that it is written to disk by
         Ansible in the process of moving the module with its argument to
         the node where it is executed."
    type: str
  revoke_reason:
    description:
      - "One of the revocation reasonCodes defined in
         L(https://tools.ietf.org/html/rfc5280#section-5.3.1, Section 5.3.1 of RFC5280)."
      - "Possible values are C(0) (unspecified), C(1) (keyCompromise),
         C(2) (cACompromise), C(3) (affiliationChanged), C(4) (superseded),
         C(5) (cessationOfOperation), C(6) (certificateHold),
         C(8) (removeFromCRL), C(9) (privilegeWithdrawn),
         C(10) (aACompromise)"
    type: int
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
    ModuleFailException,
    ACMEAccount,
    nopad_b64,
    pem_to_der,
    handle_standard_module_arguments,
    get_default_argspec,
)

from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = get_default_argspec()
    argument_spec.update(dict(
        private_key_src=dict(type='path'),
        private_key_content=dict(type='str', no_log=True),
        certificate=dict(type='path', required=True),
        revoke_reason=dict(type='int'),
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=(
            ['account_key_src', 'account_key_content', 'private_key_src', 'private_key_content'],
        ),
        mutually_exclusive=(
            ['account_key_src', 'account_key_content', 'private_key_src', 'private_key_content'],
        ),
        supports_check_mode=False,
    )
    handle_standard_module_arguments(module)

    try:
        account = ACMEAccount(module)
        # Load certificate
        certificate = pem_to_der(module.params.get('certificate'))
        certificate = nopad_b64(certificate)
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
        private_key_content = module.params.get('private_key_content')
        # Revoke certificate
        if private_key or private_key_content:
            # Step 1: load and parse private key
            error, private_key_data = account.parse_key(private_key, private_key_content)
            if error:
                raise ModuleFailException("error while parsing private key: %s" % error)
            # Step 2: sign revokation request with private key
            jws_header = {
                "alg": private_key_data['alg'],
                "jwk": private_key_data['jwk'],
            }
            result, info = account.send_signed_request(endpoint, payload, key_data=private_key_data, jws_header=jws_header)
        else:
            # Step 1: get hold of account URI
            created, account_data = account.setup_account(allow_creation=False)
            if created:
                raise AssertionError('Unwanted account creation')
            if account_data is None:
                raise ModuleFailException(msg='Account does not exist or is deactivated.')
            # Step 2: sign revokation request with account key
            result, info = account.send_signed_request(endpoint, payload)
        if info['status'] != 200:
            already_revoked = False
            # Standardized error from draft 14 on (https://tools.ietf.org/html/rfc8555#section-7.6)
            if result.get('type') == 'urn:ietf:params:acme:error:alreadyRevoked':
                already_revoked = True
            else:
                # Hack for Boulder errors
                if module.params.get('acme_version') == 1:
                    error_type = 'urn:acme:error:malformed'
                else:
                    error_type = 'urn:ietf:params:acme:error:malformed'
                if result.get('type') == error_type and result.get('detail') == 'Certificate already revoked':
                    # Fallback: boulder returns this in case the certificate was already revoked.
                    already_revoked = True
            # If we know the certificate was already revoked, we don't fail,
            # but successfully terminate while indicating no change
            if already_revoked:
                module.exit_json(changed=False)
            raise ModuleFailException('Error revoking certificate: {0} {1}'.format(info['status'], result))
        module.exit_json(changed=True)
    except ModuleFailException as e:
        e.do_fail(module)


if __name__ == '__main__':
    main()
