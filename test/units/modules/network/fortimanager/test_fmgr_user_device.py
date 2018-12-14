# Copyright 2018 Fortinet, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <https://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
from pyFMG.fortimgr import FortiManager
import pytest

try:
    from ansible.modules.network.fortimanager import fmgr_user_device
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)

fmg_instance = FortiManager("1.1.1.1", "admin", "")


def load_fixtures():
    fixture_path = os.path.join(
        os.path.dirname(__file__),
        'fixtures') + "/{filename}.json".format(
        filename=os.path.splitext(
            os.path.basename(__file__))[0])
    try:
        with open(fixture_path, "r") as fixture_file:
            fixture_data = json.load(fixture_file)
    except IOError:
        return []
    return [fixture_data]


@pytest.fixture(scope="function", params=load_fixtures())
def fixture_data(request):
    func_name = request.function.__name__.replace("test_", "")
    return request.param.get(func_name, None)


def test_fmgr_user_device_addsetdelete(fixture_data, mocker):
    mocker.patch("pyFMG.fortimgr.FortiManager._post_request", side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # comment: Created by Ansible
    # category: android-device
    # adom: root
    # master-device: None
    # user: test user
    # dynamic_mapping: {'category': None, 'comment': None, 'tags': None, 'master-device': None, 'mac': None,
    # 'avatar': None, 'type': None, 'user': None}
    # alias: test_device
    # mac: adlks123123123lk2
    # mode: set
    # tagging: {'category': None, 'name': None, 'tags': None}
    # avatar: None
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # category: android-device
    # adom: root
    # master-device: None
    # dynamic_mapping: {'category': None, 'comment': None, 'tags': None, 'master-device': None,
    # 'mac': None, 'avatar': None, 'type': None, 'user': None}
    # mode: set
    # alias: test_device
    # mac: adlks123123123lk2
    # avatar: None
    # tagging: {'category': None, 'name': None, 'tags': None}
    # user: None
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # category: android-device
    # adom: root
    # master-device: None
    # dynamic_mapping: {'category': None, 'comment': None, 'tags': None, 'master-device': None, 'mac': None,
    # 'avatar': None, 'type': None, 'user': None}
    # avatar: None
    # alias: test_device
    # mac: None
    # user: None
    # tagging: {'category': None, 'name': None, 'tags': None}
    # mode: set
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # category: android-device
    # adom: root
    # master-device: None
    # user: None
    # dynamic_mapping: {'category': None, 'comment': None, 'tags': None, 'master-device': None, 'mac': None,
    # 'avatar': None, 'type': None, 'user': None}
    # alias: testdevice
    # mac: adlks123123123lk2
    # mode: set
    # tagging: {'category': None, 'name': None, 'tags': None}
    # avatar: None
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # category: android-device
    # adom: root
    # master-device: None
    # dynamic_mapping: {'category': None, 'comment': None, 'tags': None, 'master-device': None, 'mac': None,
    # 'avatar': None, 'type': None, 'user': None}
    # mode: set
    # alias: testdevice
    # mac: 00:0000 00 00.00
    # avatar: None
    # tagging: {'category': None, 'name': None, 'tags': None}
    # user: None
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # category: android-device
    # adom: root
    # master-device: None
    # dynamic_mapping: {'category': None, 'comment': None, 'tags': None, 'master-device': None, 'mac': None,
    # 'avatar': None, 'type': None, 'user': None}
    # avatar: None
    # alias: testdevice
    # mac: a0:c9:a0:a4:50:bc
    # user: None
    # tagging: {'category': None, 'name': None, 'tags': None}
    # mode: set
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # category: android-device
    # adom: root
    # master-device: None
    # user: test user
    # dynamic_mapping: {'category': None, 'comment': None, 'tags': None, 'master-device': None, 'mac': None,
    # 'avatar': None, 'type': None, 'user': None}
    # alias: testdevice
    # mac: a0:c9:a0:a4:50:bc
    # mode: set
    # tagging: {'category': None, 'name': None, 'tags': None}
    # avatar: None
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # category: android-device
    # adom: root
    # master-device: None
    # dynamic_mapping: {'category': None, 'comment': None, 'tags': None, 'master-device': None, 'mac': None,
    # 'avatar': None, 'type': None, 'user': None}
    # mode: set
    # alias: testdevice
    # mac: a0:c9:a0:a4:50:bc
    # avatar: None
    # tagging: {'category': None, 'name': None, 'tags': None}
    # user: test user
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # category: android-device
    # adom: root
    # master-device: None
    # dynamic_mapping: {'category': None, 'comment': None, 'tags': None, 'master-device': None, 'mac': None,
    # 'avatar': None, 'type': None, 'user': None}
    # avatar: None
    # alias: testdevice
    # mac: a0:c9:a0:a4:50:bc
    # user: test user
    # tagging: {'category': None, 'name': None, 'tags': None}
    # mode: set
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # adom: root
    # master-device: None
    # dynamic_mapping: {'category': None, 'comment': None, 'mac': None, 'avatar': None, 'tags': None,
    # 'master-device': None, 'type': None, 'user': None}
    # mac: a0:c9:a0:a4:50:bc
    # user: test user
    # tagging: {'category': None, 'name': None, 'tags': None}
    # category: android-device
    # alias: testdevice
    # mode: delete
    # avatar: None
    ##################################################

    # Test using fixture 1 #
    output = fmgr_user_device.fmgr_user_device_addsetdelete(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10
    # Test using fixture 2 #
    output = fmgr_user_device.fmgr_user_device_addsetdelete(fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10
    # Test using fixture 3 #
    output = fmgr_user_device.fmgr_user_device_addsetdelete(fmg_instance, fixture_data[2]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -9998
    # Test using fixture 4 #
    output = fmgr_user_device.fmgr_user_device_addsetdelete(fmg_instance, fixture_data[3]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10
    # Test using fixture 5 #
    output = fmgr_user_device.fmgr_user_device_addsetdelete(fmg_instance, fixture_data[4]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10
    # Test using fixture 6 #
    output = fmgr_user_device.fmgr_user_device_addsetdelete(fmg_instance, fixture_data[5]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 7 #
    output = fmgr_user_device.fmgr_user_device_addsetdelete(fmg_instance, fixture_data[6]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 8 #
    output = fmgr_user_device.fmgr_user_device_addsetdelete(fmg_instance, fixture_data[7]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 9 #
    output = fmgr_user_device.fmgr_user_device_addsetdelete(fmg_instance, fixture_data[8]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 10 #
    output = fmgr_user_device.fmgr_user_device_addsetdelete(fmg_instance, fixture_data[9]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
