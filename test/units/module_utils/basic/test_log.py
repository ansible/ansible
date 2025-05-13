# -*- coding: utf-8 -*-
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import syslog
from itertools import product

import pytest


class TestAnsibleModuleLogSmokeTest:
    DATA = [u'Text string', u'Toshio くらとみ non-ascii test']
    DATA = DATA + [d.encode('utf-8') for d in DATA]
    DATA += [b'non-utf8 :\xff: test']

    @pytest.mark.parametrize('msg, stdin', ((m, {}) for m in DATA), indirect=['stdin'])
    def test_smoketest_syslog(self, am, mocker, msg):
        # These talk to the live daemons on the system.  Need to do this to
        # show that what we send doesn't cause an issue once it gets to the
        # daemon.  These are just smoketests to test that we don't fail.
        mocker.patch('ansible.module_utils.basic.has_journal', False)

        am.log(u'Text string')
        am.log(u'Toshio くらとみ non-ascii test')

        am.log(b'Byte string')
        am.log(u'Toshio くらとみ non-ascii test'.encode('utf-8'))
        am.log(b'non-utf8 :\xff: test')


class TestAnsibleModuleLogSyslog:
    """Test the AnsibleModule Log Method"""

    OUTPUT_DATA = [
        (u'Text string', u'Text string'),
        (u'Toshio くらとみ non-ascii test', u'Toshio くらとみ non-ascii test'),
        (b'Byte string', u'Byte string'),
        (u'Toshio くらとみ non-ascii test'.encode('utf-8'), u'Toshio くらとみ non-ascii test'),
        (b'non-utf8 :\xff: test', b'non-utf8 :\xff: test'.decode('utf-8', 'replace')),
    ]

    @pytest.mark.parametrize('no_log, stdin', (product((True, False), [{}])), indirect=['stdin'])
    def test_no_log(self, am, mocker, no_log):
        """Test that when no_log is set, logging does not occur"""
        mock_syslog = mocker.patch('syslog.syslog', autospec=True)
        mocker.patch('ansible.module_utils.basic.has_journal', False)
        am.no_log = no_log
        am.log('unittest no_log')
        if no_log:
            assert not mock_syslog.called
        else:
            mock_syslog.assert_called_once_with(syslog.LOG_INFO, 'unittest no_log')

    @pytest.mark.parametrize('msg, param, stdin',
                             ((m, p, {}) for m, p in OUTPUT_DATA),
                             indirect=['stdin'])
    def test_output_matches(self, am, mocker, msg, param):
        """Check that log messages are sent correctly"""
        mocker.patch('ansible.module_utils.basic.has_journal', False)
        mock_syslog = mocker.patch('syslog.syslog', autospec=True)

        am.log(msg)
        mock_syslog.assert_called_once_with(syslog.LOG_INFO, param)
