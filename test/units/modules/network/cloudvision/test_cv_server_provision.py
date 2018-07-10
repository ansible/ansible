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
#

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, Mock
import sys
sys.modules['cvprac'] = Mock()
sys.modules['cvprac.cvp_client'] = Mock()
sys.modules['cvprac.cvp_client_errors'] = Mock()
import ansible.modules.network.cloudvision.cv_server_provision as cv_server_provision


class MockException(BaseException):
    pass


class TestCvServerProvision(unittest.TestCase):
    @patch('ansible.modules.network.cloudvision.cv_server_provision.CvpApiError',
           new_callable=lambda: MockException)
    @patch('ansible.modules.network.cloudvision.cv_server_provision.server_configurable_configlet')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.switch_in_compliance')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.switch_info')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.connect')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.AnsibleModule')
    def test_main_module_args(self, mock_module, mock_connect, mock_info,
                              mock_comp, mock_server_conf, mock_exception):
        ''' Test main module args.
        '''
        mock_module_object = Mock()
        mock_module_object.params = dict(action='show', switch_name='eos')
        mock_module_object.fail_json.side_effect = SystemExit('Exiting')
        mock_module.return_value = mock_module_object
        mock_connect.return_value = 'Client'
        mock_info.side_effect = mock_exception('Error Getting Info')
        argument_spec = dict(
            host=dict(required=True),
            port=dict(required=False, default=None),
            protocol=dict(default='https', choices=['http', 'https']),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            server_name=dict(required=True),
            switch_name=dict(required=True),
            switch_port=dict(required=True),
            port_vlan=dict(required=False, default=None),
            template=dict(require=True),
            action=dict(default='show', choices=['show', 'add', 'remove']),
            auto_run=dict(type='bool', default=False),
        )
        self.assertRaises(SystemExit, cv_server_provision.main)
        mock_module.assert_called_with(argument_spec=argument_spec,
                                       supports_check_mode=False)
        self.assertEqual(mock_connect.call_count, 1)
        self.assertEqual(mock_info.call_count, 1)
        mock_comp.assert_not_called()
        mock_server_conf.assert_not_called()
        mock_module_object.fail_json.assert_called_with(msg='Error Getting Info')

    @patch('ansible.modules.network.cloudvision.cv_server_provision.CvpApiError',
           new_callable=lambda: MockException)
    @patch('ansible.modules.network.cloudvision.cv_server_provision.server_configurable_configlet')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.switch_in_compliance')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.switch_info')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.connect')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.AnsibleModule')
    def test_main_no_switch_configlet(self, mock_module, mock_connect,
                                      mock_info, mock_comp, mock_server_conf,
                                      mock_exception):
        ''' Test main fails if switch has no configlet for Ansible to edit.
        '''
        mock_module_object = Mock()
        mock_module_object.params = dict(action='add', switch_name='eos')
        mock_module_object.fail_json.side_effect = SystemExit('Exiting')
        mock_module.return_value = mock_module_object
        mock_connect.return_value = 'Client'
        mock_info.return_value = 'Info'
        mock_server_conf.return_value = None
        self.assertRaises(SystemExit, cv_server_provision.main)
        self.assertEqual(mock_connect.call_count, 1)
        self.assertEqual(mock_info.call_count, 1)
        self.assertEqual(mock_comp.call_count, 1)
        self.assertEqual(mock_server_conf.call_count, 1)
        mock_module_object.fail_json.assert_called_with(
            msg='Switch eos has no configurable server ports.')

    @patch('ansible.modules.network.cloudvision.cv_server_provision.CvpApiError',
           new_callable=lambda: MockException)
    @patch('ansible.modules.network.cloudvision.cv_server_provision.port_configurable')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.server_configurable_configlet')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.switch_in_compliance')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.switch_info')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.connect')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.AnsibleModule')
    def test_main_port_not_in_config(self, mock_module, mock_connect, mock_info,
                                     mock_comp, mock_server_conf,
                                     mock_port_conf, mock_exception):
        ''' Test main fails if user specified port not in configlet.
        '''
        mock_module_object = Mock()
        mock_module_object.params = dict(action='add', switch_name='eos',
                                         switch_port='3')
        mock_module_object.fail_json.side_effect = SystemExit('Exiting')
        mock_module.return_value = mock_module_object
        mock_connect.return_value = 'Client'
        mock_info.return_value = 'Info'
        mock_server_conf.return_value = 'Configlet'
        mock_port_conf.return_value = None
        self.assertRaises(SystemExit, cv_server_provision.main)
        self.assertEqual(mock_connect.call_count, 1)
        self.assertEqual(mock_info.call_count, 1)
        self.assertEqual(mock_comp.call_count, 1)
        self.assertEqual(mock_server_conf.call_count, 1)
        self.assertEqual(mock_port_conf.call_count, 1)
        mock_module_object.fail_json.assert_called_with(
            msg='Port 3 is not configurable as a server port on switch eos.')

    @patch('ansible.modules.network.cloudvision.cv_server_provision.configlet_action')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.port_configurable')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.server_configurable_configlet')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.switch_in_compliance')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.switch_info')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.connect')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.AnsibleModule')
    def test_main_show(self, mock_module, mock_connect, mock_info, mock_comp,
                       mock_server_conf, mock_port_conf, mock_conf_action):
        ''' Test main good with show action.
        '''
        mock_module_object = Mock()
        mock_module_object.params = dict(action='show', switch_name='eos',
                                         switch_port='3', auto_run=False)
        mock_module.return_value = mock_module_object
        mock_connect.return_value = 'Client'
        mock_info.return_value = 'Info'
        mock_server_conf.return_value = 'Configlet'
        mock_port_conf.return_value = 'Port'
        mock_conf_action.return_value = dict()
        cv_server_provision.main()
        self.assertEqual(mock_connect.call_count, 1)
        self.assertEqual(mock_info.call_count, 1)
        mock_comp.assert_not_called()
        self.assertEqual(mock_server_conf.call_count, 1)
        self.assertEqual(mock_port_conf.call_count, 1)
        self.assertEqual(mock_conf_action.call_count, 1)
        mock_module_object.fail_json.assert_not_called()
        return_dict = dict(changed=False, switchInfo='Info',
                           switchConfigurable=True, portConfigurable=True,
                           taskCreated=False, taskExecuted=False,
                           taskCompleted=False)
        mock_module_object.exit_json.assert_called_with(**return_dict)

    @patch('ansible.modules.network.cloudvision.cv_server_provision.configlet_action')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.port_configurable')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.server_configurable_configlet')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.switch_in_compliance')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.switch_info')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.connect')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.AnsibleModule')
    def test_main_add_no_auto_run(self, mock_module, mock_connect, mock_info,
                                  mock_comp, mock_server_conf, mock_port_conf,
                                  mock_conf_action):
        ''' Test main good with add action and no auto_run.
        '''
        mock_module_object = Mock()
        mock_module_object.params = dict(action='add', switch_name='eos',
                                         switch_port='3', auto_run=False)
        mock_module.return_value = mock_module_object
        mock_connect.return_value = 'Client'
        mock_info.return_value = 'Info'
        mock_server_conf.return_value = 'Configlet'
        mock_port_conf.return_value = 'Port'
        mock_conf_action.return_value = dict(taskCreated=True)
        cv_server_provision.main()
        self.assertEqual(mock_connect.call_count, 1)
        self.assertEqual(mock_info.call_count, 1)
        self.assertEqual(mock_comp.call_count, 1)
        self.assertEqual(mock_server_conf.call_count, 1)
        self.assertEqual(mock_port_conf.call_count, 1)
        self.assertEqual(mock_conf_action.call_count, 1)
        mock_module_object.fail_json.assert_not_called()
        return_dict = dict(changed=False, switchInfo='Info',
                           switchConfigurable=True, portConfigurable=True,
                           taskCreated=True, taskExecuted=False,
                           taskCompleted=False)
        mock_module_object.exit_json.assert_called_with(**return_dict)

    @patch('ansible.modules.network.cloudvision.cv_server_provision.wait_for_task_completion')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.configlet_update_task')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.configlet_action')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.port_configurable')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.server_configurable_configlet')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.switch_in_compliance')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.switch_info')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.connect')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.AnsibleModule')
    def test_main_add_auto_run(self, mock_module, mock_connect, mock_info,
                               mock_comp, mock_server_conf, mock_port_conf,
                               mock_conf_action, mock_conf_task, mock_wait):
        ''' Test main good with add and auto_run. Config updated, task created.
        '''
        mock_module_object = Mock()
        mock_module_object.params = dict(action='add', switch_name='eos',
                                         switch_port='3', auto_run=True)
        mock_module.return_value = mock_module_object
        mock_client_object = Mock()
        mock_connect.return_value = mock_client_object
        mock_info.return_value = 'Info'
        mock_server_conf.return_value = 'Configlet'
        mock_port_conf.return_value = 'Port'
        mock_conf_action.return_value = dict(taskCreated=True, changed=True)
        mock_conf_task.return_value = '7'
        mock_wait.return_value = True
        cv_server_provision.main()
        self.assertEqual(mock_connect.call_count, 1)
        self.assertEqual(mock_info.call_count, 1)
        self.assertEqual(mock_comp.call_count, 1)
        self.assertEqual(mock_server_conf.call_count, 1)
        self.assertEqual(mock_port_conf.call_count, 1)
        self.assertEqual(mock_conf_action.call_count, 1)
        self.assertEqual(mock_conf_task.call_count, 1)
        self.assertEqual(mock_wait.call_count, 1)
        mock_module_object.fail_json.assert_not_called()
        return_dict = dict(changed=True, switchInfo='Info', taskId='7',
                           switchConfigurable=True, portConfigurable=True,
                           taskCreated=True, taskExecuted=True,
                           taskCompleted=True)
        mock_module_object.exit_json.assert_called_with(**return_dict)

    @patch('ansible.modules.network.cloudvision.cv_server_provision.wait_for_task_completion')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.configlet_update_task')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.configlet_action')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.port_configurable')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.server_configurable_configlet')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.switch_in_compliance')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.switch_info')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.connect')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.AnsibleModule')
    def test_main_add_auto_run_no_task(self, mock_module, mock_connect,
                                       mock_info, mock_comp, mock_server_conf,
                                       mock_port_conf, mock_conf_action, mock_conf_task,
                                       mock_wait):
        ''' Test main good with add and auto_run. Config not updated, no task.
        '''
        mock_module_object = Mock()
        mock_module_object.params = dict(action='add', switch_name='eos',
                                         switch_port='3', auto_run=True)
        mock_module.return_value = mock_module_object
        mock_client_object = Mock()
        mock_connect.return_value = mock_client_object
        mock_info.return_value = 'Info'
        mock_server_conf.return_value = 'Configlet'
        mock_port_conf.return_value = 'Port'
        mock_conf_action.return_value = dict(taskCreated=True, changed=False)
        mock_conf_task.return_value = None
        cv_server_provision.main()
        self.assertEqual(mock_connect.call_count, 1)
        self.assertEqual(mock_info.call_count, 1)
        self.assertEqual(mock_comp.call_count, 1)
        self.assertEqual(mock_server_conf.call_count, 1)
        self.assertEqual(mock_port_conf.call_count, 1)
        self.assertEqual(mock_conf_action.call_count, 1)
        self.assertEqual(mock_conf_task.call_count, 1)
        mock_wait.assert_not_called()
        mock_module_object.fail_json.assert_not_called()
        return_dict = dict(changed=False, switchInfo='Info',
                           switchConfigurable=True, portConfigurable=True,
                           taskCreated=False, taskExecuted=False,
                           taskCompleted=False)
        mock_module_object.exit_json.assert_called_with(**return_dict)

    @patch('ansible.modules.network.cloudvision.cv_server_provision.CvpClient')
    def test_connect_good(self, mock_client):
        ''' Test connect success.
        '''
        module = Mock()
        module.params = dict(host='host', username='username',
                             password='password', protocol='https', port='10')
        connect_mock = Mock()
        mock_client.return_value = connect_mock
        client = cv_server_provision.connect(module)
        self.assertIsInstance(client, Mock)
        self.assertEqual(mock_client.call_count, 1)
        connect_mock.connect.assert_called_once_with(['host'], 'username',
                                                     'password', port='10',
                                                     protocol='https')
        module.fail_json.assert_not_called()

    @patch('ansible.modules.network.cloudvision.cv_server_provision.CvpLoginError',
           new_callable=lambda: MockException)
    @patch('ansible.modules.network.cloudvision.cv_server_provision.CvpClient')
    def test_connect_fail(self, mock_client, mock_exception):
        ''' Test connect failure with login error.
        '''
        module = Mock()
        module.params = dict(host='host', username='username',
                             password='password', protocol='https', port='10')
        module.fail_json.side_effect = SystemExit
        connect_mock = Mock()
        connect_mock.connect.side_effect = mock_exception('Login Error')
        mock_client.return_value = connect_mock
        self.assertRaises(SystemExit, cv_server_provision.connect, module)
        self.assertEqual(connect_mock.connect.call_count, 1)
        module.fail_json.assert_called_once_with(msg='Login Error')

    def test_switch_info_good(self):
        ''' Test switch_info success.
        '''
        module = Mock()
        module.params = dict(switch_name='eos')
        module.client.api.get_device_by_name.return_value = dict(fqdn='eos')
        info = cv_server_provision.switch_info(module)
        self.assertEqual(module.client.api.get_device_by_name.call_count, 1)
        self.assertEqual(info['fqdn'], 'eos')
        module.fail_json.assert_not_called()

    def test_switch_info_no_switch(self):
        ''' Test switch_info fails.
        '''
        module = Mock()
        module.params = dict(switch_name='eos')
        module.client.api.get_device_by_name.return_value = None
        info = cv_server_provision.switch_info(module)
        self.assertEqual(module.client.api.get_device_by_name.call_count, 1)
        self.assertEqual(info, None)
        module.fail_json.assert_called_once_with(
            msg="Device with name 'eos' does not exist.")

    def test_switch_in_compliance_good(self):
        ''' Test switch_in_compliance good.
        '''
        module = Mock()
        module.client.api.check_compliance.return_value = dict(
            complianceCode='0000')
        sw_info = dict(key='key', type='type', fqdn='eos')
        cv_server_provision.switch_in_compliance(module, sw_info)
        self.assertEqual(module.client.api.check_compliance.call_count, 1)
        module.fail_json.assert_not_called()

    def test_switch_in_compliance_fail(self):
        ''' Test switch_in_compliance fail.
        '''
        module = Mock()
        module.client.api.check_compliance.return_value = dict(
            complianceCode='0001')
        sw_info = dict(key='key', type='type', fqdn='eos')
        cv_server_provision.switch_in_compliance(module, sw_info)
        self.assertEqual(module.client.api.check_compliance.call_count, 1)
        module.fail_json.assert_called_with(
            msg='Switch eos is not in compliance.'
                ' Returned compliance code 0001.')

    def test_server_configurable_configlet_good(self):
        ''' Test server_configurable_configlet good.
        '''
        module = Mock()
        module.params = dict(switch_name='eos')
        configlets = [dict(name='configlet1', info='line'),
                      dict(name='eos-server', info='info')]
        module.client.api.get_configlets_by_device_id.return_value = configlets
        sw_info = dict(key='key', type='type', fqdn='eos')
        result = cv_server_provision.server_configurable_configlet(module,
                                                                   sw_info)
        self.assertEqual(module.client.api.get_configlets_by_device_id.call_count, 1)
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'eos-server')
        self.assertEqual(result['info'], 'info')

    def test_server_configurable_configlet_not_configurable(self):
        ''' Test server_configurable_configlet fail. No server configlet.
        '''
        module = Mock()
        module.params = dict(switch_name='eos')
        configlets = [dict(name='configlet1', info='line'),
                      dict(name='configlet2', info='info')]
        module.client.api.get_configlets_by_device_id.return_value = configlets
        sw_info = dict(key='key', type='type', fqdn='eos')
        result = cv_server_provision.server_configurable_configlet(module, sw_info)
        self.assertEqual(module.client.api.get_configlets_by_device_id.call_count, 1)
        self.assertIsNone(result)

    def test_server_configurable_configlet_no_configlets(self):
        ''' Test server_configurable_configlet fail. No switch configlets.
        '''
        module = Mock()
        module.params = dict(switch_name='eos')
        module.client.api.get_configlets_by_device_id.return_value = []
        sw_info = dict(key='key', type='type', fqdn='eos')
        result = cv_server_provision.server_configurable_configlet(module,
                                                                   sw_info)
        self.assertEqual(module.client.api.get_configlets_by_device_id.call_count, 1)
        self.assertIsNone(result)

    def test_port_configurable_good(self):
        ''' Test port_configurable user provided switch port in configlet.
        '''
        module = Mock()
        module.params = dict(switch_name='eos', switch_port='3')
        config = '!\ninterface Ethernet3\n!\ninterface Ethernet4\n!'
        configlet = dict(name='eos-server', config=config)
        result = cv_server_provision.port_configurable(module, configlet)
        self.assertTrue(result)

    def test_port_configurable_fail(self):
        ''' Test port_configurable user provided switch port not in configlet.
        '''
        module = Mock()
        module.params = dict(switch_name='eos', switch_port='2')
        config = '!\ninterface Ethernet3\n!\ninterface Ethernet4\n!'
        configlet = dict(name='eos-server', config=config)
        result = cv_server_provision.port_configurable(module, configlet)
        self.assertFalse(result)

    def test_port_configurable_fail_no_config(self):
        ''' Test port_configurable configlet empty.
        '''
        module = Mock()
        module.params = dict(switch_name='eos', switch_port='2')
        config = ''
        configlet = dict(name='eos-server', config=config)
        result = cv_server_provision.port_configurable(module, configlet)
        self.assertFalse(result)

    def test_configlet_action_show_blank_config(self):
        ''' Test configlet_action show returns current port configuration.
        '''
        module = Mock()
        module.params = dict(action='show', switch_name='eos', switch_port='3')
        config = '!\ninterface Ethernet3\n!\ninterface Ethernet4\n!'
        configlet = dict(name='eos-server', key='key', config=config)
        result = cv_server_provision.configlet_action(module, configlet)
        self.assertIsNotNone(result)
        self.assertEqual(result['currentConfigBlock'], 'interface Ethernet3\n!')
        module.client.api.update_configlet.assert_not_called()

    @patch('ansible.modules.network.cloudvision.cv_server_provision.config_from_template')
    def test_configlet_action_add_with_task(self, mock_template):
        ''' Test configlet_action add with change updates configlet and adds
            proper info to return data. Including task spawned info.
        '''
        module = Mock()
        module.params = dict(action='add', switch_name='eos', switch_port='3')
        config = '!\ninterface Ethernet3\n!\ninterface Ethernet4\n!'
        configlet = dict(name='eos-server', key='key', config=config)
        template_config = ('interface Ethernet3\n   description Host eos'
                           ' managed by Ansible and Jinja template\n'
                           '   load-interval 30\n'
                           '   switchport\n'
                           '   switchport mode trunk\n'
                           '   no shutdown\n!')
        mock_template.return_value = template_config
        update_return = dict(data='Configlet eos-server successfully updated'
                                  ' and task initiated.')
        module.client.api.update_configlet.return_value = update_return
        result = cv_server_provision.configlet_action(module, configlet)
        self.assertIsNotNone(result)
        self.assertEqual(result['oldConfigBlock'], 'interface Ethernet3\n!')
        full_config = '!\n' + template_config + '\ninterface Ethernet4\n!'
        self.assertEqual(result['fullConfig'], full_config)
        self.assertEqual(result['updateConfigletResponse'],
                         update_return['data'])
        self.assertTrue(result['changed'])
        self.assertTrue(result['taskCreated'])
        self.assertEqual(module.client.api.update_configlet.call_count, 1)

    @patch('ansible.modules.network.cloudvision.cv_server_provision.config_from_template')
    def test_configlet_action_add_no_task(self, mock_template):
        ''' Test configlet_action add that doesn't change configlet adds proper
            info to return data. Does not including any task info.
        '''
        module = Mock()
        module.params = dict(action='add', switch_name='eos', switch_port='3')
        config = ('!\ninterface Ethernet3\n   description test\n'
                  '!\ninterface Ethernet4\n!')
        configlet = dict(name='eos-server', key='key', config=config)
        template_config = 'interface Ethernet3\n   description test\n!'
        mock_template.return_value = template_config
        update_return = dict(data='Configlet eos-server successfully updated.')
        module.client.api.update_configlet.return_value = update_return
        result = cv_server_provision.configlet_action(module, configlet)
        self.assertIsNotNone(result)
        self.assertEqual(result['oldConfigBlock'],
                         'interface Ethernet3\n   description test\n!')
        self.assertEqual(result['fullConfig'], config)
        self.assertEqual(result['updateConfigletResponse'],
                         update_return['data'])
        self.assertNotIn('changed', result)
        self.assertNotIn('taskCreated', result)
        self.assertEqual(module.client.api.update_configlet.call_count, 1)

    def test_configlet_action_remove_with_task(self):
        ''' Test configlet_action remove with change updates configlet and adds
            proper info to return data. Including task spawned info.
        '''
        module = Mock()
        module.params = dict(action='remove', switch_name='eos',
                             switch_port='3')
        config = ('!\ninterface Ethernet3\n   description test\n'
                  '!\ninterface Ethernet4\n!')
        configlet = dict(name='eos-server', key='key', config=config)
        update_return = dict(data='Configlet eos-server successfully updated'
                                  ' and task initiated.')
        module.client.api.update_configlet.return_value = update_return
        result = cv_server_provision.configlet_action(module, configlet)
        self.assertIsNotNone(result)
        self.assertEqual(result['oldConfigBlock'],
                         'interface Ethernet3\n   description test\n!')
        full_config = '!\ninterface Ethernet3\n!\ninterface Ethernet4\n!'
        self.assertEqual(result['fullConfig'], full_config)
        self.assertEqual(result['updateConfigletResponse'],
                         update_return['data'])
        self.assertTrue(result['changed'])
        self.assertTrue(result['taskCreated'])
        self.assertEqual(module.client.api.update_configlet.call_count, 1)

    def test_configlet_action_remove_no_task(self):
        ''' Test configlet_action with remove that doesn't change configlet and
            adds proper info to return data. Does not including any task info.
        '''
        module = Mock()
        module.params = dict(action='remove', switch_name='eos',
                             switch_port='3')
        config = '!\ninterface Ethernet3\n!\ninterface Ethernet4\n!'
        configlet = dict(name='eos-server', key='key', config=config)
        update_return = dict(data='Configlet eos-server successfully updated.')
        module.client.api.update_configlet.return_value = update_return
        result = cv_server_provision.configlet_action(module, configlet)
        self.assertIsNotNone(result)
        self.assertEqual(result['oldConfigBlock'], 'interface Ethernet3\n!')
        self.assertEqual(result['fullConfig'], config)
        self.assertEqual(result['updateConfigletResponse'],
                         update_return['data'])
        self.assertNotIn('changed', result)
        self.assertNotIn('taskCreated', result)
        self.assertEqual(module.client.api.update_configlet.call_count, 1)

    def test_current_config_empty_config(self):
        ''' Test current_config with empty config for port
        '''
        module = Mock()
        module.params = dict(switch_name='eos', switch_port='4')
        config = '!\ninterface Ethernet3\n!\ninterface Ethernet4'
        result = cv_server_provision.current_config(module, config)
        self.assertIsNotNone(result)
        self.assertEqual(result, 'interface Ethernet4')

    def test_current_config_with_config(self):
        ''' Test current_config with config for port
        '''
        module = Mock()
        module.params = dict(switch_name='eos', switch_port='3')
        config = ('!\ninterface Ethernet3\n   description test\n'
                  '!\ninterface Ethernet4\n!')
        result = cv_server_provision.current_config(module, config)
        self.assertIsNotNone(result)
        self.assertEqual(result, 'interface Ethernet3\n   description test\n!')

    def test_current_config_no_match(self):
        ''' Test current_config with no entry for port
        '''
        module = Mock()
        module.fail_json.side_effect = SystemExit
        module.params = dict(switch_name='eos', switch_port='2')
        config = '!\ninterface Ethernet3\n   description test\n!'
        self.assertRaises(SystemExit, cv_server_provision.current_config,
                          module, config)

    def test_valid_template_true(self):
        ''' Test valid_template true
        '''
        template = 'interface Ethernet3\n   description test\n!'
        result = cv_server_provision.valid_template('3', template)
        self.assertTrue(result)

    def test_valid_template_false(self):
        ''' Test valid_template false
        '''
        template = 'interface Ethernet3\n   description test\n!'
        result = cv_server_provision.valid_template('4', template)
        self.assertFalse(result)

    @patch('jinja2.DebugUndefined')
    @patch('jinja2.Environment')
    @patch('jinja2.FileSystemLoader')
    def test_config_from_template_no_template(self, mock_file_sys, mock_env,
                                              mock_debug):
        ''' Test config_from_template good. No template.
        '''
        module = Mock()
        module.fail_json.side_effect = SystemExit
        module.params = dict(switch_name='eos', switch_port='3',
                             server_name='new', template='jinja.j2')
        mock_file_sys.return_value = 'file'
        mock_debug.return_value = 'debug'
        env_mock = Mock()
        env_mock.get_template.return_value = None
        mock_env.return_value = env_mock
        self.assertRaises(SystemExit, cv_server_provision.config_from_template,
                          module)
        self.assertEqual(mock_file_sys.call_count, 1)
        self.assertEqual(mock_env.call_count, 1)
        self.assertEqual(module.fail_json.call_count, 1)

    @patch('jinja2.meta.find_undeclared_variables')
    @patch('jinja2.DebugUndefined')
    @patch('jinja2.Environment')
    @patch('jinja2.FileSystemLoader')
    def test_config_from_template_good_no_vlan(self, mock_file_sys, mock_env, mock_debug,
                                               mock_find):
        ''' Test config_from_template good. No port_vlan.
        '''
        module = Mock()
        module.params = dict(switch_name='eos', switch_port='3',
                             server_name='new', template='jinja.j2')
        mock_file_sys.return_value = 'file'
        mock_debug.return_value = 'debug'
        template_mock = Mock()
        template_mock.render.return_value = ('interface Ethernet3\n'
                                             '   description test\n'
                                             '   switchport\n'
                                             '   switchport mode trunk\n'
                                             '   no shutdown\n!')
        env_mock = Mock()
        env_mock.loader.get_source.return_value = ['one', 'two']
        env_mock.parse.return_value = 'parsed'
        env_mock.get_template.return_value = template_mock
        mock_env.return_value = env_mock
        mock_find.return_value = dict(server_name=None, switch_port=None)
        result = cv_server_provision.config_from_template(module)
        self.assertIsNotNone(result)
        expected = ('interface Ethernet3\n'
                    '   description test\n'
                    '   switchport\n'
                    '   switchport mode trunk\n'
                    '   no shutdown\n!')
        self.assertEqual(result, expected)
        self.assertEqual(mock_file_sys.call_count, 1)
        self.assertEqual(mock_env.call_count, 1)
        module.fail_json.assert_not_called()

    @patch('jinja2.meta.find_undeclared_variables')
    @patch('jinja2.DebugUndefined')
    @patch('jinja2.Environment')
    @patch('jinja2.FileSystemLoader')
    def test_config_from_template_good_vlan(self, mock_file_sys, mock_env, mock_debug,
                                            mock_find):
        ''' Test config_from_template good. With port_vlan.
        '''
        module = Mock()
        module.params = dict(switch_name='eos', switch_port='3',
                             server_name='new', template='jinja.j2', port_vlan='7')
        mock_file_sys.return_value = 'file'
        mock_debug.return_value = 'debug'
        template_mock = Mock()
        template_mock.render.return_value = ('interface Ethernet3\n'
                                             '   description test\n'
                                             '   switchport\n'
                                             '   switchport access vlan 7\n'
                                             '   no shutdown\n!')
        env_mock = Mock()
        env_mock.loader.get_source.return_value = ['one', 'two']
        env_mock.parse.return_value = 'parsed'
        env_mock.get_template.return_value = template_mock
        mock_env.return_value = env_mock
        mock_find.return_value = dict(server_name=None, switch_port=None,
                                      port_vlan=None)
        result = cv_server_provision.config_from_template(module)
        self.assertIsNotNone(result)
        expected = ('interface Ethernet3\n'
                    '   description test\n'
                    '   switchport\n'
                    '   switchport access vlan 7\n'
                    '   no shutdown\n!')
        self.assertEqual(result, expected)
        self.assertEqual(mock_file_sys.call_count, 1)
        self.assertEqual(mock_env.call_count, 1)
        module.fail_json.assert_not_called()

    @patch('jinja2.meta.find_undeclared_variables')
    @patch('jinja2.DebugUndefined')
    @patch('jinja2.Environment')
    @patch('jinja2.FileSystemLoader')
    def test_config_from_template_fail_wrong_port(self, mock_file_sys, mock_env,
                                                  mock_debug, mock_find):
        ''' Test config_from_template fail. Wrong port number in template.
        '''
        module = Mock()
        module.params = dict(switch_name='eos', switch_port='4',
                             server_name='new', template='jinja.j2')
        mock_file_sys.return_value = 'file'
        mock_debug.return_value = 'debug'
        template_mock = Mock()
        template_mock.render.return_value = ('interface Ethernet3\n'
                                             '   description test\n!')
        env_mock = Mock()
        env_mock.loader.get_source.return_value = ['one', 'two']
        env_mock.parse.return_value = 'parsed'
        env_mock.get_template.return_value = template_mock
        mock_env.return_value = env_mock
        mock_find.return_value = dict(server_name=None, switch_port=None)
        result = cv_server_provision.config_from_template(module)
        self.assertIsNotNone(result)
        expected = 'interface Ethernet3\n   description test\n!'
        self.assertEqual(result, expected)
        self.assertEqual(mock_file_sys.call_count, 1)
        self.assertEqual(mock_env.call_count, 1)
        module.fail_json.assert_called_with(msg='Template content does not'
                                                ' configure proper interface'
                                                ' - %s' % expected)

    @patch('jinja2.meta.find_undeclared_variables')
    @patch('jinja2.DebugUndefined')
    @patch('jinja2.Environment')
    @patch('jinja2.FileSystemLoader')
    def test_config_from_template_fail_no_vlan(self, mock_file_sys, mock_env,
                                               mock_debug, mock_find):
        ''' Test config_from_template fail. Template needs vlan but none provided.
        '''
        module = Mock()
        module.params = dict(switch_name='eos', switch_port='3',
                             server_name='new', template='jinja.j2',
                             port_vlan=None)
        mock_file_sys.return_value = 'file'
        mock_debug.return_value = 'debug'
        template_mock = Mock()
        template_mock.render.return_value = ('interface Ethernet3\n'
                                             '   description test\n!')
        env_mock = Mock()
        env_mock.loader.get_source.return_value = ['one', 'two']
        env_mock.parse.return_value = 'parsed'
        env_mock.get_template.return_value = template_mock
        mock_env.return_value = env_mock
        mock_find.return_value = dict(server_name=None, switch_port=None,
                                      port_vlan=None)
        result = cv_server_provision.config_from_template(module)
        self.assertIsNotNone(result)
        expected = 'interface Ethernet3\n   description test\n!'
        self.assertEqual(result, expected)
        self.assertEqual(mock_file_sys.call_count, 1)
        self.assertEqual(mock_env.call_count, 1)
        module.fail_json.assert_called_with(msg='Template jinja.j2 requires a'
                                                ' vlan. Please re-run with vlan'
                                                ' number provided.')

    def test_updated_configlet_content_add(self):
        ''' Test updated_configlet_content. Add config.
        '''
        module = Mock()
        module.params = dict(switch_name='eos', switch_port='3')
        existing_config = '!\ninterface Ethernet3\n!\ninterface Ethernet4\n!'
        new_config_block = 'interface Ethernet3\n   description test\n!'
        result = cv_server_provision.updated_configlet_content(module,
                                                               existing_config,
                                                               new_config_block)
        expected = ('!\ninterface Ethernet3\n   description test\n'
                    '!\ninterface Ethernet4\n!')
        self.assertEqual(result, expected)
        module.fail_json.assert_not_called()

    def test_updated_configlet_content_remove(self):
        ''' Test updated_configlet_content. Remove config.
        '''
        module = Mock()
        module.params = dict(switch_name='eos', switch_port='3')
        existing_config = ('!\ninterface Ethernet3\n   description test\n'
                           '!\ninterface Ethernet4')
        new_config_block = 'interface Ethernet3\n!'
        result = cv_server_provision.updated_configlet_content(module,
                                                               existing_config,
                                                               new_config_block)
        expected = '!\ninterface Ethernet3\n!\ninterface Ethernet4'
        self.assertEqual(result, expected)
        module.fail_json.assert_not_called()

    def test_updated_configlet_content_no_match(self):
        ''' Test updated_configlet_content. Interface not in config.
        '''
        module = Mock()
        module.fail_json.side_effect = SystemExit
        module.params = dict(switch_name='eos', switch_port='2')
        existing_config = '!\ninterface Ethernet3\n   description test\n!'
        new_config_block = 'interface Ethernet3\n!'
        self.assertRaises(SystemExit,
                          cv_server_provision.updated_configlet_content,
                          module, existing_config, new_config_block)

    @patch('time.sleep')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.switch_info')
    def test_configlet_update_task_good_one_try(self, mock_info, mock_sleep):
        ''' Test configlet_update_task gets task after one try.
        '''
        module = Mock()
        task = dict(data=dict(WORKFLOW_ACTION='Configlet Push'),
                    description='Configlet Assign',
                    workOrderId='7')
        device_info = dict(taskIdList=[task])
        mock_info.return_value = device_info
        result = cv_server_provision.configlet_update_task(module)
        self.assertEqual(result, '7')
        mock_sleep.assert_not_called()
        self.assertEqual(mock_info.call_count, 1)

    @patch('time.sleep')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.switch_info')
    def test_configlet_update_task_good_three_tries(self, mock_info, mock_sleep):
        ''' Test configlet_update_task gets task on third try.
        '''
        module = Mock()
        task1 = dict(data=dict(WORKFLOW_ACTION='Configlet Push'),
                     description='Configlet Assign',
                     workOrderId='7')
        task2 = dict(data=dict(WORKFLOW_ACTION='Nonsense'),
                     description='Configlet Assign',
                     workOrderId='700')
        device_info = dict(taskIdList=[task1, task2])
        mock_info.side_effect = [dict(), dict(), device_info]
        result = cv_server_provision.configlet_update_task(module)
        self.assertEqual(result, '7')
        self.assertEqual(mock_sleep.call_count, 2)
        self.assertEqual(mock_info.call_count, 3)

    @patch('time.sleep')
    @patch('ansible.modules.network.cloudvision.cv_server_provision.switch_info')
    def test_configlet_update_task_no_task(self, mock_info, mock_sleep):
        ''' Test configlet_update_task does not get task after three tries.
        '''
        module = Mock()
        mock_info.side_effect = [dict(), dict(), dict()]
        result = cv_server_provision.configlet_update_task(module)
        self.assertIsNone(result)
        self.assertEqual(mock_sleep.call_count, 3)
        self.assertEqual(mock_info.call_count, 3)

    @patch('time.sleep')
    def test_wait_for_task_completion_good_one_try(self, mock_time):
        ''' Test wait_for_task_completion completed. One Try.
        '''
        module = Mock()
        module.client.api.get_task_by_id.return_value = dict(
            workOrderUserDefinedStatus='Completed')
        result = cv_server_provision.wait_for_task_completion(module, '7')
        self.assertTrue(result)
        self.assertEqual(module.client.api.get_task_by_id.call_count, 1)
        module.fail_json.assert_not_called()
        mock_time.assert_not_called()

    @patch('time.sleep')
    def test_wait_for_task_completion_good_three_tries(self, mock_time):
        ''' Test wait_for_task_completion completed. Three tries.
        '''
        module = Mock()
        try_one_two = dict(workOrderUserDefinedStatus='Pending')
        try_three = dict(workOrderUserDefinedStatus='Completed')
        module.client.api.get_task_by_id.side_effect = [try_one_two,
                                                        try_one_two, try_three]
        result = cv_server_provision.wait_for_task_completion(module, '7')
        self.assertTrue(result)
        self.assertEqual(module.client.api.get_task_by_id.call_count, 3)
        module.fail_json.assert_not_called()
        self.assertEqual(mock_time.call_count, 2)

    @patch('time.sleep')
    def test_wait_for_task_completion_fail(self, mock_time):
        ''' Test wait_for_task_completion failed.
        '''
        module = Mock()
        try_one = dict(workOrderUserDefinedStatus='Failed')
        try_two = dict(workOrderUserDefinedStatus='Completed')
        module.client.api.get_task_by_id.side_effect = [try_one, try_two]
        result = cv_server_provision.wait_for_task_completion(module, '7')
        self.assertTrue(result)
        self.assertEqual(module.client.api.get_task_by_id.call_count, 2)
        text = ('Task 7 has reported status Failed. Please consult the CVP'
                ' admins for more information.')
        module.fail_json.assert_called_with(msg=text)
        self.assertEqual(mock_time.call_count, 1)
