#!/usr/bin/env python

import optparse
import yaml

from jinja2 import Environment, FileSystemLoader

from ansible.playbook import Play
from ansible.playbook.block import Block
from ansible.playbook.role import Role
from ansible.playbook.task import Task

template_file = 'playbooks_directives.rst.j2'
oblist = {}
clist = []
class_list = [ Play, Role, Block, Task ]

p = optparse.OptionParser(
    version='%prog 1.0',
    usage='usage: %prog [options]',
    description='Generate module documentation from metadata',
)
p.add_option("-T", "--template-dir", action="store", dest="template_dir", default="hacking/templates", help="directory containing Jinja2 templates")
p.add_option("-o", "--output-dir", action="store", dest="output_dir", default='/tmp/', help="Output directory for rst files")
p.add_option("-d", "--docs-source", action="store", dest="docs", default=None, help="Source for attribute docs")

(options, args) = p.parse_args()

for aclass in class_list:
    aobj = aclass()
    name = type(aobj).__name__

    if options.docs:
        with open(options.docs) as f:
            docs = yaml.safe_load(f)
    else:
        docs = {}

    # build ordered list to loop over and dict with attributes
    clist.append(name)
    oblist[name] = dict((x, aobj.__dict__['_attributes'][x]) for x in aobj.__dict__['_attributes'] if 'private' not in x or not x.private)

    # pick up docs if they exist
    for a in oblist[name]:
        if a in docs:
            oblist[name][a] = docs[a]
        else:
            oblist[name][a] = ' UNDOCUMENTED!! '

    # loop is really with_ for users
    if name == 'Task':
        oblist[name]['with_<lookup_plugin>'] = 'with_ is how loops are defined, it can use any available lookup plugin to generate the item list'

    # local_action is implicit with action
    if 'action' in oblist[name]:
        oblist[name]['local_action'] = 'Same as action but also implies `delegate_to: localhost`'

env = Environment(loader=FileSystemLoader(options.template_dir), trim_blocks=True,)
template = env.get_template(template_file)
outputname = options.output_dir + template_file.replace('.j2','')
tempvars = { 'oblist': oblist, 'clist': clist }

with open( outputname, 'w') as f:
    f.write(template.render(tempvars))
