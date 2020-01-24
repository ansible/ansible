# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, F5 Networks Inc.
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
    from library.modules.bigip_asm_dos_application import ApiParameters
    from library.modules.bigip_asm_dos_application import ModuleParameters
    from library.modules.bigip_asm_dos_application import ModuleManager
    from library.modules.bigip_asm_dos_application import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_asm_dos_application import ApiParameters
    from ansible.modules.network.f5.bigip_asm_dos_application import ModuleParameters
    from ansible.modules.network.f5.bigip_asm_dos_application import ModuleManager
    from ansible.modules.network.f5.bigip_asm_dos_application import ArgumentSpec

    # Ansible 2.8 imports
    from units.compat import unittest
    from units.compat.mock import Mock
    from units.compat.mock import patch

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
            profile='dos_foo',
            geolocations=dict(
                blacklist=['Argentina', 'Montenegro'],
                whitelist=['France', 'Belgium']
            ),
            heavy_urls=dict(
                auto_detect=True,
                latency_threshold=3000,
                exclude=['/exclude1.html', '/exclude2.html'],
                include=[dict(url='include1.html', threshold='auto'),
                         dict(url='include2.html', threshold='2000')],
            ),
            mobile_detection=dict(
                enabled=True,
                allow_android_rooted_device=True,
                allow_any_android_package=True,
                allow_any_ios_package=True,
                allow_jailbroken_devices=True,
                allow_emulators=True,
                client_side_challenge_mode='cshui',
                ios_allowed_package_names=['foo', 'bar'],
                android_publishers=['cert1.crt', 'cert2.crt']
            ),
            rtbh_duration=180,
            rtbh_enable=True,
            scrubbing_duration=360,
            scrubbing_enable=True,
            single_page_application=True,
            trigger_irule=False,
            partition='Common'
        )

        p = ModuleParameters(params=args)
        assert p.profile == 'dos_foo'
        assert p.geo_whitelist == ['France', 'Belgium']
        assert p.geo_blacklist == ['Argentina', 'Montenegro']
        assert p.auto_detect == 'enabled'
        assert p.latency_threshold == 3000
        assert p.hw_url_exclude == ['/exclude1.html', '/exclude2.html']
        assert dict(name='URL/include1.html', threshold='auto', url='/include1.html') in p.hw_url_include
        assert dict(name='URL/include2.html', threshold='2000', url='/include2.html') in p.hw_url_include
        assert p.allow_android_rooted_device == 'true'
        assert p.enable_mobile_detection == 'enabled'
        assert p.allow_any_android_package == 'true'
        assert p.allow_any_ios_package == 'true'
        assert p.allow_jailbroken_devices == 'true'
        assert p.allow_emulators == 'true'
        assert p.client_side_challenge_mode == 'cshui'
        assert p.ios_allowed_package_names == ['foo', 'bar']
        assert p.android_publishers == ['/Common/cert1.crt', '/Common/cert2.crt']
        assert p.rtbh_duration == 180
        assert p.rtbh_enable == 'enabled'
        assert p.scrubbing_duration == 360
        assert p.scrubbing_enable == 'enabled'
        assert p.single_page_application == 'enabled'
        assert p.trigger_irule == 'disabled'

    def test_api_parameters(self):
        args = load_fixture('load_asm_dos.json')

        p = ApiParameters(params=args)
        assert p.geo_whitelist == ['Aland Islands']
        assert p.geo_blacklist == ['Afghanistan']
        assert p.auto_detect == 'enabled'
        assert p.latency_threshold == 1000
        assert p.hw_url_exclude == ['/exclude.html']
        assert dict(name='URL/test.htm', threshold='auto', url='/test.htm') in p.hw_url_include
        assert dict(name='URL/testy.htm', threshold='auto', url='/testy.htm') in p.hw_url_include
        assert p.allow_android_rooted_device == 'false'
        assert p.enable_mobile_detection == 'disabled'
        assert p.allow_any_android_package == 'false'
        assert p.allow_any_ios_package == 'false'
        assert p.allow_jailbroken_devices == 'true'
        assert p.allow_emulators == 'true'
        assert p.client_side_challenge_mode == 'pass'
        assert p.ios_allowed_package_names == ['foobarapp']
        assert p.android_publishers == ['/Common/ca-bundle.crt']
        assert p.rtbh_duration == 300
        assert p.rtbh_enable == 'enabled'
        assert p.scrubbing_duration == 60
        assert p.scrubbing_enable == 'enabled'
        assert p.single_page_application == 'enabled'
        assert p.trigger_irule == 'enabled'


class TestManager(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()
        try:
            self.p1 = patch('library.modules.bigip_asm_dos_application.module_provisioned')
            self.m1 = self.p1.start()
            self.m1.return_value = True
        except Exception:
            self.p1 = patch('ansible.modules.network.f5.bigip_asm_dos_application.module_provisioned')
            self.m1 = self.p1.start()
            self.m1.return_value = True

    def tearDown(self):
        self.p1.stop()

    def test_create_asm_dos_profile(self, *args):
        set_module_args(dict(
            profile='dos_foo',
            geolocations=dict(
                blacklist=['Argentina', 'Montenegro'],
                whitelist=['France', 'Belgium']
            ),
            heavy_urls=dict(
                auto_detect=True,
                latency_threshold=3000,
                exclude=['/exclude1.html', '/exclude2.html'],
                include=[dict(url='include1.html', threshold='auto'),
                         dict(url='include2.html', threshold='2000')]
            ),
            mobile_detection=dict(
                enabled=True,
                allow_android_rooted_device=True,
                allow_any_android_package=True,
                allow_any_ios_package=True,
                allow_jailbroken_devices=True,
                allow_emulators=True,
                client_side_challenge_mode='cshui',
                ios_allowed_package_names=['foo', 'bar'],
                android_publishers=['cert1.crt', 'cert2.crt']
            ),
            rtbh_duration=180,
            rtbh_enable=True,
            scrubbing_duration=360,
            scrubbing_enable=True,
            single_page_application=True,
            trigger_irule=False,
            partition='Common',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)
        mm.version_less_than_13_1 = Mock(return_value=False)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['geolocations'] == dict(blacklist=['Argentina', 'Montenegro'], whitelist=['France', 'Belgium'])
        assert results['heavy_urls'] == dict(auto_detect='yes', latency_threshold=3000,
                                             exclude=['/exclude1.html', '/exclude2.html'],
                                             include=[dict(url='/include1.html', threshold='auto'),
                                                      dict(url='/include2.html', threshold='2000')]
                                             )
        assert results['mobile_detection'] == dict(enabled='yes', allow_android_rooted_device='yes',
                                                   allow_any_android_package='yes', allow_any_ios_package='yes',
                                                   allow_jailbroken_devices='yes', allow_emulators='yes',
                                                   client_side_challenge_mode='cshui',
                                                   ios_allowed_package_names=['foo', 'bar'],
                                                   android_publishers=['/Common/cert1.crt', '/Common/cert2.crt']
                                                   )
        assert results['rtbh_duration'] == 180
        assert results['rtbh_enable'] == 'yes'
        assert results['scrubbing_duration'] == 360
        assert results['scrubbing_enable'] == 'yes'
        assert results['single_page_application'] == 'yes'
        assert results['trigger_irule'] == 'no'

    def test_update_asm_dos_profile(self, *args):
        set_module_args(dict(
            profile='test',
            heavy_urls=dict(
                latency_threshold=3000,
                exclude=['/exclude1.html', '/exclude2.html'],
                include=[dict(url='include1.html', threshold='auto'),
                         dict(url='include2.html', threshold='2000')]
            ),
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        current = ApiParameters(params=load_fixture('load_asm_dos.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=True)
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)
        mm.version_less_than_13_1 = Mock(return_value=False)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['heavy_urls'] == dict(latency_threshold=3000, exclude=['/exclude1.html', '/exclude2.html'],
                                             include=[dict(url='/include1.html', threshold='auto'),
                                                      dict(url='/include2.html', threshold='2000')]
                                             )
