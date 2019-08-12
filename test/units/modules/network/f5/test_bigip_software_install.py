# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
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
    from library.modules.bigip_software_install import ApiParameters
    from library.modules.bigip_software_install import ModuleParameters
    from library.modules.bigip_software_install import ModuleManager
    from library.modules.bigip_software_install import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_software_install import ApiParameters
    from ansible.modules.network.f5.bigip_software_install import ModuleParameters
    from ansible.modules.network.f5.bigip_software_install import ModuleManager
    from ansible.modules.network.f5.bigip_software_install import ArgumentSpec

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
            volume='HD1.2',
            image='BIGIP-13.0.0.0.0.1645.iso',
        )

        p = ModuleParameters(params=args)
        assert p.volume == 'HD1.2'
        assert p.image == 'BIGIP-13.0.0.0.0.1645.iso'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create(self, *args):
        set_module_args(dict(
            image='BIGIP-13.0.0.0.0.1645.iso',
            volume='HD1.2',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        current = ApiParameters()
        current.read_image_from_device = Mock(
            side_effect=[
                ['BIGIP-13.0.0.0.0.1645.iso'],
                ['BIGIP-12.1.3.4-0.0.2.iso'],
            ]
        )

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.have = current

        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)
        mm.volume_exists = Mock(return_value=True)
        mm.update_on_device = Mock(return_value=True)
        mm.wait_for_device_reboot = Mock(return_value=True)
        mm.wait_for_software_install_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
