# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2017, Ansible Project
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import json
import typing as t

from ansible.errors import AnsibleJSONParserError
from ansible.errors.utils import RedactAnnotatedSourceContext
from ansible.parsing.vault import VaultSecret
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.parsing.yaml.errors import AnsibleYAMLParserError
from ansible.utils.datatag.tags import AnsibleSourcePosition
from ansible.utils.serialization import legacy


def from_yaml(
    data: str,
    file_name: str | None = None,  # DTFIX-MERGE: consider deprecating this in favor of tagging AnsibleSourcePosition on data
    show_content: bool = True,  # deprecated: description='deprecate show_content in favor of RedactAnnotatedSourceContext' core_version='2.22'
    vault_secrets: list[tuple[str, VaultSecret]] | None = None,  # DTFIX-MERGE: can we remove/deprecate this?
    json_only: bool = False,
) -> t.Any:
    """Creates a Python data structure from the given data, which can be either a JSON or YAML string."""
    origin = AnsibleSourcePosition.get_or_create_tag(data, file_name)

    data = origin.tag(data)

    # DTFIX-MERGE: provide Ansible-specific top-level APIs to expose JSON and YAML serialization/deserialization to hide the error handling logic

    with RedactAnnotatedSourceContext.when(not show_content):
        # FIXME: this whole two-step should be unnecessary, implement this natively in the YAML decoder or delegate?
        try:
            # we first try to load this data as JSON.
            # Fixes issues with extra vars json strings not being parsed correctly by the yaml parser
            return json.loads(data, cls=legacy.Decoder)
        except Exception as ex:
            json_ex = ex

        if json_only:
            AnsibleJSONParserError.handle_exception(json_ex, origin=origin)

        try:
            return AnsibleLoader(data).get_single_data()
        except Exception as yaml_ex:
            # DTFIX-MERGE: how can we indicate in AnsibleSourcePosition that the data is in-memory only, to support context information -- is that useful?
            #        we'd need to pass data to handle_exception so it could be used as the content instead of reading from disk
            AnsibleYAMLParserError.handle_exception(yaml_ex, origin=origin)
