# (c) 2014, Nandor Sivok <dominis@haxor.hu>
# (c) 2016, Redhat Inc
#
# ansible-console is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ansible-console is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

########################################################
# ansible-console is an interactive REPL shell for ansible
# with built-in tab completion for all the documented modules
#
# Available commands:
#  cd - change host/group (you can use host patterns eg.: app*.dc*:!app01*)
#  list - list available hosts in the current path
#  forks - change fork
#  become - become
#  ! - forces shell module instead of the ansible module (!yum update -y)

import atexit
import cmd
import getpass
import readline
import os
import sys

from ansible import constants as C
from ansible.cli import CLI
from ansible.errors import AnsibleError, AnsibleOptionsError

from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory import Inventory
from ansible.parsing.dataloader import DataLoader
from ansible.parsing.splitter import parse_kv
from ansible.playbook.play import Play
from ansible.vars import VariableManager
from ansible.utils import module_docs
from ansible.utils.color import stringc
from ansible.utils.unicode import to_unicode, to_str
from ansible.plugins import module_loader


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ConsoleCLI(CLI, cmd.Cmd):

    modules = []

    def __init__(self, args):

        super(ConsoleCLI, self).__init__(args)

        self.intro = 'Welcome to the ansible console.\nType help or ? to list commands.\n'

        self.groups = []
        self.hosts = []
        self.pattern = None
        self.variable_manager = None
        self.loader = None
        self.passwords = dict()

        self.modules = None
        cmd.Cmd.__init__(self)

    def parse(self):
        self.parser = CLI.base_parser(
            usage='%prog <host-pattern> [options]',
            runas_opts=True,
            inventory_opts=True,
            connect_opts=True,
            check_opts=True,
            vault_opts=True,
            fork_opts=True,
            module_opts=True,
        )

        # options unique to shell
        self.parser.add_option('--step', dest='step', action='store_true',
            help="one-step-at-a-time: confirm each task before running")

        self.parser.set_defaults(cwd='*')
        self.options, self.args = self.parser.parse_args(self.args[1:])

        display.verbosity = self.options.verbosity
        self.validate_conflicts(runas_opts=True, vault_opts=True, fork_opts=True)

        return True

    def get_names(self):
        return dir(self)

    def cmdloop(self):
        try:
            cmd.Cmd.cmdloop(self)
        except KeyboardInterrupt:
            self.do_exit(self)

    def set_prompt(self):
        login_user = self.options.remote_user or getpass.getuser()
        self.selected = self.inventory.list_hosts(self.options.cwd)
        prompt = "%s@%s (%d)[f:%s]" % (login_user, self.options.cwd, len(self.selected), self.options.forks)
        if self.options.become and self.options.become_user in [None, 'root']:
            prompt += "# "
            color = C.COLOR_ERROR
        else:
            prompt += "$ "
            color = C.COLOR_HIGHLIGHT
        self.prompt = stringc(prompt, color)

    def list_modules(self):
        modules = set()
        if self.options.module_path is not None:
            for i in self.options.module_path.split(os.pathsep):
                module_loader.add_directory(i)

        module_paths = module_loader._get_paths()
        for path in module_paths:
            if path is not None:
                modules.update(self._find_modules_in_path(path))
        return modules

    def _find_modules_in_path(self, path):

        if os.path.isdir(path):
            for module in os.listdir(path):
                if module.startswith('.'):
                    continue
                elif os.path.isdir(module):
                    self._find_modules_in_path(module)
                elif module.startswith('__'):
                    continue
                elif any(module.endswith(x) for x in C.BLACKLIST_EXTS):
                    continue
                elif module in C.IGNORE_FILES:
                    continue
                elif module.startswith('_'):
                    fullpath = '/'.join([path,module])
                    if os.path.islink(fullpath): # avoids aliases
                        continue
                    module = module.replace('_', '', 1)

                module = os.path.splitext(module)[0] # removes the extension
                yield module

    def default(self, arg, forceshell=False):
        """ actually runs modules """
        if arg.startswith("#"):
            return False

        if not self.options.cwd:
            display.error("No host found")
            return False

        if arg.split()[0] in self.modules:
            module = arg.split()[0]
            module_args = ' '.join(arg.split()[1:])
        else:
            module = 'shell'
            module_args = arg

        if forceshell is True:
            module = 'shell'
            module_args = arg

        self.options.module_name = module

        result = None
        try:
            play_ds = dict(
                name = "Ansible Shell",
                hosts = self.options.cwd,
                gather_facts = 'no',
                #tasks = [ dict(action=dict(module=module, args=parse_kv(module_args)), async=self.options.async, poll=self.options.poll_interval) ]
                tasks = [ dict(action=dict(module=module, args=parse_kv(module_args)))]
            )
            play = Play().load(play_ds, variable_manager=self.variable_manager, loader=self.loader)
        except Exception as e:
            display.error(u"Unable to build command: %s" % to_unicode(e))
            return False

        try:
            cb = 'minimal' #FIXME: make callbacks configurable
            # now create a task queue manager to execute the play
            self._tqm = None
            try:
                self._tqm = TaskQueueManager(
                        inventory=self.inventory,
                        variable_manager=self.variable_manager,
                        loader=self.loader,
                        options=self.options,
                        passwords=self.passwords,
                        stdout_callback=cb,
                        run_additional_callbacks=C.DEFAULT_LOAD_CALLBACK_PLUGINS,
                        run_tree=False,
                    )

                result = self._tqm.run(play)
            finally:
                if self._tqm:
                    self._tqm.cleanup()

            if result is None:
                display.error("No hosts found")
                return False
        except KeyboardInterrupt:
            display.error('User interrupted execution')
            return False
        except Exception as e:
            display.error(to_unicode(e))
            #FIXME: add traceback in very very verbose mode
            return False

    def emptyline(self):
        return

    def do_shell(self, arg):
        """
        You can run shell commands through the shell module.

        eg.:
        shell ps uax | grep java | wc -l
        shell killall python
        shell halt -n

        You can use the ! to force the shell module. eg.:
        !ps aux | grep java | wc -l
        """
        self.default(arg, True)

    def do_forks(self, arg):
        """Set the number of forks"""
        if not arg:
            display.display('Usage: forks <number>')
            return
        self.options.forks = int(arg)
        self.set_prompt()

    do_serial = do_forks

    def do_verbosity(self, arg):
        """Set verbosity level"""
        if not arg:
            display.display('Usage: verbosity <number>')
        else:
            display.verbosity = int(arg)
            display.v('verbosity level set to %s' % arg)

    def do_cd(self, arg):
        """
            Change active host/group. You can use hosts patterns as well eg.:
            cd webservers
            cd webservers:dbservers
            cd webservers:!phoenix
            cd webservers:&staging
            cd webservers:dbservers:&staging:!phoenix
        """
        if not arg:
            self.options.cwd = '*'
        elif arg == '..':
            try:
                self.options.cwd = self.inventory.groups_for_host(self.options.cwd)[1].name
            except Exception:
                self.options.cwd = ''
        elif arg in '/*':
            self.options.cwd = 'all'
        elif self.inventory.get_hosts(arg):
            self.options.cwd = arg
        else:
            display.display("no host matched")

        self.set_prompt()

    def do_list(self, arg):
        """List the hosts in the current group"""
        if arg == 'groups':
            for group in self.groups:
                display.display(group)
        else:
            for host in self.selected:
                display.display(host.name)

    def do_become(self, arg):
        """Toggle whether plays run with become"""
        if arg:
            self.options.become_user = arg
            display.v("become changed to %s" % self.options.become)
            self.set_prompt()
        else:
            display.display("Please specify become value, e.g. `become yes`")

    def do_remote_user(self, arg):
        """Given a username, set the remote user plays are run by"""
        if arg:
            self.options.remote_user = arg
            self.set_prompt()
        else:
            display.display("Please specify a remote user, e.g. `remote_user root`")

    def do_become_user(self, arg):
        """Given a username, set the user that plays are run by when using become"""
        if arg:
            self.options.become_user = arg
        else:
            display.display("Please specify a user, e.g. `become_user jenkins`")
            display.v("Current user is %s" % self.options.become_user)
        self.set_prompt()

    def do_become_method(self, arg):
        """Given a become_method, set the privilege escalation method when using become"""
        if arg:
            self.options.become_method = arg
            display.v("become_method changed to %s" % self.options.become_method)
        else:
            display.display("Please specify a become_method, e.g. `become_method su`")

    def do_exit(self, args):
        """Exits from the console"""
        sys.stdout.write('\n')
        return -1

    do_EOF = do_exit

    def helpdefault(self, module_name):
        if module_name in self.modules:
            in_path = module_loader.find_plugin(module_name)
            if in_path:
                oc, a, _ = module_docs.get_docstring(in_path)
                if oc:
                    display.display(oc['short_description'])
                    display.display('Parameters:')
                    for opt in oc['options'].keys():
                        display.display('  ' + stringc(opt, C.COLOR_HIGHLIGHT) + ' ' + oc['options'][opt]['description'][0])
                else:
                    display.error('No documentation found for %s.' % module_name)
            else:
                display.error('%s is not a valid command, use ? to list all valid commands.' % module_name)

    def complete_cd(self, text, line, begidx, endidx):
        mline = line.partition(' ')[2]
        offs = len(mline) - len(text)

        if self.options.cwd in ('all','*','\\'):
            completions = self.hosts + self.groups
        else:
            completions = [x.name for x in self.inventory.list_hosts(self.options.cwd)]

        return [to_str(s)[offs:] for s in completions if to_str(s).startswith(to_str(mline))]

    def completedefault(self, text, line, begidx, endidx):
        if line.split()[0] in self.modules:
            mline = line.split(' ')[-1]
            offs = len(mline) - len(text)
            completions = self.module_args(line.split()[0])

            return [s[offs:] + '=' for s in completions if s.startswith(mline)]

    def module_args(self, module_name):
        in_path = module_loader.find_plugin(module_name)
        oc, a, _ = module_docs.get_docstring(in_path)
        return oc['options'].keys()


    def run(self):

        super(ConsoleCLI, self).run()

        sshpass    = None
        becomepass = None
        vault_pass = None

        # hosts
        if len(self.args) != 1:
            self.pattern = 'all'
        else:
            self.pattern = self.args[0]
        self.options.cwd = self.pattern


        # dynamically add modules as commands
        self.modules = self.list_modules()
        for module in self.modules:
            setattr(self, 'do_' + module, lambda arg, module=module: self.default(module + ' ' + arg))
            setattr(self, 'help_' + module, lambda module=module: self.helpdefault(module))

        self.normalize_become_options()
        (sshpass, becomepass) = self.ask_passwords()
        self.passwords = { 'conn_pass': sshpass, 'become_pass': becomepass }

        self.loader = DataLoader()

        if self.options.vault_password_file:
            # read vault_pass from a file
            vault_pass = CLI.read_vault_password_file(self.options.vault_password_file, loader=self.loader)
            self.loader.set_vault_password(vault_pass)
        elif self.options.ask_vault_pass:
            vault_pass = self.ask_vault_passwords()[0]
            self.loader.set_vault_password(vault_pass)

        self.variable_manager = VariableManager()
        self.inventory = Inventory(loader=self.loader, variable_manager=self.variable_manager, host_list=self.options.inventory)
        self.variable_manager.set_inventory(self.inventory)

        if len(self.inventory.list_hosts(self.pattern)) == 0:
            # Empty inventory
            display.warning("provided hosts list is empty, only localhost is available")

        self.inventory.subset(self.options.subset)
        self.groups = self.inventory.list_groups()
        self.hosts = [x.name for x in self.inventory.list_hosts(self.pattern)]

        # This hack is to work around readline issues on a mac:
        #  http://stackoverflow.com/a/7116997/541202
        if 'libedit' in readline.__doc__:
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")

        histfile = os.path.join(os.path.expanduser("~"), ".ansible-console_history")
        try:
            readline.read_history_file(histfile)
        except IOError:
            pass

        atexit.register(readline.write_history_file, histfile)
        self.set_prompt()
        self.cmdloop()

