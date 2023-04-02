# VENDORED FROM antsibull-docs-parser - DO NOT MODIFY HERE!

# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2022, Ansible Project
"""
Internal parsing code.
"""

import re
import typing as t

_ESCAPE_OR_COMMA = re.compile(r"\\(.)| *(,) *")
_ESCAPE_OR_CLOSING = re.compile(r"\\(.)|([)])")


def parse_parameters_escaped(
    text: str,
    index: int,
    parameter_count: int,
    strict: bool,
) -> t.Tuple[t.List[str], int, t.Optional[str]]:
    result: t.List[str] = []
    parameters_left = parameter_count
    while parameters_left > 1:
        parameters_left -= 1
        value: t.List[str] = []
        while True:
            match = _ESCAPE_OR_COMMA.search(text, pos=index)
            if not match:
                result.append("".join(value))
                return (
                    result,
                    len(text),
                    "Cannot find comma separating parameter"
                    f" {parameter_count - parameters_left} from the next one",
                )
            value.append(text[index : match.start(0)])
            index = match.end(0)
            if match.group(1):
                if strict and match.group(1) not in ("\\", ")"):
                    result.append("".join(value))
                    return (
                        result,
                        index,
                        f'Unnecessarily escaped "{match.group(1)}"',
                    )
                value.append(match.group(1))
            else:
                break
        result.append("".join(value))
    value = []
    while True:
        match = _ESCAPE_OR_CLOSING.search(text, pos=index)
        if not match:
            result.append("".join(value))
            return result, len(text), 'Cannot find closing ")" after last parameter'
        value.append(text[index : match.start(0)])
        index = match.end(0)
        if match.group(1):
            if strict and match.group(1) not in ("\\", ")"):
                result.append("".join(value))
                return (
                    result,
                    index,
                    f'Unnecessarily escaped "{match.group(1)}"',
                )
            value.append(match.group(1))
        else:
            break
    result.append("".join(value))
    return result, index, None


def parse_parameters_unescaped(
    text: str,
    index: int,
    parameter_count: int,
    strict: bool,  # pylint: disable=unused-argument
) -> t.Tuple[t.List[str], int, t.Optional[str]]:
    result: t.List[str] = []
    first = True
    parameters_left = parameter_count
    while parameters_left > 1:
        parameters_left -= 1
        next_index = text.find(",", index)
        if next_index < 0:
            return (
                result,
                len(text),
                "Cannot find comma separating parameter"
                f" {parameter_count - parameters_left} from the next one",
            )
        parameter = text[index:next_index].rstrip(" ")
        if not first:
            parameter = parameter.lstrip(" ")
        else:
            first = False
        result.append(parameter)
        index = next_index + 1
    next_index = text.find(")", index)
    if next_index < 0:
        return result, len(text), 'Cannot find closing ")" after last parameter'
    parameter = text[index:next_index]
    if not first:
        parameter = parameter.lstrip(" ")
    result.append(parameter)
    index = next_index + 1
    return result, index, None
