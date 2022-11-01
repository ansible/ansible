# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# This is a virtual module that is entirely implemented as an action plugin and runs on the controller

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: template
version_added: historical
short_description: Template a file out to a target host
options:
  follow:
    description:
    - Determine whether symbolic links should be followed.
    - When set to C(true) symbolic links will be followed, if they exist.
    - When set to C(false) symbolic links will not be followed.
    - Previous to Ansible 2.4, this was hardcoded as C(true).
    type: bool
    default: no
    version_added: '2.4'
notes:
- For Windows you can use M(ansible.windows.win_template) which uses C(\r\n) as C(newline_sequence) by default.
- The C(jinja2_native) setting has no effect. Native types are never used in the C(template) module which is by design used for generating text files.
  For working with templates and utilizing Jinja2 native types see the C(jinja2_native) parameter of the C(template lookup).
seealso:
- module: ansible.builtin.copy
- module: ansible.windows.win_copy
- module: ansible.windows.win_template
author:
- Ansible Core Team
- Michael DeHaan
extends_documentation_fragment:
- action_common_attributes
- action_common_attributes.flow
- action_common_attributes.files
- backup
- files
- template_common
- validate
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
      platforms: posix
    safe_file_operations:
      support: full
    vault:
      support: full
'''

EXAMPLES = r'''
- name: Template a file to /etc/file.conf
  ansible.builtin.template:
    src: /mytemplates/foo.j2
    dest: /etc/file.conf
    owner: bin
    group: wheel
    mode: '0644'

- name: Template a file, using symbolic modes (equivalent to 0644)
  ansible.builtin.template:
    src: /mytemplates/foo.j2
    dest: /etc/file.conf
    owner: bin
    group: wheel
    mode: u=rw,g=r,o=r

- name: Copy a version of named.conf that is dependent on the OS. setype obtained by doing ls -Z /etc/named.conf on original file
  ansible.builtin.template:
    src: named.conf_{{ ansible_os_family }}.j2
    dest: /etc/named.conf
    group: named
    setype: named_conf_t
    mode: 0640

- name: Create a DOS-style text file from a template
  ansible.builtin.template:
    src: config.ini.j2
    dest: /share/windows/config.ini
    newline_sequence: '\r\n'

- name: Copy a new sudoers file into place, after passing validation with visudo
  ansible.builtin.template:
    src: /mine/sudoers
    dest: /etc/sudoers
    validate: /usr/sbin/visudo -cf %s

- name: Update sshd configuration safely, avoid locking yourself out
  ansible.builtin.template:
    src: etc/ssh/sshd_config.j2
    dest: /etc/ssh/sshd_config
    owner: root
    group: root
    mode: '0600'
    validate: /usr/sbin/sshd -t -f %s
    backup: yes
'''
