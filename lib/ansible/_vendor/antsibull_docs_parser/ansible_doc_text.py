# VENDORED FROM antsibull-docs-parser - DO NOT MODIFY HERE!

# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2023, Ansible Project
"""
Ansible-doc text serialization.
"""

import typing as t

from . import dom
from .format import Formatter, LinkProvider
from .format import format_paragraphs as _format_paragraphs

# The following makes it easier for us to script updates of the bundled code. It is not part of
# upstream antsibull-docs-parser
_BUNDLED_METADATA = {"pypi_name": "antsibull-docs-parser", "version": "0.2.0", "comment": "Keep in sync with validate-modules's requirements.in"}


class AnsibleDocTextFormatter(Formatter):
    @staticmethod
    def _format_option_like(
        part: t.Union[dom.OptionNamePart, dom.ReturnValuePart],
    ) -> str:
        value = part.value
        if value is None:
            text = f"`{part.name}'"
        else:
            text = f"`{part.name}={value}'"
        plugin = part.plugin
        if plugin:
            plugin_suffix = (
                "" if plugin.type in ("role", "module", "playbook") else " plugin"
            )
            plugin_text = f"{plugin.type}{plugin_suffix} {plugin.fqcn}"
            entrypoint = part.entrypoint
            if plugin.type == "role" and entrypoint is not None:
                plugin_text = f"{plugin_text}, {entrypoint} entrypoint"
            text = f"{text} (of {plugin_text})"
        return text

    def format_error(self, part: dom.ErrorPart) -> str:
        return f"[[ERROR while parsing: {part.message}]]"

    def format_bold(self, part: dom.BoldPart) -> str:
        return f"*{part.text}*"

    def format_code(self, part: dom.CodePart) -> str:
        return f"`{part.text}'"

    def format_horizontal_line(self, part: dom.HorizontalLinePart) -> str:
        return f"\n{'-' * 13}\n"

    def format_italic(self, part: dom.ItalicPart) -> str:
        return f"`{part.text}'"

    def format_link(self, part: dom.LinkPart) -> str:
        return f"{part.text} <{part.url}>"

    def format_module(self, part: dom.ModulePart, url: t.Optional[str]) -> str:
        return f"[{part.fqcn}]"

    def format_rst_ref(self, part: dom.RSTRefPart) -> str:
        return part.text

    def format_url(self, part: dom.URLPart) -> str:
        return part.url

    def format_text(self, part: dom.TextPart) -> str:
        return part.text

    def format_env_variable(self, part: dom.EnvVariablePart) -> str:
        return f"`{part.name}'"

    def format_option_name(self, part: dom.OptionNamePart, url: t.Optional[str]) -> str:
        return self._format_option_like(part)

    def format_option_value(self, part: dom.OptionValuePart) -> str:
        return f"`{part.value}'"

    def format_plugin(self, part: dom.PluginPart, url: t.Optional[str]) -> str:
        return f"[{part.plugin.fqcn}]"

    def format_return_value(
        self, part: dom.ReturnValuePart, url: t.Optional[str]
    ) -> str:
        return self._format_option_like(part)


DEFAULT_ANSIBLE_DOC_FORMATTER = AnsibleDocTextFormatter()


def to_ansible_doc_text(
    paragraphs: t.Sequence[dom.Paragraph],
    formatter: Formatter = DEFAULT_ANSIBLE_DOC_FORMATTER,
    link_provider: t.Optional[LinkProvider] = None,
    par_start: str = "",
    par_end: str = "",
    par_sep: str = "\n\n",
    par_empty: str = "",
    current_plugin: t.Optional[dom.PluginIdentifier] = None,
) -> str:
    return _format_paragraphs(
        paragraphs,
        formatter=formatter,
        link_provider=link_provider,
        par_start=par_start,
        par_end=par_end,
        par_sep=par_sep,
        par_empty=par_empty,
        current_plugin=current_plugin,
    )
