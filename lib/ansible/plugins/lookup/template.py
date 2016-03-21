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

import datetime
import os
import pwd
import time

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.utils.unicode import to_bytes, to_unicode

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

                    try:
                        template_uid = pwd.getpwuid(os.stat(lookupfile).st_uid).pw_name
                    except:
                        template_uid = os.stat(lookupfile).st_uid

                    temp_vars = self._templar._available_variables.copy()

                    temp_vars['template_host']     = os.uname()[1]
                    temp_vars['template_path']     = lookupfile
                    temp_vars['template_mtime']    = datetime.datetime.fromtimestamp(os.path.getmtime(lookupfile))
                    temp_vars['template_uid']      = template_uid
                    temp_vars['template_fullpath'] = os.path.abspath(lookupfile)
                    temp_vars['template_run_date'] = datetime.datetime.now()

                    managed_default = C.DEFAULT_MANAGED_STR
                    managed_str = managed_default.format(
                        host = temp_vars['template_host'],
                        uid  = temp_vars['template_uid'],
                        file = to_bytes(temp_vars['template_path'])
                    )
                    temp_vars['ansible_managed'] = time.strftime(
                        managed_str,
                        time.localtime(os.path.getmtime(lookupfile))
                    )

                    searchpath = [self._loader._basedir, os.path.dirname(lookupfile)]
                    if 'role_path' in variables:
                        searchpath.insert(1, C.DEFAULT_ROLES_PATH)
                        searchpath.insert(1, variables['role_path'])

                    self._templar.environment.loader.searchpath = searchpath

                    old_vars = self._templar._available_variables
                    self._templar.set_available_variables(temp_vars)
                    res = self._templar.template(template_data, preserve_trailing_newlines=True,convert_data=convert_data_p)
                    self._templar.set_available_variables(old_vars)
                    ret.append(res)
            else:
                raise AnsibleError("the template file %s could not be found for the lookup" % term)

        return ret
