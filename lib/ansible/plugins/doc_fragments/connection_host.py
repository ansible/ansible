# Copyright (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations


class ModuleDocFragment(object):

    # common shelldocumentation fragment
    DOCUMENTATION = """
options:
    remote_addr:
        version_added: '2.19'
        type: str
        description:
          - The inventory host address, potentially displayed by debug messages and callback plugins.
        vars:
          - name: ansible_host
"""
