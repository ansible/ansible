#!/usr/bin/env python

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

    # force to list so we can check length
    if not isinstance(nodes, list):
        nodes = list(nodes)

    if len(head) == 1:
        out = head[0]
    else:
        out = u''.join([text_type(v) for v in chain(head, nodes)])

    #import q; q(out)
    #import q; q(len(head))
    #import q; q(len(nodes))

    #  short circuit literal_eval when possible
    if len(head) >= len(nodes) and not isinstance(out, list):
        #import q; q(out)
        return out

    try:
        #import q; q(out)
        #eout = literal_eval(out)
        #import q; q(type(eout))
        #import q; q(eout)
        #return eout
        return literal_eval(out)
    except (ValueError, SyntaxError, MemoryError):
        return out
