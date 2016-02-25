#!/usr/bin/env python2

import optparse
from jinja2 import Environment, FileSystemLoader

from ansible.playbook import  Play
from ansible.playbook.block import  Block
from ansible.playbook.role import  Role
from ansible.playbook.task import  Task

template_file = 'playbooks_directives.rst.j2'
oblist = {}
for aclass in Play, Block, Role, Task:
    aobj = aclass()
    oblist[type(aobj).__name__] = aobj

p = optparse.OptionParser(
    version='%prog 1.0',
    usage='usage: %prog [options]',
    description='Generate module documentation from metadata',
)
p.add_option("-T", "--template-dir", action="store", dest="template_dir", default="hacking/templates", help="directory containing Jinja2 templates")
p.add_option("-o", "--output-dir", action="store", dest="output_dir", default='/tmp/', help="Output directory for rst files")

(options, args) = p.parse_args()

env = Environment(loader=FileSystemLoader(options.template_dir), trim_blocks=True,)
template = env.get_template(template_file)
outputname = options.output_dir + template_file.replace('.j2','')
tempvars = { 'oblist': oblist }

with open( outputname, 'w') as f:
    f.write(template.render(tempvars))
