# Copyright (c) 2017 Ansible Project
#
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
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
    def __init__(self, msg, last_traceback=None, exception=None):
        self.msg = msg
        self.last_traceback = last_traceback
        self.exception = exception


def delete_connection(client, connection_id):
    try:
        client.delete_connection(connectionId=connection_id)
    except botocore.exceptions.ClientError as e:
        raise DirectConnectError(msg="Failed to delete DirectConnection {0}.".format(connection_id),
                                 last_traceback=traceback.format_exc(),
                                 exception=e)


def associate_connection_and_lag(client, connection_id, lag_id):
    try:
        client.associate_connection_with_lag(connectionId=connection_id,
                                             lagId=lag_id)
    except botocore.exceptions.ClientError as e:
        raise DirectConnectError(msg="Failed to associate Direct Connect connection {0}"
                                 " with link aggregation group {1}.".format(connection_id, lag_id),
                                 last_traceback=traceback.format_exc(),
                                 exception=e)


def disassociate_connection_and_lag(client, connection_id, lag_id):
    try:
        client.disassociate_connection_from_lag(connectionId=connection_id,
                                                lagId=lag_id)
    except botocore.exceptions.ClientError as e:
        raise DirectConnectError(msg="Failed to disassociate Direct Connect connection {0}"
                                 " from link aggregation group {1}.".format(connection_id, lag_id),
                                 last_traceback=traceback.format_exc(),
                                 exception=e)


def delete_virtual_interface(client, virtual_interface):
    try:
        client.delete_virtual_interface(virtualInterfaceId=virtual_interface)
    except botocore.exceptions.ClientError as e:
        raise DirectConnectError(msg="Could not delete virtual interface {0}".format(virtual_interface),
                                 last_traceback=traceback.format_exc(),
                                 exception=e)
