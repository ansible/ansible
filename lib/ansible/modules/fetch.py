# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# This is a virtual module that is entirely implemented as an action plugin and runs on the controller

from __future__ import annotations


DOCUMENTATION = r"""
---
module: fetch
short_description: Fetch files from remote nodes
description:
- This module works like M(ansible.builtin.copy), but in reverse.
- It is used for fetching files from remote machines and storing them locally in a file tree, organized by hostname.
- Files that already exist at O(dest) will be overwritten if they are different than the O(src).
- This module is also supported for Windows targets.
version_added: '0.2'
options:
  src:
    description:
    - The file on the remote system to fetch.
    - This I(must) be a file, not a directory.
    - Recursive fetching may be supported in a later release.
    required: yes
  dest:
    description:
    - A directory to save the file into.
    - For example, if O(dest=/backup), then O(src=/etc/profile) on host
      C(host.example.com), would save the file into C(/backup/host.example.com/etc/profile).
      The host name is based on the inventory name.
    required: yes
  fail_on_missing:
    version_added: '1.1'
    description:
    - When set to V(true), the task will fail if the remote file cannot be read for any reason.
    - Prior to Ansible 2.5, setting this would only fail if the source file was missing.
    - The default was changed to V(true) in Ansible 2.5.
    type: bool
    default: yes
  validate_checksum:
    version_added: '1.4'
    description:
    - Verify that the source and destination checksums match after the files are fetched.
    type: bool
    default: yes
  flat:
    version_added: '1.2'
    description:
    - Allows you to override the default behavior of appending hostname/path/to/file to the destination.
    - If O(dest) ends with '/', it will use the basename of the source file, similar to the copy module.
    - This can be useful if working with a single host, or if retrieving files that are uniquely named per host.
    - If using multiple hosts with the same filename, the file will be overwritten for each host.
    type: bool
    default: no
extends_documentation_fragment:
    - action_common_attributes
    - action_common_attributes.files
    - action_common_attributes.flow
attributes:
  action:
    support: full
  async:
    support: none
  bypass_host_loop:
    support: none
  check_mode:
    support: full
  diff_mode:
    support: full
  platform:
    platforms: posix, windows
  safe_file_operations:
    support: none
  vault:
    support: none
notes:
- When running fetch with C(become), the M(ansible.builtin.slurp) module will also be
  used to fetch the contents of the file for determining the remote
  checksum. This effectively doubles the transfer size, and
  depending on the file size can consume all available memory on the
  remote or local hosts causing a C(MemoryError). Due to this it is
  advisable to run this module without C(become) whenever possible.
- Prior to Ansible 2.5 this module would not fail if reading the remote
  file was impossible unless O(fail_on_missing) was set.
- In Ansible 2.5 or later, playbook authors are encouraged to use
  C(fail_when) or C(ignore_errors) to get this ability. They may
  also explicitly set O(fail_on_missing) to V(false) to get the
  non-failing behaviour.
- Ansible 2.19 and onwards, SHA256 is used to calculate checksum.
seealso:
- module: ansible.builtin.copy
- module: ansible.builtin.slurp
author:
- Ansible Core Team
- Michael DeHaan
"""

EXAMPLES = r"""
- name: Store file into /tmp/fetched/host.example.com/tmp/somefile
  ansible.builtin.fetch:
    src: /tmp/somefile
    dest: /tmp/fetched

- name: Specifying a path directly
  ansible.builtin.fetch:
    src: /tmp/somefile
    dest: /tmp/prefix-{{ inventory_hostname }}
    flat: yes

- name: Specifying a destination path
  ansible.builtin.fetch:
    src: /tmp/uniquefile
    dest: /tmp/special/
    flat: yes

- name: Storing in a path relative to the playbook
  ansible.builtin.fetch:
    src: /tmp/uniquefile
    dest: special/prefix-{{ inventory_hostname }}
    flat: yes
"""
