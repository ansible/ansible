#!/usr/bin/env python
#
# Copyright (c) 2017, Arista Networks EOS+
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
#   Neither the name of Arista Networks nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# 'AS IS' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import mock
import re
import time
import ansible.modules.network.cloudvision.cv_server_provision as cv_server_provision
import jinja2
from jinja2 import meta
from nose.tools import assert_equals, assert_raises, raises,\
    assert_is_instance, assert_is_not_none, assert_is_none,\
    assert_true, assert_false, assert_not_in

from ansible.module_utils.basic import AnsibleModule
from cvprac.cvp_client import CvpClient
from cvprac.cvp_api import CvpApi
from cvprac.cvp_client_errors import CvpLoginError, CvpApiError


@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.server_configurable_configlet')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.switch_in_compliance')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.switch_info')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.connect')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.AnsibleModule')
def test_main_module_args(mock_module, mock_connect, mock_info, mock_comp,
                          mock_server_conf):
    ''' Test main module args.
    '''
    mock_module_object = mock.Mock()
    mock_module_object.params = dict(action='show', switch_name='eos')
    mock_module_object.fail_json.side_effect = SystemExit('Exiting')
    mock_module.return_value = mock_module_object
    mock_connect.return_value = 'Client'
    mock_info.side_effect = CvpApiError('Error Getting Info')
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
    assert_raises(SystemExit, cv_server_provision.main)
    mock_module.assert_called_with(argument_spec=argument_spec,
                                   supports_check_mode=False)
    mock_connect.assert_called_once()
    mock_info.assert_called_once()
    mock_comp.assert_not_called()
    mock_server_conf.assert_not_called()
    mock_module_object.fail_json.assert_called_with(msg='Error Getting Info')


@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.server_configurable_configlet')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.switch_in_compliance')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.switch_info')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.connect')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.AnsibleModule')
def test_main_no_switch_configlet(mock_module, mock_connect, mock_info,
                                  mock_comp, mock_server_conf):
    ''' Test main fails if switch has no configlet for Ansible to edit.
    '''
    mock_module_object = mock.Mock()
    mock_module_object.params = dict(action='add', switch_name='eos')
    mock_module_object.fail_json.side_effect = SystemExit('Exiting')
    mock_module.return_value = mock_module_object
    mock_connect.return_value = 'Client'
    mock_info.return_value = 'Info'
    mock_server_conf.return_value = None
    assert_raises(SystemExit, cv_server_provision.main)
    mock_connect.assert_called_once()
    mock_info.assert_called_once()
    mock_comp.assert_called_once()
    mock_server_conf.assert_called_once()
    mock_module_object.fail_json.assert_called_with(
        msg='Switch eos has no configurable server ports.')


@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.port_configurable')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.server_configurable_configlet')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.switch_in_compliance')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.switch_info')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.connect')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.AnsibleModule')
def test_main_port_not_in_config(mock_module, mock_connect, mock_info,
                                 mock_comp, mock_server_conf, mock_port_conf):
    ''' Test main fails if user specified port not in configlet.
    '''
    mock_module_object = mock.Mock()
    mock_module_object.params = dict(action='add', switch_name='eos',
                                     switch_port='3')
    mock_module_object.fail_json.side_effect = SystemExit('Exiting')
    mock_module.return_value = mock_module_object
    mock_connect.return_value = 'Client'
    mock_info.return_value = 'Info'
    mock_server_conf.return_value = 'Configlet'
    mock_port_conf.return_value = None
    assert_raises(SystemExit, cv_server_provision.main)
    mock_connect.assert_called_once()
    mock_info.assert_called_once()
    mock_comp.assert_called_once()
    mock_server_conf.assert_called_once()
    mock_port_conf.assert_called_once()
    mock_module_object.fail_json.assert_called_with(
        msg='Port 3 is not configurable as a server port on switch eos.')


@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.configlet_action')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.port_configurable')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.server_configurable_configlet')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.switch_in_compliance')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.switch_info')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.connect')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.AnsibleModule')
def test_main_show(mock_module, mock_connect, mock_info, mock_comp,
                   mock_server_conf, mock_port_conf, mock_conf_action):
    ''' Test main good with show action.
    '''
    mock_module_object = mock.Mock()
    mock_module_object.params = dict(action='show', switch_name='eos',
                                     switch_port='3', auto_run=False)
    mock_module.return_value = mock_module_object
    mock_connect.return_value = 'Client'
    mock_info.return_value = 'Info'
    mock_server_conf.return_value = 'Configlet'
    mock_port_conf.return_value = 'Port'
    mock_conf_action.return_value = dict()
    cv_server_provision.main()
    mock_connect.assert_called_once()
    mock_info.assert_called_once()
    mock_comp.assert_not_called()
    mock_server_conf.assert_called_once()
    mock_port_conf.assert_called_once()
    mock_conf_action.assert_called_once()
    mock_module_object.fail_json.assert_not_called()
    return_dict = dict(changed=False, switchInfo='Info',
                       switchConfigurable=True, portConfigurable=True,
                       taskCreated=False, taskExecuted=False,
                       taskCompleted=False)
    mock_module_object.exit_json.assert_called_with(**return_dict)


@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.configlet_action')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.port_configurable')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.server_configurable_configlet')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.switch_in_compliance')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.switch_info')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.connect')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.AnsibleModule')
def test_main_add_no_auto_run(mock_module, mock_connect, mock_info, mock_comp,
                              mock_server_conf, mock_port_conf,
                              mock_conf_action):
    ''' Test main good with add action and no auto_run.
    '''
    mock_module_object = mock.Mock()
    mock_module_object.params = dict(action='add', switch_name='eos',
                                     switch_port='3', auto_run=False)
    mock_module.return_value = mock_module_object
    mock_connect.return_value = 'Client'
    mock_info.return_value = 'Info'
    mock_server_conf.return_value = 'Configlet'
    mock_port_conf.return_value = 'Port'
    mock_conf_action.return_value = dict(taskCreated=True)
    cv_server_provision.main()
    mock_connect.assert_called_once()
    mock_info.assert_called_once()
    mock_comp.assert_called_once()
    mock_server_conf.assert_called_once()
    mock_port_conf.assert_called_once()
    mock_conf_action.assert_called_once()
    mock_module_object.fail_json.assert_not_called()
    return_dict = dict(changed=False, switchInfo='Info',
                       switchConfigurable=True, portConfigurable=True,
                       taskCreated=True, taskExecuted=False,
                       taskCompleted=False)
    mock_module_object.exit_json.assert_called_with(**return_dict)


@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.wait_for_task_completion')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.configlet_update_task')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.configlet_action')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.port_configurable')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.server_configurable_configlet')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.switch_in_compliance')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.switch_info')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.connect')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.AnsibleModule')
def test_main_add_auto_run(mock_module, mock_connect, mock_info, mock_comp,
                           mock_server_conf, mock_port_conf, mock_conf_action,
                           mock_conf_task, mock_wait):
    ''' Test main good with add and auto_run. Config updated, task created.
    '''
    mock_module_object = mock.Mock()
    mock_module_object.params = dict(action='add', switch_name='eos',
                                     switch_port='3', auto_run=True)
    mock_module.return_value = mock_module_object
    mock_client_object = mock.Mock()
    mock_connect.return_value = mock_client_object
    mock_info.return_value = 'Info'
    mock_server_conf.return_value = 'Configlet'
    mock_port_conf.return_value = 'Port'
    mock_conf_action.return_value = dict(taskCreated=True, changed=True)
    mock_conf_task.return_value = '7'
    mock_wait.return_value = True
    cv_server_provision.main()
    mock_connect.assert_called_once()
    mock_info.assert_called_once()
    mock_comp.assert_called_once()
    mock_server_conf.assert_called_once()
    mock_port_conf.assert_called_once()
    mock_conf_action.assert_called_once()
    mock_conf_task.assert_called_once()
    mock_wait.assert_called_once()
    mock_module_object.fail_json.assert_not_called()
    return_dict = dict(changed=True, switchInfo='Info', taskId='7',
                       switchConfigurable=True, portConfigurable=True,
                       taskCreated=True, taskExecuted=True,
                       taskCompleted=True)
    mock_module_object.exit_json.assert_called_with(**return_dict)


@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.wait_for_task_completion')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.configlet_update_task')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.configlet_action')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.port_configurable')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.server_configurable_configlet')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.switch_in_compliance')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.switch_info')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.connect')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.AnsibleModule')
def test_main_add_auto_run_no_task(mock_module, mock_connect, mock_info,
                                   mock_comp, mock_server_conf, mock_port_conf,
                                   mock_conf_action, mock_conf_task,
                                   mock_wait):
    ''' Test main good with add and auto_run. Config not updated, no task.
    '''
    mock_module_object = mock.Mock()
    mock_module_object.params = dict(action='add', switch_name='eos',
                                     switch_port='3', auto_run=True)
    mock_module.return_value = mock_module_object
    mock_client_object = mock.Mock()
    mock_connect.return_value = mock_client_object
    mock_info.return_value = 'Info'
    mock_server_conf.return_value = 'Configlet'
    mock_port_conf.return_value = 'Port'
    mock_conf_action.return_value = dict(taskCreated=True, changed=False)
    mock_conf_task.return_value = None
    cv_server_provision.main()
    mock_connect.assert_called_once()
    mock_info.assert_called_once()
    mock_comp.assert_called_once()
    mock_server_conf.assert_called_once()
    mock_port_conf.assert_called_once()
    mock_conf_action.assert_called_once()
    mock_conf_task.assert_called_once()
    mock_wait.assert_not_called()
    mock_module_object.fail_json.assert_not_called()
    return_dict = dict(changed=False, switchInfo='Info',
                       switchConfigurable=True, portConfigurable=True,
                       taskCreated=False, taskExecuted=False,
                       taskCompleted=False)
    mock_module_object.exit_json.assert_called_with(**return_dict)


@mock.patch('cvprac.cvp_client.CvpClient.connect')
def test_connect_good(mock_client_connect):
    ''' Test connect success.
    '''
    module = mock.Mock()
    module.params = dict(host='host', username='username',
                         password='password', protocol='https', port='10')
    client = cv_server_provision.connect(module)
    assert_is_instance(client, CvpClient)
    mock_client_connect.assert_called_once()
    module.fail_json.assert_not_called()


@mock.patch('cvprac.cvp_client.CvpClient.connect')
def test_connect_fail(mock_client_connect):
    ''' Test connect failure with login error.
    '''
    module = mock.Mock()
    module.params = dict(host='host', username='username',
                         password='password', protocol='https', port='10')
    mock_client_connect.side_effect = CvpLoginError('Login Error')
    client = cv_server_provision.connect(module)
    assert_is_instance(client, CvpClient)
    mock_client_connect.assert_called_once()
    module.fail_json.assert_called_once_with(msg='Login Error')


@mock.patch('cvprac.cvp_api.CvpApi.get_device_by_name')
def test_switch_info_good(mock_api_get_device):
    ''' Test switch_info success.
    '''
    module = mock.Mock()
    module.params = dict(switch_name='eos')
    module.client = CvpClient()
    mock_api_get_device.return_value = dict(fqdn='eos')
    info = cv_server_provision.switch_info(module)
    mock_api_get_device.assert_called_once()
    assert_equals(info['fqdn'], 'eos')
    module.fail_json.assert_not_called()


@mock.patch('cvprac.cvp_api.CvpApi.get_device_by_name')
def test_switch_info_no_switch(mock_api_get_device):
    ''' Test switch_info fails.
    '''
    module = mock.Mock()
    module.params = dict(switch_name='eos')
    module.client = CvpClient()
    mock_api_get_device.return_value = None
    info = cv_server_provision.switch_info(module)
    mock_api_get_device.assert_called_once()
    assert_equals(info, None)
    module.fail_json.assert_called_once_with(
        msg="Device with name 'eos' does not exist.")


@mock.patch('cvprac.cvp_api.CvpApi.check_compliance')
def test_switch_in_compliance_good(mock_api_compliance):
    ''' Test switch_in_compliance good.
    '''
    module = mock.Mock()
    module.client = CvpClient()
    sw_info = dict(key='key', type='type', fqdn='eos')
    mock_api_compliance.return_value = dict(complianceCode='0000')
    cv_server_provision.switch_in_compliance(module, sw_info)
    mock_api_compliance.assert_called_once()
    module.fail_json.assert_not_called()


@mock.patch('cvprac.cvp_api.CvpApi.check_compliance')
def test_switch_in_compliance_fail(mock_api_compliance):
    ''' Test switch_in_compliance fail.
    '''
    module = mock.Mock()
    module.client = CvpClient()
    sw_info = dict(key='key', type='type', fqdn='eos')
    mock_api_compliance.return_value = dict(complianceCode='0001')
    cv_server_provision.switch_in_compliance(module, sw_info)
    mock_api_compliance.assert_called_once()
    module.fail_json.assert_called_with(
        msg='Switch eos is not in compliance. Returned compliance code 0001.')


@mock.patch('cvprac.cvp_api.CvpApi.get_configlets_by_device_id')
def test_server_configurable_configlet_good(mock_api_configlets):
    ''' Test server_configurable_configlet good.
    '''
    module = mock.Mock()
    module.params = dict(switch_name='eos')
    module.client = CvpClient()
    sw_info = dict(key='key', type='type', fqdn='eos')
    mock_api_configlets.return_value = [dict(name='configlet1', info='line'),
                                        dict(name='eos-server', info='info')]
    result = cv_server_provision.server_configurable_configlet(module, sw_info)
    mock_api_configlets.assert_called_once()
    assert_is_not_none(result)
    assert_equals(result['name'], 'eos-server')
    assert_equals(result['info'], 'info')


@mock.patch('cvprac.cvp_api.CvpApi.get_configlets_by_device_id')
def test_server_configurable_configlet_not_configurable(mock_api_configlets):
    ''' Test server_configurable_configlet fail. No server configlet.
    '''
    module = mock.Mock()
    module.params = dict(switch_name='eos')
    module.client = CvpClient()
    sw_info = dict(key='key', type='type', fqdn='eos')
    mock_api_configlets.return_value = [dict(name='configlet1', info='line'),
                                        dict(name='configlet2', info='info')]
    result = cv_server_provision.server_configurable_configlet(module, sw_info)
    mock_api_configlets.assert_called_once()
    assert_is_none(result)


@mock.patch('cvprac.cvp_api.CvpApi.get_configlets_by_device_id')
def test_server_configurable_configlet_no_configlets(mock_api_configlets):
    ''' Test server_configurable_configlet fail. No switch configlets.
    '''
    module = mock.Mock()
    module.params = dict(switch_name='eos')
    module.client = CvpClient()
    sw_info = dict(key='key', type='type', fqdn='eos')
    mock_api_configlets.return_value = []
    result = cv_server_provision.server_configurable_configlet(module, sw_info)
    mock_api_configlets.assert_called_once()
    assert_is_none(result)


def test_port_configurable_good():
    ''' Test port_configurable user provided switch port in configlet.
    '''
    module = mock.Mock()
    module.params = dict(switch_name='eos', switch_port='3')
    module.client = CvpClient()
    config = '!\ninterface Ethernet3\n!\ninterface Ethernet4\n!'
    configlet = dict(name='eos-server', config=config)
    result = cv_server_provision.port_configurable(module, configlet)
    assert_true(result)


def test_port_configurable_fail():
    ''' Test port_configurable user provided switch port not in configlet.
    '''
    module = mock.Mock()
    module.params = dict(switch_name='eos', switch_port='2')
    module.client = CvpClient()
    config = '!\ninterface Ethernet3\n!\ninterface Ethernet4\n!'
    configlet = dict(name='eos-server', config=config)
    result = cv_server_provision.port_configurable(module, configlet)
    assert_false(result)


def test_port_configurable_fail_no_config():
    ''' Test port_configurable configlet empty.
    '''
    module = mock.Mock()
    module.params = dict(switch_name='eos', switch_port='2')
    module.client = CvpClient()
    config = ''
    configlet = dict(name='eos-server', config=config)
    result = cv_server_provision.port_configurable(module, configlet)
    assert_false(result)


@mock.patch('cvprac.cvp_api.CvpApi.update_configlet')
def test_configlet_action_show_blank_config(mock_update_configlet):
    ''' Test configlet_action show returns current port configuration.
    '''
    module = mock.Mock()
    module.params = dict(action='show', switch_name='eos', switch_port='3')
    module.client = CvpClient()
    config = '!\ninterface Ethernet3\n!\ninterface Ethernet4\n!'
    configlet = dict(name='eos-server', key='key', config=config)
    result = cv_server_provision.configlet_action(module, configlet)
    assert_is_not_none(result)
    assert_equals(result['currentConfigBlock'], 'interface Ethernet3\n!')
    mock_update_configlet.assert_not_called()


@mock.patch('cvprac.cvp_api.CvpApi.update_configlet')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.config_from_template')
def test_configlet_action_add_with_task(mock_template, mock_update_configlet):
    ''' Test configlet_action add with change updates configlet and adds
        proper info to return data. Including task spawned info.
    '''
    module = mock.Mock()
    module.params = dict(action='add', switch_name='eos', switch_port='3')
    module.client = CvpClient()
    config = '!\ninterface Ethernet3\n!\ninterface Ethernet4\n!'
    configlet = dict(name='eos-server', key='key', config=config)
    template_config = ('interface Ethernet3\n   description Host eos'
                       ' managed by Ansible and Jinja template\n'
                       '   load-interval 30\n'
                       '   switchport\n'
                       '   switchport mode trunk\n'
                       '   no shutdown\n!')
    mock_template.return_value = template_config
    updated_configlet_return = dict(data='Configlet eos-server successfully'
                                         ' updated and task initiated.')
    mock_update_configlet.return_value = updated_configlet_return
    result = cv_server_provision.configlet_action(module, configlet)
    assert_is_not_none(result)
    assert_equals(result['oldConfigBlock'], 'interface Ethernet3\n!')
    full_config = '!\n' + template_config + '\ninterface Ethernet4\n!'
    assert_equals(result['fullConfig'], full_config)
    assert_equals(result['updateConfigletResponse'],
                  updated_configlet_return['data'])
    assert_true(result['changed'])
    assert_true(result['taskCreated'])
    mock_update_configlet.assert_called_once()


@mock.patch('cvprac.cvp_api.CvpApi.update_configlet')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.config_from_template')
def test_configlet_action_add_no_task(mock_template, mock_update_configlet):
    ''' Test configlet_action add that doesn't change configlet adds proper
        info to return data. Does not including any task info.
    '''
    module = mock.Mock()
    module.params = dict(action='add', switch_name='eos', switch_port='3')
    module.client = CvpClient()
    config = ('!\ninterface Ethernet3\n   description test\n'
              '!\ninterface Ethernet4\n!')
    configlet = dict(name='eos-server', key='key', config=config)
    template_config = 'interface Ethernet3\n   description test\n!'
    mock_template.return_value = template_config
    updated_configlet_return = dict(data='Configlet eos-server successfully'
                                         ' updated.')
    mock_update_configlet.return_value = updated_configlet_return
    result = cv_server_provision.configlet_action(module, configlet)
    assert_is_not_none(result)
    assert_equals(result['oldConfigBlock'],
                  'interface Ethernet3\n   description test\n!')
    assert_equals(result['fullConfig'], config)
    assert_equals(result['updateConfigletResponse'],
                  updated_configlet_return['data'])
    assert_not_in('changed', result)
    assert_not_in('taskCreated', result)
    mock_update_configlet.assert_called_once()


@mock.patch('cvprac.cvp_api.CvpApi.update_configlet')
def test_configlet_action_remove_with_task(mock_update_configlet):
    ''' Test configlet_action remove with change updates configlet and adds
        proper info to return data. Including task spawned info.
    '''
    module = mock.Mock()
    module.params = dict(action='remove', switch_name='eos', switch_port='3')
    module.client = CvpClient()
    config = ('!\ninterface Ethernet3\n   description test\n'
              '!\ninterface Ethernet4\n!')
    configlet = dict(name='eos-server', key='key', config=config)
    updated_configlet_return = dict(data='Configlet eos-server successfully'
                                         ' updated and task initiated.')
    mock_update_configlet.return_value = updated_configlet_return
    result = cv_server_provision.configlet_action(module, configlet)
    assert_is_not_none(result)
    assert_equals(result['oldConfigBlock'],
                  'interface Ethernet3\n   description test\n!')
    full_config = '!\ninterface Ethernet3\n!\ninterface Ethernet4\n!'
    assert_equals(result['fullConfig'], full_config)
    assert_equals(result['updateConfigletResponse'],
                  updated_configlet_return['data'])
    assert_true(result['changed'])
    assert_true(result['taskCreated'])
    mock_update_configlet.assert_called_once()


@mock.patch('cvprac.cvp_api.CvpApi.update_configlet')
def test_configlet_action_remove_no_task(mock_update_configlet):
    ''' Test configlet_action with remove that doesn't change configlet and
        adds proper info to return data. Does not including any task info.
    '''
    module = mock.Mock()
    module.params = dict(action='remove', switch_name='eos', switch_port='3')
    module.client = CvpClient()
    config = '!\ninterface Ethernet3\n!\ninterface Ethernet4\n!'
    configlet = dict(name='eos-server', key='key', config=config)
    updated_configlet_return = dict(data='Configlet eos-server successfully'
                                         ' updated.')
    mock_update_configlet.return_value = updated_configlet_return
    result = cv_server_provision.configlet_action(module, configlet)
    assert_is_not_none(result)
    assert_equals(result['oldConfigBlock'], 'interface Ethernet3\n!')
    assert_equals(result['fullConfig'], config)
    assert_equals(result['updateConfigletResponse'],
                  updated_configlet_return['data'])
    assert_not_in('changed', result)
    assert_not_in('taskCreated', result)
    mock_update_configlet.assert_called_once()


def test_current_config_empty_config():
    ''' Test current_config with empty config for port
    '''
    module = mock.Mock()
    module.params = dict(switch_name='eos', switch_port='4')
    config = '!\ninterface Ethernet3\n!\ninterface Ethernet4'
    result = cv_server_provision.current_config(module, config)
    assert_is_not_none(result)
    assert_equals(result, 'interface Ethernet4')


def test_current_config_with_config():
    ''' Test current_config with config for port
    '''
    module = mock.Mock()
    module.params = dict(switch_name='eos', switch_port='3')
    config = ('!\ninterface Ethernet3\n   description test\n'
              '!\ninterface Ethernet4\n!')
    result = cv_server_provision.current_config(module, config)
    assert_is_not_none(result)
    assert_equals(result, 'interface Ethernet3\n   description test\n!')


def test_valid_template_true():
    ''' Test valid_template true
    '''
    template = 'interface Ethernet3\n   description test\n!'
    result = cv_server_provision.valid_template('3', template)
    assert_true(result)


def test_valid_template_false():
    ''' Test valid_template false
    '''
    template = 'interface Ethernet3\n   description test\n!'
    result = cv_server_provision.valid_template('4', template)
    assert_false(result)


@mock.patch('jinja2.meta.find_undeclared_variables')
@mock.patch('jinja2.DebugUndefined')
@mock.patch('jinja2.Environment')
@mock.patch('jinja2.FileSystemLoader')
def test_config_from_template_good_no_vlan(mock_file_sys, mock_env, mock_debug,
                                           mock_find):
    ''' Test config_from_template good. No port_vlan.
    '''
    module = mock.Mock()
    module.params = dict(switch_name='eos', switch_port='3',
                         server_name='new', template='jinja.j2')
    mock_file_sys.return_value = 'file'
    mock_debug.return_value = 'debug'
    template_mock = mock.Mock()
    template_mock.render.return_value = ('interface Ethernet3\n'
                                         '   description test\n'
                                         '   switchport\n'
                                         '   switchport mode trunk\n'
                                         '   no shutdown\n!')
    env_mock = mock.Mock()
    env_mock.loader.get_source.return_value = ['one', 'two']
    env_mock.parse.return_value = 'parsed'
    env_mock.get_template.return_value = template_mock
    mock_env.return_value = env_mock
    mock_find.return_value = dict(server_name=None, switch_port=None)
    result = cv_server_provision.config_from_template(module)
    assert_is_not_none(result)
    expected = ('interface Ethernet3\n'
                '   description test\n'
                '   switchport\n'
                '   switchport mode trunk\n'
                '   no shutdown\n!')
    assert_equals(result, expected)
    mock_file_sys.assert_called_once()
    mock_env.assert_called_once()
    module.fail_json.assert_not_called()


@mock.patch('jinja2.meta.find_undeclared_variables')
@mock.patch('jinja2.DebugUndefined')
@mock.patch('jinja2.Environment')
@mock.patch('jinja2.FileSystemLoader')
def test_config_from_template_good_vlan(mock_file_sys, mock_env, mock_debug,
                                        mock_find):
    ''' Test config_from_template good. With port_vlan.
    '''
    module = mock.Mock()
    module.params = dict(switch_name='eos', switch_port='3',
                         server_name='new', template='jinja.j2', port_vlan='7')
    mock_file_sys.return_value = 'file'
    mock_debug.return_value = 'debug'
    template_mock = mock.Mock()
    template_mock.render.return_value = ('interface Ethernet3\n'
                                         '   description test\n'
                                         '   switchport\n'
                                         '   switchport access vlan 7\n'
                                         '   no shutdown\n!')
    env_mock = mock.Mock()
    env_mock.loader.get_source.return_value = ['one', 'two']
    env_mock.parse.return_value = 'parsed'
    env_mock.get_template.return_value = template_mock
    mock_env.return_value = env_mock
    mock_find.return_value = dict(server_name=None, switch_port=None,
                                  port_vlan=None)
    result = cv_server_provision.config_from_template(module)
    assert_is_not_none(result)
    expected = ('interface Ethernet3\n'
                '   description test\n'
                '   switchport\n'
                '   switchport access vlan 7\n'
                '   no shutdown\n!')
    assert_equals(result, expected)
    mock_file_sys.assert_called_once()
    mock_env.assert_called_once()
    module.fail_json.assert_not_called()


@mock.patch('jinja2.meta.find_undeclared_variables')
@mock.patch('jinja2.DebugUndefined')
@mock.patch('jinja2.Environment')
@mock.patch('jinja2.FileSystemLoader')
def test_config_from_template_fail_wrong_port(mock_file_sys, mock_env,
                                              mock_debug, mock_find):
    ''' Test config_from_template fail. Wrong port number in template.
    '''
    module = mock.Mock()
    module.params = dict(switch_name='eos', switch_port='4',
                         server_name='new', template='jinja.j2')
    mock_file_sys.return_value = 'file'
    mock_debug.return_value = 'debug'
    template_mock = mock.Mock()
    template_mock.render.return_value = ('interface Ethernet3\n'
                                         '   description test\n!')
    env_mock = mock.Mock()
    env_mock.loader.get_source.return_value = ['one', 'two']
    env_mock.parse.return_value = 'parsed'
    env_mock.get_template.return_value = template_mock
    mock_env.return_value = env_mock
    mock_find.return_value = dict(server_name=None, switch_port=None)
    result = cv_server_provision.config_from_template(module)
    assert_is_not_none(result)
    expected = 'interface Ethernet3\n   description test\n!'
    assert_equals(result, expected)
    mock_file_sys.assert_called_once()
    mock_env.assert_called_once()
    module.fail_json.assert_called_with(msg='Template content does not'
                                            ' configure proper interface'
                                            ' - %s' % expected)


@mock.patch('jinja2.meta.find_undeclared_variables')
@mock.patch('jinja2.DebugUndefined')
@mock.patch('jinja2.Environment')
@mock.patch('jinja2.FileSystemLoader')
def test_config_from_template_fail_no_vlan(mock_file_sys, mock_env,
                                           mock_debug, mock_find):
    ''' Test config_from_template fail. Template needs vlan but none provided.
    '''
    module = mock.Mock()
    module.params = dict(switch_name='eos', switch_port='3',
                         server_name='new', template='jinja.j2',
                         port_vlan=None)
    mock_file_sys.return_value = 'file'
    mock_debug.return_value = 'debug'
    template_mock = mock.Mock()
    template_mock.render.return_value = ('interface Ethernet3\n'
                                         '   description test\n!')
    env_mock = mock.Mock()
    env_mock.loader.get_source.return_value = ['one', 'two']
    env_mock.parse.return_value = 'parsed'
    env_mock.get_template.return_value = template_mock
    mock_env.return_value = env_mock
    mock_find.return_value = dict(server_name=None, switch_port=None,
                                  port_vlan=None)
    result = cv_server_provision.config_from_template(module)
    assert_is_not_none(result)
    expected = 'interface Ethernet3\n   description test\n!'
    assert_equals(result, expected)
    mock_file_sys.assert_called_once()
    mock_env.assert_called_once()
    module.fail_json.assert_called_with(msg='Template jinja.j2 requires a'
                                            ' vlan. Please re-run with vlan'
                                            ' number provided.')


def test_updated_configlet_content_add():
    ''' Test updated_configlet_content. Add config.
    '''
    module = mock.Mock()
    module.params = dict(switch_name='eos', switch_port='3')
    existing_config = '!\ninterface Ethernet3\n!\ninterface Ethernet4\n!'
    new_config_block = 'interface Ethernet3\n   description test\n!'
    result = cv_server_provision.updated_configlet_content(module,
                                                           existing_config,
                                                           new_config_block)
    expected = ('!\ninterface Ethernet3\n   description test\n'
                '!\ninterface Ethernet4\n!')
    assert_equals(result, expected)
    module.fail_json.assert_not_called()


def test_updated_configlet_content_remove():
    ''' Test updated_configlet_content. Remove config.
    '''
    module = mock.Mock()
    module.params = dict(switch_name='eos', switch_port='3')
    existing_config = ('!\ninterface Ethernet3\n   description test\n'
                       '!\ninterface Ethernet4')
    new_config_block = 'interface Ethernet3\n!'
    result = cv_server_provision.updated_configlet_content(module,
                                                           existing_config,
                                                           new_config_block)
    expected = '!\ninterface Ethernet3\n!\ninterface Ethernet4'
    assert_equals(result, expected)
    module.fail_json.assert_not_called()


@mock.patch('time.sleep')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.switch_info')
def test_configlet_update_task_good_one_try(mock_info, mock_sleep):
    ''' Test configlet_update_task gets task after one try.
    '''
    module = mock.Mock()
    task = dict(data=dict(WORKFLOW_ACTION='Configlet Push'),
                description='Configlet Assign',
                workOrderId='7')
    device_info = dict(taskIdList=[task])
    mock_info.return_value = device_info
    result = cv_server_provision.configlet_update_task(module)
    assert_equals(result, '7')
    mock_sleep.assert_not_called()
    mock_info.assert_called_once()


@mock.patch('time.sleep')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.switch_info')
def test_configlet_update_task_good_three_tries(mock_info, mock_sleep):
    ''' Test configlet_update_task gets task on third try.
    '''
    module = mock.Mock()
    task1 = dict(data=dict(WORKFLOW_ACTION='Configlet Push'),
                 description='Configlet Assign',
                 workOrderId='7')
    task2 = dict(data=dict(WORKFLOW_ACTION='Nonsense'),
                 description='Configlet Assign',
                 workOrderId='700')
    device_info = dict(taskIdList=[task1, task2])
    mock_info.side_effect = [dict(), dict(), device_info]
    result = cv_server_provision.configlet_update_task(module)
    assert_equals(result, '7')
    assert_equals(mock_sleep.call_count, 2)
    assert_equals(mock_info.call_count, 3)


@mock.patch('time.sleep')
@mock.patch('ansible.modules.network.cloudvision.cv_server_provision.switch_info')
def test_configlet_update_task_no_task(mock_info, mock_sleep):
    ''' Test configlet_update_task does not get task after three tries.
    '''
    module = mock.Mock()
    mock_info.side_effect = [dict(), dict(), dict()]
    result = cv_server_provision.configlet_update_task(module)
    assert_is_none(result)
    assert_equals(mock_sleep.call_count, 3)
    assert_equals(mock_info.call_count, 3)


@mock.patch('time.sleep')
@mock.patch('cvprac.cvp_api.CvpApi.get_task_by_id')
def test_wait_for_task_completion_good_one_try(mock_task, mock_time):
    ''' Test wait_for_task_completion completed. One Try.
    '''
    module = mock.Mock()
    module.client = CvpClient()
    mock_task.return_value = dict(workOrderUserDefinedStatus='Completed')
    result = cv_server_provision.wait_for_task_completion(module, '7')
    assert_true(result)
    mock_task.assert_called_once()
    module.fail_json.assert_not_called()
    mock_time.assert_not_called()


@mock.patch('time.sleep')
@mock.patch('cvprac.cvp_api.CvpApi.get_task_by_id')
def test_wait_for_task_completion_good_three_tries(mock_task, mock_time):
    ''' Test wait_for_task_completion completed. Three tries.
    '''
    module = mock.Mock()
    module.client = CvpClient()
    try_one_two = dict(workOrderUserDefinedStatus='Pending')
    try_three = dict(workOrderUserDefinedStatus='Completed')
    mock_task.side_effect = [try_one_two, try_one_two, try_three]
    result = cv_server_provision.wait_for_task_completion(module, '7')
    assert_true(result)
    assert_equals(mock_task.call_count, 3)
    module.fail_json.assert_not_called()
    assert_equals(mock_time.call_count, 2)


@mock.patch('time.sleep')
@mock.patch('cvprac.cvp_api.CvpApi.get_task_by_id')
def test_wait_for_task_completion_fail(mock_task, mock_time):
    ''' Test wait_for_task_completion failed.
    '''
    module = mock.Mock()
    module.client = CvpClient()
    try_one_two = dict(workOrderUserDefinedStatus='Failed')
    try_three = dict(workOrderUserDefinedStatus='Completed')
    mock_task.side_effect = [try_one_two, try_three]
    result = cv_server_provision.wait_for_task_completion(module, '7')
    assert_true(result)
    assert_equals(mock_task.call_count, 2)
    module.fail_json.assert_called_with(msg='Task 7 has reported status'
                                            ' Failed. Please consult the CVP'
                                            ' admins for more information.')
    assert_equals(mock_time.call_count, 1)
