# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations


class ModuleDocFragment(object):

    # common shelldocumentation fragment
    DOCUMENTATION = """
options:
    pipelining:
          default: false
          description:
            - Pipelining reduces the number of connection operations required to execute a module on the remote server,
              by executing many Ansible modules without actual file transfers.
            - This can result in a very significant performance improvement when enabled.
            - However this can conflict with privilege escalation (C(become)).
              For example, when using sudo operations you must first disable C(requiretty) in the sudoers file for the target hosts,
              which is why this feature is disabled by default.
          env:
            - name: ANSIBLE_PIPELINING
          ini:
            - section: defaults
              key: pipelining
            - section: connection
              key: pipelining
          type: boolean
          vars:
            - name: ansible_pipelining
"""
