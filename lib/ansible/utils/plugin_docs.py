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

from collections import MutableMapping, MutableSet, MutableSequence

from ansible.errors import AnsibleAssertionError
from ansible.module_utils.six import string_types
from ansible.parsing.plugin_docs import read_docstring
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.plugins.loader import fragment_loader

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
        if fragment_class is None:
            raise AnsibleAssertionError('fragment_class is None')

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
    DOCUMENTATION can be extended using documentation fragments loaded by the PluginLoader from the module_docs_fragments directory.
    """

    data = read_docstring(filename, verbose=verbose)

    # add fragments to documentation
    if data.get('doc', False):
        add_fragments(data['doc'], filename)

    return data['doc'], data['plainexamples'], data['returndocs'], data['metadata']
