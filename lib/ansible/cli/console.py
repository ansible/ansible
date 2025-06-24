#!/usr/bin/env python
# Copyright: (c) 2014, Nandor Sivok <dominis@haxor.hu>
# Copyright: (c) 2016, Redhat Inc
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# PYTHON_ARGCOMPLETE_OK

from __future__ import annotations

# ansible.cli needs to be imported first, to ensure the source bin/* scripts run that code first
from ansible.cli import CLI

import atexit
import cmd
import getpass
import readline
import os
import sys

from ansible import constants as C
from ansible import context
from ansible.cli.arguments import option_helpers as opt_help
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.module_utils.common.text.converters import to_native, to_text
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.parsing.splitter import parse_kv
from ansible.playbook.play import Play
from ansible.plugins.list import list_plugins
from ansible.plugins.loader import module_loader, fragment_loader
from ansible.utils import plugin_docs
from ansible.utils.color import stringc
from ansible._internal._datatag._tags import TrustedAsTemplate
from ansible.utils.display import Display

display = Display()


class ConsoleCLI(CLI, cmd.Cmd):
    """
       A REPL that allows for running ad-hoc tasks against a chosen inventory
       from a nice shell with built-in tab completion (based on dominis'
       ``ansible-shell``).

       It supports several commands, and you can modify its configuration at
       runtime:

       - ``cd [pattern]``: change host/group
         (you can use host patterns eg.: ``app*.dc*:!app01*``)
       - ``list``: list available hosts in the current path
       - ``list groups``: list groups included in the current path
       - ``become``: toggle the become flag
       - ``!``: forces shell module instead of the ansible module
         (``!yum update -y``)
       - ``verbosity [num]``: set the verbosity level
       - ``forks [num]``: set the number of forks
       - ``become_user [user]``: set the become_user
       - ``remote_user [user]``: set the remote_user
       - ``become_method [method]``: set the privilege escalation method
       - ``check [bool]``: toggle check mode
       - ``diff [bool]``: toggle diff mode
       - ``timeout [integer]``: set the timeout of tasks in seconds
         (0 to disable)
       - ``help [command/module]``: display documentation for
         the command or module
       - ``exit``: exit ``ansible-console``
    """

    name = 'ansible-console'
    modules = []  # type: list[str] | None
    ARGUMENTS = {'host-pattern': 'A name of a group in the inventory, a shell-like glob '
                                 'selecting hosts in inventory or any combination of the two separated by commas.'}

    # use specific to console, but fallback to highlight for backwards compatibility
    NORMAL_PROMPT = C.COLOR_CONSOLE_PROMPT or C.COLOR_HIGHLIGHT

    USES_CONNECTION = True

    def __init__(self, args):

        super(ConsoleCLI, self).__init__(args)

        self.intro = 'Welcome to the ansible console. Type help or ? to list commands.\n'

        self.groups = []
        self.hosts = []
        self.pattern = None
        self.variable_manager = None
        self.loader = None
        self.passwords = dict()

        self.cwd = '*'

        # Defaults for these are set from the CLI in run()
        self.remote_user = None
        self.become = None
        self.become_user = None
        self.become_method = None
        self.check_mode = None
        self.diff = None
        self.forks = None
        self.task_timeout = None
        self.collections = None

        cmd.Cmd.__init__(self)

    def init_parser(self):
        super(ConsoleCLI, self).init_parser(
            desc="REPL console for executing Ansible tasks.",
            epilog="This is not a live session/connection: each task is executed in the background and returns its results."
        )
        opt_help.add_runas_options(self.parser)
        opt_help.add_inventory_options(self.parser)
        opt_help.add_connect_options(self.parser)
        opt_help.add_check_options(self.parser)
        opt_help.add_vault_options(self.parser)
        opt_help.add_fork_options(self.parser)
        opt_help.add_module_options(self.parser)
        opt_help.add_basedir_options(self.parser)
        opt_help.add_runtask_options(self.parser)
        opt_help.add_tasknoplay_options(self.parser)

        # options unique to shell
        self.parser.add_argument('pattern', help='host pattern', metavar='pattern', default='all', nargs='?')
        self.parser.add_argument('--step', dest='step', action='store_true',
                                 help="one-step-at-a-time: confirm each task before running")

    def post_process_args(self, options):
        options = super(ConsoleCLI, self).post_process_args(options)
        display.verbosity = options.verbosity
        self.validate_conflicts(options, runas_opts=True, fork_opts=True)
        return options

    def get_names(self):
        return dir(self)

    def cmdloop(self):
        try:
            cmd.Cmd.cmdloop(self)

        except KeyboardInterrupt:
            self.cmdloop()

        except EOFError:
            self.display("[Ansible-console was exited]")
            self.do_exit(self)

    def set_prompt(self):
        login_user = self.remote_user or getpass.getuser()
        self.selected = self.inventory.list_hosts(self.cwd)
        prompt = "%s@%s (%d)[f:%s]" % (login_user, self.cwd, len(self.selected), self.forks)
        if self.become and self.become_user in [None, 'root']:
            prompt += "# "
            color = C.COLOR_ERROR
        else:
            prompt += "$ "
            color = self.NORMAL_PROMPT
        self.prompt = stringc(prompt, color, wrap_nonvisible_chars=True)

    def list_modules(self):
        return list_plugins('module', self.collections)

    def default(self, line, forceshell=False):
        """ actually runs modules """
        if line.startswith("#"):
            return False

        if not self.cwd:
            display.error("No host found")
            return False

        # defaults
        module = 'shell'
        module_args = line

        if forceshell is not True:
            possible_module, *possible_args = line.split()
            if module_loader.find_plugin(possible_module):
                # we found module!
                module = possible_module
                if possible_args:
                    module_args = ' '.join(possible_args)
                else:
                    module_args = ''

        module_args = TrustedAsTemplate().tag(module_args)

        if self.callback:
            cb = self.callback
        elif C.DEFAULT_LOAD_CALLBACK_PLUGINS and C.DEFAULT_STDOUT_CALLBACK != 'default':
            cb = C.DEFAULT_STDOUT_CALLBACK
        else:
            cb = 'minimal'

        result = None
        try:
            check_raw = module in C._ACTION_ALLOWS_RAW_ARGS
            task = dict(action=dict(module=module, args=parse_kv(module_args, check_raw=check_raw)), timeout=self.task_timeout)
            play_ds = dict(
                name="Ansible Shell",
                hosts=self.cwd,
                gather_facts='no',
                tasks=[task],
                remote_user=self.remote_user,
                become=self.become,
                become_user=self.become_user,
                become_method=self.become_method,
                check_mode=self.check_mode,
                diff=self.diff,
                collections=self.collections,
            )
            play = Play().load(play_ds, variable_manager=self.variable_manager, loader=self.loader)
        except Exception as e:
            display.error(u"Unable to build command: %s" % to_text(e))
            return False

        try:
            # now create a task queue manager to execute the play
            self._tqm = None
            try:
                self._tqm = TaskQueueManager(
                    inventory=self.inventory,
                    variable_manager=self.variable_manager,
                    loader=self.loader,
                    passwords=self.passwords,
                    stdout_callback_name=cb,
                    run_additional_callbacks=C.DEFAULT_LOAD_CALLBACK_PLUGINS,
                    run_tree=False,
                    forks=self.forks,
                )

                result = self._tqm.run(play)
                display.debug(result)
            finally:
                if self._tqm:
                    self._tqm.cleanup()
                if self.loader:
                    self.loader.cleanup_all_tmp_files()

            if result is None:
                display.error("No hosts found")
                return False
        except KeyboardInterrupt:
            display.error('User interrupted execution')
            return False
        except Exception as ex:
            display.error(ex)
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

    def help_shell(self):
        display.display("You can run shell commands through the shell module.")

    def do_forks(self, arg):
        """Set the number of forks"""
        if arg:
            try:
                forks = int(arg)
            except TypeError:
                display.error('Invalid argument for "forks"')
                self.usage_forks()

            if forks > 0:
                self.forks = forks
                self.set_prompt()

            else:
                display.display('forks must be greater than or equal to 1')
        else:
            self.usage_forks()

    def help_forks(self):
        display.display("Set the number of forks to use per task")
        self.usage_forks()

    def usage_forks(self):
        display.display('Usage: forks <number>')

    do_serial = do_forks
    help_serial = help_forks

    def do_collections(self, arg):
        """Set list of collections for 'short name' usage"""
        if arg in ('', 'none'):
            self.collections = None
        elif not arg:
            self.usage_collections()
        else:
            collections = arg.split(',')
            for collection in collections:
                if self.collections is None:
                    self.collections = []
                self.collections.append(collection.strip())

        if self.collections:
            display.v('Collections name search is set to: %s' % ', '.join(self.collections))
        else:
            display.v('Collections name search is using defaults')

    def help_collections(self):
        display.display("Set the collection name search path when using short names for plugins")
        self.usage_collections()

    def usage_collections(self):
        display.display('Usage: collections <collection1>[, <collection2> ...]\n Use empty quotes or "none" to reset to default.\n')

    def do_verbosity(self, arg):
        """Set verbosity level"""
        if not arg:
            display.display('Usage: verbosity <number>')
        else:
            try:
                display.verbosity = int(arg)
                display.v('verbosity level set to %s' % arg)
            except (TypeError, ValueError) as e:
                display.error('The verbosity must be a valid integer: %s' % to_text(e))

    def help_verbosity(self):
        display.display("Set the verbosity level, equivalent to -v for 1 and -vvvv for 4.")

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
            self.cwd = '*'
        elif arg in '/*':
            self.cwd = 'all'
        elif self.inventory.get_hosts(arg):
            self.cwd = arg
        else:
            display.display("no host matched")

        self.set_prompt()

    def help_cd(self):
        display.display("Change active host/group. ")
        self.usage_cd()

    def usage_cd(self):
        display.display("Usage: cd <group>|<host>|<host pattern>")

    def do_list(self, arg):
        """List the hosts in the current group"""
        if not arg:
            for host in self.selected:
                display.display(host.name)
        elif arg == 'groups':
            for group in self.groups:
                display.display(group)
        else:
            display.error('Invalid option passed to "list"')
            self.help_list()

    def help_list(self):
        display.display("List the hosts in the current group or a list of groups if you add 'groups'.")

    def do_become(self, arg):
        """Toggle whether plays run with become"""
        if arg:
            self.become = boolean(arg, strict=False)
            display.v("become changed to %s" % self.become)
            self.set_prompt()
        else:
            display.display("Please specify become value, e.g. `become yes`")

    def help_become(self):
        display.display("Toggle whether the tasks are run with become")

    def do_remote_user(self, arg):
        """Given a username, set the remote user plays are run by"""
        if arg:
            self.remote_user = arg
            self.set_prompt()
        else:
            display.display("Please specify a remote user, e.g. `remote_user root`")

    def help_remote_user(self):
        display.display("Set the user for use as login to the remote target")

    def do_become_user(self, arg):
        """Given a username, set the user that plays are run by when using become"""
        if arg:
            self.become_user = arg
        else:
            display.display("Please specify a user, e.g. `become_user jenkins`")
            display.v("Current user is %s" % self.become_user)
        self.set_prompt()

    def help_become_user(self):
        display.display("Set the user for use with privilege escalation (which remote user attempts to 'become' when become is enabled)")

    def do_become_method(self, arg):
        """Given a become_method, set the privilege escalation method when using become"""
        if arg:
            self.become_method = arg
            display.v("become_method changed to %s" % self.become_method)
        else:
            display.display("Please specify a become_method, e.g. `become_method su`")
            display.v("Current become_method is %s" % self.become_method)

    def help_become_method(self):
        display.display("Set the privilege escalation plugin to use when become is enabled")

    def do_check(self, arg):
        """Toggle whether plays run with check mode"""
        if arg:
            self.check_mode = boolean(arg, strict=False)
            display.display("check mode changed to %s" % self.check_mode)
        else:
            display.display("Please specify check mode value, e.g. `check yes`")
            display.v("check mode is currently %s." % self.check_mode)

    def help_check(self):
        display.display("Toggle check_mode for the tasks")

    def do_diff(self, arg):
        """Toggle whether plays run with diff"""
        if arg:
            self.diff = boolean(arg, strict=False)
            display.display("diff mode changed to %s" % self.diff)
        else:
            display.display("Please specify a diff value , e.g. `diff yes`")
            display.v("diff mode is currently %s" % self.diff)

    def help_diff(self):
        display.display("Toggle diff output for the tasks")

    def do_timeout(self, arg):
        """Set the timeout"""
        if arg:
            try:
                timeout = int(arg)
                if timeout < 0:
                    display.error('The timeout must be greater than or equal to 1, use 0 to disable')
                else:
                    self.task_timeout = timeout
            except (TypeError, ValueError) as e:
                display.error('The timeout must be a valid positive integer, or 0 to disable: %s' % to_text(e))
        else:
            self.usage_timeout()

    def help_timeout(self):
        display.display("Set task timeout in seconds")
        self.usage_timeout()

    def usage_timeout(self):
        display.display('Usage: timeout <seconds>')

    def do_exit(self, args):
        """Exits from the console"""
        sys.stdout.write('\nAnsible-console was exited.\n')
        return -1

    def help_exit(self):
        display.display("LEAVE!")

    do_EOF = do_exit
    help_EOF = help_exit

    def helpdefault(self, module_name):
        if module_name:
            in_path = module_loader.find_plugin(module_name)
            if in_path:
                oc, a, _dummy1, _dummy2 = plugin_docs.get_docstring(in_path, fragment_loader)
                if oc:
                    display.display(oc['short_description'])
                    display.display('Parameters:')
                    for opt in oc['options'].keys():
                        display.display('  ' + stringc(opt, self.NORMAL_PROMPT) + ' ' + oc['options'][opt]['description'][0])
                else:
                    display.error('No documentation found for %s.' % module_name)
            else:
                display.error('%s is not a valid command, use ? to list all valid commands.' % module_name)

    def help_help(self):
        display.warning("Don't be redundant!")

    def complete_cd(self, text, line, begidx, endidx):
        mline = line.partition(' ')[2]
        offs = len(mline) - len(text)

        if self.cwd in ('all', '*', '\\'):
            completions = self.hosts + self.groups
        else:
            completions = [x.name for x in self.inventory.list_hosts(self.cwd)]

        return [to_native(s)[offs:] for s in completions if to_native(s).startswith(to_native(mline))]

    def completedefault(self, text, line, begidx, endidx):
        if line.split()[0] in self.list_modules():
            mline = line.split(' ')[-1]
            offs = len(mline) - len(text)
            completions = self.module_args(line.split()[0])

            return [s[offs:] + '=' for s in completions if s.startswith(mline)]

    def module_args(self, module_name):
        in_path = module_loader.find_plugin(module_name)
        oc, a, _dummy1, _dummy2 = plugin_docs.get_docstring(in_path, fragment_loader, is_module=True)
        return list(oc['options'].keys())

    def run(self):

        super(ConsoleCLI, self).run()

        sshpass = None
        becomepass = None

        # hosts
        self.pattern = context.CLIARGS['pattern']
        self.cwd = self.pattern

        # Defaults from the command line
        self.remote_user = context.CLIARGS['remote_user']
        self.become = context.CLIARGS['become']
        self.become_user = context.CLIARGS['become_user']
        self.become_method = context.CLIARGS['become_method']
        self.check_mode = context.CLIARGS['check']
        self.diff = context.CLIARGS['diff']
        self.forks = context.CLIARGS['forks']
        self.task_timeout = context.CLIARGS['task_timeout']

        # set module path if needed
        if context.CLIARGS['module_path']:
            for path in context.CLIARGS['module_path']:
                if path:
                    module_loader.add_directory(path)

        # dynamically add 'canonical' modules as commands, aliases could be used and dynamically loaded
        self.modules = self.list_modules()
        for module in self.modules:
            setattr(self, 'do_' + module, lambda arg, module=module: self.default(module + ' ' + arg))
            setattr(self, 'help_' + module, lambda module=module: self.helpdefault(module))

        (sshpass, becomepass) = self.ask_passwords()
        self.passwords = {'conn_pass': sshpass, 'become_pass': becomepass}

        self.loader, self.inventory, self.variable_manager = self._play_prereqs()

        hosts = self.get_host_list(self.inventory, context.CLIARGS['subset'], self.pattern)

        self.groups = self.inventory.list_groups()
        self.hosts = [x.name for x in hosts]

        # This hack is to work around readline issues on a mac:
        #  http://stackoverflow.com/a/7116997/541202
        if 'libedit' in readline.__doc__:
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")

        histfile = os.path.join(os.path.expanduser("~"), ".ansible-console_history")
        try:
            readline.read_history_file(histfile)
        except OSError:
            pass

        atexit.register(readline.write_history_file, histfile)
        self.set_prompt()
        self.cmdloop()

    def __getattr__(self, name):
        """ handle not found to populate dynamically a module function if module matching name exists """
        attr = None

        if name.startswith('do_'):
            module = name.replace('do_', '')
            if module_loader.find_plugin(module):
                setattr(self, name, lambda arg, module=module: self.default(module + ' ' + arg))
                attr = object.__getattr__(self, name)
        elif name.startswith('help_'):
            module = name.replace('help_', '')
            if module_loader.find_plugin(module):
                setattr(self, name, lambda module=module: self.helpdefault(module))
                attr = object.__getattr__(self, name)

        if attr is None:
            raise AttributeError(f"{self.__class__} does not have a {name} attribute")

        return attr


def main(args=None):
    ConsoleCLI.cli_executor(args)


if __name__ == '__main__':
    main()
