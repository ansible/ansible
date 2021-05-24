# (c) 2012, Daniel Hokka Zakrisson <daniel@hozac.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    name: file
    author: Daniel Hokka Zakrisson (!UNKNOWN) <daniel@hozac.com>
    version_added: "0.9"
    short_description: read file contents
    description:
        - This lookup returns the contents from a file on the Ansible controller's file system.
    options:
      _terms:
        description: path(s) of files to read
        required: True
      rstrip:
        description: whether or not to remove whitespace from the ending of the looked-up file
        type: bool
        required: False
        default: True
      lstrip:
        description: whether or not to remove whitespace from the beginning of the looked-up file
        type: bool
        required: False
        default: False
      raw:
        description:
            - Whether or not to automatically use vault and/or variable loading
        type: bool
        required: False
        default: False
        version_added: '2.12'
    notes:
      - By default, if read in variable context, the file can be interpreted as YAML or JSON if the content is valid to the parser
      - This lookup does not understand 'globing', use the fileglob lookup instead
      - There is no support for binary content, everything read will be transformed to Python unicode text internally
"""

EXAMPLES = """
- debug: msg="the value of foo.txt is {{lookup('file', '/etc/foo.txt') }}"

- name: display multiple file contents
  debug:
    msg: '{{ lookup("file", "/path/to/foo.txt", "bar.txt", "/path/to/biz.txt") }}'
"""

RETURN = """
  _raw:
    description:
      - content of file(s)
    type: list
    elements: str
"""

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils._text import to_text, to_native
from ansible.utils.display import Display

display = Display()


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        ret = []
        self.set_options(var_options=variables, direct=kwargs)

        for term in terms:
            display.debug("File lookup term: %s" % term)

            # Find the file in the expected search path
            lookupfile = self.find_file_in_search_path(variables, 'files', term)
            display.vvvv(u"File lookup using %s as file" % lookupfile)
            try:
                if lookupfile:
                    if self.get_option('raw'):
                        try:
                            with open(lookupfile, 'rb') as f:
                                b_contents = f.read()
                        except (IOError, OSError) as e:
                            raise AnsibleError("Unable to read file (%s) contents: %s" % (lookupfile, to_native(e)))
                    else:
                        b_contents, show_data = self._loader._get_file_contents(lookupfile)

                    contents = to_text(b_contents, errors='surrogate_or_strict')
                    if self.get_option('lstrip'):
                        contents = contents.lstrip()
                    if self.get_option('rstrip'):
                        contents = contents.rstrip()
                    ret.append(contents)
                else:
                    raise AnsibleParserError()
            except AnsibleParserError:
                raise AnsibleError("could not locate file in lookup: %s" % term)

        return ret
