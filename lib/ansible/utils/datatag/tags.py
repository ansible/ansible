from __future__ import annotations

import dataclasses
import os
import types
import typing as t

from ansible.module_utils.datatag import _tag_dataclass_kwargs, AnsibleDatatagBase, AnsibleSingletonTagBase


@dataclasses.dataclass(**_tag_dataclass_kwargs)
class AnsibleSourcePosition(AnsibleDatatagBase):
    """
    A tag that stores origin metadata for a tagged value, intended for forensic/diagnostic use.
    Source position metadata should not be used to make runtime decisions, as it is not guaranteed to be present or accurate.
    Setting both `path` and `line_num` can result in diagnostic display of referenced file contents.
    Either `path` or `description` must be present.
    """
    # DTFIX-MERGE: rename class to Origin, and rename src_pos/source_position/etc. locals/args to origin
    src: str | None = None  # DTFIX-MERGE: rename src to path (don't forget the replace method)
    """The path from which the tagged content originated."""
    description: str | None = None
    """A description of the origin, for display to users."""
    line: int | None = None  # DTFIX-MERGE: rename to line_num (don't forget the replace method)
    """An optional line number, starting at 1."""
    col: int | None = None  # DTFIX-MERGE: rename to col_num (don't forget the replace method)
    """An optional column number, starting at 1."""

    UNKNOWN: t.ClassVar[t.Self]

    @classmethod
    def get_or_create_tag(cls, value: t.Any, path: str | os.PathLike | None) -> AnsibleSourcePosition:
        """Return the tag from the given value, creating a tag from the provided path if no tag was found."""
        if not (tag := cls.get_tag(value)):
            if path:
                tag = AnsibleSourcePosition(src=str(path))  # convert tagged strings and path-like values to a native str
            else:
                tag = AnsibleSourcePosition.UNKNOWN

        return tag

    def replace(
        self,
        src: str | types.EllipsisType = ...,
        description: str | types.EllipsisType = ...,
        line: int | None | types.EllipsisType = ...,
        col: int | None | types.EllipsisType = ...,
    ) -> t.Self:
        """Return a new source position based on an existing one, with the given fields replaced."""
        return dataclasses.replace(
            self,
            **{key: value for key, value in dict(
                src=src,
                description=description,
                line=line,
                col=col,
            ).items() if value is not ...}  # type: ignore[arg-type]
        )

    def _post_validate(self) -> None:
        if self.src:
            if not self.src.startswith('/'):
                raise RuntimeError('The `src` field must be an absolute path.')
        elif not self.description:
            raise RuntimeError('The `src` or `description` field must be specified.')

    def __str__(self) -> str:
        """Renders the source position in the form of file:line:col, omitting missing/invalid elements from the right."""
        if self.src:
            value = self.src
        else:
            value = self.description

        if self.line and self.line > 0:
            value += f':{self.line}'

            if self.col and self.col > 0:
                value += f':{self.col}'

        if self.src and self.description:
            value += f' ({self.description})'

        return value


AnsibleSourcePosition.UNKNOWN = AnsibleSourcePosition(description='<unknown>')


@dataclasses.dataclass(**_tag_dataclass_kwargs)
class VaultedValue(AnsibleDatatagBase):
    """Tag for vault-encrypted strings that carries the original ciphertext for round-tripping."""
    ciphertext: str


@dataclasses.dataclass(**_tag_dataclass_kwargs)
class TrustedAsTemplate(AnsibleSingletonTagBase):
    """
    Indicates the tagged string is trusted to parse and render as a template.
    Do *NOT* apply this tag to data from untrusted sources, as this would allow code injection during templating.
    """


@dataclasses.dataclass(**_tag_dataclass_kwargs)
class NotATemplate(AnsibleSingletonTagBase):
    """
    Used for internal things like error messages that might contain a template-ish looking thing but that we don't
    want to spam users with untrusted warnings or unnecessarily recurse into containers we know shouldn't be templated (for performance, not security).
    """


@dataclasses.dataclass(**_tag_dataclass_kwargs)
class _EncryptedSource(AnsibleSingletonTagBase):
    """
    For internal use only.
    Indicates the tagged value was sourced from an encrypted file.
    Currently applied only by DataLoader.load_from_file().
    """
