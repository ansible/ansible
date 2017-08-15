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

from __future__ import print_function
__metaclass__ = type

import cgi
import datetime
import glob
import optparse
import os
import re
import sys
import warnings
import yaml

from collections import defaultdict
from jinja2 import Environment, FileSystemLoader
from six import iteritems

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes
from ansible.utils import plugin_docs

#####################################################################################
# constants and paths

# if a module is added in a version of Ansible older than this, don't print the version added information
# in the module documentation because everyone is assumed to be running something newer than this already.
TO_OLD_TO_BE_NOTABLE = 1.3

# Get parent directory of the directory this script lives in
MODULEDIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), os.pardir, 'lib', 'ansible', 'modules'
))

# The name of the DOCUMENTATION template
EXAMPLE_YAML = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), os.pardir, 'examples', 'DOCUMENTATION.yml'
))

_ITALIC = re.compile(r"I\(([^)]+)\)")
_BOLD = re.compile(r"B\(([^)]+)\)")
_MODULE = re.compile(r"M\(([^)]+)\)")
_URL = re.compile(r"U\(([^)]+)\)")
_CONST = re.compile(r"C\(([^)]+)\)")

DEPRECATED = b" (D)"


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


def html_ify(text):
    ''' convert symbols like I(this is in italics) to valid HTML '''

    t = cgi.escape(text)
    t = _ITALIC.sub("<em>" + r"\1" + "</em>", t)
    t = _BOLD.sub("<b>" + r"\1" + "</b>", t)
    t = _MODULE.sub("<span class='module'>" + r"\1" + "</span>", t)
    t = _URL.sub("<a href='" + r"\1" + "'>" + r"\1" + "</a>", t)
    t = _CONST.sub("<code>" + r"\1" + "</code>", t)

    return t


def rst_fmt(text, fmt):
    ''' helper for Jinja2 to do format strings '''

    return fmt % (text)


def rst_xline(width, char="="):
    ''' return a restructured text line of a given length '''

    return char * width


def write_data(text, options, outputname, module):
    ''' dumps module output to a file or the screen, as requested '''

    if options.output_dir is not None:
        fname = os.path.join(options.output_dir, outputname % module)
        fname = fname.replace(".py", "")
        f = open(fname, 'wb')
        f.write(to_bytes(text))
        f.close()
    else:
        print(text)


def list_modules(module_dir, depth=0, limit_to_modules=None):
    ''' returns a hash of categories, each category being a hash of module names to file paths '''

    categories = dict()
    module_info = dict()
    aliases = defaultdict(set)

    # * windows powershell modules have documentation stubs in python docstring
    #   format (they are not executed) so skip the ps1 format files
    # * One glob level for every module level that we're going to traverse
    files = (
        glob.glob("%s/*.py" % module_dir) +
        glob.glob("%s/*/*.py" % module_dir) +
        glob.glob("%s/*/*/*.py" % module_dir) +
        glob.glob("%s/*/*/*/*.py" % module_dir)
    )

    for module_path in files:
        if module_path.endswith('__init__.py'):
            continue
        category = categories
        mod_path_only = module_path
        # Start at the second directory because we don't want the "vendor"

        mod_path_only = os.path.dirname(module_path[len(module_dir):])

        # directories (core, extras)
        for new_cat in mod_path_only.split('/')[1:]:
            if new_cat not in category:
                category[new_cat] = dict()
            category = category[new_cat]

        module = os.path.splitext(os.path.basename(module_path))[0]
        if module in plugin_docs.BLACKLIST['MODULE']:
            # Do not list blacklisted modules
            continue
        if module.startswith("_") and os.path.islink(module_path):
            source = os.path.splitext(os.path.basename(os.path.realpath(module_path)))[0]
            module = module.replace("_", "", 1)
            aliases[source].add(module)
            continue

        # If requested, limit module documentation building only to passed-in
        # modules.
        if limit_to_modules is None or module.lower() in limit_to_modules:
            category[module] = module_path
            module_info[module] = module_path

    # keep module tests out of becoming module docs
    if 'test' in categories:
        del categories['test']

    return module_info, categories, aliases


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
    p.add_option("-l", "--limit-to-modules", action="store", dest="limit_to_modules", default=None,
                 help="Limit building module documentation to comma-separated list of modules. Specify non-existing module name for no modules.")
    p.add_option('-V', action='version', help='Show version number and exit')
    return p


def jinja2_environment(template_dir, typ):

    env = Environment(loader=FileSystemLoader(template_dir),
                      variable_start_string="@{",
                      variable_end_string="}@",
                      trim_blocks=True)
    env.globals['xline'] = rst_xline

    if typ == 'rst':
        env.filters['convert_symbols_to_format'] = rst_ify
        env.filters['html_ify'] = html_ify
        env.filters['fmt'] = rst_fmt
        env.filters['xline'] = rst_xline
        template = env.get_template('plugin.rst.j2')
        outputname = "%s_module.rst"
    else:
        raise Exception("unknown module format type: %s" % typ)

    return env, template, outputname


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
        module = module.replace("_", "", 1)

    print("rendering: %s" % module)

    # use ansible core library to parse out doc metadata YAML and plaintext examples
    doc, examples, returndocs, metadata = plugin_docs.get_docstring(fname, verbose=options.verbose)

    # crash if module is missing documentation and not explicitly hidden from docs index
    if doc is None:
        sys.exit("*** ERROR: MODULE MISSING DOCUMENTATION: %s, %s ***\n" % (fname, module))

    if metadata is None:
        sys.exit("*** ERROR: MODULE MISSING METADATA: %s, %s ***\n" % (fname, module))

    if deprecated and 'deprecated' not in doc:
        sys.exit("*** ERROR: DEPRECATED MODULE MISSING 'deprecated' DOCUMENTATION: %s, %s ***\n" % (fname, module))

    if module in aliases:
        doc['aliases'] = aliases[module]

    all_keys = []

    if 'version_added' not in doc:
        sys.exit("*** ERROR: missing version_added in: %s ***\n" % module)

    added = 0
    if doc['version_added'] == 'historical':
        del doc['version_added']
    else:
        added = doc['version_added']

    # don't show version added information if it's too old to be called out
    if too_old(added):
        del doc['version_added']

    if 'options' in doc and doc['options']:
        for (k, v) in iteritems(doc['options']):
            # don't show version added information if it's too old to be called out
            if 'version_added' in doc['options'][k] and too_old(doc['options'][k]['version_added']):
                del doc['options'][k]['version_added']
            if 'description' not in doc['options'][k]:
                raise AnsibleError("Missing required description for option %s in %s " % (k, module))

            required_value = doc['options'][k].get('required', False)
            if not isinstance(required_value, bool):
                raise AnsibleError("Invalid required value '%s' for option '%s' in '%s' (must be truthy)" % (required_value, k, module))
            if not isinstance(doc['options'][k]['description'], list):
                doc['options'][k]['description'] = [doc['options'][k]['description']]

            all_keys.append(k)

    all_keys = sorted(all_keys)

    doc['option_keys'] = all_keys
    doc['filename'] = fname
    doc['docuri'] = doc['module'].replace('_', '-')
    doc['now_date'] = datetime.date.today().strftime('%Y-%m-%d')
    doc['ansible_version'] = options.ansible_version
    doc['plainexamples'] = examples  # plain text
    doc['metadata'] = metadata

    if returndocs:
        try:
            doc['returndocs'] = yaml.safe_load(returndocs)
        except:
            print("could not load yaml: %s" % returndocs)
            raise
    else:
        doc['returndocs'] = None

    # here is where we build the table of contents...

    try:
        text = template.render(doc)
    except Exception as e:
        raise AnsibleError("Failed to render doc for %s: %s" % (fname, str(e)))
    write_data(text, options, outputname, module)
    return doc['short_description']


def print_modules(module, category_file, deprecated, options, env, template, outputname, module_map, aliases):
    modstring = module
    if modstring.startswith('_'):
        modstring = module[1:]
    modname = modstring
    if module in deprecated:
        modstring = to_bytes(modstring) + DEPRECATED

    category_file.write(b"  %s - %s <%s_module>\n" % (to_bytes(modstring), to_bytes(rst_ify(module_map[module][1])), to_bytes(modname)))


def process_category(category, categories, options, env, template, outputname):

    # FIXME:
    # We no longer conceptually deal with a mapping of category names to
    # modules to file paths.  Instead we want several different records:
    # (1) Mapping of module names to file paths (what's presently used
    #     as categories['all']
    # (2) Mapping of category names to lists of module names (what you'd
    #     presently get from categories[category_name][subcategory_name].keys()
    # (3) aliases (what's presently in categories['_aliases']
    #
    # list_modules() now returns those.  Need to refactor this function and
    # main to work with them.

    module_map = categories[category]
    module_info = categories['all']

    aliases = {}
    if '_aliases' in categories:
        aliases = categories['_aliases']

    category_file_path = os.path.join(options.output_dir, "list_of_%s_modules.rst" % category)
    category_file = open(category_file_path, "wb")
    print("*** recording category %s in %s ***" % (category, category_file_path))

    # start a new category file

    category = category.replace("_", " ")
    category = category.title()

    modules = []
    deprecated = []
    for module in module_map.keys():
        if isinstance(module_map[module], dict):
            for mod in (m for m in module_map[module].keys() if m in module_info):
                if mod.startswith("_"):
                    deprecated.append(mod)
        else:
            if module not in module_info:
                continue
            if module.startswith("_"):
                deprecated.append(module)
        modules.append(module)

    modules.sort(key=lambda k: k[1:] if k.startswith('_') else k)

    category_header = b"%s Modules" % (to_bytes(category.title()))
    underscores = b"`" * len(category_header)

    category_file.write(b"""\
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
            print_modules(module, category_file, deprecated, options, env, template, outputname, module_info, aliases)

    sections.sort()
    for section in sections:
        category_file.write(b"\n%s\n%s\n\n" % (to_bytes(section.replace("_", " ").title()), b'-' * len(section)))
        category_file.write(b".. toctree:: :maxdepth: 1\n\n")

        section_modules = list(module_map[section].keys())
        section_modules.sort(key=lambda k: k[1:] if k.startswith('_') else k)
        # for module in module_map[section]:
        for module in (m for m in section_modules if m in module_info):
            print_modules(module, category_file, deprecated, options, env, template, outputname, module_info, aliases)

    category_file.write(b"""\n\n
.. note::
    - %s: This marks a module as deprecated, which means a module is kept for backwards compatibility but usage is discouraged.
       The module documentation details page may explain more about this rationale.
""" % DEPRECATED)
    category_file.close()

    # TODO: end a new category file


def validate_options(options):
    ''' validate option parser options '''

    if not options.module_dir:
        sys.exit("--module-dir is required", file=sys.stderr)
    if not os.path.exists(options.module_dir):
        sys.exit("--module-dir does not exist: %s" % options.module_dir, file=sys.stderr)
    if not options.template_dir:
        sys.exit("--template-dir must be specified")


def main():

    p = generate_parser()

    (options, args) = p.parse_args()
    validate_options(options)

    env, template, outputname = jinja2_environment(options.template_dir, options.type)

    # Convert passed-in limit_to_modules to None or list of modules.
    if options.limit_to_modules is not None:
        options.limit_to_modules = [s.lower() for s in options.limit_to_modules.split(",")]

    mod_info, categories, aliases = list_modules(options.module_dir, limit_to_modules=options.limit_to_modules)
    categories['all'] = mod_info
    categories['_aliases'] = aliases
    category_names = [c for c in categories.keys() if not c.startswith('_')]
    category_names.sort()

    # Write master category list
    category_list_path = os.path.join(options.output_dir, "modules_by_category.rst")
    with open(category_list_path, "wb") as category_list_file:
        category_list_file.write(b"Module Index\n")
        category_list_file.write(b"============\n")
        category_list_file.write(b"\n\n")
        category_list_file.write(b".. toctree::\n")
        category_list_file.write(b"   :maxdepth: 1\n\n")

        for category in category_names:
            category_list_file.write(b"   list_of_%s_modules\n" % to_bytes(category))

    # Import all the docs into memory
    module_map = mod_info.copy()

    for modname in module_map:
        result = process_module(modname, options, env, template, outputname, module_map, aliases)
        if result == 'SKIPPED':
            del categories['all'][modname]
        else:
            categories['all'][modname] = (categories['all'][modname], result)

    # Render all the docs to rst via category pages
    for category in category_names:
        process_category(category, categories, options, env, template, outputname)


if __name__ == '__main__':
    main()
