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
    from ansible.modules.network.fortimanager import fmgr_user_group
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)

fmg_instance = FortiManager("1.1.1.1", "admin", "")


def load_fixtures():
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures') + "/{filename}.json".format(filename=os.path.splitext(os.path.basename(__file__))[0])
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


def test_fmgr_user_group_addsetdelete(fixture_data, mocker):
    mocker.patch("pyFMG.fortimgr.FortiManager._post_request", side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # expire-type: None
    # auth-concurrent-override: None
    # sponsor: None
    # multiple-guest-add: None
    # guest: {'comment': None, 'name': None, 'mobile-phone': None, 'company': None, 'sponsor': None, 'user-id': None, 'password': None, 'email': None, 'expiration': None}
    # sms-custom-server: None
    # authtimeout: None
    # sso-attribute-value: None
    # member: None
    # http-digest-realm: None
    # user-id: None
    # email: None
    # match: {'server-name': None, 'group-name': None}
    # sms-server: None
    # adom: root
    # mobile-phone: None
    # company: None
    # expire: None
    # max-accounts: None
    # password: None
    # user-name: None
    # group-type: None
    # name: None
    # mode: add
    # auth-concurrent-value: None
    ##################################################
    ##################################################
    # expire-type: None
    # auth-concurrent-override: None
    # sponsor: None
    # multiple-guest-add: None
    # guest: {'comment': None, 'name': None, 'mobile-phone': None, 'company': None, 'sponsor': None, 'user-id': None, 'password': None, 'email': None, 'expiration': None}
    # sms-custom-server: None
    # authtimeout: None
    # sso-attribute-value: None
    # member: None
    # http-digest-realm: None
    # user-id: None
    # email: None
    # match: {'server-name': None, 'group-name': None}
    # sms-server: None
    # adom: root
    # mobile-phone: None
    # company: None
    # expire: None
    # max-accounts: None
    # password: None
    # user-name: None
    # group-type: None
    # name: AnsibleUserGroup
    # mode: add
    # auth-concurrent-value: None
    ##################################################
    ##################################################
    # expire-type: None
    # auth-concurrent-override: None
    # sponsor: None
    # multiple-guest-add: None
    # guest: {'comment': None, 'name': None, 'mobile-phone': None, 'company': None, 'sponsor': None, 'user-id': None, 'password': None, 'email': None, 'expiration': None}
    # sms-custom-server: None
    # authtimeout: None
    # sso-attribute-value: None
    # member: None
    # http-digest-realm: None
    # user-id: None
    # email: None
    # match: {'server-name': None, 'group-name': None}
    # sms-server: None
    # adom: root
    # mobile-phone: None
    # company: None
    # expire: None
    # max-accounts: None
    # password: auto-generate
    # user-name: None
    # group-type: None
    # name: AnsibleUserGroup
    # mode: add
    # auth-concurrent-value: None
    ##################################################
    ##################################################
    # expire-type: None
    # auth-concurrent-override: None
    # sponsor: None
    # multiple-guest-add: None
    # guest: {'comment': None, 'name': None, 'mobile-phone': None, 'company': None, 'sponsor': None, 'user-id': None, 'password': None, 'email': None, 'expiration': None}
    # sms-custom-server: None
    # authtimeout: None
    # sso-attribute-value: None
    # member: None
    # http-digest-realm: None
    # user-id: None
    # email: None
    # match: {'server-name': None, 'group-name': None}
    # sms-server: None
    # adom: root
    # mobile-phone: None
    # company: None
    # expire: None
    # max-accounts: None
    # password: auto-generate
    # user-name: None
    # group-type: None
    # name: AnsibleUserGroup
    # mode: set
    # auth-concurrent-value: None
    ##################################################
    ##################################################
    # expire-type: None
    # auth-concurrent-override: None
    # sponsor: None
    # multiple-guest-add: None
    # guest: {'comment': None, 'name': None, 'mobile-phone': None, 'company': None, 'sponsor': None, 'user-id': None, 'password': None, 'email': None, 'expiration': None}
    # sms-custom-server: None
    # authtimeout: None
    # sso-attribute-value: None
    # member: None
    # http-digest-realm: None
    # user-id: None
    # email: None
    # match: {'server-name': None, 'group-name': None}
    # sms-server: None
    # adom: root
    # mobile-phone: None
    # company: None
    # expire: None
    # max-accounts: None
    # password: auto-generate
    # user-name: None
    # group-type: None
    # name: AnsibleUserGroup
    # mode: set
    # auth-concurrent-value: None
    ##################################################
    ##################################################
    # expire-type: None
    # auth-concurrent-override: None
    # sponsor: None
    # multiple-guest-add: None
    # guest: {'comment': None, 'name': None, 'mobile-phone': None, 'company': None, 'sponsor': None, 'user-id': None, 'password': None, 'email': None, 'expiration': None}
    # sms-custom-server: None
    # authtimeout: None
    # sso-attribute-value: None
    # member: None
    # http-digest-realm: None
    # user-id: email
    # email: None
    # match: {'server-name': None, 'group-name': None}
    # sms-server: None
    # adom: root
    # mobile-phone: None
    # company: None
    # expire: None
    # max-accounts: None
    # password: auto-generate
    # user-name: enable
    # group-type: None
    # name: AnsibleUserGroup
    # mode: set
    # auth-concurrent-value: None
    ##################################################
    ##################################################
    # expire-type: None
    # auth-concurrent-override: disable
    # sponsor: None
    # multiple-guest-add: None
    # guest: {'comment': None, 'name': None, 'mobile-phone': None, 'company': None, 'sponsor': None, 'user-id': None, 'password': None, 'email': None, 'expiration': None}
    # sms-custom-server: None
    # authtimeout: None
    # sso-attribute-value: None
    # member: None
    # http-digest-realm: None
    # user-id: email
    # email: disable
    # match: {'server-name': None, 'group-name': None}
    # sms-server: None
    # adom: root
    # mobile-phone: disable
    # company: optional
    # expire: None
    # max-accounts: None
    # password: auto-generate
    # user-name: enable
    # group-type: firewall
    # name: AnsibleUserGroup
    # mode: set
    # auth-concurrent-value: None
    ##################################################
    ##################################################
    # expire-type: None
    # auth-concurrent-override: disable
    # sponsor: None
    # multiple-guest-add: None
    # guest: {'comment': None, 'name': None, 'mobile-phone': None, 'company': None, 'sponsor': None, 'user-id': None, 'password': None, 'email': None, 'expiration': None}
    # sms-custom-server: None
    # authtimeout: None
    # sso-attribute-value: None
    # member: None
    # http-digest-realm: None
    # user-id: email
    # email: enable
    # match: {'server-name': None, 'group-name': None}
    # sms-server: None
    # adom: root
    # mobile-phone: disable
    # company: optional
    # expire: None
    # max-accounts: None
    # password: auto-generate
    # user-name: enable
    # group-type: firewall
    # name: AnsibleUserGroup
    # mode: set
    # auth-concurrent-value: None
    ##################################################
    ##################################################
    # expire-type: None
    # auth-concurrent-override: disable
    # sponsor: None
    # multiple-guest-add: None
    # guest: {'comment': None, 'name': None, 'mobile-phone': None, 'company': None, 'sponsor': None, 'user-id': None, 'password': None, 'email': None, 'expiration': None}
    # sms-custom-server: None
    # authtimeout: None
    # sso-attribute-value: None
    # member: None
    # http-digest-realm: None
    # user-id: email
    # email: enable
    # match: {'server-name': None, 'group-name': None}
    # sms-server: None
    # adom: root
    # mobile-phone: disable
    # company: optional
    # expire: None
    # max-accounts: None
    # password: auto-generate
    # user-name: enable
    # group-type: firewall
    # name: AnsibleUserGroup
    # mode: set
    # auth-concurrent-value: None
    ##################################################
    ##################################################
    # expire-type: None
    # auth-concurrent-override: disable
    # sponsor: None
    # multiple-guest-add: None
    # guest: {'comment': None, 'name': None, 'mobile-phone': None, 'company': None, 'sponsor': None, 'user-id': None, 'password': None, 'email': None, 'expiration': None}
    # sms-custom-server: None
    # authtimeout: None
    # sso-attribute-value: None
    # member: None
    # http-digest-realm: None
    # user-id: email
    # email: enable
    # match: {'server-name': None, 'group-name': None}
    # sms-server: None
    # adom: root
    # mobile-phone: disable
    # company: optional
    # expire: None
    # max-accounts: None
    # password: auto-generate
    # user-name: enable
    # group-type: firewall
    # name: AnsibleUserGroup
    # mode: delete
    # auth-concurrent-value: None
    ##################################################
    ##################################################
    # expire-type: None
    # auth-concurrent-override: disable
    # sponsor: None
    # multiple-guest-add: None
    # guest: {'comment': None, 'name': None, 'mobile-phone': None, 'company': None, 'sponsor': None, 'user-id': None, 'password': None, 'email': None, 'expiration': None}
    # sms-custom-server: None
    # authtimeout: None
    # sso-attribute-value: None
    # member: None
    # http-digest-realm: None
    # user-id: email
    # email: enable
    # match: {'server-name': None, 'group-name': None}
    # sms-server: None
    # adom: root
    # mobile-phone: disable
    # company: optional
    # expire: None
    # max-accounts: None
    # password: auto-generate
    # user-name: enable
    # group-type: firewall
    # name: AnsibleUserGroup
    # mode: set
    # auth-concurrent-value: None
    ##################################################
    ##################################################
    # expire-type: None
    # auth-concurrent-override: disable
    # sponsor: None
    # multiple-guest-add: None
    # guest: {'comment': None, 'sponsor': None, 'expiration': None, 'mobile-phone': None, 'company': None, 'password': None, 'user-id': None, 'email': None, 'name': None}
    # sms-custom-server: None
    # authtimeout: None
    # sso-attribute-value: None
    # member: None
    # http-digest-realm: None
    # user-id: email
    # email: enable
    # match: {'server-name': None, 'group-name': None}
    # sms-server: None
    # adom: root
    # mobile-phone: disable
    # company: optional
    # expire: None
    # max-accounts: None
    # password: auto-generate
    # user-name: enable
    # group-type: firewall
    # name: AnsibleUserGroup
    # mode: delete
    # auth-concurrent-value: None
    ##################################################

    # Test using fixture 1 #
    output = fmgr_user_group.fmgr_user_group_addsetdelete(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -1
    # Test using fixture 2 #
    output = fmgr_user_group.fmgr_user_group_addsetdelete(fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 3 #
    output = fmgr_user_group.fmgr_user_group_addsetdelete(fmg_instance, fixture_data[2]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -2
    # Test using fixture 4 #
    output = fmgr_user_group.fmgr_user_group_addsetdelete(fmg_instance, fixture_data[3]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 5 #
    output = fmgr_user_group.fmgr_user_group_addsetdelete(fmg_instance, fixture_data[4]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 6 #
    output = fmgr_user_group.fmgr_user_group_addsetdelete(fmg_instance, fixture_data[5]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 7 #
    output = fmgr_user_group.fmgr_user_group_addsetdelete(fmg_instance, fixture_data[6]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -9998
    # Test using fixture 8 #
    output = fmgr_user_group.fmgr_user_group_addsetdelete(fmg_instance, fixture_data[7]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 9 #
    output = fmgr_user_group.fmgr_user_group_addsetdelete(fmg_instance, fixture_data[8]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 10 #
    output = fmgr_user_group.fmgr_user_group_addsetdelete(fmg_instance, fixture_data[9]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 11 #
    output = fmgr_user_group.fmgr_user_group_addsetdelete(fmg_instance, fixture_data[10]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 12 #
    output = fmgr_user_group.fmgr_user_group_addsetdelete(fmg_instance, fixture_data[11]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0

