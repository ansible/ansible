# (c) 2016, Koen Smets <koen.smets@gmail.com>
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
import subprocess

from distutils.util import strtobool

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.parsing.splitter import parse_kv

DEFAULT_LENGTH = 16
DEFAULT_NO_SYMBOLS = 'True'
VALID_PARAMS = frozenset(('length', 'no-symbols'))


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
    params['no-symbols'] = bool(strtobool(params.get('no-symbols', DEFAULT_NO_SYMBOLS)))

    return relpath, params


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):
        password_store_dir = os.path.expanduser(os.getenv('PASSWORD_STORE_DIR', '~/.password-store'))

        ret = []
        for term in terms:
            relpath, params = _parse_parameters(term)

            # create password if file doesn't exist 
            path = os.path.join(password_store_dir, relpath + '.gpg')
            if not os.path.exists(path):
                p = subprocess.Popen('pass generate %s %s %d' % ('-n' if params['no-symbols'] else '', relpath, params['length']), shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                (stdout, stderr) = p.communicate()
                if p.returncode != 0:
                     raise AnsibleError("lookup_plugin.pass(%s) returned %d" % (term, p.returncode))
            
            # get password
            p = subprocess.Popen('pass %s' % relpath, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            (stdout, stderr) = p.communicate()
            if p.returncode == 0:
                ret.append(stdout.decode("utf-8").rstrip())
            else:
                raise AnsibleError("lookup_plugin.pass(%s) returned %d" % (term, p.returncode))
        return ret
