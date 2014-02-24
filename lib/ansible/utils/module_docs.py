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

from ansible.utils import module_docs_fragments as fragments


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
    """

    doc = None
    plainexamples = None

    try:
        # Thank you, Habbie, for this bit of code :-)
        M = ast.parse(''.join(open(filename)))
        for child in M.body:
            if isinstance(child, ast.Assign):
                if 'DOCUMENTATION' in (t.id for t in child.targets):
                    doc = yaml.safe_load(child.value.s)
                    fragment_name = doc.get('extends_documentation_fragment',
                                            'DOESNOTEXIST').upper()
                    fragment_yaml = getattr(fragments, fragment_name, None)
                    if fragment_yaml:
                        fragment = yaml.safe_load(fragment_yaml)
                        if fragment.has_key('notes'):
                            notes = fragment.pop('notes')
                            if notes:
                                if not doc.has_key('notes'):
                                    doc['notes'] = []
                                doc['notes'].extend(notes)
                        for key, value in fragment.items():
                            if not doc.has_key(key):
                                doc[key] = value
                            else:
                                doc[key].update(value)

                if 'EXAMPLES' in (t.id for t in child.targets):
                    plainexamples = child.value.s[1:]  # Skip first empty line
    except:
        traceback.print_exc() # temp
        if verbose == True:
            traceback.print_exc()
            print "unable to parse %s" % filename
    return doc, plainexamples

