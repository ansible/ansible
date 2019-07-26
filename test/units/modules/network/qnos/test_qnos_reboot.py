#
# (c) 2016 Red Hat Inc.
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch, MagicMock
from ansible.modules.network.qnos import qnos_reboot
from units.modules.utils import set_module_args
from .qnos_module import TestQnosModule, load_fixture

class TestQnosRebootModule(TestQnosModule):

    module = qnos_reboot

    def setUp(self):
        super(TestQnosRebootModule, self).setUp()
        self.mock_run_reload = patch('ansible.modules.network.qnos.qnos_reboot.run_reload')
        self.run_reload = self.mock_run_reload.start()

    def tearDown(self):
        super(TestQnosRebootModule, self).tearDown()
        self.mock_run_reload.stop()

    def load_fixtures(self, commands=None):

        def load_from_file(*args, **kwargs):
            module = args
            output = list()
            if kwargs['save']==True:
                filename = 'qnos_reboot_save_yes'
            else:
                filename = 'qnos_reboot_save_no'
            output.append(load_fixture(filename))
            return output

        self.run_reload.side_effect = load_from_file

    def test_qnos_reboot_save_no(self):
        set_module_args(dict(confirm='yes', save='no'))
        self.execute_module(changed=False)

    def test_qnos_reboot_check_return_var(self):
        set_module_args(dict(confirm='yes', save='yes'))
        result = self.execute_module(changed=True)
        self.assertTrue(result['response'][0].find("successfully") >= 0)

    def test_qnos_reboot_check_return_var_nosave(self):
        set_module_args(dict(confirm='yes', save='no'))
        result = self.execute_module(changed=False)
        self.assertTrue(result['response'][0].find("Configuration Not Saved") >= 0)
