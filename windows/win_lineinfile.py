#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = """
---
module: win_lineinfile
author: "Brian Lloyd <brian.d.lloyd@gmail.com>"
short_description: Ensure a particular line is in a file, or replace an existing line using a back-referenced regular expression.
description:
  - This module will search a file for a line, and ensure that it is present or absent.
  - This is primarily useful when you want to change a single line in a file only.
version_added: "2.0"
options:
  dest:
    required: true
    aliases: [ name, destfile ]
    description:
      - The path of the file to modify.
  regexp:
    required: false
    description:
      - "The regular expression to look for in every line of the file. For C(state=present), the pattern to replace if found; only the last line found will be replaced. For C(state=absent), the pattern of the line to remove.  Uses .NET compatible regular expressions; see U(https://msdn.microsoft.com/en-us/library/hs600312%28v=vs.110%29.aspx)."
  state:
    required: false
    choices: [ present, absent ]
    default: "present"
    description:
      - Whether the line should be there or not.
  line:
    required: false
    description:
      - Required for C(state=present). The line to insert/replace into the file. If C(backrefs) is set, may contain backreferences that will get expanded with the C(regexp) capture groups if the regexp matches.
  backrefs:
    required: false
    default: "no"
    choices: [ "yes", "no" ]
    description:
      - Used with C(state=present). If set, line can contain backreferences (both positional and named) that will get populated if the C(regexp) matches. This flag changes the operation of the module slightly; C(insertbefore) and C(insertafter) will be ignored, and if the C(regexp) doesn't match anywhere in the file, the file will be left unchanged.
      - If the C(regexp) does match, the last matching line will be replaced by the expanded line parameter.
  insertafter:
    required: false
    default: EOF
    description:
      - Used with C(state=present). If specified, the line will be inserted after the last match of specified regular expression. A special value is available; C(EOF) for inserting the line at the end of the file.
      - If specified regular expresion has no matches, EOF will be used instead.  May not be used with C(backrefs).
    choices: [ 'EOF', '*regex*' ]
  insertbefore:
    required: false
    description:
      - Used with C(state=present). If specified, the line will be inserted before the last match of specified regular expression. A value is available; C(BOF) for inserting the line at the beginning of the file.
      - If specified regular expresion has no matches, the line will be inserted at the end of the file.  May not be used with C(backrefs).
    choices: [ 'BOF', '*regex*' ]
  create:
    required: false
    choices: [ "yes", "no" ]
    default: "no"
    description:
      - Used with C(state=present). If specified, the file will be created if it does not already exist. By default it will fail if the file is missing.
  backup:
    required: false
    default: "no"
    choices: [ "yes", "no" ]
    description:
      - Create a backup file including the timestamp information so you can get the original file back if you somehow clobbered it incorrectly.
  validate:
    required: false
    description:
      - Validation to run before copying into place.  Use %s in the command to indicate the current file to validate.
      - The command is passed securely so shell features like expansion and pipes won't work.
    default: None
  encoding:
    required: false
    default: "auto"
    description:
      - Specifies the encoding of the source text file to operate on (and thus what the output encoding will be). The default of C(auto) will cause the module to auto-detect the encoding of the source file and ensure that the modified file is written with the same encoding.
      - "An explicit encoding can be passed as a string that is a valid value to pass to the .NET framework System.Text.Encoding.GetEncoding() method - see U(https://msdn.microsoft.com/en-us/library/system.text.encoding%28v=vs.110%29.aspx)."
      - This is mostly useful with C(create=yes) if you want to create a new file with a specific encoding. If C(create=yes) is specified without a specific encoding, the default encoding (UTF-8, no BOM) will be used.
  newline:
    required: false
    description:
      - "Specifies the line separator style to use for the modified file. This defaults to the windows line separator (\r\n). Note that the indicated line separator will be used for file output regardless of the original line seperator that appears in the input file."
    choices: [ "windows", "unix" ]
    default: "windows"
"""

EXAMPLES = """
- win_lineinfile: dest=C:\\temp\\example.conf regexp=^name= line="name=JohnDoe"

- win_lineinfile: dest=C:\\temp\\example.conf state=absent regexp="^name="

- win_lineinfile: dest=C:\\temp\\example.conf regexp='^127\.0\.0\.1' line='127.0.0.1 localhost'

- win_lineinfile: dest=C:\\temp\\httpd.conf regexp="^Listen " insertafter="^#Listen " line="Listen 8080"

- win_lineinfile: dest=C:\\temp\\services regexp="^# port for http" insertbefore="^www.*80/tcp" line="# port for http by default"

# Create file if it doesnt exist with a specific encoding
- win_lineinfile: dest=C:\\temp\\utf16.txt create="yes" encoding="utf-16" line="This is a utf-16 encoded file"

# Add a line to a file and ensure the resulting file uses unix line separators
- win_lineinfile: dest=C:\\temp\\testfile.txt line="Line added to file" newline="unix"

"""
