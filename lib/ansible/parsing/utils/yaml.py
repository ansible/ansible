# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2017, Ansible Project
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import json
import typing as t

import yaml

from ansible.errors import AnsibleJSONParserError
from ansible._internal._errors import _error_utils
from ansible.parsing.vault import VaultSecret
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible._internal._yaml._errors import AnsibleYAMLParserError
from ansible._internal._datatag._tags import Origin
from ansible._internal._json._profiles import _legacy


def from_yaml(
    data: str,
    file_name: str | None = None,
    show_content: bool = True,
    vault_secrets: list[tuple[str, VaultSecret]] | None = None,  # deprecated: description='Deprecate vault_secrets, it has no effect.' core_version='2.23'
    json_only: bool = False,
) -> t.Any:
    """Creates a Python data structure from the given data, which can be either a JSON or YAML string."""
    # FUTURE: provide Ansible-specific top-level APIs to expose JSON and YAML serialization/deserialization to hide the error handling logic
    #         once those are in place, defer deprecate this entire function

    origin = Origin.get_or_create_tag(data, file_name)

    data = origin.tag(data)

    with _error_utils.RedactAnnotatedSourceContext.when(not show_content):
        try:
            # we first try to load this data as JSON.
            # Fixes issues with extra vars json strings not being parsed correctly by the yaml parser
            return json.loads(data, cls=_legacy.Decoder)
        except Exception as ex:
            json_ex = ex

        if json_only:
            AnsibleJSONParserError.handle_exception(json_ex, origin=origin)

        try:
            return yaml.load(data, Loader=AnsibleLoader)  # type: ignore[arg-type]
        except Exception as yaml_ex:
            # DTFIX-FUTURE: how can we indicate in Origin that the data is in-memory only, to support context information -- is that useful?
            #        we'd need to pass data to handle_exception so it could be used as the content instead of reading from disk
            AnsibleYAMLParserError.handle_exception(yaml_ex, origin=origin)
