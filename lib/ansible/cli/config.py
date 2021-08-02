# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import shlex
import subprocess
import yaml

from ansible import context
import ansible.plugins.loader as plugin_loader

from ansible import constants as C
from ansible.cli import CLI
from ansible.cli.arguments import option_helpers as opt_help
from ansible.config.manager import ConfigManager, Setting
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.module_utils._text import to_native, to_text, to_bytes
from ansible.module_utils.common._collections_compat import Mapping
from ansible.module_utils.six import string_types
from ansible.module_utils.six.moves import shlex_quote
from ansible.parsing.quoting import is_quoted
from ansible.parsing.yaml.dumper import AnsibleDumper
from ansible.utils.color import stringc
from ansible.utils.display import Display
from ansible.utils.path import unfrackpath

display = Display()


class ConfigCLI(CLI):
    """ Config command line class """

    def __init__(self, args, callback=None):

        self.config_file = None
        self.config = None
        super(ConfigCLI, self).__init__(args, callback)

    def init_parser(self):

        super(ConfigCLI, self).init_parser(
            desc="View ansible configuration.",
        )

        common = opt_help.argparse.ArgumentParser(add_help=False)
        opt_help.add_verbosity_options(common)
        common.add_argument('-c', '--config', dest='config_file',
                            help="path to configuration file, defaults to first file found in precedence.")
        common.add_argument("-t", "--type", action="store", default='base', dest='type', choices=['all', 'base'] + list(C.CONFIGURABLE_PLUGINS),
                            help="Filter down to a specific plugin type.")
        common.add_argument('args', help='Specific plugin to target, requires type of plugin to be set', nargs='*')

        subparsers = self.parser.add_subparsers(dest='action')
        subparsers.required = True

        list_parser = subparsers.add_parser('list', help='Print all config options', parents=[common])
        list_parser.set_defaults(func=self.execute_list)

        dump_parser = subparsers.add_parser('dump', help='Dump configuration', parents=[common])
        dump_parser.set_defaults(func=self.execute_dump)
        dump_parser.add_argument('--only-changed', '--changed-only', dest='only_changed', action='store_true',
                                 help="Only show configurations that have changed from the default")

        view_parser = subparsers.add_parser('view', help='View configuration file', parents=[common])
        view_parser.set_defaults(func=self.execute_view)

        init_parser = subparsers.add_parser('init', help='Create initial configuration', parents=[common])
        init_parser.set_defaults(func=self.execute_init)
        init_parser.add_argument('--format', '-f', dest='format', action='store', choices=['ini', 'env', 'vars'], default='ini',
                                 help='Output format for init')
        init_parser.add_argument('--disabled', dest='commented', action='store_true', default=False,
                                 help='Prefixes all entries with a comment character to disable them')

        # search_parser = subparsers.add_parser('find', help='Search configuration')
        # search_parser.set_defaults(func=self.execute_search)
        # search_parser.add_argument('args', help='Search term', metavar='<search term>')

    def post_process_args(self, options):
        options = super(ConfigCLI, self).post_process_args(options)
        display.verbosity = options.verbosity

        return options

    def run(self):

        super(ConfigCLI, self).run()

        if context.CLIARGS['config_file']:
            self.config_file = unfrackpath(context.CLIARGS['config_file'], follow=False)
            b_config = to_bytes(self.config_file)
            if os.path.exists(b_config) and os.access(b_config, os.R_OK):
                self.config = ConfigManager(self.config_file)
            else:
                raise AnsibleOptionsError('The provided configuration file is missing or not accessible: %s' % to_native(self.config_file))
        else:
            self.config = C.config
            self.config_file = self.config._config_file

        if self.config_file:
            try:
                if not os.path.exists(self.config_file):
                    raise AnsibleOptionsError("%s does not exist or is not accessible" % (self.config_file))
                elif not os.path.isfile(self.config_file):
                    raise AnsibleOptionsError("%s is not a valid file" % (self.config_file))

                os.environ['ANSIBLE_CONFIG'] = to_native(self.config_file)
            except Exception:
                if context.CLIARGS['action'] in ['view']:
                    raise
                elif context.CLIARGS['action'] in ['edit', 'update']:
                    display.warning("File does not exist, used empty file: %s" % self.config_file)

        elif context.CLIARGS['action'] == 'view':
            raise AnsibleError('Invalid or no config file was supplied')

        # run the requested action
        context.CLIARGS['func']()

    def execute_update(self):
        '''
        Updates a single setting in the specified ansible.cfg
        '''
        raise AnsibleError("Option not implemented yet")

        # pylint: disable=unreachable
        if context.CLIARGS['setting'] is None:
            raise AnsibleOptionsError("update option requires a setting to update")

        (entry, value) = context.CLIARGS['setting'].split('=')
        if '.' in entry:
            (section, option) = entry.split('.')
        else:
            section = 'defaults'
            option = entry
        subprocess.call([
            'ansible',
            '-m', 'ini_file',
            'localhost',
            '-c', 'local',
            '-a', '"dest=%s section=%s option=%s value=%s backup=yes"' % (self.config_file, section, option, value)
        ])

    def execute_view(self):
        '''
        Displays the current config file
        '''
        try:
            with open(self.config_file, 'rb') as f:
                self.pager(to_text(f.read(), errors='surrogate_or_strict'))
        except Exception as e:
            raise AnsibleError("Failed to open config file: %s" % to_native(e))

    def execute_edit(self):
        '''
        Opens ansible.cfg in the default EDITOR
        '''
        raise AnsibleError("Option not implemented yet")

        # pylint: disable=unreachable
        try:
            editor = shlex.split(os.environ.get('EDITOR', 'vi'))
            editor.append(self.config_file)
            subprocess.call(editor)
        except Exception as e:
            raise AnsibleError("Failed to open editor: %s" % to_native(e))

    def _list_plugin_settings(self, ptype, plugins=None):
        entries = {}
        loader = getattr(plugin_loader, '%s_loader' % ptype)

        # build list
        if plugins:
            plugin_cs = []
            for plugin in plugins:
                p = loader.get(plugin, class_only=True)
                if p is None:
                    display.warning("Skipping %s as we could not find matching plugin" % plugin)
                else:
                    plugin_cs.append(p)
        else:
            plugin_cs = loader.all(class_only=True)

        # iterate over class instances
        for plugin in plugin_cs:
            finalname = name = plugin._load_name
            if name.startswith('_'):
                # alias or deprecated
                if os.path.islink(plugin._original_path):
                    continue
                else:
                    finalname = name.replace('_', '', 1) + ' (DEPRECATED)'

            entries[finalname] = self.config.get_configuration_definitions(ptype, name)

        return entries

    def _list_entries_from_args(self):
        '''
        build a dict with the list requested configs
        '''
        config_entries = {}
        if context.CLIARGS['type'] in ('base', 'all'):
            # this dumps main/common configs
            config_entries = self.config.get_configuration_definitions(ignore_private=True)

        if context.CLIARGS['type'] != 'base':
            config_entries['PLUGINS'] = {}

        if context.CLIARGS['type'] == 'all':
            # now each plugin type
            for ptype in C.CONFIGURABLE_PLUGINS:
                config_entries['PLUGINS'][ptype.upper()] = self._list_plugin_settings(ptype)
        elif context.CLIARGS['type'] != 'base':
            config_entries['PLUGINS'][context.CLIARGS['type']] = self._list_plugin_settings(context.CLIARGS['type'], context.CLIARGS['args'])

        return config_entries

    def execute_list(self):
        '''
        list and output available configs
        '''

        config_entries = self._list_entries_from_args()
        self.pager(to_text(yaml.dump(config_entries, Dumper=AnsibleDumper), errors='surrogate_or_strict'))

    def _get_settings_vars(self, settings, subkey):

        data = []
        if context.CLIARGS['commented']:
            prefix = '#'
        else:
            prefix = ''

        for setting in settings:

            if not settings[setting].get('description'):
                continue

            default = settings[setting].get('default', '')
            if subkey == 'env':
                stype = settings[setting].get('type', '')
                if stype == 'boolean':
                    if default:
                        default = '1'
                    else:
                        default = '0'
                elif default:
                    if stype == 'list':
                        if not isinstance(default, string_types):
                            # python lists are not valid env ones
                            try:
                                default = ', '.join(default)
                            except Exception as e:
                                # list of other stuff
                                default = '%s' % to_native(default)
                    if isinstance(default, string_types) and not is_quoted(default):
                        default = shlex_quote(default)
                elif default is None:
                    default = ''

            if subkey in settings[setting] and settings[setting][subkey]:
                entry = settings[setting][subkey][-1]['name']
                if isinstance(settings[setting]['description'], string_types):
                    desc = settings[setting]['description']
                else:
                    desc = '\n#'.join(settings[setting]['description'])
                name = settings[setting].get('name', setting)
                data.append('# %s(%s): %s' % (name, settings[setting].get('type', 'string'), desc))

                # TODO: might need quoting and value coercion depending on type
                if subkey == 'env':
                    data.append('%s%s=%s' % (prefix, entry, default))
                elif subkey == 'vars':
                    data.append(prefix + to_text(yaml.dump({entry: default}, Dumper=AnsibleDumper, default_flow_style=False), errors='surrogate_or_strict'))
                data.append('')

        return data

    def _get_settings_ini(self, settings):

        sections = {}
        for o in sorted(settings.keys()):

            opt = settings[o]

            if not isinstance(opt, Mapping):
                # recursed into one of the few settings that is a mapping, now hitting it's strings
                continue

            if not opt.get('description'):
                # its a plugin
                new_sections = self._get_settings_ini(opt)
                for s in new_sections:
                    if s in sections:
                        sections[s].extend(new_sections[s])
                    else:
                        sections[s] = new_sections[s]
                continue

            if isinstance(opt['description'], string_types):
                desc = '# (%s) %s' % (opt.get('type', 'string'), opt['description'])
            else:
                desc = "# (%s) " % opt.get('type', 'string')
                desc += "\n# ".join(opt['description'])

            if 'ini' in opt and opt['ini']:
                entry = opt['ini'][-1]
                if entry['section'] not in sections:
                    sections[entry['section']] = []

                default = opt.get('default', '')
                if opt.get('type', '') == 'list' and not isinstance(default, string_types):
                    # python lists are not valid ini ones
                    default = ', '.join(default)
                elif default is None:
                    default = ''

                if context.CLIARGS['commented']:
                    entry['key'] = ';%s' % entry['key']

                key = desc + '\n%s=%s' % (entry['key'], default)
                sections[entry['section']].append(key)

        return sections

    def execute_init(self):

        data = []
        config_entries = self._list_entries_from_args()
        plugin_types = config_entries.pop('PLUGINS', None)

        if context.CLIARGS['format'] == 'ini':
            sections = self._get_settings_ini(config_entries)

            if plugin_types:
                for ptype in plugin_types:
                    plugin_sections = self._get_settings_ini(plugin_types[ptype])
                    for s in plugin_sections:
                        if s in sections:
                            sections[s].extend(plugin_sections[s])
                        else:
                            sections[s] = plugin_sections[s]

            if sections:
                for section in sections.keys():
                    data.append('[%s]' % section)
                    for key in sections[section]:
                        data.append(key)
                        data.append('')
                    data.append('')

        elif context.CLIARGS['format'] in ('env', 'vars'):  # TODO: add yaml once that config option is added
            data = self._get_settings_vars(config_entries, context.CLIARGS['format'])
            if plugin_types:
                for ptype in plugin_types:
                    for plugin in plugin_types[ptype].keys():
                        data.extend(self._get_settings_vars(plugin_types[ptype][plugin], context.CLIARGS['format']))

        self.pager(to_text('\n'.join(data), errors='surrogate_or_strict'))

    def _render_settings(self, config):

        text = []
        for setting in sorted(config):
            if isinstance(config[setting], Setting):
                if config[setting].origin == 'default':
                    color = 'green'
                elif config[setting].origin == 'REQUIRED':
                    color = 'red'
                else:
                    color = 'yellow'
                msg = "%s(%s) = %s" % (setting, config[setting].origin, config[setting].value)
            else:
                color = 'green'
                msg = "%s(%s) = %s" % (setting, 'default', config[setting].get('default'))
            if not context.CLIARGS['only_changed'] or color == 'yellow':
                text.append(stringc(msg, color))

        return text

    def _get_global_configs(self):
        config = self.config.get_configuration_definitions(ignore_private=True).copy()
        for setting in self.config.data.get_settings():
            if setting.name in config:
                config[setting.name] = setting

        return self._render_settings(config)

    def _get_plugin_configs(self, ptype, plugins):

        # prep loading
        loader = getattr(plugin_loader, '%s_loader' % ptype)

        # acumulators
        text = []
        config_entries = {}

        # build list
        if plugins:
            plugin_cs = []
            for plugin in plugins:
                p = loader.get(plugin, class_only=True)
                if p is None:
                    display.warning("Skipping %s as we could not find matching plugin" % plugin)
                else:
                    plugin_cs.append(loader.get(plugin, class_only=True))
        else:
            plugin_cs = loader.all(class_only=True)

        for plugin in plugin_cs:
            # in case of deprecastion they diverge
            finalname = name = plugin._load_name
            if name.startswith('_'):
                if os.path.islink(plugin._original_path):
                    # skip alias
                    continue
                # deprecated, but use 'nice name'
                finalname = name.replace('_', '', 1) + ' (DEPRECATED)'

            # default entries per plugin
            config_entries[finalname] = self.config.get_configuration_definitions(ptype, name)

            try:
                # populate config entries by loading plugin
                dump = loader.get(name, class_only=True)
            except Exception as e:
                display.warning('Skipping "%s" %s plugin, as we cannot load plugin to check config due to : %s' % (name, ptype, to_native(e)))
                continue

            # actually get the values
            for setting in config_entries[finalname].keys():
                try:
                    v, o = C.config.get_config_value_and_origin(setting, plugin_type=ptype, plugin_name=name)
                except AnsibleError as e:
                    if to_text(e).startswith('No setting was provided for required configuration'):
                        v = None
                        o = 'REQUIRED'
                    else:
                        raise e
                config_entries[finalname][setting] = Setting(setting, v, o, None)

            # pretty please!
            results = self._render_settings(config_entries[finalname])
            if results:
                # avoid header for empty lists (only changed!)
                text.append('\n%s:\n%s' % (finalname, '_' * len(finalname)))
                text.extend(results)
        return text

    def execute_dump(self):
        '''
        Shows the current settings, merges ansible.cfg if specified
        '''
        if context.CLIARGS['type'] == 'base':
            # deal with base
            text = self._get_global_configs()
        elif context.CLIARGS['type'] == 'all':
            # deal with base
            text = self._get_global_configs()
            # deal with plugins
            for ptype in C.CONFIGURABLE_PLUGINS:
                text.append('\n%s:\n%s' % (ptype.upper(), '=' * len(ptype)))
                text.extend(self._get_plugin_configs(ptype, context.CLIARGS['args']))
        else:
            # deal with plugins
            text = self._get_plugin_configs(context.CLIARGS['type'], context.CLIARGS['args'])

        self.pager(to_text('\n'.join(text), errors='surrogate_or_strict'))
