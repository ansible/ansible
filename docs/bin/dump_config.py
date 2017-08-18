#!/usr/bin/env python

import optparse
import yaml

from jinja2 import Environment, FileSystemLoader

template_file = 'config.rst.j2'
oblist = {}
clist = []

p = optparse.OptionParser(
    version='%prog 1.0',
    usage='usage: %prog [options]',
    description='Generate module documentation from metadata',
)
p.add_option("-T", "--template-dir", action="store", dest="template_dir", default="../templates", help="directory containing Jinja2 templates")
p.add_option("-o", "--output-dir", action="store", dest="output_dir", default='/tmp/', help="Output directory for rst files")
p.add_option("-d", "--docs-source", action="store", dest="docs", default=None, help="Source for attribute docs")

(options, args) = p.parse_args()


if options.docs:
    with open(options.docs) as f:
        docs = yaml.safe_load(f)
else:
    docs = {}

config_options = docs
#print('config_options: %s' % config_options)

#    # build ordered list to loop over and dict with attributes
#    clist.append(name)
#    oblist[name] = dict((x, aobj.__dict__['_attributes'][x]) for x in aobj.__dict__['_attributes'] if 'private' not in x or not x.private)

env = Environment(loader=FileSystemLoader(options.template_dir), trim_blocks=True,)
template = env.get_template(template_file)
outputname = options.output_dir + template_file.replace('.j2', '')
tempvars = {'config_options': config_options}
import pprint
pprint.pprint(config_options)
with open(outputname, 'w') as f:
    f.write(template.render(tempvars).encode('utf-8'))
