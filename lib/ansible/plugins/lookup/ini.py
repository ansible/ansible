# (c) 2015, Yannig Perre <yannig.perre(at)gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
    name: ini
    author: Yannig Perre (!UNKNOWN) <yannig.perre(at)gmail.com>
    version_added: "2.0"
    short_description: read data from an ini file
    description:
      - "The ini lookup reads the contents of a file in INI format C(key1=value1).
        This plugin retrieves the value on the right side after the equal sign C('=') of a given section C([section])."
      - "You can also read a property file which - in this case - does not contain section."
    options:
      _terms:
        description: The key(s) to look up.
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
      case_sensitive:
        description:
          Whether key names read from O(file) should be case sensitive. This prevents
          duplicate key errors if keys only differ in case.
        default: False
        version_added: '2.12'
      allow_no_value:
        description:
        - Read an ini file which contains key without value and without '=' symbol.
        type: bool
        default: False
        aliases: ['allow_none']
        version_added: '2.12'
      interpolation:
        description:
          Allows for interpolation of values, see https://docs.python.org/3/library/configparser.html#configparser.BasicInterpolation
        type: bool
        default: True
        version_added: '2.18'
    seealso:
      - ref: playbook_task_paths
        description: Search paths used for relative files.
"""

EXAMPLES = """
- ansible.builtin.debug: msg="User in integration is {{ lookup('ansible.builtin.ini', 'user', section='integration', file='users.ini') }}"

- ansible.builtin.debug: msg="User in production  is {{ lookup('ansible.builtin.ini', 'user', section='production',  file='users.ini') }}"

- ansible.builtin.debug: msg="user.name is {{ lookup('ansible.builtin.ini', 'user.name', type='properties', file='user.properties') }}"

- ansible.builtin.debug:
    msg: "{{ item }}"
  loop: "{{ q('ansible.builtin.ini', '.*', section='section1', file='test.ini', re=True) }}"

- name: Read an ini file with allow_no_value
  ansible.builtin.debug:
    msg: "{{ lookup('ansible.builtin.ini', 'user', file='mysql.ini', section='mysqld', allow_no_value=True) }}"
"""

RETURN = """
_raw:
  description:
    - value(s) of the key(s) in the ini file
  type: list
  elements: str
"""

import configparser
import os
import re

from io import StringIO
from collections import defaultdict
from collections.abc import MutableSequence

from ansible.errors import AnsibleError
from ansible.module_utils.common.text.converters import to_native
from ansible.plugins.lookup import LookupBase


def _parse_params(term, paramvals):
    """Safely split parameter term to preserve spaces"""

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

        self.cp = configparser.ConfigParser(
            allow_no_value=paramvals.get('allow_no_value', paramvals.get('allow_none')),
            interpolation=configparser.BasicInterpolation() if paramvals.get('interpolation') else None,
        )
        if paramvals['case_sensitive']:
            self.cp.optionxform = to_native

        ret = []
        for term in terms:

            key = term
            # parameters specified?
            if '=' in term or ' ' in term.strip():
                self._deprecate_inline_kv()
                params = _parse_params(term, paramvals)
                param = None
                try:
                    updated_key = False
                    updated_options = False
                    for param in params:
                        if '=' in param:
                            name, value = param.split('=')
                            if name not in paramvals:
                                raise AnsibleError(f"{name!r} is not a valid option.")
                            self.set_option(name, value)
                            updated_options = True
                        elif key == term:
                            # only take first, this format never supported multiple keys inline
                            key = param
                            updated_key = True
                    if updated_options:
                        paramvals = self.get_options()
                except ValueError as ex:
                    # bad params passed
                    raise ValueError(f"Could not use {param!r} from {params!r}.") from ex
                if not updated_key:
                    raise ValueError(f"No key to look up was provided as first term within string inline options: {term}")
                    # only passed options in inline string

            # TODO: look to use cache to avoid redoing this for every term if they use same file
            # Retrieve file path
            path = self.find_file_in_search_path(variables, 'files', paramvals['file'])

            # Create StringIO later used to parse ini
            config = StringIO()
            # Special case for java properties
            if paramvals['type'] == "properties":
                config.write(u'[java_properties]\n')
                paramvals['section'] = 'java_properties'

            contents = self._loader.get_text_file_contents(path, encoding=paramvals['encoding'])
            config.write(contents)
            config.seek(0, os.SEEK_SET)

            try:
                self.cp.read_file(config)
            except configparser.DuplicateOptionError as ex:
                raise ValueError(f"Duplicate option in {paramvals['file']!r}.") from ex

            try:
                var = self.get_value(key, paramvals['section'], paramvals['default'], paramvals['re'])
            except configparser.NoSectionError:
                raise ValueError(f"No section {paramvals['section']!r} in {paramvals['file']!r}.") from None

            if var is not None:
                if isinstance(var, MutableSequence):
                    for v in var:
                        ret.append(v)
                else:
                    ret.append(var)

        return ret
