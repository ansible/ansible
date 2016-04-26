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
            relpath = ' '.join((relpath, params['_raw_params']))
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
        if ',,' in params['chars']:
            tmp_chars.append(u',')
        tmp_chars.extend(c for c in params['chars'].replace(',,', ',').split(',') if c)
        params['chars'] = tmp_chars
    else:
        # Default chars for password
        params['chars'] = ['ascii_letters', 'digits', ".,:-_"]

    return relpath, params


class LookupModule(LookupBase):

    def random_password(self, length=DEFAULT_LENGTH, chars=C.DEFAULT_PASSWORD_CHARS):
        '''
        Return a random password string of length containing only chars.
        NOTE: this was moved from the old ansible utils code, as nothing
              else appeared to use it.
        '''

        password = []
        while len(password) < length:
            new_char = os.urandom(1)
            if new_char in chars:
                password.append(new_char)

        return ''.join(password)

    def random_salt(self):
        salt_chars = ascii_letters + digits + './'
        return self.random_password(length=8, chars=salt_chars)

    def run(self, terms, variables, **kwargs):

        ret = []

        for term in terms:
            relpath, params = _parse_parameters(term)

            # get password or create it if file doesn't exist
            path = self._loader.path_dwim(relpath)
            if not os.path.exists(path):
                pathdir = os.path.dirname(path)
                try:
                    makedirs_safe(pathdir, mode=0o700)
                except OSError as e:
                    raise AnsibleError("cannot create the path for the password lookup: %s (error was %s)" % (pathdir, str(e)))

                chars = "".join(getattr(string, c, c) for c in params['chars']).replace('"', '').replace("'", '')
                password = ''.join(random.choice(chars) for _ in range(params['length']))

                if params['encrypt'] is not None:
                    salt = self.random_salt()
                    content = '%s salt=%s' % (password, salt)
                else:
                    content = password
                with open(path, 'w') as f:
                    os.chmod(path, 0o600)
                    f.write(content + '\n')
            else:
                content = open(path).read().rstrip()

                password = content
                salt = None
                if params['encrypt'] is not None:
                    try:
                        sep = content.rindex(' ')
                    except ValueError:
                        # No salt
                        pass
                    else:
                        salt_field = content[sep + 1:]
                        if salt_field.startswith('salt='):
                            password = content[:sep]
                            salt = salt_field[len('salt='):]

                    # crypt requested, add salt if missing
                    if not salt:
                        salt = self.random_salt()
                        content = '%s salt=%s' % (password, salt)
                        with open(path, 'w') as f:
                            os.chmod(path, 0o600)
                            f.write(content + '\n')

            if params['encrypt']:
                password = do_encrypt(password, params['encrypt'], salt=salt)

            ret.append(password)

        return ret
