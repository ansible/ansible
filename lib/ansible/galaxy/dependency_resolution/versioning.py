# -*- coding: utf-8 -*-
# Copyright: (c) 2019-2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Version comparison helpers."""

from __future__ import annotations

import operator
import typing as t

from ansible.module_utils.compat.version import LooseVersion
from ansible.utils.version import SemanticVersion

_OPERATORS = {
    '!=': operator.ne,
    '==': operator.eq,
    '=': operator.eq,
    '>=': operator.ge,
    '>': operator.gt,
    '<=': operator.le,
    '<': operator.lt,
}


def is_pre_release(version: str) -> bool:
    """Figure out if a given version is a pre-release."""
    try:
        return SemanticVersion(version).is_prerelease
    except ValueError:
        return False


def _split_requirement(req: str) -> tuple[t.Callable[[t.Any, t.Any], bool], str]:
    """Split a single requirement into its operator and version, ignoring surrounding whitespace."""
    req = req.strip()
    op_pos = 2 if len(req) > 1 and req[1] == '=' else 1
    if op := _OPERATORS.get(req[:op_pos]):
        return op, req[op_pos:].lstrip()

    return operator.eq, req


def is_valid_version_spec(version_spec: object) -> bool:
    """Check that every ','-delimited requirement is '*' or an optional operator followed by a version."""
    if not isinstance(version_spec, str):
        return False

    for req in version_spec.split(','):
        requirement = _split_requirement(req)[1]
        if requirement == '*':
            continue

        if not requirement:
            return False

        try:
            SemanticVersion.from_loose_version(LooseVersion(requirement))
        except ValueError:
            return False

    return True


def meets_requirements(version: str, requirements: str) -> bool:
    """Verify if a given version satisfies all the requirements.

    Supported version identifiers are:
      * '=='
      * '!='
      * '>'
      * '>='
      * '<'
      * '<='
      * '*'

    Each requirement is delimited by ','.
    """
    for req in requirements.split(','):
        op, requirement = _split_requirement(req)

        if requirement == '*' or version == '*':
            continue

        if not op(
                SemanticVersion(version),
                SemanticVersion.from_loose_version(LooseVersion(requirement)),
        ):
            break
    else:
        return True

    # The loop was broken early, it does not meet all the requirements
    return False
