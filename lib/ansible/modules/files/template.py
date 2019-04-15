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
description:
- Templates are processed by the L(Jinja2 templating language,http://jinja.pocoo.org/docs/).
- Documentation on the template formatting can be found in the
  L(Template Designer Documentation,http://jinja.pocoo.org/docs/templates/).
- Additional variables listed below can be used in templates.
- C(ansible_managed) (configurable via the C(defaults) section of C(ansible.cfg)) contains a string which can be used to
  describe the template name, host, modification time of the template file and the owner uid.
- C(template_host) contains the node name of the template's machine.
- C(template_uid) is the numeric user id of the owner.
- C(template_path) is the path of the template.
- C(template_fullpath) is the absolute path of the template.
- C(template_destpath) is the path of the template on the remote system (added in 2.8).
- C(template_run_date) is the date that the template was rendered.
options:
  src:
    description:
    - Path of a Jinja2 formatted template on the Ansible controller.
    - This can be a relative or an absolute path.
    type: path
    required: yes
  dest:
    description:
    - Location to render the template to on the remote machine.
    type: path
    required: yes
  backup:
    description:
    - Determine whether a backup should be created.
    - When set to C(yes), create a backup file including the timestamp information
      so you can get the original file back if you somehow clobbered it incorrectly.
    type: bool
    default: no
  newline_sequence:
    description:
    - Specify the newline sequence to use for templating files.
    type: str
    choices: [ '\n', '\r', '\r\n' ]
    default: '\n'
    version_added: '2.4'
  block_start_string:
    description:
    - The string marking the beginning of a block.
    type: str
    default: '{%'
    version_added: '2.4'
  block_end_string:
    description:
    - The string marking the end of a block.
    type: str
    default: '%}'
    version_added: '2.4'
  variable_start_string:
    description:
    - The string marking the beginning of a print statement.
    type: str
    default: '{{'
    version_added: '2.4'
  variable_end_string:
    description:
    - The string marking the end of a print statement.
    type: str
    default: '}}'
    version_added: '2.4'
  trim_blocks:
    description:
    - Determine when newlines should be removed from blocks.
    - When set to C(yes) the first newline after a block is removed (block, not variable tag!).
    type: bool
    default: yes
    version_added: '2.4'
  lstrip_blocks:
    description:
    - Determine when leading spaces and tabs should be stripped.
    - When set to C(yes) leading spaces and tabs are stripped from the start of a line to a block.
    - This functionality requires Jinja 2.7 or newer.
    type: bool
    default: no
    version_added: '2.6'
  force:
    description:
    - Determine when the file is being transferred if the destination already exists.
    - When set to C(yes), replace the remote file when contents are different than the source.
    - When set to C(no), the file will only be transferred if the destination does not exist.
    type: bool
    default: yes
  follow:
    description:
    - Determine whether symbolic links should be followed.
    - When set to C(yes) symbolic links will be followed, if they exist.
    - When set to C(no) symbolic links will not be followed.
    - Previous to Ansible 2.4, this was hardcoded as C(yes).
    type: bool
    default: no
    version_added: '2.4'
  output_encoding:
    description:
    - Overrides the encoding used to write the template file defined by C(dest).
    - It defaults to C(utf-8), but any encoding supported by python can be used.
    - The source template file must always be encoded using C(utf-8), for homogeneity.
    type: str
    default: utf-8
    version_added: '2.7'
notes:
- Including a string that uses a date in the template will result in the template being marked 'changed' each time.
- Since Ansible 0.9, templates are loaded with C(trim_blocks=True).
- >
  Also, you can override jinja2 settings by adding a special header to template file.
  i.e. C(#jinja2:variable_start_string:'[%', variable_end_string:'%]', trim_blocks: False)
  which changes the variable interpolation markers to C([% var %]) instead of C({{ var }}).
  This is the best way to prevent evaluation of things that look like, but should not be Jinja2.
- Using raw/endraw in Jinja2 will not work as you expect because templates in Ansible are recursively
  evaluated.
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
- files
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
    src: named.conf_{{ ansible_os_family}}.j2
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
