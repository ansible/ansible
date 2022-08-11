# (c) Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import os


from ansible import constants as C
from ansible.collections.list import list_collections
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native, to_bytes
from ansible.plugins import loader
from ansible.utils.display import Display
from ansible.utils.path import is_subpath
from ansible.utils.collection_loader._collection_finder import _get_collection_path

display = Display()

# not real plugins
IGNORE = {
    # ptype: names
    'module': ('async_wrapper', ),
    'cache': ('base', ),
}


def _list_plugins_from_paths(ptype, dirs, collection, depth=0):

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
                    b_plugin, ext = os.path.splitext(plugin_file)
                    plugin = to_native(b_plugin)
                    full_path = os.path.join(b_path, plugin_file)

                    if os.path.isdir(full_path):
                        # its a dir, recurse
                        if collection in C.SYNTHETIC_COLLECTIONS:
                            if not os.path.exists(os.path.join(full_path, b'__init__.py')):
                                # dont recurse for synthetic unless init.py present
                                continue

                        # actually recurse dirs
                        plugins.update(_list_plugins_from_paths(ptype, [to_native(full_path)], collection, depth=depth + 1))
                    else:
                        if any([
                                plugin in C.IGNORE_FILES,                # general files to ignore
                                ext in C.REJECT_EXTS,                    # general extensions to ignore
                                plugin in IGNORE.get(bkey, ()),          # plugin in reject list
                        ]):
                            continue

                        if ptype in ('test', 'filter'):
                            ploader = getattr(loader, '{0}_loader'.format(ptype))

                            if ptype == 'filter':
                                method_name = 'filters'
                            elif ptype == 'test':
                                method_name = 'tests'
                            else:
                                raise AnsibleError('how did you get here?')

                            added = False

                            try:
                                if path not in ploader._extra_dirs:
                                    ploader.add_directory(path)
                                    added = True
                                for plugin_map in ploader.all():
                                    if not is_subpath(plugin_map._original_path, path, real=True):
                                        # loader will not restrict to collection so we need to do it here
                                        # requires both to be 'real' since loader solves symlinks
                                        continue
                                    try:
                                        # uses the jinja2 method tests/filters to get 'name -> function' map
                                        method_map = getattr(plugin_map, method_name)
                                        jplugins = method_map()
                                        seen = set()
                                        # skip aliases, names that reference same function
                                        for candidate in jplugins:
                                            if jplugins[candidate] not in seen:
                                                # use names and associate to actual file instead of 'function'
                                                composite = [collection]
                                                if depth:
                                                    composite.extend(plugin_map._original_path.split(os.path.sep)[depth * -1:])
                                                composite.append(to_native(candidate))
                                                fqcn = '.'.join(composite)
                                                plugins[fqcn] = plugin_map._original_path
                                                seen.add(jplugins[candidate])
                                    except Exception as e:
                                        display.warning("Skipping plugin file %s as it seems to be invalid: %r" % (to_native(plugin_map._original_path), e))
                            finally:
                                if added:
                                    ploader._extra_dirs.remove(os.path.realpath(path))
                                    ploader._clear_caches()
                        else:
                            # collectionize name
                            composite = [collection]
                            if depth:
                                composite.extend(path.split(os.path.sep)[depth * -1:])
                            composite.append(to_native(plugin))
                            plugin = '.'.join(composite)

                            if not os.path.islink(full_path):
                                # skip aliases, author should document in 'aliaes' field
                                plugins[plugin] = full_path
            else:
                display.debug("Skip listing plugins in '{0}' as it is not a directory".format(path))
        else:
            display.debug("Skip listing plugins in '{0}' as it does not exist".format(path))

    return plugins


def list_collection_plugins(ptype, collections, search_paths=None):

    # starts at  {plugin_name: filepath, ...}, but changes at the end
    plugins = {}
    dirs = []
    try:
        ploader = getattr(loader, '{0}_loader'.format(ptype))
    except AttributeError:
        raise AnsibleError('Cannot list plugins, incorrect plugin type supplied: {0}'.format(ptype))

    # get plugins for each collection
    for collection in collections.keys():
        if collection == 'ansible.builtin':
            # dirs from ansible install, but not configured paths
            dirs.extend([d.path for d in ploader._get_paths_with_context() if d.path not in ploader.config])
        elif collection == 'ansible.legacy':
            # configured paths + search paths (should include basedirs/-M)
            dirs = ploader.config
            if search_paths is not None:
                for d in search_paths:
                    if not d.endswith(ploader.subdir):
                        d = os.path.join([d, ploader.subdir])
                    dirs.append(d)
        else:
            # search path in this case is for locating collection itself
            b_ptype = to_bytes(C.COLLECTION_PTYPE_COMPAT.get(ptype, ptype))
            dirs = [to_native(os.path.join(collections[collection], b'plugins', b_ptype))]

        plugins.update(_list_plugins_from_paths(ptype, dirs, collection))

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


def list_plugins(ptype, collection=None, search_paths=None):

    # {plugin_name: (filepath, class), ...}
    plugins = {}
    do_legacy = False
    collections = {}
    if collection is None:
        # list all collections
        collections['ansible.builtin'] = b''
        collections.update(list_collections(search_paths=search_paths, dedupe=True))
        do_legacy = True
    elif collection == 'ansilbe.builtin':
        collections['ansible.builtin'] = b''
    elif collection == 'ansible.legacy':
        do_legacy = True
    else:
        try:
            collections[collection] = to_bytes(_get_collection_path(collection))
        except ValueError as e:
            raise AnsibleError("Cannot use supplied collection {0}: {1}".format(collection, to_native(e)), orig_exc=e)

    if collections:
        plugins.update(list_collection_plugins(ptype, collections))

    if do_legacy:
        legacy = list_collection_plugins(ptype, {'ansible.legacy': search_paths})
        for plugin in legacy.keys():
            builtin = plugin.replace('ansible.legacy.', 'ansible.builtin.', 1)
            if builtin in plugins and legacy[plugin][0] == plugins[builtin][0]:
                # add only if no overlap or overlap but diff files
                continue
            plugins[plugin] = legacy[plugin]

    return plugins


# wrappers
def list_plugin_names(ptype, collection=None):
    return list_plugins(ptype, collection).keys()


def list_plugin_files(ptype, collection=None):
    plugins = list_plugins(ptype, collection)
    return [plugins[k][0] for k in plugins.keys()]


def list_plugin_classes(ptype, collection=None):
    plugins = list_plugins(ptype, collection)
    return [plugins[k][1] for k in plugins.keys()]
