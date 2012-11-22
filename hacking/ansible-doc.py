#!/usr/bin/env python
# (c) 2012, Jan-Piet Mens <jpmens () gmail.com>
#
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
#

import os
import sys
import yaml
import codecs
import json
import ast
from jinja2 import Environment, FunctionLoader, Template
import re
import optparse
import time
import datetime
from ansible import utils
from ansible import errors
from ansible.utils import module_docs
import ansible.constants as C


# Get parent directory of the directory this script lives in
MODULEDIR=os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), os.pardir, 'library'
    ))

T_LISTING = '''{{ "%-20s" | format(module) }}  {{ short_description | jpfunc | truncate(70) }}'''

T_SNIPPET = '''
- name: {{ short_description | jpfunc }}
  action: {{ module }}
{% for k in option_keys %}
{% set v = options[k] %}
        {{ "%-20s" | format(k + '=') }}    # {{ v.description[0] | truncate(50) | jpfunc }}
{% endfor -%}
'''

T_MODULEDOC = '''
> {{ module | upper }}  ({{filename}})

{% for desc in description %}
{{ desc | jpfunc | wordwrap(width=70) | indent(indentfirst=True) }}
{% endfor %}

{% if options %}
   Options:
{% for k in option_keys %}
{% set v = options[k] %}
   o {{ k }}
{% for desc in v.description %}{{ desc|jpfunc| wordwrap(width=60)|indent(10,indentfirst=True) }}
{% endfor %}
         {% if v.get('choices') %} Choices : {% for choice in v.get('choices',[]) %}{{ choice }}{% if not loop.last %},{%else%}.{%endif%}{% endfor %}
{% endif %}

{% endfor %}
{% endif %}

{# ." ------ NOTES #}
{% if notes %}
{% for note in notes %}
{{ note | jpfunc }}
{% endfor %}
{% endif %}

{# ------ EXAMPLES #}
{% if examples is defined %}
{% for e in examples %}
    {{ e['code'] }}
{% endfor %}
{% endif %}
'''

# There is a better way of doing this!
# TODO: somebody add U(text, http://foo.bar/) as described by Tim in #991

_ITALIC = re.compile(r"I\(([^)]+)\)")
_BOLD   = re.compile(r"B\(([^)]+)\)")
_MODULE = re.compile(r"M\(([^)]+)\)")
_URL    = re.compile(r"U\(([^)]+)\)")
_CONST  = re.compile(r"C\(([^)]+)\)")

def markdown_ify(text):

    t = _ITALIC.sub("_" + r"\1" + "_", text)
    t = _BOLD.sub("**" + r"\1" + "**", t)
    t = _MODULE.sub("*" + r"\1" + "*", t)
    t = _URL.sub("[" + r"\1" + "](" + r"\1" + ")", t)
    t = _CONST.sub("`" + r"\1" + "`", t)

    return t

def main():

    p = optparse.OptionParser(
        version='%prog 1.0',
        usage='usage: %prog [options] ',
        description='Show Ansible module documentation',
    )

    p.add_option("-M", "--module-dir",
            action="store",
            dest="module_dir",
            default=MODULEDIR,
            help="Ansible modules/ directory")
    p.add_option("-l", "--list",
            action="store_true",
            default=False,
            dest='list_dir',
            help='List available modules')
    p.add_option("-s", "--snippet",
            action="store_true",
            default=False,
            dest='show_snippet',
            help='Show playbook snippet for module')
    p.add_option("-m", "--module",
            action='append',
            default=[],
            dest='module_list',
            help="Add modules to process in module_dir")
    p.add_option('-V', action='version', help='Show version number and exit')

    (options, args) = p.parse_args()

    env = Environment(
        trim_blocks=True,
    )
    env.filters['jpfunc'] = markdown_ify

    if options.module_dir is not None:
        utils.plugins.vars_loader.add_directory(options.module_dir)

    if options.list_dir:
        # list all modules
        ls_templ = env.from_string(T_LISTING)
        paths = utils.plugins.module_finder._get_paths()
        for path in paths:
            # os.system("ls -C %s" % (path))
            for module in os.listdir(path):
                filename = utils.plugins.module_finder.find_plugin(module)

                try:
                    doc = utils.module_docs.get_docstring(filename)
                    text = ls_templ.render(doc)
                    print text.rstrip()
                except:
                    pass
            
        sys.exit()

    tmpl = env.from_string(T_SNIPPET)
    full_tmpl = env.from_string(T_MODULEDOC)

    for module_name in options.module_list:

        filename = utils.plugins.module_finder.find_plugin(module_name)
        if filename is None:
            sys.exit("module %s not found in %s" % (module_name,
                    utils.plugins.module_finder.print_paths()))

        if filename.endswith(".swp"):
            continue

        doc = utils.module_docs.get_docstring(filename)

        if doc is None and module not in ansible.utils.module_docs.BLACKLIST_MODULES:
            sys.stderr.write("*** ERROR: MODULE MISSING DOCUMENTATION: %s ***\n" % module)
            sys.exit(1)

        if not doc is None:

            all_keys = []
            for (k,v) in doc['options'].iteritems():
                all_keys.append(k)
            all_keys = sorted(all_keys)
            doc['option_keys'] = all_keys 

            doc['filename']         = filename
            doc['docuri']           = doc['module'].replace('_', '-')
            doc['now_date']         = datetime.date.today().strftime('%Y-%m-%d')

        if options.show_snippet:
            text = tmpl.render(doc)
            print text.rstrip()
        else:
            text = full_tmpl.render(doc)
            print text.rstrip()

if __name__ == '__main__':
    main()
