# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.grpc import GrpcBase
from ansible.plugins.grpc.iosxr_pb import ems_grpc_pb2


class Grpc(GrpcBase):

    def __init__(self, connection):
        super(Grpc, self).__init__(connection)

    def get_config(self, section=None):
        stub = ems_grpc_pb2.beta_create_gRPCConfigOper_stub(self._connection._channel)
        message = ems_grpc_pb2.ConfigGetArgs(yangpathjson=section)
        responses = stub.GetConfig(message, self._connection._timeout, metadata=self._connection._login_credentials)
        output = {'response': '', 'error': ''}
        for response in responses:
            output['response'] += response.yangjson
            output['error'] += response.errors
        return output

    def get(self, section=None):
        stub = ems_grpc_pb2.beta_create_gRPCConfigOper_stub(self._connection._channel)
        message = ems_grpc_pb2.GetOperArgs(yangpathjson=section)
        responses = stub.GetOper(message, self._connection._timeout, metadata=self._connection._login_credentials)
        output = {'response': '', 'error': ''}
        for response in responses:
            output['response'] += response.yangjson
            output['error'] += response.errors
        return output

    def run_cli(self, command=None, display=None):
        if command is None:
            raise ValueError('command value must be provided')

        output = {'response': '', 'error': ''}
        stub = ems_grpc_pb2.beta_create_gRPCExec_stub(self._connection._channel)
        message = ems_grpc_pb2.ShowCmdArgs(cli=command)
        if display == 'text':
            responses = stub.ShowCmdTextOutput(message, self._connection._timeout, metadata=self._connection._login_credentials)
            for response in responses:
                output['response'] += response.output
                output['error'] += response.errors
        else:
            responses = stub.ShowCmdJSONOutput(message, self._connection._timeout, metadata=self._connection._login_credentials)
            for response in responses:
                output['response'] += response.jsonoutput
                output['error'] += response.errors

        return output

    @property
    def server_capabilities(self):
        capability = dict()
        capability['display'] = ['json', 'text']
        capability['data_type'] = ['config', 'oper']
        capability['supports_commit'] = True
        capability['supports_cli_command'] = True
        return capability

    def get_capabilities(self):
        result = dict()
        result['rpc'] = self.__rpc__ + ['commit', 'discard_changes']
        result['network_api'] = 'grpc'
        result['server_capabilities'] = self.server_capabilities
        return result
