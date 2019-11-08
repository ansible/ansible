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
    from library.modules.bigip_imish_config import ModuleManager
    from library.modules.bigip_imish_config import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_imish_config import ModuleManager
    from ansible.modules.network.f5.bigip_imish_config import ArgumentSpec

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


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create(self, *args):
        set_module_args(dict(
            lines=[
                'bgp graceful-restart restart-time 120',
                'redistribute kernel route-map rhi',
                'neighbor 10.10.10.11 remote-as 65000',
                'neighbor 10.10.10.11 fall-over bfd',
                'neighbor 10.10.10.11 remote-as 65000',
                'neighbor 10.10.10.11 fall-over bfd'
            ],
            parents='router bgp 64664',
            before='bfd slow-timer 2000',
            match='exact',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        current = load_fixture('load_imish_output_1.json')
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive,
            required_if=self.spec.required_if,
            add_file_common_args=self.spec.add_file_common_args
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.read_current_from_device = Mock(return_value=current['commandResult'])
        mm.upload_file_to_device = Mock(return_value=True)
        mm.load_config_on_device = Mock(return_value=True)
        mm.remove_uploaded_file_from_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
