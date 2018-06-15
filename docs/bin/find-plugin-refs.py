#!/usr/bin/env python

# To run this script, first make webdocs in the toplevel of the checkout.  This will generate all
# rst files from their sources.  Then run this script ./docs/bin/find-plugin-refs.py
#
# No output means that there are no longer any bare module and plugin names referenced via :ref:
#
# For my listing of what needs to be changed after running this script, see the comment at the end
# of the file


import glob
import os
import re

from ansible.module_utils._text import to_text


TOPDIR = os.path.join(os.path.dirname(__file__), '..', 'docsite', 'rst')


def plugin_names(topdir):
    plugins = set()

    # Modules are in a separate directory
    for module_filename in glob.glob(os.path.join(topdir, 'modules', '*_module.rst')):
        module_filename = os.path.basename(module_filename)
        module_name = module_filename[:module_filename.index('_module.rst')]
        plugins.add(module_name)

    for plugin_filename in glob.glob(os.path.join(topdir, 'plugins', '*', '*.rst')):
        plugin_filename = os.path.basename(plugin_filename)
        plugin_name = plugin_filename[:plugin_filename.index('.rst')]
        plugins.add(plugin_name)

    return plugins


def process_refs(topdir, plugin_names):
    REF_RE = re.compile(':ref:`([^`]*)`')
    LABEL_RE = re.compile('<([^>]*)>$')

    # Walk the whole docs tree looking for :ref:.  Anywhere those are found, search for `([^`]*)`
    for dirpath, dirnames, filenames in os.walk(topdir):
        for filename in filenames:
            with open(os.path.join(dirpath, filename), 'rb') as f:
                data = f.read()
                data = to_text(data)
                for ref_match in re.finditer(REF_RE, data):
                    label = ref_match.group(1)

                    # If the ref label includes "<", then search for the label inside of the "<>"
                    label_match = re.search(LABEL_RE, label)
                    if label_match:
                        label = label_match.group(1)

                    # If the ref label is listed in plugins, then print that the file contains an unported ref
                    if label in plugin_names:
                        print(':ref:`{0}` matching plugin {1} was found in {2}'.format(ref_match.group(1), label, os.path.join(dirpath, filename)))


if __name__ == '__main__':

    plugins = plugin_names(TOPDIR)

    process_refs(TOPDIR, plugins)

    # Fixes needed: docs/bin/plugin_formatter.py
    # - t = _MODULE.sub(r":ref:`\1 <\1>`", t)
    # + t = _MODULE.sub(r":ref:`\1 <module_\1>`", t)
    #
    # These have @{module}@ in the template and need to have something like module_@{module}@
    # If any of these list plugins as well as modules, they will need to have a conditional or extra
    # data passed in to handle that in a generic fashion:
    #
    # docs/templates/list_of_CATEGORY_modules.rst.j2
    # docs/templates/list_of_CATEGORY_plugins.rst.j2
    # docs/templates/modules_by_support.rst.j2
    #
    # These are just a simple manual fix:
    # :ref:`command` matching plugin command was found in ./../docsite/rst/user_guide/intro_adhoc.rst
    # :ref:`shell` matching plugin shell was found in ./../docsite/rst/user_guide/intro_adhoc.rst
    # :ref:`config` matching plugin config was found in ./../docsite/rst/installation_guide/intro_configuration.rst
