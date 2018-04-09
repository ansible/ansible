# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

########################################################

import os

from ansible import constants as C
from ansible.cli import CLI
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.module_utils._text import to_text
from ansible.parsing.splitter import parse_kv
from ansible.playbook import Playbook
from ansible.playbook.play import Play
from ansible.plugins.loader import get_all_plugin_loaders

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


########################################################

class AdHocCLI(CLI):
    ''' is an extra-simple tool/framework/API for doing 'remote things'.
        this command allows you to define and run a single task 'playbook' against a set of hosts
    '''

    def parse(self):
        ''' create an options parser for bin/ansible '''

        self.parser = CLI.base_parser(
            usage='%prog <host-pattern> [options]',
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
            desc="Define and run a single task 'playbook' against a set of hosts",
            epilog="Some modules do not make sense in Ad-Hoc (include, meta, etc)",
        )

        # options unique to ansible ad-hoc
        self.parser.add_option('-a', '--args', dest='module_args',
                               help="module arguments", default=C.DEFAULT_MODULE_ARGS)
        self.parser.add_option('-m', '--module-name', dest='module_name',
                               help="module name to execute (default=%s)" % C.DEFAULT_MODULE_NAME,
                               default=C.DEFAULT_MODULE_NAME)

        super(AdHocCLI, self).parse()

        if len(self.args) < 1:
            raise AnsibleOptionsError("Missing target hosts")
        elif len(self.args) > 1:
            raise AnsibleOptionsError("Extraneous options or arguments")

        display.verbosity = self.options.verbosity
        self.validate_conflicts(runas_opts=True, vault_opts=True, fork_opts=True)

    def _play_ds(self, pattern, async_val, poll):
        check_raw = self.options.module_name in ('command', 'win_command', 'shell', 'win_shell', 'script', 'raw')
        return dict(
            name="Ansible Ad-Hoc",
            hosts=pattern,
            gather_facts='no',
            tasks=[dict(action=dict(module=self.options.module_name, args=parse_kv(self.options.module_args, check_raw=check_raw)), async_val=async_val,
                        poll=poll)]
        )

    def run(self):
        ''' create and execute the single task playbook '''

        super(AdHocCLI, self).run()

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
            hosts = CLI.get_host_list(inventory, self.options.subset, pattern)
        except AnsibleError:
            if self.options.subset:
                raise
            else:
                hosts = []
                display.warning("No hosts matched, nothing to do")

        if self.options.listhosts:
            display.display('  hosts (%d):' % len(hosts))
            for host in hosts:
                display.display('    %s' % host)
            return 0

        if self.options.module_name in C.MODULE_REQUIRE_ARGS and not self.options.module_args:
            err = "No argument passed to %s module" % self.options.module_name
            if pattern.endswith(".yml"):
                err = err + ' (did you mean to run ansible-playbook?)'
            raise AnsibleOptionsError(err)

        # Avoid modules that don't work with ad-hoc
        if self.options.module_name.startswith(('include', 'import_')):
            raise AnsibleOptionsError("'%s' is not a valid action for ad-hoc commands" % self.options.module_name)

        play_ds = self._play_ds(pattern, self.options.seconds, self.options.poll_interval)
        play = Play().load(play_ds, variable_manager=variable_manager, loader=loader)

        # used in start callback
        playbook = Playbook(loader)
        playbook._entries.append(play)
        playbook._file_name = '__adhoc_playbook__'

        if self.callback:
            cb = self.callback
        elif self.options.one_line:
            cb = 'oneline'
        # Respect custom 'stdout_callback' only with enabled 'bin_ansible_callbacks'
        elif C.DEFAULT_LOAD_CALLBACK_PLUGINS and C.DEFAULT_STDOUT_CALLBACK != 'default':
            cb = C.DEFAULT_STDOUT_CALLBACK
        else:
            cb = 'minimal'

        run_tree = False
        if self.options.tree:
            C.DEFAULT_CALLBACK_WHITELIST.append('tree')
            C.TREE_DIR = self.options.tree
            run_tree = True

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
                run_tree=run_tree,
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
