# (c) 2012, Daniel Hokka Zakrisson <daniel@hozac.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: file
    author: Daniel Hokka Zakrisson <daniel@hozac.com>
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
      encodings:
        description: encoding types of files to be read
        default: ['utf-8', 'utf-16']
        type: list
    notes:
      - if read in variable context, the file can be interpreted as YAML if the content is valid to the parser.
      - this lookup does not understand 'globing', use the fileglob lookup instead.
"""

EXAMPLES = """
- debug: msg="the value of foo.txt is {{lookup('file', '/etc/foo.txt') }}"

- debug: msg="the value of foo.txt is {{ lookup('file', '/tmp/test.sql', encodings=['utf-8', 'utf-16', 'utf-32'] }}"

- name: display multiple file contents
  debug: var=item
  with_file:
    - "/path/to/foo.txt"
    - "bar.txt"  # will be looked in files/ dir relative to play or in role
    - "/path/to/biz.txt"
"""

RETURN = """
  _raw:
    description:
      - content of file(s)
"""

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils._text import to_text
from ansible.utils.display import Display

display = Display()

def attempt_decode(b_contents, encodings):
    """
    Attempts to decode content using passed encoding types.

    Raises AnsibleError if all attempted encoding types fail.

    Returns decoded contetn.
    """
    decode_errors = list()
    for encoding in encodings:
        try:
            contents = to_text(b_contents,
                               encoding=encoding,
                               errors='surrogate_or_strict')
        except UnicodeDecodeError as e:
            decode_errors.append(e.encoding)
        else:
            return contents

    raise AnsibleError(
          'Failed to decode file using [{encoding_types}] encoding types.'
          .format(encoding_types=', '.join(decode_errors))
    )


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        ret = []

        for term in terms:
            display.debug("File lookup term: %s" % term)

            # Find the file in the expected search path
            lookupfile = self.find_file_in_search_path(variables, 'files', term)
            display.vvvv(u"File lookup using %s as file" % lookupfile)
            try:
                if lookupfile:
                    b_contents, show_data = self._loader._get_file_contents(lookupfile)
                    encodings = kwargs.get('encodings', ['utf-8', 'utf-16'])
                    contents = attempt_decode(b_contents, encodings)
                    if kwargs.get('lstrip', False):
                        contents = contents.lstrip()
                    if kwargs.get('rstrip', True):
                        contents = contents.rstrip()
                    ret.append(contents)
                else:
                    raise AnsibleParserError()
            except AnsibleParserError:
                raise AnsibleError("could not locate file in lookup: %s" % term)

        return ret
