#!/usr/bin/env python
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# PYTHON_ARGCOMPLETE_OK

from __future__ import annotations

# ansible.cli needs to be imported first, to ensure the source bin/* scripts run that code first
from ansible.cli import CLI

import os
import shlex
import sys
import yaml

from collections.abc import Mapping

from ansible import context
import ansible.plugins.loader as plugin_loader

from ansible import constants as C
from ansible.cli.arguments import option_helpers as opt_help
from ansible.config.manager import ConfigManager
from ansible.errors import AnsibleError, AnsibleOptionsError, AnsibleRequiredOptionError
from ansible.module_utils.common.text.converters import to_native, to_text, to_bytes
from ansible._internal import _json
from ansible.parsing.quoting import is_quoted
from ansible.parsing.yaml.dumper import AnsibleDumper
from ansible.utils.color import stringc
from ansible.utils.display import Display
from ansible.utils.path import unfrackpath

display = Display()


_IGNORE_CHANGED = frozenset({'_terms', '_input'})


def yaml_dump(data, default_flow_style=False, default_style=None):
    return yaml.dump(data, Dumper=AnsibleDumper, default_flow_style=default_flow_style, default_style=default_style)


def yaml_short(data):
    return yaml_dump(data, default_flow_style=True, default_style="''")


def get_constants():
    """ helper method to ensure we can template based on existing constants """
    if not hasattr(get_constants, 'cvars'):
        get_constants.cvars = {k: getattr(C, k) for k in dir(C) if not k.startswith('__')}
    return get_constants.cvars


def _ansible_env_vars(varname):
    """ return true or false depending if variable name is possibly a 'configurable' ansible env variable """
    return all(
        [
            varname.startswith("ANSIBLE_"),
            not varname.startswith(("ANSIBLE_TEST_", "ANSIBLE_LINT_")),
            varname not in ("ANSIBLE_CONFIG", "ANSIBLE_DEV_HOME"),
        ]
    )


def _get_evar_list(settings):
    data = []
    for setting in settings:
        if 'env' in settings[setting] and settings[setting]['env']:
            for varname in settings[setting]['env']:
                data.append(varname.get('name'))
    return data


def _get_ini_entries(settings):
    data = {}
    for setting in settings:
        if 'ini' in settings[setting] and settings[setting]['ini']:
            for kv in settings[setting]['ini']:
                if not kv['section'] in data:
                    data[kv['section']] = set()
                data[kv['section']].add(kv['key'])
    return data


class ConfigCLI(CLI):
    """ Config command line class """

    name = 'ansible-config'

    def __init__(self, args, callback=None):

        self.config_file = None
        self.config = None
        super(ConfigCLI, self).__init__(args, callback)

    def init_parser(self):

        super(ConfigCLI, self).init_parser(
            desc="View ansible configuration.",
        )

        common = opt_help.ArgumentParser(add_help=False)
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
        list_parser.add_argument('--format', '-f', dest='format', action='store', choices=['json', 'yaml'], default='yaml',
                                 help='Output format for list')

        dump_parser = subparsers.add_parser('dump', help='Dump configuration', parents=[common])
        dump_parser.set_defaults(func=self.execute_dump)
        dump_parser.add_argument('--only-changed', '--changed-only', dest='only_changed', action='store_true',
                                 help="Only show configurations that have changed from the default")
        dump_parser.add_argument('--format', '-f', dest='format', action='store', choices=['json', 'yaml', 'display'], default='display',
                                 help='Output format for dump')

        view_parser = subparsers.add_parser('view', help='View configuration file', parents=[common])
        view_parser.set_defaults(func=self.execute_view)

        init_parser = subparsers.add_parser('init', help='Create initial configuration', parents=[common])
        init_parser.set_defaults(func=self.execute_init)
        init_parser.add_argument('--format', '-f', dest='format', action='store', choices=['ini', 'env', 'vars'], default='ini',
                                 help='Output format for init')
        init_parser.add_argument('--disabled', dest='commented', action='store_true', default=False,
                                 help='Prefixes all entries with a comment character to disable them')

        validate_parser = subparsers.add_parser('validate',
                                                help='Validate the configuration file and environment variables. '
                                                     'By default it only checks the base settings without accounting for plugins (see -t).',
                                                parents=[common])
        validate_parser.set_defaults(func=self.execute_validate)
        validate_parser.add_argument('--format', '-f', dest='format', action='store', choices=['ini', 'env'] , default='ini',
                                     help='Output format for init')

    def post_process_args(self, options):
        options = super(ConfigCLI, self).post_process_args(options)
        display.verbosity = options.verbosity

        return options

    def run(self):

        super(ConfigCLI, self).run()

        # initialize each galaxy server's options from known listed servers
        self._galaxy_servers = [s for s in C.GALAXY_SERVER_LIST or [] if s]  # clean list, reused later here
        C.config.load_galaxy_server_defs(self._galaxy_servers)

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

        elif context.CLIARGS['action'] == 'view':
            raise AnsibleError('Invalid or no config file was supplied')

        # run the requested action
        context.CLIARGS['func']()

    def execute_view(self):
        """
        Displays the current config file
        """
        try:
            with open(self.config_file, 'rb') as f:
                self.pager(to_text(f.read(), errors='surrogate_or_strict'))
        except Exception as e:
            raise AnsibleError("Failed to open config file: %s" % to_native(e))

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
        """
        build a dict with the list requested configs
        """

        config_entries = {}
        if context.CLIARGS['type'] in ('base', 'all'):
            # this dumps main/common configs
            config_entries = self.config.get_configuration_definitions(ignore_private=True)

            # for base and all, we include galaxy servers
            config_entries['GALAXY_SERVERS'] = {}
            for server in self._galaxy_servers:
                config_entries['GALAXY_SERVERS'][server] = self.config.get_configuration_definitions('galaxy_server', server)

        if context.CLIARGS['type'] != 'base':
            config_entries['PLUGINS'] = {}

        if context.CLIARGS['type'] == 'all':
            # now each plugin type
            for ptype in C.CONFIGURABLE_PLUGINS:
                config_entries['PLUGINS'][ptype.upper()] = self._list_plugin_settings(ptype)
        elif context.CLIARGS['type'] != 'base':
            # only for requested types
            config_entries['PLUGINS'][context.CLIARGS['type']] = self._list_plugin_settings(context.CLIARGS['type'], context.CLIARGS['args'])

        return config_entries

    def execute_list(self):
        """
        list and output available configs
        """

        config_entries = self._list_entries_from_args()
        if context.CLIARGS['format'] == 'yaml':
            output = yaml_dump(config_entries)
        elif context.CLIARGS['format'] == 'json':
            output = _json.json_dumps_formatted(config_entries)

        self.pager(to_text(output, errors='surrogate_or_strict'))

    def _get_settings_vars(self, settings, subkey):

        data = []
        if context.CLIARGS['commented']:
            prefix = '#'
        else:
            prefix = ''

        for setting in settings:

            if not settings[setting].get('description'):
                continue

            default = self.config.template_default(settings[setting].get('default', ''), get_constants())
            if subkey == 'env':
                stype = settings[setting].get('type', '')
                if stype == 'boolean':
                    if default:
                        default = '1'
                    else:
                        default = '0'
                elif default:
                    if stype == 'list':
                        if not isinstance(default, str):
                            # python lists are not valid env ones
                            try:
                                default = ', '.join(default)
                            except Exception as e:
                                # list of other stuff
                                default = '%s' % to_native(default)
                    if isinstance(default, str) and not is_quoted(default):
                        default = shlex.quote(default)
                elif default is None:
                    default = ''

            if subkey in settings[setting] and settings[setting][subkey]:
                entry = settings[setting][subkey][-1]['name']
                if isinstance(settings[setting]['description'], str):
                    desc = settings[setting]['description']
                else:
                    desc = '\n#'.join(settings[setting]['description'])
                name = settings[setting].get('name', setting)
                data.append('# %s(%s): %s' % (name, settings[setting].get('type', 'string'), desc))

                # TODO: might need quoting and value coercion depending on type
                if subkey == 'env':
                    if entry.startswith('_ANSIBLE_'):
                        continue
                    data.append('%s%s=%s' % (prefix, entry, default))
                elif subkey == 'vars':
                    if entry.startswith('_ansible_'):
                        continue
                    data.append(prefix + '%s: %s' % (entry, to_text(yaml_short(default), errors='surrogate_or_strict')))
                data.append('')

        return data

    def _get_settings_ini(self, settings, seen):

        sections = {}
        for o in sorted(settings.keys()):

            opt = settings[o]

            if not isinstance(opt, Mapping):
                # recursed into one of the few settings that is a mapping, now hitting it's strings
                continue

            if not opt.get('description'):
                # its a plugin
                new_sections = self._get_settings_ini(opt, seen)
                for s in new_sections:
                    if s in sections:
                        sections[s].extend(new_sections[s])
                    else:
                        sections[s] = new_sections[s]
                continue

            if isinstance(opt['description'], str):
                desc = '# (%s) %s' % (opt.get('type', 'string'), opt['description'])
            else:
                desc = "# (%s) " % opt.get('type', 'string')
                desc += "\n# ".join(opt['description'])

            if 'ini' in opt and opt['ini']:
                entry = opt['ini'][-1]
                if entry['section'] not in seen:
                    seen[entry['section']] = []
                if entry['section'] not in sections:
                    sections[entry['section']] = []

                # avoid dupes
                if entry['key'] not in seen[entry['section']]:
                    seen[entry['section']].append(entry['key'])

                    default = self.config.template_default(opt.get('default', ''), get_constants())
                    if opt.get('type', '') == 'list' and not isinstance(default, str):
                        # python lists are not valid ini ones
                        default = ', '.join(default)
                    elif default is None:
                        default = ''

                    if context.CLIARGS.get('commented', False):
                        entry['key'] = ';%s' % entry['key']

                    key = desc + '\n%s=%s' % (entry['key'], default)

                    sections[entry['section']].append(key)

        return sections

    def execute_init(self):
        """Create initial configuration"""

        seen = {}
        data = []
        config_entries = self._list_entries_from_args()
        plugin_types = config_entries.pop('PLUGINS', None)

        if context.CLIARGS['format'] == 'ini':
            sections = self._get_settings_ini(config_entries, seen)

            if plugin_types:
                for ptype in plugin_types:
                    plugin_sections = self._get_settings_ini(plugin_types[ptype], seen)
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

        entries = []
        for setting in sorted(config):
            changed = (config[setting]['origin'] not in ('default', 'REQUIRED') and setting not in _IGNORE_CHANGED)

            if context.CLIARGS['format'] == 'display':
                if isinstance(config[setting], dict):
                    # proceed normally
                    value = config[setting]['value']
                    if config[setting]['origin'] == 'default' or setting in _IGNORE_CHANGED:
                        color = 'green'
                        value = self.config.template_default(value, get_constants())
                    elif config[setting]['origin'] == 'REQUIRED':
                        # should include '_terms', '_input', etc
                        color = 'red'
                    else:
                        color = 'yellow'
                    msg = "%s(%s) = %s" % (setting, config[setting]['origin'], value)
                else:
                    color = 'green'
                    msg = "%s(%s) = %s" % (setting, 'default', config[setting].get('default'))

                entry = stringc(msg, color)
            else:
                entry = {}
                for key in config[setting].keys():
                    if key == 'type':
                        continue
                    entry[key] = config[setting][key]

            if not context.CLIARGS['only_changed'] or changed:
                entries.append(entry)

        return entries

    def _get_global_configs(self):

        # Add base
        config = self.config.get_configuration_definitions(ignore_private=True)
        # convert to settings
        settings = {}
        for setting in config.keys():
            v, o = C.config.get_config_value_and_origin(setting, cfile=self.config_file, variables=get_constants())
            settings[setting] = {
                'name': setting,
                'value': v,
                'origin': o,
                'type': None
            }

        return self._render_settings(settings)

    def _get_plugin_configs(self, ptype, plugins):

        # prep loading
        loader = getattr(plugin_loader, '%s_loader' % ptype)

        # accumulators
        output = []
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
            # in case of deprecation they diverge
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
                    v, o = C.config.get_config_value_and_origin(setting, cfile=self.config_file, plugin_type=ptype, plugin_name=name, variables=get_constants())
                except AnsibleRequiredOptionError:
                    v = None
                    o = 'REQUIRED'

                if v is None and o is None:
                    # not all cases will be error
                    o = 'REQUIRED'

                config_entries[finalname][setting] = {
                    'name': setting,
                    'value': v,
                    'origin': o,
                    'type': None
                }

            # pretty please!
            results = self._render_settings(config_entries[finalname])
            if results:
                if context.CLIARGS['format'] == 'display':
                    # avoid header for empty lists (only changed!)
                    output.append('\n%s:\n%s' % (finalname, '_' * len(finalname)))
                    output.extend(results)
                else:
                    output.append({finalname: results})

        return output

    def _get_galaxy_server_configs(self):

        output = []
        # add galaxy servers
        for server in self._galaxy_servers:
            server_config = {}
            s_config = self.config.get_configuration_definitions('galaxy_server', server)
            for setting in s_config.keys():
                try:
                    v, o = C.config.get_config_value_and_origin(setting, plugin_type='galaxy_server', plugin_name=server, cfile=self.config_file)
                except AnsibleError as e:
                    if s_config[setting].get('required', False):
                        v = None
                        o = 'REQUIRED'
                    else:
                        raise e
                if v is None and o is None:
                    # not all cases will be error
                    o = 'REQUIRED'
                server_config[setting] = {
                    'name': setting,
                    'value': v,
                    'origin': o,
                    'type': None
                }
            if context.CLIARGS['format'] == 'display':
                if not context.CLIARGS['only_changed'] or server_config:
                    equals = '=' * len(server)
                    output.append(f'\n{server}\n{equals}')
                    output.extend(self._render_settings(server_config))
            else:
                output.append({server: server_config})

        return output

    def execute_dump(self):
        """
        Shows the current settings, merges ansible.cfg if specified
        """
        output = []
        if context.CLIARGS['type'] in ('base', 'all'):
            # deal with base
            output = self._get_global_configs()

            # add galaxy servers
            server_config_list = self._get_galaxy_server_configs()
            if context.CLIARGS['format'] == 'display':
                output.append('\nGALAXY_SERVERS:\n')
                output.extend(server_config_list)
            else:
                configs = {}
                for server_config in server_config_list:
                    server = list(server_config.keys())[0]
                    server_reduced_config = server_config.pop(server)
                    configs[server] = list(server_reduced_config.values())
                output.append({'GALAXY_SERVERS': configs})

        if context.CLIARGS['type'] == 'all':
            # add all plugins
            for ptype in C.CONFIGURABLE_PLUGINS:
                plugin_list = self._get_plugin_configs(ptype, context.CLIARGS['args'])
                if context.CLIARGS['format'] == 'display':
                    if not context.CLIARGS['only_changed'] or plugin_list:
                        output.append('\n%s:\n%s' % (ptype.upper(), '=' * len(ptype)))
                        output.extend(plugin_list)
                else:
                    if ptype in ('modules', 'doc_fragments'):
                        pname = ptype.upper()
                    else:
                        pname = '%s_PLUGINS' % ptype.upper()
                    output.append({pname: plugin_list})

        elif context.CLIARGS['type'] != 'base':
            # deal with specific plugin
            output = self._get_plugin_configs(context.CLIARGS['type'], context.CLIARGS['args'])

        if context.CLIARGS['format'] == 'display':
            text = '\n'.join(output)
        if context.CLIARGS['format'] == 'yaml':
            text = yaml_dump(output)
        elif context.CLIARGS['format'] == 'json':
            text = _json.json_dumps_formatted(output)

        self.pager(to_text(text, errors='surrogate_or_strict'))

    def execute_validate(self):

        found = False
        config_entries = self._list_entries_from_args()
        plugin_types = config_entries.pop('PLUGINS', None)
        galaxy_servers = config_entries.pop('GALAXY_SERVERS', None)

        if context.CLIARGS['format'] == 'ini':
            if C.CONFIG_FILE is not None:
                # validate ini config since it is found

                sections = _get_ini_entries(config_entries)
                # Also from plugins
                if plugin_types:
                    for ptype in plugin_types:
                        for plugin in plugin_types[ptype].keys():
                            plugin_sections = _get_ini_entries(plugin_types[ptype][plugin])
                            for s in plugin_sections:
                                if s in sections:
                                    sections[s].update(plugin_sections[s])
                                else:
                                    sections[s] = plugin_sections[s]
                if galaxy_servers:
                    for server in galaxy_servers:
                        server_sections = _get_ini_entries(galaxy_servers[server])
                        for s in server_sections:
                            if s in sections:
                                sections[s].update(server_sections[s])
                            else:
                                sections[s] = server_sections[s]
                if sections:
                    p = C.config._parsers[C.CONFIG_FILE]
                    for s in p.sections():
                        # check for valid sections
                        if s not in sections:
                            display.error(f"Found unknown section '{s}' in '{C.CONFIG_FILE}.")
                            found = True
                            continue

                        # check keys in valid sections
                        for k in p.options(s):
                            if k not in sections[s]:
                                display.error(f"Found unknown key '{k}' in section '{s}' in '{C.CONFIG_FILE}.")
                                found = True

        elif context.CLIARGS['format'] == 'env':
            # validate any 'ANSIBLE_' env vars found
            evars = [varname for varname in os.environ.keys() if _ansible_env_vars(varname)]
            if evars:
                data = _get_evar_list(config_entries)
                if plugin_types:
                    for ptype in plugin_types:
                        for plugin in plugin_types[ptype].keys():
                            data.extend(_get_evar_list(plugin_types[ptype][plugin]))

                for evar in evars:
                    if evar not in data:
                        display.error(f"Found unknown environment variable '{evar}'.")
                        found = True

        # we found discrepancies!
        if found:
            sys.exit(1)

        # allsgood
        display.display("All configurations seem valid!")


def main(args=None):
    ConfigCLI.cli_executor(args)


if __name__ == '__main__':
    main()
