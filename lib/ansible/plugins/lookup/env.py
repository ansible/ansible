# (c) 2012, Jan-Piet Mens <jpmens(at)gmail.com>
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

from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        options = {'allow_undefined': True, 'default': ''}

        # override options passed in
        options.update(kwargs)

        ret = []
        for term in terms:

            var = term.split()[0]
            envvar = os.getenv(var)

            if envvar is None:
                if options['allow_undefined']:
                    ret.append(options['default'])
                else:
                    raise AnsibleError('Undefined environment variable: %s' % var)
            else:
                ret.append(envvar)

        return ret
