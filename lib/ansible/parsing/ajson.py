# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

# Imported for backwards compat
from ansible.module_utils.common.json import AnsibleJSONEncoder

from ansible.parsing.vault import VaultLib
from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode
from ansible.utils.unsafe_proxy import wrap_var


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
