#
# (c) 2018, Luca 'remix_tj' Lorenzetto <lorenzetto.luca@gmail.com>
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


class ModuleDocFragment(object):

    DOCUMENTATION = """
options:
  - See respective platform section for more details
requirements:
  - See respective platform section for more details
notes:
  - Ansible modules are available for EMC VNX.
"""

    # Documentation fragment for VNX (emc_vnx)
    EMC_VNX = """
options:
    sp_address:
        description:
            - Address of the SP of target/secondary storage
        required: true
    sp_user:
        description:
            - Username for accessing SP
        default: sysadmin
        required: false
    sp_password:
        description:
            - password for accessing SP
        default: sysadmin
        required: false
requirements:
  - An EMC VNX Storage device
  - Ansible 2.7
  - storops (0.5.10 or greater). Install using 'pip install storops'
notes:
  - The modules prefixed with emc_vnx are built to support the ONTAP storage platform.
    """
