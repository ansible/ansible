#!/usr/bin/python
#  -*- coding: utf-8 -*-
#
# Copyright 2017 Radware LTD.
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

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
module: vdirect_runnable
author: Evgeny Fedoruk @ Radware LTD (@evgenyfedoruk)
short_description: Runs templates and workflow actions in Radware vDirect server
description:
    - Runs configuration templates, creates workflows and runs workflow actions in Radware vDirect server.
notes:
    - Requires the Radware vdirect-client Python package on the host. This is as easy as
      C(pip install vdirect-client)
version_added: "2.5"
options:
  vdirect_ip:
    description:
     - Primary vDirect server IP address, may be set as C(VDIRECT_IP) environment variable.
    required: true
  vdirect_user:
    description:
     - vDirect server username, may be set as C(VDIRECT_USER) environment variable.
    required: true
  vdirect_password:
    description:
     - vDirect server password, may be set as C(VDIRECT_PASSWORD) environment variable.
    required: true
  vdirect_secondary_ip:
    description:
     - Secondary vDirect server IP address, may be set as C(VDIRECT_SECONDARY_IP) environment variable.
  vdirect_wait:
    description:
     - Wait for async operation to complete, may be set as C(VDIRECT_WAIT) environment variable.
    type: bool
    default: 'yes'
  vdirect_https_port:
    description:
     - vDirect server HTTPS port number, may be set as C(VDIRECT_HTTPS_PORT) environment variable.
    default: 2189
  vdirect_http_port:
    description:
     - vDirect server HTTP port number, may be set as C(VDIRECT_HTTP_PORT) environment variable.
    default: 2188
  vdirect_timeout:
    description:
     - Amount of time to wait for async operation completion [seconds],
     - may be set as C(VDIRECT_TIMEOUT) environment variable.
    default: 60
  vdirect_use_ssl:
    description:
     - If C(no), an HTTP connection will be used instead of the default HTTPS connection,
     - may be set as C(VDIRECT_HTTPS) or C(VDIRECT_USE_SSL) environment variable.
    type: bool
    default: 'yes'
  validate_certs:
    description:
     - If C(no), SSL certificates will not be validated,
     - may be set as C(VDIRECT_VALIDATE_CERTS) or C(VDIRECT_VERIFY) environment variable.
     - This should only set to C(no) used on personally controlled sites using self-signed certificates.
    type: bool
    default: 'yes'
    aliases: [ vdirect_validate_certs ]
  runnable_type:
    description:
     - vDirect runnable type.
    required: true
    choices: ['ConfigurationTemplate', 'Workflow', 'WorkflowTemplate']
  runnable_name:
    description:
     - vDirect runnable name to run.
     - May be configuration template name, workflow template name or workflow instance name.
    required: true
  action_name:
    description:
     - Workflow action name to run.
     - Required if I(runnable_type=Workflow).
  parameters:
    description:
     - Action parameters dictionary. In case of C(ConfigurationTemplate) runnable type,
     - the device connection details should always be passed as a parameter.

requirements:
  - "vdirect-client >= 4.1.1"
'''

EXAMPLES = '''
- name: vdirect_runnable
  vdirect_runnable:
      vdirect_ip: 10.10.10.10
      vdirect_user: vDirect
      vdirect_password: radware
      runnable_type: ConfigurationTemplate
      runnable_name: get_vlans
      parameters: {'vlans_needed':1,'adc':[{'type':'Adc','name':'adc-1'}]}
'''

RETURN = '''
result:
    description: Message detailing run result
    returned: success
    type: str
    sample: "Workflow action run completed."
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from vdirect_client import rest_client
    HAS_REST_CLIENT = True
except ImportError:
    HAS_REST_CLIENT = False

CONFIGURATION_TEMPLATE_RUNNABLE_TYPE = 'ConfigurationTemplate'
WORKFLOW_TEMPLATE_RUNNABLE_TYPE = 'WorkflowTemplate'
WORKFLOW_RUNNABLE_TYPE = 'Workflow'

TEMPLATE_SUCCESS = 'Configuration template run completed.'
WORKFLOW_CREATION_SUCCESS = 'Workflow created.'
WORKFLOW_ACTION_SUCCESS = 'Workflow action run completed.'

meta_args = dict(
    vdirect_ip=dict(required=True, fallback=(env_fallback, ['VDIRECT_IP'])),
    vdirect_user=dict(required=True, fallback=(env_fallback, ['VDIRECT_USER'])),
    vdirect_password=dict(
        required=True, fallback=(env_fallback, ['VDIRECT_PASSWORD']),
        no_log=True, type='str'),
    vdirect_secondary_ip=dict(
        required=False, fallback=(env_fallback, ['VDIRECT_SECONDARY_IP']),
        default=None),
    vdirect_use_ssl=dict(
        required=False, fallback=(env_fallback, ['VDIRECT_HTTPS', 'VDIRECT_USE_SSL']),
        default=True, type='bool'),
    vdirect_wait=dict(
        required=False, fallback=(env_fallback, ['VDIRECT_WAIT']),
        default=True, type='bool'),
    vdirect_timeout=dict(
        required=False, fallback=(env_fallback, ['VDIRECT_TIMEOUT']),
        default=60, type='int'),
    validate_certs=dict(
        required=False, fallback=(env_fallback, ['VDIRECT_VERIFY', 'VDIRECT_VALIDATE_CERTS']),
        default=True, type='bool', aliases=['vdirect_validate_certs']),
    vdirect_https_port=dict(
        required=False, fallback=(env_fallback, ['VDIRECT_HTTPS_PORT']),
        default=2189, type='int'),
    vdirect_http_port=dict(
        required=False, fallback=(env_fallback, ['VDIRECT_HTTP_PORT']),
        default=2188, type='int'),
    runnable_type=dict(
        required=True,
        choices=[CONFIGURATION_TEMPLATE_RUNNABLE_TYPE, WORKFLOW_TEMPLATE_RUNNABLE_TYPE, WORKFLOW_RUNNABLE_TYPE]),
    runnable_name=dict(required=True),
    action_name=dict(required=False, default=None),
    parameters=dict(required=False, type='dict', default={})
)


class RunnableException(Exception):
    def __init__(self, reason, details):
        self.reason = reason
        self.details = details

    def __str__(self):
        return 'Reason: {0}. Details:{1}.'.format(self.reason, self.details)


class WrongActionNameException(RunnableException):
    def __init__(self, action, available_actions):
        super(WrongActionNameException, self).__init__('Wrong action name ' + repr(action),
                                                       'Available actions are: ' + repr(available_actions))


class MissingActionParametersException(RunnableException):
    def __init__(self, required_parameters):
        super(MissingActionParametersException, self).__init__(
            'Action parameters missing',
            'Required parameters are: ' + repr(required_parameters))


class MissingRunnableException(RunnableException):
    def __init__(self, name):
        super(MissingRunnableException, self).__init__(
            'Runnable missing',
            'Runnable ' + name + ' is missing')


class VdirectRunnable(object):

    CREATE_WORKFLOW_ACTION = 'createWorkflow'
    RUN_ACTION = 'run'

    def __init__(self, params):
        self.client = rest_client.RestClient(params['vdirect_ip'],
                                             params['vdirect_user'],
                                             params['vdirect_password'],
                                             wait=params['vdirect_wait'],
                                             secondary_vdirect_ip=params['vdirect_secondary_ip'],
                                             https_port=params['vdirect_https_port'],
                                             http_port=params['vdirect_http_port'],
                                             timeout=params['vdirect_timeout'],
                                             https=params['vdirect_use_ssl'],
                                             verify=params['validate_certs'])
        self.params = params
        self.type = self.params['runnable_type']
        self.name = self.params['runnable_name']
        if 'parameters' in self.params:
            self.action_params = self.params['parameters']
        else:
            self.action_params = []

    def _validate_runnable_exists(self):
        res = self.client.runnable.get_runnable_objects(self.type)
        runnable_names = res[rest_client.RESP_DATA]['names']
        if self.name not in runnable_names:
            raise MissingRunnableException(self.name)

    def _validate_action_name(self):
        if self.type == WORKFLOW_TEMPLATE_RUNNABLE_TYPE:
            self.action_name = VdirectRunnable.CREATE_WORKFLOW_ACTION
        elif self.type == CONFIGURATION_TEMPLATE_RUNNABLE_TYPE:
            self.action_name = VdirectRunnable.RUN_ACTION
        else:
            self.action_name = self.params['action_name']
            res = self.client.runnable.get_available_actions(self.type, self.name)
            available_actions = res[rest_client.RESP_DATA]['names']
            if self.action_name not in available_actions:
                raise WrongActionNameException(self.action_name, available_actions)

    def _validate_required_action_params(self):
        action_params_names = [n for n in self.action_params]

        res = self.client.runnable.get_action_info(self.type, self.name, self.action_name)
        if 'parameters' in res[rest_client.RESP_DATA]:
            action_params_spec = res[rest_client.RESP_DATA]['parameters']
        else:
            action_params_spec = []

        required_action_params_dict = [{'name': p['name'], 'type': p['type']} for p in action_params_spec
                                       if p['type'] == 'alteon' or
                                       p['type'] == 'defensePro' or
                                       p['type'] == 'appWall' or
                                       p['direction'] != 'out']
        required_action_params_names = [n['name'] for n in required_action_params_dict]

        if set(required_action_params_names) & set(action_params_names) != set(required_action_params_names):
            raise MissingActionParametersException(required_action_params_dict)

    def run(self):
        self._validate_runnable_exists()
        self._validate_action_name()
        self._validate_required_action_params()

        data = self.action_params

        result = self.client.runnable.run(data, self.type, self.name, self.action_name)
        result_to_return = {'msg': ''}
        if result[rest_client.RESP_STATUS] == 200:
            if result[rest_client.RESP_DATA]['success']:
                if self.type == WORKFLOW_TEMPLATE_RUNNABLE_TYPE:
                    result_to_return['msg'] = WORKFLOW_CREATION_SUCCESS
                elif self.type == CONFIGURATION_TEMPLATE_RUNNABLE_TYPE:
                    result_to_return['msg'] = TEMPLATE_SUCCESS
                else:
                    result_to_return['msg'] = WORKFLOW_ACTION_SUCCESS

                if 'parameters' in result[rest_client.RESP_DATA]:
                    result_to_return['parameters'] = result[rest_client.RESP_DATA]['parameters']

            else:
                if 'exception' in result[rest_client.RESP_DATA]:
                    raise RunnableException(result[rest_client.RESP_DATA]['exception']['message'],
                                            result[rest_client.RESP_STR])
                else:
                    raise RunnableException('The status returned ' + str(result[rest_client.RESP_DATA]['status']),
                                            result[rest_client.RESP_STR])
        else:
            raise RunnableException(result[rest_client.RESP_REASON],
                                    result[rest_client.RESP_STR])

        return result_to_return


def main():

    module = AnsibleModule(argument_spec=meta_args,
                           required_if=[['runnable_type', WORKFLOW_RUNNABLE_TYPE, ['action_name']]])

    if not HAS_REST_CLIENT:
        module.fail_json(msg="The python vdirect-client module is required")

    try:
        vdirect_runnable = VdirectRunnable(module.params)
        result = vdirect_runnable.run()
        result = dict(result=result)
        module.exit_json(**result)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
