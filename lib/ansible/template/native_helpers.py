# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


import ast
from itertools import islice, chain
from types import GeneratorType

from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.six import string_types
from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode
from ansible.utils.native_jinja import NativeJinjaText


_JSON_MAP = {
    "true": True,
    "false": False,
    "null": None,
}


class Json2Python(ast.NodeTransformer):
    def visit_Name(self, node):
        if node.id not in _JSON_MAP:
            return node
        return ast.Constant(value=_JSON_MAP[node.id])


def ansible_eval_concat(nodes):
    """Return a string of concatenated compiled nodes. Throw an undefined error
    if any of the nodes is undefined.

    If the result of concat appears to be a dictionary, list or bool,
    try and convert it to such using literal_eval, the same mechanism as used
    in jinja2_native.

    Used in Templar.template() when jinja2_native=False and convert_data=True.
    """
    head = list(islice(nodes, 2))

    if not head:
        return ''

    if len(head) == 1:
        out = head[0]

        if isinstance(out, NativeJinjaText):
            return out

        out = to_text(out)
    else:
        if isinstance(nodes, GeneratorType):
            nodes = chain(head, nodes)
        out = ''.join([to_text(v) for v in nodes])

    # if this looks like a dictionary, list or bool, convert it to such
    if out.startswith(('{', '[')) or out in ('True', 'False'):
        try:
            out = ast.literal_eval(
                ast.fix_missing_locations(
                    Json2Python().visit(
                        ast.parse(out, mode='eval')
                    )
                )
            )
        except (TypeError, ValueError, SyntaxError, MemoryError):
            pass

    return out


def ansible_concat(nodes):
    """Return a string of concatenated compiled nodes. Throw an undefined error
    if any of the nodes is undefined. Other than that it is equivalent to
    Jinja2's default concat function.

    Used in Templar.template() when jinja2_native=False and convert_data=False.
    """
    return ''.join([to_text(v) for v in nodes])


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
        out = head[0]

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

        # short-circuit literal_eval for anything other than strings
        if not isinstance(out, string_types):
            return out
    else:
        if isinstance(nodes, GeneratorType):
            nodes = chain(head, nodes)
        out = ''.join([to_text(v) for v in nodes])

    try:
        evaled = ast.literal_eval(
            # In Python 3.10+ ast.literal_eval removes leading spaces/tabs
            # from the given string. For backwards compatibility we need to
            # parse the string ourselves without removing leading spaces/tabs.
            ast.parse(out, mode='eval')
        )
    except (TypeError, ValueError, SyntaxError, MemoryError):
        return out

    if isinstance(evaled, string_types):
        quote = out[0]
        return f'{quote}{evaled}{quote}'

    return evaled
