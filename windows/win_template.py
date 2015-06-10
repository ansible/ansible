# this is a virtual module that is entirely implemented server side

DOCUMENTATION = '''
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
    default: null
    aliases: []
  dest:
    description:
      - Location to render the template to on the remote machine.
    required: true
    default: null
notes:
  - "templates are loaded with C(trim_blocks=True)."
  - By default, windows line endings are not created in the generated file.
  - In order to ensure windows line endings are in the generated file,
    add the following header as the first line of your template:
    "#jinja2: newline_sequence:'\r\n'"
    and ensure each line of the template ends with \r\n
  - Beware fetching files from windows machines when creating templates
    because certain tools, such as Powershell ISE,  and regedit's export facility
    add a Byte Order Mark as the first character of the file, which can cause tracebacks.  
  - Use "od -cx" to examine your templates for Byte Order Marks.
requirements: []
author: "Jon Hawkesworth (@jhawkesworth)"
'''

EXAMPLES = '''
# Playbook Example  (win_template can only be run inside a playbook)
- win_template: src=/mytemplates/file.conf.j2 dest=C:\\temp\\file.conf 


'''
