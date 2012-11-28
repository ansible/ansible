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
import json
import ast
import textwrap
import re
import optparse
import time
import datetime
from ansible import utils
from ansible import errors
from ansible.utils import module_docs
import ansible.constants as C

MODULEDIR = C.DEFAULT_MODULE_PATH

_ITALIC = re.compile(r"I\(([^)]+)\)")
_BOLD   = re.compile(r"B\(([^)]+)\)")
_MODULE = re.compile(r"M\(([^)]+)\)")
_URL    = re.compile(r"U\(([^)]+)\)")
_CONST  = re.compile(r"C\(([^)]+)\)")

def tty_ify(text):

    t = _ITALIC.sub("`" + r"\1" + "'", text)    # I(word) => `word'
    t = _BOLD.sub("*" + r"\1" + "*", t)         # B(word) => *word*
    t = _MODULE.sub("[" + r"\1" + "]", t)       # M(word) => [word]
    t = _URL.sub(r"\1", t)                      # U(word) => word
    t = _CONST.sub("`" + r"\1" + "'", t)        # C(word) => `word'

    return t

def print_man(doc):

    opt_indent="        "
    print "> %s\n" % doc['module'].upper()

    desc = "".join(doc['description'])

    print "%s\n" % textwrap.fill(tty_ify(desc), initial_indent="  ", subsequent_indent="  ")
    
    print "Options (= is mandatory):\n"

    for o in doc['option_keys']:
        opt = doc['options'][o]

        if opt.get('required', False):
            opt_leadin = "="
        else:
            opt_leadin = "-"

        print "%s %s" % (opt_leadin, o)
        desc = "".join(opt['description'])

        if 'choices' in opt:
            choices = ", ".join(opt['choices'])
            desc = desc + " (Choices: " + choices + ")"
        print "%s\n" % textwrap.fill(tty_ify(desc), initial_indent=opt_indent,
                            subsequent_indent=opt_indent)

    if 'notes' in doc:
        notes = "".join(doc['notes'])
        print "Notes:%s\n" % textwrap.fill(tty_ify(notes), initial_indent="  ",
                            subsequent_indent=opt_indent)


    for ex in doc['examples']:
        print "%s%s" % (opt_indent, ex['code'])

def print_snippet(doc):

    desc = tty_ify("".join(doc['short_description']))
    print "- name: %s" % (desc)
    print "  action: %s" % (doc['module'])

    for o in doc['options']:
        opt = doc['options'][o]
        desc = tty_ify("".join(opt['description']))
        s = o + "="
        print "      %-20s   # %s" % (s, desc[0:60])

def main():

    p = optparse.OptionParser(
        version='%prog 1.0',
        usage='usage: %prog [options] [module...]',
        description='Show Ansible module documentation',
    )

    p.add_option("-M", "--module-path",
            action="store",
            dest="module_path",
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
            help='Show playbook snippet for specified module(s)')
    p.add_option('-v', action='version', help='Show version number and exit')

    (options, args) = p.parse_args()

    if options.module_path is not None:
        utils.plugins.vars_loader.add_directory(options.module_path)

    if options.list_dir:
        # list all modules
        paths = utils.plugins.module_finder._get_paths()
        module_list = []
        for path in paths:
            # os.system("ls -C %s" % (path))
            if os.path.isdir(path):
                for module in os.listdir(path):
                    module_list.append(module)

        for module in sorted(module_list):

            if module in module_docs.BLACKLIST_MODULES:
                continue

            filename = utils.plugins.module_finder.find_plugin(module)
            try:
                doc = utils.module_docs.get_docstring(filename)
                desc = tty_ify(doc.get('short_description', '?'))
                if len(desc) > 55:
                    desc = desc + '...'
                print "%-20s %-60.60s" % (module, desc)
            except:
                sys.stderr.write("ERROR: module %s missing documentation\n" % module)
                pass

        sys.exit()

    module_list = []

    if len(args) == 0:
        p.print_help()
    
    for module in args:

        filename = utils.plugins.module_finder.find_plugin(module)
        if filename is None:
            sys.stderr.write("module %s not found in %s\n" % (module,
                    utils.plugins.module_finder.print_paths()))
            continue

        if filename.endswith(".swp"):
            continue

        try:
            doc = utils.module_docs.get_docstring(filename)
        except:
            sys.stderr.write("ERROR: module %s missing documentation\n" % module)
            continue

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
                print_snippet(doc)
            else:
                print_man(doc)
        else:
            sys.stderr.write("ERROR: module %s missing documentation\n" % module)

if __name__ == '__main__':
    main()
