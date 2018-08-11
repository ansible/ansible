#
# Copyright (c) 2018, Luca 'remix_tj' Lorenzetto <lorenzetto.luca@gmail.com>
#
# This file is part of Ansible
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


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
            - Address of the SP of target/secondary storage.
        required: true
    sp_user:
        description:
            - Username for accessing SP.
        default: sysadmin
        required: false
    sp_password:
        description:
            - password for accessing SP.
        default: sysadmin
        required: false
requirements:
  - An EMC VNX Storage device.
  - Ansible 2.7.
  - storops (0.5.10 or greater). Install using 'pip install storops'.
notes:
  - The modules prefixed with emc_vnx are built to support the EMC VNX storage platform.
    """
