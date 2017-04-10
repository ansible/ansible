# -*- coding: utf-8 -*-

import unittest

from ansible.parsing.utils.addresses import parse_address

class TestParseAddress(unittest.TestCase):

    tests = {
        # IPv4 addresses
        '192.0.2.3': ['192.0.2.3', None],
        '192.0.2.3:23': ['192.0.2.3', 23],

        # IPv6 addresses
        '::': ['::', None],
        '::1': ['::1', None],
        '[::1]:442': ['::1', 442],
        'abcd:ef98:7654:3210:abcd:ef98:7654:3210': ['abcd:ef98:7654:3210:abcd:ef98:7654:3210', None],
        '[abcd:ef98:7654:3210:abcd:ef98:7654:3210]:42': ['abcd:ef98:7654:3210:abcd:ef98:7654:3210', 42],
        '1234:5678:9abc:def0:1234:5678:9abc:def0': ['1234:5678:9abc:def0:1234:5678:9abc:def0', None],
        '1234::9abc:def0:1234:5678:9abc:def0': ['1234::9abc:def0:1234:5678:9abc:def0', None],
        '1234:5678::def0:1234:5678:9abc:def0': ['1234:5678::def0:1234:5678:9abc:def0', None],
        '1234:5678:9abc::1234:5678:9abc:def0': ['1234:5678:9abc::1234:5678:9abc:def0', None],
        '1234:5678:9abc:def0::5678:9abc:def0': ['1234:5678:9abc:def0::5678:9abc:def0', None],
        '1234:5678:9abc:def0:1234::9abc:def0': ['1234:5678:9abc:def0:1234::9abc:def0', None],
        '1234:5678:9abc:def0:1234:5678::def0': ['1234:5678:9abc:def0:1234:5678::def0', None],
        '1234:5678:9abc:def0:1234:5678::': ['1234:5678:9abc:def0:1234:5678::', None],
        '::9abc:def0:1234:5678:9abc:def0': ['::9abc:def0:1234:5678:9abc:def0', None],
        '0:0:0:0:0:ffff:1.2.3.4': ['0:0:0:0:0:ffff:1.2.3.4', None],
        '0:0:0:0:0:0:1.2.3.4': ['0:0:0:0:0:0:1.2.3.4', None],
        '::ffff:1.2.3.4': ['::ffff:1.2.3.4', None],
        '::1.2.3.4': ['::1.2.3.4', None],
        '1234::': ['1234::', None],

        # Hostnames
        'some-host': ['some-host', None],
        'some-host:80': ['some-host', 80],
        'some.host.com:492': ['some.host.com', 492],
        '[some.host.com]:493': ['some.host.com', 493],
        'a-b.3foo_bar.com:23': ['a-b.3foo_bar.com', 23],
        u'fóöbär': [u'fóöbär', None],
        u'fóöbär:32': [u'fóöbär', 32],
        u'fóöbär.éxàmplê.com:632': [u'fóöbär.éxàmplê.com', 632],

        # Various errors
        '': [None, None],
        'some..host': [None, None],
        'some.': [None, None],
        '[example.com]': [None, None],
        'some-': [None, None],
        'some-.foo.com': [None, None],
        'some.-foo.com': [None, None],
    }

    range_tests = {
        '192.0.2.[3:10]': ['192.0.2.[3:10]', None],
        '192.0.2.[3:10]:23': ['192.0.2.[3:10]', 23],
        'abcd:ef98::7654:[1:9]': ['abcd:ef98::7654:[1:9]', None],
        '[abcd:ef98::7654:[6:32]]:2222': ['abcd:ef98::7654:[6:32]', 2222],
        '[abcd:ef98::7654:[9ab3:fcb7]]:2222': ['abcd:ef98::7654:[9ab3:fcb7]', 2222],
        u'fóöb[a:c]r.éxàmplê.com:632': [u'fóöb[a:c]r.éxàmplê.com', 632],
        '[a:b]foo.com': ['[a:b]foo.com', None],
        'foo[a:b].com': ['foo[a:b].com', None],
        'foo[a:b]:42': ['foo[a:b]', 42],
        'foo[a-b]-.com': [None, None],
        'foo[a-b]:32': [None, None],
        'foo[x-y]': [None, None],
    }

    def test_without_ranges(self):
        for t in self.tests:
            test = self.tests[t]

            try:
                (host, port) = parse_address(t)
            except:
                host = None
                port = None

            assert host == test[0]
            assert port == test[1]

    def test_with_ranges(self):
        for t in self.range_tests:
            test = self.range_tests[t]

            try:
                (host, port) = parse_address(t, allow_ranges=True)
            except:
                host = None
                port = None

            assert host == test[0]
            assert port == test[1]
