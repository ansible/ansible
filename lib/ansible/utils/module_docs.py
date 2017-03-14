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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys
import ast
import traceback

from collections import MutableMapping, MutableSet, MutableSequence

from ansible.compat.six import string_types
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.plugins import fragment_loader

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

# modules that are ok that they do not have documentation strings
BLACKLIST_MODULES = frozenset((
    'async_wrapper',
))

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

    # ensure metadata defaults
    metadata = {'metadata_version': '1.0',
                'status': ['preview'],
                'supported_by': 'community'}

    try:
        # Thank you, Habbie, for this bit of code :-)
        M = ast.parse(''.join(open(filename)))
        for child in M.body:
            if isinstance(child, ast.Assign):
                for t in child.targets:
                    try:
                        theid = t.id
                    except AttributeError as e:
                        # skip errors can happen when trying to use the normal code
                        display.warning("Failed to assign id for %s on %s, skipping" % (t, filename))
                        continue

                    if 'DOCUMENTATION' == theid:
                        doc = AnsibleLoader(child.value.s, file_name=filename).get_single_data()
                        fragments = doc.get('extends_documentation_fragment', [])

                        if isinstance(fragments, string_types):
                            fragments = [ fragments ]

                        # Allow the module to specify a var other than DOCUMENTATION
                        # to pull the fragment from, using dot notation as a separator
                        for fragment_slug in fragments:
                            fragment_slug = fragment_slug.lower()
                            if '.' in fragment_slug:
                                fragment_name, fragment_var = fragment_slug.split('.', 1)
                                fragment_var = fragment_var.upper()
                            else:
                                fragment_name, fragment_var = fragment_slug, 'DOCUMENTATION'

                            fragment_class = fragment_loader.get(fragment_name)
                            assert fragment_class is not None

                            fragment_yaml = getattr(fragment_class, fragment_var, '{}')
                            fragment = AnsibleLoader(fragment_yaml, file_name=filename).get_single_data()

                            if 'notes' in fragment:
                                notes = fragment.pop('notes')
                                if notes:
                                    if 'notes' not in doc:
                                        doc['notes'] = []
                                    doc['notes'].extend(notes)

                            if 'options' not in fragment:
                                raise Exception("missing options in fragment (%s), possibly misformatted?: %s" % (fragment_name, filename))

                            for key, value in fragment.items():
                                if key not in doc:
                                    doc[key] = value
                                else:
                                    if isinstance(doc[key], MutableMapping):
                                        doc[key].update(value)
                                    elif isinstance(doc[key], MutableSet):
                                        doc[key].add(value)
                                    elif isinstance(doc[key], MutableSequence):
                                        doc[key] = sorted(frozenset(doc[key] + value))
                                    else:
                                        raise Exception("Attempt to extend a documentation fragement (%s) of unknown type: %s" % (fragment_name, filename))

                    elif 'EXAMPLES' == theid:
                        plainexamples = child.value.s[1:]  # Skip first empty line

                    elif 'RETURN' == theid:
                        returndocs = child.value.s[1:]

                    elif 'ANSIBLE_METADATA' == theid:
                        metadata = ast.literal_eval(child.value)
                        if not isinstance(metadata, MutableMapping):
                            # try yaml loading
                            metadata = AnsibleLoader(metadata, file_name=filename).get_single_data()

                        if not isinstance(metadata, MutableMapping):
                            display.warning("Invalid metadata detected in %s, using defaults" % filename)
                            metadata = {'status': ['preview'], 'supported_by': 'community', 'metadata_version': '1.0'}

    except:
        display.error("unable to parse %s" % filename)
        if verbose is True:
            display.display("unable to parse %s" % filename)
            raise

    return doc, plainexamples, returndocs, metadata
