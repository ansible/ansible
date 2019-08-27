#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a virtual module that is entirely implemented server side

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: win_template
version_added: "1.9.2"
options:
  backup:
    description:
    - Determine whether a backup should be created.
    - When set to C(yes), create a backup file including the timestamp information
      so you can get the original file back if you somehow clobbered it incorrectly.
    type: bool
    default: no
    version_added: '2.8'
  newline_sequence:
    default: '\r\n'
  force:
    version_added: '2.4'
notes:
- Beware fetching files from windows machines when creating templates because certain tools, such as Powershell ISE,
  and regedit's export facility add a Byte Order Mark as the first character of the file, which can cause tracebacks.
- You can use the M(win_copy) module with the C(content:) option if you prefer the template inline, as part of the
  playbook.
- For Linux you can use M(template) which uses '\\n' as C(newline_sequence) by default.
seealso:
- module: win_copy
- module: copy
- module: template
author:
- Jon Hawkesworth (@jhawkesworth)
extends_documentation_fragment:
- template_common
'''

EXAMPLES = r'''
- name: Create a file from a Jinja2 template
  win_template:
    src: /mytemplates/file.conf.j2
    dest: C:\Temp\file.conf

- name: Create a Unix-style file from a Jinja2 template
  win_template:
    src: unix/config.conf.j2
    dest: C:\share\unix\config.conf
    newline_sequence: '\n'
    backup: yes
'''

RETURN = r'''
backup_file:
    description: Name of the backup file that was created.
    returned: if backup=yes
    type: str
    sample: C:\Path\To\File.txt.11540.20150212-220915.bak
'''
