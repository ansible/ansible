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

import ast
import yaml

from collections import MutableMapping, MutableSet, MutableSequence

from ansible.module_utils.six import string_types
from ansible.parsing.metadata import extract_metadata
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.plugins import fragment_loader

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


# modules that are ok that they do not have documentation strings
BLACKLIST = {
    'MODULE': frozenset(('async_wrapper',)),
    'CACHE': frozenset(('base',)),
}


def add_fragments(doc, filename):

    fragments = doc.get('extends_documentation_fragment', [])

    if isinstance(fragments, string_types):
        fragments = [fragments]

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
            if key in doc:
                # assumes both structures have same type
                if isinstance(doc[key], MutableMapping):
                    value.update(doc[key])
                elif isinstance(doc[key], MutableSet):
                    value.add(doc[key])
                elif isinstance(doc[key], MutableSequence):
                    value = sorted(frozenset(value + doc[key]))
                else:
                    raise Exception("Attempt to extend a documentation fragement (%s) of unknown type: %s" % (fragment_name, filename))
            doc[key] = value


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

    # FIXME: Should refactor this so that we have a docstring parsing
    # function and a separate variable parsing function
    # Can have a function one higher that invokes whichever is needed
    #
    # Should look roughly like this:
    # get_plugin_doc(filename, verbose=False)
    #   documentation = extract_docstring(plugin_ast, identifier, verbose=False)
    #   if not documentation and not (filter or test):
    #       documentation = extract_variables(plugin_ast)
    #   documentation['metadata'] = extract_metadata(plugin_ast)

    data = {
        'doc': None,
        'plainexamples': None,
        'returndocs': None,
        'metadata': None
    }

    string_to_vars = {
        'DOCUMENTATION': 'doc',
        'EXAMPLES': 'plainexamples',
        'RETURN': 'returndocs',
    }

    try:
        b_module_data = open(filename, 'rb').read()
        M = ast.parse(b_module_data)
        try:
            display.debug('Attempt first docstring is yaml docs')
            docstring = yaml.load(M.body[0].value.s)
            for string in string_to_vars.keys():
                if string in docstring:
                    data[string_to_vars[string]] = docstring[string]
                display.debug('assigned :%s' % string_to_vars[string])
        except Exception as e:
            display.debug('failed docstring parsing: %s' % str(e))

        if 'docs' not in data or not data['docs']:
            display.debug('Fallback to vars parsing')
            for child in M.body:
                if isinstance(child, ast.Assign):
                    for t in child.targets:
                        try:
                            theid = t.id
                        except AttributeError:
                            # skip errors can happen when trying to use the normal code
                            display.warning("Failed to assign id for %s on %s, skipping" % (t, filename))
                            continue

                        if theid in string_to_vars:
                            varkey = string_to_vars[theid]
                            if isinstance(child.value, ast.Dict):
                                data[varkey] = ast.literal_eval(child.value)
                            else:
                                if theid == 'DOCUMENTATION':
                                    # string should be yaml
                                    data[varkey] = AnsibleLoader(child.value.s, file_name=filename).get_single_data()
                                else:
                                    # not yaml, should be a simple string
                                    data[varkey] = child.value.s
                            display.debug('assigned :%s' % varkey)

        # Metadata is per-file rather than per-plugin/function
        data['metadata'] = extract_metadata(module_ast=M)[0]

        # add fragments to documentation
        if data['doc']:
            add_fragments(data['doc'], filename)

        # remove version
        if data['metadata']:
            for x in ('version', 'metadata_version'):
                if x in data['metadata']:
                    del data['metadata'][x]
    except Exception as e:
        display.error("unable to parse %s" % filename)
        if verbose is True:
            display.display("unable to parse %s" % filename)
            raise

    return data['doc'], data['plainexamples'], data['returndocs'], data['metadata']
