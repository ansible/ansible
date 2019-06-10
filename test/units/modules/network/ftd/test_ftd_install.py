# Copyright (c) 2019 Cisco and/or its affiliates.
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
#

from __future__ import absolute_import

import pytest
from units.compat.mock import PropertyMock
from ansible.module_utils import basic
from units.modules.utils import set_module_args, exit_json, fail_json, AnsibleFailJson, AnsibleExitJson

from ansible.modules.network.ftd import ftd_install
from ansible.module_utils.network.ftd.device import FtdModel

DEFAULT_MODULE_PARAMS = dict(
    device_hostname="firepower",
    device_username="admin",
    device_password="pass",
    device_new_password="newpass",
    device_sudo_password="sudopass",
    device_ip="192.168.0.1",
    device_netmask="255.255.255.0",
    device_gateway="192.168.0.254",
    device_model=FtdModel.FTD_ASA5516_X,
    dns_server="8.8.8.8",
    console_ip="10.89.0.0",
    console_port="2004",
    console_username="console_user",
    console_password="console_pass",
    rommon_file_location="tftp://10.0.0.1/boot/ftd-boot-1.9.2.0.lfbff",
    image_file_location="http://10.0.0.1/Release/ftd-6.2.3-83.pkg",
    image_version="6.2.3-83",
    search_domains="cisco.com",
    force_install=False
)


class TestFtdInstall(object):
    module = ftd_install

    @pytest.fixture(autouse=True)
    def module_mock(self, mocker):
        mocker.patch.multiple(basic.AnsibleModule, exit_json=exit_json, fail_json=fail_json)
        mocker.patch.object(basic.AnsibleModule, '_socket_path', new_callable=PropertyMock, create=True,
                            return_value=mocker.MagicMock())

    @pytest.fixture(autouse=True)
    def connection_mock(self, mocker):
        connection_class_mock = mocker.patch('ansible.modules.network.ftd.ftd_install.Connection')
        return connection_class_mock.return_value

    @pytest.fixture
    def config_resource_mock(self, mocker):
        resource_class_mock = mocker.patch('ansible.modules.network.ftd.ftd_install.BaseConfigurationResource')
        return resource_class_mock.return_value

    @pytest.fixture(autouse=True)
    def ftd_factory_mock(self, mocker):
        return mocker.patch('ansible.modules.network.ftd.ftd_install.FtdPlatformFactory')

    @pytest.fixture(autouse=True)
    def has_kick_mock(self, mocker):
        return mocker.patch('ansible.module_utils.network.ftd.device.HAS_KICK', True)

    def test_module_should_fail_when_kick_is_not_installed(self, mocker):
        mocker.patch('ansible.module_utils.network.ftd.device.HAS_KICK', False)

        set_module_args(dict(DEFAULT_MODULE_PARAMS))
        with pytest.raises(AnsibleFailJson) as ex:
            self.module.main()

        result = ex.value.args[0]
        assert result['failed']
        assert "Firepower-kickstart library is required to run this module" in result['msg']

    def test_module_should_fail_when_platform_is_not_supported(self, config_resource_mock):
        config_resource_mock.execute_operation.return_value = {'platformModel': 'nonSupportedModel'}
        module_params = dict(DEFAULT_MODULE_PARAMS)
        del module_params['device_model']

        set_module_args(module_params)
        with pytest.raises(AnsibleFailJson) as ex:
            self.module.main()

        result = ex.value.args[0]
        assert result['failed']
        assert result['msg'] == "Platform model 'nonSupportedModel' is not supported by this module."

    def test_module_should_fail_when_device_model_is_missing_with_local_connection(self, mocker):
        mocker.patch.object(basic.AnsibleModule, '_socket_path', create=True, return_value=None)
        module_params = dict(DEFAULT_MODULE_PARAMS)
        del module_params['device_model']

        set_module_args(module_params)
        with pytest.raises(AnsibleFailJson) as ex:
            self.module.main()

        result = ex.value.args[0]
        assert result['failed']
        expected_msg = \
            "The following parameters are mandatory when the module is used with 'local' connection: device_model."
        assert expected_msg == result['msg']

    def test_module_should_fail_when_management_ip_values_are_missing_with_local_connection(self, mocker):
        mocker.patch.object(basic.AnsibleModule, '_socket_path', create=True, return_value=None)
        module_params = dict(DEFAULT_MODULE_PARAMS)
        del module_params['device_ip']
        del module_params['device_netmask']
        del module_params['device_gateway']

        set_module_args(module_params)
        with pytest.raises(AnsibleFailJson) as ex:
            self.module.main()

        result = ex.value.args[0]
        assert result['failed']
        expected_msg = "The following parameters are mandatory when the module is used with 'local' connection: " \
                       "device_gateway, device_ip, device_netmask."
        assert expected_msg == result['msg']

    def test_module_should_return_when_software_is_already_installed(self, config_resource_mock):
        config_resource_mock.execute_operation.return_value = {
            'softwareVersion': '6.3.0-11',
            'platformModel': 'Cisco ASA5516-X Threat Defense'
        }
        module_params = dict(DEFAULT_MODULE_PARAMS)
        module_params['image_version'] = '6.3.0-11'

        set_module_args(module_params)
        with pytest.raises(AnsibleExitJson) as ex:
            self.module.main()

        result = ex.value.args[0]
        assert not result['changed']
        assert result['msg'] == 'FTD already has 6.3.0-11 version of software installed.'

    def test_module_should_proceed_if_software_is_already_installed_and_force_param_given(self, config_resource_mock):
        config_resource_mock.execute_operation.return_value = {
            'softwareVersion': '6.3.0-11',
            'platformModel': 'Cisco ASA5516-X Threat Defense'
        }
        module_params = dict(DEFAULT_MODULE_PARAMS)
        module_params['image_version'] = '6.3.0-11'
        module_params['force_install'] = True

        set_module_args(module_params)
        with pytest.raises(AnsibleExitJson) as ex:
            self.module.main()

        result = ex.value.args[0]
        assert result['changed']
        assert result['msg'] == 'Successfully installed FTD image 6.3.0-11 on the firewall device.'

    def test_module_should_install_ftd_image(self, config_resource_mock, ftd_factory_mock):
        config_resource_mock.execute_operation.side_effect = [
            {
                'softwareVersion': '6.2.3-11',
                'platformModel': 'Cisco ASA5516-X Threat Defense'
            }
        ]
        module_params = dict(DEFAULT_MODULE_PARAMS)

        set_module_args(module_params)
        with pytest.raises(AnsibleExitJson) as ex:
            self.module.main()

        result = ex.value.args[0]
        assert result['changed']
        assert result['msg'] == 'Successfully installed FTD image 6.2.3-83 on the firewall device.'
        ftd_factory_mock.create.assert_called_once_with('Cisco ASA5516-X Threat Defense', DEFAULT_MODULE_PARAMS)
        ftd_factory_mock.create.return_value.install_ftd_image.assert_called_once_with(DEFAULT_MODULE_PARAMS)

    def test_module_should_fill_management_ip_values_when_missing(self, config_resource_mock, ftd_factory_mock):
        config_resource_mock.execute_operation.side_effect = [
            {
                'softwareVersion': '6.3.0-11',
                'platformModel': 'Cisco ASA5516-X Threat Defense'
            },
            {
                'items': [{
                    'ipv4Address': '192.168.1.1',
                    'ipv4NetMask': '255.255.255.0',
                    'ipv4Gateway': '192.168.0.1'
                }]
            }
        ]
        module_params = dict(DEFAULT_MODULE_PARAMS)
        expected_module_params = dict(module_params)
        del module_params['device_ip']
        del module_params['device_netmask']
        del module_params['device_gateway']
        expected_module_params.update(
            device_ip='192.168.1.1',
            device_netmask='255.255.255.0',
            device_gateway='192.168.0.1'
        )

        set_module_args(module_params)
        with pytest.raises(AnsibleExitJson):
            self.module.main()

        ftd_factory_mock.create.assert_called_once_with('Cisco ASA5516-X Threat Defense', expected_module_params)
        ftd_factory_mock.create.return_value.install_ftd_image.assert_called_once_with(expected_module_params)

    def test_module_should_fill_dns_server_when_missing(self, config_resource_mock, ftd_factory_mock):
        config_resource_mock.execute_operation.side_effect = [
            {
                'softwareVersion': '6.3.0-11',
                'platformModel': 'Cisco ASA5516-X Threat Defense'
            },
            {
                'items': [{
                    'dnsServerGroup': {
                        'id': '123'
                    }
                }]
            },
            {
                'dnsServers': [{
                    'ipAddress': '8.8.9.9'
                }]
            }
        ]
        module_params = dict(DEFAULT_MODULE_PARAMS)
        expected_module_params = dict(module_params)
        del module_params['dns_server']
        expected_module_params['dns_server'] = '8.8.9.9'

        set_module_args(module_params)
        with pytest.raises(AnsibleExitJson):
            self.module.main()

        ftd_factory_mock.create.assert_called_once_with('Cisco ASA5516-X Threat Defense', expected_module_params)
        ftd_factory_mock.create.return_value.install_ftd_image.assert_called_once_with(expected_module_params)
