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
from ansible.compat.tests.mock import patch
from ansible.modules.network.icx import icx_lldp
from units.modules.utils import set_module_args
from .icx_module import TestICXModule, load_fixture


class TestICXlldpModule(TestICXModule):

    module = icx_lldp

    def setUp(self):
        super(TestICXlldpModule, self).setUp()

        self.mock_load_config = patch('ansible.modules.network.icx.icx_lldp.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_run_commands = patch('ansible.modules.network.icx.icx_lldp.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_get_env_diff = patch('ansible.modules.network.icx.icx_lldp.get_env_diff')
        self.get_env_diff = self.mock_get_env_diff.start()
        self.set_running_config()

    def tearDown(self):
        super(TestICXlldpModule, self).tearDown()
        self.mock_load_config.stop()
        self.mock_run_commands.stop()
        self.mock_get_env_diff.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            compares = None
            module, commands = args
            state = module.params['state']
            if module.params['check_running_config'] is not None:
                compares = module.params['check_running_config']
            else:
                compares = None

            env = self.get_running_config(compares)
            self.get_env_diff.return_value = self.get_running_config(compare=None)
            if env is True:
                return load_fixture('icx_lldp_%s' % state).strip()
            else:
                self.run_commands.return_value = 0, '', None
                return ''
        self.run_commands.side_effect = load_from_file

    def test_icx_lldp_enable_state_None(self):
        interfaces_spec = [dict(name='ethernet 1/1/9', state='present')]
        set_module_args(dict(interfaces=interfaces_spec))
        if not self.ENV_ICX_USE_DIFF:
            result = self.execute_module(failed=True)
        else:
            result = self.execute_module(failed=True)

    def test_icx_lldp_enable_state_absent_compare(self):
        interfaces_spec = [dict(name='ethernet 1/1/9', state='present')]
        set_module_args(dict(interfaces=interfaces_spec, state='absent', check_running_config=True))
        if self.get_running_config(compare=True):
            if not self.ENV_ICX_USE_DIFF:
                result = self.execute_module(changed=True)
                self.assertEqual(result['commands'], ['no lldp run'])
            else:
                result = self.execute_module(changed=True)
                self.assertEqual(result['commands'], ['no lldp run'])

    def test_icx_lldp_enable_state_present(self):
        interfaces_spec = [dict(name='ethernet 1/1/9', state='present')]
        set_module_args(dict(interfaces=interfaces_spec, state='present'))
        if not self.ENV_ICX_USE_DIFF:
            result = self.execute_module(changed=True)
            self.assertEqual(result['commands'], ['lldp enable ports ethernet 1/1/9'])

        else:
            result = self.execute_module(changed=True)
            self.assertEqual(result['commands'], ['lldp enable ports ethernet 1/1/9'])

    def test_icx_lldp_multi_enable_state_present(self):
        interfaces_spec = [dict(name=['ethernet 1/1/9', 'ethernet 1/1/1 to 1/1/6'], state='present')]
        set_module_args(dict(interfaces=interfaces_spec, state='present'))
        if not self.ENV_ICX_USE_DIFF:
            result = self.execute_module(changed=True)
            self.assertEqual(result['commands'], ['lldp enable ports ethernet 1/1/9', 'lldp enable ports ethernet 1/1/1 to 1/1/6'])
        else:
            result = self.execute_module(changed=True)
            self.assertEqual(result['commands'], ['lldp enable ports ethernet 1/1/9', 'lldp enable ports ethernet 1/1/1 to 1/1/6'])

    def test_icx_lldp_multi_disable_state_present(self):
        interfaces_spec = [dict(name=['ethernet 1/1/9', 'ethernet 1/1/1 to 1/1/6'], state='absent')]
        set_module_args(dict(interfaces=interfaces_spec, state='present'))
        if not self.ENV_ICX_USE_DIFF:
            result = self.execute_module(changed=True)
            self.assertEqual(result['commands'], ['no lldp enable ports ethernet 1/1/9', 'no lldp enable ports ethernet 1/1/1 to 1/1/6'])
        else:
            result = self.execute_module(changed=True)
            self.assertEqual(result['commands'], ['no lldp enable ports ethernet 1/1/9', 'no lldp enable ports ethernet 1/1/1 to 1/1/6'])

    def test_icx_lldp_all_error(self):
        interfaces_spec = [dict(name=['ethernet all'], state='absent')]
        set_module_args(dict(interfaces=interfaces_spec, state='present'))
        if not self.ENV_ICX_USE_DIFF:
            self.execute_module(failed=True)
        else:
            self.execute_module(failed=True)
