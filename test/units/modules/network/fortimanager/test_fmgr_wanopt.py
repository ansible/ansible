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
    from ansible.modules.network.fortimanager import fmgr_wanopt
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


def test_fmgr_wanopt_profile_addsetdelete(fixture_data, mocker):
    mocker.patch("pyFMG.fortimgr.FortiManager._post_request", side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # ftp: {'status': None, 'log-traffic': None, 'byte-caching': None, 'prefer-chunking': None, 'secure-tunnel': None,
    #  'port': None, 'tunnel-sharing': None}
    # http: {'status': None, 'ssl': None, 'tunnel-non-http': None, 'log-traffic': None, 'byte-caching': None,
    #  'unknown-http-version': None, 'prefer-chunking': None, 'tunnel-sharing': None, 'port': None, 'ssl-port': None,
    #  'secure-tunnel': None}
    # cifs: {'status': None, 'log-traffic': None, 'byte-caching': None, 'prefer-chunking': None, 'secure-tunnel': None,
    #  'port': None, 'tunnel-sharing': None}
    # adom: root
    # auth-group: None
    # mapi: {'status': None, 'log-traffic': None, 'byte-caching': None, 'secure-tunnel': None, 'port': None,
    #  'tunnel-sharing': None}
    # comments: None
    # mode: delete
    # tcp: {'status': None, 'byte-caching-opt': None, 'ssl': None, 'log-traffic': None, 'byte-caching': None,
    # 'secure-tunnel': None, 'port': None, 'ssl-port': None, 'tunnel-sharing': None}
    # transparent: None
    # name: Ansible_WanOpt_Profile
    ##################################################
    ##################################################
    # ftp: {'status': None, 'log-traffic': None, 'byte-caching': None, 'prefer-chunking': None, 'tunnel-sharing': None,
    #  'port': None, 'secure-tunnel': None}
    # http: {'status': None, 'log-traffic': None, 'tunnel-non-http': None, 'ssl': None, 'byte-caching': None,
    #  'unknown-http-version': None, 'prefer-chunking': None, 'secure-tunnel': None, 'port': None, 'ssl-port': None,
    #  'tunnel-sharing': None}
    # cifs: {'status': None, 'log-traffic': None, 'byte-caching': None, 'prefer-chunking': None, 'tunnel-sharing': None,
    #  'port': None, 'secure-tunnel': None}
    # adom: root
    # auth-group: None
    # mapi: {'status': None, 'log-traffic': None, 'byte-caching': None, 'secure-tunnel': None, 'port': None,
    #  'tunnel-sharing': None}
    # comments: Created by Ansible
    # mode: set
    # tcp: {'status': None, 'byte-caching-opt': None, 'log-traffic': None, 'ssl': None, 'byte-caching': None,
    #  'tunnel-sharing': None, 'port': None, 'ssl-port': None, 'secure-tunnel': None}
    # transparent: enable
    # name: Ansible_WanOpt_Profile
    ##################################################
    ##################################################
    # ftp: {'status': None, 'log-traffic': None, 'byte-caching': None, 'prefer-chunking': None, 'secure-tunnel': None,
    #  'port': None, 'tunnel-sharing': None}
    # http: {'status': None, 'ssl': None, 'tunnel-non-http': None, 'log-traffic': None, 'byte-caching': None,
    #  'unknown-http-version': None, 'prefer-chunking': None, 'tunnel-sharing': None, 'port': None, 'ssl-port': None,
    #  'secure-tunnel': None}
    # cifs: {'status': None, 'log-traffic': None, 'byte-caching': None, 'prefer-chunking': None, 'secure-tunnel': None,
    #  'port': None, 'tunnel-sharing': None}
    # adom: root
    # auth-group: None
    # mapi: {'status': None, 'log-traffic': None, 'byte-caching': None, 'secure-tunnel': None, 'port': None,
    #  'tunnel-sharing': None}
    # comments: None
    # mode: delete
    # tcp: {'status': None, 'byte-caching-opt': None, 'ssl': None, 'log-traffic': None, 'byte-caching': None,
    #  'secure-tunnel': None, 'port': None, 'ssl-port': None, 'tunnel-sharing': None}
    # transparent: None
    # name: Ansible_WanOpt_Profile
    ##################################################
    ##################################################
    # ftp: {'status': None, 'log-traffic': None, 'byte-caching': None, 'prefer-chunking': None, 'tunnel-sharing': None,
    #  'port': None, 'secure-tunnel': None}
    # http: {'status': None, 'log-traffic': None, 'tunnel-non-http': None, 'ssl': None, 'byte-caching': None,
    #  'unknown-http-version': None, 'prefer-chunking': None, 'secure-tunnel': None, 'port': None, 'ssl-port': None,
    #  'tunnel-sharing': None}
    # cifs: {'status': None, 'log-traffic': None, 'byte-caching': None, 'prefer-chunking': None, 'tunnel-sharing': None,
    #  'port': None, 'secure-tunnel': None}
    # adom: root
    # auth-group: None
    # mapi: {'status': None, 'log-traffic': None, 'byte-caching': None, 'secure-tunnel': None, 'port': None,
    #  'tunnel-sharing': None}
    # comments: Created by Ansible
    # mode: set
    # tcp: {'status': None, 'byte-caching-opt': None, 'log-traffic': None, 'ssl': None, 'byte-caching': None,
    #  'tunnel-sharing': None, 'port': None, 'ssl-port': None, 'secure-tunnel': None}
    # transparent: enable
    # name: Ansible_WanOpt_Profile
    ##################################################
    ##################################################
    # ftp: {'status': None, 'log-traffic': None, 'byte-caching': None, 'prefer-chunking': None, 'secure-tunnel': None,
    #  'port': None, 'tunnel-sharing': None}
    # http: {'status': None, 'ssl': None, 'tunnel-non-http': None, 'log-traffic': None, 'byte-caching': None,
    #  'unknown-http-version': None, 'prefer-chunking': None, 'tunnel-sharing': None, 'port': None, 'ssl-port': None,
    #  'secure-tunnel': None}
    # cifs: {'status': None, 'log-traffic': None, 'byte-caching': None, 'prefer-chunking': None, 'secure-tunnel': None,
    #  'port': None, 'tunnel-sharing': None}
    # adom: root
    # auth-group: None
    # mapi: {'status': None, 'log-traffic': None, 'byte-caching': None, 'secure-tunnel': None, 'port': None,
    #  'tunnel-sharing': None}
    # comments: None
    # mode: delete
    # tcp: {'status': None, 'byte-caching-opt': None, 'ssl': None, 'log-traffic': None, 'byte-caching': None,
    #  'secure-tunnel': None, 'port': None, 'ssl-port': None, 'tunnel-sharing': None}
    # transparent: None
    # name: Ansible_WanOpt_Profile
    ##################################################
    ##################################################
    # ftp: {'status': None, 'log-traffic': None, 'byte-caching': None, 'prefer-chunking': None, 'tunnel-sharing': None,
    #  'port': None, 'secure-tunnel': None}
    # http: {'status': None, 'log-traffic': None, 'tunnel-non-http': None, 'ssl': None, 'byte-caching': None,
    #  'unknown-http-version': None, 'prefer-chunking': None, 'secure-tunnel': None, 'port': None, 'ssl-port': None,
    #  'tunnel-sharing': None}
    # cifs: {'status': None, 'log-traffic': None, 'byte-caching': None, 'prefer-chunking': None, 'tunnel-sharing': None,
    #  'port': None, 'secure-tunnel': None}
    # adom: root
    # auth-group: None
    # mapi: {'status': None, 'log-traffic': None, 'byte-caching': None, 'secure-tunnel': None, 'port': None,
    #  'tunnel-sharing': None}
    # comments: None
    # mode: delete
    # tcp: {'status': None, 'byte-caching-opt': None, 'log-traffic': None, 'ssl': None, 'byte-caching': None,
    #  'tunnel-sharing': None, 'port': None, 'ssl-port': None, 'secure-tunnel': None}
    # transparent: None
    # name: Ansible_WanOpt_Profile
    ##################################################
    ##################################################
    # ftp: [{'status': 'enable', 'log-traffic': 'enable', 'byte-caching': 'enable', 'prefer-chunking': 'dynamic',
    #  'tunnel-sharing': 'private', 'port': 80, 'secure-tunnel': 'enable'}]
    # http: {'status': None, 'ssl': None, 'tunnel-non-http': None, 'log-traffic': None, 'byte-caching': None,
    #  'unknown-http-version': None, 'prefer-chunking': None, 'tunnel-sharing': None, 'port': None, 'ssl-port': None,
    #  'secure-tunnel': None}
    # cifs: [{'status': 'enable', 'log-traffic': 'enable', 'byte-caching': 'enable', 'prefer-chunking': 'dynamic',
    #  'tunnel-sharing': 'private', 'port': 80, 'secure-tunnel': 'enable'}]
    # adom: root
    # auth-group: None
    # mapi: {'status': None, 'log-traffic': None, 'byte-caching': None, 'secure-tunnel': None, 'port': None,
    #  'tunnel-sharing': None}
    # comments: Created by Ansible
    # mode: set
    # tcp: {'status': None, 'byte-caching-opt': None, 'ssl': None, 'log-traffic': None, 'byte-caching': None,
    #  'secure-tunnel': None, 'port': None, 'ssl-port': None, 'tunnel-sharing': None}
    # transparent: enable
    # name: Ansible_WanOpt_Profile
    ##################################################
    ##################################################
    # ftp: {'status': 'enable', 'log-traffic': 'enable', 'byte-caching': 'enable', 'prefer-chunking': 'dynamic',
    #  'tunnel-sharing': 'private', 'port': 80, 'secure-tunnel': 'enable'}
    # http: {'status': None, 'log-traffic': None, 'tunnel-non-http': None, 'ssl': None, 'byte-caching': None,
    #  'unknown-http-version': None, 'prefer-chunking': None, 'secure-tunnel': None, 'port': None, 'ssl-port': None,
    #  'tunnel-sharing': None}
    # cifs: {'status': 'enable', 'log-traffic': 'enable', 'byte-caching': 'enable', 'prefer-chunking': 'dynamic',
    #  'tunnel-sharing': 'private', 'port': 80, 'secure-tunnel': 'enable'}
    # adom: root
    # auth-group: None
    # mapi: {'status': None, 'log-traffic': None, 'byte-caching': None, 'secure-tunnel': None, 'port': None,
    #  'tunnel-sharing': None}
    # comments: Created by Ansible
    # name: Ansible_WanOpt_Profile
    # tcp: {'status': None, 'byte-caching-opt': None, 'log-traffic': None, 'ssl': None, 'byte-caching': None,
    #  'tunnel-sharing': None, 'port': None, 'ssl-port': None, 'secure-tunnel': None}
    # transparent: enable
    # mode: set
    ##################################################
    ##################################################
    # ftp: {'status': 'enable', 'log-traffic': 'enable', 'byte-caching': 'enable', 'prefer-chunking': 'dynamic',
    #  'secure-tunnel': 'disable', 'port': 80, 'tunnel-sharing': 'private'}
    # http: {'status': None, 'ssl': None, 'tunnel-non-http': None, 'log-traffic': None, 'byte-caching': None,
    #  'unknown-http-version': None, 'prefer-chunking': None, 'tunnel-sharing': None, 'port': None, 'ssl-port': None,
    #  'secure-tunnel': None}
    # cifs: {'status': 'enable', 'log-traffic': 'enable', 'byte-caching': 'enable', 'prefer-chunking': 'dynamic',
    #  'secure-tunnel': 'enable', 'port': 80, 'tunnel-sharing': 'private'}
    # comments: Created by Ansible
    # adom: root
    # auth-group: None
    # mapi: {'status': None, 'log-traffic': None, 'byte-caching': None, 'secure-tunnel': None, 'port': None,
    #  'tunnel-sharing': None}
    # tcp: {'status': None, 'byte-caching-opt': None, 'ssl': None, 'log-traffic': None, 'byte-caching': None,
    #  'secure-tunnel': None, 'port': None, 'ssl-port': None, 'tunnel-sharing': None}
    # mode: set
    # transparent: enable
    # name: Ansible_WanOpt_Profile
    ##################################################
    ##################################################
    # ftp: {'status': 'enable', 'log-traffic': 'enable', 'byte-caching': 'enable', 'prefer-chunking': 'dynamic',
    #  'tunnel-sharing': 'private', 'port': 80, 'secure-tunnel': 'disable'}
    # http: {'status': None, 'log-traffic': None, 'tunnel-non-http': None, 'ssl': None, 'byte-caching': None,
    #  'unknown-http-version': None, 'prefer-chunking': None, 'secure-tunnel': None, 'port': None, 'ssl-port': None,
    #  'tunnel-sharing': None}
    # cifs: {'status': 'enable', 'log-traffic': 'enable', 'byte-caching': 'enable', 'prefer-chunking': 'dynamic',
    #  'port': 80, 'tunnel-sharing': 'private'}
    # adom: root
    # auth-group: None
    # mapi: {'status': None, 'log-traffic': None, 'byte-caching': None, 'secure-tunnel': None, 'port': None,
    #  'tunnel-sharing': None}
    # tcp: {'status': None, 'byte-caching-opt': None, 'log-traffic': None, 'ssl': None, 'byte-caching': None,
    #  'tunnel-sharing': None, 'port': None, 'ssl-port': None, 'secure-tunnel': None}
    # name: Ansible_WanOpt_Profile
    # mode: set
    # transparent: enable
    # comments: Created by Ansible
    ##################################################
    ##################################################
    # ftp: {'status': None, 'log-traffic': None, 'byte-caching': None, 'prefer-chunking': None, 'secure-tunnel': None,
    #  'port': None, 'tunnel-sharing': None}
    # http: {'status': None, 'ssl': None, 'tunnel-non-http': None, 'log-traffic': None, 'byte-caching': None,
    #  'unknown-http-version': None, 'prefer-chunking': None, 'tunnel-sharing': None, 'port': None, 'ssl-port': None,
    #  'secure-tunnel': None}
    # cifs: {'status': None, 'log-traffic': None, 'byte-caching': None, 'prefer-chunking': None, 'secure-tunnel': None,
    #  'port': None, 'tunnel-sharing': None}
    # adom: root
    # auth-group: None
    # mapi: {'status': None, 'log-traffic': None, 'byte-caching': None, 'secure-tunnel': None, 'port': None,
    #  'tunnel-sharing': None}
    # tcp: {'status': None, 'byte-caching-opt': None, 'ssl': None, 'log-traffic': None, 'byte-caching': None,
    #  'secure-tunnel': None, 'port': None, 'ssl-port': None, 'tunnel-sharing': None}
    # mode: delete
    # comments: None
    # transparent: None
    # name: Ansible_WanOpt_Profile
    ##################################################
    ##################################################
    # http: {'status': None, 'log-traffic': None, 'prefer-chunking': None, 'port': None, 'ssl': None,
    #  'tunnel-non-http': None, 'byte-caching': None, 'unknown-http-version': None, 'secure-tunnel': None,
    #  'ssl-port': None, 'tunnel-sharing': None}
    # cifs: {'status': 'enable', 'log-traffic': 'enable', 'byte-caching': 'enable', 'prefer-chunking': 'dynamic',
    #  'port': 80, 'tunnel-sharing': 'private'}
    # adom: root
    # auth-group: None
    # tcp: {'status': None, 'log-traffic': None, 'byte-caching-opt': None, 'byte-caching': None, 'ssl': None,
    #  'tunnel-sharing': None, 'port': None, 'ssl-port': None, 'secure-tunnel': None}
    # transparent: enable
    # ftp: {'status': 'enable', 'log-traffic': 'enable', 'byte-caching': 'enable', 'prefer-chunking': 'dynamic',
    #  'tunnel-sharing': 'private', 'port': 80, 'secure-tunnel': 'disable'}
    # name: Ansible_WanOpt_Profile
    # mapi: {'status': None, 'log-traffic': None, 'byte-caching': None, 'secure-tunnel': None, 'port': None,
    #  'tunnel-sharing': None}
    # comments: Created by Ansible
    # mode: set
    ##################################################

    # Test using fixture 1 #
    output = fmgr_wanopt.fmgr_wanopt_profile_addsetdelete(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -3
    # Test using fixture 2 #
    output = fmgr_wanopt.fmgr_wanopt_profile_addsetdelete(fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 3 #
    output = fmgr_wanopt.fmgr_wanopt_profile_addsetdelete(fmg_instance, fixture_data[2]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 4 #
    output = fmgr_wanopt.fmgr_wanopt_profile_addsetdelete(fmg_instance, fixture_data[3]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 5 #
    output = fmgr_wanopt.fmgr_wanopt_profile_addsetdelete(fmg_instance, fixture_data[4]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 6 #
    output = fmgr_wanopt.fmgr_wanopt_profile_addsetdelete(fmg_instance, fixture_data[5]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -3
    # Test using fixture 7 #
    output = fmgr_wanopt.fmgr_wanopt_profile_addsetdelete(fmg_instance, fixture_data[6]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10
    # Test using fixture 8 #
    output = fmgr_wanopt.fmgr_wanopt_profile_addsetdelete(fmg_instance, fixture_data[7]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -9998
    # Test using fixture 9 #
    output = fmgr_wanopt.fmgr_wanopt_profile_addsetdelete(fmg_instance, fixture_data[8]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -9998
    # Test using fixture 10 #
    output = fmgr_wanopt.fmgr_wanopt_profile_addsetdelete(fmg_instance, fixture_data[9]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 11 #
    output = fmgr_wanopt.fmgr_wanopt_profile_addsetdelete(fmg_instance, fixture_data[10]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 12 #
    output = fmgr_wanopt.fmgr_wanopt_profile_addsetdelete(fmg_instance, fixture_data[11]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
