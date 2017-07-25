# -*- coding: utf-8 -*-

# (c) 2017, Nokia
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

import json
from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes

from nose.plugins.skip import SkipTest
try:
    from vspk import v5_0 as vsdk
    from bambou import nurest_session
except ImportError:
    raise SkipTest('Nuage Ansible modules requires the vspk and bambou python libraries')


def set_module_args(args):
    set_module_args_custom_auth(args=args, auth={
        'api_username': 'csproot',
        'api_password': 'csproot',
        'api_enterprise': 'csp',
        'api_url': 'https://localhost:8443',
        'api_version': 'v5_0'
    })


def set_module_args_custom_auth(args, auth):
    args['auth'] = auth
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


class AnsibleExitJson(Exception):
    pass


class AnsibleFailJson(Exception):
    pass


class MockNuageResponse(object):
    def __init__(self, status_code, reason, errors):
        self.status_code = status_code
        self.reason = reason
        self.errors = errors


class MockNuageConnection(object):
    def __init__(self, status_code, reason, errors):
        self.response = MockNuageResponse(status_code, reason, errors)


class TestNuageModule(unittest.TestCase):

    def setUp(self):

        def session_start(self):
            self._root_object = vsdk.NUMe()
            self._root_object.enterprise_id = 'enterprise-id'
            nurest_session._NURESTSessionCurrentContext.session = self
            return self

        self.session_mock = patch('vspk.v5_0.NUVSDSession.start', new=session_start)
        self.session_mock.start()

        def fail_json(*args, **kwargs):
            kwargs['failed'] = True
            raise AnsibleFailJson(kwargs)

        self.fail_json_mock = patch('ansible.module_utils.basic.AnsibleModule.fail_json', new=fail_json)
        self.fail_json_mock.start()

        def exit_json(*args, **kwargs):
            if 'changed' not in kwargs:
                kwargs['changed'] = False
            raise AnsibleExitJson(kwargs)

        self.exit_json_mock = patch('ansible.module_utils.basic.AnsibleModule.exit_json', new=exit_json)
        self.exit_json_mock.start()

    def tearDown(self):
        self.session_mock.stop()
        self.fail_json_mock.stop()
        self.exit_json_mock.stop()
