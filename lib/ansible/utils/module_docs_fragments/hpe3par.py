# -*- coding: utf-8 -*-
#
# Copyright (2018) Hewlett Packard Enterprise Development LP
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


class ModuleDocFragment(object):

    # HPE 3PAR doc fragment
    DOCUMENTATION = '''
options:
    storage_system_ip:
      description:
        - "The storage system IP address."
      required: true
    storage_system_password:
      description:
        - "The storage system password."
      required: true
    storage_system_username:
      description:
        - "The storage system user name."
      required: true

requirements:
  - "3PAR OS - 3.2.2 MU6, 3.3.1 MU1"
  - "Ansible - 2.4"
  - "hpe3par_sdk 1.0.0"
  - "WSAPI service should be enabled on the 3PAR storage array."
    '''

