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

DOCUMENTATION = '''
---
module: template
version_added: historical
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
      - Path of a Jinja2 formatted template on the Ansible controller. This can be a relative or absolute path.
    required: true
  dest:
    description:
      - Location to render the template to on the remote machine.
    required: true
  backup:
    description:
      - Create a backup file including the timestamp information so you can get
        the original file back if you somehow clobbered it incorrectly.
    required: false
    choices: [ "yes", "no" ]
    default: "no"
  force:
    description:
      - the default is C(yes), which will replace the remote file when contents
        are different than the source.  If C(no), the file will only be transferred
        if the destination does not exist.
    required: false
    choices: [ "yes", "no" ]
    default: "yes"
notes:
  - "Since Ansible version 0.9, templates are loaded with C(trim_blocks=True)."
author:
    - Ansible Core Team
    - Michael DeHaan
extends_documentation_fragment:
    - files
    - validate
'''

EXAMPLES = '''
# Example from Ansible Playbooks
- template: src=/mytemplates/foo.j2 dest=/etc/file.conf owner=bin group=wheel mode=0644

# The same example, but using symbolic modes equivalent to 0644
- template: src=/mytemplates/foo.j2 dest=/etc/file.conf owner=bin group=wheel mode="u=rw,g=r,o=r"

# Copy a new "sudoers" file into place, after passing validation with visudo
- template: src=/mine/sudoers dest=/etc/sudoers validate='visudo -cf %s'
'''
