#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016 Michael Gruener <michael.gruener@chaosmoon.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: letsencrypt
author: "Michael Gruener (@mgruener)"
version_added: "2.2"
short_description: Create SSL certificates with Let's Encrypt
description:
   - "Create and renew SSL certificates with Let's Encrypt. Let’s Encrypt is a
      free, automated, and open certificate authority (CA), run for the
      public’s benefit. For details see U(https://letsencrypt.org). The current
      implementation supports the http-01, tls-sni-02 and dns-01 challenges."
   - "To use this module, it has to be executed at least twice. Either as two
      different tasks in the same run or during multiple runs."
   - "Between these two tasks you have to fulfill the required steps for the
      chosen challenge by whatever means necessary. For http-01 that means
      creating the necessary challenge file on the destination webserver. For
      dns-01 the necessary dns record has to be created. tls-sni-02 requires
      you to create a SSL certificate with the appropriate subjectAlternativeNames.
      It is I(not) the responsibility of this module to perform these steps."
   - "For details on how to fulfill these challenges, you might have to read through
      U(https://tools.ietf.org/html/draft-ietf-acme-acme-02#section-7)"
   - "Although the defaults are chosen so that the module can be used with
      the Let's Encrypt CA, the module can be used with any service using the ACME
      protocol."
requirements:
  - "python >= 2.6"
  - openssl
options:
  account_key:
    description:
      - "File containing the the Let's Encrypt account RSA key."
      - "Can be created with C(openssl rsa ...)."
    required: true
  account_email:
    description:
      - "The email address associated with this account."
      - "It will be used for certificate expiration warnings."
    required: false
    default: null
  acme_directory:
    description:
      - "The ACME directory to use. This is the entry point URL to access
         CA server API."
      - "For safety reasons the default is set to the Let's Encrypt staging server.
         This will create technically correct, but untrusted certificates."
    required: false
    default: https://acme-staging.api.letsencrypt.org/directory
  agreement:
    description:
      - "URI to a terms of service document you agree to when using the
         ACME service at C(acme_directory)."
    required: false
    default: 'https://letsencrypt.org/documents/LE-SA-v1.1.1-August-1-2016.pdf'
  challenge:
    description: The challenge to be performed.
    required: false
    choices: [ 'http-01', 'dns-01', 'tls-sni-02']
    default: 'http-01'
  csr:
    description:
      - "File containing the CSR for the new certificate."
      - "Can be created with C(openssl csr ...)."
      - "The CSR may contain multiple Subject Alternate Names, but each one
         will lead to an individual challenge that must be fulfilled for the
         CSR to be signed."
    required: true
    aliases: ['src']
  data:
    description:
      - "The data to validate ongoing challenges."
      - "The value that must be used here will be provided by a previous use
         of this module."
    required: false
    default: null
  dest:
    description: The destination file for the certificate.
    required: true
    aliases: ['cert']
  remaining_days:
    description:
      - "The number of days the certificate must have left being valid.
         If C(cert_days < remaining_days), then it will be renewed.
         If the certificate is not renewed, module return values will not
         include C(challenge_data)."
    required: false
    default: 10
'''

EXAMPLES = '''
- letsencrypt:
    account_key: /etc/pki/cert/private/account.key
    csr: /etc/pki/cert/csr/sample.com.csr
    dest: /etc/httpd/ssl/sample.com.crt
  register: sample_com_challenge

# perform the necessary steps to fulfill the challenge
# for example:
#
# - copy:
#     dest: /var/www/html/{{ sample_com_challenge['challenge_data']['sample.com']['http-01']['resource'] }}
#     content: "{{ sample_com_challenge['challenge_data']['sample.com']['http-01']['resource_value'] }}"
#     when: sample_com_challenge|changed

- letsencrypt:
    account_key: /etc/pki/cert/private/account.key
    csr: /etc/pki/cert/csr/sample.com.csr
    dest: /etc/httpd/ssl/sample.com.crt
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
authorizations:
  description: ACME authorization data.
  returned: changed
  type: complex
  contains:
      authorization:
        description: ACME authorization object. See https://tools.ietf.org/html/draft-ietf-acme-acme-02#section-6.1.2
        returned: success
        type: dict
'''

import base64
import binascii
import copy
import hashlib
import json
import locale
import os
import re
import shutil
import tempfile
import textwrap
import time
import traceback
from datetime import datetime

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url


def nopad_b64(data):
    return base64.urlsafe_b64encode(data).decode('utf8').replace("=", "")


def simple_get(module, url):
    resp, info = fetch_url(module, url, method='GET')

    result = None
    try:
        content = resp.read()
    except AttributeError:
        if info['body']:
            content = info['body']

    if content:
        if info['content-type'].startswith('application/json'):
            try:
                result = module.from_json(content.decode('utf8'))
            except ValueError:
                module.fail_json(msg="Failed to parse the ACME response: {0} {1}".format(url, content))
        else:
            result = content

    if info['status'] >= 400:
        module.fail_json(msg="ACME request failed: CODE: {0} RESULT: {1}".format(info['status'], result))
    return result


def get_cert_days(module, cert_file):
    '''
    Return the days the certificate in cert_file remains valid and -1
    if the file was not found.
    '''
    if not os.path.exists(cert_file):
        return -1

    openssl_bin = module.get_bin_path('openssl', True)
    openssl_cert_cmd = [openssl_bin, "x509", "-in", cert_file, "-noout", "-text"]
    _, out, _ = module.run_command(openssl_cert_cmd, check_rc=True)
    try:
        not_after_str = re.search(r"\s+Not After\s*:\s+(.*)", out.decode('utf8')).group(1)
        not_after = datetime.datetime.fromtimestamp(time.mktime(time.strptime(not_after_str, '%b %d %H:%M:%S %Y %Z')))
    except AttributeError:
        module.fail_json(msg="No 'Not after' date found in {0}".format(cert_file))
    except ValueError:
        module.fail_json(msg="Failed to parse 'Not after' date of {0}".format(cert_file))
    now = datetime.datetime.utcnow()
    return (not_after - now).days


# function source: network/basics/uri.py
def write_file(module, dest, content):
    '''
    Write content to destination file dest, only if the content
    has changed.
    '''
    changed = False
    # create a tempfile with some test content
    _, tmpsrc = tempfile.mkstemp()
    f = open(tmpsrc, 'wb')
    try:
        f.write(content)
    except Exception as err:
        os.remove(tmpsrc)
        module.fail_json(msg="failed to create temporary content file: %s" % to_native(err), exception=traceback.format_exc())
    f.close()
    checksum_src = None
    checksum_dest = None
    # raise an error if there is no tmpsrc file
    if not os.path.exists(tmpsrc):
        os.remove(tmpsrc)
        module.fail_json(msg="Source %s does not exist" % (tmpsrc))
    if not os.access(tmpsrc, os.R_OK):
        os.remove(tmpsrc)
        module.fail_json(msg="Source %s not readable" % (tmpsrc))
    checksum_src = module.sha1(tmpsrc)
    # check if there is no dest file
    if os.path.exists(dest):
        # raise an error if copy has no permission on dest
        if not os.access(dest, os.W_OK):
            os.remove(tmpsrc)
            module.fail_json(msg="Destination %s not writable" % (dest))
        if not os.access(dest, os.R_OK):
            os.remove(tmpsrc)
            module.fail_json(msg="Destination %s not readable" % (dest))
        checksum_dest = module.sha1(dest)
    else:
        if not os.access(os.path.dirname(dest), os.W_OK):
            os.remove(tmpsrc)
            module.fail_json(msg="Destination dir %s not writable" % (os.path.dirname(dest)))
    if checksum_src != checksum_dest:
        try:
            shutil.copyfile(tmpsrc, dest)
            changed = True
        except Exception as err:
            os.remove(tmpsrc)
            module.fail_json(msg="failed to copy %s to %s: %s" % (tmpsrc, dest, to_native(err)), exception=traceback.format_exc())
    os.remove(tmpsrc)
    return changed


class ACMEDirectory(object):
    '''
    The ACME server directory. Gives access to the available resources
    and the Replay-Nonce for a given URI. This only works for
    URIs that permit GET requests (so normally not the ones that
    require authentication).
    https://tools.ietf.org/html/draft-ietf-acme-acme-02#section-6.2
    '''
    def __init__(self, module):
        self.module = module
        self.directory_root = module.params['acme_directory']

        self.directory = simple_get(self.module, self.directory_root)

    def __getitem__(self, key):
        return self.directory[key]

    def get_nonce(self, resource=None):
        url = self.directory_root
        if resource is not None:
            url = resource
        _, info = fetch_url(self.module, url, method='HEAD')
        if info['status'] != 200:
            self.module.fail_json(msg="Failed to get replay-nonce, got status {0}".format(info['status']))
        return info['replay-nonce']


class ACMEAccount(object):
    '''
    ACME account object. Handles the authorized communication with the
    ACME server. Provides access to account bound information like
    the currently active authorizations and valid certificates
    '''
    def __init__(self, module):
        self.module = module
        self.agreement = module.params['agreement']
        self.key = module.params['account_key']
        self.email = module.params['account_email']
        self.data = module.params['data']
        self.directory = ACMEDirectory(module)
        self.uri = None
        self.changed = False

        self._authz_list_uri = None
        self._certs_list_uri = None

        if not os.path.exists(self.key):
            module.fail_json(msg="Account key %s not found" % (self.key))

        self._openssl_bin = module.get_bin_path('openssl', True)

        pub_hex, pub_exp = self._parse_account_key(self.key)
        self.jws_header = {
            "alg": "RS256",
            "jwk": {
                "e": nopad_b64(binascii.unhexlify(pub_exp.encode("utf-8"))),
                "kty": "RSA",
                "n": nopad_b64(binascii.unhexlify(re.sub(r"(\s|:)", "", pub_hex).encode("utf-8"))),
            },
        }
        self.init_account()

    def get_keyauthorization(self, token):
        '''
        Returns the key authorization for the given token
        https://tools.ietf.org/html/draft-ietf-acme-acme-02#section-7.1
        '''
        accountkey_json = json.dumps(self.jws_header['jwk'], sort_keys=True, separators=(',', ':'))
        thumbprint = nopad_b64(hashlib.sha256(accountkey_json.encode('utf8')).digest())
        return "{0}.{1}".format(token, thumbprint)

    def _parse_account_key(self, key):
        '''
        Parses an RSA key file in PEM format and returns the modulus
        and public exponent of the key
        '''
        openssl_keydump_cmd = [self._openssl_bin, "rsa", "-in", key, "-noout", "-text"]
        _, out, _ = self.module.run_command(openssl_keydump_cmd, check_rc=True)

        pub_hex, pub_exp = re.search(
            r"modulus:\n\s+00:([a-f0-9\:\s]+?)\npublicExponent: ([0-9]+)",
            out.decode('utf8'), re.MULTILINE | re.DOTALL).groups()
        pub_exp = "{0:x}".format(int(pub_exp))
        if len(pub_exp) % 2:
            pub_exp = "0{0}".format(pub_exp)

        return pub_hex, pub_exp

    def send_signed_request(self, url, payload):
        '''
        Sends a JWS signed HTTP POST request to the ACME server and returns
        the response as dictionary
        https://tools.ietf.org/html/draft-ietf-acme-acme-02#section-5.2
        '''
        protected = copy.deepcopy(self.jws_header)
        protected["nonce"] = self.directory.get_nonce()

        try:
            payload64 = nopad_b64(self.module.jsonify(payload).encode('utf8'))
            protected64 = nopad_b64(self.module.jsonify(protected).encode('utf8'))
        except Exception as e:
            self.module.fail_json(msg="Failed to encode payload / headers as JSON: {0}".format(e))

        openssl_sign_cmd = [self._openssl_bin, "dgst", "-sha256", "-sign", self.key]
        sign_payload = "{0}.{1}".format(protected64, payload64).encode('utf8')
        _, out, _ = self.module.run_command(openssl_sign_cmd, data=sign_payload, check_rc=True, binary_data=True)

        data = self.module.jsonify({
            "header": self.jws_header,
            "protected": protected64,
            "payload": payload64,
            "signature": nopad_b64(out),
        })

        resp, info = fetch_url(self.module, url, data=data, method='POST')
        result = None
        try:
            content = resp.read()
        except AttributeError:
            if info['body']:
                content = info['body']

        if content:
            if info['content-type'].startswith('application/json'):
                try:
                    result = self.module.from_json(content.decode('utf8'))
                except ValueError:
                    self.module.fail_json(msg="Failed to parse the ACME response: {0} {1}".format(url, content))
            else:
                result = content

        return result, info

    def _new_reg(self, contact=[]):
        '''
        Registers a new ACME account. Returns True if the account was
        created and False if it already existed (e.g. it was not newly
        created)
        https://tools.ietf.org/html/draft-ietf-acme-acme-02#section-6.3
        '''
        if self.uri is not None:
            return True

        new_reg = {
            'resource': 'new-reg',
            'agreement': self.agreement,
            'contact': contact
        }

        result, info = self.send_signed_request(self.directory['new-reg'], new_reg)
        if 'location' in info:
            self.uri = info['location']

        if info['status'] in [200, 201]:
            # Account did not exist
            self.changed = True
            return True
        elif info['status'] == 409:
            # Account did exist
            return False
        else:
            self.module.fail_json(msg="Error registering: {0} {1}".format(info['status'], result))

    def init_account(self):
        '''
        Create or update an account on the ACME server. As the only way
        (without knowing an account URI) to test if an account exists
        is to try and create one with the provided account key, this
        method will always result in an account being present (except
        on error situations). If the account already exists, it will
        update the contact information.
        https://tools.ietf.org/html/draft-ietf-acme-acme-02#section-6.3
        '''

        contact = []
        if self.email:
            contact.append('mailto:' + self.email)

        # if this is not a new registration (e.g. existing account)
        if not self._new_reg(contact):
            # pre-existing account, get account data...
            result, _ = self.send_signed_request(self.uri, {'resource': 'reg'})

            # XXX: letsencrypt/boulder#1435
            if 'authorizations' in result:
                self._authz_list_uri = result['authorizations']
            if 'certificates' in result:
                self._certs_list_uri = result['certificates']

            # ...and check if update is necessary
            do_update = False
            if 'contact' in result:
                if contact != result['contact']:
                    do_update = True
            elif len(contact) > 0:
                do_update = True

            if do_update:
                upd_reg = result
                upd_reg['contact'] = contact
                result, _ = self.send_signed_request(self.uri, upd_reg)
                self.changed = True

    def get_authorizations(self):
        '''
        Return a list of currently active authorizations
        https://tools.ietf.org/html/draft-ietf-acme-acme-02#section-6.4
        '''
        authz_list = {'authorizations': []}
        if self._authz_list_uri is None:
            # XXX: letsencrypt/boulder#1435
            # Workaround, retrieve the known authorization urls
            # from the data attribute
            # It is also a way to limit the queried authorizations, which
            # might become relevant at some point
            if (self.data is not None) and ('authorizations' in self.data):
                for auth in self.data['authorizations']:
                    authz_list['authorizations'].append(auth['uri'])
            else:
                return []
        else:
            # TODO: need to handle pagination
            authz_list = simple_get(self.module, self._authz_list_uri)

        authz = []
        for auth_uri in authz_list['authorizations']:
            auth = simple_get(self.module, auth_uri)
            auth['uri'] = auth_uri
            authz.append(auth)

        return authz


class ACMEClient(object):
    '''
    ACME client class. Uses an ACME account object and a CSR to
    start and validate ACME challenges and download the respective
    certificates.
    '''
    def __init__(self, module):
        self.module = module
        self.challenge = module.params['challenge']
        self.csr = module.params['csr']
        self.dest = module.params['dest']
        self.account = ACMEAccount(module)
        self.directory = self.account.directory
        self.authorizations = self.account.get_authorizations()
        self.cert_days = -1
        self.changed = self.account.changed

        if not os.path.exists(self.csr):
            module.fail_json(msg="CSR %s not found" % (self.csr))

        self._openssl_bin = module.get_bin_path('openssl', True)
        self.domains = self._get_csr_domains()

    def _get_csr_domains(self):
        '''
        Parse the CSR and return the list of requested domains
        '''
        openssl_csr_cmd = [self._openssl_bin, "req", "-in", self.csr, "-noout", "-text"]
        _, out, _ = self.module.run_command(openssl_csr_cmd, check_rc=True)

        domains = set([])
        common_name = re.search(r"Subject:.*? CN\s?=\s?([^\s,;/]+)", out.decode('utf8'))
        if common_name is not None:
            domains.add(common_name.group(1))
        subject_alt_names = re.search(r"X509v3 Subject Alternative Name: \n +([^\n]+)\n", out.decode('utf8'), re.MULTILINE | re.DOTALL)
        if subject_alt_names is not None:
            for san in subject_alt_names.group(1).split(", "):
                if san.startswith("DNS:"):
                    domains.add(san[4:])
        return domains

    def _get_domain_auth(self, domain):
        '''
        Get the status string of the first authorization for the given domain.
        Return None if no active authorization for the given domain was found.
        '''
        if self.authorizations is None:
            return None

        for auth in self.authorizations:
            if (auth['identifier']['type'] == 'dns') and (auth['identifier']['value'] == domain):
                return auth
        return None

    def _add_or_update_auth(self, auth):
        '''
        Add or update the given authroization in the global authorizations list.
        Return True if the auth was updated/added and False if no change was
        necessary.
        '''
        for index, cur_auth in enumerate(self.authorizations):
            if (cur_auth['uri'] == auth['uri']):
                # does the auth parameter contain updated data?
                if cur_auth != auth:
                    # yes, update our current authorization list
                    self.authorizations[index] = auth
                    return True
                else:
                    return False
        # this is a new authorization, add it to the list of current
        # authorizations
        self.authorizations.append(auth)
        return True

    def _new_authz(self, domain):
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
            self.module.fail_json(msg="Error requesting challenges: CODE: {0} RESULT: {1}".format(info['status'], result))
        else:
            result['uri'] = info['location']
            return result

    def _get_challenge_data(self, auth):
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

            # NOTE: tls-sni-01 is not supported by choice
            # too complex to be useful and tls-sni-02 is an alternative
            # as soon as it is implemented server side
            if type == 'http-01':
                # https://tools.ietf.org/html/draft-ietf-acme-acme-02#section-7.2
                resource = '.well-known/acme-challenge/' + token
                value = keyauthorization
            elif type == 'tls-sni-02':
                # https://tools.ietf.org/html/draft-ietf-acme-acme-02#section-7.3
                token_digest = hashlib.sha256(token.encode('utf8')).hexdigest()
                ka_digest = hashlib.sha256(keyauthorization.encode('utf8')).hexdigest()
                len_token_digest = len(token_digest)
                len_ka_digest = len(ka_digest)
                resource = 'subjectAlternativeNames'
                value = [
                    "{0}.{1}.token.acme.invalid".format(token_digest[:len_token_digest // 2], token_digest[len_token_digest // 2:]),
                    "{0}.{1}.ka.acme.invalid".format(ka_digest[:len_ka_digest // 2], ka_digest[len_ka_digest // 2:]),
                ]
            elif type == 'dns-01':
                # https://tools.ietf.org/html/draft-ietf-acme-acme-02#section-7.4
                resource = '_acme-challenge'
                value = nopad_b64(hashlib.sha256(keyauthorization).digest()).encode('utf8')
            else:
                continue

            data[type] = {'resource': resource, 'resource_value': value}
        return data

    def _validate_challenges(self, auth):
        '''
        Validate the authorization provided in the auth dict. Returns True
        when the validation was successful and False when it was not.
        '''
        for challenge in auth['challenges']:
            if self.challenge != challenge['type']:
                continue

            uri = challenge['uri']
            token = re.sub(r"[^A-Za-z0-9_\-]", "_", challenge['token'])
            keyauthorization = self.account.get_keyauthorization(token)

            challenge_response = {
                "resource": "challenge",
                "keyAuthorization": keyauthorization,
            }
            result, info = self.account.send_signed_request(uri, challenge_response)
            if info['status'] not in [200, 202]:
                self.module.fail_json(msg="Error validating challenge: CODE: {0} RESULT: {1}".format(info['status'], result))

        status = ''

        while status not in ['valid', 'invalid', 'revoked']:
            result = simple_get(self.module, auth['uri'])
            result['uri'] = auth['uri']
            if self._add_or_update_auth(result):
                self.changed = True
            # draft-ietf-acme-acme-02
            # "status (required, string): ...
            # If this field is missing, then the default value is "pending"."
            if 'status' not in result:
                status = 'pending'
            else:
                status = result['status']
            time.sleep(2)

        if status == 'invalid':
            error_details = ''
            # multiple challenges could have failed at this point, gather error
            # details for all of them before failing
            for challenge in result['challenges']:
                if challenge['status'] == 'invalid':
                    error_details += ' CHALLENGE: {0}'.format(challenge['type'])
                    if 'error' in challenge:
                        error_details += ' DETAILS: {0};'.format(challenge['error']['detail'])
                    else:
                        error_details += ';'
            self.module.fail_json(msg="Authorization for {0} returned invalid: {1}".format(result['identifier']['value'], error_details))

        return status == 'valid'

    def _new_cert(self):
        '''
        Create a new certificate based on the csr.
        Return the certificate object as dict
        https://tools.ietf.org/html/draft-ietf-acme-acme-02#section-6.5
        '''
        openssl_csr_cmd = [self._openssl_bin, "req", "-in", self.csr, "-outform", "DER"]
        _, out, _ = self.module.run_command(openssl_csr_cmd, check_rc=True)

        new_cert = {
            "resource": "new-cert",
            "csr": nopad_b64(out),
        }
        result, info = self.account.send_signed_request(self.directory['new-cert'], new_cert)
        if info['status'] not in [200, 201]:
            self.module.fail_json(msg="Error new cert: CODE: {0} RESULT: {1}".format(info['status'], result))
        else:
            return {'cert': result, 'uri': info['location']}

    def _der_to_pem(self, der_cert):
        '''
        Convert the DER format certificate in der_cert to a PEM format
        certificate and return it.
        '''
        return """-----BEGIN CERTIFICATE-----\n{0}\n-----END CERTIFICATE-----\n""".format(
            "\n".join(textwrap.wrap(base64.b64encode(der_cert).decode('utf8'), 64)))

    def do_challenges(self):
        '''
        Create new authorizations for all domains of the CSR and return
        the challenge details for the chosen challenge type.
        '''
        data = {}
        for domain in self.domains:
            auth = self._get_domain_auth(domain)
            if auth is None:
                new_auth = self._new_authz(domain)
                self._add_or_update_auth(new_auth)
                data[domain] = self._get_challenge_data(new_auth)
                self.changed = True
            elif (auth['status'] == 'pending') or ('status' not in auth):
                # draft-ietf-acme-acme-02
                # "status (required, string): ...
                # If this field is missing, then the default value is "pending"."
                self._validate_challenges(auth)
                # _validate_challenges updates the global authrozation dict,
                # so get the current version of the authorization we are working
                # on to retrieve the challenge data
                data[domain] = self._get_challenge_data(self._get_domain_auth(domain))

        return data

    def get_certificate(self):
        '''
        Request a new certificate and write it to the destination file.
        Only do this if a destination file was provided and if all authorizations
        for the domains of the csr are valid. No Return value.
        '''
        if self.dest is None:
            return

        for domain in self.domains:
            auth = self._get_domain_auth(domain)
            if auth is None or ('status' not in auth) or (auth['status'] != 'valid'):
                return

        cert = self._new_cert()
        if cert['cert'] is not None:
            pem_cert = self._der_to_pem(cert['cert'])
            if write_file(self.module, self.dest, pem_cert):
                self.cert_days = get_cert_days(self.module, self.dest)
                self.changed = True


def main():
    module = AnsibleModule(
        argument_spec=dict(
            account_key=dict(required=True, type='path'),
            account_email=dict(required=False, default=None, type='str'),
            acme_directory=dict(required=False, default='https://acme-staging.api.letsencrypt.org/directory', type='str'),
            agreement=dict(required=False, default='https://letsencrypt.org/documents/LE-SA-v1.1.1-August-1-2016.pdf', type='str'),
            challenge=dict(required=False, default='http-01', choices=['http-01', 'dns-01', 'tls-sni-02'], type='str'),
            csr=dict(required=True, aliases=['src'], type='path'),
            data=dict(required=False, no_log=True, default=None, type='dict'),
            dest=dict(required=True, aliases=['cert'], type='path'),
            remaining_days=dict(required=False, default=10, type='int'),
        ),
        supports_check_mode=True,
    )

    # AnsibleModule() changes the locale, so change it back to C because we rely on time.strptime() when parsing certificate dates.
    locale.setlocale(locale.LC_ALL, "C")

    cert_days = get_cert_days(module, module.params['dest'])
    if cert_days < module.params['remaining_days']:
        # If checkmode is active, base the changed state solely on the status
        # of the certificate file as all other actions (accessing an account, checking
        # the authorization status...) would lead to potential changes of the current
        # state
        if module.check_mode:
            module.exit_json(changed=True, authorizations={}, challenge_data={}, cert_days=cert_days)
        else:
            client = ACMEClient(module)
            client.cert_days = cert_days
            data = client.do_challenges()
            client.get_certificate()
            module.exit_json(changed=client.changed, authorizations=client.authorizations, challenge_data=data, cert_days=client.cert_days)
    else:
        module.exit_json(changed=False, cert_days=cert_days)


if __name__ == '__main__':
    main()
