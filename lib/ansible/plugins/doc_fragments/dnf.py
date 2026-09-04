# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Ansible, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations


class ModuleDocFragment(object):

    # Standard documentation fragment shared by the dnf and dnf5 modules
    DOCUMENTATION = r"""
options:
  clean_requirements_on_remove:
    description:
      - If V(true), when removing a package with O(state=absent), also remove the
        dependencies that were installed for it and are no longer required by any other
        package.
      - Unlike O(autoremove), this only affects dependencies of the packages being
        removed in the current operation and does not perform a full system-wide sweep
        of orphaned packages.
      - When not set, the behavior falls back to the value of O(autoremove) to preserve
        backwards compatibility.
      - Only used when O(state=absent).
    type: bool
    version_added: "2.22"
"""
