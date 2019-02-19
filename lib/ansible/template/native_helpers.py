# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ast import literal_eval
from itertools import islice, chain
import types

from jinja2._compat import text_type

from jinja2.runtime import StrictUndefined
from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode


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

        # TODO send unvaulted data to literal_eval?
        if isinstance(out, AnsibleVaultEncryptedUnicode):
            return out.data

        if isinstance(out, StrictUndefined):
            # A hack to raise proper UndefinedError/AnsibleUndefinedVariable exception.
            # We need to access the AnsibleUndefined(StrictUndefined) object by either of the following:
            # __iter__, __str__, __len__, __nonzero__, __eq__, __ne__, __bool__, __hash__
            # to actually raise the exception.
            # (see Jinja2 source of StrictUndefined to get up to date info)
            # Otherwise the undefined error would be raised on the next access which might not be properly handled.
            # See https://github.com/ansible/ansible/issues/52158
            # We do that only here because it is taken care of by text_type() in the else block below already.
            str(out)

        # short circuit literal_eval when possible
        if not isinstance(out, list):
            return out
    else:
        if isinstance(nodes, types.GeneratorType):
            nodes = chain(head, nodes)
        # Stringifying the nodes is important as it takes care of
        # StrictUndefined by side-effect - by raising an exception.
        out = u''.join([text_type(v) for v in nodes])

    try:
        return literal_eval(out)
    except (ValueError, SyntaxError, MemoryError):
        return out
