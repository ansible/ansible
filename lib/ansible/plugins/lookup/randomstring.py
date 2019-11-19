from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
        lookup: randomstring
        author: Jason Neurohr <jason@jasonneurohr.com>
        version_added: "2.10"
        short_description: Generates a random string of the desired length with an optional prefix and/or suffix.
        description:
            - A lookup plugin generates a random string of the desired length with an optional prefix and/or suffix.
            - Useful for situations where a random value is required to avoid clashes.
        options:
          prefix:
            description: A prefix to add to the output
            required: False
            type: str
          suffix:
            description: A suffix to add to the output
            required: False
            type: str
          length:
            description: The length of the output exclusive of the prefix and/or suffix
            required: False
            type: int
            default: 8
"""


EXAMPLES = """
- name: Test with no arguments
  debug:
    msg: "{{ lookup('randomstring') }}"

- name: Test with length
  debug:
    msg: "{{ lookup('randomstring', length=10) }}"

- name: Test with prefix
  debug:
    msg: "{{ lookup('randomstring', prefix='beginning-') }}"

- name: Test with suffix
  debug:
    msg: "{{ lookup('randomstring', suffix='-end') }}"

- name: Test with all options
  debug:
    msg: "{{ lookup('randomstring', length=15, prefix='beginning-', suffix='-end') }}"

- name: Test with no arguments, random_string output only
  debug:
    msg: "{{ lookup('randomstring').random_string }}"

- name: Test with no arguments, total_length output only
  debug:
    msg: "{{ lookup('randomstring').total_length }}"
"""


RETURNS = """
  _list:
      description:
        - A list containing a single dictionary of the random string output data.
      type: list
      contains:
      random_string:
        description: The resultant random string value.
        type: str
      total_length:
        description: The total length of the random string inclusive or prefix and/or suffix if provided.
        type: str
"""

import random
import string

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

display = Display()


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        prefix = kwargs.get('prefix')
        suffix = kwargs.get('suffix')
        length = kwargs.get('length', 8)

        ret = []

        random_output = self.generate_random_string(
            prefix,
            suffix,
            length
        )

        output = {
            'random_string': random_output,
            'total_length': len(random_output)
        }

        ret.append(output)

        return ret


    def generate_random_string(self, prefix=None, suffix=None, length=8):
        """Generates a random string of letters and digits"""

        letters_and_digits = string.ascii_letters + string.digits

        output = ''.join(random.choice(letters_and_digits) for i in range(length))

        if prefix is not None:
            output = prefix + output

        if suffix is not None:
            output = output + suffix

        return output