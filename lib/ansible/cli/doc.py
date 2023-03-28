#!/usr/bin/env python
# Copyright: (c) 2014, James Tanner <tanner.jc@gmail.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# PYTHON_ARGCOMPLETE_OK

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# ansible.cli needs to be imported first, to ensure the source bin/* scripts run that code first
from ansible.cli import CLI

import pkgutil
import os
import os.path
import re
import textwrap
import traceback

import ansible.plugins.loader as plugin_loader

from pathlib import Path

from ansible import constants as C
from ansible import context
from ansible.cli.arguments import option_helpers as opt_help
from ansible.collections.list import list_collection_dirs
from ansible.errors import AnsibleError, AnsibleOptionsError, AnsibleParserError, AnsiblePluginNotFound
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.common.collections import is_sequence
from ansible.module_utils.common.json import json_dump
from ansible.module_utils.common.yaml import yaml_dump
from ansible.module_utils.compat import importlib
from ansible.module_utils.six import string_types
from ansible.parsing.plugin_docs import read_docstub
from ansible.parsing.utils.yaml import from_yaml
from ansible.parsing.yaml.dumper import AnsibleDumper
from ansible.plugins.list import list_plugins
from ansible.plugins.loader import action_loader, fragment_loader
from ansible.utils.collection_loader import AnsibleCollectionConfig, AnsibleCollectionRef
from ansible.utils.collection_loader._collection_finder import _get_collection_name_from_path
from ansible.utils.display import Display
from ansible.utils.plugin_docs import get_plugin_docs, get_docstring, get_versioned_doclink

display = Display()


TARGET_OPTIONS = C.DOCUMENTABLE_PLUGINS + ('role', 'keyword',)
PB_OBJECTS = ['Play', 'Role', 'Block', 'Task']
PB_LOADED = {}
SNIPPETS = ['inventory', 'lookup', 'module']


def add_collection_plugins(plugin_list, plugin_type, coll_filter=None):
    display.deprecated("add_collection_plugins method, use ansible.plugins.list functions instead.", version='2.17')
    plugin_list.update(list_plugins(plugin_type, coll_filter))


def jdump(text):
    try:
        display.display(json_dump(text))
    except TypeError as e:
        display.vvv(traceback.format_exc())
        raise AnsibleError('We could not convert all the documentation into JSON as there was a conversion issue: %s' % to_native(e))


class RoleMixin(object):
    """A mixin containing all methods relevant to role argument specification functionality.

    Note: The methods for actual display of role data are not present here.
    """

    # Potential locations of the role arg spec file in the meta subdir, with main.yml
    # having the lowest priority.
    ROLE_ARGSPEC_FILES = ['argument_specs' + e for e in C.YAML_FILENAME_EXTENSIONS] + ["main" + e for e in C.YAML_FILENAME_EXTENSIONS]

    def _load_argspec(self, role_name, collection_path=None, role_path=None):
        """Load the role argument spec data from the source file.

        :param str role_name: The name of the role for which we want the argspec data.
        :param str collection_path: Path to the collection containing the role. This
            will be None for standard roles.
        :param str role_path: Path to the standard role. This will be None for
            collection roles.

        We support two files containing the role arg spec data: either meta/main.yml
        or meta/argument_spec.yml. The argument_spec.yml file will take precedence
        over the meta/main.yml file, if it exists. Data is NOT combined between the
        two files.

        :returns: A dict of all data underneath the ``argument_specs`` top-level YAML
            key in the argspec data file. Empty dict is returned if there is no data.
        """

        if collection_path:
            meta_path = os.path.join(collection_path, 'roles', role_name, 'meta')
        elif role_path:
            meta_path = os.path.join(role_path, 'meta')
        else:
            raise AnsibleError("A path is required to load argument specs for role '%s'" % role_name)

        path = None

        # Check all potential spec files
        for specfile in self.ROLE_ARGSPEC_FILES:
            full_path = os.path.join(meta_path, specfile)
            if os.path.exists(full_path):
                path = full_path
                break

        if path is None:
            return {}

        try:
            with open(path, 'r') as f:
                data = from_yaml(f.read(), file_name=path)
                if data is None:
                    data = {}
                return data.get('argument_specs', {})
        except (IOError, OSError) as e:
            raise AnsibleParserError("An error occurred while trying to read the file '%s': %s" % (path, to_native(e)), orig_exc=e)

    def _find_all_normal_roles(self, role_paths, name_filters=None):
        """Find all non-collection roles that have an argument spec file.

        Note that argument specs do not actually need to exist within the spec file.

        :param role_paths: A tuple of one or more role paths. When a role with the same name
            is found in multiple paths, only the first-found role is returned.
        :param name_filters: A tuple of one or more role names used to filter the results.

        :returns: A set of tuples consisting of: role name, full role path
        """
        found = set()
        found_names = set()

        for path in role_paths:
            if not os.path.isdir(path):
                continue

            # Check each subdir for an argument spec file
            for entry in os.listdir(path):
                role_path = os.path.join(path, entry)

                # Check all potential spec files
                for specfile in self.ROLE_ARGSPEC_FILES:
                    full_path = os.path.join(role_path, 'meta', specfile)
                    if os.path.exists(full_path):
                        if name_filters is None or entry in name_filters:
                            if entry not in found_names:
                                found.add((entry, role_path))
                            found_names.add(entry)
                        # select first-found
                        break
        return found

    def _find_all_collection_roles(self, name_filters=None, collection_filter=None):
        """Find all collection roles with an argument spec file.

        Note that argument specs do not actually need to exist within the spec file.

        :param name_filters: A tuple of one or more role names used to filter the results. These
            might be fully qualified with the collection name (e.g., community.general.roleA)
            or not (e.g., roleA).

        :param collection_filter: A string containing the FQCN of a collection which will be
            used to limit results. This filter will take precedence over the name_filters.

        :returns: A set of tuples consisting of: role name, collection name, collection path
        """
        found = set()
        b_colldirs = list_collection_dirs(coll_filter=collection_filter)
        for b_path in b_colldirs:
            path = to_text(b_path, errors='surrogate_or_strict')
            collname = _get_collection_name_from_path(b_path)

            roles_dir = os.path.join(path, 'roles')
            if os.path.exists(roles_dir):
                for entry in os.listdir(roles_dir):

                    # Check all potential spec files
                    for specfile in self.ROLE_ARGSPEC_FILES:
                        full_path = os.path.join(roles_dir, entry, 'meta', specfile)
                        if os.path.exists(full_path):
                            if name_filters is None:
                                found.add((entry, collname, path))
                            else:
                                # Name filters might contain a collection FQCN or not.
                                for fqcn in name_filters:
                                    if len(fqcn.split('.')) == 3:
                                        (ns, col, role) = fqcn.split('.')
                                        if '.'.join([ns, col]) == collname and entry == role:
                                            found.add((entry, collname, path))
                                    elif fqcn == entry:
                                        found.add((entry, collname, path))
                            break
        return found

    def _build_summary(self, role, collection, argspec):
        """Build a summary dict for a role.

        Returns a simplified role arg spec containing only the role entry points and their
        short descriptions, and the role collection name (if applicable).

        :param role: The simple role name.
        :param collection: The collection containing the role (None or empty string if N/A).
        :param argspec: The complete role argspec data dict.

        :returns: A tuple with the FQCN role name and a summary dict.
        """
        if collection:
            fqcn = '.'.join([collection, role])
        else:
            fqcn = role
        summary = {}
        summary['collection'] = collection
        summary['entry_points'] = {}
        for ep in argspec.keys():
            entry_spec = argspec[ep] or {}
            summary['entry_points'][ep] = entry_spec.get('short_description', '')
        return (fqcn, summary)

    def _build_doc(self, role, path, collection, argspec, entry_point):
        if collection:
            fqcn = '.'.join([collection, role])
        else:
            fqcn = role
        doc = {}
        doc['path'] = path
        doc['collection'] = collection
        doc['entry_points'] = {}
        for ep in argspec.keys():
            if entry_point is None or ep == entry_point:
                entry_spec = argspec[ep] or {}
                doc['entry_points'][ep] = entry_spec

        # If we didn't add any entry points (b/c of filtering), ignore this entry.
        if len(doc['entry_points'].keys()) == 0:
            doc = None

        return (fqcn, doc)

    def _create_role_list(self, fail_on_errors=True):
        """Return a dict describing the listing of all roles with arg specs.

        :param role_paths: A tuple of one or more role paths.

        :returns: A dict indexed by role name, with 'collection' and 'entry_points' keys per role.

        Example return:

            results = {
               'roleA': {
                  'collection': '',
                  'entry_points': {
                     'main': 'Short description for main'
                  }
               },
               'a.b.c.roleB': {
                  'collection': 'a.b.c',
                  'entry_points': {
                     'main': 'Short description for main',
                     'alternate': 'Short description for alternate entry point'
                  }
               'x.y.z.roleB': {
                  'collection': 'x.y.z',
                  'entry_points': {
                     'main': 'Short description for main',
                  }
               },
            }
        """
        roles_path = self._get_roles_path()
        collection_filter = self._get_collection_filter()
        if not collection_filter:
            roles = self._find_all_normal_roles(roles_path)
        else:
            roles = []
        collroles = self._find_all_collection_roles(collection_filter=collection_filter)

        result = {}

        for role, role_path in roles:
            try:
                argspec = self._load_argspec(role, role_path=role_path)
                fqcn, summary = self._build_summary(role, '', argspec)
                result[fqcn] = summary
            except Exception as e:
                if fail_on_errors:
                    raise
                result[role] = {
                    'error': 'Error while loading role argument spec: %s' % to_native(e),
                }

        for role, collection, collection_path in collroles:
            try:
                argspec = self._load_argspec(role, collection_path=collection_path)
                fqcn, summary = self._build_summary(role, collection, argspec)
                result[fqcn] = summary
            except Exception as e:
                if fail_on_errors:
                    raise
                result['%s.%s' % (collection, role)] = {
                    'error': 'Error while loading role argument spec: %s' % to_native(e),
                }

        return result

    def _create_role_doc(self, role_names, entry_point=None, fail_on_errors=True):
        """
        :param role_names: A tuple of one or more role names.
        :param role_paths: A tuple of one or more role paths.
        :param entry_point: A role entry point name for filtering.
        :param fail_on_errors: When set to False, include errors in the JSON output instead of raising errors

        :returns: A dict indexed by role name, with 'collection', 'entry_points', and 'path' keys per role.
        """
        roles_path = self._get_roles_path()
        roles = self._find_all_normal_roles(roles_path, name_filters=role_names)
        collroles = self._find_all_collection_roles(name_filters=role_names)

        result = {}

        for role, role_path in roles:
            try:
                argspec = self._load_argspec(role, role_path=role_path)
                fqcn, doc = self._build_doc(role, role_path, '', argspec, entry_point)
                if doc:
                    result[fqcn] = doc
            except Exception as e:  # pylint:disable=broad-except
                result[role] = {
                    'error': 'Error while processing role: %s' % to_native(e),
                }

        for role, collection, collection_path in collroles:
            try:
                argspec = self._load_argspec(role, collection_path=collection_path)
                fqcn, doc = self._build_doc(role, collection_path, collection, argspec, entry_point)
                if doc:
                    result[fqcn] = doc
            except Exception as e:  # pylint:disable=broad-except
                result['%s.%s' % (collection, role)] = {
                    'error': 'Error while processing role: %s' % to_native(e),
                }

        return result


class DocCLI(CLI, RoleMixin):
    ''' displays information on modules installed in Ansible libraries.
        It displays a terse listing of plugins and their short descriptions,
        provides a printout of their DOCUMENTATION strings,
        and it can create a short "snippet" which can be pasted into a playbook.  '''

    name = 'ansible-doc'

    # default ignore list for detailed views
    IGNORE = ('module', 'docuri', 'version_added', 'version_added_collection', 'short_description', 'now_date', 'plainexamples', 'returndocs', 'collection')

    # Warning: If you add more elements here, you also need to add it to the docsite build (in the
    # ansible-community/antsibull repo)
    _ITALIC = re.compile(r"\bI\(([^)]+)\)")
    _BOLD = re.compile(r"\bB\(([^)]+)\)")
    _MODULE = re.compile(r"\bM\(([^)]+)\)")
    _LINK = re.compile(r"\bL\(([^)]+), *([^)]+)\)")
    _URL = re.compile(r"\bU\(([^)]+)\)")
    _REF = re.compile(r"\bR\(([^)]+), *([^)]+)\)")
    _CONST = re.compile(r"\bC\(([^)]+)\)")
    _RULER = re.compile(r"\bHORIZONTALLINE\b")

    # rst specific
    _RST_NOTE = re.compile(r".. note::")
    _RST_SEEALSO = re.compile(r".. seealso::")
    _RST_ROLES = re.compile(r":\w+?:`")
    _RST_DIRECTIVES = re.compile(r".. \w+?::")

    def __init__(self, args):

        super(DocCLI, self).__init__(args)
        self.plugin_list = set()

    @classmethod
    def find_plugins(cls, path, internal, plugin_type, coll_filter=None):
        display.deprecated("find_plugins method as it is incomplete/incorrect. use ansible.plugins.list functions instead.", version='2.17')
        return list_plugins(plugin_type, coll_filter, [path]).keys()

    @classmethod
    def tty_ify(cls, text):

        # general formatting
        t = cls._ITALIC.sub(r"`\1'", text)    # I(word) => `word'
        t = cls._BOLD.sub(r"*\1*", t)         # B(word) => *word*
        t = cls._MODULE.sub("[" + r"\1" + "]", t)       # M(word) => [word]
        t = cls._URL.sub(r"\1", t)                      # U(word) => word
        t = cls._LINK.sub(r"\1 <\2>", t)                # L(word, url) => word <url>
        t = cls._REF.sub(r"\1", t)            # R(word, sphinx-ref) => word
        t = cls._CONST.sub(r"`\1'", t)        # C(word) => `word'
        t = cls._RULER.sub("\n{0}\n".format("-" * 13), t)   # HORIZONTALLINE => -------

        # remove rst
        t = cls._RST_SEEALSO.sub(r"See also:", t)   # seealso to See also:
        t = cls._RST_NOTE.sub(r"Note:", t)          # .. note:: to note:
        t = cls._RST_ROLES.sub(r"`", t)             # remove :ref: and other tags, keep tilde to match ending one
        t = cls._RST_DIRECTIVES.sub(r"", t)         # remove .. stuff:: in general

        return t

    def init_parser(self):

        coll_filter = 'A supplied argument will be used for filtering, can be a namespace or full collection name.'

        super(DocCLI, self).init_parser(
            desc="plugin documentation tool",
            epilog="See man pages for Ansible CLI options or website for tutorials https://docs.ansible.com"
        )
        opt_help.add_module_options(self.parser)
        opt_help.add_basedir_options(self.parser)

        # targets
        self.parser.add_argument('args', nargs='*', help='Plugin', metavar='plugin')

        self.parser.add_argument("-t", "--type", action="store", default='module', dest='type',
                                 help='Choose which plugin type (defaults to "module"). '
                                      'Available plugin types are : {0}'.format(TARGET_OPTIONS),
                                 choices=TARGET_OPTIONS)

        # formatting
        self.parser.add_argument("-j", "--json", action="store_true", default=False, dest='json_format',
                                 help='Change output into json format.')

        # TODO: warn if not used with -t roles
        # role-specific options
        self.parser.add_argument("-r", "--roles-path", dest='roles_path', default=C.DEFAULT_ROLES_PATH,
                                 type=opt_help.unfrack_path(pathsep=True),
                                 action=opt_help.PrependListAction,
                                 help='The path to the directory containing your roles.')

        # modifiers
        exclusive = self.parser.add_mutually_exclusive_group()
        # TODO: warn if not used with -t roles
        exclusive.add_argument("-e", "--entry-point", dest="entry_point",
                               help="Select the entry point for role(s).")

        # TODO: warn with --json as it is incompatible
        exclusive.add_argument("-s", "--snippet", action="store_true", default=False, dest='show_snippet',
                               help='Show playbook snippet for these plugin types: %s' % ', '.join(SNIPPETS))

        # TODO: warn when arg/plugin is passed
        exclusive.add_argument("-F", "--list_files", action="store_true", default=False, dest="list_files",
                               help='Show plugin names and their source files without summaries (implies --list). %s' % coll_filter)
        exclusive.add_argument("-l", "--list", action="store_true", default=False, dest='list_dir',
                               help='List available plugins. %s' % coll_filter)
        exclusive.add_argument("--metadata-dump", action="store_true", default=False, dest='dump',
                               help='**For internal use only** Dump json metadata for all entries, ignores other options.')

        self.parser.add_argument("--no-fail-on-errors", action="store_true", default=False, dest='no_fail_on_errors',
                                 help='**For internal use only** Only used for --metadata-dump. '
                                      'Do not fail on errors. Report the error message in the JSON instead.')

    def post_process_args(self, options):
        options = super(DocCLI, self).post_process_args(options)

        display.verbosity = options.verbosity

        return options

    def display_plugin_list(self, results):

        # format for user
        displace = max(len(x) for x in results.keys())
        linelimit = display.columns - displace - 5
        text = []
        deprecated = []

        # format display per option
        if context.CLIARGS['list_files']:
            # list plugin file names
            for plugin in sorted(results.keys()):
                filename = to_native(results[plugin])

                # handle deprecated for builtin/legacy
                pbreak = plugin.split('.')
                if pbreak[-1].startswith('_') and pbreak[0] == 'ansible' and pbreak[1] in ('builtin', 'legacy'):
                    pbreak[-1] = pbreak[-1][1:]
                    plugin = '.'.join(pbreak)
                    deprecated.append("%-*s %-*.*s" % (displace, plugin, linelimit, len(filename), filename))
                else:
                    text.append("%-*s %-*.*s" % (displace, plugin, linelimit, len(filename), filename))
        else:
            # list plugin names and short desc
            for plugin in sorted(results.keys()):
                desc = DocCLI.tty_ify(results[plugin])

                if len(desc) > linelimit:
                    desc = desc[:linelimit] + '...'

                pbreak = plugin.split('.')
                if pbreak[-1].startswith('_'):  # Handle deprecated # TODO: add mark for deprecated collection plugins
                    pbreak[-1] = pbreak[-1][1:]
                    plugin = '.'.join(pbreak)
                    deprecated.append("%-*s %-*.*s" % (displace, plugin, linelimit, len(desc), desc))
                else:
                    text.append("%-*s %-*.*s" % (displace, plugin, linelimit, len(desc), desc))

        if len(deprecated) > 0:
            text.append("\nDEPRECATED:")
            text.extend(deprecated)

        # display results
        DocCLI.pager("\n".join(text))

    def _display_available_roles(self, list_json):
        """Display all roles we can find with a valid argument specification.

        Output is: fqcn role name, entry point, short description
        """
        roles = list(list_json.keys())
        entry_point_names = set()
        for role in roles:
            for entry_point in list_json[role]['entry_points'].keys():
                entry_point_names.add(entry_point)

        max_role_len = 0
        max_ep_len = 0

        if roles:
            max_role_len = max(len(x) for x in roles)
        if entry_point_names:
            max_ep_len = max(len(x) for x in entry_point_names)

        linelimit = display.columns - max_role_len - max_ep_len - 5
        text = []

        for role in sorted(roles):
            for entry_point, desc in list_json[role]['entry_points'].items():
                if len(desc) > linelimit:
                    desc = desc[:linelimit] + '...'
                text.append("%-*s %-*s %s" % (max_role_len, role,
                                              max_ep_len, entry_point,
                                              desc))

        # display results
        DocCLI.pager("\n".join(text))

    def _display_role_doc(self, role_json):
        roles = list(role_json.keys())
        text = []
        for role in roles:
            text += self.get_role_man_text(role, role_json[role])

        # display results
        DocCLI.pager("\n".join(text))

    @staticmethod
    def _list_keywords():
        return from_yaml(pkgutil.get_data('ansible', 'keyword_desc.yml'))

    @staticmethod
    def _get_keywords_docs(keys):

        data = {}
        descs = DocCLI._list_keywords()
        for key in keys:

            if key.startswith('with_'):
                # simplify loops, dont want to handle every with_<lookup> combo
                keyword = 'loop'
            elif key == 'async':
                # cause async became reserved in python we had to rename internally
                keyword = 'async_val'
            else:
                keyword = key

            try:
                # if no desc, typeerror raised ends this block
                kdata = {'description': descs[key]}

                # get playbook objects for keyword and use first to get keyword attributes
                kdata['applies_to'] = []
                for pobj in PB_OBJECTS:
                    if pobj not in PB_LOADED:
                        obj_class = 'ansible.playbook.%s' % pobj.lower()
                        loaded_class = importlib.import_module(obj_class)
                        PB_LOADED[pobj] = getattr(loaded_class, pobj, None)

                    if keyword in PB_LOADED[pobj].fattributes:
                        kdata['applies_to'].append(pobj)

                        # we should only need these once
                        if 'type' not in kdata:

                            fa = PB_LOADED[pobj].fattributes.get(keyword)
                            if getattr(fa, 'private'):
                                kdata = {}
                                raise KeyError

                            kdata['type'] = getattr(fa, 'isa', 'string')

                            if keyword.endswith('when') or keyword in ('until',):
                                # TODO: make this a field attribute property,
                                # would also helps with the warnings on {{}} stacking
                                kdata['template'] = 'implicit'
                            elif getattr(fa, 'static'):
                                kdata['template'] = 'static'
                            else:
                                kdata['template'] = 'explicit'

                            # those that require no processing
                            for visible in ('alias', 'priority'):
                                kdata[visible] = getattr(fa, visible)

                # remove None keys
                for k in list(kdata.keys()):
                    if kdata[k] is None:
                        del kdata[k]

                data[key] = kdata

            except (AttributeError, KeyError) as e:
                display.warning("Skipping Invalid keyword '%s' specified: %s" % (key, to_text(e)))
                if display.verbosity >= 3:
                    display.verbose(traceback.format_exc())

        return data

    def _get_collection_filter(self):

        coll_filter = None
        if len(context.CLIARGS['args']) == 1:
            coll_filter = context.CLIARGS['args'][0]
            if not AnsibleCollectionRef.is_valid_collection_name(coll_filter):
                raise AnsibleError('Invalid collection name (must be of the form namespace.collection): {0}'.format(coll_filter))
            elif len(context.CLIARGS['args']) > 1:
                raise AnsibleOptionsError("Only a single collection filter is supported.")

        return coll_filter

    def _list_plugins(self, plugin_type, content):

        results = {}
        self.plugins = {}
        loader = DocCLI._prep_loader(plugin_type)

        coll_filter = self._get_collection_filter()
        self.plugins.update(list_plugins(plugin_type, coll_filter))

        # get appropriate content depending on option
        if content == 'dir':
            results = self._get_plugin_list_descriptions(loader)
        elif content == 'files':
            results = {k: self.plugins[k][0] for k in self.plugins.keys()}
        else:
            results = {k: {} for k in self.plugins.keys()}
            self.plugin_list = set()  # reset for next iteration

        return results

    def _get_plugins_docs(self, plugin_type, names, fail_ok=False, fail_on_errors=True):

        loader = DocCLI._prep_loader(plugin_type)

        # get the docs for plugins in the command line list
        plugin_docs = {}
        for plugin in names:
            doc = {}
            try:
                doc, plainexamples, returndocs, metadata = get_plugin_docs(plugin, plugin_type, loader, fragment_loader, (context.CLIARGS['verbosity'] > 0))
            except AnsiblePluginNotFound as e:
                display.warning(to_native(e))
                continue
            except Exception as e:
                if not fail_on_errors:
                    plugin_docs[plugin] = {'error': 'Missing documentation or could not parse documentation: %s' % to_native(e)}
                    continue
                display.vvv(traceback.format_exc())
                msg = "%s %s missing documentation (or could not parse documentation): %s\n" % (plugin_type, plugin, to_native(e))
                if fail_ok:
                    display.warning(msg)
                else:
                    raise AnsibleError(msg)

            if not doc:
                # The doc section existed but was empty
                if not fail_on_errors:
                    plugin_docs[plugin] = {'error': 'No valid documentation found'}
                continue

            docs = DocCLI._combine_plugin_doc(plugin, plugin_type, doc, plainexamples, returndocs, metadata)
            if not fail_on_errors:
                # Check whether JSON serialization would break
                try:
                    json_dump(docs)
                except Exception as e:  # pylint:disable=broad-except
                    plugin_docs[plugin] = {'error': 'Cannot serialize documentation as JSON: %s' % to_native(e)}
                    continue

            plugin_docs[plugin] = docs

        return plugin_docs

    def _get_roles_path(self):
        '''
         Add any 'roles' subdir in playbook dir to the roles search path.
         And as a last resort, add the playbook dir itself. Order being:
           - 'roles' subdir of playbook dir
           - DEFAULT_ROLES_PATH (default in cliargs)
           - playbook dir (basedir)
         NOTE: This matches logic in RoleDefinition._load_role_path() method.
        '''
        roles_path = context.CLIARGS['roles_path']
        if context.CLIARGS['basedir'] is not None:
            subdir = os.path.join(context.CLIARGS['basedir'], "roles")
            if os.path.isdir(subdir):
                roles_path = (subdir,) + roles_path
            roles_path = roles_path + (context.CLIARGS['basedir'],)
        return roles_path

    @staticmethod
    def _prep_loader(plugin_type):
        ''' return a plugint type specific loader '''
        loader = getattr(plugin_loader, '%s_loader' % plugin_type)

        # add to plugin paths from command line
        if context.CLIARGS['basedir'] is not None:
            loader.add_directory(context.CLIARGS['basedir'], with_subdir=True)

        if context.CLIARGS['module_path']:
            for path in context.CLIARGS['module_path']:
                if path:
                    loader.add_directory(path)

        # save only top level paths for errors
        loader._paths = None  # reset so we can use subdirs later

        return loader

    def run(self):

        super(DocCLI, self).run()

        basedir = context.CLIARGS['basedir']
        plugin_type = context.CLIARGS['type'].lower()
        do_json = context.CLIARGS['json_format'] or context.CLIARGS['dump']
        listing = context.CLIARGS['list_files'] or context.CLIARGS['list_dir']

        if context.CLIARGS['list_files']:
            content = 'files'
        elif context.CLIARGS['list_dir']:
            content = 'dir'
        else:
            content = None

        docs = {}

        if basedir:
            AnsibleCollectionConfig.playbook_paths = basedir

        if plugin_type not in TARGET_OPTIONS:
            raise AnsibleOptionsError("Unknown or undocumentable plugin type: %s" % plugin_type)

        if context.CLIARGS['dump']:
            # we always dump all types, ignore restrictions
            ptypes = TARGET_OPTIONS
            docs['all'] = {}
            for ptype in ptypes:

                no_fail = bool(not context.CLIARGS['no_fail_on_errors'])
                if ptype == 'role':
                    roles = self._create_role_list(fail_on_errors=no_fail)
                    docs['all'][ptype] = self._create_role_doc(roles.keys(), context.CLIARGS['entry_point'], fail_on_errors=no_fail)
                elif ptype == 'keyword':
                    names = DocCLI._list_keywords()
                    docs['all'][ptype] = DocCLI._get_keywords_docs(names.keys())
                else:
                    plugin_names = self._list_plugins(ptype, None)
                    docs['all'][ptype] = self._get_plugins_docs(ptype, plugin_names, fail_ok=(ptype in ('test', 'filter')), fail_on_errors=no_fail)
                    # reset list after each type to avoid polution
        elif listing:
            if plugin_type == 'keyword':
                docs = DocCLI._list_keywords()
            elif plugin_type == 'role':
                docs = self._create_role_list()
            else:
                docs = self._list_plugins(plugin_type, content)
        else:
            # here we require a name
            if len(context.CLIARGS['args']) == 0:
                raise AnsibleOptionsError("Missing name(s), incorrect options passed for detailed documentation.")

            if plugin_type == 'keyword':
                docs = DocCLI._get_keywords_docs(context.CLIARGS['args'])
            elif plugin_type == 'role':
                docs = self._create_role_doc(context.CLIARGS['args'], context.CLIARGS['entry_point'])
            else:
                # display specific plugin docs
                docs = self._get_plugins_docs(plugin_type, context.CLIARGS['args'])

        # Display the docs
        if do_json:
            jdump(docs)
        else:
            text = []
            if plugin_type in C.DOCUMENTABLE_PLUGINS:
                if listing and docs:
                    self.display_plugin_list(docs)
                elif context.CLIARGS['show_snippet']:
                    if plugin_type not in SNIPPETS:
                        raise AnsibleError('Snippets are only available for the following plugin'
                                           ' types: %s' % ', '.join(SNIPPETS))

                    for plugin, doc_data in docs.items():
                        try:
                            textret = DocCLI.format_snippet(plugin, plugin_type, doc_data['doc'])
                        except ValueError as e:
                            display.warning("Unable to construct a snippet for"
                                            " '{0}': {1}".format(plugin, to_text(e)))
                        else:
                            text.append(textret)
                else:
                    # Some changes to how plain text docs are formatted
                    for plugin, doc_data in docs.items():

                        textret = DocCLI.format_plugin_doc(plugin, plugin_type,
                                                           doc_data['doc'], doc_data['examples'],
                                                           doc_data['return'], doc_data['metadata'])
                        if textret:
                            text.append(textret)
                        else:
                            display.warning("No valid documentation was retrieved from '%s'" % plugin)

            elif plugin_type == 'role':
                if context.CLIARGS['list_dir'] and docs:
                    self._display_available_roles(docs)
                elif docs:
                    self._display_role_doc(docs)

            elif docs:
                text = DocCLI.tty_ify(DocCLI._dump_yaml(docs))

            if text:
                DocCLI.pager(''.join(text))

        return 0

    @staticmethod
    def get_all_plugins_of_type(plugin_type):
        loader = getattr(plugin_loader, '%s_loader' % plugin_type)
        paths = loader._get_paths_with_context()
        plugins = {}
        for path_context in paths:
            plugins.update(list_plugins(plugin_type))
        return sorted(plugins.keys())

    @staticmethod
    def get_plugin_metadata(plugin_type, plugin_name):
        # if the plugin lives in a non-python file (eg, win_X.ps1), require the corresponding python file for docs
        loader = getattr(plugin_loader, '%s_loader' % plugin_type)
        result = loader.find_plugin_with_context(plugin_name, mod_type='.py', ignore_deprecated=True, check_aliases=True)
        if not result.resolved:
            raise AnsibleError("unable to load {0} plugin named {1} ".format(plugin_type, plugin_name))
        filename = result.plugin_resolved_path
        collection_name = result.plugin_resolved_collection

        try:
            doc, __, __, __ = get_docstring(filename, fragment_loader, verbose=(context.CLIARGS['verbosity'] > 0),
                                            collection_name=collection_name, plugin_type=plugin_type)
        except Exception:
            display.vvv(traceback.format_exc())
            raise AnsibleError("%s %s at %s has a documentation formatting error or is missing documentation." % (plugin_type, plugin_name, filename))

        if doc is None:
            # Removed plugins don't have any documentation
            return None

        return dict(
            name=plugin_name,
            namespace=DocCLI.namespace_from_plugin_filepath(filename, plugin_name, loader.package_path),
            description=doc.get('short_description', "UNKNOWN"),
            version_added=doc.get('version_added', "UNKNOWN")
        )

    @staticmethod
    def namespace_from_plugin_filepath(filepath, plugin_name, basedir):
        if not basedir.endswith('/'):
            basedir += '/'
        rel_path = filepath.replace(basedir, '')
        extension_free = os.path.splitext(rel_path)[0]
        namespace_only = extension_free.rsplit(plugin_name, 1)[0].strip('/_')
        clean_ns = namespace_only.replace('/', '.')
        if clean_ns == '':
            clean_ns = None

        return clean_ns

    @staticmethod
    def _combine_plugin_doc(plugin, plugin_type, doc, plainexamples, returndocs, metadata):
        # generate extra data
        if plugin_type == 'module':
            # is there corresponding action plugin?
            if plugin in action_loader:
                doc['has_action'] = True
            else:
                doc['has_action'] = False

        # return everything as one dictionary
        return {'doc': doc, 'examples': plainexamples, 'return': returndocs, 'metadata': metadata}

    @staticmethod
    def format_snippet(plugin, plugin_type, doc):
        ''' return heavily commented plugin use to insert into play '''
        if plugin_type == 'inventory' and doc.get('options', {}).get('plugin'):
            # these do not take a yaml config that we can write a snippet for
            raise ValueError('The {0} inventory plugin does not take YAML type config source'
                             ' that can be used with the "auto" plugin so a snippet cannot be'
                             ' created.'.format(plugin))

        text = []

        if plugin_type == 'lookup':
            text = _do_lookup_snippet(doc)

        elif 'options' in doc:
            text = _do_yaml_snippet(doc)

        text.append('')
        return "\n".join(text)

    @staticmethod
    def format_plugin_doc(plugin, plugin_type, doc, plainexamples, returndocs, metadata):
        collection_name = doc['collection']

        # TODO: do we really want this?
        # add_collection_to_versions_and_dates(doc, '(unknown)', is_module=(plugin_type == 'module'))
        # remove_current_collection_from_versions_and_dates(doc, collection_name, is_module=(plugin_type == 'module'))
        # remove_current_collection_from_versions_and_dates(
        #     returndocs, collection_name, is_module=(plugin_type == 'module'), return_docs=True)

        # assign from other sections
        doc['plainexamples'] = plainexamples
        doc['returndocs'] = returndocs
        doc['metadata'] = metadata

        try:
            text = DocCLI.get_man_text(doc, collection_name, plugin_type)
        except Exception as e:
            display.vvv(traceback.format_exc())
            raise AnsibleError("Unable to retrieve documentation from '%s' due to: %s" % (plugin, to_native(e)), orig_exc=e)

        return text

    def _get_plugin_list_descriptions(self, loader):

        descs = {}
        for plugin in self.plugins.keys():
            # TODO: move to plugin itself i.e: plugin.get_desc()
            doc = None
            filename = Path(to_native(self.plugins[plugin][0]))
            docerror = None
            try:
                doc = read_docstub(filename)
            except Exception as e:
                docerror = e

            # plugin file was empty or had error, lets try other options
            if doc is None:
                # handle test/filters that are in file with diff name
                base = plugin.split('.')[-1]
                basefile = filename.with_name(base + filename.suffix)
                for extension in C.DOC_EXTENSIONS:
                    docfile = basefile.with_suffix(extension)
                    try:
                        if docfile.exists():
                            doc = read_docstub(docfile)
                    except Exception as e:
                        docerror = e

            if docerror:
                display.warning("%s has a documentation formatting error: %s" % (plugin, docerror))
                continue

            if not doc or not isinstance(doc, dict):
                desc = 'UNDOCUMENTED'
            else:
                desc = doc.get('short_description', 'INVALID SHORT DESCRIPTION').strip()

            descs[plugin] = desc

        return descs

    @staticmethod
    def print_paths(finder):
        ''' Returns a string suitable for printing of the search path '''

        # Uses a list to get the order right
        ret = []
        for i in finder._get_paths(subdirs=False):
            i = to_text(i, errors='surrogate_or_strict')
            if i not in ret:
                ret.append(i)
        return os.pathsep.join(ret)

    @staticmethod
    def _dump_yaml(struct, flow_style=False):
        return yaml_dump(struct, default_flow_style=flow_style, default_style="''", Dumper=AnsibleDumper).rstrip('\n')

    @staticmethod
    def _indent_lines(text, indent):
        return DocCLI.tty_ify('\n'.join([indent + line for line in text.split('\n')]))

    @staticmethod
    def _format_version_added(version_added, version_added_collection=None):
        if version_added_collection == 'ansible.builtin':
            version_added_collection = 'ansible-core'
            # In ansible-core, version_added can be 'historical'
            if version_added == 'historical':
                return 'historical'
        if version_added_collection:
            version_added = '%s of %s' % (version_added, version_added_collection)
        return 'version %s' % (version_added, )

    @staticmethod
    def add_fields(text, fields, limit, opt_indent, return_values=False, base_indent=''):

        for o in sorted(fields):
            # Create a copy so we don't modify the original (in case YAML anchors have been used)
            opt = dict(fields[o])

            # required is used as indicator and removed
            required = opt.pop('required', False)
            if not isinstance(required, bool):
                raise AnsibleError("Incorrect value for 'Required', a boolean is needed.: %s" % required)
            if required:
                opt_leadin = "="
            else:
                opt_leadin = "-"

            text.append("%s%s %s" % (base_indent, opt_leadin, o))

            # description is specifically formated and can either be string or list of strings
            if 'description' not in opt:
                raise AnsibleError("All (sub-)options and return values must have a 'description' field")
            if is_sequence(opt['description']):
                for entry_idx, entry in enumerate(opt['description'], 1):
                    if not isinstance(entry, string_types):
                        raise AnsibleError("Expected string in description of %s at index %s, got %s" % (o, entry_idx, type(entry)))
                    text.append(textwrap.fill(DocCLI.tty_ify(entry), limit, initial_indent=opt_indent, subsequent_indent=opt_indent))
            else:
                if not isinstance(opt['description'], string_types):
                    raise AnsibleError("Expected string in description of %s, got %s" % (o, type(opt['description'])))
                text.append(textwrap.fill(DocCLI.tty_ify(opt['description']), limit, initial_indent=opt_indent, subsequent_indent=opt_indent))
            del opt['description']

            suboptions = []
            for subkey in ('options', 'suboptions', 'contains', 'spec'):
                if subkey in opt:
                    suboptions.append((subkey, opt.pop(subkey)))

            if not required and not return_values and 'default' not in opt:
                opt['default'] = None

            # sanitize config items
            conf = {}
            for config in ('env', 'ini', 'yaml', 'vars', 'keyword'):
                if config in opt and opt[config]:
                    # Create a copy so we don't modify the original (in case YAML anchors have been used)
                    conf[config] = [dict(item) for item in opt.pop(config)]
                    for ignore in DocCLI.IGNORE:
                        for item in conf[config]:
                            if ignore in item:
                                del item[ignore]

            # reformat cli optoins
            if 'cli' in opt and opt['cli']:
                conf['cli'] = []
                for cli in opt['cli']:
                    if 'option' not in cli:
                        conf['cli'].append({'name': cli['name'], 'option': '--%s' % cli['name'].replace('_', '-')})
                    else:
                        conf['cli'].append(cli)
                del opt['cli']

            # add custom header for conf
            if conf:
                text.append(DocCLI._indent_lines(DocCLI._dump_yaml({'set_via': conf}), opt_indent))

            # these we handle at the end of generic option processing
            version_added = opt.pop('version_added', None)
            version_added_collection = opt.pop('version_added_collection', None)

            # general processing for options
            for k in sorted(opt):
                if k.startswith('_'):
                    continue

                if is_sequence(opt[k]):
                    text.append(DocCLI._indent_lines('%s: %s' % (k, DocCLI._dump_yaml(opt[k], flow_style=True)), opt_indent))
                else:
                    text.append(DocCLI._indent_lines(DocCLI._dump_yaml({k: opt[k]}), opt_indent))

            if version_added:
                text.append("%sadded in: %s\n" % (opt_indent, DocCLI._format_version_added(version_added, version_added_collection)))

            for subkey, subdata in suboptions:
                text.append('')
                text.append("%s%s:\n" % (opt_indent, subkey.upper()))
                DocCLI.add_fields(text, subdata, limit, opt_indent + '    ', return_values, opt_indent)
            if not suboptions:
                text.append('')

    def get_role_man_text(self, role, role_json):
        '''Generate text for the supplied role suitable for display.

        This is similar to get_man_text(), but roles are different enough that we have
        a separate method for formatting their display.

        :param role: The role name.
        :param role_json: The JSON for the given role as returned from _create_role_doc().

        :returns: A array of text suitable for displaying to screen.
        '''
        text = []
        opt_indent = "        "
        pad = display.columns * 0.20
        limit = max(display.columns - int(pad), 70)

        text.append("> %s    (%s)\n" % (role.upper(), role_json.get('path')))

        for entry_point in role_json['entry_points']:
            doc = role_json['entry_points'][entry_point]

            if doc.get('short_description'):
                text.append("ENTRY POINT: %s - %s\n" % (entry_point, doc.get('short_description')))
            else:
                text.append("ENTRY POINT: %s\n" % entry_point)

            if doc.get('description'):
                if isinstance(doc['description'], list):
                    desc = " ".join(doc['description'])
                else:
                    desc = doc['description']

                text.append("%s\n" % textwrap.fill(DocCLI.tty_ify(desc),
                                                   limit, initial_indent=opt_indent,
                                                   subsequent_indent=opt_indent))
            if doc.get('options'):
                text.append("OPTIONS (= is mandatory):\n")
                DocCLI.add_fields(text, doc.pop('options'), limit, opt_indent)
                text.append('')

            if doc.get('attributes'):
                text.append("ATTRIBUTES:\n")
                text.append(DocCLI._indent_lines(DocCLI._dump_yaml(doc.pop('attributes')), opt_indent))
                text.append('')

            # generic elements we will handle identically
            for k in ('author',):
                if k not in doc:
                    continue
                if isinstance(doc[k], string_types):
                    text.append('%s: %s' % (k.upper(), textwrap.fill(DocCLI.tty_ify(doc[k]),
                                            limit - (len(k) + 2), subsequent_indent=opt_indent)))
                elif isinstance(doc[k], (list, tuple)):
                    text.append('%s: %s' % (k.upper(), ', '.join(doc[k])))
                else:
                    # use empty indent since this affects the start of the yaml doc, not it's keys
                    text.append(DocCLI._indent_lines(DocCLI._dump_yaml({k.upper(): doc[k]}), ''))
                text.append('')

        return text

    @staticmethod
    def get_man_text(doc, collection_name='', plugin_type=''):
        # Create a copy so we don't modify the original
        doc = dict(doc)

        DocCLI.IGNORE = DocCLI.IGNORE + (context.CLIARGS['type'],)
        opt_indent = "        "
        text = []
        pad = display.columns * 0.20
        limit = max(display.columns - int(pad), 70)

        plugin_name = doc.get(context.CLIARGS['type'], doc.get('name')) or doc.get('plugin_type') or plugin_type
        if collection_name:
            plugin_name = '%s.%s' % (collection_name, plugin_name)

        text.append("> %s    (%s)\n" % (plugin_name.upper(), doc.pop('filename')))

        if isinstance(doc['description'], list):
            desc = " ".join(doc.pop('description'))
        else:
            desc = doc.pop('description')

        text.append("%s\n" % textwrap.fill(DocCLI.tty_ify(desc), limit, initial_indent=opt_indent,
                                           subsequent_indent=opt_indent))

        if 'version_added' in doc:
            version_added = doc.pop('version_added')
            version_added_collection = doc.pop('version_added_collection', None)
            text.append("ADDED IN: %s\n" % DocCLI._format_version_added(version_added, version_added_collection))

        if doc.get('deprecated', False):
            text.append("DEPRECATED: \n")
            if isinstance(doc['deprecated'], dict):
                if 'removed_at_date' in doc['deprecated']:
                    text.append(
                        "\tReason: %(why)s\n\tWill be removed in a release after %(removed_at_date)s\n\tAlternatives: %(alternative)s" % doc.pop('deprecated')
                    )
                else:
                    if 'version' in doc['deprecated'] and 'removed_in' not in doc['deprecated']:
                        doc['deprecated']['removed_in'] = doc['deprecated']['version']
                    text.append("\tReason: %(why)s\n\tWill be removed in: Ansible %(removed_in)s\n\tAlternatives: %(alternative)s" % doc.pop('deprecated'))
            else:
                text.append("%s" % doc.pop('deprecated'))
            text.append("\n")

        if doc.pop('has_action', False):
            text.append("  * note: %s\n" % "This module has a corresponding action plugin.")

        if doc.get('options', False):
            text.append("OPTIONS (= is mandatory):\n")
            DocCLI.add_fields(text, doc.pop('options'), limit, opt_indent)
            text.append('')

        if doc.get('attributes', False):
            text.append("ATTRIBUTES:\n")
            text.append(DocCLI._indent_lines(DocCLI._dump_yaml(doc.pop('attributes')), opt_indent))
            text.append('')

        if doc.get('notes', False):
            text.append("NOTES:")
            for note in doc['notes']:
                text.append(textwrap.fill(DocCLI.tty_ify(note), limit - 6,
                                          initial_indent=opt_indent[:-2] + "* ", subsequent_indent=opt_indent))
            text.append('')
            text.append('')
            del doc['notes']

        if doc.get('seealso', False):
            text.append("SEE ALSO:")
            for item in doc['seealso']:
                if 'module' in item:
                    text.append(textwrap.fill(DocCLI.tty_ify('Module %s' % item['module']),
                                limit - 6, initial_indent=opt_indent[:-2] + "* ", subsequent_indent=opt_indent))
                    description = item.get('description')
                    if description is None and item['module'].startswith('ansible.builtin.'):
                        description = 'The official documentation on the %s module.' % item['module']
                    if description is not None:
                        text.append(textwrap.fill(DocCLI.tty_ify(description),
                                    limit - 6, initial_indent=opt_indent + '   ', subsequent_indent=opt_indent + '   '))
                    if item['module'].startswith('ansible.builtin.'):
                        relative_url = 'collections/%s_module.html' % item['module'].replace('.', '/', 2)
                        text.append(textwrap.fill(DocCLI.tty_ify(get_versioned_doclink(relative_url)),
                                    limit - 6, initial_indent=opt_indent + '   ', subsequent_indent=opt_indent))
                elif 'name' in item and 'link' in item and 'description' in item:
                    text.append(textwrap.fill(DocCLI.tty_ify(item['name']),
                                limit - 6, initial_indent=opt_indent[:-2] + "* ", subsequent_indent=opt_indent))
                    text.append(textwrap.fill(DocCLI.tty_ify(item['description']),
                                limit - 6, initial_indent=opt_indent + '   ', subsequent_indent=opt_indent + '   '))
                    text.append(textwrap.fill(DocCLI.tty_ify(item['link']),
                                limit - 6, initial_indent=opt_indent + '   ', subsequent_indent=opt_indent + '   '))
                elif 'ref' in item and 'description' in item:
                    text.append(textwrap.fill(DocCLI.tty_ify('Ansible documentation [%s]' % item['ref']),
                                limit - 6, initial_indent=opt_indent[:-2] + "* ", subsequent_indent=opt_indent))
                    text.append(textwrap.fill(DocCLI.tty_ify(item['description']),
                                limit - 6, initial_indent=opt_indent + '   ', subsequent_indent=opt_indent + '   '))
                    text.append(textwrap.fill(DocCLI.tty_ify(get_versioned_doclink('/#stq=%s&stp=1' % item['ref'])),
                                limit - 6, initial_indent=opt_indent + '   ', subsequent_indent=opt_indent + '   '))

            text.append('')
            text.append('')
            del doc['seealso']

        if doc.get('requirements', False):
            req = ", ".join(doc.pop('requirements'))
            text.append("REQUIREMENTS:%s\n" % textwrap.fill(DocCLI.tty_ify(req), limit - 16, initial_indent="  ", subsequent_indent=opt_indent))

        # Generic handler
        for k in sorted(doc):
            if k in DocCLI.IGNORE or not doc[k]:
                continue
            if isinstance(doc[k], string_types):
                text.append('%s: %s' % (k.upper(), textwrap.fill(DocCLI.tty_ify(doc[k]), limit - (len(k) + 2), subsequent_indent=opt_indent)))
            elif isinstance(doc[k], (list, tuple)):
                text.append('%s: %s' % (k.upper(), ', '.join(doc[k])))
            else:
                # use empty indent since this affects the start of the yaml doc, not it's keys
                text.append(DocCLI._indent_lines(DocCLI._dump_yaml({k.upper(): doc[k]}), ''))
            del doc[k]
            text.append('')

        if doc.get('plainexamples', False):
            text.append("EXAMPLES:")
            text.append('')
            if isinstance(doc['plainexamples'], string_types):
                text.append(doc.pop('plainexamples').strip())
            else:
                try:
                    text.append(yaml_dump(doc.pop('plainexamples'), indent=2, default_flow_style=False))
                except Exception as e:
                    raise AnsibleParserError("Unable to parse examples section", orig_exc=e)
            text.append('')
            text.append('')

        if doc.get('returndocs', False):
            text.append("RETURN VALUES:")
            DocCLI.add_fields(text, doc.pop('returndocs'), limit, opt_indent, return_values=True)

        return "\n".join(text)


def _do_yaml_snippet(doc):
    text = []

    mdesc = DocCLI.tty_ify(doc['short_description'])
    module = doc.get('module')

    if module:
        # this is actually a usable task!
        text.append("- name: %s" % (mdesc))
        text.append("  %s:" % (module))
    else:
        # just a comment, hopefully useful yaml file
        text.append("# %s:" % doc.get('plugin', doc.get('name')))

    pad = 29
    subdent = '# '.rjust(pad + 2)
    limit = display.columns - pad

    for o in sorted(doc['options'].keys()):
        opt = doc['options'][o]
        if isinstance(opt['description'], string_types):
            desc = DocCLI.tty_ify(opt['description'])
        else:
            desc = DocCLI.tty_ify(" ".join(opt['description']))

        required = opt.get('required', False)
        if not isinstance(required, bool):
            raise ValueError("Incorrect value for 'Required', a boolean is needed: %s" % required)

        o = '%s:' % o
        if module:
            if required:
                desc = "(required) %s" % desc
            text.append("      %-20s   # %s" % (o, textwrap.fill(desc, limit, subsequent_indent=subdent)))
        else:
            if required:
                default = '(required)'
            else:
                default = opt.get('default', 'None')

            text.append("%s %-9s # %s" % (o, default, textwrap.fill(desc, limit, subsequent_indent=subdent, max_lines=3)))

    return text


def _do_lookup_snippet(doc):
    text = []
    snippet = "lookup('%s', " % doc.get('plugin', doc.get('name'))
    comment = []

    for o in sorted(doc['options'].keys()):

        opt = doc['options'][o]
        comment.append('# %s(%s): %s' % (o, opt.get('type', 'string'), opt.get('description', '')))
        if o in ('_terms', '_raw', '_list'):
            # these are 'list of arguments'
            snippet += '< %s >' % (o)
            continue

        required = opt.get('required', False)
        if not isinstance(required, bool):
            raise ValueError("Incorrect value for 'Required', a boolean is needed: %s" % required)

        if required:
            default = '<REQUIRED>'
        else:
            default = opt.get('default', 'None')

        if opt.get('type') in ('string', 'str'):
            snippet += ", %s='%s'" % (o, default)
        else:
            snippet += ', %s=%s' % (o, default)

    snippet += ")"

    if comment:
        text.extend(comment)
        text.append('')
    text.append(snippet)

    return text


def main(args=None):
    DocCLI.cli_executor(args)


if __name__ == '__main__':
    main()
