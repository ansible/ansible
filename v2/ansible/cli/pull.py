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
import sys

from ansible import constants as C
from ansible.errors import *
from ansible.cli import CLI
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory import Inventory
from ansible.parsing import DataLoader
from ansible.parsing.splitter import parse_kv
from ansible.playbook.play import Play
from ansible.utils.display import Display
from ansible.utils.vault import read_vault_file
from ansible.vars import VariableManager

########################################################

class PullCLI(CLI):
    ''' code behind ansible ad-hoc cli'''

    def parse(self):
        ''' create an options parser for bin/ansible '''

        self.parser = CLI.base_parser(
            usage='%prog <host-pattern> [options]',
            runas_opts=True,
            async_opts=True,
            output_opts=True,
            connect_opts=True,
            check_opts=True,
            runtask_opts=True,
            vault_opts=True,
        )

        # options unique to pull

        self.options, self.args = self.parser.parse_args()

        if len(self.args) != 1:
            raise AnsibleOptionsError("Missing target hosts")

        self.display.verbosity = self.options.verbosity
        self.validate_conflicts()

        return True


    def run(self):
        ''' use Runner lib to do SSH things '''

        raise AnsibleError("Not ported to v2 yet")
