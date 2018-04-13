# (c) 2013, Jayson Vantuyl <jayson@aggressive.ly>
# (c) 2012-17 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: sequence
    author: Jayson Vantuyl <jayson@aggressive.ly>
    version_added: "1.0"
    short_description: generate a list based on a number sequence
    description:
      - generates a sequence of items. You can specify a start value, an end value, an optional "stride" value that specifies the number of steps
        to increment the sequence, and an optional printf-style format string.
      - 'Arguments can be specified as key=value pair strings or as a shortcut form of the arguments string is also accepted: [start-]end[/stride][:format].'
      - 'Numerical values can be specified in decimal, hexadecimal (0x3f8) or octal (0600).'
      - Starting at version 1.9.2, negative strides are allowed.
    options:
      start:
        description: number at which to start the sequence
        default: 0
        type: number
      end:
        description: number at which to end the sequence, dont use this with count
        type: number
        default: 0
      count:
        description: number of elements in the sequence, this is not to be used with end
        type: number
        default: 0
      stride:
        description: increments between sequence numbers, the default is 1 unless the end is less than the start, then it is -1.
        type: number
      format:
        description: return a string with the generated number formated in
"""

EXAMPLES = """
- name: create some test users
  user:
    name: "{{ item }}"
    state: present
    groups: "evens"
  with_sequence: start=0 end=32 format=testuser%02x

- name: create a series of directories with even numbers for some reason
  file:
    dest: "/var/stuff/{{ item }}"
    state: directory
  with_sequence: start=4 end=16 stride=2

- name: a simpler way to use the sequence plugin create 4 groups
  group:
    name: "group{{ item }}"
    state: present
  with_sequence: count=4

- name: the final countdown
  debug: msg={{item}} seconds to detonation
  with_sequence: end=0 start=10
"""

RETURN = """
  _list:
    description: generated sequence of numbers or strings
"""

from re import compile as re_compile, IGNORECASE

from ansible.errors import AnsibleError
from ansible.module_utils.six.moves import xrange
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

    def reset(self):
        """set sensible defaults"""
        self.start = 1
        self.count = None
        self.end = None
        self.stride = 1
        self.format = "%d"

    def parse_kv_args(self, args):
        """parse key-value style arguments"""
        for arg in ["start", "end", "count", "stride"]:
            try:
                arg_raw = args.pop(arg, None)
                if arg_raw is None:
                    continue
                arg_cooked = int(arg_raw, 0)
                setattr(self, arg, arg_cooked)
            except ValueError:
                raise AnsibleError(
                    "can't parse arg %s=%r as integer"
                    % (arg, arg_raw)
                )
        if 'format' in args:
            self.format = args.pop("format")
        if args:
            raise AnsibleError(
                "unrecognized arguments to with_sequence: %r"
                % args.keys()
            )

    def parse_simple_args(self, term):
        """parse the shortcut forms, return True/False"""
        match = SHORTCUT.match(term)
        if not match:
            return False

        _, start, end, _, stride, _, format = match.groups()

        if start is not None:
            try:
                start = int(start, 0)
            except ValueError:
                raise AnsibleError("can't parse start=%s as integer" % start)
        if end is not None:
            try:
                end = int(end, 0)
            except ValueError:
                raise AnsibleError("can't parse end=%s as integer" % end)
        if stride is not None:
            try:
                stride = int(stride, 0)
            except ValueError:
                raise AnsibleError("can't parse stride=%s as integer" % stride)

        if start is not None:
            self.start = start
        if end is not None:
            self.end = end
        if stride is not None:
            self.stride = stride
        if format is not None:
            self.format = format

        return True

    def sanity_check(self):
        if self.count is None and self.end is None:
            raise AnsibleError("must specify count or end in with_sequence")
        elif self.count is not None and self.end is not None:
            raise AnsibleError("can't specify both count and end in with_sequence")
        elif self.count is not None:
            # convert count to end
            if self.count != 0:
                self.end = self.start + self.count * self.stride - 1
            else:
                self.start = 0
                self.end = 0
                self.stride = 0
            del self.count
        if self.stride > 0 and self.end < self.start:
            raise AnsibleError("to count backwards make stride negative")
        if self.stride < 0 and self.end > self.start:
            raise AnsibleError("to count forward don't make stride negative")
        if self.format.count('%') != 1:
            raise AnsibleError("bad formatting string: %s" % self.format)

    def generate_sequence(self):
        if self.stride >= 0:
            adjust = 1
        else:
            adjust = -1
        numbers = xrange(self.start, self.end + adjust, self.stride)

        for i in numbers:
            try:
                formatted = self.format % i
                yield formatted
            except (ValueError, TypeError):
                raise AnsibleError(
                    "problem formatting %r with %r" % (i, self.format)
                )

    def run(self, terms, variables, **kwargs):
        results = []

        for term in terms:
            try:
                self.reset()  # clear out things for this iteration
                try:
                    if not self.parse_simple_args(term):
                        self.parse_kv_args(parse_kv(term))
                except AnsibleError:
                    raise
                except Exception as e:
                    raise AnsibleError("unknown error parsing with_sequence arguments: %r. Error was: %s" % (term, e))

                self.sanity_check()
                if self.stride != 0:
                    results.extend(self.generate_sequence())
            except AnsibleError:
                raise
            except Exception as e:
                raise AnsibleError(
                    "unknown error generating sequence: %s" % e
                )

        return results
