# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import re

from ansible.errors import AnsibleError


def compile_validation_pattern(pattern: object) -> re.Pattern[str] | None:
    """Compile an optional vars_prompt validation expression before prompting."""
    if pattern is None:
        return None
    if not isinstance(pattern, str):
        raise AnsibleError("The vars_prompt validate option must be a string.", obj=pattern)
    try:
        return re.compile(pattern)
    except re.error as ex:
        raise AnsibleError("Invalid regular expression in vars_prompt validate.", obj=pattern) from ex
