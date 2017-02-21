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

from ansible import constants as C
from ansible.compat.six import text_type
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.parsing.splitter import parse_kv
from ansible.plugins.lookup import LookupBase
from ansible.utils.encrypt import do_encrypt
from ansible.utils.path import makedirs_safe


DEFAULT_LENGTH = 20
VALID_PARAMS = frozenset(('length', 'encrypt', 'chars'))


def _parse_parameters(term):
    """Hacky parsing of params

    See https://github.com/ansible/ansible-modules-core/issues/1968#issuecomment-136842156
    and the first_found lookup For how we want to fix this later
    """
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


def _read_password_file(b_path):
    """Read the contents of a password file and return it
    :arg b_path: A byte string containing the path to the password file
    :returns: a text string containing the contents of the password file or
        None if no password file was present.
    """
    content = None

    if os.path.exists(b_path):
        with open(b_path, 'rb') as f:
            b_content = f.read().rstrip()
        content = to_text(b_content, errors='surrogate_or_strict')

    return content


def _gen_candidate_chars(characters):
    '''Generate a string containing all valid chars as defined by ``characters``

    :arg characters: A list of character specs. The character specs are
        shorthand names for sets of characters like 'digits', 'ascii_letters',
        or 'punctuation' or a string to be included verbatim.

    The values of each char spec can be:

    * a name of an attribute in the 'strings' module ('digits' for example).
      The value of the attribute will be added to the candidate chars.
    * a string of characters. If the string isn't an attribute in 'string'
      module, the string will be directly added to the candidate chars.

    For example::

        characters=['digits', '?|']``

    will match ``string.digits`` and add all ascii digits.  ``'?|'`` will add
    the question mark and pipe characters directly. Return will be the string::

        u'0123456789?|'
    '''
    chars = []
    for chars_spec in characters:
        # getattr from string expands things like "ascii_letters" and "digits"
        # into a set of characters.
        chars.append(to_text(getattr(string, to_native(chars_spec), chars_spec),
                            errors='strict'))
    chars = u''.join(chars).replace(u'"', u'').replace(u"'", u'')
    return chars


def _random_password(length=DEFAULT_LENGTH, chars=C.DEFAULT_PASSWORD_CHARS):
    '''Return a random password string of length containing only chars

    :kwarg length: The number of characters in the new password.  Defaults to 20.
    :kwarg chars: The characters to choose from.  The default is all ascii
        letters, ascii digits, and these symbols ``.,:-_``

    .. note: this was moved from the old ansible utils code, as nothing
        else appeared to use it.
    '''
    assert isinstance(chars, text_type), '%s (%s) is not a text_type' % (chars, type(chars))

    random_generator = random.SystemRandom()

    password = []
    while len(password) < length:
        new_char = random_generator.choice(chars)
        password.append(new_char)

    return u''.join(password)


def _random_salt():
    """Return a text string suitable for use as a salt for the hash functions we use to encrypt passwords.
    """
    # Note passlib salt values must be pure ascii so we can't let the user
    # configure this
    salt_chars = _gen_candidate_chars(['ascii_letters', 'digits', './'])
    return _random_password(length=8, chars=salt_chars)


def _parse_content(content):
    '''parse our password data format into password and salt

    :arg content: The data read from the file
    :returns: password and salt
    '''
    password = content
    salt = None

    salt_slug = u' salt='
    try:
        sep = content.rindex(salt_slug)
    except ValueError:
        # No salt
        pass
    else:
        salt = password[sep + len(salt_slug):]
        password = content[:sep]

    return password, salt


def _format_content(password, salt, encrypt=True):
    """Format the password and salt for saving
    :arg password: the plaintext password to save
    :arg salt: the salt to use when encrypting a password
    :arg encrypt: Whether the user requests that this password is encrypted.
        Note that the password is saved in clear.  Encrypt just tells us if we
        must save the salt value for idempotence.  Defaults to True.
    :returns: a text string containing the formatted information

    .. warning:: Passwords are saved in clear.  This is because the playbooks
        expect to get cleartext passwords from this lookup.
    """
    if not encrypt and not salt:
        return password

    # At this point, the calling code should have assured us that there is a salt value.
    assert salt, '_format_content was called with encryption requested but no salt value'

    return u'%s salt=%s' % (password, salt)


def _write_password_file(b_path, content):
    b_pathdir = os.path.dirname(b_path)
    makedirs_safe(b_pathdir, mode=0o700)

    with open(b_path, 'wb') as f:
        os.chmod(b_path, 0o600)
        b_content = to_bytes(content, errors='surrogate_or_strict') + b'\n'
        f.write(b_content)


class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):
        ret = []

        for term in terms:
            relpath, params = _parse_parameters(term)
            path = self._loader.path_dwim(relpath)
            b_path = to_bytes(path, errors='surrogate_or_strict')
            chars = _gen_candidate_chars(params['chars'])

            changed = False
            content = _read_password_file(b_path)

            if content is None or b_path == to_bytes('/dev/null'):
                plaintext_password = _random_password(params['length'], chars)
                salt = None
                changed = True
            else:
                plaintext_password, salt = _parse_content(content)

            if params['encrypt'] and not salt:
                changed = True
                salt = _random_salt()

            if changed and b_path != to_bytes('/dev/null'):
                content = _format_content(plaintext_password, salt, encrypt=params['encrypt'])
                _write_password_file(b_path, content)

            if params['encrypt']:
                password = do_encrypt(plaintext_password, params['encrypt'], salt=salt)
                ret.append(password)
            else:
                ret.append(plaintext_password)

        return ret
