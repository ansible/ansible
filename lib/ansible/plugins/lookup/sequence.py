# (c) 2013, Jayson Vantuyl <jayson@aggressive.ly>
# (c) 2012-17 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
    name: sequence
    author: Jayson Vantuyl (!UNKNOWN) <jayson@aggressive.ly>
    version_added: "1.0"
    short_description: generate a list based on a number sequence
    description:
      - generates a sequence of items. You can specify a start value, an end value, an optional "stride" value that specifies the number of steps
        to increment the sequence, and an optional printf-style format string.
      - 'Arguments can be specified as key=value pair strings or as a shortcut form of the arguments string is also accepted: [start-]end[/stride][:format].'
      - 'Numerical values can be specified in decimal, hexadecimal (0x3f8) or octal (0600).'
      - Starting at version 1.9.2, negative strides are allowed.
      - Generated items are strings. Use Jinja2 filters to convert items to preferred type, e.g. C({{ 1 + item|int }}).
      - See also Jinja2 C(range) filter as an alternative.
    options:
      start:
        description: number at which to start the sequence
        default: 1
        type: integer
      end:
        description: number at which to end the sequence, dont use this with count
        type: integer
      count:
        description: number of elements in the sequence, this is not to be used with end
        type: integer
      stride:
        description: increments between sequence numbers, the default is 1 unless the end is less than the start, then it is -1.
        type: integer
        default: 1
      format:
        description: return a string with the generated number formatted in
        default: "%d"
"""

EXAMPLES = """
- name: create some test users
  ansible.builtin.user:
    name: "{{ item }}"
    state: present
    groups: "evens"
  with_sequence: start=0 end=32 format=testuser%02x

- name: create a series of directories with even numbers for some reason
  ansible.builtin.file:
    dest: "/var/stuff/{{ item }}"
    state: directory
  with_sequence: start=4 end=16 stride=2

- name: a simpler way to use the sequence plugin create 4 groups
  ansible.builtin.group:
    name: "group{{ item }}"
    state: present
  with_sequence: count=4

- name: the final countdown
  ansible.builtin.debug:
    msg: "{{item}} seconds to detonation"
  with_sequence: start=10 end=0 stride=-1

- name: Use of variable
  ansible.builtin.debug:
    msg: "{{ item }}"
  with_sequence: start=1 end="{{ end_at }}"
  vars:
    - end_at: 10
"""

RETURN = """
  _list:
    description:
      - A list containing generated sequence of items
    type: list
    elements: str
"""

from re import compile as re_compile, IGNORECASE

from ansible.errors import AnsibleError
from ansible.parsing.splitter import parse_kv
from ansible.plugins.lookup import LookupBase


# shortcut format
NUM = "(0?x?[0-9a-f]+)"
SHORTCUT = re_compile(
    "^(" +        # Group 0
    NUM +         # Group 1: Start
    "-)?" +
    NUM +         # Group 2: End
    "(/" +        # Group 3
    NUM +         # Group 4: Stride
    ")?" +
    "(:(.+))?$",  # Group 5, Group 6: Format String
    IGNORECASE
)
FIELDS = frozenset(('start', 'end', 'stride', 'count', 'format'))


class LookupModule(LookupBase):
    """
    sequence lookup module

    Used to generate some sequence of items. Takes arguments in two forms.

    The simple / shortcut form is:

      [start-]end[/stride][:format]

    As indicated by the brackets: start, stride, and format string are all
    optional.  The format string is in the style of printf.  This can be used
    to pad with zeros, format in hexadecimal, etc.  All of the numerical values
    can be specified in octal (i.e. 0664) or hexadecimal (i.e. 0x3f8).
    Negative numbers are not supported.

    Some examples:

      5 -> ["1","2","3","4","5"]
      5-8 -> ["5", "6", "7", "8"]
      2-10/2 -> ["2", "4", "6", "8", "10"]
      4:host%02d -> ["host01","host02","host03","host04"]

    The standard Ansible key-value form is accepted as well.  For example:

      start=5 end=11 stride=2 format=0x%02x -> ["0x05","0x07","0x09","0x0a"]

    This format takes an alternate form of "end" called "count", which counts
    some number from the starting value.  For example:

      count=5 -> ["1", "2", "3", "4", "5"]
      start=0x0f00 count=4 format=%04x -> ["0f00", "0f01", "0f02", "0f03"]
      start=0 count=5 stride=2 -> ["0", "2", "4", "6", "8"]
      start=1 count=5 stride=2 -> ["1", "3", "5", "7", "9"]

    The count option is mostly useful for avoiding off-by-one errors and errors
    calculating the number of entries in a sequence when a stride is specified.
    """

    def parse_kv_args(self, args):
        """parse key-value style arguments"""
        for arg in FIELDS:
            value = args.pop(arg, None)
            if value is not None:
                self.set_option(arg, value)
        if args:
            raise AnsibleError(
                "unrecognized arguments to with_sequence: %s"
                % list(args.keys())
            )

    def parse_simple_args(self, term):
        """parse the shortcut forms, return True/False"""
        match = SHORTCUT.match(term)
        if not match:
            return False

        dummy, start, end, dummy, stride, dummy, format = match.groups()

        for key in FIELDS:
            value = locals().get(key, None)
            if value is not None:
                self.set_option(key, value)

        return True

    def set_fields(self):
        for f in FIELDS:
            setattr(self, f, self.get_option(f))

    def sanity_check(self):
        """
        Returns True if options comprise a valid sequence expression
        Raises AnsibleError if options are an invalid expression
        Returns false if options are valid but result in an empty sequence - these cases do not raise exceptions
        in order to maintain historic behavior
        """
        if self.count is None and self.end is None:
            raise AnsibleError("must specify count or end in with_sequence")
        elif self.count is not None and self.end is not None:
            raise AnsibleError("can't specify both count and end in with_sequence")
        elif self.count is not None:
            # convert count to end
            if self.count != 0:
                self.end = self.start + self.count * self.stride - 1
            else:
                return False
        if self.stride > 0 and self.end < self.start:
            raise AnsibleError("to count backwards make stride negative")
        if self.stride < 0 and self.end > self.start:
            raise AnsibleError("to count forward don't make stride negative")
        if self.stride == 0:
            return False
        if self.format.count('%') != 1:
            raise AnsibleError("bad formatting string: %s" % self.format)

        return True

    def generate_sequence(self):
        if self.stride >= 0:
            adjust = 1
        else:
            adjust = -1
        numbers = range(self.start, self.end + adjust, self.stride)

        for i in numbers:
            try:
                formatted = self.format % i
                yield formatted
            except (ValueError, TypeError):
                raise AnsibleError(
                    "problem formatting %r with %r" % (i, self.format)
                )

    def run(self, terms, variables=None, **kwargs):
        results = []

        if kwargs and not terms:
            # All of the necessary arguments can be provided as keywords, but we still need something to loop over
            terms = ['']

        for term in terms:
            try:
                # set defaults/global
                self.set_options(direct=kwargs)
                try:
                    if not self.parse_simple_args(term):
                        self.parse_kv_args(parse_kv(term))
                except AnsibleError:
                    raise
                except Exception as e:
                    raise AnsibleError("unknown error parsing with_sequence arguments: %r. Error was: %s" % (term, e))

                self.set_fields()
                if self.sanity_check():
                    results.extend(self.generate_sequence())

            except AnsibleError:
                raise
            except Exception as e:
                raise AnsibleError(
                    "unknown error generating sequence: %s" % e
                )

        return results
