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
    from ansible.modules.network.fortimanager import fmgr_secprof_web
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


def test_fmgr_webfilter_profile_addsetdelete(fixture_data, mocker):
    mocker.patch("pyFMG.fortimgr.FortiManager._post_request", side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # comment: None
    # web-extended-all-action-log: None
    # url-extraction: {'status': None, 'redirect-url': None, 'server-fqdn': None, 'redirect-header': None,
    #  'redirect-no-content': None}
    # ftgd-wf: {'filters': {'category': None, 'log': None, 'override-replacemsg': None, 'warning-duration-type': None,
    #  'warn-duration': None, 'auth-usr-grp': None, 'action': None, 'warning-prompt': None}, 'ovrd': None,
    #  'rate-image-urls': None, 'quota': {'category': None, 'value': None, 'override-replacemsg': None,
    #  'duration': None, 'type': None, 'unit': None}, 'options': None, 'rate-javascript-urls': None,
    #  'max-quota-timeout': None, 'rate-css-urls': None, 'exempt-quota': None, 'rate-crl-urls': None}
    # log-all-url: None
    # extended-log: None
    # web-filter-cookie-removal-log: None
    # https-replacemsg: None
    # web: {'log-search': None, 'bword-threshold': None, 'bword-table': None, 'whitelist': None,
    #  'youtube-restrict': None, 'safe-search': None, 'blacklist': None, 'keyword-match': None,
    #  'urlfilter-table': None, 'content-header-list': None}
    # wisp: None
    # web-filter-vbs-log: None
    # youtube-channel-filter: {'comment': None, 'channel-id': None}
    # override: {'profile': None, 'ovrd-scope': None, 'ovrd-dur-mode': None, 'profile-attribute': None,
    #  'ovrd-dur': None, 'profile-type': None, 'ovrd-user-group': None, 'ovrd-cookie': None}
    # ovrd-perm: None
    # mode: delete
    # web-content-log: None
    # web-invalid-domain-log: None
    # adom: root
    # web-filter-referer-log: None
    # inspection-mode: None
    # post-action: None
    # name: Ansible_Web_Filter_Profile
    # web-filter-command-block-log: None
    # web-filter-applet-log: None
    # web-ftgd-err-log: None
    # replacemsg-group: None
    # web-filter-jscript-log: None
    # web-filter-activex-log: None
    # web-filter-js-log: None
    # web-ftgd-quota-usage: None
    # web-filter-unknown-log: None
    # web-filter-cookie-log: None
    # youtube-channel-status: None
    # web-url-log: None
    # options: None
    # wisp-servers: None
    # wisp-algorithm: None
    ##################################################
    ##################################################
    # comment: Created by Ansible Module TEST
    # web-filter-command-block-log: enable
    # web-invalid-domain-log: enable
    # web-extended-all-action-log: enable
    # adom: root
    # ftgd-wf: {'rate-javascript-urls': None, 'quota': {'category': None, 'value': None, 'override-replacemsg': None,
    #  'duration': None, 'type': None, 'unit': None}, 'rate-image-urls': None, 'filters': {'category': None,
    #  'auth-usr-grp': None, 'log': None, 'warning-prompt': None, 'override-replacemsg': None, 'action': None,
    #  'warn-duration': None, 'warning-duration-type': None}, 'rate-css-urls': None, 'ovrd': None,
    #  'exempt-quota': None, 'max-quota-timeout': None, 'rate-crl-urls': None, 'options': None}
    # web-content-log: enable
    # web-filter-referer-log: enable
    # log-all-url: enable
    # extended-log: enable
    # inspection-mode: proxy
    # web-filter-cookie-removal-log: enable
    # post-action: block
    # web-filter-activex-log: enable
    # web-filter-cookie-log: enable
    # web: {'blacklist': None, 'log-search': None, 'keyword-match': None, 'urlfilter-table': None, 'bword-table': None,
    #  'safe-search': None, 'whitelist': None, 'content-header-list': None, 'youtube-restrict': None,
    #  'bword-threshold': None}
    # web-filter-applet-log: enable
    # web-ftgd-err-log: enable
    # replacemsg-group: None
    # web-filter-jscript-log: enable
    # web-ftgd-quota-usage: enable
    # url-extraction: {'status': None, 'server-fqdn': None, 'redirect-url': None, 'redirect-header': None,
    #  'redirect-no-content': None}
    # web-filter-js-log: enable
    # youtube-channel-filter: {'comment': None, 'channel-id': None}
    # name: Ansible_Web_Filter_Profile
    # wisp: enable
    # web-filter-vbs-log: enable
    # web-filter-unknown-log: enable
    # mode: set
    # youtube-channel-status: blacklist
    # override: {'profile': None, 'ovrd-user-group': None, 'ovrd-scope': None, 'ovrd-cookie': None,
    #  'ovrd-dur-mode': None, 'profile-attribute': None, 'ovrd-dur': None, 'profile-type': None}
    # web-url-log: enable
    # ovrd-perm: bannedword-override
    # https-replacemsg: None
    # options: js
    # wisp-servers: None
    # wisp-algorithm: auto-learning
    ##################################################

    # Test using fixture 1 #
    output = fmgr_secprof_web.fmgr_webfilter_profile_addsetdelete(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 2 #
    output = fmgr_secprof_web.fmgr_webfilter_profile_addsetdelete(fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
