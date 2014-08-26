# this is a virtual module that is entirely implemented server side

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
      - Path of a Jinja2 formatted template on the local server. This can be a relative or absolute path.
    required: true
    default: null
    aliases: []
  dest:
    description:
      - Location to render the template to on the remote machine.
    required: true
    default: null
  backup:
    description:
      - Create a backup file including the timestamp information so you can get
        the original file back if you somehow clobbered it incorrectly.
    required: false
    choices: [ "yes", "no" ]
    default: "no"
  validate:
    description:
      - The validation command to run before copying into place. 
      - The path to the file to validate is passed in via '%s' which must be present as in the visudo example below.
      - validation to run before copying into place. The command is passed 
        securely so shell features like expansion and pipes won't work.
    required: false
    default: ""
    version_added: "1.2"
notes:
  - "Since Ansible version 0.9, templates are loaded with C(trim_blocks=True)."
requirements: []
author: Michael DeHaan
extends_documentation_fragment: files
'''

EXAMPLES = '''
# Example from Ansible Playbooks
- template: src=/mytemplates/foo.j2 dest=/etc/file.conf owner=bin group=wheel mode=0644

# The same example, but using symbolic modes equivalent to 0644
- template: src=/mytemplates/foo.j2 dest=/etc/file.conf owner=bin group=wheel mode="u=rw,g=r,o=r"

# Copy a new "sudoers" file into place, after passing validation with visudo
- template: src=/mine/sudoers dest=/etc/sudoers validate='visudo -cf %s'
'''
