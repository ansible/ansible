# Copyright (c) 2022 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = """
    name: deprecated_with_docs
    short_description: test lookup
    description: test lookup
    author: Ansible Core Team
    version_added: "2.14"
    deprecated:
        why: reasons
        alternative: other thing
        removed_in: "2.16"
        removed_from_collection: "ansible.legacy"
    options: {}
"""

EXAMPLE = """
"""

RETURN = """
"""
