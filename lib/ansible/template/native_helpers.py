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

from ansible.module_utils.six import string_types
from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode


# NOTE: A copy of https://github.com/pallets/jinja/blob/master/jinja2/nativetypes.py
# which handles Ansible related use cases.
def ansible_native_concat(nodes, preserve_quotes=True):
    """Return a native Python type from the list of compiled nodes. If
    the result is a single node, its value is returned. Otherwise, the
    nodes are concatenated as strings. If the result can be parsed with
    :func:`ast.literal_eval`, the parsed value is returned. Otherwise,
    the string is returned.

    :param nodes: Iterable of nodes to concatenate.
    :param preserve_quotes: Whether to re-wrap literal strings with
        quotes, to preserve quotes around expressions for later parsing.
        Should be ``False`` in :meth:`NativeEnvironment.render`.
    """
    head = list(islice(nodes, 2))

    if not head:
        return None

    if len(head) == 1:
        raw = head[0]

        # TODO send unvaulted data to literal_eval?
        if isinstance(raw, AnsibleVaultEncryptedUnicode):
            return raw.data

        if isinstance(raw, StrictUndefined):
            # A hack to raise proper UndefinedError/AnsibleUndefinedVariable exception.
            # We need to access the AnsibleUndefined(StrictUndefined) object by either of the following:
            # __iter__, __str__, __len__, __nonzero__, __eq__, __ne__, __bool__, __hash__
            # to actually raise the exception.
            # (see Jinja2 source of StrictUndefined to get up to date info)
            # Otherwise the undefined error would be raised on the next access which might not be properly handled.
            # See https://github.com/ansible/ansible/issues/52158
            # We do that only here because it is taken care of by text_type() in the else block below already.
            str(raw)

        # short circuit literal_eval when possible
        if not isinstance(raw, list):
            return raw
    else:
        if isinstance(nodes, types.GeneratorType):
            nodes = chain(head, nodes)
        # Stringifying the nodes is important as it takes care of
        # StrictUndefined by side-effect - by raising an exception.
        raw = u''.join([text_type(v) for v in nodes])

    try:
        literal = literal_eval(raw)
    except (ValueError, SyntaxError, MemoryError):
        return raw

    # If literal_eval returned a string, re-wrap with the original
    # quote character to avoid dropping quotes between expression nodes.
    # Without this, "'{{ a }}', '{{ b }}'" results in "a, b", but should
    # be ('a', 'b').
    if preserve_quotes and isinstance(literal, string_types):
        return "{quote}{}{quote}".format(literal, quote=raw[0])

    return literal
