# (c) 2012, Daniel Hokka Zakrisson <daniel@hozac.com>
# (c) 2013, Javier Candeira <javier@candeira.com>
# (c) 2013, Maykel Moya <mmoya@speedyrails.com>
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import string
import random

from string import ascii_letters, digits

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.parsing.splitter import parse_kv
from ansible.utils.encrypt import do_encrypt
from ansible.utils.path import makedirs_safe
from ansible.compat.six import text_type

from ansible.module_utils._text import to_bytes, to_native, to_text

DEFAULT_LENGTH = 20
VALID_PARAMS = frozenset(('length', 'encrypt', 'chars'))

def _parse_parameters(term):
    # Hacky parsing of params
    # See https://github.com/ansible/ansible-modules-core/issues/1968#issuecomment-136842156
    # and the first_found lookup For how we want to fix this later
    first_split = term.split(' ', 1)
    if len(first_split) <= 1:
        # Only a single argument given, therefore it's a path
        relpath = term
        params = dict()
    else:
        relpath = first_split[0]
        params = parse_kv(first_split[1])
        if '_raw_params' in params:
            # Spaces in the path?
            relpath = u' '.join((relpath, params['_raw_params']))
            del params['_raw_params']

            # Check that we parsed the params correctly
            if not term.startswith(relpath):
                # Likely, the user had a non parameter following a parameter.
                # Reject this as a user typo
                raise AnsibleError('Unrecognized value after key=value parameters given to password lookup')
        # No _raw_params means we already found the complete path when
        # we split it initially

    # Check for invalid parameters.  Probably a user typo
    invalid_params = frozenset(params.keys()).difference(VALID_PARAMS)
    if invalid_params:
        raise AnsibleError('Unrecognized parameter(s) given to password lookup: %s' % ', '.join(invalid_params))

    # Set defaults
    params['length'] = int(params.get('length', DEFAULT_LENGTH))
    params['encrypt'] = params.get('encrypt', None)

    params['chars'] = params.get('chars', None)
    if params['chars']:
        tmp_chars = []
        if u',,' in params['chars']:
            tmp_chars.append(u',')
        tmp_chars.extend(c for c in params['chars'].replace(u',,', u',').split(u',') if c)
        params['chars'] = tmp_chars
    else:
        # Default chars for password
        params['chars'] = [u'ascii_letters', u'digits', u".,:-_"]

    return relpath, params

def _random_password(length=DEFAULT_LENGTH, chars=None):
    '''
    Return a random password string of length containing only chars.
    NOTE: this was moved from the old ansible utils code, as nothing
          else appeared to use it.
    '''

    # hate how python implements asserts. Our text strategy says that we
    # should never be passing byte strings around unless the function
    # explicitly takes a byte string as its argument.  Therefore if we get
    # a byte string here it means that the problem is in the calling code.
    # Asserts would be perfect for this if they were disabled by default.
    # Alas, in python, they're active by default; only turned off if
    # python is run with optimization.
    chars = chars or to_text(C.DEFAULT_PASSWORD_CHARS)
    assert isinstance(chars, text_type), '%s (%s) is not a text_type' % (chars, type(chars))

    random_generator = random.SystemRandom()

    password = []
    while len(password) < length:
        new_char = random_generator.choice(chars)
        password.append(new_char)

    return u''.join(password)

def _random_salt():
    salt_chars_spec = to_text(ascii_letters + digits + './', errors='surrogate_or_strict')
    salt_chars = _gen_candidate_chars([salt_chars_spec])
    return _random_password(length=8, chars=salt_chars)

def _gen_candidate_chars(characters):
    '''Generate a string containing all valid chars as defined by char spec in arg 'characters'

    The input here is a list of character specs. The character specs are shorthand
    names for sets of characters like 'digits', 'ascii_letters', or 'punctuation'.

    The values of each char spec can be:
        - a name of an attribute in the 'strings' module ('digits' for example). The
        value of the attribute will be added to the candidate chars return value.
        - a string of characters. If the string isn't an attribute in 'string' module, the
        string will be directly added to the candidate chars.

    characters=['digits', '?|'] will match string.digits and add all ascii digits, and '?|'
    will add those chars directly. Return will be the string '0123456789?|'
    '''
    chars = []
    for chars_spec in characters:
        chars.append(to_text(getattr(string, to_native(chars_spec), chars_spec),
                            errors='surrogate_or_strict'))
    chars = u''.join(chars).replace(u'"', u'').replace(u"'", u'')
    return chars

def _create_password_file_dir(b_path):
    b_pathdir = os.path.dirname(b_path)

    try:
        makedirs_safe(b_pathdir, mode=0o700)
    except OSError as e:
        raise AnsibleError("cannot create the path for the password lookup: %s (error was %s)" % (b_pathdir, str(e)))

def _read_password_file(b_path):
    content = open(b_path, 'rb').read().rstrip()
    return content

def _parse_password(b_content):
    content = to_text(b_content, errors='surrogate_or_strict')
    password = content
    salt = None

    try:
        sep = content.rindex(' salt=')
    except ValueError:
        # No salt
        pass
    else:
        salt = password[sep + len(' salt='):]
        password = content[:sep]

    return content, password, salt

def _write_password_file(b_path, content):
    with open(b_path, 'wb') as f:
        os.chmod(b_path, 0o600)
        f.write(content)

def _format_content(password, salt, encrypt):
    if not encrypt:
        return password

    return u'%s salt=%s' % (password, salt)

def _read_or_create_password_file_dir(b_path):
    salt = None
    plaintext_password = None
    content = None

    if os.path.exists(b_path):
        b_file_content = _read_password_file(b_path)
        content, plaintext_password, salt = _parse_password(b_file_content)
    else:
        _create_password_file_dir(b_path)

    return content, plaintext_password, salt

def _update_content(plaintext_password, salt, params):
    if not salt:
        salt = _random_salt()

    # An empty string is a poor but valid plaintext_password
    if plaintext_password is None:
        chars = _gen_candidate_chars(params['chars'])
        plaintext_password = _random_password(length=params['length'],
                                              chars=chars)

    content = _format_content(password=plaintext_password,
                              salt=salt,
                              encrypt=params['encrypt'])

    return content, plaintext_password, salt

class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):
        ret = []

        for term in terms:
            relpath, params = _parse_parameters(term)
            path = self._loader.path_dwim(relpath)
            b_path = to_bytes(path, errors='surrogate_or_strict')

            # get password or create it if file doesn't exist
            content, plaintext_password, salt = _read_or_create_password_file_dir(b_path)
            content, plaintext_password, salt = _update_content(plaintext_password, salt, params)

            # save it
            b_content = to_bytes(content, errors='surrogate_or_strict') + b'\n'
            _write_password_file(b_path, b_content)

            if params['encrypt']:
                b_password = do_encrypt(plaintext_password, params['encrypt'],
                                       salt=to_bytes(salt, errors='surrogate_or_strict'))
                password = to_text(b_password, errors='surrogate_or_strict')
                ret.append(password)
            else:
                ret.append(plaintext_password)

        return ret
