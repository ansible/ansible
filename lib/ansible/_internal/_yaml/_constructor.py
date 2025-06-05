from __future__ import annotations

import abc
import copy
import typing as t

from yaml import Node, ScalarNode
from yaml.constructor import SafeConstructor
from yaml.resolver import BaseResolver

from ansible import constants as C
from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils._internal._datatag import AnsibleTagHelper, AnsibleDatatagBase
from ansible._internal._datatag._tags import Origin, TrustedAsTemplate
from ansible.parsing.vault import EncryptedString
from ansible.utils.display import Display

from ._errors import AnsibleConstructorError

display = Display()

_TRUSTED_AS_TEMPLATE: t.Final[TrustedAsTemplate] = TrustedAsTemplate()


class _BaseConstructor(SafeConstructor, metaclass=abc.ABCMeta):
    """Base class for Ansible YAML constructors."""

    @classmethod
    @abc.abstractmethod
    def _register_constructors(cls) -> None:
        """Method used to register constructors to derived types during class initialization."""

    def __init_subclass__(cls, **kwargs) -> None:
        """Initialization for derived types."""
        cls._register_constructors()


class AnsibleInstrumentedConstructor(_BaseConstructor):
    """Ansible constructor which supports Ansible custom behavior such as `Origin` tagging, but no Ansible-specific YAML tags."""

    name: t.Any  # provided by the YAML parser, which retrieves it from the stream

    def __init__(self, origin: Origin, trusted_as_template: bool) -> None:
        if not origin.line_num:
            origin = origin.replace(line_num=1)

        self._origin = origin
        self._trusted_as_template = trusted_as_template
        self._duplicate_key_mode = C.config.get_config_value('DUPLICATE_YAML_DICT_KEY')

        super().__init__()

    @property
    def trusted_as_template(self) -> bool:
        return self._trusted_as_template

    def construct_yaml_map(self, node):
        data = self._node_position_info(node).tag({})  # always an ordered dictionary on py3.7+
        yield data
        value = self.construct_mapping(node)
        data.update(value)

    def construct_mapping(self, node, deep=False):
        # Delegate to built-in implementation to construct the mapping.
        # This is done before checking for duplicates to leverage existing error checking on the input node.
        mapping = super().construct_mapping(node, deep)
        keys = set()

        # Now that the node is known to be a valid mapping, handle any duplicate keys.
        for key_node, _value_node in node.value:
            if (key := self.construct_object(key_node, deep=deep)) in keys:
                msg = f'Found duplicate mapping key {key!r}.'

                if self._duplicate_key_mode == 'error':
                    raise AnsibleConstructorError(problem=msg, problem_mark=key_node.start_mark)

                if self._duplicate_key_mode == 'warn':
                    display.warning(msg=msg, obj=key, help_text='Using last defined value only.')

            keys.add(key)

        return mapping

    def construct_yaml_int(self, node):
        value = super().construct_yaml_int(node)
        return self._node_position_info(node).tag(value)

    def construct_yaml_float(self, node):
        value = super().construct_yaml_float(node)
        return self._node_position_info(node).tag(value)

    def construct_yaml_timestamp(self, node):
        value = super().construct_yaml_timestamp(node)
        return self._node_position_info(node).tag(value)

    def construct_yaml_omap(self, node):
        origin = self._node_position_info(node)
        display.deprecated(
            msg='Use of the YAML `!!omap` tag is deprecated.',
            version='2.23',
            obj=origin,
            help_text='Use a standard mapping instead, as key order is always preserved.',
        )
        items = list(super().construct_yaml_omap(node))[0]
        items = [origin.tag(item) for item in items]
        yield origin.tag(items)

    def construct_yaml_pairs(self, node):
        origin = self._node_position_info(node)
        display.deprecated(
            msg='Use of the YAML `!!pairs` tag is deprecated.',
            version='2.23',
            obj=origin,
            help_text='Use a standard mapping instead.',
        )
        items = list(super().construct_yaml_pairs(node))[0]
        items = [origin.tag(item) for item in items]
        yield origin.tag(items)

    def construct_yaml_str(self, node: ScalarNode) -> str:
        # Override the default string handling function
        # to always return unicode objects
        # DTFIX-FUTURE: is this to_text conversion still necessary under Py3?
        value = to_text(self.construct_scalar(node))

        tags: list[AnsibleDatatagBase] = [self._node_position_info(node)]

        if self.trusted_as_template:
            # NB: since we're not context aware, this will happily add trust to dictionary keys; this is actually necessary for
            #  certain backward compat scenarios, though might be accomplished in other ways if we wanted to avoid trusting keys in
            #  the general scenario
            tags.append(_TRUSTED_AS_TEMPLATE)

        return AnsibleTagHelper.tag(value, tags)

    def construct_yaml_binary(self, node):
        value = super().construct_yaml_binary(node)

        return AnsibleTagHelper.tag(value, self._node_position_info(node))

    def construct_yaml_set(self, node):
        data = AnsibleTagHelper.tag(set(), self._node_position_info(node))
        yield data
        value = self.construct_mapping(node)
        data.update(value)

    def construct_yaml_seq(self, node):
        data = self._node_position_info(node).tag([])
        yield data
        data.extend(self.construct_sequence(node))

    def _resolve_and_construct_object(self, node):
        # use a copied node to avoid mutating existing node and tripping the recursion check in construct_object
        copied_node = copy.copy(node)
        # repeat implicit resolution process to determine the proper tag for the value in the unsafe node
        copied_node.tag = t.cast(BaseResolver, self).resolve(type(node), node.value, (True, False))

        # re-entrant call using the correct tag
        # non-deferred construction of hierarchical nodes so the result is a fully realized object, and so our stateful unsafe propagation behavior works
        return self.construct_object(copied_node, deep=True)

    def _node_position_info(self, node) -> Origin:
        # the line number where the previous token has ended (plus empty lines)
        # Add one so that the first line is line 1 rather than line 0
        return self._origin.replace(line_num=node.start_mark.line + self._origin.line_num, col_num=node.start_mark.column + 1)

    @classmethod
    def _register_constructors(cls) -> None:
        constructors: dict[str, t.Callable] = {
            'tag:yaml.org,2002:binary': cls.construct_yaml_binary,
            'tag:yaml.org,2002:float': cls.construct_yaml_float,
            'tag:yaml.org,2002:int': cls.construct_yaml_int,
            'tag:yaml.org,2002:map': cls.construct_yaml_map,
            'tag:yaml.org,2002:omap': cls.construct_yaml_omap,
            'tag:yaml.org,2002:pairs': cls.construct_yaml_pairs,
            'tag:yaml.org,2002:python/dict': cls.construct_yaml_map,
            'tag:yaml.org,2002:python/unicode': cls.construct_yaml_str,
            'tag:yaml.org,2002:seq': cls.construct_yaml_seq,
            'tag:yaml.org,2002:set': cls.construct_yaml_set,
            'tag:yaml.org,2002:str': cls.construct_yaml_str,
            'tag:yaml.org,2002:timestamp': cls.construct_yaml_timestamp,
        }

        for tag, constructor in constructors.items():
            cls.add_constructor(tag, constructor)


class AnsibleConstructor(AnsibleInstrumentedConstructor):
    """Ansible constructor which supports Ansible custom behavior such as `Origin` tagging, as well as Ansible-specific YAML tags."""

    def __init__(self, origin: Origin, trusted_as_template: bool) -> None:
        self._unsafe_depth = 0  # volatile state var used during recursive construction of a value tagged unsafe

        super().__init__(origin=origin, trusted_as_template=trusted_as_template)

    @property
    def trusted_as_template(self) -> bool:
        return self._trusted_as_template and not self._unsafe_depth

    def construct_yaml_unsafe(self, node):
        self._unsafe_depth += 1

        try:
            return self._resolve_and_construct_object(node)
        finally:
            self._unsafe_depth -= 1

    def construct_yaml_vault(self, node: Node) -> EncryptedString:
        ciphertext = self._resolve_and_construct_object(node)

        if not isinstance(ciphertext, str):
            raise AnsibleConstructorError(problem=f"the {node.tag!r} tag requires a string value", problem_mark=node.start_mark)

        encrypted_string = AnsibleTagHelper.tag_copy(ciphertext, EncryptedString(ciphertext=AnsibleTagHelper.untag(ciphertext)))

        return encrypted_string

    def construct_yaml_vault_encrypted(self, node: Node) -> EncryptedString:
        origin = self._node_position_info(node)
        display.deprecated(
            msg='Use of the YAML `!vault-encrypted` tag is deprecated.',
            version='2.23',
            obj=origin,
            help_text='Use the `!vault` tag instead.',
        )

        return self.construct_yaml_vault(node)

    @classmethod
    def _register_constructors(cls) -> None:
        super()._register_constructors()

        constructors: dict[str, t.Callable] = {
            '!unsafe': cls.construct_yaml_unsafe,
            '!vault': cls.construct_yaml_vault,
            '!vault-encrypted': cls.construct_yaml_vault_encrypted,
        }

        for tag, constructor in constructors.items():
            cls.add_constructor(tag, constructor)
