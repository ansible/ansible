# (c) 2015, Yannig Perre <yannig.perre(at)gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: ini
    author: Yannig Perre <yannig.perre(at)gmail.com>
    version_added: "2.0"
    short_description: read data from a ini file
    description:
      - "The ini lookup reads the contents of a file in INI format C(key1=value1).
        This plugin retrieve the value on the right side after the equal sign C('=') of a given section C([section])."
      - "You can also read a property file which - in this case - does not contain section."
    options:
      _terms:
        description: they key(s) too look up
        required: True
    type:
      description: ini Type of the file. 'properties' refers to the Java properties files.
      default: 'ini'
      choices: ['ini', 'properties']
    file:
      description: Name of the file to load
      default: ansible.ini
    section:
      default: global
      description: section where to lookup for key.
    re:
      default: False
      type: boolean
      description:  Flag to indicate if the key supplied is a regexp.
    encoding:
      default: utf-8
      description:  Text encoding to use.
    default:
      description: return value if the key is not in the ini file
      default: ''
"""

EXAMPLES = """
- debug: msg="User in integration is {{ lookup('ini', 'user section=integration file=users.ini') }}"

- debug: msg="User in production  is {{ lookup('ini', 'user section=production  file=users.ini') }}"

- debug: msg="user.name is {{ lookup('ini', 'user.name type=properties file=user.properties') }}"

- debug:
    msg: "{{ item }}"
  with_ini:
    - value[1-2]
    - section: section1
    - file: "lookup.ini"
    - re: true
"""

RETURN = """
_raw:
  description:
    - value(s) of the key(s) in the ini file
"""
import os
import re
from collections import MutableSequence
from io import StringIO

from ansible.errors import AnsibleError, AnsibleAssertionError
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
                    if name not in paramvals:
                        raise AnsibleAssertionError('%s not in paramvals' % name)
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
