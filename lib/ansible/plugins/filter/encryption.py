# Copyright: (c) 2021, Ansible Project

from __future__ import annotations

from jinja2.runtime import Undefined
from jinja2.exceptions import UndefinedError

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils.common.text.converters import to_native, to_bytes
from ansible._internal._templating._jinja_common import VaultExceptionMarker
from ansible._internal._datatag._tags import VaultedValue
from ansible.parsing.vault import is_encrypted, VaultSecret, VaultLib, VaultHelper
from ansible import template as _template
from ansible.utils.display import Display

display = Display()


def do_vault(data, secret, salt=None, vault_id='filter_default', wrap_object=False, method_name=None):

    if not isinstance(secret, (str, bytes)):
        raise TypeError(f"Secret passed is required to be a string, instead we got {type(secret)}.")

    if not isinstance(data, (str, bytes)):
        raise TypeError(f"Can only vault strings, instead we got {type(data)}.")

    if method_name is not None:
        choices = C.config.get_config_choices('VAULT_METHOD')
        if method_name not in choices:
            raise AnsibleError(f"Invalid vault encryption method '{method_name}', valid choices are: {', '.join(choices)}")

    vault = ''
    vs = VaultSecret(to_bytes(secret))
    vl = VaultLib()
    try:
        vault = vl.encrypt(to_bytes(data), vs, vault_id, salt, method_name=method_name)
    except UndefinedError:
        raise
    except Exception as e:
        raise AnsibleError("Vault filter is unable to encrypt") from e

    if wrap_object:
        vault = VaultedValue(ciphertext=str(vault)).tag(secret)
    else:
        vault = to_native(vault)

    return vault


@_template.accept_args_markers
def do_unvault(vault, secret, vault_id='filter_default'):
    if isinstance(vault, VaultExceptionMarker):
        vault = vault._disarm()

    if (first_marker := _template.get_first_marker_arg((vault, secret, vault_id), {})) is not None:
        return first_marker

    if not isinstance(secret, (str, bytes)):
        raise TypeError(f"Secret passed is required to be as string, instead we got {type(secret)}.")

    if not isinstance(vault, (str, bytes)):
        raise TypeError(f"Vault should be in the form of a string, instead we got {type(vault)}.")

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
