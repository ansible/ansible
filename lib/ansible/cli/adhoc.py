# Copyright: (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible import constants as C
from ansible import context
from ansible.cli import CLI
from ansible.cli.arguments import optparse_helpers as opt_help
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.module_utils._text import to_text
from ansible.parsing.splitter import parse_kv
from ansible.playbook import Playbook
from ansible.playbook.play import Play
from ansible.utils.display import Display

display = Display()


class AdHocCLI(CLI):
    ''' is an extra-simple tool/framework/API for doing 'remote things'.
        this command allows you to define and run a single task 'playbook' against a set of hosts
    '''

    def init_parser(self):
        ''' create an options parser for bin/ansible '''
        super(AdHocCLI, self).init_parser(usage='%prog <host-pattern> [options]',
                                          desc="Define and run a single task 'playbook' against"
                                          " a set of hosts",
                                          epilog="Some modules do not make sense in Ad-Hoc (include,"
                                          " meta, etc)")

        opt_help.add_runas_options(self.parser)
        opt_help.add_inventory_options(self.parser)
        opt_help.add_async_options(self.parser)
        opt_help.add_output_options(self.parser)
        opt_help.add_connect_options(self.parser)
        opt_help.add_check_options(self.parser)
        opt_help.add_runtask_options(self.parser)
        opt_help.add_vault_options(self.parser)
        opt_help.add_fork_options(self.parser)
        opt_help.add_module_options(self.parser)
        opt_help.add_basedir_options(self.parser)

        # options unique to ansible ad-hoc
        self.parser.add_option('-a', '--args', dest='module_args',
                               help="module arguments", default=C.DEFAULT_MODULE_ARGS)
        self.parser.add_option('-m', '--module-name', dest='module_name',
                               help="module name to execute (default=%s)" % C.DEFAULT_MODULE_NAME,
                               default=C.DEFAULT_MODULE_NAME)

    def post_process_args(self, options, args):
        '''Post process and validate options for bin/ansible '''

        options, args = super(AdHocCLI, self).post_process_args(options, args)

        if len(args) < 1:
            raise AnsibleOptionsError("Missing target hosts")
        elif len(args) > 1:
            raise AnsibleOptionsError("Extraneous options or arguments")

        display.verbosity = options.verbosity
        self.validate_conflicts(options, runas_opts=True, vault_opts=True, fork_opts=True)

        return options, args

    def _play_ds(self, pattern, async_val, poll):
        check_raw = context.CLIARGS['module_name'] in ('command', 'win_command', 'shell', 'win_shell', 'script', 'raw')

        mytask = {'action': {'module': context.CLIARGS['module_name'], 'args': parse_kv(context.CLIARGS['module_args'], check_raw=check_raw)}}

        # avoid adding to tasks that don't support it, unless set, then give user an error
        if context.CLIARGS['module_name'] not in ('include_role', 'include_tasks') and any(frozenset((async_val, poll))):
            mytask['async_val'] = async_val
            mytask['poll'] = poll

        return dict(
            name="Ansible Ad-Hoc",
            hosts=pattern,
            gather_facts='no',
            tasks=[mytask])

    def run(self):
        ''' create and execute the single task playbook '''

        super(AdHocCLI, self).run()

        # only thing left should be host pattern
        pattern = to_text(context.CLIARGS['args'][0], errors='surrogate_or_strict')

        sshpass = None
        becomepass = None

        (sshpass, becomepass) = self.ask_passwords()
        passwords = {'conn_pass': sshpass, 'become_pass': becomepass}

        # get basic objects
        loader, inventory, variable_manager = self._play_prereqs()

        try:
            hosts = self.get_host_list(inventory, context.CLIARGS['subset'], pattern)
        except AnsibleError:
            if context.CLIARGS['subset']:
                raise
            else:
                hosts = []
                display.warning("No hosts matched, nothing to do")

        if context.CLIARGS['listhosts']:
            display.display('  hosts (%d):' % len(hosts))
            for host in hosts:
                display.display('    %s' % host)
            return 0

        if context.CLIARGS['module_name'] in C.MODULE_REQUIRE_ARGS and not context.CLIARGS['module_args']:
            err = "No argument passed to %s module" % context.CLIARGS['module_name']
            if pattern.endswith(".yml"):
                err = err + ' (did you mean to run ansible-playbook?)'
            raise AnsibleOptionsError(err)

        # Avoid modules that don't work with ad-hoc
        if context.CLIARGS['module_name'] in ('import_playbook',):
            raise AnsibleOptionsError("'%s' is not a valid action for ad-hoc commands"
                                      % context.CLIARGS['module_name'])

        play_ds = self._play_ds(pattern, context.CLIARGS['seconds'], context.CLIARGS['poll_interval'])
        play = Play().load(play_ds, variable_manager=variable_manager, loader=loader)

        # used in start callback
        playbook = Playbook(loader)
        playbook._entries.append(play)
        playbook._file_name = '__adhoc_playbook__'

        if self.callback:
            cb = self.callback
        elif context.CLIARGS['one_line']:
            cb = 'oneline'
        # Respect custom 'stdout_callback' only with enabled 'bin_ansible_callbacks'
        elif C.DEFAULT_LOAD_CALLBACK_PLUGINS and C.DEFAULT_STDOUT_CALLBACK != 'default':
            cb = C.DEFAULT_STDOUT_CALLBACK
        else:
            cb = 'minimal'

        run_tree = False
        if context.CLIARGS['tree']:
            C.DEFAULT_CALLBACK_WHITELIST.append('tree')
            C.TREE_DIR = context.CLIARGS['tree']
            run_tree = True

        # now create a task queue manager to execute the play
        self._tqm = None
        try:
            self._tqm = TaskQueueManager(
                inventory=inventory,
                variable_manager=variable_manager,
                loader=loader,
                passwords=passwords,
                stdout_callback=cb,
                run_additional_callbacks=C.DEFAULT_LOAD_CALLBACK_PLUGINS,
                run_tree=run_tree,
                forks=context.CLIARGS['forks'],
            )

            self._tqm.send_callback('v2_playbook_on_start', playbook)

            result = self._tqm.run(play)

            self._tqm.send_callback('v2_playbook_on_stats', self._tqm._stats)
        finally:
            if self._tqm:
                self._tqm.cleanup()
            if loader:
                loader.cleanup_all_tmp_files()

        return result
