#!/usr/bin/env python
# (c) 2012, Jan-Piet Mens <jpmens () gmail.com>
# (c) 2012-2014, Michael DeHaan <michael@ansible.com> and others
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

from __future__ import print_function
import os
import glob
import sys
import yaml
import re
import optparse
import datetime
import cgi
import warnings
from jinja2 import Environment, FileSystemLoader
from six import iteritems

from ansible.utils import module_docs
from ansible.utils.vars import merge_hash
from ansible.utils.unicode import to_bytes
from ansible.errors import AnsibleError

#####################################################################################
# constants and paths

# if a module is added in a version of Ansible older than this, don't print the version added information
# in the module documentation because everyone is assumed to be running something newer than this already.
TO_OLD_TO_BE_NOTABLE = 1.3

# Get parent directory of the directory this script lives in
MODULEDIR=os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), os.pardir, 'lib', 'ansible', 'modules'
))

# The name of the DOCUMENTATION template
EXAMPLE_YAML=os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), os.pardir, 'examples', 'DOCUMENTATION.yml'
))

_ITALIC = re.compile(r"I\(([^)]+)\)")
_BOLD   = re.compile(r"B\(([^)]+)\)")
_MODULE = re.compile(r"M\(([^)]+)\)")
_URL    = re.compile(r"U\(([^)]+)\)")
_CONST  = re.compile(r"C\(([^)]+)\)")

DEPRECATED = " (D)"
NOTCORE    = " (E)"
#####################################################################################

def rst_ify(text):
    ''' convert symbols like I(this is in italics) to valid restructured text '''

    try:
        t = _ITALIC.sub(r'*' + r"\1" + r"*", text)
        t = _BOLD.sub(r'**' + r"\1" + r"**", t)
        t = _MODULE.sub(r':ref:`' + r"\1 <\1>" + r"`", t)
        t = _URL.sub(r"\1", t)
        t = _CONST.sub(r'``' + r"\1" + r"``", t)
    except Exception as e:
        raise AnsibleError("Could not process (%s) : %s" % (str(text), str(e)))

    return t

#####################################################################################

def html_ify(text):
    ''' convert symbols like I(this is in italics) to valid HTML '''

    t = cgi.escape(text)
    t = _ITALIC.sub("<em>" + r"\1" + "</em>", t)
    t = _BOLD.sub("<b>" + r"\1" + "</b>", t)
    t = _MODULE.sub("<span class='module'>" + r"\1" + "</span>", t)
    t = _URL.sub("<a href='" + r"\1" + "'>" + r"\1" + "</a>", t)
    t = _CONST.sub("<code>" + r"\1" + "</code>", t)

    return t


#####################################################################################

def rst_fmt(text, fmt):
    ''' helper for Jinja2 to do format strings '''

    return fmt % (text)

#####################################################################################

def rst_xline(width, char="="):
    ''' return a restructured text line of a given length '''

    return char * width

#####################################################################################

def write_data(text, options, outputname, module):
    ''' dumps module output to a file or the screen, as requested '''

    if options.output_dir is not None:
        fname = os.path.join(options.output_dir, outputname % module)
        fname = fname.replace(".py","")
        f = open(fname, 'w')
        f.write(text.encode('utf-8'))
        f.close()
    else:
        print(text)

#####################################################################################


def list_modules(module_dir, depth=0):
    ''' returns a hash of categories, each category being a hash of module names to file paths '''

    categories = dict(all=dict(),_aliases=dict())
    if depth <= 3: # limit # of subdirs

        files = glob.glob("%s/*" % module_dir)
        for d in files:

            category = os.path.splitext(os.path.basename(d))[0]
            if os.path.isdir(d):

                res = list_modules(d, depth + 1)
                for key in list(res.keys()):
                    if key in categories:
                        categories[key] = merge_hash(categories[key], res[key])
                        res.pop(key, None)

                if depth < 2:
                    categories.update(res)
                else:
                    category = module_dir.split("/")[-1]
                    if not category in categories:
                        categories[category] = res
                    else:
                        categories[category].update(res)
            else:
                module = category
                category = os.path.basename(module_dir)
                if not d.endswith(".py") or d.endswith('__init__.py'):
                    # windows powershell modules have documentation stubs in python docstring
                    # format (they are not executed) so skip the ps1 format files
                    continue
                elif module.startswith("_") and os.path.islink(d):
                    source = os.path.splitext(os.path.basename(os.path.realpath(d)))[0]
                    module = module.replace("_","",1)
                    if not d in categories['_aliases']:
                        categories['_aliases'][source] = [module]
                    else:
                        categories['_aliases'][source].update(module)
                    continue

                if not category in categories:
                    categories[category] = {}
                categories[category][module] = d
                categories['all'][module] = d

    # keep module tests out of becomeing module docs
    if 'test' in categories:
        del categories['test']

    return categories

#####################################################################################

def generate_parser():
    ''' generate an optparse parser '''

    p = optparse.OptionParser(
        version='%prog 1.0',
        usage='usage: %prog [options] arg1 arg2',
        description='Generate module documentation from metadata',
    )

    p.add_option("-A", "--ansible-version", action="store", dest="ansible_version", default="unknown", help="Ansible version number")
    p.add_option("-M", "--module-dir", action="store", dest="module_dir", default=MODULEDIR, help="Ansible library path")
    p.add_option("-T", "--template-dir", action="store", dest="template_dir", default="hacking/templates", help="directory containing Jinja2 templates")
    p.add_option("-t", "--type", action='store', dest='type', choices=['rst'], default='rst', help="Document type")
    p.add_option("-v", "--verbose", action='store_true', default=False, help="Verbose")
    p.add_option("-o", "--output-dir", action="store", dest="output_dir", default=None, help="Output directory for module files")
    p.add_option("-I", "--includes-file", action="store", dest="includes_file", default=None, help="Create a file containing list of processed modules")
    p.add_option('-V', action='version', help='Show version number and exit')
    return p

#####################################################################################

def jinja2_environment(template_dir, typ):

    env = Environment(loader=FileSystemLoader(template_dir),
        variable_start_string="@{",
        variable_end_string="}@",
        trim_blocks=True,
    )
    env.globals['xline'] = rst_xline

    if typ == 'rst':
        env.filters['convert_symbols_to_format'] = rst_ify
        env.filters['html_ify'] = html_ify
        env.filters['fmt'] = rst_fmt
        env.filters['xline'] = rst_xline
        template = env.get_template('rst.j2')
        outputname = "%s_module.rst"
    else:
        raise Exception("unknown module format type: %s" % typ)

    return env, template, outputname

#####################################################################################
def too_old(added):
    if not added:
        return False
    try:
        added_tokens = str(added).split(".")
        readded = added_tokens[0] + "." + added_tokens[1]
        added_float = float(readded)
    except ValueError as e:
        warnings.warn("Could not parse %s: %s" % (added, str(e)))
        return False
    return (added_float < TO_OLD_TO_BE_NOTABLE)

def process_module(module, options, env, template, outputname, module_map, aliases):

    fname = module_map[module]
    if isinstance(fname, dict):
        return "SKIPPED"

    basename = os.path.basename(fname)
    deprecated = False

    # ignore files with extensions
    if not basename.endswith(".py"):
        return
    elif module.startswith("_"):
        if os.path.islink(fname):
            return  # ignore, its an alias
        deprecated = True
        module = module.replace("_","",1)

    print("rendering: %s" % module)

    # use ansible core library to parse out doc metadata YAML and plaintext examples
    doc, examples, returndocs = module_docs.get_docstring(fname, verbose=options.verbose)

    # crash if module is missing documentation and not explicitly hidden from docs index
    if doc is None:
        if module in module_docs.BLACKLIST_MODULES:
            return "SKIPPED"
        else:
            sys.stderr.write("*** ERROR: MODULE MISSING DOCUMENTATION: %s, %s ***\n" % (fname, module))
            sys.exit(1)

    if deprecated and 'deprecated' not in doc:
        sys.stderr.write("*** ERROR: DEPRECATED MODULE MISSING 'deprecated' DOCUMENTATION: %s, %s ***\n" % (fname, module))
        sys.exit(1)

    if "/core/" in fname:
        doc['core'] = True
    else:
        doc['core'] = False

    if module in aliases:
        doc['aliases'] = aliases[module]

    all_keys = []

    if not 'version_added' in doc:
        sys.stderr.write("*** ERROR: missing version_added in: %s ***\n" % module)
        sys.exit(1)

    added = 0
    if doc['version_added'] == 'historical':
        del doc['version_added']
    else:
        added = doc['version_added']

    # don't show version added information if it's too old to be called out
    if too_old(added):
        del doc['version_added']

    if 'options' in doc and doc['options']:
        for (k,v) in iteritems(doc['options']):
            # don't show version added information if it's too old to be called out
            if 'version_added' in doc['options'][k] and too_old(doc['options'][k]['version_added']):
                del doc['options'][k]['version_added']
            if not 'description' in doc['options'][k]:
                raise AnsibleError("Missing required description for option %s in %s " % (k, module))
            if not isinstance(doc['options'][k]['description'],list):
                doc['options'][k]['description'] = [doc['options'][k]['description']]

            all_keys.append(k)

    all_keys = sorted(all_keys)

    doc['option_keys']      = all_keys
    doc['filename']         = fname
    doc['docuri']           = doc['module'].replace('_', '-')
    doc['now_date']         = datetime.date.today().strftime('%Y-%m-%d')
    doc['ansible_version']  = options.ansible_version
    doc['plainexamples']    = examples  #plain text
    if returndocs:
        try:
            doc['returndocs']       = yaml.safe_load(returndocs)
        except:
            print("could not load yaml: %s" % returndocs)
            raise
    else:
        doc['returndocs']       = None

    # here is where we build the table of contents...

    try:
        text = template.render(doc)
    except Exception as e:
        raise AnsibleError("Failed to render doc for %s: %s" % (fname, str(e)))
    write_data(text, options, outputname, module)
    return doc['short_description']

#####################################################################################

def print_modules(module, category_file, deprecated, core, options, env, template, outputname, module_map, aliases):
    modstring = module
    modname = module
    if module in deprecated:
        modstring = modstring + DEPRECATED
        modname = "_" + module
    elif module not in core:
        modstring = modstring + NOTCORE

    result = process_module(modname, options, env, template, outputname, module_map, aliases)

    if result != "SKIPPED":
        category_file.write("  %s - %s <%s_module>\n" % (to_bytes(modstring), to_bytes(rst_ify(result)), to_bytes(module)))

def process_category(category, categories, options, env, template, outputname):

    module_map = categories[category]

    aliases = {}
    if '_aliases' in categories:
        aliases = categories['_aliases']

    category_file_path = os.path.join(options.output_dir, "list_of_%s_modules.rst" % category)
    category_file = open(category_file_path, "w")
    print("*** recording category %s in %s ***" % (category, category_file_path))

    # start a new category file

    category = category.replace("_"," ")
    category = category.title()

    modules = []
    deprecated = []
    core = []
    for module in module_map.keys():

        if isinstance(module_map[module], dict):
            for mod in module_map[module].keys():
                if mod.startswith("_"):
                    mod = mod.replace("_","",1)
                    deprecated.append(mod)
                elif '/core/' in module_map[module][mod]:
                    core.append(mod)
        else:
            if module.startswith("_"):
                module = module.replace("_","",1)
                deprecated.append(module)
            elif '/core/' in module_map[module]:
                core.append(module)
        modules.append(module)

    modules.sort()

    category_header = "%s Modules" % (category.title())
    underscores = "`" * len(category_header)

    category_file.write("""\
%s
%s

.. toctree:: :maxdepth: 1

""" % (category_header, underscores))
    sections = []
    for module in modules:
        if module in module_map and isinstance(module_map[module], dict):
            sections.append(module)
            continue
        else:
            print_modules(module, category_file, deprecated, core, options, env, template, outputname, module_map, aliases)

    sections.sort()
    for section in sections:
        category_file.write("\n%s\n%s\n\n" % (section.replace("_"," ").title(),'-' * len(section)))
        category_file.write(".. toctree:: :maxdepth: 1\n\n")

        section_modules = module_map[section].keys()
        section_modules.sort()
        #for module in module_map[section]:
        for module in section_modules:
            print_modules(module, category_file, deprecated, core, options, env, template, outputname, module_map[section], aliases)

    category_file.write("""\n\n
.. note::
    - %s: This marks a module as deprecated, which means a module is kept for backwards compatibility but usage is discouraged.  The module documentation details page may explain more about this rationale.
    - %s: This marks a module as 'extras', which means it ships with ansible but may be a newer module and possibly (but not necessarily) less actively maintained than 'core' modules.
    - Tickets filed on modules are filed to different repos than those on the main open source project. Core module tickets should be filed at `ansible/ansible-modules-core on GitHub <http://github.com/ansible/ansible-modules-core>`_, extras tickets to `ansible/ansible-modules-extras on GitHub <http://github.com/ansible/ansible-modules-extras>`_
""" % (DEPRECATED, NOTCORE))
    category_file.close()

    # TODO: end a new category file

#####################################################################################

def validate_options(options):
    ''' validate option parser options '''

    if not options.module_dir:
        print("--module-dir is required", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(options.module_dir):
        print("--module-dir does not exist: %s" % options.module_dir, file=sys.stderr)
        sys.exit(1)
    if not options.template_dir:
        print("--template-dir must be specified")
        sys.exit(1)

#####################################################################################

def main():

    p = generate_parser()

    (options, args) = p.parse_args()
    validate_options(options)

    env, template, outputname = jinja2_environment(options.template_dir, options.type)

    categories = list_modules(options.module_dir)
    category_names = list(categories.keys())
    category_names.sort()

    category_list_path = os.path.join(options.output_dir, "modules_by_category.rst")
    category_list_file = open(category_list_path, "w")
    category_list_file.write("Module Index\n")
    category_list_file.write("============\n")
    category_list_file.write("\n\n")
    category_list_file.write(".. toctree::\n")
    category_list_file.write("   :maxdepth: 1\n\n")

    for category in category_names:
        if category.startswith("_"):
            continue
        category_list_file.write("   list_of_%s_modules\n" % category)
        process_category(category, categories, options, env, template, outputname)

    category_list_file.close()

if __name__ == '__main__':
    main()
