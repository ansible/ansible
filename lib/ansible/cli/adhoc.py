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
from ansible.inventory import Inventory
from ansible.parsing.dataloader import DataLoader
from ansible.parsing.splitter import parse_kv
from ansible.playbook.play import Play
from ansible.plugins import get_all_plugin_loaders
from ansible.utils.vars import load_extra_vars
from ansible.vars import VariableManager

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


########################################################

class AdHocCLI(CLI):
    ''' code behind ansible ad-hoc cli'''

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
        )

        # options unique to ansible ad-hoc
        self.parser.add_option('-a', '--args', dest='module_args',
            help="module arguments", default=C.DEFAULT_MODULE_ARGS)
        self.parser.add_option('-m', '--module-name', dest='module_name',
            help="module name to execute (default=%s)" % C.DEFAULT_MODULE_NAME,
            default=C.DEFAULT_MODULE_NAME)

        self.options, self.args = self.parser.parse_args(self.args[1:])

        if len(self.args) != 1:
            raise AnsibleOptionsError("Missing target hosts")

        display.verbosity = self.options.verbosity
        self.validate_conflicts(runas_opts=True, vault_opts=True, fork_opts=True)

        return True

    def _play_ds(self, pattern, async, poll):
        return dict(
            name = "Ansible Ad-Hoc",
            hosts = pattern,
            gather_facts = 'no',
            tasks = [ dict(action=dict(module=self.options.module_name, args=parse_kv(self.options.module_args)), async=async, poll=poll) ]
        )

    def run(self):
        ''' use Runner lib to do SSH things '''

        super(AdHocCLI, self).run()

        # only thing left should be host pattern
        pattern = self.args[0]

        # ignore connection password cause we are local
        if self.options.connection == "local":
            self.options.ask_pass = False

        sshpass    = None
        becomepass = None
        vault_pass = None

        self.normalize_become_options()
        (sshpass, becomepass) = self.ask_passwords()
        passwords = { 'conn_pass': sshpass, 'become_pass': becomepass }

        loader = DataLoader()

        if self.options.vault_password_file:
            # read vault_pass from a file
            vault_pass = CLI.read_vault_password_file(self.options.vault_password_file, loader=loader)
            loader.set_vault_password(vault_pass)
        elif self.options.ask_vault_pass:
            vault_pass = self.ask_vault_passwords()[0]
            loader.set_vault_password(vault_pass)

        variable_manager = VariableManager()
        variable_manager.extra_vars = load_extra_vars(loader=loader, options=self.options)

        inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list=self.options.inventory)
        variable_manager.set_inventory(inventory)

        no_hosts = False
        if len(inventory.list_hosts(pattern)) == 0:
            # Empty inventory
            display.warning("provided hosts list is empty, only localhost is available")
            no_hosts = True

        inventory.subset(self.options.subset)
        hosts = inventory.list_hosts(pattern)
        if len(hosts) == 0 and no_hosts is False:
            # Invalid limit
            raise AnsibleError("Specified --limit does not match any hosts")

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

        # dynamically load any plugins from the playbook directory
        for name, obj in get_all_plugin_loaders():
            if obj.subdir:
                plugin_path = os.path.join('.', obj.subdir)
                if os.path.isdir(plugin_path):
                    obj.add_directory(plugin_path)

        play_ds = self._play_ds(pattern, self.options.seconds, self.options.poll_interval)
        play = Play().load(play_ds, variable_manager=variable_manager, loader=loader)

        if self.callback: 
            cb = self.callback
        elif self.options.one_line:
            cb = 'oneline'
        else:
            cb = 'minimal'

        run_tree=False
        if self.options.tree:
            C.DEFAULT_CALLBACK_WHITELIST.append('tree')
            C.TREE_DIR = self.options.tree
            run_tree=True

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

            result = self._tqm.run(play)
        finally:
            if self._tqm:
                self._tqm.cleanup()

        return result
