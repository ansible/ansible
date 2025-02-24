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

import io as _io

from yaml.resolver import Resolver

from ansible.module_utils._internal._datatag import AnsibleTagHelper
from ansible.parsing.yaml.constructor import AnsibleConstructor, _AnsibleInstrumentedConstructor
from ansible.module_utils.common.yaml import HAS_LIBYAML
from ansible._internal._datatag import _tags

if HAS_LIBYAML:
    from yaml.cyaml import CParser

    class _YamlParser(CParser):
        def __init__(self, stream: str | bytes | _io.IOBase) -> None:
            if isinstance(stream, (str, bytes)):
                stream = AnsibleTagHelper.untag(stream)  # PyYAML + libyaml barfs on str/bytes subclasses

            CParser.__init__(self, stream)

            self.name = getattr(stream, 'name', None)  # provide feature parity with the Python implementation (yaml.reader.Reader provides name)
else:
    from yaml.composer import Composer
    from yaml.reader import Reader
    from yaml.scanner import Scanner
    from yaml.parser import Parser

    class _YamlParser(Reader, Scanner, Parser, Composer):  # type: ignore[no-redef]
        def __init__(self, stream: str | bytes | _io.IOBase) -> None:
            Reader.__init__(self, stream)
            Scanner.__init__(self)
            Parser.__init__(self)
            Composer.__init__(self)


class _AnsibleInstrumentedLoader(_YamlParser, _AnsibleInstrumentedConstructor, Resolver):
    """Ansible YAML loader which supports Ansible custom behavior such as `Origin` tagging, but no Ansible-specific YAML tags."""

    def __init__(self, stream: str | bytes | _io.IOBase) -> None:
        _YamlParser.__init__(self, stream)

        _AnsibleInstrumentedConstructor.__init__(
            self,
            origin=_tags.Origin.get_or_create_tag(stream, self.name),
            trusted_as_template=_tags.TrustedAsTemplate.is_tagged_on(stream),
        )

        Resolver.__init__(self)


class AnsibleLoader(_YamlParser, AnsibleConstructor, Resolver):
    """Ansible loader which supports Ansible custom behavior such as `Origin` tagging, as well as Ansible-specific YAML tags."""

    def __init__(self, stream: str | bytes | _io.IOBase) -> None:
        _YamlParser.__init__(self, stream)

        AnsibleConstructor.__init__(
            self,
            origin=_tags.Origin.get_or_create_tag(stream, self.name),
            trusted_as_template=_tags.TrustedAsTemplate.is_tagged_on(stream),
        )

        Resolver.__init__(self)
