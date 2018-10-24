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
    from ansible.modules.network.fortimanager import fmgr_secprof_spam
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


def test_fmgr_spamfilter_profile_addsetdelete(fixture_data, mocker):
    mocker.patch("pyFMG.fortimgr.FortiManager._post_request", side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # comment: None
    # smtp: {'local-override': None, 'hdrip': None, 'log': None, 'tag-type': None, 'tag-msg': None, 'action': None}
    # spam-log: None
    # gmail: {'log': None}
    # spam-bword-table: None
    # mapi: {'action': None, 'log': None}
    # flow-based: None
    # spam-mheader-table: None
    # spam-log-fortiguard-response: None
    # yahoo-mail: {'log': None}
    # adom: root
    # pop3: {'action': None, 'tag-msg': None, 'log': None, 'tag-type': None}
    # external: None
    # spam-rbl-table: None
    # imap: {'action': None, 'tag-msg': None, 'log': None, 'tag-type': None}
    # spam-iptrust-table: None
    # replacemsg-group: None
    # name: Ansible_Spam_Filter_Profile
    # spam-bwl-table: None
    # spam-filtering: None
    # msn-hotmail: {'log': None}
    # spam-bword-threshold: None
    # mode: delete
    # options: None
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # smtp: {'local-override': None, 'hdrip': None, 'log': None, 'tag-type': None, 'tag-msg': None, 'action': None}
    # yahoo-mail: {'log': 'enable'}
    # gmail: {'log': 'enable'}
    # spam-bword-table: None
    # mapi: {'action': None, 'log': 'enable'}
    # flow-based: enable
    # spam-mheader-table: None
    # spam-log-fortiguard-response: enable
    # spam-log: enable
    # adom: root
    # pop3: {'action': None, 'log': None, 'tag-type': None, 'tag-msg': None}
    # external: enable
    # spam-rbl-table: None
    # imap: {'action': None, 'log': None, 'tag-type': None, 'tag-msg': None}
    # spam-iptrust-table: None
    # name: Ansible_Spam_Filter_Profile
    # replacemsg-group: None
    # spam-bwl-table: None
    # spam-filtering: enable
    # msn-hotmail: {'log': 'enable'}
    # spam-bword-threshold: 10
    # mode: set
    # options: bannedword
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # smtp: {'local-override': None, 'hdrip': None, 'log': None, 'tag-type': None, 'tag-msg': None, 'action': None}
    # spam-log: None
    # gmail: {'log': None}
    # spam-bword-table: None
    # mapi: {'action': None, 'log': None}
    # flow-based: enable
    # spam-mheader-table: None
    # spam-log-fortiguard-response: enable
    # yahoo-mail: {'log': None}
    # adom: root
    # pop3: {'action': None, 'tag-msg': None, 'tag-type': None, 'log': None}
    # external: enable
    # spam-rbl-table: None
    # imap: {'action': None, 'tag-msg': None, 'tag-type': None, 'log': None}
    # spam-iptrust-table: None
    # replacemsg-group: None
    # name: Ansible_Spam_Filter_Profile
    # spam-bwl-table: None
    # spam-filtering: enable
    # msn-hotmail: {'log': None}
    # spam-bword-threshold: 10
    # mode: set
    # options: bannedword
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # smtp: {'local-override': None, 'hdrip': None, 'log': None, 'tag-type': None, 'tag-msg': None, 'action': None}
    # yahoo-mail: {'log': 'enable'}
    # gmail: {'log': 'enable'}
    # spam-bword-table: None
    # mapi: {'action': None, 'log': 'enable'}
    # flow-based: enable
    # spam-mheader-table: None
    # spam-log-fortiguard-response: enable
    # spam-log: enable
    # adom: root
    # pop3: {'action': None, 'tag-type': None, 'log': None, 'tag-msg': None}
    # external: enable
    # spam-rbl-table: None
    # imap: {'action': None, 'tag-type': None, 'log': None, 'tag-msg': None}
    # spam-iptrust-table: None
    # name: Ansible_Spam_Filter_Profile
    # replacemsg-group: None
    # spam-bwl-table: None
    # spam-filtering: enable
    # msn-hotmail: {'log': 'enable'}
    # spam-bword-threshold: 10
    # mode: set
    # options: bannedword
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # smtp: {'local-override': None, 'hdrip': None, 'log': None, 'tag-type': None, 'tag-msg': None, 'action': None}
    # spam-log: None
    # gmail: {'log': None}
    # spam-bword-table: None
    # mapi: {'action': None, 'log': None}
    # flow-based: enable
    # spam-mheader-table: None
    # spam-log-fortiguard-response: enable
    # yahoo-mail: {'log': None}
    # adom: root
    # pop3: {'action': None, 'tag-msg': None, 'log': None, 'tag-type': None}
    # external: enable
    # spam-rbl-table: None
    # imap: {'action': None, 'tag-msg': None, 'log': None, 'tag-type': None}
    # spam-iptrust-table: None
    # replacemsg-group: None
    # name: Ansible_Spam_Filter_Profile
    # spam-bwl-table: None
    # spam-filtering: enable
    # msn-hotmail: {'log': None}
    # spam-bword-threshold: 10
    # mode: set
    # options: ['bannedword', 'spamfsip']
    ##################################################
    ##################################################
    # comment: None
    # smtp: {'local-override': None, 'hdrip': None, 'log': None, 'tag-type': None, 'tag-msg': None, 'action': None}
    # yahoo-mail: {'log': None}
    # gmail: {'log': None}
    # spam-bword-table: None
    # mapi: {'action': None, 'log': None}
    # flow-based: None
    # spam-mheader-table: None
    # spam-log-fortiguard-response: None
    # spam-log: None
    # adom: root
    # pop3: {'action': None, 'log': None, 'tag-type': None, 'tag-msg': None}
    # external: None
    # spam-rbl-table: None
    # imap: {'action': None, 'log': None, 'tag-type': None, 'tag-msg': None}
    # spam-iptrust-table: None
    # name: Ansible_Spam_Filter_Profile
    # replacemsg-group: None
    # spam-bwl-table: None
    # spam-filtering: None
    # msn-hotmail: {'log': None}
    # spam-bword-threshold: None
    # mode: delete
    # options: None
    ##################################################
    ##################################################
    # comment: None
    # smtp: {'local-override': None, 'hdrip': None, 'log': None, 'tag-type': None, 'tag-msg': None, 'action': None}
    # spam-log: None
    # gmail: {'log': None}
    # spam-bword-table: None
    # mapi: {'action': None, 'log': None}
    # flow-based: None
    # spam-mheader-table: None
    # spam-log-fortiguard-response: None
    # yahoo-mail: {'log': None}
    # adom: root
    # pop3: {'action': None, 'tag-msg': None, 'tag-type': None, 'log': None}
    # external: None
    # spam-rbl-table: None
    # imap: {'action': None, 'tag-msg': None, 'tag-type': None, 'log': None}
    # spam-iptrust-table: None
    # replacemsg-group: None
    # name: Ansible_Spam_Filter_Profile
    # spam-bwl-table: None
    # spam-filtering: None
    # msn-hotmail: {'log': None}
    # spam-bword-threshold: None
    # mode: delete
    # options: None
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # smtp: {'local-override': None, 'hdrip': None, 'log': None, 'tag-type': None, 'tag-msg': None, 'action': None}
    # yahoo-mail: {'log': None}
    # gmail: {'log': 'enable'}
    # spam-bword-table: None
    # mapi: {'action': None, 'log': None}
    # flow-based: enable
    # spam-mheader-table: None
    # spam-log-fortiguard-response: enable
    # spam-log: None
    # adom: root
    # pop3: {'action': None, 'tag-type': None, 'log': None, 'tag-msg': None}
    # external: enable
    # spam-rbl-table: None
    # imap: {'action': None, 'tag-type': None, 'log': None, 'tag-msg': None}
    # spam-iptrust-table: None
    # name: Ansible_Spam_Filter_Profile
    # replacemsg-group: None
    # spam-bwl-table: None
    # spam-filtering: enable
    # msn-hotmail: {'log': None}
    # spam-bword-threshold: 10
    # mode: set
    # options: ['bannedword', 'spamfsip']
    ##################################################
    ##################################################
    # comment: None
    # smtp: {'local-override': None, 'hdrip': None, 'log': None, 'tag-type': None, 'tag-msg': None, 'action': None}
    # spam-log: None
    # gmail: {'log': None}
    # spam-bword-table: None
    # mapi: {'action': None, 'log': None}
    # flow-based: None
    # spam-mheader-table: None
    # spam-log-fortiguard-response: None
    # yahoo-mail: {'log': None}
    # adom: root
    # pop3: {'action': None, 'tag-msg': None, 'log': None, 'tag-type': None}
    # external: None
    # spam-rbl-table: None
    # imap: {'action': None, 'tag-msg': None, 'log': None, 'tag-type': None}
    # spam-iptrust-table: None
    # replacemsg-group: None
    # name: Ansible_Spam_Filter_Profile
    # spam-bwl-table: None
    # spam-filtering: None
    # msn-hotmail: {'log': None}
    # spam-bword-threshold: None
    # mode: delete
    # options: None
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # smtp: {'local-override': None, 'hdrip': None, 'log': None, 'tag-type': None, 'tag-msg': None, 'action': None}
    # yahoo-mail: {'log': 'enable'}
    # gmail: {'log': 'enable'}
    # spam-bword-table: None
    # mapi: {'action': None, 'log': 'enable'}
    # flow-based: enable
    # spam-mheader-table: None
    # spam-log-fortiguard-response: enable
    # spam-log: enable
    # adom: root
    # pop3: {'action': None, 'log': None, 'tag-type': None, 'tag-msg': None}
    # external: enable
    # spam-rbl-table: None
    # imap: {'action': None, 'log': None, 'tag-type': None, 'tag-msg': None}
    # spam-iptrust-table: None
    # name: Ansible_Spam_Filter_Profile
    # replacemsg-group: None
    # spam-bwl-table: None
    # spam-filtering: enable
    # msn-hotmail: {'log': 'enable'}
    # spam-bword-threshold: 10
    # mode: set
    # options: ['bannedword', 'spamfsip', 'spamfsurl', 'spamrbl', 'spamfsphish', 'spambwl']
    ##################################################
    ##################################################
    # comment: None
    # smtp: {'local-override': None, 'hdrip': None, 'log': None, 'tag-type': None, 'tag-msg': None, 'action': None}
    # spam-log: None
    # gmail: {'log': None}
    # spam-bword-table: None
    # mapi: {'action': None, 'log': None}
    # flow-based: None
    # spam-mheader-table: None
    # spam-log-fortiguard-response: None
    # yahoo-mail: {'log': None}
    # adom: root
    # pop3: {'action': None, 'tag-msg': None, 'tag-type': None, 'log': None}
    # external: None
    # spam-rbl-table: None
    # imap: {'action': None, 'tag-msg': None, 'tag-type': None, 'log': None}
    # spam-iptrust-table: None
    # replacemsg-group: None
    # name: Ansible_Spam_Filter_Profile
    # spam-bwl-table: None
    # spam-filtering: None
    # msn-hotmail: {'log': None}
    # spam-bword-threshold: None
    # mode: delete
    # options: None
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # smtp: {'local-override': None, 'hdrip': None, 'log': None, 'tag-type': None, 'tag-msg': None, 'action': None}
    # yahoo-mail: {'log': None}
    # gmail: {'log': None}
    # spam-bword-table: None
    # mapi: {'action': None, 'log': None}
    # flow-based: enable
    # spam-mheader-table: None
    # spam-log-fortiguard-response: enable
    # spam-log: None
    # adom: root
    # pop3: {'action': None, 'tag-type': None, 'log': None, 'tag-msg': None}
    # external: enable
    # spam-rbl-table: None
    # imap: {'action': None, 'tag-type': None, 'log': None, 'tag-msg': None}
    # spam-iptrust-table: None
    # name: Ansible_Spam_Filter_Profile
    # replacemsg-group: None
    # spam-bwl-table: None
    # spam-filtering: enable
    # msn-hotmail: {'log': None}
    # spam-bword-threshold: 10
    # mode: set
    # options: ['bannedword', 'spamfsip', 'spamfsurl', 'spamrbl', 'spamfsphish', 'spambwl']
    ##################################################
    ##################################################
    # comment: None
    # smtp: {'local-override': None, 'hdrip': None, 'log': None, 'tag-type': None, 'tag-msg': None, 'action': None}
    # spam-log: None
    # gmail: {'log': None}
    # spam-bword-table: None
    # mapi: {'action': None, 'log': None}
    # flow-based: None
    # spam-mheader-table: None
    # spam-log-fortiguard-response: None
    # yahoo-mail: {'log': None}
    # adom: root
    # pop3: {'action': None, 'tag-msg': None, 'log': None, 'tag-type': None}
    # external: None
    # spam-rbl-table: None
    # imap: {'action': None, 'tag-msg': None, 'log': None, 'tag-type': None}
    # spam-iptrust-table: None
    # replacemsg-group: None
    # name: Ansible_Spam_Filter_Profile
    # spam-bwl-table: None
    # spam-filtering: None
    # msn-hotmail: {'log': None}
    # spam-bword-threshold: None
    # mode: delete
    # options: None
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # smtp: {'local-override': None, 'hdrip': None, 'log': None, 'tag-type': None, 'tag-msg': None, 'action': None}
    # yahoo-mail: {'log': 'enable'}
    # gmail: {'log': 'enable'}
    # spam-bword-table: None
    # mapi: {'action': None, 'log': None}
    # flow-based: enable
    # spam-mheader-table: None
    # spam-log-fortiguard-response: enable
    # spam-log: enable
    # adom: root
    # pop3: {'action': None, 'log': None, 'tag-type': None, 'tag-msg': None}
    # external: enable
    # spam-rbl-table: None
    # imap: {'action': None, 'log': None, 'tag-type': None, 'tag-msg': None}
    # spam-iptrust-table: None
    # name: Ansible_Spam_Filter_Profile
    # replacemsg-group: None
    # spam-bwl-table: None
    # spam-filtering: enable
    # msn-hotmail: {'log': 'enable'}
    # spam-bword-threshold: 10
    # mode: set
    # options: ['bannedword', 'spamfsip', 'spamfsurl', 'spamrbl', 'spamfsphish', 'spambwl']
    ##################################################
    ##################################################
    # comment: None
    # smtp: {'local-override': None, 'hdrip': None, 'log': None, 'tag-type': None, 'tag-msg': None, 'action': None}
    # spam-log: None
    # gmail: {'log': None}
    # spam-bword-table: None
    # mapi: {'action': None, 'log': None}
    # flow-based: None
    # spam-mheader-table: None
    # spam-log-fortiguard-response: None
    # yahoo-mail: {'log': None}
    # adom: root
    # pop3: {'action': None, 'tag-msg': None, 'tag-type': None, 'log': None}
    # external: None
    # spam-rbl-table: None
    # imap: {'action': None, 'tag-msg': None, 'tag-type': None, 'log': None}
    # spam-iptrust-table: None
    # replacemsg-group: None
    # name: Ansible_Spam_Filter_Profile
    # spam-bwl-table: None
    # spam-filtering: None
    # msn-hotmail: {'log': None}
    # spam-bword-threshold: None
    # mode: delete
    # options: None
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # smtp: {'local-override': None, 'hdrip': None, 'log': None, 'tag-type': None, 'tag-msg': None, 'action': None}
    # yahoo-mail: {'log': None}
    # gmail: {'log': 'enable'}
    # spam-bword-table: None
    # mapi: {'action': None, 'log': None}
    # flow-based: enable
    # spam-mheader-table: None
    # spam-log-fortiguard-response: enable
    # spam-log: enable
    # adom: root
    # pop3: {'action': None, 'tag-type': None, 'log': None, 'tag-msg': None}
    # external: enable
    # spam-rbl-table: None
    # imap: {'action': None, 'tag-type': None, 'log': None, 'tag-msg': None}
    # spam-iptrust-table: None
    # name: Ansible_Spam_Filter_Profile
    # replacemsg-group: None
    # spam-bwl-table: None
    # spam-filtering: enable
    # msn-hotmail: {'log': None}
    # spam-bword-threshold: 10
    # mode: set
    # options: ['bannedword', 'spamfsip', 'spamfsurl', 'spamrbl', 'spamfsphish', 'spambwl']
    ##################################################
    ##################################################
    # comment: None
    # smtp: {'local-override': None, 'hdrip': None, 'log': None, 'tag-type': None, 'tag-msg': None, 'action': None}
    # spam-log: None
    # gmail: {'log': None}
    # spam-bword-table: None
    # mapi: {'action': None, 'log': None}
    # flow-based: None
    # spam-mheader-table: None
    # spam-log-fortiguard-response: None
    # yahoo-mail: {'log': None}
    # adom: root
    # pop3: {'action': None, 'tag-msg': None, 'log': None, 'tag-type': None}
    # external: None
    # spam-rbl-table: None
    # imap: {'action': None, 'tag-msg': None, 'log': None, 'tag-type': None}
    # spam-iptrust-table: None
    # replacemsg-group: None
    # name: Ansible_Spam_Filter_Profile
    # spam-bwl-table: None
    # spam-filtering: None
    # msn-hotmail: {'log': None}
    # spam-bword-threshold: None
    # mode: delete
    # options: None
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # smtp: {'local-override': None, 'hdrip': None, 'log': None, 'tag-type': None, 'tag-msg': None, 'action': None}
    # yahoo-mail: {'log': None}
    # gmail: {'log': 'enable'}
    # spam-bword-table: None
    # mapi: {'action': None, 'log': None}
    # flow-based: enable
    # spam-mheader-table: None
    # spam-log-fortiguard-response: enable
    # spam-log: enable
    # adom: root
    # pop3: {'action': None, 'log': None, 'tag-type': None, 'tag-msg': None}
    # external: enable
    # spam-rbl-table: None
    # imap: {'action': None, 'log': None, 'tag-type': None, 'tag-msg': None}
    # spam-iptrust-table: None
    # name: Ansible_Spam_Filter_Profile
    # replacemsg-group: None
    # spam-bwl-table: None
    # spam-filtering: enable
    # msn-hotmail: {'log': None}
    # spam-bword-threshold: 10
    # mode: set
    # options: ['bannedword', 'spamfsip', 'spamfsurl', 'spamrbl', 'spamfsphish', 'spambwl']
    ##################################################
    ##################################################
    # comment: None
    # smtp: {'local-override': None, 'hdrip': None, 'log': None, 'tag-type': None, 'tag-msg': None, 'action': None}
    # spam-log: None
    # gmail: {'log': None}
    # spam-bword-table: None
    # mapi: {'action': None, 'log': None}
    # flow-based: None
    # spam-mheader-table: None
    # spam-log-fortiguard-response: None
    # yahoo-mail: {'log': None}
    # adom: root
    # pop3: {'action': None, 'tag-msg': None, 'tag-type': None, 'log': None}
    # external: None
    # spam-rbl-table: None
    # imap: {'action': None, 'tag-msg': None, 'tag-type': None, 'log': None}
    # spam-iptrust-table: None
    # replacemsg-group: None
    # name: Ansible_Spam_Filter_Profile
    # spam-bwl-table: None
    # spam-filtering: None
    # msn-hotmail: {'log': None}
    # spam-bword-threshold: None
    # mode: delete
    # options: None
    ##################################################
    ##################################################
    # comment: Created by Ansible
    # smtp: {'local-override': None, 'hdrip': None, 'log': None, 'tag-type': None, 'tag-msg': None, 'action': None}
    # yahoo-mail: {'log': None}
    # gmail: {'log': 'enable'}
    # spam-bword-table: None
    # mapi: {'action': None, 'log': None}
    # flow-based: enable
    # spam-mheader-table: None
    # spam-log-fortiguard-response: enable
    # spam-log: enable
    # adom: root
    # pop3: {'action': None, 'tag-type': None, 'log': None, 'tag-msg': None}
    # external: enable
    # spam-rbl-table: None
    # imap: {'action': None, 'tag-type': None, 'log': None, 'tag-msg': None}
    # spam-iptrust-table: None
    # name: Ansible_Spam_Filter_Profile
    # replacemsg-group: None
    # spam-bwl-table: None
    # spam-filtering: enable
    # msn-hotmail: {'log': None}
    # spam-bword-threshold: 10
    # mode: set
    # options: ['bannedword', 'spamfsip', 'spamfsurl', 'spamrbl', 'spamfsphish', 'spambwl']
    ##################################################

    # Test using fixture 1 #
    output = fmgr_secprof_spam.fmgr_spamfilter_profile_addsetdelete(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -3
    # Test using fixture 2 #
    output = fmgr_secprof_spam.fmgr_spamfilter_profile_addsetdelete(fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10
    # Test using fixture 3 #
    output = fmgr_secprof_spam.fmgr_spamfilter_profile_addsetdelete(fmg_instance, fixture_data[2]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 4 #
    output = fmgr_secprof_spam.fmgr_spamfilter_profile_addsetdelete(fmg_instance, fixture_data[3]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10
    # Test using fixture 5 #
    output = fmgr_secprof_spam.fmgr_spamfilter_profile_addsetdelete(fmg_instance, fixture_data[4]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 6 #
    output = fmgr_secprof_spam.fmgr_spamfilter_profile_addsetdelete(fmg_instance, fixture_data[5]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 7 #
    output = fmgr_secprof_spam.fmgr_spamfilter_profile_addsetdelete(fmg_instance, fixture_data[6]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -3
    # Test using fixture 8 #
    output = fmgr_secprof_spam.fmgr_spamfilter_profile_addsetdelete(fmg_instance, fixture_data[7]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 9 #
    output = fmgr_secprof_spam.fmgr_spamfilter_profile_addsetdelete(fmg_instance, fixture_data[8]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 10 #
    output = fmgr_secprof_spam.fmgr_spamfilter_profile_addsetdelete(fmg_instance, fixture_data[9]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10
    # Test using fixture 11 #
    output = fmgr_secprof_spam.fmgr_spamfilter_profile_addsetdelete(fmg_instance, fixture_data[10]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -3
    # Test using fixture 12 #
    output = fmgr_secprof_spam.fmgr_spamfilter_profile_addsetdelete(fmg_instance, fixture_data[11]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 13 #
    output = fmgr_secprof_spam.fmgr_spamfilter_profile_addsetdelete(fmg_instance, fixture_data[12]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 14 #
    output = fmgr_secprof_spam.fmgr_spamfilter_profile_addsetdelete(fmg_instance, fixture_data[13]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10
    # Test using fixture 15 #
    output = fmgr_secprof_spam.fmgr_spamfilter_profile_addsetdelete(fmg_instance, fixture_data[14]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -3
    # Test using fixture 16 #
    output = fmgr_secprof_spam.fmgr_spamfilter_profile_addsetdelete(fmg_instance, fixture_data[15]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 17 #
    output = fmgr_secprof_spam.fmgr_spamfilter_profile_addsetdelete(fmg_instance, fixture_data[16]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 18 #
    output = fmgr_secprof_spam.fmgr_spamfilter_profile_addsetdelete(fmg_instance, fixture_data[17]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 19 #
    output = fmgr_secprof_spam.fmgr_spamfilter_profile_addsetdelete(fmg_instance, fixture_data[18]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 20 #
    output = fmgr_secprof_spam.fmgr_spamfilter_profile_addsetdelete(fmg_instance, fixture_data[19]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
