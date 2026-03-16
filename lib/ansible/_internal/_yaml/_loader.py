from __future__ import annotations

import io as _io

from yaml.resolver import Resolver

from ansible.module_utils._internal._datatag import AnsibleTagHelper
from ansible.module_utils.common.yaml import HAS_LIBYAML
from ansible._internal._datatag import _tags

from ._constructor import AnsibleConstructor, AnsibleInstrumentedConstructor

if HAS_LIBYAML:
    from yaml.cyaml import CParser

    class _Parser(CParser):
        def __init__(self, stream: str | bytes | _io.IOBase) -> None:
            if isinstance(stream, (str, bytes)):
                stream = AnsibleTagHelper.untag(stream)  # PyYAML + libyaml barfs on str/bytes subclasses

            CParser.__init__(self, stream)

else:
    from yaml.composer import Composer
    from yaml.reader import Reader
    from yaml.scanner import Scanner
    from yaml.parser import Parser

    class _Parser(Reader, Scanner, Parser, Composer):  # type: ignore[no-redef]
        def __init__(self, stream: str | bytes | _io.IOBase) -> None:
            Reader.__init__(self, stream)
            Scanner.__init__(self)
            Parser.__init__(self)
            Composer.__init__(self)


class _YamlParser(_Parser):
    def __init__(self, stream: str | bytes | _io.IOBase) -> None:
        super().__init__(stream)

        # The Python implementation of PyYAML (yaml.reader.Reader) provides self.name.
        # However, it will fall back to "<...>" in various cases.
        # The C implementation of PyYAML does not provide self.name.
        # To provide consistency, name retrieval is re-implemented here.
        self.name = getattr(stream, 'name', None)


class AnsibleInstrumentedLoader(_YamlParser, AnsibleInstrumentedConstructor, Resolver):
    """Ansible YAML loader which supports Ansible custom behavior such as `Origin` tagging, but no Ansible-specific YAML tags."""

    def __init__(self, stream: str | bytes | _io.IOBase) -> None:
        _YamlParser.__init__(self, stream)

        AnsibleInstrumentedConstructor.__init__(
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
