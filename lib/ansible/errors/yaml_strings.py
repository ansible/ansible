# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

__all__ = [
    'YAML_SYNTAX_ERROR',
    'YAML_POSITION_DETAILS',
    'YAML_COMMON_DICT_ERROR',
    'YAML_COMMON_UNQUOTED_VARIABLE_ERROR',
    'YAML_COMMON_UNQUOTED_COLON_ERROR',
    'YAML_COMMON_PARTIALLY_QUOTED_LINE_ERROR',
    'YAML_COMMON_UNBALANCED_QUOTES_ERROR',
]

YAML_SYNTAX_ERROR = """\
Syntax Error while loading YAML.
  %s"""

YAML_POSITION_DETAILS = """\
The error appears to be in '%s': line %s, column %s, but may
be elsewhere in the file depending on the exact syntax problem.
"""

YAML_COMMON_DICT_ERROR = """\
This one looks easy to fix. YAML thought it was looking for the start of a
hash/dictionary and was confused to see a second "{". Most likely this was
meant to be an ansible template evaluation instead, so we have to give the
parser a small hint that we wanted a string instead. The solution here is to
just quote the entire value.

For instance, if the original line was:

    app_path: {{ base_path }}/foo

It should be written as:

    app_path: "{{ base_path }}/foo"
"""

YAML_COMMON_UNQUOTED_VARIABLE_ERROR = """\
We could be wrong, but this one looks like it might be an issue with
missing quotes. Always quote template expression brackets when they
start a value. For instance:

    with_items:
      - {{ foo }}

Should be written as:

    with_items:
      - "{{ foo }}"
"""

YAML_COMMON_UNQUOTED_COLON_ERROR = """\
This one looks easy to fix. There seems to be an extra unquoted colon in the line
and this is confusing the parser. It was only expecting to find one free
colon. The solution is just add some quotes around the colon, or quote the
entire line after the first colon.

For instance, if the original line was:

    copy: src=file.txt dest=/path/filename:with_colon.txt

It can be written as:

    copy: src=file.txt dest='/path/filename:with_colon.txt'

Or:

    copy: 'src=file.txt dest=/path/filename:with_colon.txt'
"""

YAML_COMMON_PARTIALLY_QUOTED_LINE_ERROR = """\
This one looks easy to fix. It seems that there is a value started
with a quote, and the YAML parser is expecting to see the line ended
with the same kind of quote. For instance:

    when: "ok" in result.stdout

Could be written as:

   when: '"ok" in result.stdout'

Or equivalently:

   when: "'ok' in result.stdout"
"""

YAML_COMMON_UNBALANCED_QUOTES_ERROR = """\
We could be wrong, but this one looks like it might be an issue with
unbalanced quotes. If starting a value with a quote, make sure the
line ends with the same set of quotes. For instance this arbitrary
example:

    foo: "bad" "wolf"

Could be written as:

    foo: '"bad" "wolf"'
"""

YAML_COMMON_LEADING_TAB_ERROR = """\
There appears to be a tab character at the start of the line.

YAML does not use tabs for formatting. Tabs should be replaced with spaces.

For example:
    - name: update tooling
      vars:
        version: 1.2.3
#    ^--- there is a tab there.

Should be written as:
    - name: update tooling
      vars:
        version: 1.2.3
# ^--- all spaces here.
"""

YAML_AND_SHORTHAND_ERROR = """\
There appears to be both 'k=v' shorthand syntax and YAML in this task. \
Only one syntax may be used.
"""
