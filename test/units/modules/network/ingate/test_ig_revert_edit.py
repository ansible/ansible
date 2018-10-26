# -*- coding: utf-8 -*-

# Copyright (c) 2018, Ingate Systems AB
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from units.compat.mock import patch
from ansible.modules.network.ingate import ig_revert_edit
from units.modules.utils import set_module_args
from .ingate_module import TestIngateModule, load_fixture


class TestRevertEditModule(TestIngateModule):

    module = ig_revert_edit

    def setUp(self):
        super(TestRevertEditModule, self).setUp()

        self.mock_make_request = patch('ansible.modules.network.ingate.'
                                       'ig_revert_edit.make_request')
        self.make_request = self.mock_make_request.start()
        # ATM the Ingate Python SDK is not needed in this unit test.
        self.module.HAS_INGATESDK = True

    def tearDown(self):
        super(TestRevertEditModule, self).tearDown()
        self.mock_make_request.stop()

    def load_fixtures(self, fixture=None):
        self.make_request.side_effect = [load_fixture(fixture)]

    def test_ig_revert_edit(self):
        set_module_args(dict(
            client=dict(
                version='v1',
                address='127.0.0.1',
                scheme='http',
                username='alice',
                password='foobar'
            )))
        fixture = '%s.%s' % (os.path.basename(__file__).split('.')[0], 'json')
        result = self.execute_module(changed=True, fixture=fixture)
        self.assertTrue('revert-edits' in result)
