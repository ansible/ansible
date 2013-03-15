# (c) 2012, Daniel Hokka Zakrisson <daniel@hozac.com>
# (c) 2013, Javie Candeira <javier@candeira.com>
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

from ansible import utils, errors
import os
import errno
import random
from string import ascii_uppercase, ascii_lowercase, digits


class LookupModule(object):

    LENGTH = 20

    def __init__(self, length=None, basedir=None, **kwargs):
        self.basedir = basedir

    def run(self, terms, **kwargs):
        if isinstance(terms, basestring):
            terms = [ terms ]
        ret = []

        for term in terms:
            # you can't have escaped spaces in yor pathname
            params = term.split()
            relpath = params[0]
            length = LookupModule.LENGTH

            # get non-default length parameter if specified
            if len(params) > 1:
                try:
                    name, length = params[1].split('=')
                    assert(name.startswith("length"))
                    length = int(length)
                except (ValueError, AssertionError) as e:
                    raise errors.AnsibleError(e)

            # get password or create it if file doesn't exist
            path = utils.path_dwim(self.basedir, relpath)
            if not os.path.exists(path):
                pathdir = os.path.dirname(path)
                if not os.path.isdir(pathdir):
                    os.makedirs(pathdir)
                chars = ascii_uppercase + ascii_lowercase + digits + ".,:-_"
                password = ''.join(random.choice(chars) for _ in range(length))
                with open(path, 'w') as f:
                    f.write(password)
            ret.append(open(path).read().rstrip())

        return ret

