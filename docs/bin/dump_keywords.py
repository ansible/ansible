#!/usr/bin/env python

import optparse
import re
from distutils.version import LooseVersion

import jinja2
import yaml
from jinja2 import Environment, FileSystemLoader

from ansible.module_utils._text import to_bytes
from ansible.playbook import Play
from ansible.playbook.block import Block
from ansible.playbook.role import Role
from ansible.playbook.task import Task
from ansible.utils._build_helpers import update_file_if_different

template_file = 'playbooks_keywords.rst.j2'
oblist = {}
clist = []
class_list = [Play, Role, Block, Task]

p = optparse.OptionParser(
    version='%prog 1.0',
    usage='usage: %prog [options]',
    description='Generate playbook keyword documentation from code and descriptions',
)
p.add_option("-T", "--template-dir", action="store", dest="template_dir", default="../templates", help="directory containing Jinja2 templates")
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
            # check if there is an alias, otherwise undocumented
            alias = getattr(getattr(aobj, '_%s' % a), 'alias', None)
            if alias and alias in docs:
                oblist[name][alias] = docs[alias]
                del oblist[name][a]
            else:
                oblist[name][a] = ' UNDOCUMENTED!! '

    # loop is really with_ for users
    if name == 'Task':
        oblist[name]['with_<lookup_plugin>'] = 'The same as ``loop`` but magically adds the output of any lookup plugin to generate the item list.'

    # local_action is implicit with action
    if 'action' in oblist[name]:
        oblist[name]['local_action'] = 'Same as action but also implies ``delegate_to: localhost``'

    # remove unusable (used to be private?)
    for nouse in ('loop_args', 'loop_with'):
        if nouse in oblist[name]:
            del oblist[name][nouse]

env = Environment(loader=FileSystemLoader(options.template_dir), trim_blocks=True,)
template = env.get_template(template_file)
outputname = options.output_dir + template_file.replace('.j2', '')
tempvars = {'oblist': oblist, 'clist': clist}

keyword_page = template.render(tempvars)
if LooseVersion(jinja2.__version__) < LooseVersion('2.10'):
    # jinja2 < 2.10's indent filter indents blank lines.  Cleanup
    keyword_page = re.sub(' +\n', '\n', keyword_page)

update_file_if_different(outputname, to_bytes(keyword_page))
