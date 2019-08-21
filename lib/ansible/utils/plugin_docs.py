# Copyright: (c) 2012, Jan-Piet Mens <jpmens () gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible import constants as C
from ansible.release import __version__ as ansible_version
from ansible.errors import AnsibleError, AnsibleAssertionError
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_native
from ansible.module_utils.common._collections_compat import MutableMapping, MutableSet, MutableSequence
from ansible.parsing.plugin_docs import read_docstring
from ansible.parsing.yaml.loader import AnsibleLoader
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

    unknown_fragments = []

    # doc_fragments are allowed to specify a fragment var other than DOCUMENTATION
    # with a . separator; this is complicated by collections-hosted doc_fragments that
    # use the same separator. Assume it's collection-hosted normally first, try to load
    # as-specified. If failure, assume the right-most component is a var, split it off,
    # and retry the load.
    for fragment_slug in fragments:
        fragment_name = fragment_slug
        fragment_var = 'DOCUMENTATION'

        fragment_class = fragment_loader.get(fragment_name)
        if fragment_class is None and '.' in fragment_slug:
            splitname = fragment_slug.rsplit('.', 1)
            fragment_name = splitname[0]
            fragment_var = splitname[1].upper()
            fragment_class = fragment_loader.get(fragment_name)

        if fragment_class is None:
            unknown_fragments.append(fragment_slug)
            continue

        fragment_yaml = getattr(fragment_class, fragment_var, None)
        if fragment_yaml is None:
            if fragment_var != 'DOCUMENTATION':
                # if it's asking for something specific that's missing, that's an error
                unknown_fragments.append(fragment_slug)
                continue
            else:
                fragment_yaml = '{}'  # TODO: this is still an error later since we require 'options' below...

        fragment = AnsibleLoader(fragment_yaml, file_name=filename).get_single_data()

        if 'notes' in fragment:
            notes = fragment.pop('notes')
            if notes:
                if 'notes' not in doc:
                    doc['notes'] = []
                doc['notes'].extend(notes)

        if 'seealso' in fragment:
            seealso = fragment.pop('seealso')
            if seealso:
                if 'seealso' not in doc:
                    doc['seealso'] = []
                doc['seealso'].extend(seealso)

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

    if unknown_fragments:
        raise AnsibleError('unknown doc_fragment(s) in file {0}: {1}'.format(filename, to_native(', '.join(unknown_fragments))))


def get_docstring(filename, fragment_loader, verbose=False, ignore_errors=False):
    """
    DOCUMENTATION can be extended using documentation fragments loaded by the PluginLoader from the doc_fragments plugins.
    """

    data = read_docstring(filename, verbose=verbose, ignore_errors=ignore_errors)

    # add fragments to documentation
    if data.get('doc', False):
        add_fragments(data['doc'], filename, fragment_loader=fragment_loader)

    return data['doc'], data['plainexamples'], data['returndocs'], data['metadata']


def get_versioned_doclink(path):
    """
    returns a versioned documentation link for the current Ansible major.minor version; used to generate
    in-product warning/error links to the configured DOCSITE_ROOT_URL
    (eg, https://docs.ansible.com/ansible/2.8/somepath/doc.html)

    :param path: relative path to a document under docs/docsite/rst;
    :return: absolute URL to the specified doc for the current version of Ansible
    """
    path = to_native(path)
    try:
        base_url = C.config.get_config_value('DOCSITE_ROOT_URL')
        if not base_url.endswith('/'):
            base_url += '/'
        if path.startswith('/'):
            path = path[1:]
        split_ver = ansible_version.split('.')
        if len(split_ver) < 3:
            raise RuntimeError('invalid version ({0})'.format(ansible_version))

        doc_version = '{0}.{1}'.format(split_ver[0], split_ver[1])

        # check to see if it's a X.Y.0 non-rc prerelease or dev release, if so, assume devel (since the X.Y doctree
        # isn't published until beta-ish)
        if split_ver[2].startswith('0'):
            # exclude rc; we should have the X.Y doctree live by rc1
            if any((pre in split_ver[2]) for pre in ['a', 'b']) or len(split_ver) > 3 and 'dev' in split_ver[3]:
                doc_version = 'devel'

        return '{0}{1}/{2}'.format(base_url, doc_version, path)
    except Exception as ex:
        return '(unable to create versioned doc link for path {0}: {1})'.format(path, to_native(ex))
