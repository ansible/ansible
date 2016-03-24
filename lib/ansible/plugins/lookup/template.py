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

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.utils.unicode import to_unicode

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        convert_data_p = kwargs.get('convert_data', True)
        basedir = self.get_basedir(variables)

        ret = []

        for term in terms:
            display.debug("File lookup term: %s" % term)

            lookupfile = self._loader.path_dwim_relative(basedir, 'templates', term)
            display.vvvv("File lookup using %s as file" % lookupfile)
            if lookupfile and os.path.exists(lookupfile):
                with open(lookupfile, 'r') as f:
                    template_data = to_unicode(f.read())

                    searchpath = [self._loader._basedir, os.path.dirname(lookupfile)]
                    if 'role_path' in variables:
                        searchpath.insert(1, C.DEFAULT_ROLES_PATH)
                        searchpath.insert(1, variables['role_path'])

                    self._templar.environment.loader.searchpath = searchpath
                    res = self._templar.template(template_data, preserve_trailing_newlines=True,convert_data=convert_data_p)
                    ret.append(res)
            else:
                raise AnsibleError("the template file %s could not be found for the lookup" % term)

        return ret
