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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ast import literal_eval
from itertools import islice, chain
from jinja2._compat import text_type


def ansible_native_concat(nodes):
    """Return a native Python type from the list of compiled nodes. If the
    result is a single node, its value is returned. Otherwise, the nodes are
    concatenated as strings. If the result can be parsed with
    :func:`ast.literal_eval`, the parsed value is returned. Otherwise, the
    string is returned.
    """

    # https://github.com/pallets/jinja/blob/master/jinja2/nativetypes.py

    head = list(islice(nodes, 2))

    if not head:
        return None

    if len(head) == 1:
        out = head[0]
        # short circuit literal_eval when possible
        if not isinstance(out, list): # FIXME is this needed?
            return out
    else:
        out = u''.join([text_type(v) for v in chain(head, nodes)])

    try:
        return literal_eval(out)
    except (ValueError, SyntaxError, MemoryError):
        return out
