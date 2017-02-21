# (c) 2015, Yannig Perre <yannig.perre(at)gmail.com>
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

from io import StringIO
import os
import re

from ansible.compat.six.moves import configparser
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils._text import to_bytes, to_text


def _parse_params(term):
    '''Safely split parameter term to preserve spaces'''

    keys = ['key', 'type', 'section', 'file', 're', 'default']
    params = {}
    for k in keys:
        params[k] = ''

    thiskey = 'key'
    for idp,phrase in enumerate(term.split()):
        for k in keys:
            if ('%s=' % k) in phrase:
                thiskey = k
        if idp == 0 or not params[thiskey]:
            params[thiskey] = phrase
        else:
            params[thiskey] += ' ' + phrase

    rparams = [params[x] for x in keys if params[x]]
    return rparams


class LookupModule(LookupBase):

    def read_properties(self, filename, key, dflt, is_regexp):
        config = StringIO()
        current_cfg_file = open(to_bytes(filename, errors='surrogate_or_strict'), 'rb')

        config.write(u'[java_properties]\n' + to_text(current_cfg_file.read(), errors='surrogate_or_strict'))
        config.seek(0, os.SEEK_SET)
        self.cp.readfp(config)
        return self.get_value(key, 'java_properties', dflt, is_regexp)

    def read_ini(self, filename, key, section, dflt, is_regexp):
        self.cp.readfp(open(to_bytes(filename, errors='surrogate_or_strict')))
        return self.get_value(key, section, dflt, is_regexp)

    def get_value(self, key, section, dflt, is_regexp):
        # Retrieve all values from a section using a regexp
        if is_regexp:
            return [v for k, v in self.cp.items(section) if re.match(key, k)]
        value = None
        # Retrieve a single value
        try:
            value = self.cp.get(section, key)
        except configparser.NoOptionError:
            return dflt
        return value

    def run(self, terms, variables=None, **kwargs):

        basedir = self.get_basedir(variables)
        self.basedir = basedir
        self.cp      = configparser.ConfigParser()

        ret = []
        for term in terms:
            params = _parse_params(term)
            key = params[0]

            paramvals = {
                'file'     : 'ansible.ini',
                're'       : False,
                'default'  : None,
                'section'  : "global",
                'type'     : "ini",
            }

            # parameters specified?
            try:
                for param in params[1:]:
                    name, value = param.split('=')
                    assert(name in paramvals)
                    paramvals[name] = value
            except (ValueError, AssertionError) as e:
                raise AnsibleError(e)

            path = self.find_file_in_search_path(variables, 'files', paramvals['file'])
            if paramvals['type'] == "properties":
                var = self.read_properties(path, key, paramvals['default'], paramvals['re'])
            else:
                var = self.read_ini(path, key, paramvals['section'], paramvals['default'], paramvals['re'])
            if var is not None:
                if type(var) is list:
                    for v in var:
                        ret.append(v)
                else:
                    ret.append(var)
        return ret
