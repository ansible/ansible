#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from units.compat.mock import patch
from units.modules.utils import AnsibleFailJson
from ansible.modules.network.nxos import nxos_devicealias
from ansible.modules.network.nxos.nxos_devicealias import showDeviceAliasStatus
from ansible.modules.network.nxos.nxos_devicealias import showDeviceAliasDatabase

from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosDeviceAliasModule(TestNxosModule):

    module = nxos_devicealias

    def setUp(self):
        super(TestNxosDeviceAliasModule, self).setUp()

        self.mock_run_commands = patch('ansible.modules.network.nxos.nxos_devicealias.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_execute_show_cmd = patch('ansible.modules.network.nxos.nxos_devicealias.showDeviceAliasStatus.execute_show_cmd')
        self.execute_show_cmd = self.mock_execute_show_cmd.start()

        self.mock_execute_show_cmd_1 = patch('ansible.modules.network.nxos.nxos_devicealias.showDeviceAliasDatabase.execute_show_cmd')
        self.execute_show_cmd_1 = self.mock_execute_show_cmd_1.start()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_devicealias.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestNxosDeviceAliasModule, self).tearDown()
        self.mock_run_commands.stop()
        self.mock_execute_show_cmd.stop()
        self.mock_execute_show_cmd_1.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, device=''):
        self.load_config.return_value = None

    def test_da_mode_1(self):
        # Playbook mode is basic
        # Switch has mode as enahnced
        set_module_args(dict(mode='basic'))
        self.execute_show_cmd.return_value = load_fixture('nxos_devicealias', 'shdastatus.cfg')
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['terminal dont-ask', 'no device-alias mode enhanced', 'device-alias commit', 'no terminal dont-ask'])

    def test_da_mode_2(self):
        # Playbook mode is enhanced
        # Switch has mode as enahnced
        set_module_args(dict(mode='enhanced'))
        self.execute_show_cmd.return_value = load_fixture('nxos_devicealias', 'shdastatus.cfg')
        result = self.execute_module(changed=False)
        self.assertEqual(result['commands'], [])

    def test_da_distribute_1(self):
        # Playbook mode is enhanced , distrbute = True
        # Switch has mode as enahnced, distrbute = True
        set_module_args(dict(distribute=True, mode='enhanced'))
        self.execute_show_cmd.return_value = load_fixture('nxos_devicealias', 'shdastatus.cfg')
        result = self.execute_module(changed=False)
        self.assertEqual(result['commands'], [])

    def test_da_distribute_2(self):
        # Playbook mode is enhanced , distrbute = False
        # Switch has mode as enhanced, distrbute = True
        set_module_args(dict(distribute=False, mode='enhanced'))
        self.execute_show_cmd.return_value = load_fixture('nxos_devicealias', 'shdastatus.cfg')
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['no device-alias distribute'])

    def test_da_distribute_3(self):
        # Playbook mode is basic , distrbute = False
        # Switch has mode as enahnced, distrbute = True
        set_module_args(dict(distribute=False, mode='basic'))
        self.execute_show_cmd.return_value = load_fixture('nxos_devicealias', 'shdastatus.cfg')
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['no device-alias distribute', 'no device-alias mode enhanced'])

    def test_da_add_1(self):
        # Playbook mode is enhanced , distrbute = true , some new da being added
        # Switch has mode as enahnced, distrbute = True, switch doesnt have the new da being added
        set_module_args(dict(distribute=True, mode='enhanced', da=[dict(name='somename', pwwn='10:00:00:00:89:a1:01:03'), dict(name='somename1', pwwn='10:00:00:00:89:a1:02:03')]))
        self.execute_show_cmd.return_value = load_fixture('nxos_devicealias', 'shdastatus.cfg')
        self.execute_show_cmd_1.return_value = load_fixture('nxos_devicealias', 'shdadatabse.cfg')
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['terminal dont-ask', 'device-alias database',
                                              'device-alias name somename pwwn 10:00:00:00:89:a1:01:03',
                                              'device-alias name somename1 pwwn 10:00:00:00:89:a1:02:03',
                                              'device-alias commit', 'no terminal dont-ask'])

    def test_da_add_2(self):
        # Playbook mode is enhanced , distrbute = true , some new da being added
        # Switch has mode as enahnced, distrbute = True, switch already has the pwwn:name
        set_module_args(dict(distribute=True, mode='enhanced', da=[dict(name='tieHost-2', pwwn='10:00:00:00:89:a1:01:02')]))
        self.execute_show_cmd.return_value = load_fixture('nxos_devicealias', 'shdastatus.cfg')
        self.execute_show_cmd_1.return_value = load_fixture('nxos_devicealias', 'shdadatabse.cfg')
        result = self.execute_module(changed=False)
        self.assertEqual(result['commands'], [])

    def test_da_add_3(self):
        # Playbook mode is enhanced , distrbute = true , some new da being added
        # Switch has mode as enahnced, distrbute = True, switch same name present with different pwwn
        set_module_args(dict(distribute=True, mode='enhanced', da=[dict(name='tieHost-2', pwwn='10:00:00:00:89:a1:01:ff')]))
        self.execute_show_cmd.return_value = load_fixture('nxos_devicealias', 'shdastatus.cfg')
        self.execute_show_cmd_1.return_value = load_fixture('nxos_devicealias', 'shdadatabse.cfg')
        result = self.execute_module(changed=False, failed=True)
        #self.assertEqual(result['commands'], [])

    def test_da_add_4(self):
        # Playbook mode is enhanced , distrbute = true , some new da being added
        # Switch has mode as enahnced, distrbute = True, switch same pwwn present with different name
        set_module_args(dict(distribute=True, mode='enhanced', da=[dict(name='tieHost-2222', pwwn='10:00:00:00:89:a1:01:02')]))
        self.execute_show_cmd.return_value = load_fixture('nxos_devicealias', 'shdastatus.cfg')
        self.execute_show_cmd_1.return_value = load_fixture('nxos_devicealias', 'shdadatabse.cfg')
        result = self.execute_module(changed=False, failed=True)
        #self.assertEqual(result['commands'], [])

    def test_da_remove_1(self):
        # Playbook mode is enhanced , distrbute = true , some da being removed
        # Switch has mode as enahnced, distrbute = True, switch has the da that needs to be removed
        set_module_args(dict(distribute=True, mode='enhanced', da=[dict(name='tieHost-2', pwwn='10:00:00:00:89:a1:01:02', remove=True)]))
        self.execute_show_cmd.return_value = load_fixture('nxos_devicealias', 'shdastatus.cfg')
        self.execute_show_cmd_1.return_value = load_fixture('nxos_devicealias', 'shdadatabse.cfg')
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['terminal dont-ask', 'device-alias database',
                                              'no device-alias name tieHost-2',
                                              'device-alias commit', 'no terminal dont-ask'])

    def test_da_remove_2(self):
        # Playbook mode is enhanced , distrbute = true , some da being removed
        # Switch has mode as enahnced, distrbute = True, switch does NOT have the da that needs to be removed
        set_module_args(dict(distribute=True, mode='enhanced', da=[dict(name='somename', pwwn='10:00:00:00:89:a1:01:02', remove=True)]))
        self.execute_show_cmd.return_value = load_fixture('nxos_devicealias', 'shdastatus.cfg')
        self.execute_show_cmd_1.return_value = load_fixture('nxos_devicealias', 'shdadatabse.cfg')
        result = self.execute_module(changed=False)
        self.assertEqual(result['commands'], [])

    def test_da_lock(self):
        # Playbook mode with some data, but switch has cfs lock acq
        set_module_args(dict(distribute=True, mde='enhanced', da=[dict(name='somename', pwwn='10:00:00:00:89:a1:01:02', remove=True)]))
        self.execute_show_cmd.return_value = load_fixture('nxos_devicealias', 'shdastatuslock.cfg')
        self.execute_module(failed=True)

    def test_da_paramete_not_supported(self):
        # Playbook mode with some data, but switch has cfs lock acq
        # the below one instead of 'mode' we are passing 'mod', kind of typo in playbook
        set_module_args(dict(distribute=True, mod='enhanced', da=[dict(name='somename', pwwn='10:00:00:00:89:a1:01:02', remove=True)]))
        self.execute_show_cmd.return_value = load_fixture('nxos_devicealias', 'shdastatus.cfg')
        self.execute_show_cmd_1.return_value = load_fixture('nxos_devicealias', 'shdadatabse.cfg')
        with pytest.raises(AnsibleFailJson) as errinfo:
            self.execute_module()
        testdata = errinfo.value.args[0]
        assert 'Unsupported parameters' in str(testdata['msg'])
        assert testdata['failed']

    def test_da_name_parameter_missing(self):
        # Lets say you are trying to add a device alias but forgot to put 'name' in the 'da' parameter
        set_module_args(dict(distribute=True, mode='enhanced', da=[dict(pwwn='10:00:00:00:89:a1:01:02')]))
        self.execute_show_cmd.return_value = load_fixture('nxos_devicealias', 'shdastatus.cfg')
        self.execute_show_cmd_1.return_value = load_fixture('nxos_devicealias', 'shdadatabse.cfg')
        with pytest.raises(AnsibleFailJson) as errinfo:
            self.execute_module()
        testdata = errinfo.value.args[0]
        assert 'missing required arguments' in str(testdata['msg'])
        assert testdata['failed']

    def test_da_rename_1(self):
        # rename works
        set_module_args(dict(rename=[dict(old_name='test1_add', new_name='test234'),
                                     dict(old_name='tieHost-1', new_name='tieTarget-1')]))
        self.execute_show_cmd.return_value = load_fixture('nxos_devicealias', 'shdastatus.cfg')
        self.execute_show_cmd_1.return_value = load_fixture('nxos_devicealias', 'shdadatabse.cfg')
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['terminal dont-ask', 'device-alias database',
                                              'device-alias rename test1_add test234',
                                              'device-alias rename tieHost-1 tieTarget-1',
                                              'device-alias commit', 'no terminal dont-ask'])

    def test_da_rename_2(self):
        # rename : oldname not present
        set_module_args(dict(rename=[dict(old_name='test1', new_name='test234'),
                                     dict(old_name='tie', new_name='tieTarget-1')]))
        self.execute_show_cmd.return_value = load_fixture('nxos_devicealias', 'shdastatus.cfg')
        self.execute_show_cmd_1.return_value = load_fixture('nxos_devicealias', 'shdadatabse.cfg')
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(result['commands'], [])

    def test_da_mansi(self):

        set_module_args(
            {
                "distribute": True,
                "mode": "enhanced",
            }
        )
        self.execute_show_cmd.return_value = load_fixture('nxos_devicealias', 'shdastatus_mansi.cfg')
        self.execute_show_cmd_1.return_value = load_fixture('nxos_devicealias', 'shdadatabse.cfg')
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['device-alias distribute', 'terminal dont-ask',
                                              'device-alias mode enhanced',
                                              'device-alias commit', 'no terminal dont-ask'])
