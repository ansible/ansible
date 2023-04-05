# VENDORED FROM antsibull-docs-parser - DO NOT MODIFY HERE!
# pylint: disable=useless-option-value:

# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2023, Ansible Project
"""
Flexible formatting of DOM.
"""

import abc
import typing as t

from . import dom

# The following makes it easier for us to script updates of the bundled code. It is not part of
# upstream antsibull-docs-parser
_BUNDLED_METADATA = {"pypi_name": "antsibull-docs-parser", "version": "0.2.0", "comment": "Keep in sync with validate-modules's requirements.in"}


class LinkProvider(abc.ABC):
    """
    Provide URLs for objects, if available.
    """

    def plugin_link(  # pylint:disable=no-self-use
        self,
        plugin: dom.PluginIdentifier,  # pylint:disable=unused-argument
    ) -> t.Optional[str]:
        """Provides a link to a plugin."""
        return None

    def plugin_option_like_link(  # pylint:disable=no-self-use
        self,
        plugin: dom.PluginIdentifier,  # pylint:disable=unused-argument
        entrypoint: t.Optional[str],  # pylint:disable=unused-argument
        # pylint:disable-next=unused-argument
        what: "t.Union[t.Literal['option'], t.Literal['retval']]",
        # pylint:disable-next=unused-argument
        name: t.List[str],
        # pylint:disable-next=unused-argument
        current_plugin: bool,
    ) -> t.Optional[str]:
        """Provides a link to a plugin's option or return value."""
        return None


class _DefaultLinkProvider(LinkProvider):
    pass


class Formatter(abc.ABC):
    """
    Abstract base class for a formatter whose functions will be called for
    parts of a paragraph.
    """

    @abc.abstractmethod
    def format_error(self, part: dom.ErrorPart) -> str:
        pass  # pragma: no cover

    @abc.abstractmethod
    def format_bold(self, part: dom.BoldPart) -> str:
        pass  # pragma: no cover

    @abc.abstractmethod
    def format_code(self, part: dom.CodePart) -> str:
        pass  # pragma: no cover

    @abc.abstractmethod
    def format_horizontal_line(self, part: dom.HorizontalLinePart) -> str:
        pass  # pragma: no cover

    @abc.abstractmethod
    def format_italic(self, part: dom.ItalicPart) -> str:
        pass  # pragma: no cover

    @abc.abstractmethod
    def format_link(self, part: dom.LinkPart) -> str:
        pass  # pragma: no cover

    @abc.abstractmethod
    def format_module(self, part: dom.ModulePart, url: t.Optional[str]) -> str:
        pass  # pragma: no cover

    @abc.abstractmethod
    def format_rst_ref(self, part: dom.RSTRefPart) -> str:
        pass  # pragma: no cover

    @abc.abstractmethod
    def format_url(self, part: dom.URLPart) -> str:
        pass  # pragma: no cover

    @abc.abstractmethod
    def format_text(self, part: dom.TextPart) -> str:
        pass  # pragma: no cover

    @abc.abstractmethod
    def format_env_variable(self, part: dom.EnvVariablePart) -> str:
        pass  # pragma: no cover

    @abc.abstractmethod
    def format_option_name(self, part: dom.OptionNamePart, url: t.Optional[str]) -> str:
        pass  # pragma: no cover

    @abc.abstractmethod
    def format_option_value(self, part: dom.OptionValuePart) -> str:
        pass  # pragma: no cover

    @abc.abstractmethod
    def format_plugin(self, part: dom.PluginPart, url: t.Optional[str]) -> str:
        pass  # pragma: no cover

    @abc.abstractmethod
    def format_return_value(
        self, part: dom.ReturnValuePart, url: t.Optional[str]
    ) -> str:
        pass  # pragma: no cover


class _FormatWalker(dom.Walker):
    """
    Walker which calls a formatter's functions and stores the result in a list.
    """

    destination: t.List[str]
    formatter: Formatter
    link_provider: LinkProvider
    current_plugin: t.Optional[dom.PluginIdentifier]

    def __init__(
        self,
        destination: t.List[str],
        formatter: Formatter,
        link_provider: LinkProvider,
        current_plugin: t.Optional[dom.PluginIdentifier],
    ):
        self.destination = destination
        self.formatter = formatter
        self.link_provider = link_provider
        self.current_plugin = current_plugin

    def process_error(self, part: dom.ErrorPart) -> None:
        self.destination.append(self.formatter.format_error(part))

    def process_bold(self, part: dom.BoldPart) -> None:
        self.destination.append(self.formatter.format_bold(part))

    def process_code(self, part: dom.CodePart) -> None:
        self.destination.append(self.formatter.format_code(part))

    def process_horizontal_line(self, part: dom.HorizontalLinePart) -> None:
        self.destination.append(self.formatter.format_horizontal_line(part))

    def process_italic(self, part: dom.ItalicPart) -> None:
        self.destination.append(self.formatter.format_italic(part))

    def process_link(self, part: dom.LinkPart) -> None:
        self.destination.append(self.formatter.format_link(part))

    def process_module(self, part: dom.ModulePart) -> None:
        url = self.link_provider.plugin_link(
            dom.PluginIdentifier(fqcn=part.fqcn, type="module")
        )
        self.destination.append(self.formatter.format_module(part, url))

    def process_rst_ref(self, part: dom.RSTRefPart) -> None:
        self.destination.append(self.formatter.format_rst_ref(part))

    def process_url(self, part: dom.URLPart) -> None:
        self.destination.append(self.formatter.format_url(part))

    def process_text(self, part: dom.TextPart) -> None:
        self.destination.append(self.formatter.format_text(part))

    def process_env_variable(self, part: dom.EnvVariablePart) -> None:
        self.destination.append(self.formatter.format_env_variable(part))

    def process_option_name(self, part: dom.OptionNamePart) -> None:
        url = None
        if part.plugin:
            url = self.link_provider.plugin_option_like_link(
                part.plugin,
                part.entrypoint,
                "option",
                part.link,
                part.plugin == self.current_plugin,
            )
        self.destination.append(self.formatter.format_option_name(part, url))

    def process_option_value(self, part: dom.OptionValuePart) -> None:
        self.destination.append(self.formatter.format_option_value(part))

    def process_plugin(self, part: dom.PluginPart) -> None:
        url = self.link_provider.plugin_link(part.plugin)
        self.destination.append(self.formatter.format_plugin(part, url))

    def process_return_value(self, part: dom.ReturnValuePart) -> None:
        url = None
        if part.plugin:
            url = self.link_provider.plugin_option_like_link(
                part.plugin,
                part.entrypoint,
                "retval",
                part.link,
                part.plugin == self.current_plugin,
            )
        self.destination.append(self.formatter.format_return_value(part, url))


def format_paragraphs(
    paragraphs: t.Sequence[dom.Paragraph],
    formatter: Formatter,
    link_provider: t.Optional[LinkProvider] = None,
    par_start: str = "",
    par_end: str = "",
    par_sep: str = "",
    par_empty: str = "",
    current_plugin: t.Optional[dom.PluginIdentifier] = None,
) -> str:
    """
    Apply the formatter to all parts of the given paragraphs, concatenate the results,
    and insert start and end sequences for paragraphs and sequences between paragraphs.

    ``link_provider`` and ``current_plugin`` will be used to compute optional URLs
    that will be passed to the formatter.
    """
    if link_provider is None:
        link_provider = _DefaultLinkProvider()
    result: t.List[str] = []
    walker = _FormatWalker(result, formatter, link_provider, current_plugin)
    for paragraph in paragraphs:
        if result:
            result.append(par_sep)
        result.append(par_start)
        before_len = len(result)
        dom.walk(paragraph, walker)
        if before_len == len(result):
            result.append(par_empty)
        result.append(par_end)
    return "".join(result)
