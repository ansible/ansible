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

import pytest

pytest.importorskip("kick")

from ansible.module_utils.network.ftd.device import FtdPlatformFactory, FtdModel, FtdAsa5500xPlatform, \
    Ftd2100Platform, AbstractFtdPlatform
from units.modules.network.ftd.test_ftd_install import DEFAULT_MODULE_PARAMS


class TestFtdModel(object):

    def test_has_value_should_return_true_for_existing_models(self):
        assert FtdModel.FTD_2120 in FtdModel.supported_models()
        assert FtdModel.FTD_ASA5516_X in FtdModel.supported_models()

    def test_has_value_should_return_false_for_non_existing_models(self):
        assert 'nonExistingModel' not in FtdModel.supported_models()
        assert None not in FtdModel.supported_models()


class TestFtdPlatformFactory(object):

    @pytest.fixture(autouse=True)
    def mock_devices(self, mocker):
        mocker.patch('ansible.module_utils.network.ftd.device.Kp')
        mocker.patch('ansible.module_utils.network.ftd.device.Ftd5500x')

    def test_factory_should_return_corresponding_platform(self):
        ftd_platform = FtdPlatformFactory.create(FtdModel.FTD_ASA5508_X, dict(DEFAULT_MODULE_PARAMS))
        assert type(ftd_platform) is FtdAsa5500xPlatform
        ftd_platform = FtdPlatformFactory.create(FtdModel.FTD_2130, dict(DEFAULT_MODULE_PARAMS))
        assert type(ftd_platform) is Ftd2100Platform

    def test_factory_should_raise_error_with_not_supported_model(self):
        with pytest.raises(ValueError) as ex:
            FtdPlatformFactory.create('nonExistingModel', dict(DEFAULT_MODULE_PARAMS))
        assert "FTD model 'nonExistingModel' is not supported by this module." == ex.value.args[0]


class TestAbstractFtdPlatform(object):

    def test_install_ftd_image_raise_error_on_abstract_class(self):
        with pytest.raises(NotImplementedError):
            AbstractFtdPlatform().install_ftd_image(dict(DEFAULT_MODULE_PARAMS))

    def test_supports_ftd_model_should_return_true_for_supported_models(self):
        assert Ftd2100Platform.supports_ftd_model(FtdModel.FTD_2120)
        assert FtdAsa5500xPlatform.supports_ftd_model(FtdModel.FTD_ASA5516_X)

    def test_supports_ftd_model_should_return_false_for_non_supported_models(self):
        assert not AbstractFtdPlatform.supports_ftd_model(FtdModel.FTD_2120)
        assert not Ftd2100Platform.supports_ftd_model(FtdModel.FTD_ASA5508_X)
        assert not FtdAsa5500xPlatform.supports_ftd_model(FtdModel.FTD_2120)

    def test_parse_rommon_file_location(self):
        server, path = AbstractFtdPlatform.parse_rommon_file_location('tftp://1.2.3.4/boot/rommon-boot.foo')
        assert '1.2.3.4' == server
        assert '/boot/rommon-boot.foo' == path

    def test_parse_rommon_file_location_should_fail_for_non_tftp_protocol(self):
        with pytest.raises(ValueError) as ex:
            AbstractFtdPlatform.parse_rommon_file_location('http://1.2.3.4/boot/rommon-boot.foo')
        assert 'The ROMMON image must be downloaded from TFTP server' in str(ex)


class TestFtd2100Platform(object):

    @pytest.fixture
    def kp_mock(self, mocker):
        return mocker.patch('ansible.module_utils.network.ftd.device.Kp')

    @pytest.fixture
    def module_params(self):
        return dict(DEFAULT_MODULE_PARAMS)

    def test_install_ftd_image_should_call_kp_module(self, kp_mock, module_params):
        ftd = FtdPlatformFactory.create(FtdModel.FTD_2110, module_params)
        ftd.install_ftd_image(module_params)

        assert kp_mock.called
        assert kp_mock.return_value.ssh_console.called
        ftd_line = kp_mock.return_value.ssh_console.return_value
        assert ftd_line.baseline_fp2k_ftd.called
        assert ftd_line.disconnect.called

    def test_install_ftd_image_should_call_disconnect_when_install_fails(self, kp_mock, module_params):
        ftd_line = kp_mock.return_value.ssh_console.return_value
        ftd_line.baseline_fp2k_ftd.side_effect = Exception('Something went wrong')

        ftd = FtdPlatformFactory.create(FtdModel.FTD_2120, module_params)
        with pytest.raises(Exception):
            ftd.install_ftd_image(module_params)

        assert ftd_line.baseline_fp2k_ftd.called
        assert ftd_line.disconnect.called


class TestFtdAsa5500xPlatform(object):

    @pytest.fixture
    def asa5500x_mock(self, mocker):
        return mocker.patch('ansible.module_utils.network.ftd.device.Ftd5500x')

    @pytest.fixture
    def module_params(self):
        return dict(DEFAULT_MODULE_PARAMS)

    def test_install_ftd_image_should_call_kp_module(self, asa5500x_mock, module_params):
        ftd = FtdPlatformFactory.create(FtdModel.FTD_ASA5508_X, module_params)
        ftd.install_ftd_image(module_params)

        assert asa5500x_mock.called
        assert asa5500x_mock.return_value.ssh_console.called
        ftd_line = asa5500x_mock.return_value.ssh_console.return_value
        assert ftd_line.rommon_to_new_image.called
        assert ftd_line.disconnect.called

    def test_install_ftd_image_should_call_disconnect_when_install_fails(self, asa5500x_mock, module_params):
        ftd_line = asa5500x_mock.return_value.ssh_console.return_value
        ftd_line.rommon_to_new_image.side_effect = Exception('Something went wrong')

        ftd = FtdPlatformFactory.create(FtdModel.FTD_ASA5516_X, module_params)
        with pytest.raises(Exception):
            ftd.install_ftd_image(module_params)

        assert ftd_line.rommon_to_new_image.called
        assert ftd_line.disconnect.called
