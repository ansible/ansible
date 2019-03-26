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

from ansible.module_utils.six.moves.urllib.parse import urlparse

try:
    from kick.device2.ftd5500x.actions.ftd5500x import Ftd5500x
    from kick.device2.kp.actions import Kp

    HAS_KICK = True
except ImportError:
    HAS_KICK = False


def assert_kick_is_installed(module):
    if not HAS_KICK:
        module.fail_json(msg='Firepower-kick library is required to run this module. '
                             'Please, install it with `pip install firepower-kick` command and run the playbook again.')


class FtdModel:
    FTD_ASA5506_X = 'Cisco ASA5506-X Threat Defense'
    FTD_ASA5508_X = 'Cisco ASA5508-X Threat Defense'
    FTD_ASA5516_X = 'Cisco ASA5516-X Threat Defense'

    FTD_2110 = 'Cisco Firepower 2110 Threat Defense'
    FTD_2120 = 'Cisco Firepower 2120 Threat Defense'
    FTD_2130 = 'Cisco Firepower 2130 Threat Defense'
    FTD_2140 = 'Cisco Firepower 2140 Threat Defense'

    @classmethod
    def supported_models(cls):
        return [getattr(cls, item) for item in dir(cls) if item.startswith('FTD_')]


class FtdPlatformFactory(object):

    @staticmethod
    def create(model, module_params):
        for cls in AbstractFtdPlatform.__subclasses__():
            if cls.supports_ftd_model(model):
                return cls(module_params)
        raise ValueError("FTD model '%s' is not supported by this module." % model)


class AbstractFtdPlatform(object):
    PLATFORM_MODELS = []

    def install_ftd_image(self, params):
        raise NotImplementedError('The method should be overridden in subclass')

    @classmethod
    def supports_ftd_model(cls, model):
        return model in cls.PLATFORM_MODELS

    @staticmethod
    def parse_rommon_file_location(rommon_file_location):
        rommon_url = urlparse(rommon_file_location)
        if rommon_url.scheme != 'tftp':
            raise ValueError('The ROMMON image must be downloaded from TFTP server, other protocols are not supported.')
        return rommon_url.netloc, rommon_url.path


class Ftd2100Platform(AbstractFtdPlatform):
    PLATFORM_MODELS = [FtdModel.FTD_2110, FtdModel.FTD_2120, FtdModel.FTD_2130, FtdModel.FTD_2140]

    def __init__(self, params):
        self._ftd = Kp(hostname=params["device_hostname"],
                       login_username=params["device_username"],
                       login_password=params["device_password"],
                       sudo_password=params.get("device_sudo_password") or params["device_password"])

    def install_ftd_image(self, params):
        line = self._ftd.ssh_console(ip=params["console_ip"],
                                     port=params["console_port"],
                                     username=params["console_username"],
                                     password=params["console_password"])

        try:
            rommon_server, rommon_path = self.parse_rommon_file_location(params["rommon_file_location"])
            line.baseline_fp2k_ftd(tftp_server=rommon_server,
                                   rommon_file=rommon_path,
                                   uut_hostname=params["device_hostname"],
                                   uut_username=params["device_username"],
                                   uut_password=params.get("device_new_password") or params["device_password"],
                                   uut_ip=params["device_ip"],
                                   uut_netmask=params["device_netmask"],
                                   uut_gateway=params["device_gateway"],
                                   dns_servers=params["dns_server"],
                                   search_domains=params["search_domains"],
                                   fxos_url=params["image_file_location"],
                                   ftd_version=params["image_version"])
        finally:
            line.disconnect()


class FtdAsa5500xPlatform(AbstractFtdPlatform):
    PLATFORM_MODELS = [FtdModel.FTD_ASA5506_X, FtdModel.FTD_ASA5508_X, FtdModel.FTD_ASA5516_X]

    def __init__(self, params):
        self._ftd = Ftd5500x(hostname=params["device_hostname"],
                             login_password=params["device_password"],
                             sudo_password=params.get("device_sudo_password") or params["device_password"])

    def install_ftd_image(self, params):
        line = self._ftd.ssh_console(ip=params["console_ip"],
                                     port=params["console_port"],
                                     username=params["console_username"],
                                     password=params["console_password"])
        try:
            rommon_server, rommon_path = self.parse_rommon_file_location(params["rommon_file_location"])
            line.rommon_to_new_image(rommon_tftp_server=rommon_server,
                                     rommon_image=rommon_path,
                                     pkg_image=params["image_file_location"],
                                     uut_ip=params["device_ip"],
                                     uut_netmask=params["device_netmask"],
                                     uut_gateway=params["device_gateway"],
                                     dns_server=params["dns_server"],
                                     search_domains=params["search_domains"],
                                     hostname=params["device_hostname"])
        finally:
            line.disconnect()
