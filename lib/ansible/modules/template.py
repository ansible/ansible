# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# This is a virtual module that is entirely implemented as an action plugin and runs on the controller

from __future__ import annotations


DOCUMENTATION = r"""
---
module: template
version_added: historical
short_description: Template a file out to a target host
options:
  follow:
    description:
    - Determine whether symbolic links should be followed.
    - When set to V(true) symbolic links will be followed, if they exist.
    - When set to V(false) symbolic links will not be followed.
    - Previous to Ansible 2.4, this was hardcoded as V(true).
    type: bool
    default: no
    version_added: '2.4'
notes:
- For Windows you can use M(ansible.windows.win_template) which uses V(\\r\\n) as O(newline_sequence) by default.
- The C(jinja2_native) setting has no effect. Native types are never used in the M(ansible.builtin.template) module
  which is by design used for generating text files. For working with templates and utilizing Jinja2 native types see
  the O(ansible.builtin.template#lookup:jinja2_native) parameter of the P(ansible.builtin.template#lookup) lookup.
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
"""

EXAMPLES = r"""
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
    mode: '0640'

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
"""

RETURN = r"""
dest:
    description: Destination file/path, equal to the value passed to I(dest).
    returned: success
    type: str
    sample: /path/to/file.txt
checksum:
    description: SHA1 checksum of the rendered file
    returned: always
    type: str
    sample: 373296322247ab85d26d5d1257772757e7afd172
uid:
    description: Numeric id representing the file owner
    returned: success
    type: int
    sample: 1003
gid:
    description: Numeric id representing the group of the owner
    returned: success
    type: int
    sample: 1003
owner:
    description: User name of owner
    returned: success
    type: str
    sample: httpd
group:
    description: Group name of owner
    returned: success
    type: str
    sample: www-data
md5sum:
    description: MD5 checksum of the rendered file
    returned: changed
    type: str
    sample: d41d8cd98f00b204e9800998ecf8427e
mode:
    description: Unix permissions of the file in octal representation as a string
    returned: success
    type: str
    sample: 1755
size:
    description: Size of the rendered file in bytes
    returned: success
    type: int
    sample: 42
src:
    description: Source file used for the copy on the target machine.
    returned: changed
    type: str
    sample: /home/httpd/.ansible/tmp/ansible-tmp-1423796390.97-147729857856000/source
"""
