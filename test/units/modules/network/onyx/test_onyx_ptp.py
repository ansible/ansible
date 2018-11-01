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

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_ptp_global
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxPtpModule(TestOnyxModule):

    module = onyx_ptp_global

    def setUp(self):
        self._ptp_enabled = True
        self._ntp_enabled = True
        super(TestOnyxPtpModule, self).setUp()

        self.mock_get_ptp_config = patch.object(onyx_ptp_global.OnyxPtpGlobalModule, "_show_ptp_config")
        self.get_ptp_config = self.mock_get_ptp_config.start()
        self.mock_get_ntp_config = patch.object(onyx_ptp_global.OnyxPtpGlobalModule, "_show_ntp_config")
        self.get_ntp_config = self.mock_get_ntp_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxPtpModule, self).tearDown()
        self.mock_get_ptp_config.stop()
        self.mock_get_ntp_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        if self._ptp_enabled:
            config_file = 'onyx_show_ptp_clock.cfg'
            self.get_ptp_config.return_value = load_fixture(config_file)
        else:
            self.get_ptp_config.return_value = None

        config_file = 'onyx_show_ntp_configured.cfg'
        ret_val = load_fixture(config_file)
        if self._ntp_enabled:
            ret_val[0]['NTP enabled'] = 'yes'
        self.get_ntp_config.return_value = ret_val
        self.load_config.return_value = None

    def test_ptp_enabled_no_change(self):
        set_module_args(dict(ptp_state='enabled'))
        self.execute_module(changed=False)

    def test_ptp_enabled_with_change(self):
        self._ptp_enabled = False
        set_module_args(dict(ptp_state='enabled'))
        commands = ['protocol ptp']
        self.execute_module(changed=True, commands=commands)

    def test_ptp_disabled_no_change(self):
        self._ptp_enabled = False
        set_module_args(dict(ptp_state='disabled'))
        self.execute_module(changed=False)

    def test_ptp_disabled_with_change(self):
        set_module_args(dict(ptp_state='disabled'))
        commands = ['no protocol ptp']
        self.execute_module(changed=True, commands=commands)

    def test_ntp_enabled_no_change(self):
        self._ptp_enabled = False
        set_module_args(dict(ntp_state='enabled',
                             ptp_state='disabled'))
        self.execute_module(changed=False)

    def test_ntp_enabled_with_change(self):
        self._ptp_enabled = False
        self._ntp_enabled = False
        set_module_args(dict(ntp_state='enabled',
                             ptp_state='disabled'))
        commands = ['ntp enable']
        self.execute_module(changed=True, commands=commands)

    def test_ntp_disabled_no_change(self):
        self._ntp_enabled = False
        set_module_args(dict(ntp_state='disabled'))
        self.execute_module(changed=False)

    def test_ntp_disabled_with_change(self):
        set_module_args(dict(ntp_state='disabled'))
        commands = ['no ntp enable']
        self.execute_module(changed=True, commands=commands)

    def test_set_domain_no_change(self):
        self._ntp_enabled = False
        set_module_args(dict(ntp_state='disabled',
                             domain=127))
        self.execute_module(changed=False)

    def test_set_domain_with_change(self):
        set_module_args(dict(domain=100))
        commands = ['ptp domain 100']
        self.execute_module(changed=True, commands=commands)

    def test_set_primary_priority_no_change(self):
        set_module_args(dict(primary_priority=128))
        self.execute_module(changed=False)

    def test_set_primary_priority_with_change(self):
        set_module_args(dict(primary_priority=250))
        commands = ['ptp priority1 250']
        self.execute_module(changed=True, commands=commands)

    def test_set_secondary_priority_no_change(self):
        set_module_args(dict(secondary_priority=128))
        self.execute_module(changed=False)

    def test_set_secondary_priority_with_change(self):
        set_module_args(dict(secondary_priority=190))
        commands = ['ptp priority2 190']
        self.execute_module(changed=True, commands=commands)
