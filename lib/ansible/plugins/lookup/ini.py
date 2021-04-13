# (c) 2015, Yannig Perre <yannig.perre(at)gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    name: ini
    author: Yannig Perre (!UNKNOWN) <yannig.perre(at)gmail.com>
    version_added: "2.0"
    short_description: read data from a ini file
    description:
      - "The ini lookup reads the contents of a file in INI format C(key1=value1).
        This plugin retrieves the value on the right side after the equal sign C('=') of a given section C([section])."
      - "You can also read a property file which - in this case - does not contain section."
    options:
      _terms:
        description: The key(s) to look up
        required: True
      type:
        description: Type of the file. 'properties' refers to the Java properties files.
        default: 'ini'
        choices: ['ini', 'properties']
      file:
        description: Name of the file to load.
        default: 'ansible.ini'
      section:
        default: global
        description: Section where to lookup the key.
      re:
        default: False
        type: boolean
        description: Flag to indicate if the key supplied is a regexp.
      encoding:
        default: utf-8
        description:  Text encoding to use.
      default:
        description: Return value if the key is not in the ini file.
        default: ''
"""

EXAMPLES = """
- debug: msg="User in integration is {{ lookup('ini', 'user', section='integration', file='users.ini') }}"

- debug: msg="User in production  is {{ lookup('ini', 'user', section='production',  file='users.ini') }}"

- debug: msg="user.name is {{ lookup('ini', 'user.name', type='properties', file='user.properties') }}"

- debug:
    msg: "{{ item }}"
  loop: "{{q('ini', '.*', section='section1', file='test.ini', re=True)}}"
"""

RETURN = """
_raw:
  description:
    - value(s) of the key(s) in the ini file
  type: list
  elements: str
"""

import os
import re

from io import StringIO
from collections import defaultdict

from ansible.errors import AnsibleLookupError
from ansible.module_utils.six.moves import configparser
from ansible.module_utils._text import to_bytes, to_text, to_native
from ansible.module_utils.common._collections_compat import MutableSequence
from ansible.plugins.lookup import LookupBase


def _parse_params(term, paramvals):
    '''Safely split parameter term to preserve spaces'''

    # TODO: deprecate this method
    valid_keys = paramvals.keys()
    params = defaultdict(lambda: '')

    # TODO: check kv_parser to see if it can handle spaces this same way
    keys = []
    thiskey = 'key'  # initialize for 'lookup item'
    for idp, phrase in enumerate(term.split()):

        # update current key if used
        if '=' in phrase:
            for k in valid_keys:
                if ('%s=' % k) in phrase:
                    thiskey = k

        # if first term or key does not exist
        if idp == 0 or not params[thiskey]:
            params[thiskey] = phrase
            keys.append(thiskey)
        else:
            # append to existing key
            params[thiskey] += ' ' + phrase

    # return list of values
    return [params[x] for x in keys]


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

        self.set_options(var_options=variables, direct=kwargs)
        paramvals = self.get_options()

        self.cp = configparser.ConfigParser()

        ret = []
        for term in terms:

            key = term
            # parameters specified?
            if '=' in term or ' ' in term.strip():
                self._deprecate_inline_kv()
                params = _parse_params(term, paramvals)
                try:
                    for param in params:
                        if '=' in param:
                            name, value = param.split('=')
                            if name not in paramvals:
                                raise AnsibleLookupError('%s is not a valid option.' % name)
                            paramvals[name] = value
                        elif key == term:
                            # only take first, this format never supported multiple keys inline
                            key = param
                except ValueError as e:
                    # bad params passed
                    raise AnsibleLookupError("Could not use '%s' from '%s': %s" % (param, params, to_native(e)), orig_exc=e)

            # TODO: look to use cache to avoid redoing this for every term if they use same file
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
