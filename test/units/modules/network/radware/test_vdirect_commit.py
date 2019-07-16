# -*- coding: utf-8 -*-
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

import os
from units.compat.mock import patch, MagicMock

from units.compat import unittest
from units.compat.mock import patch

BASE_PARAMS = {'vdirect_ip': None, 'vdirect_user': None, 'vdirect_password': None,
               'vdirect_wait': None, 'vdirect_secondary_ip': None,
               'vdirect_https_port': None, 'vdirect_http_port': None,
               'vdirect_timeout': None, 'vdirect_use_ssl': None, 'validate_certs': None}

COMMIT_PARAMS = {'devices': ['adc', 'defensepro', 'vx', 'appwall'], 'apply': True, 'save': True, 'sync': True}

COMMIT_GET_DEVICE_200_RESULT = [200, '', '', {'type': 'AlteonPartitioned'}]
COMMIT_GET_DEVICE_404_RESULT = [404, '', '', '']

COMMIT_RESULT_200 = [200, '', '', '']
COMMIT_RESULT_204 = [204, '', '', '']

MODULE_RESULT = {"msg": "Requested actions were successfully performed on all devices.",
                 "details": [{'device_name': 'adc', 'device_type': 'Adc',
                              'apply': 'succeeded', 'save': 'succeeded', 'sync': 'succeeded'},
                             {'device_name': 'defensepro', 'device_type': 'DefensePro',
                              'commit': 'succeeded'},
                             {'device_name': 'vx', 'device_type': 'Container',
                              'apply': 'succeeded', 'save': 'succeeded'},
                             {'device_name': 'appwall', 'device_type': 'AppWall',
                              'commit': 'succeeded'}]}


@patch('vdirect_client.rest_client.RestClient')
class RestClient:
    def __init__(self, vdirect_ip=None, vdirect_user=None, vdirect_password=None, wait=None,
                 secondary_vdirect_ip=None, https_port=None, http_port=None,
                 timeout=None, https=None, strict_http_results=None,
                 verify=None):
        pass


class DeviceMock:

    def __init__(self, name, client):
        self.name = name
        self.client = client
        self.get_throw = False
        self.control_throw = False
        self.exception = Exception('exception message')
        self.control_result = COMMIT_RESULT_200

    def set_control_result(self, result):
        self.control_result = result

    def throw_exception(self, get_throw=False, control_throw=False):
        self.get_throw = get_throw
        self.control_throw = control_throw

    def get(self, name):
        if self.get_throw:
            raise self.exception  # pylint: disable=E0702
        if name == self.name:
            return COMMIT_GET_DEVICE_200_RESULT
        else:
            return COMMIT_GET_DEVICE_404_RESULT

    def control_device(self, name, action):
        if self.control_throw:
            raise self.exception  # pylint: disable=E0702
        return self.control_result

    def control(self, name, action):
        return self.control_device(name, action)


class TestManager(unittest.TestCase):

    def setUp(self):
        self.module_mock = MagicMock()
        self.module_mock.rest_client.RESP_STATUS = 0
        self.module_mock.rest_client.RESP_REASON = 1
        self.module_mock.rest_client.RESP_STR = 2
        self.module_mock.rest_client.RESP_DATA = 3

    def test_missing_parameter(self, *args):
        with patch.dict('sys.modules', **{
            'vdirect_client': self.module_mock,
            'vdirect_client.rest_client.RestClient': self.module_mock,
        }):
            from ansible.modules.network.radware import vdirect_commit

            try:
                params = BASE_PARAMS.copy()
                vdirect_commit.VdirectCommit(params)
                self.fail("KeyError was not thrown for missing parameter")
            except KeyError:
                assert True

    def test_validate_devices(self, *args):
        with patch.dict('sys.modules', **{
            'vdirect_client': self.module_mock,
            'vdirect_client.rest_client.RestClient': self.module_mock,
        }):
            from ansible.modules.network.radware import vdirect_commit

            BASE_PARAMS.update(COMMIT_PARAMS)
            vdirectcommit = vdirect_commit.VdirectCommit(BASE_PARAMS)
            vdirectcommit.client.adc = DeviceMock('adc', vdirectcommit.client)
            vdirectcommit.client.container = DeviceMock('vx', vdirectcommit.client)
            vdirectcommit.client.appWall = DeviceMock('appwall', vdirectcommit.client)
            vdirectcommit.client.defensePro = DeviceMock('defensepro', vdirectcommit.client)

            vdirectcommit._validate_devices()
            assert True

            vdirectcommit.client.adc.throw_exception(True)
            try:
                vdirectcommit._validate_devices()
                self.fail("CommitException was not thrown for device communication failure")
            except vdirect_commit.CommitException:
                assert True

            vdirectcommit.client.adc.throw_exception(False)
            vdirectcommit.client.defensePro.throw_exception(True)
            try:
                vdirectcommit._validate_devices()
                self.fail("CommitException was not thrown for device communication failure")
            except vdirect_commit.CommitException:
                assert True

            vdirectcommit.client.defensePro.throw_exception(False)

            vdirectcommit.client.adc.name = 'wrong'
            try:
                vdirectcommit._validate_devices()
                self.fail("MissingDeviceException was not thrown for missing device")
            except vdirect_commit.MissingDeviceException:
                assert True

    def test_commit(self, *args):
        with patch.dict('sys.modules', **{
            'vdirect_client': self.module_mock,
            'vdirect_client.rest_client.RestClient': self.module_mock,
        }):
            from ansible.modules.network.radware import vdirect_commit

            BASE_PARAMS.update(COMMIT_PARAMS)
            vdirectcommit = vdirect_commit.VdirectCommit(BASE_PARAMS)
            vdirectcommit.client.adc = DeviceMock('adc', vdirectcommit.client)
            vdirectcommit.client.container = DeviceMock('vx', vdirectcommit.client)
            vdirectcommit.client.appWall = DeviceMock('appwall', vdirectcommit.client)
            vdirectcommit.client.defensePro = DeviceMock('defensepro', vdirectcommit.client)

            res = vdirectcommit.commit()
            assert res == MODULE_RESULT

            vdirectcommit.sync = False
            for detail in MODULE_RESULT['details']:
                if 'sync' in detail:
                    detail['sync'] = vdirect_commit.NOT_PERFORMED
            res = vdirectcommit.commit()
            assert res == MODULE_RESULT

            vdirectcommit.client.adc.control_result = COMMIT_RESULT_204
            vdirectcommit.client.adc.control_result[self.module_mock.rest_client.RESP_STATUS] = 500
            vdirectcommit.client.adc.control_result[self.module_mock.rest_client.RESP_STR] = 'Some Failure'
            MODULE_RESULT['msg'] = 'Failure occurred while performing requested actions on devices. See details'
            for detail in MODULE_RESULT['details']:
                if detail['device_name'] == 'adc':
                    detail['apply'] = vdirect_commit.FAILED
                    detail['failure_description'] = 'Some Failure'
                    detail['save'] = vdirect_commit.NOT_PERFORMED
                    detail['sync'] = vdirect_commit.NOT_PERFORMED
            res = vdirectcommit.commit()
            assert res == MODULE_RESULT

            vdirectcommit.client.adc.throw_exception(control_throw=True)
            for detail in MODULE_RESULT['details']:
                if detail['device_name'] == 'adc':
                    detail['failure_description'] = 'Exception occurred while performing apply action. ' \
                                                    'Exception: exception message'
            res = vdirectcommit.commit()
            assert res == MODULE_RESULT
