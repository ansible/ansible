# -*- coding: utf-8 -*-
# (c) 2019, Daryl Banttari <dbanttari@gmail.com>
#
# This file is part of Ansible
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: hmac
    author:
        - Daryl Banttari <dbanttari@gmail.com>
    version_added: 2.9
    requirements:
        - base64
        - hmac
        - hashlib
    short_description: Calculates an HMAC authorization token
    description:
        - This lookup calculates an HMAC authorization token
        - Result is a base64-encoded string
    options:
        _terms:
            description: List of strings to calculate HMAC signatures
            required: True
        secret:
            description: Secret to use to create the signature`
            required: True
        encoding:
            description: Encoding of the secret.  Can be any Python-valid string encoding or "base64"
            required: false
            default: utf-8
        algorithm:
            description: Hash algorithm to use (see https://docs.python.org/3/library/hashlib.html)
            required: false
            default: sha256
    notes:
        - If HMACs from different secrets are needed, you'll need to make multiple calls to this lookup
"""

EXAMPLE = """
- name: Calculate HMAC using password
  debug:
    msg: "{{ lookup('hmac', 'string_to_be_signed', secret=hmac_secret }}"

- name: Calculate HMAC using base64-encoded password
  debug:
    msg: "{{ lookup('hmac', 'string_to_be_signed', secret=hmac_secret, encoding='base64') }}"

- name: Calculate SHA512 HMAC using base64-encoded password
  debug:
    msg: "{{ lookup('hmac', 'string_to_be_signed', secret=hmac_secret, encoding='base64', algorithm='sha512') }}"
"""

RETURN = """
  _raw:
    description: base64-encoded hmac signature
"""

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from base64 import b64encode, b64decode
import hmac
import hashlib
from inspect import getmembers

class LookupModule(LookupBase):

    def run(self, terms, inject=None, variables=None, **kwargs):
        try:
            if isinstance(terms, str):
                terms = [terms]
            secret = kwargs.get('secret')
            encoding = kwargs.get('encoding', 'utf-8')
            if encoding == 'base64':
                secret_bytes = b64decode(secret)
            else:
                secret_bytes = secret.encode(encoding)
            algorithm = kwargs.get('algorithm', 'sha256').lower()
            # was looking at using `inspect` to get a reference without this mess
            # (python2's hmac method doesn't accept a string argument for hasher)
            # but that was leading to some non-trivial code complication, so with
            # deference to the KISS principle:
            if algorithm == 'md5':
                hasher = hashlib.md5
            elif algorithm == 'sha1':
                hasher = hashlib.sha1
            elif algorithm == 'sha224':
                hasher = hashlib.sha224
            elif algorithm == 'sha256':
                hasher = hashlib.sha256
            elif algorithm == 'sha384':
                hasher = hashlib.sha384
            elif algorithm == 'sha512':
                hasher = hashlib.sha512
            else:
                raise Exception("Unknown hash method: {}".format(algorithm))
            ret = []
            for term in terms:
                mac = hmac.new(secret_bytes, term.encode(), hasher).digest()
                mac_b64 = b64encode(mac).decode('utf-8')
                ret.append(mac_b64)
            return ret
        except Exception as e:
            raise AnsibleError('HMAC Failed: {}'.format(str(e)))
