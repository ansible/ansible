from __future__ import annotations

import abc
import collections.abc as c
import typing as t

from yaml.nodes import ScalarNode, Node

from ansible._internal._templating import _jinja_common
from ansible.module_utils import _internal
from ansible.module_utils._internal._datatag import AnsibleTaggedObject, Tripwire, AnsibleTagHelper
from ansible.parsing.vault import VaultHelper
from ansible.module_utils.common.yaml import HAS_LIBYAML

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

    def represent_ansible_tagged_object(self, data: AnsibleTaggedObject) -> Node:
        if _internal.is_intermediate_mapping(data):
            return self.represent_dict(data)

        if _internal.is_intermediate_iterable(data):
            return self.represent_list(data)

        if node := self.get_node_from_ciphertext(data):
            return node

        return self.represent_data(AnsibleTagHelper.as_native_type(data))  # automatically decrypts encrypted strings

    def represent_tripwire(self, data: Tripwire) -> t.NoReturn:
        data.trip()
