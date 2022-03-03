# -*- coding: utf-8 -*-
# Copyright: (c) 2019-2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Version comparison helpers."""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import operator

from ansible.module_utils.compat.version import LooseVersion
from ansible.utils.version import SemanticVersion


def is_pre_release(version):
    # type: (str) -> bool
    """Figure out if a given version is a pre-release."""
    try:
        return SemanticVersion(version).is_prerelease
    except ValueError:
        return False


def meets_requirements(version, requirements):
    # type: (str, str) -> bool
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
    op_map = {
        '!=': operator.ne,
        '==': operator.eq,
        '=': operator.eq,
        '>=': operator.ge,
        '>': operator.gt,
        '<=': operator.le,
        '<': operator.lt,
    }

    for req in requirements.split(','):
        op_pos = 2 if len(req) > 1 and req[1] == '=' else 1
        op = op_map.get(req[:op_pos])

        requirement = req[op_pos:]
        if not op:
            requirement = req
            op = operator.eq

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
