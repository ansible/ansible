# Copyright (c) 2018 Cisco and/or its affiliates.
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

from ansible.module_utils.network.ftd.configuration import ParamName, PATH_PARAMS_FOR_DEFAULT_OBJ


class FtdOperations:
    """
    Utility class for common operation names
    """
    GET_SYSTEM_INFO = 'getSystemInformation'
    GET_MANAGEMENT_IP_LIST = 'getManagementIPList'
    GET_DNS_SETTING_LIST = 'getDeviceDNSSettingsList'
    GET_DNS_SERVER_GROUP = 'getDNSServerGroup'


def get_system_info(resource):
    """
    Executes `getSystemInformation` operation and returns information about the system.

    :param resource: a BaseConfigurationResource object to connect to the device
    :return: a dictionary with system information about the device and its software
    """
    path_params = {ParamName.PATH_PARAMS: PATH_PARAMS_FOR_DEFAULT_OBJ}
    system_info = resource.execute_operation(FtdOperations.GET_SYSTEM_INFO, path_params)
    return system_info
