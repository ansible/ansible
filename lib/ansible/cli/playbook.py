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
import sys

from ansible import constants as C
from ansible.cli import CLI
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.inventory import Inventory
from ansible.parsing import DataLoader
from ansible.parsing.splitter import parse_kv
from ansible.playbook import Playbook
from ansible.playbook.task import Task
from ansible.utils.display import Display
from ansible.utils.unicode import to_unicode
from ansible.utils.vars import combine_vars
from ansible.utils.vault import read_vault_file
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
            diff_opts=True,
            runtask_opts=True,
            vault_opts=True,
            fork_opts=True,
        )

        # ansible playbook specific opts
        parser.add_option('--list-tasks', dest='listtasks', action='store_true',
            help="list all tasks that would be executed")
        parser.add_option('--step', dest='step', action='store_true',
            help="one-step-at-a-time: confirm each task before running")
        parser.add_option('--start-at-task', dest='start_at',
            help="start the playbook at the task matching this name")
        parser.add_option('--list-tags', dest='listtags', action='store_true',
            help="list all available tags")

        self.options, self.args = parser.parse_args()


        self.parser = parser

        if len(self.args) == 0:
            raise AnsibleOptionsError("You must specify a playbook file to run")

        self.display.verbosity = self.options.verbosity
        self.validate_conflicts(runas_opts=True, vault_opts=True)

    def run(self):

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
            vault_pass = read_vault_file(self.options.vault_password_file)
        elif self.options.ask_vault_pass:
            vault_pass = self.ask_vault_passwords(ask_vault_pass=True, ask_new_vault_pass=False, confirm_new=False)[0]

        loader = DataLoader(vault_password=vault_pass)

        extra_vars = {}
        for extra_vars_opt in self.options.extra_vars:
            extra_vars_opt = to_unicode(extra_vars_opt, errors='strict')
            if extra_vars_opt.startswith(u"@"):
                # Argument is a YAML file (JSON is a subset of YAML)
                data = loader.load_from_file(extra_vars_opt[1:])
            elif extra_vars_opt and extra_vars_opt[0] in u'[{':
                # Arguments as YAML
                data = loader.load(extra_vars_opt)
            else:
                # Arguments as Key-value
                data = parse_kv(extra_vars_opt)
            extra_vars = combine_vars(extra_vars, data)

        # FIXME: this should be moved inside the playbook executor code
        only_tags = self.options.tags.split(",")
        skip_tags = self.options.skip_tags
        if self.options.skip_tags is not None:
            skip_tags = self.options.skip_tags.split(",")

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
        variable_manager.extra_vars = extra_vars

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

                self.display.display('\nplaybook: %s\n' % p['playbook'])
                for play in p['plays']:
                    if self.options.listhosts:
                        self.display.display("\n  %s (%s): host count=%d" % (play['name'], play['pattern'], len(play['hosts'])))
                        for host in play['hosts']:
                            self.display.display("    %s" % host)
                    if self.options.listtasks: #TODO: do we want to display block info?
                        self.display.display("\n  %s" % (play['name']))
                        for task in play['tasks']:
                            self.display.display("    %s" % task)
                    if self.options.listtags: #TODO: fix once we figure out block handling above
                        self.display.display("\n  %s: tags count=%d" % (play['name'], len(play['tags'])))
                        for tag in play['tags']:
                            self.display.display("    %s" % tag)
            return 0
        else:
            return results
