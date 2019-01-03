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

from units.compat.mock import patch
from units.modules.utils import set_module_args as _set_module_args, AnsibleExitJson, AnsibleFailJson, ModuleTestCase

import pytest

try:
    from vspk import v5_0 as vsdk
    from bambou import nurest_session
except ImportError:
    pytestmark = pytest.mark.skip('Nuage Ansible modules requires the vspk and bambou python libraries')


def set_module_args(args):
    if 'auth' not in args:
        args['auth'] = {
            'api_username': 'csproot',
            'api_password': 'csproot',
            'api_enterprise': 'csp',
            'api_url': 'https://localhost:8443',
            'api_version': 'v5_0'
        }
    return _set_module_args(args)


class MockNuageResponse(object):
    def __init__(self, status_code, reason, errors):
        self.status_code = status_code
        self.reason = reason
        self.errors = errors


class MockNuageConnection(object):
    def __init__(self, status_code, reason, errors):
        self.response = MockNuageResponse(status_code, reason, errors)


class TestNuageModule(ModuleTestCase):

    def setUp(self):
        super(TestNuageModule, self).setUp()

        def session_start(self):
            self._root_object = vsdk.NUMe()
            self._root_object.enterprise_id = 'enterprise-id'
            nurest_session._NURESTSessionCurrentContext.session = self
            return self

        self.session_mock = patch('vspk.v5_0.NUVSDSession.start', new=session_start)
        self.session_mock.start()

    def tearDown(self):
        super(TestNuageModule, self).tearDown()
        self.session_mock.stop()
