# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from collections import Mapping
from datetime import date, datetime

from ansible.module_utils._text import to_text
from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode
from ansible.utils.unsafe_proxy import AnsibleUnsafe, wrap_var
from ansible.parsing.vault import VaultLib


class AnsibleJSONDecoder(json.JSONDecoder):

    _vaults = {}

    @classmethod
    def set_secrets(cls, secrets):
        cls._vaults['default'] = VaultLib(secrets=secrets)

    def _decode_map(self, value):

        if value.get('__ansible_unsafe', False):
            value = wrap_var(value.get('__ansible_unsafe'))
        elif value.get('__ansible_vault', False):
            value = AnsibleVaultEncryptedUnicode(value.get('__ansible_vault'))
            if self._vaults:
                value.vault = self._vaults['default']
        else:
            for k in value:
                if isinstance(value[k], Mapping):
                    value[k] = self._decode_map(value[k])
        return value

    def decode(self, obj):
        ''' use basic json decoding except for specific ansible objects unsafe and vault '''

        value = super(AnsibleJSONDecoder, self).decode(obj)

        if isinstance(value, Mapping):
            value = self._decode_map(value)

        return value


# TODO: find way to integrate with the encoding modules do in module_utils
class AnsibleJSONEncoder(json.JSONEncoder):
    '''
    Simple encoder class to deal with JSON encoding of Ansible internal types
    '''
    def default(self, o):
        if isinstance(o, AnsibleVaultEncryptedUnicode):
            # vault object
            value = {'__ansible_vault': to_text(o._ciphertext, errors='surrogate_or_strict', nonstring='strict')}
        elif isinstance(o, AnsibleUnsafe):
            # unsafe object
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
