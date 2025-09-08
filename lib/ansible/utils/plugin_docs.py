# Copyright: (c) 2012, Jan-Piet Mens <jpmens () gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from collections.abc import MutableMapping, MutableSet, MutableSequence
from pathlib import Path

import yaml

from ansible import constants as C
from ansible.release import __version__ as ansible_version
from ansible.errors import AnsibleError, AnsibleParserError, AnsiblePluginNotFound
from ansible.module_utils._internal import _no_six
from ansible.module_utils.common.text.converters import to_native
from ansible.parsing.plugin_docs import read_docstring
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.utils.display import Display
from ansible._internal._datatag import _tags

_FRAGMENTABLE = ('DOCUMENTATION', 'RETURN')
display = Display()


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
                raise Exception("Attempt to extend a documentation fragment, invalid type for %s" % key)
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

    def process_attributes(attributes):
        for attribute in attributes.values():
            if not isinstance(attribute, MutableMapping):
                continue
            if 'version_added' in attribute:
                callback(attribute, 'version_added', 'version_added_collection')

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
    if isinstance(fragment.get('attributes'), MutableMapping):
        process_attributes(fragment['attributes'])


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


class AnsibleFragmentError(AnsibleError):
    pass


def add_fragments(doc, filename, fragment_loader, is_module=False, section='DOCUMENTATION'):

    if section not in _FRAGMENTABLE:
        raise AnsibleError(f"Invalid fragment section ({section}) passed to render {filename}, it can only be one of {_FRAGMENTABLE!r}")

    fragments = doc.pop('extends_documentation_fragment', [])

    if isinstance(fragments, str):
        fragments = fragments.split(',')

    unknown_fragments = []

    # doc_fragments are allowed to specify a fragment var other than DOCUMENTATION or RETURN
    # with a . separator; this is complicated by collections-hosted doc_fragments that
    # use the same separator. Assume it's collection-hosted normally first, try to load
    # as-specified. If failure, assume the right-most component is a var, split it off,
    # and retry the load.
    for fragment_slug in fragments:
        fragment_name = fragment_slug.strip()
        fragment_var = section

        fragment_class = fragment_loader.get(fragment_name)
        if fragment_class is None and '.' in fragment_slug:
            splitname = fragment_slug.rsplit('.', 1)
            fragment_name = splitname[0]
            fragment_var = splitname[1].upper()
            fragment_class = fragment_loader.get(fragment_name)

        if fragment_class is None:
            unknown_fragments.append(fragment_slug)
            continue

        # trust-tagged source propagates to loaded values; expressions and templates in config require trust
        fragment_yaml = _tags.TrustedAsTemplate().tag(getattr(fragment_class, fragment_var, None))
        if fragment_yaml is None:
            if fragment_var not in _FRAGMENTABLE:
                # if it's asking for something specific that's missing, that's an error
                unknown_fragments.append(fragment_slug)
                continue
            else:
                fragment_yaml = '{}'  # TODO: this is still an error later since we require 'options' below...

        fragment = yaml.load(_tags.Origin(path=filename).tag(fragment_yaml), Loader=AnsibleLoader)

        real_fragment_name = getattr(fragment_class, 'ansible_name')
        real_collection_name = '.'.join(real_fragment_name.split('.')[0:2]) if '.' in real_fragment_name else ''
        add_collection_to_versions_and_dates(fragment, real_collection_name, is_module=is_module, return_docs=(section == 'RETURN'))

        if section == 'DOCUMENTATION':
            # notes, seealso, options and attributes entries are specificly merged, but only occur in documentation section
            for doc_key in ['notes', 'seealso']:
                if doc_key in fragment:
                    entries = fragment.pop(doc_key)
                    if entries:
                        if doc_key not in doc:
                            doc[doc_key] = []
                        doc[doc_key].extend(entries)

            if 'options' not in fragment and 'attributes' not in fragment:
                raise AnsibleFragmentError("missing options or attributes in fragment (%s), possibly misformatted?: %s" % (fragment_name, filename))

            # ensure options themselves are directly merged
            for doc_key in ['options', 'attributes']:
                if doc_key in fragment:
                    if doc_key in doc:
                        try:
                            merge_fragment(doc[doc_key], fragment.pop(doc_key))
                        except Exception as e:
                            raise AnsibleFragmentError("%s %s (%s) of unknown type: %s" % (to_native(e), doc_key, fragment_name, filename))
                    else:
                        doc[doc_key] = fragment.pop(doc_key)

        # merge rest of the sections
        try:
            merge_fragment(doc, fragment)
        except Exception as e:
            raise AnsibleFragmentError("%s (%s) of unknown type: %s" % (to_native(e), fragment_name, filename))

    if unknown_fragments:
        raise AnsibleFragmentError('unknown doc_fragment(s) in file {0}: {1}'.format(filename, to_native(', '.join(unknown_fragments))))


def get_docstring(filename, fragment_loader, verbose=False, ignore_errors=False, collection_name=None, is_module=None, plugin_type=None):
    """
    DOCUMENTATION can be extended using documentation fragments loaded by the PluginLoader from the doc_fragments plugins.
    """

    if is_module is None:
        if plugin_type is None:
            is_module = False
        else:
            is_module = (plugin_type == 'module')
    else:
        # TODO deprecate is_module argument, now that we have 'type'
        pass

    data = read_docstring(filename, verbose=verbose, ignore_errors=ignore_errors)

    if data.get('doc', False):
        # add collection name to versions and dates
        if collection_name is not None:
            add_collection_to_versions_and_dates(data['doc'], collection_name, is_module=is_module)

        # add fragments to documentation
        add_fragments(data['doc'], filename, fragment_loader=fragment_loader, is_module=is_module, section='DOCUMENTATION')

    if data.get('returndocs', False):
        # add collection name to versions and dates
        if collection_name is not None:
            add_collection_to_versions_and_dates(data['returndocs'], collection_name, is_module=is_module, return_docs=True)

        # add fragments to return
        add_fragments(data['returndocs'], filename, fragment_loader=fragment_loader, is_module=is_module, section='RETURN')

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


def _find_adjacent(path, plugin, extensions):

    adjacent = Path(path)

    plugin_base_name = plugin.split('.')[-1]
    if adjacent.stem != plugin_base_name:
        # this should only affect filters/tests
        adjacent = adjacent.with_name(plugin_base_name)

    paths = []
    for ext in extensions:
        candidate = adjacent.with_suffix(ext)
        if candidate == adjacent:
            # we're looking for an adjacent file, skip this since it's identical
            continue
        if candidate.exists():
            paths.append(to_native(candidate))

    return paths


def find_plugin_docfile(plugin, plugin_type, loader):
    """  if the plugin lives in a non-python file (eg, win_X.ps1), require the corresponding 'sidecar' file for docs """

    context = loader.find_plugin_with_context(plugin, ignore_deprecated=False, check_aliases=True)
    if (not context or not context.resolved) and plugin_type in ('filter', 'test'):
        # should only happen for filters/test
        plugin_obj, context = loader.get_with_context(plugin)

    if not context or not context.resolved:
        raise AnsiblePluginNotFound('%s was not found' % (plugin), plugin_load_context=context)

    docfile = Path(context.plugin_resolved_path)
    if docfile.suffix not in C.DOC_EXTENSIONS:
        # only look for adjacent if plugin file does not support documents
        filenames = _find_adjacent(docfile, plugin, C.DOC_EXTENSIONS)
        filename = filenames[0] if filenames else None
    else:
        filename = to_native(docfile)

    if filename is None:
        raise AnsibleError('%s cannot contain DOCUMENTATION nor does it have a companion documentation file' % (plugin))

    return filename, context


def get_plugin_docs(plugin, plugin_type, loader, fragment_loader, verbose):

    # find plugin doc file, if it doesn't exist this will throw error, we let it through
    # can raise exception and short circuit when 'not found'
    filename, context = find_plugin_docfile(plugin, plugin_type, loader)
    collection_name = context.plugin_resolved_collection

    try:
        docs = get_docstring(filename, fragment_loader, verbose=verbose, collection_name=collection_name, plugin_type=plugin_type)
    except Exception as ex:
        raise AnsibleParserError(f'{plugin_type} plugin {plugin!r} did not contain a DOCUMENTATION attribute in {filename!r}.') from ex

    # no good? try adjacent
    if not docs[0]:
        for newfile in _find_adjacent(filename, plugin, C.DOC_EXTENSIONS):
            try:
                docs = get_docstring(newfile, fragment_loader, verbose=verbose, collection_name=collection_name, plugin_type=plugin_type)
                filename = newfile
                if docs[0] is not None:
                    break
            except Exception as ex:
                raise AnsibleParserError(f'{plugin_type} plugin {plugin!r} adjacent file did not contain a DOCUMENTATION attribute in {filename!r}.') from ex

    # add extra data to docs[0] (aka 'DOCUMENTATION')
    if docs[0] is None:
        raise AnsibleParserError(f'No documentation available for {plugin_type} plugin {plugin!r} in {filename!r}.')

    docs[0]['filename'] = filename
    docs[0]['collection'] = collection_name
    docs[0]['plugin_name'] = context.resolved_fqcn

    return docs


def __getattr__(importable_name):
    return _no_six.deprecate(importable_name, __name__, "string_types")
