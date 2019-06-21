# -*- coding: utf-8 -*-

# This module is proudly sponsored by CGI (www.cgi.com) and
# KPN (www.kpn.com).
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import pytest
from units.compat.mock import patch
from ansible.modules.monitoring import icinga2_host
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args


class TestIcinga2_HostModule(ModuleTestCase):

    def setUp(self):
        super(TestIcinga2_HostModule, self).setUp()
        self.module = icinga2_host

    def tearDown(self):
        super(TestIcinga2_HostModule, self).tearDown()

    def test_without_required_parameters(self):
        """Failure must occurs when all parameters are missing"""
        with self.assertRaises(AnsibleFailJson):
            set_module_args({})
            self.module.main()

    def test_invalid_old_token(self):
        """Failure if there is url info but no name"""
        set_module_args({
            'url': 'http://test.com',
        })
        with self.assertRaises(AnsibleFailJson):
            self.module.main()
