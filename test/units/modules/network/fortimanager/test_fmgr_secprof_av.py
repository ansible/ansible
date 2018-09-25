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
    from ansible.modules.network.fortimanager import fmgr_secprof_av
except ImportError:
    pytest.skip("Could not load required modules for testing", allow_module_level=True)

fmg_instance = FortiManager("1.1.1.1", "admin", "")


def load_fixtures():
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures') + \
                   "/{filename}.json".format(filename=os.path.splitext(os.path.basename(__file__))[0])
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


def test_fmgr_antivirus_profile_addSetDelete(fixture_data, mocker):
    mocker.patch("pyFMG.fortimgr.FortiManager._post_request", side_effect=fixture_data)
    #  Fixture sets used:###########################

    ##################################################
    # comment: None
    # av-block-log: None
    # extended-log: None
    # analytics-db: None
    # analytics-wl-filetype: None
    # av-virus-log: None
    # content-disarm: {'pdf-act-movie': None, 'pdf-act-gotor': None, 'pdf-act-java': None,
    # 'original-file-destination': None, 'office-hylink': None, 'pdf-act-sound': None, 'detect-only': None,
    # 'office-embed': None, 'office-linked': None, 'pdf-javacode': None, 'pdf-hyperlink': None, 'pdf-embedfile': None,
    #  'office-macro': None, 'pdf-act-form': None, 'pdf-act-launch': None, 'cover-page': None}
    # ftp: {'outbreak-prevention': None, 'options': None, 'archive-log': None, 'emulator': None, 'archive-block': None}
    # mapi: {'executables': None, 'archive-log': None, 'outbreak-prevention': None, 'emulator': None,
    #  'archive-block': None, 'options': None}
    # analytics-max-upload: None
    # nntp: {'outbreak-prevention': None, 'options': None, 'archive-log': None, 'emulator': None, 'archive-block': None}
    # smb: {'outbreak-prevention': None, 'options': None, 'archive-log': None, 'emulator': None, 'archive-block': None}
    # analytics-bl-filetype: None
    # http: {'archive-log': None, 'outbreak-prevention': None, 'emulator': None, 'archive-block': None,
    #  'content-disarm': None, 'options': None}
    # adom: root
    # smtp: {'executables': None, 'archive-log': None, 'outbreak-prevention': None, 'emulator': None,
    #  'archive-block': None, 'content-disarm': None, 'options': None}
    # pop3: {'executables': None, 'archive-log': None, 'outbreak-prevention': None, 'emulator': None,
    #  'archive-block': None, 'content-disarm': None, 'options': None}
    # inspection-mode: None
    # ftgd-analytics: None
    # imap: {'executables': None, 'archive-log': None, 'outbreak-prevention': None, 'emulator': None,
    #  'archive-block': None, 'content-disarm': None, 'options': None}
    # name: Ansible_AV_Profile
    # replacemsg-group: None
    # scan-mode: None
    # nac-quar: {'infected': None, 'log': None, 'expiry': None}
    # mode: delete
    # mobile-malware-db: None
    ##################################################
    ##################################################
    # comment: Created by Ansible Module TEST
    # name: Ansible_AV_Profile
    # scan-mode: full
    # av-block-log: enable
    # inspection-mode: proxy
    # av-virus-log: enable
    # ftgd-analytics: everything
    # mobile-malware-db: enable
    # mode: set
    # adom: root
    ##################################################
    ##################################################
    # comment: None
    # av-block-log: None
    # extended-log: None
    # analytics-db: None
    # analytics-wl-filetype: None
    # av-virus-log: None
    # content-disarm: {'pdf-act-movie': None, 'pdf-act-gotor': None, 'office-macro': None, 'pdf-act-java': None,
    #  'original-file-destination': None, 'office-hylink': None, 'pdf-act-sound': None, 'detect-only': None,
    #  'office-embed': None, 'office-linked': None, 'pdf-javacode': None, 'pdf-hyperlink': None, 'cover-page': None,
    #  'pdf-embedfile': None, 'pdf-act-form': None, 'pdf-act-launch': None}
    # ftp: {'outbreak-prevention': None, 'options': None, 'archive-log': None, 'emulator': None, 'archive-block': None}
    # mapi: {'executables': None, 'archive-log': None, 'outbreak-prevention': None, 'emulator': None,
    #  'archive-block': None, 'options': None}
    # analytics-max-upload: None
    # nntp: {'outbreak-prevention': None, 'options': None, 'archive-log': None, 'emulator': None, 'archive-block': None}
    # smb: {'outbreak-prevention': None, 'options': None, 'archive-log': None, 'emulator': None, 'archive-block': None}
    # analytics-bl-filetype: None
    # http: {'archive-log': None, 'outbreak-prevention': None, 'emulator': None, 'archive-block': None,
    #  'content-disarm': None, 'options': None}
    # adom: root
    # smtp: {'executables': None, 'archive-log': None, 'outbreak-prevention': None, 'emulator': None,
    #  'archive-block': None, 'content-disarm': None, 'options': None}
    # pop3: {'executables': None, 'archive-log': None, 'outbreak-prevention': None, 'emulator': None,
    #  'archive-block': None, 'content-disarm': None, 'options': None}
    # inspection-mode: None
    # ftgd-analytics: None
    # imap: {'executables': None, 'archive-log': None, 'outbreak-prevention': None, 'emulator': None,
    #  'archive-block': None, 'content-disarm': None, 'options': None}
    # name: Ansible_AV_Profile
    # replacemsg-group: None
    # scan-mode: None
    # nac-quar: {'infected': None, 'log': None, 'expiry': None}
    # mode: delete
    # mobile-malware-db: None
    ##################################################
    ##################################################
    # comment: Created by Ansible Module TEST
    # name: Ansible_AV_Profile
    # scan-mode: full
    # av-block-log: enable
    # inspection-mode: proxy
    # av-virus-log: enable
    # ftgd-analytics: everything
    # mobile-malware-db: enable
    # mode: set
    # adom: root
    ##################################################
    ##################################################
    # comment: None
    # av-block-log: None
    # extended-log: None
    # analytics-db: None
    # analytics-wl-filetype: None
    # av-virus-log: None
    # content-disarm: {'pdf-act-movie': None, 'pdf-act-gotor': None, 'pdf-act-java': None,
    #  'original-file-destination': None, 'cover-page': None, 'pdf-act-sound': None, 'detect-only': None,
    #  'office-embed': None, 'pdf-embedfile': None, 'office-linked': None, 'pdf-javacode': None, 'pdf-hyperlink': None,
    #  'office-hylink': None, 'office-macro': None, 'pdf-act-form': None, 'pdf-act-launch': None}
    # ftp: {'outbreak-prevention': None, 'options': None, 'archive-log': None, 'emulator': None, 'archive-block': None}
    # smtp: {'executables': None, 'archive-log': None, 'outbreak-prevention': None, 'emulator': None,
    #  'archive-block': None, 'content-disarm': None, 'options': None}
    # mapi: {'executables': None, 'archive-log': None, 'outbreak-prevention': None, 'emulator': None,
    #  'archive-block': None, 'options': None}
    # analytics-max-upload: None
    # nntp: {'outbreak-prevention': None, 'options': None, 'archive-log': None, 'emulator': None, 'archive-block': None}
    # smb: {'outbreak-prevention': None, 'options': None, 'archive-log': None, 'emulator': None, 'archive-block': None}
    # analytics-bl-filetype: None
    # http: {'archive-log': None, 'outbreak-prevention': None, 'emulator': None, 'archive-block': None,
    #  'content-disarm': None, 'options': None}
    # adom: root
    # scan-mode: None
    # pop3: {'executables': None, 'archive-log': None, 'outbreak-prevention': None, 'emulator': None,
    #  'archive-block': None, 'content-disarm': None, 'options': None}
    # inspection-mode: None
    # ftgd-analytics: None
    # imap: {'executables': None, 'archive-log': None, 'outbreak-prevention': None, 'emulator': None,
    #  'archive-block': None, 'content-disarm': None, 'options': None}
    # name: Ansible_AV_Profile
    # replacemsg-group: None
    # nac-quar: {'infected': None, 'log': None, 'expiry': None}
    # mode: delete
    # mobile-malware-db: None
    ##################################################

    # Test using fixture 1 #
    output = fmgr_secprof_av.fmgr_antivirus_profile_addSetDelete(fmg_instance, fixture_data[0]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -3
    # Test using fixture 2 #
    output = fmgr_secprof_av.fmgr_antivirus_profile_addSetDelete(fmg_instance, fixture_data[1]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 3 #
    output = fmgr_secprof_av.fmgr_antivirus_profile_addSetDelete(fmg_instance, fixture_data[2]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 4 #
    output = fmgr_secprof_av.fmgr_antivirus_profile_addSetDelete(fmg_instance, fixture_data[3]['paramgram_used'])
    assert output['raw_response']['status']['code'] == 0
    # Test using fixture 5 #
    output = fmgr_secprof_av.fmgr_antivirus_profile_addSetDelete(fmg_instance, fixture_data[4]['paramgram_used'])
    assert output['raw_response']['status']['code'] == -10015
