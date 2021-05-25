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
from ansible.module_utils.common.collections import is_sequence, Mapping
from ansible.module_utils.common.text.converters import container_to_text
from ansible.module_utils.six import PY2, text_type
from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode
from ansible.utils.native_jinja import NativeJinjaText


def _fail_on_undefined(data):
    """Recursively find an undefined value in a nested data structure
    and properly raise the undefined exception.
    """
    if isinstance(data, Mapping):
        for value in data.values():
            _fail_on_undefined(value)
    elif is_sequence(data):
        for item in data:
            _fail_on_undefined(item)
    else:
        if isinstance(data, StrictUndefined):
            # To actually raise the undefined exception we need to
            # access the undefined object otherwise the exception would
            # be raised on the next access which might not be properly
            # handled.
            # See https://github.com/ansible/ansible/issues/52158
            # and StrictUndefined implementation in upstream Jinja2.
            str(data)

    return data


def ansible_native_concat(nodes):
    """Return a native Python type from the list of compiled nodes. If the
    result is a single node, its value is returned. Otherwise, the nodes are
    concatenated as strings. If the result can be parsed with
    :func:`ast.literal_eval`, the parsed value is returned. Otherwise, the
    string is returned.

    https://github.com/pallets/jinja/blob/master/src/jinja2/nativetypes.py
    """
    head = list(islice(nodes, 2))

    if not head:
        return None

    if len(head) == 1:
        out = _fail_on_undefined(head[0])

        # TODO send unvaulted data to literal_eval?
        if isinstance(out, AnsibleVaultEncryptedUnicode):
            return out.data

        if isinstance(out, NativeJinjaText):
            # Sometimes (e.g. ``| string``) we need to mark variables
            # in a special way so that they remain strings and are not
            # passed into literal_eval.
            # See:
            # https://github.com/ansible/ansible/issues/70831
            # https://github.com/pallets/jinja/issues/1200
            # https://github.com/ansible/ansible/issues/70831#issuecomment-664190894
            return out
    else:
        if isinstance(nodes, types.GeneratorType):
            nodes = chain(head, nodes)
        out = u''.join([to_text(_fail_on_undefined(v)) for v in nodes])

    try:
        out = literal_eval(out)
        if PY2:
            # ensure bytes are not returned back into Ansible from templating
            out = container_to_text(out)
        return out
    except (ValueError, SyntaxError, MemoryError):
        return out
