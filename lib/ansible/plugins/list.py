# (c) Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


import dataclasses
import os

from ansible import context
from ansible import constants as C
from ansible.collections.list import list_collections
from ansible.errors import AnsibleError
from ansible.module_utils.common.text.converters import to_native, to_bytes
from ansible.plugins import loader
from ansible.utils.display import Display
from ansible.utils.collection_loader._collection_finder import _get_collection_path
from ansible._internal._templating._jinja_plugins import get_jinja_builtin_plugin_descriptions

display = Display()

# not real plugins
IGNORE = {
    # ptype: names
    'module': ('async_wrapper', ),
    'cache': ('base', ),
}


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class _PluginDocMetadata:
    """Information about a plugin."""

    name: str
    """The fully qualified name of the plugin."""
    path: bytes | None = None
    """The path to the plugin file, or None if not available."""
    plugin_obj: object | None = None
    """The loaded plugin object, or None if not loaded."""
    jinja_builtin_short_description: str | None = None
    """The short description of the plugin if it is a Jinja builtin, otherwise None."""


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

                        resource_dir = to_native(os.path.dirname(full_path))
                        resource_name = get_composite_name(collection, plugin, resource_dir, depth)

                        if ptype in ('test', 'filter'):
                            # NOTE: pass the composite resource to ensure any relative
                            # imports it contains are interpreted in the correct context
                            if collection:
                                resource_name = '.'.join(resource_name.split('.')[2:])
                            try:
                                file_plugins = _list_j2_plugins_from_file(collection, full_path, ptype, resource_name)
                            except KeyError as e:
                                display.warning('Skipping file %s: %s' % (full_path, to_native(e)))
                                continue

                            for plugin in file_plugins:
                                plugin_name = get_composite_name(collection, plugin.ansible_name, resource_dir, depth)
                                plugins[plugin_name] = full_path
                        else:
                            plugin_name = resource_name
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


def list_collection_plugins(ptype: str, collections: dict[str, bytes], search_paths: list[str] | None = None) -> dict[str, tuple[bytes, object | None]]:
    # Kept for backwards compatibility.
    return {
        name: (info.path, info.plugin_obj)
        for name, info in _list_collection_plugins_with_info(ptype, collections).items()
    }


def _list_collection_plugins_with_info(
    ptype: str,
    collections: dict[str, bytes],
) -> dict[str, _PluginDocMetadata]:
    # TODO: update to use importlib.resources

    try:
        ploader = getattr(loader, '{0}_loader'.format(ptype))
    except AttributeError:
        raise AnsibleError(f"Cannot list plugins, incorrect plugin type {ptype!r} supplied.") from None

    builtin_jinja_plugins = {}
    plugin_paths = {}

    # get plugins for each collection
    for collection, path in collections.items():
        if collection == 'ansible.builtin':
            # dirs from ansible install, but not configured paths
            dirs = [d.path for d in ploader._get_paths_with_context() if d.internal]

            if ptype in ('filter', 'test'):
                builtin_jinja_plugins = get_jinja_builtin_plugin_descriptions(ptype)

        elif collection == 'ansible.legacy':
            # configured paths + search paths (should include basedirs/-M)
            dirs = [d.path for d in ploader._get_paths_with_context() if not d.internal]
            if context.CLIARGS.get('module_path', None):
                dirs.extend(context.CLIARGS['module_path'])
        else:
            # search path in this case is for locating collection itselfA
            b_ptype = to_bytes(C.COLLECTION_PTYPE_COMPAT.get(ptype, ptype))
            dirs = [to_native(os.path.join(path, b'plugins', b_ptype))]
            # acr = AnsibleCollectionRef.try_parse_fqcr(collection, ptype)
            # if acr:
            #     dirs = acr.subdirs
            # else:

            #     raise Exception('bad acr for %s, %s' % (collection, ptype))

        plugin_paths.update(_list_plugins_from_paths(ptype, dirs, collection, docs=True))

    plugins = {}
    if ptype in ('module',):
        # no 'invalid' tests for modules
        for plugin, plugin_path in plugin_paths.items():
            plugins[plugin] = _PluginDocMetadata(name=plugin, path=plugin_path)
    else:
        # detect invalid plugin candidates AND add loaded object to return data
        for plugin, plugin_path in plugin_paths.items():
            pobj = None
            try:
                pobj = ploader.get(plugin, class_only=True)
            except Exception as e:
                display.vvv("The '{0}' {1} plugin could not be loaded from '{2}': {3}".format(plugin, ptype, plugin_path, to_native(e)))

            plugins[plugin] = _PluginDocMetadata(
                name=plugin,
                path=plugin_path,
                plugin_obj=pobj,
                jinja_builtin_short_description=builtin_jinja_plugins.get(plugin),
            )

        # Add in any builtin Jinja2 plugins that have not been shadowed in Ansible.
        plugins.update(
            (plugin_name, _PluginDocMetadata(name=plugin_name, jinja_builtin_short_description=plugin_description))
            for plugin_name, plugin_description in builtin_jinja_plugins.items() if plugin_name not in plugins
        )

    return plugins


def list_plugins(ptype: str, collections: list[str] | None = None, search_paths: list[str] | None = None) -> dict[str, tuple[bytes, object | None]]:
    # Kept for backwards compatibility.
    return {
        name: (info.path, info.plugin_obj)
        for name, info in _list_plugins_with_info(ptype, collections, search_paths).items()
    }


def _list_plugins_with_info(
    ptype: str,
    collections: list[str] = None,
    search_paths: list[str] | None = None,
) -> dict[str, _PluginDocMetadata]:
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
                except ValueError as ex:
                    raise AnsibleError(f"Cannot use supplied collection {collection!r}.") from ex

    if plugin_collections:
        plugins.update(_list_collection_plugins_with_info(ptype, plugin_collections))

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
