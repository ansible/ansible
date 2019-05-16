# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import shlex
import subprocess
import sys
import yaml

from ansible import context
from ansible.cli import CLI
from ansible.config.manager import ConfigManager, Setting, find_ini_config_file
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.module_utils._text import to_native, to_text
from ansible.parsing.yaml.dumper import AnsibleDumper
from ansible.utils.color import stringc
from ansible.utils.display import Display
from ansible.utils.path import unfrackpath

display = Display()


class ConfigCLI(CLI):
    """ Config command line class """

    VALID_ACTIONS = frozenset(("view", "dump", "list"))  # TODO: edit, update, search

    def __init__(self, args, callback=None):

        self.config_file = None
        self.config = None
        super(ConfigCLI, self).__init__(args, callback)

    def init_parser(self):

        super(ConfigCLI, self).init_parser(
            usage="usage: %%prog [%s] [--help] [options] [ansible.cfg]" % "|".join(sorted(self.VALID_ACTIONS)),
            epilog="\nSee '%s <command> --help' for more information on a specific command.\n\n" % os.path.basename(sys.argv[0]),
            desc="View ansible configuration.",
        )
        self.parser.add_option('-c', '--config', dest='config_file',
                               help="path to configuration file, defaults to first file found in precedence.")

        self.set_action()

        # options specific to self.actions
        if self.action == "list":
            self.parser.set_usage("usage: %prog list [options] ")

        elif self.action == "dump":
            self.parser.add_option('--only-changed', dest='only_changed', action='store_true',
                                   help="Only show configurations that have changed from the default")

        elif self.action == "update":
            self.parser.add_option('-s', '--setting', dest='setting', help="config setting, the section defaults to 'defaults'")
            self.parser.set_usage("usage: %prog update [options] [-c ansible.cfg] -s '[section.]setting=value'")

        elif self.action == "search":
            self.parser.set_usage("usage: %prog update [options] [-c ansible.cfg] <search term>")

    def post_process_args(self, options, args):
        options, args = super(ConfigCLI, self).post_process_args(options, args)
        display.verbosity = options.verbosity

        return options, args

    def run(self):

        super(ConfigCLI, self).run()

        if context.CLIARGS['config_file']:
            self.config_file = unfrackpath(context.CLIARGS['config_file'], follow=False)
            self.config = ConfigManager(self.config_file)
        else:
            self.config = ConfigManager()
            self.config_file = find_ini_config_file()

        if self.config_file:
            try:
                if not os.path.exists(self.config_file):
                    raise AnsibleOptionsError("%s does not exist or is not accessible" % (self.config_file))
                elif not os.path.isfile(self.config_file):
                    raise AnsibleOptionsError("%s is not a valid file" % (self.config_file))

                os.environ['ANSIBLE_CONFIG'] = to_native(self.config_file)
            except Exception:
                if self.action in ['view']:
                    raise
                elif self.action in ['edit', 'update']:
                    display.warning("File does not exist, used empty file: %s" % self.config_file)

        elif self.action == 'view':
            raise AnsibleError('Invalid or no config file was supplied')

        self.execute()

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

    def execute_list(self):
        '''
        list all current configs reading lib/constants.py and shows env and config file setting names
        '''
        self.pager(to_text(yaml.dump(self.config.get_configuration_definitions(), Dumper=AnsibleDumper), errors='surrogate_or_strict'))

    def execute_dump(self):
        '''
        Shows the current settings, merges ansible.cfg if specified
        '''
        # FIXME: deal with plugins, not just base config
        text = []
        defaults = self.config.get_configuration_definitions().copy()
        for setting in self.config.data.get_settings():
            if setting.name in defaults:
                defaults[setting.name] = setting

        for setting in sorted(defaults):
            if isinstance(defaults[setting], Setting):
                if defaults[setting].origin == 'default':
                    color = 'green'
                else:
                    color = 'yellow'
                msg = "%s(%s) = %s" % (setting, defaults[setting].origin, defaults[setting].value)
            else:
                color = 'green'
                msg = "%s(%s) = %s" % (setting, 'default', defaults[setting].get('default'))
            if not context.CLIARGS['only_changed'] or color == 'yellow':
                text.append(stringc(msg, color))

        self.pager(to_text('\n'.join(text), errors='surrogate_or_strict'))
