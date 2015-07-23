# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.template import Templar

class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        if not isinstance(terms, list):
            terms = [ terms ]

        ret = []

        templar = Templar(loader=self._loader, variables=variables)

        if 'role_path' in variables:
            basedir = variables['role_path']
        else:
            basedir = self._loader.get_basedir()

        for term in terms:
            self._display.debug("File lookup term: %s" % term)

            lookupfile = self._loader.path_dwim_relative(basedir, 'templates', term)
            self._display.vvvv("File lookup using %s as file" % lookupfile)
            if lookupfile and os.path.exists(lookupfile):
                with open(lookupfile, 'r') as f:
                    template_data = f.read()
                    res = templar.template(template_data, preserve_trailing_newlines=True)
                    ret.append(res)
            else:
                raise AnsibleError("the template file %s could not be found for the lookup" % term)

        return ret
