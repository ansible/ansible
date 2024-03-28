# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

import json

import datetime

from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.six.moves.collections_abc import Mapping
from ansible.module_utils.common.collections import is_sequence


def _is_unsafe(value):
    return getattr(value, '__UNSAFE__', False) and not getattr(value, '__ENCRYPTED__', False)


def _is_vault(value):
    return getattr(value, '__ENCRYPTED__', False)


def _preprocess_unsafe_encode(value):
    """Recursively preprocess a data structure converting instances of ``AnsibleUnsafe``
    into their JSON dict representations

    Used in ``AnsibleJSONEncoder.iterencode``
    """
    if _is_unsafe(value):
        value = {'__ansible_unsafe': to_text(value._strip_unsafe(), errors='surrogate_or_strict', nonstring='strict')}
    elif is_sequence(value):
        value = [_preprocess_unsafe_encode(v) for v in value]
    elif isinstance(value, Mapping):
        value = dict((k, _preprocess_unsafe_encode(v)) for k, v in value.items())

    return value


def json_dump(structure):
    return json.dumps(structure, cls=AnsibleJSONEncoder, sort_keys=True, indent=4)


class AnsibleJSONEncoder(json.JSONEncoder):
    '''
    Simple encoder class to deal with JSON encoding of Ansible internal types
    '''

    def __init__(self, preprocess_unsafe=False, vault_to_text=False, **kwargs):
        self._preprocess_unsafe = preprocess_unsafe
        self._vault_to_text = vault_to_text
        super(AnsibleJSONEncoder, self).__init__(**kwargs)

    # NOTE: ALWAYS inform AWS/Tower when new items get added as they consume them downstream via a callback
    def default(self, o):
        if getattr(o, '__ENCRYPTED__', False):
            # vault object
            if self._vault_to_text:
                value = to_text(o, errors='surrogate_or_strict')
            else:
                value = {'__ansible_vault': to_text(o._ciphertext, errors='surrogate_or_strict', nonstring='strict')}
        elif getattr(o, '__UNSAFE__', False):
            # unsafe object, this will never be triggered, see ``AnsibleJSONEncoder.iterencode``
            value = {'__ansible_unsafe': to_text(o._strip_unsafe(), errors='surrogate_or_strict', nonstring='strict')}
        elif isinstance(o, Mapping):
            # hostvars and other objects
            value = dict(o)
        elif isinstance(o, (datetime.date, datetime.datetime)):
            # date object
            value = o.isoformat()
        else:
            # use default encoder
            value = super(AnsibleJSONEncoder, self).default(o)
        return value

    def iterencode(self, o, **kwargs):
        """Custom iterencode, primarily design to handle encoding ``AnsibleUnsafe``
        as the ``AnsibleUnsafe`` subclasses inherit from string types and
        ``json.JSONEncoder`` does not support custom encoders for string types
        """
        if self._preprocess_unsafe:
            o = _preprocess_unsafe_encode(o)

        return super(AnsibleJSONEncoder, self).iterencode(o, **kwargs)
