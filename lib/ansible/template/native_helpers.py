# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ast import literal_eval
from itertools import islice, chain
import types

from jinja2.runtime import StrictUndefined

from ansible.module_utils._text import to_text
from ansible.module_utils.common.text.converters import container_to_text
from ansible.module_utils.six import PY2
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
            # We do that only here because it is taken care of by to_text() in the else block below already.
            str(out)
    else:
        if isinstance(nodes, types.GeneratorType):
            nodes = chain(head, nodes)
        # Stringifying the nodes is important as it takes care of
        # StrictUndefined by side-effect - by raising an exception.
        out = u''.join([to_text(v) for v in nodes])

    try:
        out = literal_eval(out)
        if PY2:
            # ensure bytes are not returned back into Ansible from templating
            out = container_to_text(out)
        return out
    except (ValueError, SyntaxError, MemoryError):
        return out
