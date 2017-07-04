# this is a virtual module that is entirely implemented server side

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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = r'''
---
module: win_template
version_added: "1.9.2"
short_description: Templates a file out to a remote server.
description:
     - Templates are processed by the Jinja2 templating language
       (U(http://jinja.pocoo.org/docs/)) - documentation on the template
       formatting can be found in the Template Designer Documentation
       (U(http://jinja.pocoo.org/docs/templates/)).
     - "Six additional variables can be used in templates: C(ansible_managed)
       (configurable via the C(defaults) section of C(ansible.cfg)) contains a string
       which can be used to describe the template name, host, modification time of the
       template file and the owner uid, C(template_host) contains the node name of
       the template's machine, C(template_uid) the owner, C(template_path) the
       absolute path of the template, C(template_fullpath) is the absolute path of the
       template, and C(template_run_date) is the date that the template was rendered. Note that including
       a string that uses a date in the template will result in the template being marked 'changed'
       each time."
options:
  src:
    description:
      - Path of a Jinja2 formatted template on the local server. This can be a relative or absolute path.
    required: true
  dest:
    description:
      - Location to render the template to on the remote machine.
    required: true
  newline_sequence:
    description:
      - Specify the newline sequence to use for templating files.
    choices: [ '\n', '\r', '\r\n' ]
    default: '\r\n'
    version_added: '2.4'
  block_start_string:
    description:
      - The string marking the beginning of a block.
    default: '{%'
    version_added: '2.4'
  block_end_string:
    description:
      - The string marking the end of a block.
    default: '%}'
    version_added: '2.4'
  variable_start_string:
    description:
      - The string marking the beginning of a print statement.
    default: '{{'
    version_added: '2.4'
  variable_end_string:
    description:
      - The string marking the end of a print statement.
    default: '}}'
    version_added: '2.4'
  trim_blocks:
    description:
      - If this is set to True the first newline after a block is removed (block, not variable tag!).
    default: "no"
    version_added: '2.4'
  force:
    description:
      - the default is C(yes), which will replace the remote file when contents
        are different than the source.  If C(no), the file will only be transferred
        if the destination does not exist.
    choices: [ "yes", "no" ]
    default: "yes"
    version_added: '2.4'
notes:
  - For other platforms you can use M(template) which uses '\n' as C(newline_sequence).
  - Templates are loaded with C(trim_blocks=True).
  - Beware fetching files from windows machines when creating templates
    because certain tools, such as Powershell ISE,  and regedit's export facility
    add a Byte Order Mark as the first character of the file, which can cause tracebacks.
  - To find Byte Order Marks in files, use C(Format-Hex <file> -Count 16) on Windows, and use C(od -a -t x1 -N 16 <file>) on Linux.
  - "Also, you can override jinja2 settings by adding a special header to template file.
    i.e. C(#jinja2:variable_start_string:'[%', variable_end_string:'%]', trim_blocks: False)
    which changes the variable interpolation markers to  [% var %] instead of  {{ var }}.
    This is the best way to prevent evaluation of things that look like, but should not be Jinja2.
    raw/endraw in Jinja2 will not work as you expect because templates in Ansible are recursively evaluated."
author: "Jon Hawkesworth (@jhawkesworth)"
'''

EXAMPLES = r'''
- name: Create a file from a Jinja2 template
  win_template:
    src: /mytemplates/file.conf.j2
    dest: C:\temp\file.conf

- name: Create a Unix-style file from a Jinja2 template
  win_template:
    src: unix/config.conf.j2
    dest: C:\share\unix\config.conf
    newline_sequence: '\n'
'''
