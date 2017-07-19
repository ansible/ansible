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
"""
This module adds shared support for Direct Connect modules.
"""

import traceback
try:
    import botocore
except ImportError:
    pass
from ansible.module_utils.ec2 import camel_dict_to_snake_dict


class DirectConnectError(Exception):
    def __init__(self, msg, last_traceback=None, response={}):
        self.msg = msg
        self.last_traceback = last_traceback
        self.response = camel_dict_to_snake_dict(response)


def delete_connection(client, connection_id):
    try:
        client.delete_connection(connectionId=connection_id)
    except botocore.exceptions.ClientError as e:
        raise DirectConnectError(msg="Failed to delete DirectConnection {0}.".format(connection_id),
                                 last_traceback=traceback.format_exc(),
                                 response=e.response)


def associate_connection_and_lag(client, connection_id, lag_id):
    try:
        client.associate_connection_with_lag(connectionId=connection_id,
                                             lagId=lag_id)
    except botocore.exceptions.ClientError as e:
        raise DirectConnectError(msg="Failed to associate Direct Connect connection {0}"
                                 " with link aggregation group {1}.".format(connection_id, lag_id),
                                 last_traceback=traceback.format_exc(),
                                 response=e.response)


def disassociate_connection_and_lag(client, connection_id, lag_id):
    try:
        client.disassociate_connection_from_lag(connectionId=connection_id,
                                                lagId=lag_id)
    except botocore.exceptions.ClientError as e:
        raise DirectConnectError(msg="Failed to disassociate Direct Connect connection {0}"
                                 " from link aggregation group {1}.".format(connection_id, lag_id),
                                 last_traceback=traceback.format_exc(),
                                 response=e.response)
