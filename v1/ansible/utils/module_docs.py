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
import ast
import yaml
import traceback

from ansible import utils

# modules that are ok that they do not have documentation strings
BLACKLIST_MODULES = [
   'async_wrapper', 'accelerate', 'async_status'
]

def get_docstring(filename, verbose=False):
    """
    Search for assignment of the DOCUMENTATION and EXAMPLES variables
    in the given file.
    Parse DOCUMENTATION from YAML and return the YAML doc or None
    together with EXAMPLES, as plain text.

    DOCUMENTATION can be extended using documentation fragments
    loaded by the PluginLoader from the module_docs_fragments
    directory.
    """

    doc = None
    plainexamples = None
    returndocs = None

    try:
        # Thank you, Habbie, for this bit of code :-)
        M = ast.parse(''.join(open(filename)))
        for child in M.body:
            if isinstance(child, ast.Assign):
                if 'DOCUMENTATION' in (t.id for t in child.targets):
                    doc = yaml.safe_load(child.value.s)
                    fragment_slug = doc.get('extends_documentation_fragment',
                                            'doesnotexist').lower()

                    # Allow the module to specify a var other than DOCUMENTATION
                    # to pull the fragment from, using dot notation as a separator
                    if '.' in fragment_slug:
                        fragment_name, fragment_var = fragment_slug.split('.', 1)
                        fragment_var = fragment_var.upper()
                    else:
                        fragment_name, fragment_var = fragment_slug, 'DOCUMENTATION'


                    if fragment_slug != 'doesnotexist':
                        fragment_class = utils.plugins.fragment_loader.get(fragment_name)
                        assert fragment_class is not None

                        fragment_yaml = getattr(fragment_class, fragment_var, '{}')
                        fragment = yaml.safe_load(fragment_yaml)

                        if fragment.has_key('notes'):
                            notes = fragment.pop('notes')
                            if notes:
                                if not doc.has_key('notes'):
                                    doc['notes'] = []
                                doc['notes'].extend(notes)

                        if 'options' not in fragment.keys():
                            raise Exception("missing options in fragment, possibly misformatted?")

                        for key, value in fragment.items():
                            if not doc.has_key(key):
                                doc[key] = value
                            else:
                                doc[key].update(value)

                if 'EXAMPLES' in (t.id for t in child.targets):
                    plainexamples = child.value.s[1:]  # Skip first empty line

                if 'RETURN' in (t.id for t in child.targets):
                    returndocs = child.value.s[1:]
    except:
        traceback.print_exc() # temp
        if verbose == True:
            traceback.print_exc()
            print "unable to parse %s" % filename
    return doc, plainexamples, returndocs

