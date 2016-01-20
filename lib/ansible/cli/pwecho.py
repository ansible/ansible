# (c) 2016, Joonas Aunola <joonas@aunola.fi>
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
#
# ansible-pwecho echoes the content of ANSIBLE_SSH_PASS environment
# variable.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys

from ansible.cli import CLI


class PwechoCLI(CLI):

    def __init__(self, args):
        super(PwechoCLI, self).__init__(args)

    def run(self):
        sys.stdout.write(os.getenv("ANSIBLE_SSH_PASS", ""))
        sys.stdout.flush()

    def parse(self):
        return
