# Copyright: (c) 2014, James Tanner <tanner.jc@gmail.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import datetime
import json
import os
import textwrap
import traceback
import yaml

import ansible.plugins.loader as plugin_loader

from ansible import constants as C
from ansible import context
from ansible.cli import CLI
from ansible.cli.arguments import option_helpers as opt_help
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.module_utils._text import to_native
from ansible.module_utils.common._collections_compat import Container, Sequence
from ansible.module_utils.six import string_types
from ansible.parsing.metadata import extract_metadata
from ansible.parsing.plugin_docs import read_docstub
from ansible.parsing.yaml.dumper import AnsibleDumper
from ansible.plugins.loader import action_loader, fragment_loader
from ansible.utils.collection_loader import set_collection_playbook_paths
from ansible.utils.display import Display
from ansible.utils.plugin_docs import BLACKLIST, get_docstring, get_versioned_doclink
display = Display()


def jdump(text):
    display.display(json.dumps(text, sort_keys=True, indent=4))


class RemovedPlugin(Exception):
    pass


class PluginNotFound(Exception):
    pass


class DocCLI(CLI):
    ''' displays information on modules installed in Ansible libraries.
        It displays a terse listing of plugins and their short descriptions,
        provides a printout of their DOCUMENTATION strings,
        and it can create a short "snippet" which can be pasted into a playbook.  '''

    # default ignore list for detailed views
    IGNORE = ('module', 'docuri', 'version_added', 'short_description', 'now_date', 'plainexamples', 'returndocs')

    def __init__(self, args):

        super(DocCLI, self).__init__(args)
        self.plugin_list = set()

    def init_parser(self):

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
                               help='Show plugin names and their source files without summaries (implies --list)')
        exclusive.add_argument("-l", "--list", action="store_true", default=False, dest='list_dir',
                               help='List available plugins')
        exclusive.add_argument("-s", "--snippet", action="store_true", default=False, dest='show_snippet',
                               help='Show playbook snippet for specified plugin(s)')
        exclusive.add_argument("--metadata-dump", action="store_true", default=False, dest='dump',
                               help='**For internal testing only** Dump json metadata for all plugins.')

    def post_process_args(self, options):
        options = super(DocCLI, self).post_process_args(options)

        display.verbosity = options.verbosity

        return options

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
            set_collection_playbook_paths(basedir)
            loader.add_directory(basedir, with_subdir=True)
        if context.CLIARGS['module_path']:
            for path in context.CLIARGS['module_path']:
                if path:
                    loader.add_directory(path)

        # save only top level paths for errors
        search_paths = DocCLI.print_paths(loader)
        loader._paths = None  # reset so we can use subdirs below

        # list plugins names and filepath for type
        if context.CLIARGS['list_files']:
            paths = loader._get_paths()
            for path in paths:
                self.plugin_list.update(DocCLI.find_plugins(path, plugin_type))

            plugins = self._get_plugin_list_filenames(loader)
            if do_json:
                jdump(plugins)
            else:
                # format for user
                displace = max(len(x) for x in self.plugin_list)
                linelimit = display.columns - displace - 5
                text = []

                for plugin in plugins.keys():
                    filename = plugins[plugin]
                    text.append("%-*s %-*.*s" % (displace, plugin, linelimit, len(filename), filename))

                DocCLI.pager("\n".join(text))

        # list file plugins for type (does not read docs, very fast)
        elif context.CLIARGS['list_dir']:
            paths = loader._get_paths()
            for path in paths:
                self.plugin_list.update(DocCLI.find_plugins(path, plugin_type))

            descs = self._get_plugin_list_descriptions(loader)
            if do_json:
                jdump(descs)
            else:
                displace = max(len(x) for x in self.plugin_list)
                linelimit = display.columns - displace - 5
                text = []
                deprecated = []
                for plugin in descs.keys():

                    desc = DocCLI.tty_ify(descs[plugin])

                    if len(desc) > linelimit:
                        desc = desc[:linelimit] + '...'

                    if plugin.startswith('_'):  # Handle deprecated
                        deprecated.append("%-*s %-*.*s" % (displace, plugin[1:], linelimit, len(desc), desc))
                    else:
                        text.append("%-*s %-*.*s" % (displace, plugin, linelimit, len(desc), desc))

                    if len(deprecated) > 0:
                        text.append("\nDEPRECATED:")
                        text.extend(deprecated)

                DocCLI.pager("\n".join(text))

        # dump plugin desc/metadata as JSON
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
                    doc, plainexamples, returndocs, metadata = DocCLI._get_plugin_doc(plugin, loader, search_paths)
                except PluginNotFound:
                    display.warning("%s %s not found in:\n%s\n" % (plugin_type, plugin, search_paths))
                    continue
                except RemovedPlugin:
                    display.warning("%s %s has been removed\n" % (plugin_type, plugin))
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
                # Some changes to how json docs are formatted
                for plugin, doc_data in plugin_docs.items():
                    try:
                        doc_data['return'] = yaml.load(doc_data['return'])
                    except Exception:
                        pass

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

                if text:
                    DocCLI.pager(''.join(text))

        return 0

    @staticmethod
    def get_all_plugins_of_type(plugin_type):
        loader = getattr(plugin_loader, '%s_loader' % plugin_type)
        plugin_list = set()
        paths = loader._get_paths()
        for path in paths:
            plugins_to_add = DocCLI.find_plugins(path, plugin_type)
            plugin_list.update(plugins_to_add)
        return sorted(set(plugin_list))

    @staticmethod
    def get_plugin_metadata(plugin_type, plugin_name):
        # if the plugin lives in a non-python file (eg, win_X.ps1), require the corresponding python file for docs
        loader = getattr(plugin_loader, '%s_loader' % plugin_type)
        filename = loader.find_plugin(plugin_name, mod_type='.py', ignore_deprecated=True, check_aliases=True)
        if filename is None:
            raise AnsibleError("unable to load {0} plugin named {1} ".format(plugin_type, plugin_name))

        try:
            doc, __, __, metadata = get_docstring(filename, fragment_loader, verbose=(context.CLIARGS['verbosity'] > 0))
        except Exception:
            display.vvv(traceback.format_exc())
            raise AnsibleError(
                "%s %s at %s has a documentation error formatting or is missing documentation." %
                (plugin_type, plugin_name, filename))

        if doc is None:
            if 'removed' not in metadata.get('status', []):
                raise AnsibleError(
                    "%s %s at %s has a documentation error formatting or is missing documentation." %
                    (plugin_type, plugin_name, filename))

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
    def _get_plugin_doc(plugin, loader, search_paths):
        # if the plugin lives in a non-python file (eg, win_X.ps1), require the corresponding python file for docs
        filename = loader.find_plugin(plugin, mod_type='.py', ignore_deprecated=True, check_aliases=True)
        if filename is None:
            raise PluginNotFound('%s was not found in %s' % (plugin, search_paths))

        doc, plainexamples, returndocs, metadata = get_docstring(filename, fragment_loader, verbose=(context.CLIARGS['verbosity'] > 0))

        # If the plugin existed but did not have a DOCUMENTATION element and was not removed, it's
        # an error
        if doc is None:
            # doc may be None when the module has been removed.  Calling code may choose to
            # handle that but we can't.
            if 'status' in metadata and isinstance(metadata['status'], Container):
                if 'removed' in metadata['status']:
                    raise RemovedPlugin('%s has been removed' % plugin)

                # Backwards compat: no documentation but valid metadata (or no metadata, which results in using the default metadata).
                # Probably should make this an error in 2.10
                return {}, {}, {}, metadata
            else:
                # If metadata is invalid, warn but don't error
                display.warning(u'%s has an invalid ANSIBLE_METADATA field' % plugin)

            raise ValueError('%s did not contain a DOCUMENTATION attribute' % plugin)

        doc['filename'] = filename
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
        # assign from other sections
        doc['plainexamples'] = plainexamples
        doc['returndocs'] = returndocs
        doc['metadata'] = metadata

        if context.CLIARGS['show_snippet'] and plugin_type == 'module':
            text = DocCLI.get_snippet_text(doc)
        else:
            text = DocCLI.get_man_text(doc, plugin_type=plugin_type)

        return text

    @staticmethod
    def find_plugins(path, ptype):

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
                with open(filename) as f:
                    metadata = extract_metadata(module_data=f.read())
                if metadata[0]:
                    if 'removed' not in metadata[0].get('status', []):
                        display.warning("%s parsing did not produce documentation." % plugin)
                    else:
                        continue
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
    def add_fields(text, fields, limit, opt_indent):

        for o in sorted(fields):
            opt = fields[o]

            required = opt.pop('required', False)
            if not isinstance(required, bool):
                raise AnsibleError("Incorrect value for 'Required', a boolean is needed.: %s" % required)
            if required:
                opt_leadin = "="
            else:
                opt_leadin = "-"

            text.append("%s %s" % (opt_leadin, o))

            if isinstance(opt['description'], list):
                for entry in opt['description']:
                    text.append(textwrap.fill(DocCLI.tty_ify(entry), limit, initial_indent=opt_indent, subsequent_indent=opt_indent))
            else:
                text.append(textwrap.fill(DocCLI.tty_ify(opt['description']), limit, initial_indent=opt_indent, subsequent_indent=opt_indent))
            del opt['description']

            aliases = ''
            if 'aliases' in opt:
                if len(opt['aliases']) > 0:
                    aliases = "(Aliases: " + ", ".join(str(i) for i in opt['aliases']) + ")"
                del opt['aliases']
            choices = ''
            if 'choices' in opt:
                if len(opt['choices']) > 0:
                    choices = "(Choices: " + ", ".join(str(i) for i in opt['choices']) + ")"
                del opt['choices']
            default = ''
            if 'default' in opt or not required:
                default = "[Default: %s" % str(opt.pop('default', '(null)')) + "]"

            text.append(textwrap.fill(DocCLI.tty_ify(aliases + choices + default), limit,
                                      initial_indent=opt_indent, subsequent_indent=opt_indent))

            if 'options' in opt:
                text.append("%soptions:\n" % opt_indent)
                DocCLI.add_fields(text, opt.pop('options'), limit, opt_indent + opt_indent)

            if 'spec' in opt:
                text.append("%sspec:\n" % opt_indent)
                DocCLI.add_fields(text, opt.pop('spec'), limit, opt_indent + opt_indent)

            conf = {}
            for config in ('env', 'ini', 'yaml', 'vars', 'keywords'):
                if config in opt and opt[config]:
                    conf[config] = opt.pop(config)
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
            text.append('')

    @staticmethod
    def get_support_block(doc):
        # Note: 'curated' is deprecated and not used in any of the modules we ship
        support_level_msg = {'core': 'The Ansible Core Team',
                             'network': 'The Ansible Network Team',
                             'certified': 'an Ansible Partner',
                             'community': 'The Ansible Community',
                             'curated': 'A Third Party',
                             }
        return ["  * This module is maintained by %s" % support_level_msg[doc['metadata']['supported_by']]]

    @staticmethod
    def get_metadata_block(doc):
        text = []

        text.append("METADATA:")
        text.append('\tSUPPORT LEVEL: %s' % doc['metadata']['supported_by'])

        for k in (m for m in doc['metadata'] if m != 'supported_by'):
            if isinstance(k, list):
                text.append("\t%s: %s" % (k.capitalize(), ", ".join(doc['metadata'][k])))
            else:
                text.append("\t%s: %s" % (k.capitalize(), doc['metadata'][k]))
        return text

    @staticmethod
    def get_man_text(doc, plugin_type=None):

        DocCLI.IGNORE = DocCLI.IGNORE + (context.CLIARGS['type'],)
        opt_indent = "        "
        text = []
        pad = display.columns * 0.20
        limit = max(display.columns - int(pad), 70)

        plugin_name = doc.get(context.CLIARGS['type'], doc.get('name')) or doc.get('plugin_type') or plugin_type
        text.append("> %s    (%s)\n" % (plugin_name.upper(), doc.pop('filename')))

        if isinstance(doc['description'], list):
            desc = " ".join(doc.pop('description'))
        else:
            desc = doc.pop('description')

        text.append("%s\n" % textwrap.fill(DocCLI.tty_ify(desc), limit, initial_indent=opt_indent,
                                           subsequent_indent=opt_indent))

        if 'deprecated' in doc and doc['deprecated'] is not None and len(doc['deprecated']) > 0:
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

        try:
            support_block = DocCLI.get_support_block(doc)
            if support_block:
                text.extend(support_block)
        except Exception:
            pass  # FIXME: not suported by plugins

        if doc.pop('has_action', False):
            text.append("  * note: %s\n" % "This module has a corresponding action plugin.")

        if 'options' in doc and doc['options']:
            text.append("OPTIONS (= is mandatory):\n")
            DocCLI.add_fields(text, doc.pop('options'), limit, opt_indent)
            text.append('')

        if 'notes' in doc and doc['notes'] and len(doc['notes']) > 0:
            text.append("NOTES:")
            for note in doc['notes']:
                text.append(textwrap.fill(DocCLI.tty_ify(note), limit - 6,
                                          initial_indent=opt_indent[:-2] + "* ", subsequent_indent=opt_indent))
            text.append('')
            text.append('')
            del doc['notes']

        if 'seealso' in doc and doc['seealso']:
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

        if 'requirements' in doc and doc['requirements'] is not None and len(doc['requirements']) > 0:
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
                text.append(DocCLI._dump_yaml({k.upper(): doc[k]}, opt_indent))
            del doc[k]
        text.append('')

        if 'plainexamples' in doc and doc['plainexamples'] is not None:
            text.append("EXAMPLES:")
            text.append('')
            if isinstance(doc['plainexamples'], string_types):
                text.append(doc.pop('plainexamples').strip())
            else:
                text.append(yaml.dump(doc.pop('plainexamples'), indent=2, default_flow_style=False))
            text.append('')
            text.append('')

        if 'returndocs' in doc and doc['returndocs'] is not None:
            text.append("RETURN VALUES:")
            if isinstance(doc['returndocs'], string_types):
                text.append(doc.pop('returndocs'))
            else:
                text.append(yaml.dump(doc.pop('returndocs'), indent=2, default_flow_style=False))
        text.append('')

        try:
            metadata_block = DocCLI.get_metadata_block(doc)
            if metadata_block:
                text.extend(metadata_block)
                text.append('')
        except Exception:
            pass  # metadata is optional

        return "\n".join(text)
