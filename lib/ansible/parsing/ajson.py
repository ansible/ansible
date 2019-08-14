# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from datetime import date, datetime

from ansible.module_utils._text import to_text
from ansible.module_utils.common._collections_compat import Mapping
from ansible.module_utils.common.collections import is_sequence
from ansible.module_utils.six import binary_type, text_type
from ansible.parsing.vault import VaultLib
from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode
from ansible.utils.unsafe_proxy import AnsibleUnsafe, wrap_var


class AnsibleJSONDecoder(json.JSONDecoder):

    _vaults = {}

    def __init__(self, *args, **kwargs):
        kwargs['object_hook'] = self.object_hook
        super(AnsibleJSONDecoder, self).__init__(*args, **kwargs)

    @classmethod
    def set_secrets(cls, secrets):
        cls._vaults['default'] = VaultLib(secrets=secrets)

    def object_hook(self, pairs):
        for key in pairs:
            value = pairs[key]

            if key == '__ansible_vault':
                value = AnsibleVaultEncryptedUnicode(value)
                if self._vaults:
                    value.vault = self._vaults['default']
                return value
            elif key == '__ansible_unsafe':
                return wrap_var(value)

        return pairs


def _preprocess_unsafe_encode(value):
    """Recursively preprocess a data structure converting instances of ``AnsibleUnsafe``
    into their JSON dict representations

    Used in ``AnsibleJSONEncoder.encode``
    """
    if isinstance(value, AnsibleUnsafe):
        value = {'__ansible_unsafe': to_text(value, errors='surrogate_or_strict', nonstring='strict')}
    elif is_sequence(value):
        value = [_preprocess_unsafe_encode(v) for v in value]
    elif isinstance(value, Mapping):
        value = dict((k, _preprocess_unsafe_encode(v)) for k, v in value.items())

    return value


# TODO: find way to integrate with the encoding modules do in module_utils
class AnsibleJSONEncoder(json.JSONEncoder):
    '''
    Simple encoder class to deal with JSON encoding of Ansible internal types
    '''

    # NOTE: ALWAYS inform AWS/Tower when new items get added as they consume them downstream via a callback
    def default(self, o):
        if isinstance(o, AnsibleVaultEncryptedUnicode):
            # vault object
            value = {'__ansible_vault': to_text(o._ciphertext, errors='surrogate_or_strict', nonstring='strict')}
        elif isinstance(o, AnsibleUnsafe):
            # unsafe object, this will never be triggered, see ``encode``
            value = {'__ansible_unsafe': to_text(o, errors='surrogate_or_strict', nonstring='strict')}
        elif isinstance(o, Mapping):
            # hostvars and other objects
            value = dict(o)
        elif isinstance(o, (date, datetime)):
            # date object
            value = o.isoformat()
        else:
            # use default encoder
            value = super(AnsibleJSONEncoder, self).default(o)
        return value

    def encode(self, o):
        """Custom encode, primarily design to handle encoding ``AnsibleUnsafe``
        as the ``AnsibleUnsafe`` subclasses inherit from string types and the
        ``json.JSONEncoder`` does not support custom encoders for string types
        """
        o = _preprocess_unsafe_encode(o)

        return super(AnsibleJSONEncoder, self).encode(o)
