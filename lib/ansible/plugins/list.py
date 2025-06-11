# (c) Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


import os

from ansible import context
from ansible import constants as C
from ansible.collections.list import list_collections
from ansible.errors import AnsibleError
from ansible.module_utils.common.text.converters import to_native, to_bytes
from ansible.plugins import loader
from ansible.utils.display import Display
from ansible.utils.collection_loader._collection_finder import _get_collection_path

display = Display()

# not real plugins
IGNORE = {
    # ptype: names
    'module': ('async_wrapper', ),
    'cache': ('base', ),
}


def get_composite_name(collection, name, path, depth):
    resolved_collection = collection
    if '.' not in name:
        resource_name = name
    else:
        if collection == 'ansible.legacy' and name.startswith('ansible.builtin.'):
            resolved_collection = 'ansible.builtin'
        resource_name = '.'.join(name.split(f"{resolved_collection}.")[1:])

    # create FQCN
    composite = [resolved_collection]
    if depth:
        composite.extend(path.split(os.path.sep)[depth * -1:])
    composite.append(to_native(resource_name))
    return '.'.join(composite)


def _list_plugins_from_paths(ptype, dirs, collection, depth=0, docs=False):
    # TODO: update to use importlib.resources

    plugins = {}

    for path in dirs:
        display.debug("Searching '{0}'s '{1}' for {2} plugins".format(collection, path, ptype))
        b_path = to_bytes(path)

        if os.path.basename(b_path).startswith((b'.', b'__')):
            # skip hidden/special dirs
            continue

        if os.path.exists(b_path):
            if os.path.isdir(b_path):
                bkey = ptype.lower()
                for plugin_file in os.listdir(b_path):

                    if plugin_file.startswith((b'.', b'__')):
                        # hidden or python internal file/dir
                        continue

                    display.debug("Found possible plugin: '{0}'".format(plugin_file))
                    b_plugin, b_ext = os.path.splitext(plugin_file)
                    plugin = to_native(b_plugin)
                    full_path = os.path.join(b_path, plugin_file)

                    if os.path.isdir(full_path):
                        # its a dir, recurse
                        if collection in C.SYNTHETIC_COLLECTIONS:
                            if not os.path.exists(os.path.join(full_path, b'__init__.py')):
                                # dont recurse for synthetic unless init.py present
                                continue

                        # actually recurse dirs
                        plugins.update(_list_plugins_from_paths(ptype, [to_native(full_path)], collection, depth=depth + 1, docs=docs))
                    else:
                        if any([
                                plugin in C.IGNORE_FILES,                # general files to ignore
                                to_native(b_ext) in C.REJECT_EXTS,       # general extensions to ignore
                                b_ext in (b'.yml', b'.yaml', b'.json'),  # ignore docs files
                                plugin in IGNORE.get(bkey, ()),          # plugin in reject list
                                os.path.islink(full_path),               # skip aliases, author should document in 'aliases' field
                                not docs and b_ext in (b''),             # ignore no ext when looking for docs files
                        ]):
                            continue

                        if ptype in ('test', 'filter'):
                            try:
                                file_plugins = _list_j2_plugins_from_file(collection, full_path, ptype, plugin)
                            except KeyError as e:
                                display.warning('Skipping file %s: %s' % (full_path, to_native(e)))
                                continue

                            for plugin in file_plugins:
                                plugin_name = get_composite_name(collection, plugin.ansible_name, os.path.dirname(to_native(full_path)), depth)
                                plugins[plugin_name] = full_path
                        else:
                            plugin_name = get_composite_name(collection, plugin, os.path.dirname(to_native(full_path)), depth)
                            plugins[plugin_name] = full_path
            else:
                display.debug("Skip listing plugins in '{0}' as it is not a directory".format(path))
        else:
            display.debug("Skip listing plugins in '{0}' as it does not exist".format(path))

    return plugins


def _list_j2_plugins_from_file(collection, plugin_path, ptype, plugin_name):

    ploader = getattr(loader, '{0}_loader'.format(ptype))
    file_plugins = ploader.get_contained_plugins(collection, plugin_path, plugin_name)
    return file_plugins


def list_collection_plugins(ptype, collections, search_paths=None):
    # TODO: update to use importlib.resources

    # starts at  {plugin_name: filepath, ...}, but changes at the end
    plugins = {}
    try:
        ploader = getattr(loader, '{0}_loader'.format(ptype))
    except AttributeError:
        raise AnsibleError('Cannot list plugins, incorrect plugin type supplied: {0}'.format(ptype))

    # get plugins for each collection
    for collection in collections.keys():
        if collection == 'ansible.builtin':
            # dirs from ansible install, but not configured paths
            dirs = [d.path for d in ploader._get_paths_with_context() if d.internal]
        elif collection == 'ansible.legacy':
            # configured paths + search paths (should include basedirs/-M)
            dirs = [d.path for d in ploader._get_paths_with_context() if not d.internal]
            if context.CLIARGS.get('module_path', None):
                dirs.extend(context.CLIARGS['module_path'])
        else:
            # search path in this case is for locating collection itselfA
            b_ptype = to_bytes(C.COLLECTION_PTYPE_COMPAT.get(ptype, ptype))
            dirs = [to_native(os.path.join(collections[collection], b'plugins', b_ptype))]
            # acr = AnsibleCollectionRef.try_parse_fqcr(collection, ptype)
            # if acr:
            #     dirs = acr.subdirs
            # else:

            #     raise Exception('bad acr for %s, %s' % (collection, ptype))

        plugins.update(_list_plugins_from_paths(ptype, dirs, collection, docs=True))

    #  return plugin and it's class object, None for those not verifiable or failing
    if ptype in ('module',):
        # no 'invalid' tests for modules
        for plugin in plugins.keys():
            plugins[plugin] = (plugins[plugin], None)
    else:
        # detect invalid plugin candidates AND add loaded object to return data
        for plugin in list(plugins.keys()):
            pobj = None
            try:
                pobj = ploader.get(plugin, class_only=True)
            except Exception as e:
                display.vvv("The '{0}' {1} plugin could not be loaded from '{2}': {3}".format(plugin, ptype, plugins[plugin], to_native(e)))

            # sets final {plugin_name: (filepath, class|NONE if not loaded), ...}
            plugins[plugin] = (plugins[plugin], pobj)

    # {plugin_name: (filepath, class), ...}
    return plugins


def list_plugins(ptype, collections=None, search_paths=None):
    if isinstance(collections, str):
        collections = [collections]

    # {plugin_name: (filepath, class), ...}
    plugins = {}
    plugin_collections = {}
    if collections is None:
        # list all collections, add synthetic ones
        plugin_collections['ansible.builtin'] = b''
        plugin_collections['ansible.legacy'] = b''
        plugin_collections.update(list_collections(search_paths=search_paths, dedupe=True))
    else:
        for collection in collections:
            if collection == 'ansible.legacy':
                # add builtin, since legacy also resolves to these
                plugin_collections[collection] = b''
                plugin_collections['ansible.builtin'] = b''
            else:
                try:
                    plugin_collections[collection] = to_bytes(_get_collection_path(collection))
                except ValueError as e:
                    raise AnsibleError("Cannot use supplied collection {0}: {1}".format(collection, to_native(e)), orig_exc=e)

    if plugin_collections:
        plugins.update(list_collection_plugins(ptype, plugin_collections))

    return plugins


# wrappers
def list_plugin_names(ptype, collection=None):
    return [plugin.ansible_name for plugin in list_plugins(ptype, collection)]


def list_plugin_files(ptype, collection=None):
    plugins = list_plugins(ptype, collection)
    return [plugins[k][0] for k in plugins.keys()]


def list_plugin_classes(ptype, collection=None):
    plugins = list_plugins(ptype, collection)
    return [plugins[k][1] for k in plugins.keys()]
