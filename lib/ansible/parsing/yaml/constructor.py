# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

import copy
import typing as t

from yaml import Node
from yaml.constructor import SafeConstructor
from yaml.resolver import BaseResolver

from ansible import constants as C
from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.datatag import AnsibleTagHelper
from ...utils.datatag.tags import AnsibleSourcePosition, TrustedAsTemplate, NotATemplate
from ansible.parsing.vault import VaultSecret, EncryptedString
from ansible.utils.display import Display

from .errors import AnsibleConstructorError

display = Display()

_NOT_A_TEMPLATE: t.Final[NotATemplate] = NotATemplate()
_TRUSTED_AS_TEMPLATE: t.Final[TrustedAsTemplate] = TrustedAsTemplate()


class AnsibleConstructor(SafeConstructor):
    name: t.Any  # provided by the YAML parser, which retrieves it from the stream

    def __init__(
        self,
        origin: AnsibleSourcePosition,
        vault_secrets: list[tuple[str, VaultSecret]] | None = None,  # DTFIX-MERGE: can we remove/deprecate this?
        trusted_as_template: bool = False,
    ) -> None:
        self._origin = origin
        super(AnsibleConstructor, self).__init__()
        self._trusted_as_template = trusted_as_template

        # volatile state var used during recursive construction of a value tagged unsafe
        self._unsafe_depth = 0
        self._duplicate_key_mode = C.config.get_config_value('DUPLICATE_YAML_DICT_KEY')

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
        src_pos = self._node_position_info(node)
        display.deprecated(
            msg='Use of the YAML `!!omap` tag is deprecated.',
            version='2.21',
            obj=src_pos,
            help_text='Use a standard mapping instead, as key order is always preserved.',
        )
        items = list(super().construct_yaml_omap(node))[0]
        items = [src_pos.tag(item) for item in items]
        yield src_pos.tag(items)

    def construct_yaml_pairs(self, node):
        src_pos = self._node_position_info(node)
        display.deprecated(
            msg='Use of the YAML `!!pairs` tag is deprecated.',
            version='2.21',
            obj=src_pos,
            help_text='Use a standard mapping instead.',
        )
        items = list(super().construct_yaml_pairs(node))[0]
        items = [src_pos.tag(item) for item in items]
        yield src_pos.tag(items)

    def construct_yaml_str(self, node):
        # Override the default string handling function
        # to always return unicode objects
        # DTFIX-FUTURE: is this to_text conversion still necessary under Py3?
        value = to_text(self.construct_scalar(node))

        tags = [self._node_position_info(node)]

        if self._unsafe_depth:
            tags.append(_NOT_A_TEMPLATE)
        elif self._trusted_as_template:
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

    def construct_yaml_vault(self, node: Node) -> EncryptedString:
        ciphertext = self._resolve_and_construct_object(node)

        if not isinstance(ciphertext, str):
            raise AnsibleConstructorError(problem=f"the {node.tag!r} tag requires a string value", problem_mark=node.start_mark)

        encrypted_string = AnsibleTagHelper.tag_copy(ciphertext, EncryptedString(ciphertext=AnsibleTagHelper.untag(ciphertext)))

        return encrypted_string

    def construct_yaml_seq(self, node):
        data = self._node_position_info(node).tag([])
        yield data
        data.extend(self.construct_sequence(node))

    def construct_yaml_unsafe(self, node):
        self._unsafe_depth += 1

        try:
            return self._resolve_and_construct_object(node)
        finally:
            self._unsafe_depth -= 1

    def _resolve_and_construct_object(self, node):
        # use a copied node to avoid mutating existing node and tripping the recursion check in construct_object
        copied_node = copy.copy(node)
        # repeat implicit resolution process to determine the proper tag for the value in the unsafe node
        copied_node.tag = t.cast(BaseResolver, self).resolve(type(node), node.value, (True, False))

        # re-entrant call using the correct tag
        # non-deferred construction of hierarchical nodes so the result is a fully realized object, and so our stateful unsafe propagation behavior works
        return self.construct_object(copied_node, deep=True)

    def _node_position_info(self, node) -> AnsibleSourcePosition:
        # the line number where the previous token has ended (plus empty lines)
        # Add one so that the first line is line 1 rather than line 0
        return self._origin.replace(line=node.start_mark.line + 1, col=node.start_mark.column + 1)

# DTFIX-MERGE: review and deprecate tags below as appropriate


AnsibleConstructor.add_constructor(
    u'tag:yaml.org,2002:map',
    AnsibleConstructor.construct_yaml_map)  # type: ignore[type-var]

AnsibleConstructor.add_constructor(
    u'tag:yaml.org,2002:python/dict',
    AnsibleConstructor.construct_yaml_map)  # type: ignore[type-var]

AnsibleConstructor.add_constructor(
    u'tag:yaml.org,2002:str',
    AnsibleConstructor.construct_yaml_str)  # type: ignore[type-var]

AnsibleConstructor.add_constructor(
    u'tag:yaml.org,2002:binary',
    AnsibleConstructor.construct_yaml_binary)  # type: ignore[type-var]

AnsibleConstructor.add_constructor(
    u'tag:yaml.org,2002:set',
    AnsibleConstructor.construct_yaml_set)  # type: ignore[type-var]

AnsibleConstructor.add_constructor(
    u'tag:yaml.org,2002:omap',
    AnsibleConstructor.construct_yaml_omap)  # type: ignore[type-var]

AnsibleConstructor.add_constructor(
    u'tag:yaml.org,2002:pairs',
    AnsibleConstructor.construct_yaml_pairs)  # type: ignore[type-var]

AnsibleConstructor.add_constructor(
    'tag:yaml.org,2002:int',
    AnsibleConstructor.construct_yaml_int)  # type: ignore[type-var]

AnsibleConstructor.add_constructor(
    'tag:yaml.org,2002:float',
    AnsibleConstructor.construct_yaml_float)  # type: ignore[type-var]

AnsibleConstructor.add_constructor(
    'tag:yaml.org,2002:timestamp',
    AnsibleConstructor.construct_yaml_timestamp)  # type: ignore[type-var]

AnsibleConstructor.add_constructor(
    u'tag:yaml.org,2002:python/unicode',
    AnsibleConstructor.construct_yaml_str)  # type: ignore[type-var]

AnsibleConstructor.add_constructor(
    u'tag:yaml.org,2002:seq',
    AnsibleConstructor.construct_yaml_seq)  # type: ignore[type-var]

AnsibleConstructor.add_constructor(
    u'!unsafe',
    AnsibleConstructor.construct_yaml_unsafe)  # type: ignore[type-var]

AnsibleConstructor.add_constructor(
    u'!vault',
    AnsibleConstructor.construct_yaml_vault)  # type: ignore[type-var]

# FIXME: deprecate !vault-encrypted
AnsibleConstructor.add_constructor(
    u'!vault-encrypted',
    AnsibleConstructor.construct_yaml_vault)  # type: ignore[type-var]
