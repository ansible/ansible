# this is a virtual module that is entirely implemented server side
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: template
version_added: historical
short_description: Templates a file out to a remote server
description:
     - Templates are processed by the Jinja2 templating language
       (U(http://jinja.pocoo.org/docs/)) - documentation on the template
       formatting can be found in the Template Designer Documentation
       (U(http://jinja.pocoo.org/docs/templates/)).
     - "Six additional variables can be used in templates:
       C(ansible_managed) (configurable via the C(defaults) section of C(ansible.cfg)) contains a string which can be used to
          describe the template name, host, modification time of the template file and the owner uid.
       C(template_host) contains the node name of the template's machine.
       C(template_uid) the numeric user id of the owner.
       C(template_path) the path of the template.
       C(template_fullpath) is the absolute path of the template.
       C(template_run_date) is the date that the template was rendered."
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
    type: bool
    default: 'no'
  newline_sequence:
    description:
      - Specify the newline sequence to use for templating files.
    choices: [ '\n', '\r', '\r\n' ]
    default: '\n'
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
    type: bool
    default: 'no'
    version_added: '2.4'
  force:
    description:
      - the default is C(yes), which will replace the remote file when contents
        are different than the source.  If C(no), the file will only be transferred
        if the destination does not exist.
    type: bool
    default: 'yes'
notes:
  - For Windows you can use M(win_template) which uses '\r\n' as C(newline_sequence).
  - Including a string that uses a date in the template will result in the template being marked 'changed' each time
  - "Since Ansible version 0.9, templates are loaded with C(trim_blocks=True)."
  - "Also, you can override jinja2 settings by adding a special header to template file.
    i.e. C(#jinja2:variable_start_string:'[%', variable_end_string:'%]', trim_blocks: False)
    which changes the variable interpolation markers to  [% var %] instead of  {{ var }}.
    This is the best way to prevent evaluation of things that look like, but should not be Jinja2.
    raw/endraw in Jinja2 will not work as you expect because templates in Ansible are recursively evaluated."
  - You can use the C(copy) module with the C(content:) option if you prefer the template inline,
    as part of the playbook.
author:
    - Ansible Core Team
    - Michael DeHaan
extends_documentation_fragment:
    - files
    - validate
'''

EXAMPLES = r'''
# Example from Ansible Playbooks
- template:
    src: /mytemplates/foo.j2
    dest: /etc/file.conf
    owner: bin
    group: wheel
    mode: 0644

# The same example, but using symbolic modes equivalent to 0644
- template:
    src: /mytemplates/foo.j2
    dest: /etc/file.conf
    owner: bin
    group: wheel
    mode: "u=rw,g=r,o=r"

# Create a DOS-style text file from a template
- template:
    src: config.ini.j2
    dest: /share/windows/config.ini
    newline_sequence: '\r\n'

# Copy a new "sudoers" file into place, after passing validation with visudo
- template:
    src: /mine/sudoers
    dest: /etc/sudoers
    validate: '/usr/sbin/visudo -cf %s'

# Update sshd configuration safely, avoid locking yourself out
- template:
    src: etc/ssh/sshd_config.j2
    dest: /etc/ssh/sshd_config
    owner: root
    group: root
    mode: '0600'
    validate: /usr/sbin/sshd -t -f %s
    backup: yes
'''
