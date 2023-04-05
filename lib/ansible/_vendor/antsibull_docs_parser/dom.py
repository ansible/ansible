# VENDORED FROM antsibull-docs-parser - DO NOT MODIFY HERE!

# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2023, Ansible Project
"""
DOM classes used by parser.
"""

import abc
import sys
import typing as t
from enum import Enum
from typing import NamedTuple

if sys.version_info >= (3, 8):
    ErrorType = t.Union[
        t.Literal["ignore"], t.Literal["message"], t.Literal["exception"]
    ]
else:
    # Python 3.6/3.7 do not have t.Literal
    ErrorType = str  # pragma: no cover

# The following makes it easier for us to script updates of the bundled code. It is not part of
# upstream antsibull-docs-parser
_BUNDLED_METADATA = {"pypi_name": "antsibull-docs-parser", "version": "0.2.0", "comment": "Keep in sync with validate-modules's requirements.in"}


class PluginIdentifier(NamedTuple):
    fqcn: str
    type: str


class PartType(Enum):
    ERROR = 0
    BOLD = 1
    CODE = 2
    HORIZONTAL_LINE = 3
    ITALIC = 4
    LINK = 5
    MODULE = 6
    RST_REF = 7
    URL = 8
    TEXT = 9
    ENV_VARIABLE = 10
    OPTION_NAME = 11
    OPTION_VALUE = 12
    PLUGIN = 13
    RETURN_VALUE = 14


class TextPart(NamedTuple):
    text: str
    source: t.Optional[str] = None
    type: "t.Literal[PartType.TEXT]" = PartType.TEXT


class ItalicPart(NamedTuple):
    text: str
    source: t.Optional[str] = None
    type: "t.Literal[PartType.ITALIC]" = PartType.ITALIC


class BoldPart(NamedTuple):
    text: str
    source: t.Optional[str] = None
    type: "t.Literal[PartType.BOLD]" = PartType.BOLD


class ModulePart(NamedTuple):
    fqcn: str
    source: t.Optional[str] = None
    type: "t.Literal[PartType.MODULE]" = PartType.MODULE


class PluginPart(NamedTuple):
    plugin: PluginIdentifier
    source: t.Optional[str] = None
    type: "t.Literal[PartType.PLUGIN]" = PartType.PLUGIN


class URLPart(NamedTuple):
    url: str
    source: t.Optional[str] = None
    type: "t.Literal[PartType.URL]" = PartType.URL


class LinkPart(NamedTuple):
    text: str
    url: str
    source: t.Optional[str] = None
    type: "t.Literal[PartType.LINK]" = PartType.LINK


class RSTRefPart(NamedTuple):
    text: str
    ref: str
    source: t.Optional[str] = None
    type: "t.Literal[PartType.RST_REF]" = PartType.RST_REF


class CodePart(NamedTuple):
    text: str
    source: t.Optional[str] = None
    type: "t.Literal[PartType.CODE]" = PartType.CODE


class OptionNamePart(NamedTuple):
    plugin: t.Optional[PluginIdentifier]
    entrypoint: t.Optional[str]  # present iff plugin.type == 'role'
    link: t.List[str]
    name: str
    value: t.Optional[str]
    source: t.Optional[str] = None
    type: "t.Literal[PartType.OPTION_NAME]" = PartType.OPTION_NAME


class OptionValuePart(NamedTuple):
    value: str
    source: t.Optional[str] = None
    type: "t.Literal[PartType.OPTION_VALUE]" = PartType.OPTION_VALUE


class EnvVariablePart(NamedTuple):
    name: str
    source: t.Optional[str] = None
    type: "t.Literal[PartType.ENV_VARIABLE]" = PartType.ENV_VARIABLE


class ReturnValuePart(NamedTuple):
    plugin: t.Optional[PluginIdentifier]
    entrypoint: t.Optional[str]  # present iff plugin.type == 'role'
    link: t.List[str]
    name: str
    value: t.Optional[str]
    source: t.Optional[str] = None
    type: "t.Literal[PartType.RETURN_VALUE]" = PartType.RETURN_VALUE


class HorizontalLinePart(NamedTuple):
    source: t.Optional[str] = None
    type: "t.Literal[PartType.HORIZONTAL_LINE]" = PartType.HORIZONTAL_LINE


class ErrorPart(NamedTuple):
    message: str
    source: t.Optional[str] = None
    type: "t.Literal[PartType.ERROR]" = PartType.ERROR


AnyPart = t.Union[
    TextPart,
    ItalicPart,
    BoldPart,
    ModulePart,
    PluginPart,
    URLPart,
    LinkPart,
    RSTRefPart,
    CodePart,
    OptionNamePart,
    OptionValuePart,
    EnvVariablePart,
    ReturnValuePart,
    HorizontalLinePart,
    ErrorPart,
]


Paragraph = t.List[AnyPart]


class Walker(abc.ABC):
    """
    Abstract base class for walker whose methods will be called for parts of a paragraph.
    """

    @abc.abstractmethod
    def process_error(self, part: ErrorPart) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def process_bold(self, part: BoldPart) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def process_code(self, part: CodePart) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def process_horizontal_line(self, part: HorizontalLinePart) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def process_italic(self, part: ItalicPart) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def process_link(self, part: LinkPart) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def process_module(self, part: ModulePart) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def process_rst_ref(self, part: RSTRefPart) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def process_url(self, part: URLPart) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def process_text(self, part: TextPart) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def process_env_variable(self, part: EnvVariablePart) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def process_option_name(self, part: OptionNamePart) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def process_option_value(self, part: OptionValuePart) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def process_plugin(self, part: PluginPart) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def process_return_value(self, part: ReturnValuePart) -> None:
        pass  # pragma: no cover


class NoopWalker(Walker):
    """
    Concrete base class for walker whose methods will be called for parts of a paragraph.
    The default implementation for every part will not do anything.
    """

    def process_error(self, part: ErrorPart) -> None:
        pass

    def process_bold(self, part: BoldPart) -> None:
        pass

    def process_code(self, part: CodePart) -> None:
        pass

    def process_horizontal_line(self, part: HorizontalLinePart) -> None:
        pass

    def process_italic(self, part: ItalicPart) -> None:
        pass

    def process_link(self, part: LinkPart) -> None:
        pass

    def process_module(self, part: ModulePart) -> None:
        pass

    def process_rst_ref(self, part: RSTRefPart) -> None:
        pass

    def process_url(self, part: URLPart) -> None:
        pass

    def process_text(self, part: TextPart) -> None:
        pass

    def process_env_variable(self, part: EnvVariablePart) -> None:
        pass

    def process_option_name(self, part: OptionNamePart) -> None:
        pass

    def process_option_value(self, part: OptionValuePart) -> None:
        pass

    def process_plugin(self, part: PluginPart) -> None:
        pass

    def process_return_value(self, part: ReturnValuePart) -> None:
        pass


# pylint:disable-next=too-many-branches
def walk(paragraph: Paragraph, walker: Walker) -> None:  # noqa: C901
    """
    Call the corresponding methods of a walker object for every part of the paragraph.
    """
    for part in paragraph:
        if part.type == PartType.ERROR:
            walker.process_error(t.cast(ErrorPart, part))
        elif part.type == PartType.BOLD:
            walker.process_bold(t.cast(BoldPart, part))
        elif part.type == PartType.CODE:
            walker.process_code(t.cast(CodePart, part))
        elif part.type == PartType.HORIZONTAL_LINE:
            walker.process_horizontal_line(t.cast(HorizontalLinePart, part))
        elif part.type == PartType.ITALIC:
            walker.process_italic(t.cast(ItalicPart, part))
        elif part.type == PartType.LINK:
            walker.process_link(t.cast(LinkPart, part))
        elif part.type == PartType.MODULE:
            walker.process_module(t.cast(ModulePart, part))
        elif part.type == PartType.RST_REF:
            walker.process_rst_ref(t.cast(RSTRefPart, part))
        elif part.type == PartType.URL:
            walker.process_url(t.cast(URLPart, part))
        elif part.type == PartType.TEXT:
            walker.process_text(t.cast(TextPart, part))
        elif part.type == PartType.ENV_VARIABLE:
            walker.process_env_variable(t.cast(EnvVariablePart, part))
        elif part.type == PartType.OPTION_NAME:
            walker.process_option_name(t.cast(OptionNamePart, part))
        elif part.type == PartType.OPTION_VALUE:
            walker.process_option_value(t.cast(OptionValuePart, part))
        elif part.type == PartType.PLUGIN:
            walker.process_plugin(t.cast(PluginPart, part))
        elif part.type == PartType.RETURN_VALUE:
            walker.process_return_value(t.cast(ReturnValuePart, part))
        else:
            raise RuntimeError(f"Internal error: unknown type {part.type!r}")
