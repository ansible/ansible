from __future__ import annotations

import dataclasses
import os
import types
import typing as t

from ansible.module_utils._internal._datatag import _tag_dataclass_kwargs, AnsibleDatatagBase, AnsibleSingletonTagBase


@dataclasses.dataclass(**_tag_dataclass_kwargs)
class Origin(AnsibleDatatagBase):
    """
    A tag that stores origin metadata for a tagged value, intended for forensic/diagnostic use.
    Origin metadata should not be used to make runtime decisions, as it is not guaranteed to be present or accurate.
    Setting both `path` and `line_num` can result in diagnostic display of referenced file contents.
    Either `path` or `description` must be present.
    """

    path: str | None = None
    """The path from which the tagged content originated."""
    description: str | None = None
    """A description of the origin, for display to users."""
    line_num: int | None = None
    """An optional line number, starting at 1."""
    col_num: int | None = None
    """An optional column number, starting at 1."""

    UNKNOWN: t.ClassVar[t.Self]

    @classmethod
    def get_or_create_tag(cls, value: t.Any, path: str | os.PathLike | None) -> Origin:
        """Return the tag from the given value, creating a tag from the provided path if no tag was found."""
        if not (origin := cls.get_tag(value)):
            if path:
                origin = Origin(path=str(path))  # convert tagged strings and path-like values to a native str
            else:
                origin = Origin.UNKNOWN

        return origin

    def replace(
        self,
        path: str | types.EllipsisType = ...,
        description: str | types.EllipsisType = ...,
        line_num: int | None | types.EllipsisType = ...,
        col_num: int | None | types.EllipsisType = ...,
    ) -> t.Self:
        """Return a new origin based on an existing one, with the given fields replaced."""
        return dataclasses.replace(
            self,
            **{
                key: value
                for key, value in dict(
                    path=path,
                    description=description,
                    line_num=line_num,
                    col_num=col_num,
                ).items()
                if value is not ...
            },  # type: ignore[arg-type]
        )

    def _post_validate(self) -> None:
        if self.path:
            if not self.path.startswith('/'):
                raise RuntimeError('The `src` field must be an absolute path.')
        elif not self.description:
            raise RuntimeError('The `src` or `description` field must be specified.')

    def __str__(self) -> str:
        """Renders the origin in the form of path:line_num:col_num, omitting missing/invalid elements from the right."""
        if self.path:
            value = self.path
        else:
            value = self.description

        if self.line_num and self.line_num > 0:
            value += f':{self.line_num}'

            if self.col_num and self.col_num > 0:
                value += f':{self.col_num}'

        if self.path and self.description:
            value += f' ({self.description})'

        return value


Origin.UNKNOWN = Origin(description='<unknown>')


@dataclasses.dataclass(**_tag_dataclass_kwargs)
class VaultedValue(AnsibleDatatagBase):
    """Tag for vault-encrypted strings that carries the original ciphertext for round-tripping."""

    ciphertext: str

    def _get_tag_to_propagate(self, src: t.Any, value: object, *, value_type: t.Optional[type] = None) -> t.Self | None:
        # Since VaultedValue stores the encrypted representation of the value on which it is tagged,
        # it is incorrect to propagate the tag to a value which is not equal to the original.
        # If the tag were copied to another value and subsequently serialized as the original encrypted value,
        # the result would then differ from the value on which the tag was applied.

        # Comparisons which can trigger an exception are indicative of a bug and should not be handled here.
        # For example:
        # * When `src` is an undecryptable `EncryptedString` -- it is not valid to apply this tag to that type.
        # * When `value` is a `Marker` -- this requires a templating, but vaulted values do not support templating.

        if src == value:  # assume the tag was correctly applied to src
            return self  # same plaintext value, tag propagation with same ciphertext is safe

        return self.get_tag(value)  # different value, preserve the existing tag, if any


@dataclasses.dataclass(**_tag_dataclass_kwargs)
class TrustedAsTemplate(AnsibleSingletonTagBase):
    """
    Indicates the tagged string is trusted to parse and render as a template.
    Do *NOT* apply this tag to data from untrusted sources, as this would allow code injection during templating.
    """


@dataclasses.dataclass(**_tag_dataclass_kwargs)
class SourceWasEncrypted(AnsibleSingletonTagBase):
    """
    For internal use only.
    Indicates the tagged value was sourced from an encrypted file.
    Currently applied only by DataLoader.get_text_file_contents() and by extension DataLoader.load_from_file().
    """
