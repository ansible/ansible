# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys

from ansible import constants as C
from ansible.cli import CLI
from ansible.errors import AnsibleOptionsError, AnsibleParserError
from ansible.module_utils._text import to_text
from ansible.playbook import Playbook
from ansible.playbook.helpers import load_list_of_roles
from ansible.playbook.play import Play
from ansible.plugins.loader import get_all_plugin_loaders
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.parsing.splitter import parse_kv

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


def _play_ds(pattern, role_name, role_args_string, extra_vars, async_val, poll):
    role_args = parse_kv(role_args_string, check_raw=False)

    # TODO: use varman here? probably at least merge_dict
    role_params = {}

    role_params.update(role_args)

    # TODO: cli flag to set gather_facts ?
    return {'name': "Ansible Role",
            'hosts': pattern,
            # 'gather_facts': 'no',
            'tasks': [
                # TODO: is there anything that would be useful to run
                #       before or after a role? Maybe something to format
                #       the invocation and/or results (if it could make for
                #       better uxd that just the default callback handling)
                {'action': {'module': 'include_role',
                            'name': role_name,
                            },
                 'vars': role_params,
                 'async_val': async_val,
                 'poll': poll}
            ]
            }


class RoleCLI(CLI):
    def parse(self):
        ''' create an options parser for bin/ansible '''

        self.parser = CLI.base_parser(
            usage="usage: %%prog [%s] [--help] [options] ..." % "|".join(self.VALID_ACTIONS),
            runas_opts=True,
            inventory_opts=True,
            async_opts=True,
            output_opts=True,
            connect_opts=True,
            check_opts=True,
            runtask_opts=True,
            vault_opts=True,
            fork_opts=True,
            module_opts=True,
            basedir_opts=True,
            epilog="\nSee '%s <command> --help' for more information on a specific command.\n\n" % os.path.basename(sys.argv[0]),
            desc="Perform various Role related operations.",
        )

        # common
        self.parser.add_option('-a', '--args', dest='role_args_string',
                               help="role arguments", default=C.DEFAULT_ROLE_ARGS)
        self.parser.add_option('-A', '--arg-spec-name', dest='arg_spec_name',
                               help="The name of a argument_spec to use", default='main')
        self.parser.add_option('-r', '--role', dest='role_name',
                               help="role name to execute",
                               default=None)

        super(RoleCLI, self).parse()

        if len(self.args) < 1:
            raise AnsibleOptionsError("Missing target hosts")
        elif len(self.args) > 1:
            raise AnsibleOptionsError("Extraneous options or arguments")

        if not self.options.role_name:
            raise AnsibleOptionsError("-r/--role requires a role name")

        display.verbosity = self.options.verbosity
        self.validate_conflicts(runas_opts=True, vault_opts=True, fork_opts=True)

    def run(self):
        super(RoleCLI, self).run()

        # only thing left should be host pattern
        pattern = to_text(self.args[0], errors='surrogate_or_strict')

        sshpass = None
        becomepass = None

        self.normalize_become_options()
        (sshpass, becomepass) = self.ask_passwords()
        passwords = {'conn_pass': sshpass, 'become_pass': becomepass}

        # dynamically load any plugins
        get_all_plugin_loaders()

        loader, inventory, variable_manager = self._play_prereqs(self.options)

        try:
            role_includes = load_list_of_roles([self.options.role_name], play=None, variable_manager=variable_manager, loader=loader)
        except AssertionError as e:
            raise AnsibleParserError("A malformed role declaration was encountered.", obj=self._ds, orig_exc=e)

        for role_include in role_includes:
            display.debug('cli.role.run loaded role_include: %s' % role_include)

        extra_vars = variable_manager.extra_vars

        play_ds = _play_ds(pattern, self.options.role_name, self.options.role_args_string,
                           extra_vars, self.options.seconds, self.options.poll_interval)

        play = Play().load(play_ds, variable_manager=variable_manager, loader=loader)

        # used in start callback
        playbook = Playbook(loader)
        playbook._entries.append(play)
        playbook._file_name = '__role_playbook__'

        cb = C.DEFAULT_STDOUT_CALLBACK
        if self.callback:
            cb = self.callback

        # now create a task queue manager to execute the play
        self._tqm = None
        try:
            self._tqm = TaskQueueManager(
                inventory=inventory,
                variable_manager=variable_manager,
                loader=loader,
                options=self.options,
                passwords=passwords,
                stdout_callback=cb,
                run_additional_callbacks=C.DEFAULT_LOAD_CALLBACK_PLUGINS,
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
