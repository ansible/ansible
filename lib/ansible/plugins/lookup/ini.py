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

import os
import re
from collections import MutableSequence
from io import StringIO

from ansible.errors import AnsibleError
from ansible.module_utils.six.moves import configparser
from ansible.module_utils._text import to_bytes, to_text
from ansible.plugins.lookup import LookupBase


def _parse_params(term):
    '''Safely split parameter term to preserve spaces'''

    keys = ['key', 'type', 'section', 'file', 're', 'default', 'encoding']
    params = {}
    for k in keys:
        params[k] = ''

    thiskey = 'key'
    for idp, phrase in enumerate(term.split()):
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

        self.cp = configparser.ConfigParser()

        ret = []
        for term in terms:
            params = _parse_params(term)
            key = params[0]

            paramvals = {
                'file': 'ansible.ini',
                're': False,
                'default': None,
                'section': "global",
                'type': "ini",
                'encoding': 'utf-8',
            }

            # parameters specified?
            try:
                for param in params[1:]:
                    name, value = param.split('=')
                    assert(name in paramvals)
                    paramvals[name] = value
            except (ValueError, AssertionError) as e:
                raise AnsibleError(e)

            # Retrieve file path
            path = self.find_file_in_search_path(variables, 'files', paramvals['file'])

            # Create StringIO later used to parse ini
            config = StringIO()
            # Special case for java properties
            if paramvals['type'] == "properties":
                config.write(u'[java_properties]\n')
                paramvals['section'] = 'java_properties'

            # Open file using encoding
            contents, show_data = self._loader._get_file_contents(path)
            contents = to_text(contents, errors='surrogate_or_strict', encoding=paramvals['encoding'])
            config.write(contents)
            config.seek(0, os.SEEK_SET)

            self.cp.readfp(config)
            var = self.get_value(key, paramvals['section'], paramvals['default'], paramvals['re'])
            if var is not None:
                if isinstance(var, MutableSequence):
                    for v in var:
                        ret.append(v)
                else:
                    ret.append(var)
        return ret
