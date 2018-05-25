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
module: acme_certificate
author: "Michael Gruener (@mgruener)"
version_added: "2.2"
short_description: Create SSL certificates with an ACME protocol endpoint
description:
   - "Create and renew SSL certificates with a CA supporting the ACME protocol,
      such as Let's Encrypt (U(https://letsencrypt.org)). For details see
      U(https://letsencrypt.org). The current implementation supports the
      C(http-01) and C(dns-01) challenges."
   - "To use this module, it has to be executed twice. Either as two
      different tasks in the same run or during two runs. Note that the output
      of the first run needs to be recorded and passed to the second run as the
      module argument C(data)."
   - "Between these two tasks you have to fulfill the required steps for the
      chosen challenge by whatever means necessary. For C(http-01) that means
      creating the necessary challenge file on the destination webserver. For
      C(dns-01) the necessary dns record has to be created.
      It is I(not) the responsibility of this module to perform these steps."
   - "For details on how to fulfill these challenges, you might have to read through
      U(https://tools.ietf.org/html/draft-ietf-acme-acme-12#section-8).
      Also, consider the examples provided for this module."
   - "Although the defaults are chosen so that the module can be used with
      the Let's Encrypt CA, the module can be used with any service using the ACME
      v1 or v2 protocol."
   - "At least one of C(dest) and C(fullchain_dest) must be specified."
   - "Note: this module was called C(letsencrypt) before Ansible 2.6. The usage
      did not change."
extends_documentation_fragment:
  - acme
options:
  account_email:
    description:
      - "The email address associated with this account."
      - "It will be used for certificate expiration warnings."
  agreement:
    description:
      - "URI to a terms of service document you agree to when using the
         ACME v1 service at C(acme_directory)."
      - Default is latest gathered from C(acme_directory) URL.
      - This option will only be used when C(acme_version) is 1.
  terms_agreed:
    description:
      - "Boolean indicating whether you agree to the terms of service document."
      - "ACME servers can require this to be true."
      - This option will only be used when C(acme_version) is not 1.
    type: bool
    default: 'no'
    version_added: "2.5"
  modify_account:
    description:
      - "Boolean indicating whether the module should create the account if
         necessary, and update its contact data."
      - "Set to C(no) if you want to use C(acme_account) to manage your
         account instead, and to avoid accidental creation of a new account
         using an old key if you changed the account key with C(acme_account)."
      - "If set to C(no), C(terms_agreed) and C(account_email) are ignored."
    type: bool
    default: 'yes'
    version_added: "2.6"
  challenge:
    description: The challenge to be performed.
    choices: [ 'http-01', 'dns-01']
    default: 'http-01'
  csr:
    description:
      - "File containing the CSR for the new certificate."
      - "Can be created with C(openssl req ...)."
      - "The CSR may contain multiple Subject Alternate Names, but each one
         will lead to an individual challenge that must be fulfilled for the
         CSR to be signed."
      - "I(Note): the private key used to create the CSR I(must not) be the the
         account key. This is a bad idea from a security point of view, and
         the CA should not accept the CSR. Let's Encrypt will return an error
         in this case."
    required: true
    aliases: ['src']
  data:
    description:
      - "The data to validate ongoing challenges. This must be specified for
         the second run of the module only."
      - "The value that must be used here will be provided by a previous use
         of this module. See the examples for more details."
      - "I(Note): the C(data) option was marked as C(no_log) up to
         Ansible 2.5. From Ansible 2.6 on, it is no longer marked this way
         as it causes error messages to be come unusable, and C(data) does
         not contain any information which can be used without having
         access to the account key or which are not public anyway."
  dest:
    description:
      - "The destination file for the certificate."
      - "Required if C(fullchain_dest) is not specified."
    aliases: ['cert']
  fullchain_dest:
    description:
      - "The destination file for the full chain (i.e. certificate followed
         by chain of intermediate certificates)."
      - "Required if C(dest) is not specified."
    version_added: 2.5
    aliases: ['fullchain']
  chain_dest:
    description:
      - If specified, the intermediate certificate will be written to this file.
    aliases: ['chain']
    version_added: 2.5
  remaining_days:
    description:
      - "The number of days the certificate must have left being valid.
         If C(cert_days < remaining_days), then it will be renewed.
         If the certificate is not renewed, module return values will not
         include C(challenge_data)."
    default: 10
  deactivate_authzs:
    description:
      - "Deactivate authentication objects (authz) after issuing a certificate,
         or when issuing the certificate failed."
      - "Authentication objects are bound to an account key and remain valid
         for a certain amount of time, and can be used to issue certificates
         without having to re-authenticate the domain. This can be a security
         concern."
    type: bool
    default: 'no'
    version_added: 2.6
  force:
    description:
      - Enforces the execution of the challenge and validation, even if an
        existing certificate is still valid.
      - This is especially helpful when having an updated CSR e.g. with
        additional domains for which a new certificate is desired.
    type: bool
    default: 'no'
    version_added: 2.6
'''

EXAMPLES = R'''
### Example with HTTP challenge ###

- name: Create a challenge for sample.com using a account key from a variable.
  acme_certificate:
    account_key_content: "{{ account_private_key }}"
    csr: /etc/pki/cert/csr/sample.com.csr
    dest: /etc/httpd/ssl/sample.com.crt
  register: sample_com_challenge

# Alternative first step:
- name: Create a challenge for sample.com using a account key from hashi vault.
  acme_certificate:
    account_key_content: "{{ lookup('hashi_vault', 'secret=secret/account_private_key:value') }}"
    csr: /etc/pki/cert/csr/sample.com.csr
    fullchain_dest: /etc/httpd/ssl/sample.com-fullchain.crt
  register: sample_com_challenge

# Alternative first step:
- name: Create a challenge for sample.com using a account key file.
  acme_certificate:
    account_key_src: /etc/pki/cert/private/account.key
    csr: /etc/pki/cert/csr/sample.com.csr
    dest: /etc/httpd/ssl/sample.com.crt
    fullchain_dest: /etc/httpd/ssl/sample.com-fullchain.crt
  register: sample_com_challenge

# perform the necessary steps to fulfill the challenge
# for example:
#
# - copy:
#     dest: /var/www/html/{{ sample_com_challenge['challenge_data']['sample.com']['http-01']['resource'] }}
#     content: "{{ sample_com_challenge['challenge_data']['sample.com']['http-01']['resource_value'] }}"
#     when: sample_com_challenge is changed

- name: Let the challenge be validated and retrieve the cert and intermediate certificate
  acme_certificate:
    account_key_src: /etc/pki/cert/private/account.key
    csr: /etc/pki/cert/csr/sample.com.csr
    dest: /etc/httpd/ssl/sample.com.crt
    fullchain_dest: /etc/httpd/ssl/sample.com-fullchain.crt
    chain_dest: /etc/httpd/ssl/sample.com-intermediate.crt
    data: "{{ sample_com_challenge }}"

### Example with DNS challenge against production ACME server ###

- name: Create a challenge for sample.com using a account key file.
  acme_certificate:
    account_key_src: /etc/pki/cert/private/account.key
    account_email: myself@sample.com
    src: /etc/pki/cert/csr/sample.com.csr
    cert: /etc/httpd/ssl/sample.com.crt
    challenge: dns-01
    acme_directory: https://acme-v01.api.letsencrypt.org/directory
    # Renew if the certificate is at least 30 days old
    remaining_days: 60
  register: sample_com_challenge

# perform the necessary steps to fulfill the challenge
# for example:
#
# - route53:
#     zone: sample.com
#     record: "{{ sample_com_challenge.challenge_data['sample.com']['dns-01'].record }}"
#     type: TXT
#     ttl: 60
#     # Note: route53 requires TXT entries to be enclosed in quotes
#     value: "{{ sample_com_challenge.challenge_data['sample.com']['dns-01'].resource_value }}"
#     when: sample_com_challenge is changed
#
# Alternative way:
#
# - route53:
#     zone: sample.com
#     record: "{{ item.key }}"
#     type: TXT
#     ttl: 60
#     # Note: item.value is a list of TXT entries, and route53
#     # requires every entry to be enclosed in quotes
#     value: "{{ item.value | map('regex_replace', '^(.*)$', '\'\\1\'' ) | list }}"
#     with_dict: sample_com_challenge.challenge_data_dns
#     when: sample_com_challenge is changed

- name: Let the challenge be validated and retrieve the cert and intermediate certificate
  acme_certificate:
    account_key_src: /etc/pki/cert/private/account.key
    account_email: myself@sample.com
    src: /etc/pki/cert/csr/sample.com.csr
    cert: /etc/httpd/ssl/sample.com.crt
    fullchain: /etc/httpd/ssl/sample.com-fullchain.crt
    chain: /etc/httpd/ssl/sample.com-intermediate.crt
    challenge: dns-01
    acme_directory: https://acme-v01.api.letsencrypt.org/directory
    remaining_days: 60
    data: "{{ sample_com_challenge }}"
'''

RETURN = '''
cert_days:
  description: the number of days the certificate remains valid.
  returned: success
  type: int
challenge_data:
  description: per domain / challenge type challenge data
  returned: changed
  type: complex
  contains:
    resource:
      description: the challenge resource that must be created for validation
      returned: changed
      type: string
      sample: .well-known/acme-challenge/evaGxfADs6pSRb2LAv9IZf17Dt3juxGJ-PCt92wr-oA
    resource_value:
      description: the value the resource has to produce for the validation
      returned: changed
      type: string
      sample: IlirfxKKXA...17Dt3juxGJ-PCt92wr-oA
    record:
      description: the full DNS record's name for the challenge
      returned: changed and challenge is C(dns-01)
      type: string
      sample: _acme-challenge.example.com
      version_added: "2.5"
challenge_data_dns:
  description: list of TXT values per DNS record, in case challenge is C(dns-01)
  returned: changed
  type: dict
  version_added: "2.5"
authorizations:
  description: ACME authorization data.
  returned: changed
  type: complex
  contains:
      authorization:
        description: ACME authorization object. See U(https://tools.ietf.org/html/draft-ietf-acme-acme-12#section-7.1.4)
        returned: success
        type: dict
order_uri:
  description: ACME order URI.
  returned: changed
  type: string
  version_added: "2.5"
finalization_uri:
  description: ACME finalization URI.
  returned: changed
  type: string
  version_added: "2.5"
account_uri:
  description: ACME account URI.
  returned: changed
  type: string
  version_added: "2.5"
'''

from ansible.module_utils.acme import (
    ModuleFailException, fetch_url, write_file, nopad_b64, simple_get, ACMEAccount
)

import base64
import hashlib
import locale
import os
import re
import textwrap
import time
from datetime import datetime

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text, to_bytes


def get_cert_days(module, cert_file):
    '''
    Return the days the certificate in cert_file remains valid and -1
    if the file was not found. If cert_file contains more than one
    certificate, only the first one will be considered.
    '''
    if not os.path.exists(cert_file):
        return -1

    openssl_bin = module.get_bin_path('openssl', True)
    openssl_cert_cmd = [openssl_bin, "x509", "-in", cert_file, "-noout", "-text"]
    dummy, out, dummy = module.run_command(openssl_cert_cmd, check_rc=True, encoding=None)
    try:
        not_after_str = re.search(r"\s+Not After\s*:\s+(.*)", out.decode('utf8')).group(1)
        not_after = datetime.fromtimestamp(time.mktime(time.strptime(not_after_str, '%b %d %H:%M:%S %Y %Z')))
    except AttributeError:
        raise ModuleFailException("No 'Not after' date found in {0}".format(cert_file))
    except ValueError:
        raise ModuleFailException("Failed to parse 'Not after' date of {0}".format(cert_file))
    now = datetime.utcnow()
    return (not_after - now).days


class ACMEClient(object):
    '''
    ACME client class. Uses an ACME account object and a CSR to
    start and validate ACME challenges and download the respective
    certificates.
    '''

    def __init__(self, module):
        self.module = module
        self.version = module.params['acme_version']
        self.challenge = module.params['challenge']
        self.csr = module.params['csr']
        self.dest = module.params.get('dest')
        self.fullchain_dest = module.params.get('fullchain_dest')
        self.chain_dest = module.params.get('chain_dest')
        self.account = ACMEAccount(module)
        self.directory = self.account.directory
        self.data = module.params['data']
        self.authorizations = None
        self.cert_days = -1
        self.order_uri = self.data.get('order_uri') if self.data else None
        self.finalize_uri = self.data.get('finalize_uri') if self.data else None

        # Make sure account exists
        modify_account = module.params['modify_account']
        if modify_account or self.version > 1:
            contact = []
            if module.params['account_email']:
                contact.append('mailto:' + module.params['account_email'])
            self.changed = self.account.init_account(
                contact,
                agreement=module.params.get('agreement'),
                terms_agreed=module.params.get('terms_agreed'),
                allow_creation=modify_account,
                update_contact=modify_account
            )
        else:
            # This happens if modify_account is False and the ACME v1
            # protocol is used. In this case, we do not call init_account()
            # to avoid accidental creation of an account. This is OK
            # since for ACME v1, the account URI is not needed to send a
            # signed ACME request.
            pass

        # Extract list of domains from CSR
        if not os.path.exists(self.csr):
            raise ModuleFailException("CSR %s not found" % (self.csr))

        self._openssl_bin = module.get_bin_path('openssl', True)
        self.domains = self._get_csr_domains()

    def _get_csr_domains(self):
        '''
        Parse the CSR and return the list of requested domains
        '''
        openssl_csr_cmd = [self._openssl_bin, "req", "-in", self.csr, "-noout", "-text"]
        dummy, out, dummy = self.module.run_command(openssl_csr_cmd, check_rc=True)

        domains = set([])
        common_name = re.search(r"Subject:.*? CN\s?=\s?([^\s,;/]+)", to_text(out, errors='surrogate_or_strict'))
        if common_name is not None:
            domains.add(common_name.group(1))
        subject_alt_names = re.search(
            r"X509v3 Subject Alternative Name: (?:critical)?\n +([^\n]+)\n",
            to_text(out, errors='surrogate_or_strict'), re.MULTILINE | re.DOTALL)
        if subject_alt_names is not None:
            for san in subject_alt_names.group(1).split(", "):
                if san.startswith("DNS:"):
                    domains.add(san[4:])
        return domains

    def _add_or_update_auth(self, domain, auth):
        '''
        Add or update the given authroization in the global authorizations list.
        Return True if the auth was updated/added and False if no change was
        necessary.
        '''
        if self.authorizations.get(domain) == auth:
            return False
        self.authorizations[domain] = auth
        return True

    def _new_authz_v1(self, domain):
        '''
        Create a new authorization for the given domain.
        Return the authorization object of the new authorization
        https://tools.ietf.org/html/draft-ietf-acme-acme-02#section-6.4
        '''
        if self.account.uri is None:
            return

        new_authz = {
            "resource": "new-authz",
            "identifier": {"type": "dns", "value": domain},
        }

        result, info = self.account.send_signed_request(self.directory['new-authz'], new_authz)
        if info['status'] not in [200, 201]:
            raise ModuleFailException("Error requesting challenges: CODE: {0} RESULT: {1}".format(info['status'], result))
        else:
            result['uri'] = info['location']
            return result

    def _get_challenge_data(self, auth, domain):
        '''
        Returns a dict with the data for all proposed (and supported) challenges
        of the given authorization.
        '''

        data = {}
        # no need to choose a specific challenge here as this module
        # is not responsible for fulfilling the challenges. Calculate
        # and return the required information for each challenge.
        for challenge in auth['challenges']:
            type = challenge['type']
            token = re.sub(r"[^A-Za-z0-9_\-]", "_", challenge['token'])
            keyauthorization = self.account.get_keyauthorization(token)

            if type == 'http-01':
                # https://tools.ietf.org/html/draft-ietf-acme-acme-09#section-8.3
                resource = '.well-known/acme-challenge/' + token
                data[type] = {'resource': resource, 'resource_value': keyauthorization}
            elif type == 'dns-01':
                # https://tools.ietf.org/html/draft-ietf-acme-acme-09#section-8.5
                resource = '_acme-challenge'
                value = nopad_b64(hashlib.sha256(to_bytes(keyauthorization)).digest())
                record = (resource + domain[1:]) if domain.startswith('*.') else (resource + '.' + domain)
                data[type] = {'resource': resource, 'resource_value': value, 'record': record}
            else:
                continue

        return data

    def _fail_challenge(self, domain, auth, error):
        '''
        Aborts with a specific error for a challenge.
        '''
        error_details = ''
        # multiple challenges could have failed at this point, gather error
        # details for all of them before failing
        for challenge in auth['challenges']:
            if challenge['status'] == 'invalid':
                error_details += ' CHALLENGE: {0}'.format(challenge['type'])
                if 'error' in challenge:
                    error_details += ' DETAILS: {0};'.format(challenge['error']['detail'])
                else:
                    error_details += ';'
        raise ModuleFailException("{0}: {1}".format(error.format(domain), error_details))

    def _validate_challenges(self, domain, auth):
        '''
        Validate the authorization provided in the auth dict. Returns True
        when the validation was successful and False when it was not.
        '''
        for challenge in auth['challenges']:
            if self.challenge != challenge['type']:
                continue

            uri = challenge['uri'] if self.version == 1 else challenge['url']

            challenge_response = {}
            if self.version == 1:
                token = re.sub(r"[^A-Za-z0-9_\-]", "_", challenge['token'])
                keyauthorization = self.account.get_keyauthorization(token)
                challenge_response["resource"] = "challenge"
                challenge_response["keyAuthorization"] = keyauthorization
            result, info = self.account.send_signed_request(uri, challenge_response)
            if info['status'] not in [200, 202]:
                raise ModuleFailException("Error validating challenge: CODE: {0} RESULT: {1}".format(info['status'], result))

        status = ''

        while status not in ['valid', 'invalid', 'revoked']:
            result = simple_get(self.module, auth['uri'])
            result['uri'] = auth['uri']
            if self._add_or_update_auth(domain, result):
                self.changed = True
            # draft-ietf-acme-acme-02
            # "status (required, string): ...
            # If this field is missing, then the default value is "pending"."
            if self.version == 1 and 'status' not in result:
                status = 'pending'
            else:
                status = result['status']
            time.sleep(2)

        if status == 'invalid':
            self._fail_challenge(domain, result, 'Authorization for {0} returned invalid')

        return status == 'valid'

    def _finalize_cert(self):
        '''
        Create a new certificate based on the csr.
        Return the certificate object as dict
        https://tools.ietf.org/html/draft-ietf-acme-acme-09#section-7.4
        '''
        openssl_csr_cmd = [self._openssl_bin, "req", "-in", self.csr, "-outform", "DER"]
        dummy, out, dummy = self.module.run_command(openssl_csr_cmd, check_rc=True)

        new_cert = {
            "csr": nopad_b64(to_bytes(out)),
        }
        result, info = self.account.send_signed_request(self.finalize_uri, new_cert)
        if info['status'] not in [200]:
            raise ModuleFailException("Error new cert: CODE: {0} RESULT: {1}".format(info['status'], result))

        order = info['location']

        status = result['status']
        while status not in ['valid', 'invalid']:
            time.sleep(2)
            result = simple_get(self.module, order)
            status = result['status']

        if status != 'valid':
            raise ModuleFailException("Error new cert: CODE: {0} STATUS: {1} RESULT: {2}".format(info['status'], status, result))

        return result['certificate']

    def _der_to_pem(self, der_cert):
        '''
        Convert the DER format certificate in der_cert to a PEM format
        certificate and return it.
        '''
        return """-----BEGIN CERTIFICATE-----\n{0}\n-----END CERTIFICATE-----\n""".format(
            "\n".join(textwrap.wrap(base64.b64encode(der_cert).decode('utf8'), 64)))

    def _download_cert(self, url):
        '''
        Download and parse the certificate chain.
        https://tools.ietf.org/html/draft-ietf-acme-acme-09#section-7.4.2
        '''
        resp, info = fetch_url(self.module, url, headers={'Accept': 'application/pem-certificate-chain'})
        try:
            content = resp.read()
        except AttributeError:
            content = info.get('body')

        if not content or not info['content-type'].startswith('application/pem-certificate-chain'):
            raise ModuleFailException("Cannot download certificate chain from {0}: {1} (headers: {2})".format(url, content, info))

        cert = None
        chain = []

        # Parse data
        lines = content.decode('utf-8').splitlines(True)
        current = []
        for line in lines:
            if line.strip():
                current.append(line)
            if line.startswith('-----END CERTIFICATE-----'):
                if cert is None:
                    cert = ''.join(current)
                else:
                    chain.append(''.join(current))
                current = []

        # Process link-up headers if there was no chain in reply
        if not chain and 'link' in info:
            link = info['link']
            parsed_link = re.match(r'<(.+)>;rel="(\w+)"', link)
            if parsed_link and parsed_link.group(2) == "up":
                chain_link = parsed_link.group(1)
                chain_result, chain_info = fetch_url(self.module, chain_link, method='GET')
                if chain_info['status'] in [200, 201]:
                    chain.append(self._der_to_pem(chain_result.read()))

        if cert is None or current:
            raise ModuleFailException("Failed to parse certificate chain download from {0}: {1} (headers: {2})".format(url, content, info))
        return {'cert': cert, 'chain': chain}

    def _new_cert_v1(self):
        '''
        Create a new certificate based on the CSR (ACME v1 protocol).
        Return the certificate object as dict
        https://tools.ietf.org/html/draft-ietf-acme-acme-02#section-6.5
        '''
        openssl_csr_cmd = [self._openssl_bin, "req", "-in", self.csr, "-outform", "DER"]
        dummy, out, dummy = self.module.run_command(openssl_csr_cmd, check_rc=True)

        new_cert = {
            "resource": "new-cert",
            "csr": nopad_b64(to_bytes(out)),
        }
        result, info = self.account.send_signed_request(self.directory['new-cert'], new_cert)

        chain = []
        if 'link' in info:
            link = info['link']
            parsed_link = re.match(r'<(.+)>;rel="(\w+)"', link)
            if parsed_link and parsed_link.group(2) == "up":
                chain_link = parsed_link.group(1)
                chain_result, chain_info = fetch_url(self.module, chain_link, method='GET')
                if chain_info['status'] in [200, 201]:
                    chain = [self._der_to_pem(chain_result.read())]

        if info['status'] not in [200, 201]:
            raise ModuleFailException("Error new cert: CODE: {0} RESULT: {1}".format(info['status'], result))
        else:
            return {'cert': self._der_to_pem(result), 'uri': info['location'], 'chain': chain}

    def _new_order_v2(self):
        '''
        Start a new certificate order (ACME v2 protocol).
        https://tools.ietf.org/html/draft-ietf-acme-acme-09#section-7.4
        '''
        identifiers = []
        for domain in self.domains:
            identifiers.append({
                'type': 'dns',
                'value': domain,
            })
        new_order = {
            "identifiers": identifiers
        }
        result, info = self.account.send_signed_request(self.directory['newOrder'], new_order)

        if info['status'] not in [201]:
            raise ModuleFailException("Error new order: CODE: {0} RESULT: {1}".format(info['status'], result))

        for auth_uri in result['authorizations']:
            auth_data = simple_get(self.module, auth_uri)
            auth_data['uri'] = auth_uri
            domain = auth_data['identifier']['value']
            if auth_data.get('wildcard', False):
                domain = '*.{0}'.format(domain)
            self.authorizations[domain] = auth_data

        self.order_uri = info['location']
        self.finalize_uri = result['finalize']

    def is_first_step(self):
        '''
        Return True if this is the first execution of this module, i.e. if a
        sufficient data object from a first run has not been provided.
        '''
        if (self.data is None) or ('authorizations' not in self.data):
            return True
        if self.finalize_uri is None and self.version != 1:
            return True
        return False

    def start_challenges(self):
        '''
        Create new authorizations for all domains of the CSR,
        respectively start a new order for ACME v2.
        '''
        self.authorizations = {}
        if self.version == 1:
            for domain in self.domains:
                new_auth = self._new_authz_v1(domain)
                self._add_or_update_auth(domain, new_auth)
        else:
            self._new_order_v2()
        self.changed = True

    def get_challenges_data(self):
        '''
        Get challenge details for the chosen challenge type.
        Return a tuple of generic challenge details, and specialized DNS challenge details.
        '''
        # Get general challenge data
        data = {}
        for domain, auth in self.authorizations.items():
            data[domain] = self._get_challenge_data(self.authorizations[domain], domain)
        # Get DNS challenge data
        data_dns = {}
        if self.challenge == 'dns-01':
            for domain, challenges in data.items():
                if self.challenge in challenges:
                    values = data_dns.get(challenges[self.challenge]['record'])
                    if values is None:
                        values = []
                        data_dns[challenges[self.challenge]['record']] = values
                    values.append(challenges[self.challenge]['resource_value'])
        return data, data_dns

    def finish_challenges(self):
        '''
        Verify challenges for all domains of the CSR.
        '''
        self.authorizations = {}
        for domain, auth in self.data['authorizations'].items():
            self.authorizations[domain] = auth
            if auth['status'] == 'pending':
                self._validate_challenges(domain, auth)

    def get_certificate(self):
        '''
        Request a new certificate and write it to the destination file.
        First verifies whether all authorizations are valid; if not, aborts
        with an error.
        '''
        for domain in self.domains:
            auth = self.authorizations.get(domain)
            if auth is None:
                raise ModuleFailException('Found no authorization information for "{0}"!'.format(domain))
            if 'status' not in auth:
                self._fail_challenge(domain, auth, 'Authorization for {0} returned no status')
            if auth['status'] != 'valid':
                self._fail_challenge(domain, auth, 'Authorization for {0} returned status ' + str(auth['status']))

        if self.version == 1:
            cert = self._new_cert_v1()
        else:
            cert_uri = self._finalize_cert()
            cert = self._download_cert(cert_uri)

        if cert['cert'] is not None:
            pem_cert = cert['cert']

            chain = [link for link in cert.get('chain', [])]

            if self.dest and write_file(self.module, self.dest, pem_cert.encode('utf8')):
                self.cert_days = get_cert_days(self.module, self.dest)
                self.changed = True

            if self.fullchain_dest and write_file(self.module, self.fullchain_dest, (pem_cert + "\n".join(chain)).encode('utf8')):
                self.cert_days = get_cert_days(self.module, self.fullchain_dest)
                self.changed = True

            if self.chain_dest and write_file(self.module, self.chain_dest, ("\n".join(chain)).encode('utf8')):
                self.changed = True

    def deactivate_authzs(self):
        '''
        Deactivates all valid authz's. Does not raise exceptions.
        https://community.letsencrypt.org/t/authorization-deactivation/19860/2
        https://tools.ietf.org/html/draft-ietf-acme-acme-09#section-7.5.2
        '''
        authz_deactivate = {
            'status': 'deactivated'
        }
        if self.version == 1:
            authz_deactivate['resource'] = 'authz'
        if self.authorizations:
            for domain in self.domains:
                auth = self.authorizations.get(domain)
                if auth is None or auth.get('status') != 'valid':
                    continue
                try:
                    result, info = self.account.send_signed_request(auth['uri'], authz_deactivate)
                    if 200 <= info['status'] < 300 and result.get('status') == 'deactivated':
                        auth['status'] = 'deactivated'
                except Exception as e:
                    # Ignore errors on deactivating authzs
                    pass
                if auth.get('status') != 'deactivated':
                    self.module.warn(warning='Could not deactivate authz object {0}.'.format(auth['uri']))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            account_key_src=dict(type='path', aliases=['account_key']),
            account_key_content=dict(type='str', no_log=True),
            modify_account=dict(required=False, type='bool', default=True),
            acme_directory=dict(required=False, default='https://acme-staging.api.letsencrypt.org/directory', type='str'),
            acme_version=dict(required=False, default=1, choices=[1, 2], type='int'),
            validate_certs=dict(required=False, default=True, type='bool'),
            account_email=dict(required=False, default=None, type='str'),
            agreement=dict(required=False, type='str'),
            terms_agreed=dict(required=False, default=False, type='bool'),
            challenge=dict(required=False, default='http-01', choices=['http-01', 'dns-01'], type='str'),
            csr=dict(required=True, aliases=['src'], type='path'),
            data=dict(required=False, default=None, type='dict'),
            dest=dict(aliases=['cert'], type='path'),
            fullchain_dest=dict(aliases=['fullchain'], type='path'),
            chain_dest=dict(required=False, default=None, aliases=['chain'], type='path'),
            remaining_days=dict(required=False, default=10, type='int'),
            deactivate_authzs=dict(required=False, default=False, type='bool'),
            force=dict(required=False, default=False, type='bool'),
        ),
        required_one_of=(
            ['account_key_src', 'account_key_content'],
            ['dest', 'fullchain_dest'],
        ),
        mutually_exclusive=(
            ['account_key_src', 'account_key_content'],
        ),
        supports_check_mode=True,
    )
    if module._name == 'letsencrypt':
        module.deprecate("The 'letsencrypt' module is being renamed 'acme_certificate'", version=2.10)

    # AnsibleModule() changes the locale, so change it back to C because we rely on time.strptime() when parsing certificate dates.
    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')
    locale.setlocale(locale.LC_ALL, 'C')

    if not module.params.get('validate_certs'):
        module.warn(warning='Disabling certificate validation for communications with ACME endpoint. ' +
                            'This should only be done for testing against a local ACME server for ' +
                            'development purposes, but *never* for production purposes.')

    try:
        if module.params.get('dest'):
            cert_days = get_cert_days(module, module.params['dest'])
        else:
            cert_days = get_cert_days(module, module.params['fullchain_dest'])

        if module.params['force'] or cert_days < module.params['remaining_days']:
            # If checkmode is active, base the changed state solely on the status
            # of the certificate file as all other actions (accessing an account, checking
            # the authorization status...) would lead to potential changes of the current
            # state
            if module.check_mode:
                module.exit_json(changed=True, authorizations={}, challenge_data={}, cert_days=cert_days)
            else:
                client = ACMEClient(module)
                client.cert_days = cert_days
                if client.is_first_step():
                    # First run: start challenges / start new order
                    client.start_challenges()
                else:
                    # Second run: finish challenges, and get certificate
                    try:
                        client.finish_challenges()
                        client.get_certificate()
                    finally:
                        if module.params['deactivate_authzs']:
                            client.deactivate_authzs()
                data, data_dns = client.get_challenges_data()
                module.exit_json(
                    changed=client.changed,
                    authorizations=client.authorizations,
                    finalize_uri=client.finalize_uri,
                    order_uri=client.order_uri,
                    account_uri=client.account.uri,
                    challenge_data=data,
                    challenge_data_dns=data_dns,
                    cert_days=client.cert_days
                )
        else:
            module.exit_json(changed=False, cert_days=cert_days)
    except ModuleFailException as e:
        e.do_fail(module)


if __name__ == '__main__':
    main()
