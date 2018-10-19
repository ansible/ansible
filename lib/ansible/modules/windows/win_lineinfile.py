#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_lineinfile
author:
- Brian Lloyd (@brianlloyd)
short_description: Ensure a particular line is in a file, or replace an existing line using a back-referenced regular expression
description:
  - This module will search a file for a line, and ensure that it is present or absent.
  - This is primarily useful when you want to change a single line in a file only.
version_added: "2.0"
options:
  path:
    description:
      - The path of the file to modify.
      - Note that the Windows path delimiter C(\) must be escaped as C(\\) when the line is double quoted.
      - Before 2.3 this option was only usable as I(dest), I(destfile) and I(name).
    required: yes
    type: path
    aliases: [ dest, destfile, name ]
  regexp:
    description:
      - The regular expression to look for in every line of the file. For C(state=present), the pattern to replace if found; only the last line found
        will be replaced. For C(state=absent), the pattern of the line to remove. Uses .NET compatible regular expressions;
        see U(https://msdn.microsoft.com/en-us/library/hs600312%28v=vs.110%29.aspx).
  state:
    description:
      - Whether the line should be there or not.
    choices: [ absent, present ]
    default: present
  line:
    description:
      - Required for C(state=present). The line to insert/replace into the file. If C(backrefs) is set, may contain backreferences that will get
        expanded with the C(regexp) capture groups if the regexp matches.
      - Be aware that the line is processed first on the controller and thus is dependent on yaml quoting rules. Any double quoted line
        will have control characters, such as '\r\n', expanded. To print such characters literally, use single or no quotes.
  backrefs:
    description:
      - Used with C(state=present). If set, line can contain backreferences (both positional and named) that will get populated if the C(regexp)
        matches. This flag changes the operation of the module slightly; C(insertbefore) and C(insertafter) will be ignored, and if the C(regexp)
        doesn't match anywhere in the file, the file will be left unchanged.
      - If the C(regexp) does match, the last matching line will be replaced by the expanded line parameter.
    type: bool
    default: 'no'
  insertafter:
    description:
      - Used with C(state=present). If specified, the line will be inserted after the last match of specified regular expression. A special value is
        available; C(EOF) for inserting the line at the end of the file.
      - If specified regular expression has no matches, EOF will be used instead. May not be used with C(backrefs).
    choices: [ EOF, '*regex*' ]
    default: EOF
  insertbefore:
    description:
      - Used with C(state=present). If specified, the line will be inserted before the last match of specified regular expression. A value is available;
        C(BOF) for inserting the line at the beginning of the file.
      - If specified regular expression has no matches, the line will be inserted at the end of the file. May not be used with C(backrefs).
    choices: [ BOF, '*regex*' ]
  create:
    description:
      - Used with C(state=present). If specified, the file will be created if it does not already exist. By default it will fail if the file is missing.
    type: bool
    default: 'no'
  backup:
    description:
      - Create a backup file including the timestamp information so you can get the original file back if you somehow clobbered it incorrectly.
    type: bool
    default: 'no'
  validate:
    description:
      - Validation to run before copying into place. Use %s in the command to indicate the current file to validate.
      - The command is passed securely so shell features like expansion and pipes won't work.
  encoding:
    description:
      - Specifies the encoding of the source text file to operate on (and thus what the output encoding will be). The default of C(auto) will cause
        the module to auto-detect the encoding of the source file and ensure that the modified file is written with the same encoding.
      - An explicit encoding can be passed as a string that is a valid value to pass to the .NET framework System.Text.Encoding.GetEncoding() method -
        see U(https://msdn.microsoft.com/en-us/library/system.text.encoding%28v=vs.110%29.aspx).
      - This is mostly useful with C(create=yes) if you want to create a new file with a specific encoding. If C(create=yes) is specified without a
        specific encoding, the default encoding (UTF-8, no BOM) will be used.
    default: auto
  newline:
    description:
      - Specifies the line separator style to use for the modified file. This defaults to the windows line separator (C(\r\n)). Note that the indicated
        line separator will be used for file output regardless of the original line separator that appears in the input file.
    choices: [ unix, windows ]
    default: windows
notes:
  - As of Ansible 2.3, the I(dest) option has been changed to I(path) as default, but I(dest) still works as well.
'''

EXAMPLES = r'''
# Before 2.3, option 'dest', 'destfile' or 'name' was used instead of 'path'
- name: insert path without converting \r\n
  win_lineinfile:
    path: c:\file.txt
    line: c:\return\new

- win_lineinfile:
    path: C:\Temp\example.conf
    regexp: '^name='
    line: 'name=JohnDoe'

- win_lineinfile:
    path: C:\Temp\example.conf
    regexp: '^name='
    state: absent

- win_lineinfile:
    path: C:\Temp\example.conf
    regexp: '^127\.0\.0\.1'
    line: '127.0.0.1 localhost'

- win_lineinfile:
    path: C:\Temp\httpd.conf
    regexp: '^Listen '
    insertafter: '^#Listen '
    line: Listen 8080

- win_lineinfile:
    path: C:\Temp\services
    regexp: '^# port for http'
    insertbefore: '^www.*80/tcp'
    line: '# port for http by default'

# Create file if it doesn't exist with a specific encoding
- win_lineinfile:
    path: C:\Temp\utf16.txt
    create: yes
    encoding: utf-16
    line: This is a utf-16 encoded file

# Add a line to a file and ensure the resulting file uses unix line separators
- win_lineinfile:
    path: C:\Temp\testfile.txt
    line: Line added to file
    newline: unix

# Update a line using backrefs
- win_lineinfile:
    path: C:\Temp\example.conf
    backrefs: yes
    regexp: '(^name=)'
    line: '$1JohnDoe'
'''
