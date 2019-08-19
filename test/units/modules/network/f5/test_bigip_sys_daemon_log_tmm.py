# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import pytest
import sys

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("F5 Ansible modules require Python >= 2.7")

from ansible.module_utils.basic import AnsibleModule

try:
    from library.modules.bigip_sys_daemon_log_tmm import ApiParameters
    from library.modules.bigip_sys_daemon_log_tmm import ModuleParameters
    from library.modules.bigip_sys_daemon_log_tmm import ModuleManager
    from library.modules.bigip_sys_daemon_log_tmm import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_sys_daemon_log_tmm import ApiParameters
    from ansible.modules.network.f5.bigip_sys_daemon_log_tmm import ModuleParameters
    from ansible.modules.network.f5.bigip_sys_daemon_log_tmm import ModuleManager
    from ansible.modules.network.f5.bigip_sys_daemon_log_tmm import ArgumentSpec

    # Ansible 2.8 imports
    from units.compat import unittest
    from units.compat.mock import Mock

    from units.modules.utils import set_module_args


fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}


def load_fixture(name):
    path = os.path.join(fixture_path, name)

    if path in fixture_data:
        return fixture_data[path]

    with open(path) as f:
        data = f.read()

    try:
        data = json.loads(data)
    except Exception:
        pass

    fixture_data[path] = data
    return data


class TestParameters(unittest.TestCase):
    def test_module_parameters(self):
        args = dict(
            arp_log_level='warning',
            http_compression_log_level='error',
            http_log_level='error',
            ip_log_level='warning',
            irule_log_level='informational',
            layer4_log_level='notice',
            net_log_level='warning',
            os_log_level='notice',
            pva_log_level='debug',
            ssl_log_level='warning',
        )
        p = ModuleParameters(params=args)
        assert p.arp_log_level == 'warning'
        assert p.http_compression_log_level == 'error'
        assert p.http_log_level == 'error'
        assert p.ip_log_level == 'warning'
        assert p.irule_log_level == 'informational'
        assert p.layer4_log_level == 'notice'
        assert p.net_log_level == 'warning'
        assert p.os_log_level == 'notice'
        assert p.pva_log_level == 'debug'
        assert p.ssl_log_level == 'warning'

    def test_api_parameters(self):
        args = load_fixture('load_tmm_log.json')
        p = ApiParameters(params=args)
        assert p.arp_log_level == 'warning'
        assert p.http_compression_log_level == 'error'
        assert p.http_log_level == 'error'
        assert p.ip_log_level == 'warning'
        assert p.irule_log_level == 'informational'
        assert p.layer4_log_level == 'notice'
        assert p.net_log_level == 'warning'
        assert p.os_log_level == 'notice'
        assert p.pva_log_level == 'informational'
        assert p.ssl_log_level == 'warning'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_update(self, *args):
        set_module_args(dict(
            arp_log_level='debug',
            layer4_log_level='debug',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = ApiParameters(params=load_fixture('load_tmm_log.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(return_value=False)
        mm.read_current_from_device = Mock(return_value=current)
        mm.update_on_device = Mock(return_value=True)

        results = mm.exec_module()
        assert results['changed'] is True
