# Copyright: (c) 2014, James Tanner <tanner.jc@gmail.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import datetime
import json
import os
import re
import textwrap
import traceback
import yaml

import ansible.plugins.loader as plugin_loader

from ansible import constants as C
from ansible import context
from ansible.cli import CLI
from ansible.cli.arguments import option_helpers as opt_help
from ansible.collections.list import list_collection_dirs
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.common._collections_compat import Container, Sequence
from ansible.module_utils.common.json import AnsibleJSONEncoder
from ansible.module_utils.six import string_types
from ansible.parsing.plugin_docs import read_docstub
from ansible.parsing.yaml.dumper import AnsibleDumper
from ansible.plugins.loader import action_loader, fragment_loader
from ansible.utils.collection_loader import AnsibleCollectionConfig
from ansible.utils.collection_loader._collection_finder import _get_collection_name_from_path
from ansible.utils.display import Display
from ansible.utils.plugin_docs import (
    BLACKLIST,
    remove_current_collection_from_versions_and_dates,
    get_docstring,
    get_versioned_doclink,
)

display = Display()


def jdump(text):
    try:
        display.display(json.dumps(text, cls=AnsibleJSONEncoder, sort_keys=True, indent=4))
    except TypeError as e:
        raise AnsibleError('We could not convert all the documentation into JSON as there was a conversion issue: %s' % to_native(e))


def add_collection_plugins(plugin_list, plugin_type, coll_filter=None):

    # TODO: take into account runtime.yml once implemented
    b_colldirs = list_collection_dirs(coll_filter=coll_filter)
    for b_path in b_colldirs:
        path = to_text(b_path, errors='surrogate_or_strict')
        collname = _get_collection_name_from_path(b_path)
        ptype = C.COLLECTION_PTYPE_COMPAT.get(plugin_type, plugin_type)
        plugin_list.update(DocCLI.find_plugins(os.path.join(path, 'plugins', ptype), False, plugin_type, collection=collname))


class PluginNotFound(Exception):
    pass


class DocCLI(CLI):
    ''' displays information on modules installed in Ansible libraries.
        It displays a terse listing of plugins and their short descriptions,
        provides a printout of their DOCUMENTATION strings,
        and it can create a short "snippet" which can be pasted into a playbook.  '''

    # default ignore list for detailed views
    IGNORE = ('module', 'docuri', 'version_added', 'short_description', 'now_date', 'plainexamples', 'returndocs', 'collection')

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

    def __init__(self, args):

        super(DocCLI, self).__init__(args)
        self.plugin_list = set()

    @classmethod
    def tty_ify(cls, text):

        t = cls._ITALIC.sub(r"`\1'", text)    # I(word) => `word'
        t = cls._BOLD.sub(r"*\1*", t)         # B(word) => *word*
        t = cls._MODULE.sub("[" + r"\1" + "]", t)       # M(word) => [word]
        t = cls._URL.sub(r"\1", t)                      # U(word) => word
        t = cls._LINK.sub(r"\1 <\2>", t)                # L(word, url) => word <url>
        t = cls._REF.sub(r"\1", t)                      # R(word, sphinx-ref) => word
        t = cls._CONST.sub("`" + r"\1" + "'", t)        # C(word) => `word'
        t = cls._RULER.sub("\n{0}\n".format("-" * 13), t)   # HORIZONTALLINE => -------

        return t

    def init_parser(self):

        coll_filter = 'A supplied argument will be used for filtering, can be a namespace or full collection name.'

        super(DocCLI, self).init_parser(
            desc="plugin documentation tool",
            epilog="See man pages for Ansible CLI options or website for tutorials https://docs.ansible.com"
        )
        opt_help.add_module_options(self.parser)
        opt_help.add_basedir_options(self.parser)

        self.parser.add_argument('args', nargs='*', help='Plugin', metavar='plugin')
        self.parser.add_argument("-t", "--type", action="store", default='module', dest='type',
                                 help='Choose which plugin type (defaults to "module"). '
                                      'Available plugin types are : {0}'.format(C.DOCUMENTABLE_PLUGINS),
                                 choices=C.DOCUMENTABLE_PLUGINS)
        self.parser.add_argument("-j", "--json", action="store_true", default=False, dest='json_format',
                                 help='Change output into json format.')

        exclusive = self.parser.add_mutually_exclusive_group()
        exclusive.add_argument("-F", "--list_files", action="store_true", default=False, dest="list_files",
                               help='Show plugin names and their source files without summaries (implies --list). %s' % coll_filter)
        exclusive.add_argument("-l", "--list", action="store_true", default=False, dest='list_dir',
                               help='List available plugins. %s' % coll_filter)
        exclusive.add_argument("-s", "--snippet", action="store_true", default=False, dest='show_snippet',
                               help='Show playbook snippet for specified plugin(s)')
        exclusive.add_argument("--metadata-dump", action="store_true", default=False, dest='dump',
                               help='**For internal testing only** Dump json metadata for all plugins.')

    def post_process_args(self, options):
        options = super(DocCLI, self).post_process_args(options)

        display.verbosity = options.verbosity

        return options

    def display_plugin_list(self, results):

        # format for user
        displace = max(len(x) for x in self.plugin_list)
        linelimit = display.columns - displace - 5
        text = []

        # format display per option
        if context.CLIARGS['list_files']:
            # list plugin file names
            for plugin in results.keys():
                filename = results[plugin]
                text.append("%-*s %-*.*s" % (displace, plugin, linelimit, len(filename), filename))
        else:
            # list plugin names and short desc
            deprecated = []
            for plugin in results.keys():
                desc = DocCLI.tty_ify(results[plugin])

                if len(desc) > linelimit:
                    desc = desc[:linelimit] + '...'

                if plugin.startswith('_'):  # Handle deprecated # TODO: add mark for deprecated collection plugins
                    deprecated.append("%-*s %-*.*s" % (displace, plugin[1:], linelimit, len(desc), desc))
                else:
                    text.append("%-*s %-*.*s" % (displace, plugin, linelimit, len(desc), desc))

                if len(deprecated) > 0:
                    text.append("\nDEPRECATED:")
                    text.extend(deprecated)

        # display results
        DocCLI.pager("\n".join(text))

    def run(self):

        super(DocCLI, self).run()

        plugin_type = context.CLIARGS['type']
        do_json = context.CLIARGS['json_format']

        if plugin_type in C.DOCUMENTABLE_PLUGINS:
            loader = getattr(plugin_loader, '%s_loader' % plugin_type)
        else:
            raise AnsibleOptionsError("Unknown or undocumentable plugin type: %s" % plugin_type)

        # add to plugin paths from command line
        basedir = context.CLIARGS['basedir']
        if basedir:
            AnsibleCollectionConfig.playbook_paths = basedir
            loader.add_directory(basedir, with_subdir=True)

        if context.CLIARGS['module_path']:
            for path in context.CLIARGS['module_path']:
                if path:
                    loader.add_directory(path)

        # save only top level paths for errors
        search_paths = DocCLI.print_paths(loader)
        loader._paths = None  # reset so we can use subdirs below

        # list plugins names or filepath for type, both options share most code
        if context.CLIARGS['list_files'] or context.CLIARGS['list_dir']:

            coll_filter = None
            if len(context.CLIARGS['args']) == 1:
                coll_filter = context.CLIARGS['args'][0]

            if coll_filter in ('', None):
                paths = loader._get_paths_with_context()
                for path_context in paths:
                    self.plugin_list.update(
                        DocCLI.find_plugins(path_context.path, path_context.internal, plugin_type))

            add_collection_plugins(self.plugin_list, plugin_type, coll_filter=coll_filter)

            # get appropriate content depending on option
            if context.CLIARGS['list_dir']:
                results = self._get_plugin_list_descriptions(loader)
            elif context.CLIARGS['list_files']:
                results = self._get_plugin_list_filenames(loader)

            if do_json:
                jdump(results)
            elif self.plugin_list:
                self.display_plugin_list(results)
            else:
                display.warning("No plugins found.")
        # dump plugin desc/data as JSON
        elif context.CLIARGS['dump']:
            plugin_data = {}
            plugin_names = DocCLI.get_all_plugins_of_type(plugin_type)
            for plugin_name in plugin_names:
                plugin_info = DocCLI.get_plugin_metadata(plugin_type, plugin_name)
                if plugin_info is not None:
                    plugin_data[plugin_name] = plugin_info

            jdump(plugin_data)
        else:
            # display specific plugin docs
            if len(context.CLIARGS['args']) == 0:
                raise AnsibleOptionsError("Incorrect options passed")

            # get the docs for plugins in the command line list
            plugin_docs = {}
            for plugin in context.CLIARGS['args']:
                try:
                    doc, plainexamples, returndocs, metadata = DocCLI._get_plugin_doc(plugin, plugin_type, loader, search_paths)
                except PluginNotFound:
                    display.warning("%s %s not found in:\n%s\n" % (plugin_type, plugin, search_paths))
                    continue
                except Exception as e:
                    display.vvv(traceback.format_exc())
                    raise AnsibleError("%s %s missing documentation (or could not parse"
                                       " documentation): %s\n" %
                                       (plugin_type, plugin, to_native(e)))

                if not doc:
                    # The doc section existed but was empty
                    continue

                plugin_docs[plugin] = DocCLI._combine_plugin_doc(plugin, plugin_type, doc, plainexamples, returndocs, metadata)

            if do_json:
                jdump(plugin_docs)

            else:
                # Some changes to how plain text docs are formatted
                text = []
                for plugin, doc_data in plugin_docs.items():
                    textret = DocCLI.format_plugin_doc(plugin, plugin_type,
                                                       doc_data['doc'], doc_data['examples'],
                                                       doc_data['return'], doc_data['metadata'])
                    if textret:
                        text.append(textret)
                    else:
                        display.warning("No valid documentation was retrieved from '%s'" % plugin)

                if text:
                    DocCLI.pager(''.join(text))

        return 0

    @staticmethod
    def get_all_plugins_of_type(plugin_type):
        loader = getattr(plugin_loader, '%s_loader' % plugin_type)
        plugin_list = set()
        paths = loader._get_paths_with_context()
        for path_context in paths:
            plugins_to_add = DocCLI.find_plugins(path_context.path, path_context.internal, plugin_type)
            plugin_list.update(plugins_to_add)
        return sorted(set(plugin_list))

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
                                            collection_name=collection_name, is_module=(plugin_type == 'module'))
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
    def _get_plugin_doc(plugin, plugin_type, loader, search_paths):
        # if the plugin lives in a non-python file (eg, win_X.ps1), require the corresponding python file for docs
        result = loader.find_plugin_with_context(plugin, mod_type='.py', ignore_deprecated=True, check_aliases=True)
        if not result.resolved:
            raise PluginNotFound('%s was not found in %s' % (plugin, search_paths))
        plugin_name = result.plugin_resolved_name
        filename = result.plugin_resolved_path
        collection_name = result.plugin_resolved_collection

        doc, plainexamples, returndocs, metadata = get_docstring(
            filename, fragment_loader, verbose=(context.CLIARGS['verbosity'] > 0),
            collection_name=collection_name, is_module=(plugin_type == 'module'))

        # If the plugin existed but did not have a DOCUMENTATION element and was not removed, it's an error
        if doc is None:
            raise ValueError('%s did not contain a DOCUMENTATION attribute' % plugin)

        doc['filename'] = filename
        doc['collection'] = collection_name
        return doc, plainexamples, returndocs, metadata

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

        if context.CLIARGS['show_snippet'] and plugin_type == 'module':
            text = DocCLI.get_snippet_text(doc)
        else:
            try:
                text = DocCLI.get_man_text(doc, collection_name, plugin_type)
            except Exception as e:
                raise AnsibleError("Unable to retrieve documentation from '%s' due to: %s" % (plugin, to_native(e)))

        return text

    @staticmethod
    def find_plugins(path, internal, ptype, collection=None):
        # if internal, collection could be set to `ansible.builtin`

        display.vvvv("Searching %s for plugins" % path)

        plugin_list = set()

        if not os.path.exists(path):
            display.vvvv("%s does not exist" % path)
            return plugin_list

        if not os.path.isdir(path):
            display.vvvv("%s is not a directory" % path)
            return plugin_list

        bkey = ptype.upper()
        for plugin in os.listdir(path):
            display.vvvv("Found %s" % plugin)
            full_path = '/'.join([path, plugin])

            if plugin.startswith('.'):
                continue
            elif os.path.isdir(full_path):
                continue
            elif any(plugin.endswith(x) for x in C.BLACKLIST_EXTS):
                continue
            elif plugin.startswith('__'):
                continue
            elif plugin in C.IGNORE_FILES:
                continue
            elif plugin .startswith('_'):
                if os.path.islink(full_path):  # avoids aliases
                    continue

            plugin = os.path.splitext(plugin)[0]  # removes the extension
            plugin = plugin.lstrip('_')  # remove underscore from deprecated plugins

            if plugin not in BLACKLIST.get(bkey, ()):

                if collection:
                    plugin = '%s.%s' % (collection, plugin)

                plugin_list.add(plugin)
                display.vvvv("Added %s" % plugin)

        return plugin_list

    def _get_plugin_list_descriptions(self, loader):

        descs = {}
        plugins = self._get_plugin_list_filenames(loader)
        for plugin in plugins.keys():

            filename = plugins[plugin]

            doc = None
            try:
                doc = read_docstub(filename)
            except Exception:
                display.warning("%s has a documentation formatting error" % plugin)
                continue

            if not doc or not isinstance(doc, dict):
                desc = 'UNDOCUMENTED'
            else:
                desc = doc.get('short_description', 'INVALID SHORT DESCRIPTION').strip()

            descs[plugin] = desc

        return descs

    def _get_plugin_list_filenames(self, loader):
        pfiles = {}
        for plugin in sorted(self.plugin_list):

            try:
                # if the module lives in a non-python file (eg, win_X.ps1), require the corresponding python file for docs
                filename = loader.find_plugin(plugin, mod_type='.py', ignore_deprecated=True, check_aliases=True)

                if filename is None:
                    continue
                if filename.endswith(".ps1"):
                    continue
                if os.path.isdir(filename):
                    continue

                pfiles[plugin] = filename

            except Exception as e:
                raise AnsibleError("Failed reading docs at %s: %s" % (plugin, to_native(e)), orig_exc=e)

        return pfiles

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
    def get_snippet_text(doc):

        text = []
        desc = DocCLI.tty_ify(doc['short_description'])
        text.append("- name: %s" % (desc))
        text.append("  %s:" % (doc['module']))
        pad = 31
        subdent = " " * pad
        limit = display.columns - pad

        for o in sorted(doc['options'].keys()):
            opt = doc['options'][o]
            if isinstance(opt['description'], string_types):
                desc = DocCLI.tty_ify(opt['description'])
            else:
                desc = DocCLI.tty_ify(" ".join(opt['description']))

            required = opt.get('required', False)
            if not isinstance(required, bool):
                raise("Incorrect value for 'Required', a boolean is needed.: %s" % required)
            if required:
                desc = "(required) %s" % desc
            o = '%s:' % o
            text.append("      %-20s   # %s" % (o, textwrap.fill(desc, limit, subsequent_indent=subdent)))
        text.append('')

        return "\n".join(text)

    @staticmethod
    def _dump_yaml(struct, indent):
        return DocCLI.tty_ify('\n'.join([indent + line for line in
                                         yaml.dump(struct, default_flow_style=False,
                                                   Dumper=AnsibleDumper).split('\n')]))

    @staticmethod
    def add_fields(text, fields, limit, opt_indent, return_values=False, base_indent=''):

        for o in sorted(fields):
            # Create a copy so we don't modify the original (in case YAML anchors have been used)
            opt = dict(fields[o])

            required = opt.pop('required', False)
            if not isinstance(required, bool):
                raise AnsibleError("Incorrect value for 'Required', a boolean is needed.: %s" % required)
            if required:
                opt_leadin = "="
            else:
                opt_leadin = "-"

            text.append("%s%s %s" % (base_indent, opt_leadin, o))

            if 'description' not in opt:
                raise AnsibleError("All (sub-)options and return values must have a 'description' field")
            if isinstance(opt['description'], list):
                for entry_idx, entry in enumerate(opt['description'], 1):
                    if not isinstance(entry, string_types):
                        raise AnsibleError("Expected string in description of %s at index %s, got %s" % (o, entry_idx, type(entry)))
                    text.append(textwrap.fill(DocCLI.tty_ify(entry), limit, initial_indent=opt_indent, subsequent_indent=opt_indent))
            else:
                if not isinstance(opt['description'], string_types):
                    raise AnsibleError("Expected string in description of %s, got %s" % (o, type(opt['description'])))
                text.append(textwrap.fill(DocCLI.tty_ify(opt['description']), limit, initial_indent=opt_indent, subsequent_indent=opt_indent))
            del opt['description']

            aliases = ''
            if 'aliases' in opt:
                if len(opt['aliases']) > 0:
                    aliases = "(Aliases: " + ", ".join(to_text(i) for i in opt['aliases']) + ")"
                del opt['aliases']
            choices = ''
            if 'choices' in opt:
                if len(opt['choices']) > 0:
                    choices = "(Choices: " + ", ".join(to_text(i) for i in opt['choices']) + ")"
                del opt['choices']
            default = ''
            if not return_values:
                if 'default' in opt or not required:
                    default = "[Default: %s" % to_text(opt.pop('default', '(null)')) + "]"

            text.append(textwrap.fill(DocCLI.tty_ify(aliases + choices + default), limit,
                                      initial_indent=opt_indent, subsequent_indent=opt_indent))

            suboptions = []
            for subkey in ('options', 'suboptions', 'contains', 'spec'):
                if subkey in opt:
                    suboptions.append((subkey, opt.pop(subkey)))

            conf = {}
            for config in ('env', 'ini', 'yaml', 'vars', 'keywords'):
                if config in opt and opt[config]:
                    # Create a copy so we don't modify the original (in case YAML anchors have been used)
                    conf[config] = [dict(item) for item in opt.pop(config)]
                    for ignore in DocCLI.IGNORE:
                        for item in conf[config]:
                            if ignore in item:
                                del item[ignore]

            if conf:
                text.append(DocCLI._dump_yaml({'set_via': conf}, opt_indent))

            for k in sorted(opt):
                if k.startswith('_'):
                    continue
                if isinstance(opt[k], string_types):
                    text.append('%s%s: %s' % (opt_indent, k,
                                              textwrap.fill(DocCLI.tty_ify(opt[k]),
                                                            limit - (len(k) + 2),
                                                            subsequent_indent=opt_indent)))
                elif isinstance(opt[k], (Sequence)) and all(isinstance(x, string_types) for x in opt[k]):
                    text.append(DocCLI.tty_ify('%s%s: %s' % (opt_indent, k, ', '.join(opt[k]))))
                else:
                    text.append(DocCLI._dump_yaml({k: opt[k]}, opt_indent))

            for subkey, subdata in suboptions:
                text.append('')
                text.append("%s%s:\n" % (opt_indent, subkey.upper()))
                DocCLI.add_fields(text, subdata, limit, opt_indent + '    ', return_values, opt_indent)
            if not suboptions:
                text.append('')

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
                    description = item.get('description', 'The official documentation on the %s module.' % item['module'])
                    text.append(textwrap.fill(DocCLI.tty_ify(description), limit - 6, initial_indent=opt_indent + '   ', subsequent_indent=opt_indent + '   '))
                    text.append(textwrap.fill(DocCLI.tty_ify(get_versioned_doclink('modules/%s_module.html' % item['module'])),
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
                text.append(DocCLI._dump_yaml({k.upper(): doc[k]}, ''))
            del doc[k]
            text.append('')

        if doc.get('plainexamples', False):
            text.append("EXAMPLES:")
            text.append('')
            if isinstance(doc['plainexamples'], string_types):
                text.append(doc.pop('plainexamples').strip())
            else:
                text.append(yaml.dump(doc.pop('plainexamples'), indent=2, default_flow_style=False))
            text.append('')
            text.append('')

        if doc.get('returndocs', False):
            text.append("RETURN VALUES:")
            DocCLI.add_fields(text, doc.pop('returndocs'), limit, opt_indent, return_values=True)

        return "\n".join(text)
