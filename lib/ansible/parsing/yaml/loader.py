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

import typing as t

from yaml.resolver import Resolver

from ansible.module_utils.datatag import AnsibleTagHelper
from ansible.parsing.vault import VaultSecret
from ansible.parsing.yaml.constructor import AnsibleConstructor
from ansible.module_utils.common.yaml import HAS_LIBYAML
from ansible.utils.datatag.tags import TrustedAsTemplate, AnsibleSourcePosition

if HAS_LIBYAML:
    from yaml.cyaml import CParser

    class _YamlParser(CParser):
        def __init__(self, stream: str | bytes | t.TextIO | t.BinaryIO) -> None:
            stream = AnsibleTagHelper.untag(stream)  # PyYAML + libyaml barfs on str subclasses

            CParser.__init__(self, stream)

            self.name = getattr(stream, 'name', None)  # provide feature parity with the Python implementation (yaml.reader.Reader provides name)
else:
    from yaml.composer import Composer
    from yaml.reader import Reader
    from yaml.scanner import Scanner
    from yaml.parser import Parser

    class _YamlParser(Reader, Scanner, Parser, Composer):  # type: ignore[no-redef]
        def __init__(self, stream: str | bytes | t.TextIO | t.BinaryIO) -> None:
            Reader.__init__(self, stream)
            Scanner.__init__(self)
            Parser.__init__(self)
            Composer.__init__(self)


class AnsibleLoader(_YamlParser, AnsibleConstructor, Resolver):
    def __init__(
        self,
        stream: str | bytes | t.TextIO | t.BinaryIO,
        file_name: str | None = None,  # DTFIX-MERGE: can we eliminate this arg or make it origin instead?
        vault_secrets: list[tuple[str, VaultSecret]] | None = None,  # DTFIX-MERGE: can we remove/deprecate this?
        trusted_as_template: bool | None = None,  # DTFIX-MERGE: we're not using this, can we use a stream wrapper to carry this flag instead?
    ) -> None:
        trusted_as_template = trusted_as_template if isinstance(trusted_as_template, bool) else TrustedAsTemplate.is_tagged_on(stream)

        _YamlParser.__init__(self, stream)

        origin = AnsibleSourcePosition.get_or_create_tag(stream, file_name or self.name)

        AnsibleConstructor.__init__(self, origin=origin, trusted_as_template=trusted_as_template)
        Resolver.__init__(self)
