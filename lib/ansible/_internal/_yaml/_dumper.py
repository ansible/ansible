from __future__ import annotations

import abc
import collections.abc as c
import typing as t

from enum import StrEnum, auto
from yaml.nodes import ScalarNode, Node

from ansible._internal._datatag._tags import VaultedValue
from ansible._internal._templating import _jinja_common
from ansible.config.manager import ConfigManager
from ansible.errors import AnsibleVariableTypeError
from ansible.module_utils import _internal
from ansible.module_utils._internal._datatag import AnsibleTaggedObject, Tripwire, AnsibleTagHelper
from ansible.module_utils._internal._ambient_context import AmbientContextBase
from ansible.parsing.vault import VaultHelper, EncryptedString
from ansible.module_utils.common.yaml import HAS_LIBYAML
from ansible.utils.display import Display

display = Display()
cfg_mgr = ConfigManager()

if HAS_LIBYAML:
    from yaml.cyaml import CSafeDumper as SafeDumper
else:
    from yaml import SafeDumper  # type: ignore[assignment]


class _BaseDumper(SafeDumper, metaclass=abc.ABCMeta):
    """Base class for Ansible YAML dumpers."""

    @classmethod
    @abc.abstractmethod
    def _register_representers(cls) -> None:
        """Method used to register representers to derived types during class initialization."""

    def __init_subclass__(cls, **kwargs) -> None:
        """Initialization for derived types."""
        cls._register_representers()


class VaultBehaviors(StrEnum):
    decrypt = auto()
    preserve = auto()
    redact = auto()
    fail = auto()
    default = auto()


class VaultDecryptionContext(AmbientContextBase):

    def __init__(self, vault_behavior: VaultBehaviors):
        self.vault_behavior = vault_behavior


class AnsibleDumper(_BaseDumper):
    """A simple stub class that allows us to add representers for our custom types."""

    @classmethod
    def _register_representers(cls) -> None:
        cls.add_multi_representer(AnsibleTaggedObject, cls.represent_ansible_tagged_object)
        cls.add_multi_representer(Tripwire, cls.represent_tripwire)
        cls.add_multi_representer(c.Mapping, cls.represent_dict)
        cls.add_multi_representer(c.Collection, cls.represent_list)
        cls.add_multi_representer(_jinja_common.VaultExceptionMarker, cls.represent_vault_exception_marker)

    def get_node_from_ciphertext(self, data: object) -> ScalarNode | None:
        if ciphertext := VaultHelper.get_ciphertext(data, with_tags=False):
            return self.represent_scalar('!vault', ciphertext, style='|')

        return None

    def represent_vault_exception_marker(self, data: _jinja_common.VaultExceptionMarker) -> ScalarNode:
        if node := self.get_node_from_ciphertext(data):
            return node

        data.trip()

    def represent_vaulted_value(self, data: AnsibleTaggedObject) -> Node:
        vault_decryption_context = VaultDecryptionContext.current(optional=True)
        if vault_decryption_context:
            match vault_decryption_context.vault_behavior:
                case VaultBehaviors.default:
                    should_be_strict = cfg_mgr.get_config_value('VAULTED_VALUE_DUMP_IS_ERROR')
                    if should_be_strict:
                        raise AnsibleVariableTypeError(message="Attempted to dump a vaulted value.", obj=data)
                    else:
                        display.deprecated(msg="In future releases of ansible the default value behavior of `to_yaml` and `to_nice_yaml` "
                                               "will raise an error when attempting to decrypt vaulted values unless explicitly enabled with `vault=decrypt",
                                           version="2.999")
                        return self.represent_data(AnsibleTagHelper.as_native_type(data))
                case VaultBehaviors.decrypt:
                    return self.represent_data(AnsibleTagHelper.as_native_type(data))
                case VaultBehaviors.preserve:
                    return self.get_node_from_ciphertext(data)
                case VaultBehaviors.redact:
                    return self.represent_data('<redacted>')
                case VaultBehaviors.fail:
                    raise AnsibleVariableTypeError(message="Attempted to dump a vaulted value", obj=data)
        else:
            return self.get_node_from_ciphertext(data)

    def represent_ansible_tagged_object(self, data: AnsibleTaggedObject) -> Node:
        if _internal.is_intermediate_mapping(data):
            return self.represent_dict(data)

        if _internal.is_intermediate_iterable(data):
            return self.represent_list(data)

        if VaultedValue.is_tagged_on(data) or isinstance(data, EncryptedString):
            return self.represent_vaulted_value(data)

        return self.represent_data(AnsibleTagHelper.as_native_type(data))  # automatically decrypts encrypted strings

    def represent_tripwire(self, data: Tripwire) -> t.NoReturn:
        data.trip()
