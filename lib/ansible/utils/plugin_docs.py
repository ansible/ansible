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

from ansible.errors import AnsibleError, AnsibleAssertionError
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_native
from ansible.parsing.plugin_docs import read_docstring, read_docstub
from ansible.parsing.yaml.loader import AnsibleLoader

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


def merge_fragment(target, source):

    for key, value in source.items():
        if key in target:
            # assumes both structures have same type
            if isinstance(target[key], MutableMapping):
                value.update(target[key])
            elif isinstance(target[key], MutableSet):
                value.add(target[key])
            elif isinstance(target[key], MutableSequence):
                value = sorted(frozenset(value + target[key]))
            else:
                raise Exception("Attempt to extend a documentation fragement, invalid type for %s" % key)
        target[key] = value


def add_fragments(doc, filename, fragment_loader):

    fragments = doc.pop('extends_documentation_fragment', [])

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

        # ensure options themselves are directly merged
        if 'options' in doc:
            try:
                merge_fragment(doc['options'], fragment.pop('options'))
            except Exception as e:
                raise AnsibleError("%s options (%s) of unknown type: %s" % (to_native(e), fragment_name, filename))
        else:
            doc['options'] = fragment.pop('options')

        # merge rest of the sections
        try:
            merge_fragment(doc, fragment)
        except Exception as e:
            raise AnsibleError("%s (%s) of unknown type: %s" % (to_native(e), fragment_name, filename))


def get_docstring(filename, fragment_loader, verbose=False, ignore_errors=False):
    """
    DOCUMENTATION can be extended using documentation fragments loaded by the PluginLoader from the module_docs_fragments directory.
    """

    data = read_docstring(filename, verbose=verbose, ignore_errors=ignore_errors)

    # add fragments to documentation
    if data.get('doc', False):
        add_fragments(data['doc'], filename, fragment_loader=fragment_loader)

    return data['doc'], data['plainexamples'], data['returndocs'], data['metadata']


def get_docstub(filename, fragment_loader, verbose=False, ignore_errors=False):
    """
    When only short_description is needed, load a stub of the full DOCUMENTATION string to speed up operation.
    """

    data = read_docstub(filename, verbose=verbose, ignore_errors=ignore_errors)

    if data.get('doc', False):
        add_fragments(data['doc'], filename, fragment_loader=fragment_loader)

    return data['doc'], data['plainexamples'], data['returndocs'], data['metadata']
