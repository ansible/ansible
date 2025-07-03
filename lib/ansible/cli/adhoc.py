#!/usr/bin/env python
# Copyright: (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# PYTHON_ARGCOMPLETE_OK

from __future__ import annotations

import json

# ansible.cli needs to be imported first, to ensure the source bin/* scripts run that code first
from ansible.cli import CLI
from ansible import constants as C
from ansible import context
from ansible.cli.arguments import option_helpers as opt_help
from ansible.errors import AnsibleError, AnsibleOptionsError, AnsibleParserError
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.module_utils.common.text.converters import to_text
from ansible.parsing.splitter import parse_kv
from ansible.playbook import Playbook
from ansible.playbook.play import Play
from ansible._internal._datatag._tags import Origin
from ansible.utils.display import Display
from ansible._internal._json._profiles import _legacy

display = Display()


class AdHocCLI(CLI):
    """ is an extra-simple tool/framework/API for doing 'remote things'.
        this command allows you to define and run a single task 'playbook' against a set of hosts
    """

    name = 'ansible'

    USES_CONNECTION = True

    def init_parser(self):
        """ create an options parser for bin/ansible """
        super(AdHocCLI, self).init_parser(usage='%prog <host-pattern> [options]',
                                          desc="Define and run a single task 'playbook' against a set of hosts",
                                          epilog="Some actions do not make sense in Ad-Hoc (include, meta, etc)")

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
        opt_help.add_tasknoplay_options(self.parser)

        # options unique to ansible ad-hoc
        self.parser.add_argument('-a', '--args', dest='module_args',
                                 help="The action's options in space separated k=v format: -a 'opt1=val1 opt2=val2' "
                                      "or a json string: -a '{\"opt1\": \"val1\", \"opt2\": \"val2\"}'",
                                 default=C.DEFAULT_MODULE_ARGS)
        self.parser.add_argument('-m', '--module-name', dest='module_name',
                                 help="Name of the action to execute (default=%s)" % C.DEFAULT_MODULE_NAME,
                                 default=C.DEFAULT_MODULE_NAME)
        self.parser.add_argument('args', metavar='pattern', help='host pattern')

    def post_process_args(self, options):
        """Post process and validate options for bin/ansible """

        options = super(AdHocCLI, self).post_process_args(options)

        display.verbosity = options.verbosity
        self.validate_conflicts(options, runas_opts=True, fork_opts=True)

        return options

    def _play_ds(self, pattern, async_val, poll):
        check_raw = context.CLIARGS['module_name'] in C.MODULE_REQUIRE_ARGS

        module_args_raw = context.CLIARGS['module_args']
        module_args = None
        if module_args_raw and module_args_raw.startswith('{') and module_args_raw.endswith('}'):
            try:
                module_args = json.loads(module_args_raw, cls=_legacy.Decoder)
            except AnsibleParserError:
                pass

        if not module_args:
            module_args = parse_kv(module_args_raw, check_raw=check_raw)

        mytask = dict(
            action=context.CLIARGS['module_name'],
            args=module_args,
            timeout=context.CLIARGS['task_timeout'],
        )

        mytask = Origin(description=f'<adhoc {context.CLIARGS["module_name"]!r} task>').tag(mytask)

        # avoid adding to tasks that don't support it, unless set, then give user an error
        if context.CLIARGS['module_name'] not in C._ACTION_ALL_INCLUDE_ROLE_TASKS and any(frozenset((async_val, poll))):
            mytask['async_val'] = async_val
            mytask['poll'] = poll

        return dict(
            name="Ansible Ad-Hoc",
            hosts=pattern,
            gather_facts='no',
            tasks=[mytask])

    def run(self):
        """ create and execute the single task playbook """

        super(AdHocCLI, self).run()

        # only thing left should be host pattern
        pattern = to_text(context.CLIARGS['args'], errors='surrogate_or_strict')

        # handle password prompts
        sshpass = None
        becomepass = None

        (sshpass, becomepass) = self.ask_passwords()
        passwords = {'conn_pass': sshpass, 'become_pass': becomepass}

        # get basic objects
        loader, inventory, variable_manager = self._play_prereqs()

        # get list of hosts to execute against
        try:
            hosts = self.get_host_list(inventory, context.CLIARGS['subset'], pattern)
        except AnsibleError:
            if context.CLIARGS['subset']:
                raise
            else:
                hosts = []
                display.warning("No hosts matched, nothing to do")

        # just listing hosts?
        if context.CLIARGS['listhosts']:
            display.display('  hosts (%d):' % len(hosts))
            for host in hosts:
                display.display('    %s' % host)
            return 0

        # verify we have arguments if we know we need em
        if context.CLIARGS['module_name'] in C.MODULE_REQUIRE_ARGS and not context.CLIARGS['module_args']:
            err = "No argument passed to %s module" % context.CLIARGS['module_name']
            if pattern.endswith(".yml"):
                err = err + ' (did you mean to run ansible-playbook?)'
            raise AnsibleOptionsError(err)

        # Avoid modules that don't work with ad-hoc
        if context.CLIARGS['module_name'] in C._ACTION_IMPORT_PLAYBOOK:
            raise AnsibleOptionsError("'%s' is not a valid action for ad-hoc commands"
                                      % context.CLIARGS['module_name'])

        # construct playbook objects to wrap task
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
            C.CALLBACKS_ENABLED.append('tree')
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
                stdout_callback_name=cb,
                run_additional_callbacks=C.DEFAULT_LOAD_CALLBACK_PLUGINS,
                run_tree=run_tree,
                forks=context.CLIARGS['forks'],
            )

            self._tqm.load_callbacks()
            self._tqm.send_callback('v2_playbook_on_start', playbook)

            result = self._tqm.run(play)

            self._tqm.send_callback('v2_playbook_on_stats', self._tqm._stats)
        finally:
            if self._tqm:
                self._tqm.cleanup()
            if loader:
                loader.cleanup_all_tmp_files()

        return result


def main(args=None):
    AdHocCLI.cli_executor(args)


if __name__ == '__main__':
    main()
