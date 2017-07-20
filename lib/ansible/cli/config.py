# (c) 2017, Ansible by Red Hat, Inc.
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
# ansible-vault is a script that encrypts/decrypts YAML files. See
# http://docs.ansible.com/playbooks_vault.html for more details.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import shlex
import subprocess
import sys
import yaml

from ansible.cli import CLI
from ansible.config.data import Setting
from ansible.config.manager import ConfigManager
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.module_utils._text import to_native, to_text
from ansible.parsing.yaml.dumper import AnsibleDumper
from ansible.utils.color import stringc
from ansible.utils.path import unfrackpath


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ConfigCLI(CLI):
    """ Config command line class """

    VALID_ACTIONS = ("view", "edit", "update", "dump", "list")

    def __init__(self, args, callback=None):

        self.config_file = None
        self.config = None
        super(ConfigCLI, self).__init__(args, callback)

    def parse(self):

        self.parser = CLI.base_parser(
            usage = "usage: %%prog [%s] [--help] [options] [ansible.cfg]" % "|".join(self.VALID_ACTIONS),
            epilog = "\nSee '%s <command> --help' for more information on a specific command.\n\n" % os.path.basename(sys.argv[0])
        )

        self.parser.add_option('-c', '--config', dest='config_file', help="path to configuration file, defaults to first file found in precedence.")

        self.set_action()

        # options specific to self.actions
        if self.action == "list":
            self.parser.set_usage("usage: %prog list [options] ")
        if self.action == "dump":
            self.parser.set_usage("usage: %prog dump [options] [-c ansible.cfg]")
        elif self.action == "view":
            self.parser.set_usage("usage: %prog view [options] [-c ansible.cfg] ")
        elif self.action == "edit":
            self.parser.set_usage("usage: %prog edit [options] [-c ansible.cfg]")
        elif self.action == "update":
            self.parser.add_option('-s', '--setting', dest='setting', help="config setting, the section defaults to 'defaults'")
            self.parser.set_usage("usage: %prog update [options] [-c ansible.cfg] -s '[section.]setting=value'")

        self.options, self.args = self.parser.parse_args()
        display.verbosity = self.options.verbosity

    def run(self):

        super(ConfigCLI, self).run()

        if self.options.config_file:
            self.config_file = unfrackpath(self.options.config_file, follow=False)
            self.config = ConfigManager(self.config_file)
        else:
            self.config = ConfigManager()
            self.config_file = self.config.data.get_setting('ANSIBLE_CONFIG')
            try:
                if not os.path.exists(self.config_file):
                    raise AnsibleOptionsError("%s does not exist or is not accessible" % (self.config_file))
                elif not os.path.isfile(self.config_file):
                    raise AnsibleOptionsError("%s is not a valid file" % (self.config_file))

                os.environ['ANSIBLE_CONFIG'] = self.config_file
            except:
                if self.action in ['view']:
                    raise
                elif self.action in ['edit', 'update']:
                    display.warning("File does not exist, used empty file: %s" % self.config_file)

        self.execute()

    def execute_update(self):
        '''
        Updates a single setting in the specified ansible.cfg
        '''
        raise AnsibleError("Option not implemented yet")

        if self.options.setting is None:
            raise AnsibleOptionsError("update option requries a setting to update")

        (entry, value) = self.options.setting.split('=')
        if '.' in entry:
            (section, option) = entry.split('.')
        else:
            section = 'defaults'
            option = entry
        subprocess.call([
            'ansible',
            '-m','ini_file',
            'localhost',
            '-c','local',
            '-a','"dest=%s section=%s option=%s value=%s backup=yes"' % (self.config_file, section, option, value)
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
        try:
            editor = shlex.split(os.environ.get('EDITOR','vi'))
            editor.append(self.config_file)
            subprocess.call(editor)
        except Exception as e:
            raise AnsibleError("Failed to open editor: %s" % to_native(e))

    def execute_list(self):
        '''
        list all current configs reading lib/constants.py and shows env and config file setting names
        '''
        self.pager(to_text(yaml.dump(self.config.initial_defs, Dumper=AnsibleDumper), errors='surrogate_or_strict'))

    def execute_dump(self):
        '''
        Shows the current settings, merges ansible.cfg if specified
        '''
        text = []
        defaults = self.config.initial_defs.copy()
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
            text.append(stringc(msg, color))

        self.pager(to_text('\n'.join(text), errors='surrogate_or_strict'))
