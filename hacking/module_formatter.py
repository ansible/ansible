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
from jinja2 import Environment, FileSystemLoader
import re
import optparse
import time
import datetime
import subprocess
import ansible.utils
from ansible.utils import module_docs


# Get parent directory of the directory this script lives in
MODULEDIR=os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), os.pardir, 'library'
    ))
EXAMPLE_YAML=os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), os.pardir, 'examples', 'DOCUMENTATION.yaml'
    ))

# There is a better way of doing this!
# TODO: somebody add U(text, http://foo.bar/) as described by Tim in #991

_ITALIC = re.compile(r"I\(([^)]+)\)")
_BOLD   = re.compile(r"B\(([^)]+)\)")
_MODULE = re.compile(r"M\(([^)]+)\)")
_URL    = re.compile(r"U\(([^)]+)\)")
_CONST  = re.compile(r"C\(([^)]+)\)")

def latex_ify(text):

    t = _ITALIC.sub("\\I{" + r"\1" + "}", text)
    t = _BOLD.sub("\\B{" + r"\1" + "}", t)
    t = _MODULE.sub("\\M{" + r"\1" + "}", t)
    t = _URL.sub("\\url{" + r"\1" + "}", t)
    t = _CONST.sub("\\C{" + r"\1" + "}", t)

    return t

def html_ify(text):

    t = _ITALIC.sub("<em>" + r"\1" + "</em>", text)
    t = _BOLD.sub("<b>" + r"\1" + "</b>", t)
    t = _MODULE.sub("<span class='module'>" + r"\1" + "</span>", t)
    t = _URL.sub("<a href='" + r"\1" + "'>" + r"\1" + "</a>", t)
    t = _CONST.sub("<code>" + r"\1" + "</code>", t)
    return t

def json_ify(text):

    t = _ITALIC.sub("<em>" + r"\1" + "</em>", text)
    t = _BOLD.sub("<b>" + r"\1" + "</b>", t)
    t = _MODULE.sub("<span class='module'>" + r"\1" + "</span>", t)
    t = _URL.sub("<a href='" + r"\1" + "'>" + r"\1" + "</a>", t)
    t = _CONST.sub("<code>" + r"\1" + "</code>", t)

    return t


def js_ify(text):

    return text


def man_ify(text):

    t = _ITALIC.sub(r'\\fI' + r"\1" + r"\\fR", text)
    t = _BOLD.sub(r'\\fB' + r"\1" + r"\\fR", t)
    t = _MODULE.sub(r'\\fI' + r"\1" + r"\\fR", t)
    t = _URL.sub(r'\\fI' + r"\1" + r"\\fR", t)
    t = _CONST.sub(r'\\fC' + r"\1" + r"\\fR", t)

    return t

def rst_ify(text):

    t = _ITALIC.sub(r'*' + r"\1" + r"*", text)
    t = _BOLD.sub(r'**' + r"\1" + r"**", t)
    t = _MODULE.sub(r'``' + r"\1" + r"``", t)
    t = _URL.sub(r"\1", t)
    t = _CONST.sub(r'``' + r"\1" + r"``", t)

    return t

def markdown_ify(text):

    t = _ITALIC.sub("_" + r"\1" + "_", text)
    t = _BOLD.sub("**" + r"\1" + "**", t)
    t = _MODULE.sub("*" + r"\1" + "*", t)
    t = _URL.sub("[" + r"\1" + "](" + r"\1" + ")", t)
    t = _CONST.sub("`" + r"\1" + "`", t)

    return t

# Helper for Jinja2 (format() doesn't work here...)
def rst_fmt(text, fmt):
    return fmt % (text)

def rst_xline(width, char="="):
    return char * width

def load_examples_section(text):
    return text.split('***BREAK***')

def return_data(text, options, outputname, module):
    if options.output_dir is not None:
        f = open(os.path.join(options.output_dir, outputname % module), 'w')
        f.write(text)
        f.close()
    else:
        print text

def boilerplate():
    if not os.path.exists(EXAMPLE_YAML):
        print >>sys.stderr, "Missing example boiler plate: %S" % EXAMPLE_YAML
    print file(EXAMPLE_YAML).read()


def main():

    p = optparse.OptionParser(
        version='%prog 1.0',
        usage='usage: %prog [options] arg1 arg2',
        description='Convert Ansible module DOCUMENTATION strings to other formats',
    )

    p.add_option("-A", "--ansible-version",
            action="store",
            dest="ansible_version",
            default="unknown",
            help="Ansible version number")
    p.add_option("-M", "--module-dir",
            action="store",
            dest="module_dir",
            default=MODULEDIR,
            help="Ansible modules/ directory")
    p.add_option("-T", "--template-dir",
            action="store",
            dest="template_dir",
            default="hacking/templates",
            help="directory containing Jinja2 templates")
    p.add_option("-t", "--type",
            action='store',
            dest='type',
            choices=['html', 'latex', 'man', 'rst', 'json', 'markdown'],
            default='latex',
            help="Output type")
    p.add_option("-m", "--module",
            action='append',
            default=[],
            dest='module_list',
            help="Add modules to process in module_dir")
    p.add_option("-v", "--verbose",
            action='store_true',
            default=False,
            help="Verbose")
    p.add_option("-o", "--output-dir",
            action="store",
            dest="output_dir",
            default=None,
            help="Output directory for module files")
    p.add_option("-I", "--includes-file",
            action="store",
            dest="includes_file",
            default=None,
            help="Create a file containing list of processed modules")
    p.add_option("-G", "--generate",
            action="store_true",
            dest="do_boilerplate",
            default=False,
            help="generate boilerplate DOCUMENTATION to stdout")
    p.add_option('-V', action='version', help='Show version number and exit')

    (options, args) = p.parse_args()

#    print "M: %s" % options.module_dir
#    print "t: %s" % options.type
#    print "m: %s" % options.module_list
#    print "v: %s" % options.verbose

    if options.do_boilerplate:
        boilerplate()
        sys.exit(0)

    if not options.module_dir:
        print "Need module_dir"
        sys.exit(1)
    if not os.path.exists(options.module_dir):
        print >>sys.stderr, "Module directory does not exist: %s" % options.module_dir
        sys.exit(1)


    if not options.template_dir:
        print "Need template_dir"
        sys.exit(1)

    env = Environment(loader=FileSystemLoader(options.template_dir),
        variable_start_string="@{",
        variable_end_string="}@",
        trim_blocks=True,
    )

    env.globals['xline'] = rst_xline

    if options.type == 'latex':
        env.filters['jpfunc'] = latex_ify
        template = env.get_template('latex.j2')
        outputname = "%s.tex"
        includecmt = ""
        includefmt = "%s\n"
    if options.type == 'html':
        env.filters['jpfunc'] = html_ify
        template = env.get_template('html.j2')
        outputname = "%s.html"
        includecmt = ""
        includefmt = ""
    if options.type == 'man':
        env.filters['jpfunc'] = man_ify
        template = env.get_template('man.j2')
        outputname = "ansible.%s.3"
        includecmt = ""
        includefmt = ""
    if options.type == 'rst':
        env.filters['jpfunc'] = rst_ify
        env.filters['html_ify'] = html_ify
        env.filters['fmt'] = rst_fmt
        env.filters['xline'] = rst_xline
        template = env.get_template('rst.j2')
        outputname = "%s.rst"
        includecmt = ".. Generated by module_formatter\n"
        includefmt = ".. include:: modules/%s.rst\n"
    if options.type == 'json':
        env.filters['jpfunc'] = json_ify
        outputname = "%s.json"
        includecmt = ""
        includefmt = ""
    if options.type == 'js':
        env.filters['jpfunc'] = js_ify
        template = env.get_template('js.j2')
        outputname = "%s.js"
    if options.type == 'markdown':
        env.filters['jpfunc'] = markdown_ify
        env.filters['html_ify'] = html_ify
        template = env.get_template('markdown.j2')
        outputname = "%s.md"
        includecmt = ""
        includefmt = ""

    if options.includes_file is not None and includefmt != "":
        incfile = open(options.includes_file, "w")
        incfile.write(includecmt)

    # Temporary variable required to genrate aggregated content in 'js' format.
    js_data = []
    for module in sorted(os.listdir(options.module_dir)):
        if len(options.module_list):
            if not module in options.module_list:
                continue

        fname = os.path.join(options.module_dir, module)
        extra = os.path.join("inc", "%s.tex" % module)

        # probably could just throw out everything with extensions
        if fname.endswith(".swp") or fname.endswith(".orig") or fname.endswith(".rej"):
            continue

        print " processing module source ---> %s" % fname

        if options.type == 'js':
            if fname.endswith(".json"):
                f = open(fname)
                j = json.load(f)
                f.close()
                js_data.append(j)
            continue

        doc = ansible.utils.module_docs.get_docstring(fname, verbose=options.verbose)

        if doc is None and module not in ansible.utils.module_docs.BLACKLIST_MODULES:
            sys.stderr.write("*** ERROR: CORE MODULE MISSING DOCUMENTATION: %s ***\n" % module)
            #sys.exit(1)

        if not doc is None:

            all_keys = []
            for (k,v) in doc['options'].iteritems():
                all_keys.append(k)
            all_keys = sorted(all_keys)
            doc['option_keys'] = all_keys 

            doc['filename']         = fname
            doc['docuri']           = doc['module'].replace('_', '-')
            doc['now_date']         = datetime.date.today().strftime('%Y-%m-%d')
            doc['ansible_version']  = options.ansible_version

            if options.includes_file is not None and includefmt != "":
                incfile.write(includefmt % module)

            if options.verbose:
                print json.dumps(doc, indent=4)


            if options.type == 'latex':
                if os.path.exists(extra):
                    f = open(extra)
                    extradata = f.read()
                    f.close()
                    doc['extradata'] = extradata

            if options.type == 'json':
                text = json.dumps(doc, indent=2)
            else:
                text = template.render(doc)

            return_data(text, options, outputname, module)

    if options.type == 'js':
        docs = {}
        docs['json'] = json.dumps(js_data, indent=2)
        text = template.render(docs)
        return_data(text, options, outputname, 'modules')

if __name__ == '__main__':
    main()
