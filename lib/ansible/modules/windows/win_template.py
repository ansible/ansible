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
notes:
  - "templates are loaded with C(trim_blocks=True)."
  - By default, windows line endings are not created in the generated file.
  - "In order to ensure windows line endings are in the generated file, add the following header
    as the first line of your template: ``#jinja2: newline_sequence:'\\r\\n'`` and ensure each line
    of the template ends with \\\\r\\\\n"
  - Beware fetching files from windows machines when creating templates
    because certain tools, such as Powershell ISE,  and regedit's export facility
    add a Byte Order Mark as the first character of the file, which can cause tracebacks.
  - Use "od -cx" to examine your templates for Byte Order Marks.
author: "Jon Hawkesworth (@jhawkesworth)"
'''

EXAMPLES = r'''
- name: Create a file from a Jinja2 template
  win_template:
    src: /mytemplates/file.conf.j2
    dest: C:\temp\file.conf
'''
