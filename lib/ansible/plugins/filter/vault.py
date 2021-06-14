# Copyright 2021, Ansible Project

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleFilterError, AnsibleFilterTypeError
from ansible.module_utils._text import to_native, to_bytes
from ansible.module_utils.six import string_types
from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode
from ansible.parsing.vault import is_encrypted, VaultSecret, VaultLib
from ansible.utils.display import Display

display = Display()


def do_vault(data, secret, vaultid='default', wrap_object=False):

    if not isinstance(secret, string_types):
        raise AnsibleFilterTypeError("Secret passed is required to be as tring, instead we got: %s" % type(secret))

    if not isinstance(data, string_types):
        raise AnsibleFilterTypeError("Can only vault strings, instead we got: %s" % type(data))

    vault = ''
    vs = VaultSecret(to_bytes(secret))
    vl = VaultLib()
    try:
        vault = vl.encrypt(to_bytes(data), vs, vaultid)
    except Exception as e:
        raise AnsibleFilterError("Unable to encrypt: %s" % to_native(e), orig_exc=e)

    if wrap_object:
        vault = AnsibleVaultEncryptedUnicode(vault)
    else:
        vault = to_native(vault)

    return vault


def do_unvault(vault, secret, vaultid='default'):

    if not isinstance(secret, string_types):
        raise AnsibleFilterTypeError("Secret passed is required to be as tring, instead we got: %s" % type(secret))

    if not isinstance(vault, (string_types, AnsibleVaultEncryptedUnicode)):
        raise AnsibleFilterTypeError("Vault should be in the form of a string, instead we got: %s" % type(vault))

    data = ''
    if isinstance(vault, AnsibleVaultEncryptedUnicode):
        vault = vault.data

    if is_encrypted(vault):
        vs = VaultSecret(to_bytes(secret))
        vl = VaultLib([(vaultid, vs)])
        try:
            data = vl.decrypt(vault)
        except Exception as e:
            raise AnsibleFilterError("Unable to decrypt: %s" % to_native(e), orig_exc=e)
    else:
        data = vault

    return to_native(data)


class FilterModule(object):
    ''' Ansible math jinja2 filters '''

    def filters(self):
        filters = {
            'vault': do_vault,
            'unvault': do_unvault,
        }

        return filters
