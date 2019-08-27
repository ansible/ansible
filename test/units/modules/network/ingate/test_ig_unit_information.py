# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ingate Systems AB
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from units.compat.mock import patch
from ansible.modules.network.ingate import ig_unit_information
from units.modules.utils import set_module_args
from .ingate_module import TestIngateModule, load_fixture


class TestUnitInformationModule(TestIngateModule):

    module = ig_unit_information

    def setUp(self):
        super(TestUnitInformationModule, self).setUp()

        self.mock_make_request = patch('ansible.modules.network.ingate.'
                                       'ig_unit_information.make_request')
        self.make_request = self.mock_make_request.start()

        self.mock_is_ingatesdk_installed = patch('ansible.modules.network.ingate.'
                                                 'ig_unit_information.is_ingatesdk_installed')
        self.is_ingatesdk_installed = self.mock_is_ingatesdk_installed.start()

    def tearDown(self):
        super(TestUnitInformationModule, self).tearDown()
        self.mock_make_request.stop()
        self.mock_is_ingatesdk_installed.stop()

    def load_fixtures(self, fixture=None, command=None, changed=False):
        self.make_request.side_effect = [load_fixture(fixture)]
        self.is_ingatesdk_installed.return_value = True

    def test_ig_unit_information(self):
        set_module_args(
            dict(
                client=dict(
                    version='v1',
                    address='127.0.0.1',
                    scheme='http',
                    username='alice',
                    password='foobar'
                )
            )
        )

        fixture = '%s.%s' % (os.path.basename(__file__).split('.')[0], 'json')
        result = self.execute_module(fixture=fixture)
        self.assertTrue('unit-information' in result)
