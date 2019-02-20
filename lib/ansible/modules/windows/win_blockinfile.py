#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_blockinfile
short_description: Insert/update/remove a text block surrounded by marker lines
version_added: '2.8'
description:
- This module will insert/update/remove a block of multi-line text surrounded by customizable marker lines.
options:
  path:
    description:
      - The path of the file to modify.
      - Before Ansible 2.3 this option was only usable as I(dest), I(destfile) and I(name).
    type: path
    required: yes
    aliases: [ dest, destfile, name ]
  state:
    description:
      - Whether the line should be there or not.
    type: str
    choices: [ absent, present ]
    default: present
  marker:
    description:
    - The marker line template.
    - C({mark}) will be replaced with the values C(in marker_begin) (default="BEGIN") and C(marker_end) (default="END").
    - Using a custom marker without the C({mark}) variable may result in the block being repeatedly inserted on subsequent playbook runs.
    type: str
    default: '# {mark} ANSIBLE MANAGED BLOCK'
  block:
    description:
    - The text to insert inside the marker lines.
    - If it is missing or an empty string, the block will be removed as if C(state) were specified to C(absent).
    type: str
    default: ''
    aliases: [ content ]
  insertafter:
    description:
      - Used with C(state=present). If specified, the line will be inserted after the last match of specified regular expression. A special value is
        available; C(EOF) for inserting the line at the end of the file.
      - If specified regular expression has no matches, EOF will be used instead. May not be used with C(backrefs).
    type: str
    choices: [ EOF, '*regex*' ]
    default: EOF
  insertbefore:
    description:
      - Used with C(state=present). If specified, the line will be inserted before the last match of specified regular expression. A value is available;
        C(BOF) for inserting the line at the beginning of the file.
      - If specified regular expression has no matches, the line will be inserted at the end of the file. May not be used with C(backrefs).
    type: str
    choices: [ BOF, '*regex*' ]
  create:
    description:
      - Used with C(state=present). If specified, the file will be created if it does not already exist. By default it will fail if the file is missing.
    type: bool
    default: no
  backup:
    description:
      - Create a backup file including the timestamp information so you can get the original file back if you somehow clobbered it incorrectly.
    type: bool
    default: no
  encoding:
    description:
      - Specifies the encoding of the source text file to operate on (and thus what the output encoding will be). The default of C(auto) will cause
        the module to auto-detect the encoding of the source file and ensure that the modified file is written with the same encoding.
      - An explicit encoding can be passed as a string that is a valid value to pass to the .NET framework System.Text.Encoding.GetEncoding() method -
        see U(https://msdn.microsoft.com/en-us/library/system.text.encoding%28v=vs.110%29.aspx).
      - This is mostly useful with C(create=yes) if you want to create a new file with a specific encoding. If C(create=yes) is specified without a
        specific encoding, the default encoding (UTF-8, no BOM) will be used.
    type: str
    default: auto
  newline:
    description:
      - Specifies the line separator style to use for the modified file. This defaults to the windows line separator (C(\r\n)). Note that the indicated
        line separator will be used for file output regardless of the original line separator that appears in the input file.
    type: str
    choices: [ unix, windows ]
    default: windows
  marker_begin:
    description:
    - This will be inserted at C({mark}) in the opening ansible block marker.
    type: str
    default: BEGIN
  marker_end:
    description:
    - This will be inserted at C({mark}) in the closing ansible block marker.
    type: str
    default: END
notes:
  - This module supports check mode.
  - When using 'with_*' loops be aware that if you do not set a unique mark the block will be overwritten on each iteration.
  - When more then one block should be handled in one file you must change the I(marker) per task.
  - Unlike I(blockinfile), this module will not create parent folders for the destination file when I(create) is specified and the file does not exist.
  - When using an I(insertbefore) or I(insertafter) directive the block will be inserted before/after the last matching
    line (to maintain parity with I(blockinfile)).
seealso:
- module: win_lineinfile
- module: blockinfile
author:
- Marcus Watkins (@marwatk)
'''

EXAMPLES = r'''
- name: Add some hosts entries
  blockinfile:
    path: C:\Windows\System32\drivers\etc\hosts
    block: |
      127.0.0.1 foobar
      192.168.1.10 barfoo

- name: Insert/Update HTML surrounded by custom markers after <body> line
  blockinfile:
    path: C:\webserver\html\index.html
    marker: "<!-- {mark} ANSIBLE MANAGED BLOCK -->"
    insertafter: "<body>"
    content: |
      <h1>Welcome to {{ ansible_hostname }}</h1>
      <p>Last updated on {{ ansible_date_time.iso8601 }}</p>

- name: Remove HTML as well as surrounding markers
  blockinfile:
    path: C:\webserver\html\index.html
    marker: "<!-- {mark} ANSIBLE MANAGED BLOCK -->"
    content: ""

- name: Add mappings to /etc/hosts
  blockinfile:
    path: C:\Windows\System32\drivers\etc\hosts
    block: |
      {{ item.ip }} {{ item.name }}
    marker: "# {mark} ANSIBLE MANAGED BLOCK {{ item.name }}"
  with_items:
  - { name: host1, ip: 10.10.1.10 }
  - { name: host2, ip: 10.10.1.11 }
  - { name: host3, ip: 10.10.1.12 }
'''

RETURN = r'''
'''
