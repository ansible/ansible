# -*- coding: utf-8 -*-

# (c) 2016 Michael Gruener <michael.gruener@chaosmoon.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import base64
import binascii
import copy
import hashlib
import json
import os
import re
import shutil
import tempfile
import traceback

from ansible.module_utils._text import to_native, to_text, to_bytes
from ansible.module_utils.urls import fetch_url as _fetch_url


class ModuleFailException(Exception):
    '''
    If raised, module.fail_json() will be called with the given parameters after cleanup.
    '''
    def __init__(self, msg, **args):
        super(ModuleFailException, self).__init__(self, msg)
        self.msg = msg
        self.module_fail_args = args

    def do_fail(self, module):
        module.fail_json(msg=self.msg, other=self.module_fail_args)


def _lowercase_fetch_url(*args, **kwargs):
    '''
     Add lowercase representations of the header names as dict keys

    '''
    response, info = _fetch_url(*args, **kwargs)

    info.update(dict((header.lower(), value) for (header, value) in info.items()))
    return response, info


fetch_url = _lowercase_fetch_url


def nopad_b64(data):
    return base64.urlsafe_b64encode(data).decode('utf8').replace("=", "")


def simple_get(module, url):
    resp, info = fetch_url(module, url, method='GET')

    result = {}
    try:
        content = resp.read()
    except AttributeError:
        content = info.get('body')

    if content:
        if info['content-type'].startswith('application/json'):
            try:
                result = module.from_json(content.decode('utf8'))
            except ValueError:
                raise ModuleFailException("Failed to parse the ACME response: {0} {1}".format(url, content))
        else:
            result = content

    if info['status'] >= 400:
        raise ModuleFailException("ACME request failed: CODE: {0} RESULT: {1}".format(info['status'], result))
    return result


# function source: network/basics/uri.py
def write_file(module, dest, content):
    '''
    Write content to destination file dest, only if the content
    has changed.
    '''
    changed = False
    # create a tempfile
    fd, tmpsrc = tempfile.mkstemp(text=False)
    f = os.fdopen(fd, 'wb')
    try:
        f.write(content)
    except Exception as err:
        try:
            f.close()
        except Exception as e:
            pass
        os.remove(tmpsrc)
        raise ModuleFailException("failed to create temporary content file: %s" % to_native(err), exception=traceback.format_exc())
    f.close()
    checksum_src = None
    checksum_dest = None
    # raise an error if there is no tmpsrc file
    if not os.path.exists(tmpsrc):
        try:
            os.remove(tmpsrc)
        except Exception as e:
            pass
        raise ModuleFailException("Source %s does not exist" % (tmpsrc))
    if not os.access(tmpsrc, os.R_OK):
        os.remove(tmpsrc)
        raise ModuleFailException("Source %s not readable" % (tmpsrc))
    checksum_src = module.sha1(tmpsrc)
    # check if there is no dest file
    if os.path.exists(dest):
        # raise an error if copy has no permission on dest
        if not os.access(dest, os.W_OK):
            os.remove(tmpsrc)
            raise ModuleFailException("Destination %s not writable" % (dest))
        if not os.access(dest, os.R_OK):
            os.remove(tmpsrc)
            raise ModuleFailException("Destination %s not readable" % (dest))
        checksum_dest = module.sha1(dest)
    else:
        if not os.access(os.path.dirname(dest), os.W_OK):
            os.remove(tmpsrc)
            raise ModuleFailException("Destination dir %s not writable" % (os.path.dirname(dest)))
    if checksum_src != checksum_dest:
        try:
            shutil.copyfile(tmpsrc, dest)
            changed = True
        except Exception as err:
            os.remove(tmpsrc)
            raise ModuleFailException("failed to copy %s to %s: %s" % (tmpsrc, dest, to_native(err)), exception=traceback.format_exc())
    os.remove(tmpsrc)
    return changed


class ACMEDirectory(object):
    '''
    The ACME server directory. Gives access to the available resources
    and the Replay-Nonce for a given URI. This only works for
    URIs that permit GET requests (so normally not the ones that
    require authentication).
    https://tools.ietf.org/html/draft-ietf-acme-acme-09#section-7.1.1
    '''

    def __init__(self, module):
        self.module = module
        self.directory_root = module.params['acme_directory']
        self.version = module.params['acme_version']

        self.directory = simple_get(self.module, self.directory_root)

        # Check whether self.version matches what we expect
        if self.version == 1:
            for key in ('new-reg', 'new-authz', 'new-cert'):
                if key not in self.directory:
                    raise ModuleFailException("ACME directory does not seem to follow protocol ACME v1")
        if self.version == 2:
            for key in ('newNonce', 'newAccount', 'newOrder'):
                if key not in self.directory:
                    raise ModuleFailException("ACME directory does not seem to follow protocol ACME v2")

    def __getitem__(self, key):
        return self.directory[key]

    def get_nonce(self, resource=None):
        url = self.directory_root if self.version == 1 else self.directory['newNonce']
        if resource is not None:
            url = resource
        dummy, info = fetch_url(self.module, url, method='HEAD')
        if info['status'] not in (200, 204):
            raise ModuleFailException("Failed to get replay-nonce, got status {0}".format(info['status']))
        return info['replay-nonce']


class ACMEAccount(object):
    '''
    ACME account object. Handles the authorized communication with the
    ACME server. Provides access to account bound information like
    the currently active authorizations and valid certificates
    '''

    def __init__(self, module):
        self.module = module
        self.version = module.params['acme_version']
        # account_key path and content are mutually exclusive
        self.key = module.params['account_key_src']
        self.key_content = module.params['account_key_content']
        self.directory = ACMEDirectory(module)

        self.uri = None

        self._openssl_bin = module.get_bin_path('openssl', True)

        # Create a key file from content, key (path) and key content are mutually exclusive
        if self.key_content is not None:
            fd, tmpsrc = tempfile.mkstemp()
            module.add_cleanup_file(tmpsrc)  # Ansible will delete the file on exit
            f = os.fdopen(fd, 'wb')
            try:
                f.write(self.key_content.encode('utf-8'))
                self.key = tmpsrc
            except Exception as err:
                try:
                    f.close()
                except Exception as e:
                    pass
                raise ModuleFailException("failed to create temporary content file: %s" % to_native(err), exception=traceback.format_exc())
            f.close()

        error, self.key_data = self._parse_account_key(self.key)
        if error:
            raise ModuleFailException("error while parsing account key: %s" % error)
        self.jwk = self.key_data['jwk']
        self.jws_header = {
            "alg": self.key_data['alg'],
            "jwk": self.jwk,
        }

    def get_keyauthorization(self, token):
        '''
        Returns the key authorization for the given token
        https://tools.ietf.org/html/draft-ietf-acme-acme-09#section-8.1
        '''
        accountkey_json = json.dumps(self.jwk, sort_keys=True, separators=(',', ':'))
        thumbprint = nopad_b64(hashlib.sha256(accountkey_json.encode('utf8')).digest())
        return "{0}.{1}".format(token, thumbprint)

    def _parse_account_key(self, key):
        '''
        Parses an RSA or Elliptic Curve key file in PEM format and returns a pair
        (error, key_data).
        '''
        account_key_type = None
        with open(key, "rt") as f:
            for line in f:
                m = re.match(r"^\s*-{5,}BEGIN\s+(EC|RSA)\s+PRIVATE\s+KEY-{5,}\s*$", line)
                if m is not None:
                    account_key_type = m.group(1).lower()
                    break
        if account_key_type is None:
            # This happens for example if openssl_privatekey created this key
            # (as opposed to the OpenSSL binary). For now, we assume this is
            # an RSA key.
            # FIXME: add some kind of auto-detection
            account_key_type = "rsa"
        if account_key_type not in ("rsa", "ec"):
            return 'unknown key type "%s"' % account_key_type, {}

        openssl_keydump_cmd = [self._openssl_bin, account_key_type, "-in", key, "-noout", "-text"]
        dummy, out, dummy = self.module.run_command(openssl_keydump_cmd, check_rc=True)

        if account_key_type == 'rsa':
            pub_hex, pub_exp = re.search(
                r"modulus:\n\s+00:([a-f0-9\:\s]+?)\npublicExponent: ([0-9]+)",
                to_text(out, errors='surrogate_or_strict'), re.MULTILINE | re.DOTALL).groups()
            pub_exp = "{0:x}".format(int(pub_exp))
            if len(pub_exp) % 2:
                pub_exp = "0{0}".format(pub_exp)

            return None, {
                'type': 'rsa',
                'alg': 'RS256',
                'jwk': {
                    "kty": "RSA",
                    "e": nopad_b64(binascii.unhexlify(pub_exp.encode("utf-8"))),
                    "n": nopad_b64(binascii.unhexlify(re.sub(r"(\s|:)", "", pub_hex).encode("utf-8"))),
                },
                'hash': 'sha256',
            }
        elif account_key_type == 'ec':
            pub_data = re.search(
                r"pub:\s*\n\s+04:([a-f0-9\:\s]+?)\nASN1 OID: (\S+)(?:\nNIST CURVE: (\S+))?",
                to_text(out, errors='surrogate_or_strict'), re.MULTILINE | re.DOTALL)
            if pub_data is None:
                return 'cannot parse elliptic curve key', {}
            pub_hex = binascii.unhexlify(re.sub(r"(\s|:)", "", pub_data.group(1)).encode("utf-8"))
            asn1_oid_curve = pub_data.group(2).lower()
            nist_curve = pub_data.group(3).lower() if pub_data.group(3) else None
            if asn1_oid_curve == 'prime256v1' or nist_curve == 'p-256':
                bits = 256
                alg = 'ES256'
                hash = 'sha256'
                point_size = 32
                curve = 'P-256'
            elif asn1_oid_curve == 'secp384r1' or nist_curve == 'p-384':
                bits = 384
                alg = 'ES384'
                hash = 'sha384'
                point_size = 48
                curve = 'P-384'
            elif asn1_oid_curve == 'secp521r1' or nist_curve == 'p-521':
                # Not yet supported on Let's Encrypt side, see
                # https://github.com/letsencrypt/boulder/issues/2217
                bits = 521
                alg = 'ES512'
                hash = 'sha512'
                point_size = 66
                curve = 'P-521'
            else:
                return 'unknown elliptic curve: %s / %s' % (asn1_oid_curve, nist_curve), {}
            bytes = (bits + 7) // 8
            if len(pub_hex) != 2 * bytes:
                return 'bad elliptic curve point (%s / %s)' % (asn1_oid_curve, nist_curve), {}
            return None, {
                'type': 'ec',
                'alg': alg,
                'jwk': {
                    "kty": "EC",
                    "crv": curve,
                    "x": nopad_b64(pub_hex[:bytes]),
                    "y": nopad_b64(pub_hex[bytes:]),
                },
                'hash': hash,
                'point_size': point_size,
            }

    def send_signed_request(self, url, payload):
        '''
        Sends a JWS signed HTTP POST request to the ACME server and returns
        the response as dictionary
        https://tools.ietf.org/html/draft-ietf-acme-acme-10#section-6.2
        '''
        failed_tries = 0
        while True:
            protected = copy.deepcopy(self.jws_header)
            protected["nonce"] = self.directory.get_nonce()
            if self.version != 1:
                protected["url"] = url

            try:
                payload64 = nopad_b64(self.module.jsonify(payload).encode('utf8'))
                protected64 = nopad_b64(self.module.jsonify(protected).encode('utf8'))
            except Exception as e:
                raise ModuleFailException("Failed to encode payload / headers as JSON: {0}".format(e))

            openssl_sign_cmd = [self._openssl_bin, "dgst", "-{0}".format(self.key_data['hash']), "-sign", self.key]
            sign_payload = "{0}.{1}".format(protected64, payload64).encode('utf8')
            dummy, out, dummy = self.module.run_command(openssl_sign_cmd, data=sign_payload, check_rc=True, binary_data=True)

            if self.key_data['type'] == 'ec':
                dummy, der_out, dummy = self.module.run_command(
                    [self._openssl_bin, "asn1parse", "-inform", "DER"],
                    data=out, binary_data=True)
                expected_len = 2 * self.key_data['point_size']
                sig = re.findall(
                    r"prim:\s+INTEGER\s+:([0-9A-F]{1,%s})\n" % expected_len,
                    to_text(der_out, errors='surrogate_or_strict'))
                if len(sig) != 2:
                    raise ModuleFailException(
                        "failed to generate Elliptic Curve signature; cannot parse DER output: {0}".format(
                            to_text(der_out, errors='surrogate_or_strict')))
                sig[0] = (expected_len - len(sig[0])) * '0' + sig[0]
                sig[1] = (expected_len - len(sig[1])) * '0' + sig[1]
                out = binascii.unhexlify(sig[0]) + binascii.unhexlify(sig[1])

            data = {
                "protected": protected64,
                "payload": payload64,
                "signature": nopad_b64(to_bytes(out)),
            }
            if self.version == 1:
                data["header"] = self.jws_header
            data = self.module.jsonify(data)

            headers = {
                'Content-Type': 'application/jose+json',
            }
            resp, info = fetch_url(self.module, url, data=data, headers=headers, method='POST')
            result = {}
            try:
                content = resp.read()
            except AttributeError:
                content = info.get('body')

            if content:
                if info['content-type'].startswith('application/json') or 400 <= info['status'] < 600:
                    try:
                        result = self.module.from_json(content.decode('utf8'))
                        # In case of badNonce error, try again (up to 5 times)
                        # (https://tools.ietf.org/html/draft-ietf-acme-acme-09#section-6.6)
                        if (400 <= info['status'] < 600 and
                                result.get('type') == 'urn:ietf:params:acme:error:badNonce' and
                                failed_tries <= 5):
                            failed_tries += 1
                            continue
                    except ValueError:
                        raise ModuleFailException("Failed to parse the ACME response: {0} {1}".format(url, content))
                else:
                    result = content

            return result, info

    def set_account_uri(self, uri):
        '''
        Set account URI. For ACME v2, it needs to be used to sending signed
        requests.
        '''
        self.uri = uri
        if self.version != 1:
            self.jws_header.pop('jwk')
            self.jws_header['kid'] = self.uri

    def _new_reg(self, contact=None, agreement=None, terms_agreed=False):
        '''
        Registers a new ACME account. Returns True if the account was
        created and False if it already existed (e.g. it was not newly
        created).
        https://tools.ietf.org/html/draft-ietf-acme-acme-09#section-7.3
        '''
        contact = [] if contact is None else contact

        if self.version == 1:
            new_reg = {
                'resource': 'new-reg',
                'contact': contact
            }
            if agreement:
                new_reg['agreement'] = agreement
            else:
                new_reg['agreement'] = self.directory['meta']['terms-of-service']
            url = self.directory['new-reg']
        else:
            new_reg = {
                'contact': contact
            }
            if terms_agreed:
                new_reg['termsOfServiceAgreed'] = True
            url = self.directory['newAccount']

        result, info = self.send_signed_request(url, new_reg)
        if 'location' in info:
            self.set_account_uri(info['location'])

        if info['status'] in [200, 201]:
            # Account did not exist
            return True
        elif info['status'] == 409:
            # Account did exist
            return False
        else:
            raise ModuleFailException("Error registering: {0} {1}".format(info['status'], result))

    def init_account(self, contact, agreement=None, terms_agreed=False):
        '''
        Create or update an account on the ACME server. As the only way
        (without knowing an account URI) to test if an account exists
        is to try and create one with the provided account key, this
        method will always result in an account being present (except
        on error situations). If the account already exists, it will
        update the contact information. Return True in case something
        changed (account was created, contact info updated).
        https://tools.ietf.org/html/draft-ietf-acme-acme-09#section-7.3
        '''

        new_account = True
        changed = False
        if self.uri is not None:
            new_account = False
        else:
            new_account = self._new_reg(contact, agreement=agreement, terms_agreed=terms_agreed)
        if not new_account:
            # pre-existing account, get account data...
            data = {}
            if self.version == 1:
                data['resource'] = 'reg'
            result, info = self.send_signed_request(self.uri, data)
            if info['status'] < 200 or info['status'] >= 300:
                raise ModuleFailException("Error getting account data from {2}: {0} {1}".format(info['status'], result, self.uri))

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
                result, dummy = self.send_signed_request(self.uri, upd_reg)
                self.changed = True
                changed = True
        return new_account or changed
