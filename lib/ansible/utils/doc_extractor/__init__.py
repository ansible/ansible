# Copyright: (c) 2025, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import ast
import dataclasses
import pathlib
import warnings

import yaml


@dataclasses.dataclass(frozen=True)
class DocVar:
    name: str
    parse_yaml: bool = True


_DEFAULT_DOC_VARS = (
    DocVar('DOCUMENTATION', parse_yaml=True),
    DocVar('EXAMPLES', parse_yaml=False),
    DocVar('RETURN', parse_yaml=True),
)


def ast_py_docs(
    filename: str | pathlib.Path,
    doc_vars: list[DocVar] | None = None,
    *,
    raise_on_error: bool = False
) -> dict[str, str | dict]:
    """
    Use ast to search for assignment of the configured variables in the given file.
    YAML-parsable vars are loaded from YAML; others are returned as plain text.

    On failure, a warning is emitted and the partial data is returned. Pass
    ``raise_on_error=True`` to re-raise the original exception instead.
    """
    if doc_vars is None:
        doc_vars = list(_DEFAULT_DOC_VARS)

    specs = {v.name: v for v in doc_vars}

    data: dict[str, str | dict] = {}

    try:
        with open(filename, 'rb') as f:
            tree = ast.parse(f.read())

        for child in tree.body:
            if not isinstance(child, ast.Assign):
                continue

            for target in child.targets:
                if not isinstance(target, ast.Name):
                    continue
                if not isinstance(child.value, ast.Constant):
                    continue
                if not isinstance(child.value.value, str):
                    continue

                key = target.id

                spec = specs.get(target.id)
                if spec is None:
                    continue

                if spec.parse_yaml:
                    data[key] = yaml.safe_load(child.value.value)
                else:
                    data[key] = child.value.value

            if len(data) == len(doc_vars):
                return data

    except Exception as ex:
        if raise_on_error:
            raise
        warnings.warn(f"Unable to parse documentation in file {filename!r}: {ex}")

    return data
