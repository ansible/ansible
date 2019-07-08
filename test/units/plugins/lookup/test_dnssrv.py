# (c)2016 Andrew Zenk <azenk@umn.edu>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat import unittest

from dns import rdatatype, rdataclass, rdata
from dns.rdatatype import SRV
from dns.rdataclass import IN

from ansible.plugins.lookup.dnssrv import LookupModule


MOCK_RECORDS = [
    rdata.from_text(IN, SRV, '10 10 8443 demo-0.example.com.'),
    rdata.from_text(IN, SRV, '20 10 8443 demo-1.example.com.'),
    rdata.from_text(IN, SRV, '10 20 8443 demo-2.example.com.'),
    rdata.from_text(IN, SRV, '10 30 8443 demo-3.example.com.'),
    rdata.from_text(IN, SRV, '20 40 8443 demo-4.example.com.')
]
MOCK_ANSWER = [
    [{'priority': 10, 'weight': 3/6.*100, 'target': 'demo-3.example.com:8443'},
     {'priority': 10, 'weight': 2/6.*100, 'target': 'demo-2.example.com:8443'},
     {'priority': 10, 'weight': 1/6.*100, 'target': 'demo-0.example.com:8443'}],
    [{'priority': 20, 'weight': 4/5.*100, 'target': 'demo-4.example.com:8443'},
     {'priority': 20, 'weight': 1/5.*100, 'target': 'demo-1.example.com:8443'}]
]


class MockLookupModule(LookupModule):

    @staticmethod
    def _do_dns_query(domain):
        if domain == '_test._tcp.example.com':
            return MOCK_RECORDS
        if domain == '_inop._tcp.example.com':
            return []


class TestDnsSrvPlugin(unittest.TestCase):

    def setUp(self):
        self._dnssrv = MockLookupModule()

    def tearDown(self):
        pass

    def test_dnssrv_good_lkp(self):
        result = self._dnssrv.run(terms=['_test._tcp.example.com'])
        self.assertEqual(result, MOCK_ANSWER)

    def test_dnssrv_bad_lkp(self):
        result = self._dnssrv.run(terms=['_inop._tcp.example.com'])
        self.assertFalse(result)
