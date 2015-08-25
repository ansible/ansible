#!/usr/bin/env python

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

########################################################
import os
import stat

from ansible.cli import CLI
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.inventory import Inventory
from ansible.parsing import DataLoader
from ansible.utils.vars import load_extra_vars
from ansible.vars import VariableManager

#---------------------------------------------------------------------------------------------------

class PlaybookCLI(CLI):
    ''' code behind ansible playbook cli'''

    def parse(self):

        # create parser for CLI options
        parser = CLI.base_parser(
            usage = "%prog playbook.yml",
            connect_opts=True,
            meta_opts=True,
            runas_opts=True,
            subset_opts=True,
            check_opts=True,
            inventory_opts=True,
            runtask_opts=True,
            vault_opts=True,
            fork_opts=True,
            module_opts=True,
        )

        # ansible playbook specific opts
        parser.add_option('--list-tasks', dest='listtasks', action='store_true',
            help="list all tasks that would be executed")
        parser.add_option('--list-tags', dest='listtags', action='store_true',
            help="list all available tags")
        parser.add_option('--step', dest='step', action='store_true',
            help="one-step-at-a-time: confirm each task before running")
        parser.add_option('--start-at-task', dest='start_at_task',
            help="start the playbook at the task matching this name")

        self.options, self.args = parser.parse_args()


        self.parser = parser

        if len(self.args) == 0:
            raise AnsibleOptionsError("You must specify a playbook file to run")

        self.display.verbosity = self.options.verbosity
        self.validate_conflicts(runas_opts=True, vault_opts=True, fork_opts=True)

    def run(self):

        super(PlaybookCLI, self).run()

        # Note: slightly wrong, this is written so that implicit localhost
        # Manage passwords
        sshpass    = None
        becomepass    = None
        vault_pass = None
        passwords = {}

        # don't deal with privilege escalation or passwords when we don't need to
        if not self.options.listhosts and not self.options.listtasks and not self.options.listtags and not self.options.syntax:
            self.normalize_become_options()
            (sshpass, becomepass) = self.ask_passwords()
            passwords = { 'conn_pass': sshpass, 'become_pass': becomepass }

        if self.options.vault_password_file:
            # read vault_pass from a file
            vault_pass = CLI.read_vault_password_file(self.options.vault_password_file)
        elif self.options.ask_vault_pass:
            vault_pass = self.ask_vault_passwords(ask_vault_pass=True, ask_new_vault_pass=False, confirm_new=False)[0]

        loader = DataLoader(vault_password=vault_pass)

        # initial error check, to make sure all specified playbooks are accessible
        # before we start running anything through the playbook executor
        for playbook in self.args:
            if not os.path.exists(playbook):
                raise AnsibleError("the playbook: %s could not be found" % playbook)
            if not (os.path.isfile(playbook) or stat.S_ISFIFO(os.stat(playbook).st_mode)):
                raise AnsibleError("the playbook: %s does not appear to be a file" % playbook)

        # create the variable manager, which will be shared throughout
        # the code, ensuring a consistent view of global variables
        variable_manager = VariableManager()
        variable_manager.extra_vars = load_extra_vars(loader=loader, options=self.options)

        # create the inventory, and filter it based on the subset specified (if any)
        inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list=self.options.inventory)
        variable_manager.set_inventory(inventory)

        # (which is not returned in list_hosts()) is taken into account for
        # warning if inventory is empty.  But it can't be taken into account for
        # checking if limit doesn't match any hosts.  Instead we don't worry about
        # limit if only implicit localhost was in inventory to start with.
        #
        # Fix this when we rewrite inventory by making localhost a real host (and thus show up in list_hosts())
        no_hosts = False
        if len(inventory.list_hosts()) == 0:
            # Empty inventory
            self.display.warning("provided hosts list is empty, only localhost is available")
            no_hosts = True
        inventory.subset(self.options.subset)
        if len(inventory.list_hosts()) == 0 and no_hosts is False:
            # Invalid limit
            raise AnsibleError("Specified --limit does not match any hosts")

        # create the playbook executor, which manages running the plays via a task queue manager
        pbex = PlaybookExecutor(playbooks=self.args, inventory=inventory, variable_manager=variable_manager, loader=loader, display=self.display, options=self.options, passwords=passwords)

        results = pbex.run()

        if isinstance(results, list):
            for p in results:

                self.display.display('\nplaybook: %s' % p['playbook'])
                i = 1
                for play in p['plays']:
                    if play.name:
                        playname = play.name
                    else:
                        playname = '#' + str(i)

                    msg = "\n  PLAY: %s" % (playname)
                    mytags = set()
                    if self.options.listtags and play.tags:
                        mytags = mytags.union(set(play.tags))
                        msg += '    TAGS: [%s]' % (','.join(mytags))

                    if self.options.listhosts:
                        playhosts = set(inventory.get_hosts(play.hosts))
                        msg += "\n    pattern: %s\n    hosts (%d):" % (play.hosts, len(playhosts))
                        for host in playhosts:
                            msg += "\n      %s" % host

                    self.display.display(msg)

                    if self.options.listtags or self.options.listtasks:
                        taskmsg = '    tasks:'

                        for block in play.compile():
                            if not block.has_tasks():
                                continue

                            j = 1
                            for task in block.block:
                                taskmsg += "\n      %s" % task
                                if self.options.listtags and task.tags:
                                    taskmsg += "    TAGS: [%s]" % ','.join(mytags.union(set(task.tags)))
                                j = j + 1

                        self.display.display(taskmsg)

                    i = i + 1
            return 0
        else:
            return results
