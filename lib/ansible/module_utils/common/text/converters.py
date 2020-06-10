# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import datetime
import json

from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.common._collections_compat import Set
from ansible.module_utils.six import (
    binary_type,
    iteritems,
    text_type,
)


def _json_encode_fallback(obj):
    if isinstance(obj, Set):
        return list(obj)
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError("Cannot json serialize %s" % to_native(obj))


def jsonify(data, **kwargs):
    for encoding in ("utf-8", "latin-1"):
        try:
            return json.dumps(data, encoding=encoding, default=_json_encode_fallback, **kwargs)
        # Old systems using old simplejson module does not support encoding keyword.
        except TypeError:
            try:
                new_data = container_to_text(data, encoding=encoding)
            except UnicodeDecodeError:
                continue
            return json.dumps(new_data, default=_json_encode_fallback, **kwargs)
        except UnicodeDecodeError:
            continue
    raise UnicodeError('Invalid unicode encoding encountered')


def container_to_bytes(d, encoding='utf-8', errors='surrogate_or_strict'):
    ''' Recursively convert dict keys and values to byte str

        Specialized for json return because this only handles, lists, tuples,
        and dict container types (the containers that the json module returns)
    '''

    if isinstance(d, text_type):
        return to_bytes(d, encoding=encoding, errors=errors)
    elif isinstance(d, dict):
        return dict(container_to_bytes(o, encoding, errors) for o in iteritems(d))
    elif isinstance(d, list):
        return [container_to_bytes(o, encoding, errors) for o in d]
    elif isinstance(d, tuple):
        return tuple(container_to_bytes(o, encoding, errors) for o in d)
    else:
        return d


def container_to_text(d, encoding='utf-8', errors='surrogate_or_strict'):
    """Recursively convert dict keys and values to text str

    Specialized for json return because this only handles, lists, tuples,
    and dict container types (the containers that the json module returns)
    """

    if isinstance(d, binary_type):
        # Warning, can traceback
        return to_text(d, encoding=encoding, errors=errors)
    elif isinstance(d, dict):
        return dict(container_to_text(o, encoding, errors) for o in iteritems(d))
    elif isinstance(d, list):
        return [container_to_text(o, encoding, errors) for o in d]
    elif isinstance(d, tuple):
        return tuple(container_to_text(o, encoding, errors) for o in d)
    else:
        return d
