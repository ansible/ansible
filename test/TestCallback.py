# (C) 2013, Michael Scherer, <misc@zarb.org>

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


import os
import unittest
import subprocess

# if you change here, also change in the plugin
FILE_DISABLE = '/tmp/ansible_test_disable'
FILE_RUN = '/tmp/ansible_test_finish'


class TestInventory(unittest.TestCase):

    def setUp(self):
        self.cwd = os.getcwd()
        os.chdir(os.path.join(os.path.dirname(__file__), 'test_callbacks'))

    def clean_file(self):
        if os.path.exists(FILE_RUN):
            os.unlink(FILE_RUN)
        if os.path.exists(FILE_DISABLE):
            os.unlink(FILE_DISABLE)

    def tearDown(self):
        os.chdir(self.cwd)

    def run_ansible_playbook(self):
        subprocess.call(('source ../../hacking/env-setup 2>&1 >/dev/null;'
                         'ansible-playbook -i "127.0.0.1," test_playbook.yml 2>&1 >/dev/null'),
                        shell=True, executable='/bin/bash')

    def test_callback(self):
        self.clean_file()

        self.run_ansible_playbook()
        assert os.path.exists(FILE_RUN)
        self.clean_file()

    def test_callback_disabled(self):
        self.clean_file()
        open(FILE_DISABLE, 'w').close()

        self.run_ansible_playbook()
        assert not os.path.exists(FILE_RUN)

        self.clean_file()
