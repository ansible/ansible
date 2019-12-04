#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# This is a virtual module that is entirely implemented as an action plugin and runs on the controller

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: template
version_added: historical
short_description: Template a file out to a remote server
options:
  follow:
    description:
    - Determine whether symbolic links should be followed.
    - When set to C(yes) symbolic links will be followed, if they exist.
    - When set to C(no) symbolic links will not be followed.
    - Previous to Ansible 2.4, this was hardcoded as C(yes).
    type: bool
    default: no
    version_added: '2.4'
notes:
- You can use the M(copy) module with the C(content:) option if you prefer the template inline,
  as part of the playbook.
- For Windows you can use M(win_template) which uses '\\r\\n' as C(newline_sequence) by default.
seealso:
- module: copy
- module: win_copy
- module: win_template
author:
- Ansible Core Team
- Michael DeHaan
extends_documentation_fragment:
- backup
- files
- template_common
- validate
'''

EXAMPLES = r'''
- name: Template a file to /etc/files.conf
  template:
    src: /mytemplates/foo.j2
    dest: /etc/file.conf
    owner: bin
    group: wheel
    mode: '0644'

- name: Template a file, using symbolic modes (equivalent to 0644)
  template:
    src: /mytemplates/foo.j2
    dest: /etc/file.conf
    owner: bin
    group: wheel
    mode: u=rw,g=r,o=r

- name: Copy a version of named.conf that is dependent on the OS. setype obtained by doing ls -Z /etc/named.conf on original file
  template:
    src: named.conf_{{ ansible_os_family }}.j2
    dest: /etc/named.conf
    group: named
    setype: named_conf_t
    mode: 0640

- name: Create a DOS-style text file from a template
  template:
    src: config.ini.j2
    dest: /share/windows/config.ini
    newline_sequence: '\r\n'

- name: Copy a new sudoers file into place, after passing validation with visudo
  template:
    src: /mine/sudoers
    dest: /etc/sudoers
    validate: /usr/sbin/visudo -cf %s

- name: Update sshd configuration safely, avoid locking yourself out
  template:
    src: etc/ssh/sshd_config.j2
    dest: /etc/ssh/sshd_config
    owner: root
    group: root
    mode: '0600'
    validate: /usr/sbin/sshd -t -f %s
    backup: yes
'''
