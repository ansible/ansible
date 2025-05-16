# Copyright: (c) 2021, Ansible Project

from __future__ import annotations

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils.common.text.converters import to_native, to_bytes
from ansible.plugins import accept_args_markers
from ansible._internal._templating._jinja_common import get_first_marker_arg, VaultExceptionMarker
from ansible._internal._datatag._tags import VaultedValue
from ansible.parsing.vault import is_encrypted, VaultSecret, VaultLib, VaultHelper
from ansible.utils.display import Display

display = Display()


def do_vault(data, secret, salt=None, vault_id='filter_default', wrap_object=False, vaultid=None, method_name=None):

    if not isinstance(data, (str, bytes)):
        raise TypeError(f"Secret passed is required to be a string, instead we got {type(secret)}.")

    if method_name is not None:
        choices = C.config.get_config_choices('VAULT_PLUGIN')
        if method_name not in choices:
            raise TypeError("Invalid vault encryption method '{method_name}', valid choices are: %s" % ', '.join(choices))

    if vaultid is not None:
        display.deprecated("Use of undocumented 'vaultid', use 'vault_id' instead", version='2.20')

        if vault_id == 'filter_default':
            vault_id = vaultid
        else:
            display.warning("Ignoring vaultid as vault_id is already set.")

    vs = VaultSecret(to_bytes(secret))
    vl = VaultLib()
    try:
        vault = vl.encrypt(to_bytes(data), vs, vault_id, salt, method_name=method_name)
    except Exception as e:
        raise AnsibleError("Vault is unable to encrypt") from e

    if wrap_object:
        vault = VaultedValue(ciphertext=str(vault)).tag(secret)
    else:
        vault = to_native(vault)

    return vault


@accept_args_markers
def do_unvault(vault, secret, vault_id='filter_default', vaultid=None):
    if isinstance(vault, VaultExceptionMarker):
        vault = vault._disarm()

    if (first_marker := get_first_marker_arg((vault, secret, vault_id, vaultid), {})) is not None:
        return first_marker

    if not isinstance(secret, (str, bytes)):
        raise TypeError(f"Secret passed is required to be as string, instead we got {type(secret)}.")

    if not isinstance(vault, (str, bytes)):
        raise TypeError(f"Vault should be in the form of a string, instead we got {type(vault)}.")

    if vaultid is not None:
        display.deprecated("Use of undocumented 'vaultid', use 'vault_id' instead", version='2.20')

        if vault_id == 'filter_default':
            vault_id = vaultid
        else:
            display.warning("Ignoring vaultid as vault_id is already set.")

    vs = VaultSecret(to_bytes(secret))
    vl = VaultLib([(vault_id, vs)])

    if ciphertext := VaultHelper.get_ciphertext(vault, with_tags=True):
        vault = ciphertext

    if is_encrypted(vault):
        try:
            data = vl.decrypt(vault)
        except Exception as ex:
            raise AnsibleError("Unable to decrypt.") from ex
    else:
        data = vault

    return to_native(data)


class FilterModule(object):
    """ Ansible vault jinja2 filters """

    def filters(self):
        filters = {
            'vault': do_vault,
            'unvault': do_unvault,
        }

        return filters
