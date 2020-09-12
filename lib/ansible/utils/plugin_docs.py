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


def _process_versions_and_dates(fragment, is_module, return_docs, callback):
    def process_deprecation(deprecation, top_level=False):
        collection_name = 'removed_from_collection' if top_level else 'collection_name'
        if not isinstance(deprecation, MutableMapping):
            return
        if (is_module or top_level) and 'removed_in' in deprecation:  # used in module deprecations
            callback(deprecation, 'removed_in', collection_name)
        if 'removed_at_date' in deprecation:
            callback(deprecation, 'removed_at_date', collection_name)
        if not (is_module or top_level) and 'version' in deprecation:  # used in plugin option deprecations
            callback(deprecation, 'version', collection_name)

    def process_option_specifiers(specifiers):
        for specifier in specifiers:
            if not isinstance(specifier, MutableMapping):
                continue
            if 'version_added' in specifier:
                callback(specifier, 'version_added', 'version_added_collection')
            if isinstance(specifier.get('deprecated'), MutableMapping):
                process_deprecation(specifier['deprecated'])

    def process_options(options):
        for option in options.values():
            if not isinstance(option, MutableMapping):
                continue
            if 'version_added' in option:
                callback(option, 'version_added', 'version_added_collection')
            if not is_module:
                if isinstance(option.get('env'), list):
                    process_option_specifiers(option['env'])
                if isinstance(option.get('ini'), list):
                    process_option_specifiers(option['ini'])
                if isinstance(option.get('vars'), list):
                    process_option_specifiers(option['vars'])
                if isinstance(option.get('deprecated'), MutableMapping):
                    process_deprecation(option['deprecated'])
            if isinstance(option.get('suboptions'), MutableMapping):
                process_options(option['suboptions'])

    def process_return_values(return_values):
        for return_value in return_values.values():
            if not isinstance(return_value, MutableMapping):
                continue
            if 'version_added' in return_value:
                callback(return_value, 'version_added', 'version_added_collection')
            if isinstance(return_value.get('contains'), MutableMapping):
                process_return_values(return_value['contains'])

    if not fragment:
        return

    if return_docs:
        process_return_values(fragment)
        return

    if 'version_added' in fragment:
        callback(fragment, 'version_added', 'version_added_collection')
    if isinstance(fragment.get('deprecated'), MutableMapping):
        process_deprecation(fragment['deprecated'], top_level=True)
    if isinstance(fragment.get('options'), MutableMapping):
        process_options(fragment['options'])


def add_collection_to_versions_and_dates(fragment, collection_name, is_module, return_docs=False):
    def add(options, option, collection_name_field):
        if collection_name_field not in options:
            options[collection_name_field] = collection_name

    _process_versions_and_dates(fragment, is_module, return_docs, add)


def remove_current_collection_from_versions_and_dates(fragment, collection_name, is_module, return_docs=False):
    def remove(options, option, collection_name_field):
        if options.get(collection_name_field) == collection_name:
            del options[collection_name_field]

    _process_versions_and_dates(fragment, is_module, return_docs, remove)


def add_fragments(doc, filename, fragment_loader, is_module=False):

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

        real_collection_name = 'ansible.builtin'
        real_fragment_name = getattr(fragment_class, '_load_name')
        if real_fragment_name.startswith('ansible_collections.'):
            real_collection_name = '.'.join(real_fragment_name.split('.')[1:3])
        add_collection_to_versions_and_dates(fragment, real_collection_name, is_module=is_module)

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


def get_docstring(filename, fragment_loader, verbose=False, ignore_errors=False, collection_name=None, is_module=False):
    """
    DOCUMENTATION can be extended using documentation fragments loaded by the PluginLoader from the doc_fragments plugins.
    """

    data = read_docstring(filename, verbose=verbose, ignore_errors=ignore_errors)

    if data.get('doc', False):
        # add collection name to versions and dates
        if collection_name is not None:
            add_collection_to_versions_and_dates(data['doc'], collection_name, is_module=is_module)

        # add fragments to documentation
        add_fragments(data['doc'], filename, fragment_loader=fragment_loader, is_module=is_module)

    if data.get('returndocs', False):
        # add collection name to versions and dates
        if collection_name is not None:
            add_collection_to_versions_and_dates(data['returndocs'], collection_name, is_module=is_module, return_docs=True)

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
