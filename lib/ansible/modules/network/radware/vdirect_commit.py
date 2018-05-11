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
module: vdirect_commit
author: Evgeny Fedoruk @ Radware LTD (@evgenyfedoruk)
short_description: Commits pending configuration changes on Radware devices
description:
    - Commits pending configuration changes on one or more Radware devices via vDirect server.
    - For Alteon ADC device, apply, sync and save actions will be performed by default.
      Skipping of an action is possible by explicit parameter specifying.
    - For Alteon VX Container device, no sync operation will be performed
      since sync action is only relevant for Alteon ADC devices.
    - For DefensePro and AppWall devices, a bulk commit action will be performed.
      Explicit apply, sync and save actions specifying is not relevant.
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
  vdirect_validate_certs:
    description:
     - If C(no), SSL certificates will not be validated,
     - may be set as C(VDIRECT_VALIDATE_CERTS) or C(VDIRECT_VERIFY) environment variable.
     - This should only set to C(no) used on personally controlled sites using self-signed certificates.
    type: bool
    default: 'yes'
  devices:
    description:
     - List of Radware Alteon device names for commit operations.
    required: true
  apply:
    description:
     - If C(no), apply action will not be performed. Relevant for ADC devices only.
    type: bool
    default: 'yes'
  save:
    description:
     - If C(no), save action will not be performed. Relevant for ADC devices only.
    type: bool
    default: 'yes'
  sync:
    description:
     - If C(no), sync action will not be performed. Relevant for ADC devices only.
    type: bool
    default: 'yes'

requirements:
  - "vdirect-client >= 4.1.1"
'''

EXAMPLES = '''
- name: vdirect_commit
  vdirect_commit:
      vdirect_ip: 10.10.10.10
      vdirect_user: vDirect
      vdirect_password: radware
      devices: ['dev1', 'dev2']
      sync: no
'''

RETURN = '''
result:
    description: Message detailing actions result
    returned: success
    type: string
    sample: "Requested actions were successfully performed on all devices."
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from vdirect_client import rest_client
    HAS_REST_CLIENT = True
except ImportError:
    HAS_REST_CLIENT = False


SUCCESS = 'Requested actions were successfully performed on all devices.'
FAILURE = 'Failure occurred while performing requested actions on devices. See details'

ADC_DEVICE_TYPE = 'Adc'
CONTAINER_DEVICE_TYPE = 'Container'
PARTITIONED_CONTAINER_DEVICE_TYPE = 'AlteonPartitioned'
APPWALL_DEVICE_TYPE = 'AppWall'
DP_DEVICE_TYPE = 'DefensePro'

SUCCEEDED = 'succeeded'
FAILED = 'failed'
NOT_PERFORMED = 'not performed'

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
    vdirect_validate_certs=dict(
        required=False, fallback=(env_fallback, ['VDIRECT_VERIFY', 'VDIRECT_VALIDATE_CERTS']),
        default=True, type='bool'),
    vdirect_https_port=dict(
        required=False, fallback=(env_fallback, ['VDIRECT_HTTPS_PORT']),
        default=2189, type='int'),
    vdirect_http_port=dict(
        required=False, fallback=(env_fallback, ['VDIRECT_HTTP_PORT']),
        default=2188, type='int'),
    devices=dict(
        required=True, type='list'),
    apply=dict(
        required=False, default=True, type='bool'),
    save=dict(
        required=False, default=True, type='bool'),
    sync=dict(
        required=False, default=True, type='bool'),
)


class CommitException(Exception):
    def __init__(self, reason, details):
        self.reason = reason
        self.details = details

    def __str__(self):
        return 'Reason: {0}. Details:{1}.'.format(self.reason, self.details)


class MissingDeviceException(CommitException):
    def __init__(self, device_name):
        super(MissingDeviceException, self).__init__(
            'Device missing',
            'Device ' + repr(device_name) + ' does not exist')


class VdirectCommit(object):
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
                                             verify=params['vdirect_validate_certs'])
        self.devices = params['devices']
        self.apply = params['apply']
        self.save = params['save']
        self.sync = params['sync']
        self.devicesMap = {}

    def _validate_devices(self):
        for device in self.devices:
            try:
                res = self.client.adc.get(device)
                if res[rest_client.RESP_STATUS] == 200:
                    self.devicesMap.update({device: ADC_DEVICE_TYPE})
                    continue
                res = self.client.container.get(device)
                if res[rest_client.RESP_STATUS] == 200:
                    if res[rest_client.RESP_DATA]['type'] == PARTITIONED_CONTAINER_DEVICE_TYPE:
                        self.devicesMap.update({device: CONTAINER_DEVICE_TYPE})
                    continue
                res = self.client.appWall.get(device)
                if res[rest_client.RESP_STATUS] == 200:
                    self.devicesMap.update({device: APPWALL_DEVICE_TYPE})
                    continue
                res = self.client.defensePro.get(device)
                if res[rest_client.RESP_STATUS] == 200:
                    self.devicesMap.update({device: DP_DEVICE_TYPE})
                    continue

            except Exception as e:
                raise CommitException('Failed to communicate with device ' + device, str(e))

            raise MissingDeviceException(device)

    def _perform_action_and_update_result(self, device, action, perform, failure_occurred, actions_result):

        if not perform or failure_occurred:
            actions_result[action] = NOT_PERFORMED
            return True

        try:
            if self.devicesMap[device] == ADC_DEVICE_TYPE:
                res = self.client.adc.control_device(device, action)
            elif self.devicesMap[device] == CONTAINER_DEVICE_TYPE:
                res = self.client.container.control(device, action)
            elif self.devicesMap[device] == APPWALL_DEVICE_TYPE:
                res = self.client.appWall.control_device(device, action)
            elif self.devicesMap[device] == DP_DEVICE_TYPE:
                res = self.client.defensePro.control_device(device, action)

            if res[rest_client.RESP_STATUS] in [200, 204]:
                actions_result[action] = SUCCEEDED
            else:
                actions_result[action] = FAILED
                actions_result['failure_description'] = res[rest_client.RESP_STR]
                return False
        except Exception as e:
            actions_result[action] = FAILED
            actions_result['failure_description'] = 'Exception occurred while performing '\
                                                    + action + ' action. Exception: ' + str(e)
            return False

        return True

    def commit(self):
        self._validate_devices()

        result_to_return = dict()
        result_to_return['details'] = list()

        for device in self.devices:
            failure_occurred = False
            device_type = self.devicesMap[device]
            actions_result = dict()
            actions_result['device_name'] = device
            actions_result['device_type'] = device_type

            if device_type in [DP_DEVICE_TYPE, APPWALL_DEVICE_TYPE]:
                failure_occurred = not self._perform_action_and_update_result(
                    device, 'commit', True, failure_occurred, actions_result)\
                    or failure_occurred
            else:
                failure_occurred = not self._perform_action_and_update_result(
                    device, 'apply', self.apply, failure_occurred, actions_result)\
                    or failure_occurred
                if device_type != CONTAINER_DEVICE_TYPE:
                    failure_occurred = not self._perform_action_and_update_result(
                        device, 'sync', self.sync, failure_occurred, actions_result)\
                        or failure_occurred
                failure_occurred = not self._perform_action_and_update_result(
                    device, 'save', self.save, failure_occurred, actions_result)\
                    or failure_occurred

            result_to_return['details'].extend([actions_result])

            if failure_occurred:
                result_to_return['msg'] = FAILURE

        if 'msg' not in result_to_return:
            result_to_return['msg'] = SUCCESS

        return result_to_return


def main():

    module = AnsibleModule(argument_spec=meta_args)

    if not HAS_REST_CLIENT:
        module.fail_json(msg="The python vdirect-client module is required")

    try:
        vdirect_commit = VdirectCommit(module.params)
        result = vdirect_commit.commit()
        result = dict(result=result)
        module.exit_json(**result)
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
