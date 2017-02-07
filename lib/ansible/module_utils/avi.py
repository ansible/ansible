#
# Created on December 12, 2016
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
# module_check: not supported
# Avi Version: 16.3.2
#
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

import os


def avi_common_argument_spec():
    """
    Returns common arguments for all Avi modules
    :return: dict
    """
    return dict(
            controller=dict(default=os.environ.get('AVI_CONTROLLER', '')),
            username=dict(default=os.environ.get('AVI_USERNAME', '')),
            password=dict(default=os.environ.get('AVI_PASSWORD', ''), no_log=True),
            tenant=dict(default='admin'),
            tenant_uuid=dict(default=''))
