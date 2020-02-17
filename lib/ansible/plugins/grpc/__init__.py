# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins import AnsiblePlugin


class GrpcBase(AnsiblePlugin):
    """
    A base class for implementing gRPC abstraction layer
    """

    __rpc__ = ['channel', 'execute']

    def __init__(self, connection):
        super(GrpcBase, self).__init__()
        self._connection = connection

    @property
    def channel(self):
        return self._connection._channel
