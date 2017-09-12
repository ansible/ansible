# -*- coding: utf-8 -*-

# Copyright 2017 Dag Wieers <dag@wieers.com>

# This file is part of Ansible by Red Hat
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


import sys

from ansible.compat.tests import unittest
from ansible.module_utils.aci import aci_response_json, aci_response_xml

from nose.plugins.skip import SkipTest

try:
    from lxml import etree
    if sys.version_info >= (2, 7):
        from xmljson import cobra
except ImportError:
    raise SkipTest("aci Ansible modules require the lxml and xmljson Python libraries")


class AciRest(unittest.TestCase):

    def test_invalid_aci_login(self):
        self.maxDiff = None

        expected_result = {
            u'error_code': u'401',
            u'error_text': u'Username or password is incorrect - FAILED local authentication',
            u'imdata': [{
                u'error': {
                    u'attributes': {
                        u'code': u'401',
                        u'text': u'Username or password is incorrect - FAILED local authentication',
                    },
                },
            }],
            u'totalCount': '1',
        }

        json_response = '{"totalCount":"1","imdata":[{"error":{"attributes":{"code":"401","text":"Username or password is incorrect - FAILED local authentication"}}}]}'  # NOQA
        json_result = dict()
        aci_response_json(json_result, json_response)
        self.assertEqual(expected_result, json_result)

        # Python 2.7+ is needed for xmljson
        if sys.version_info < (2, 7):
            return

        xml_response = '''<?xml version="1.0" encoding="UTF-8"?><imdata totalCount="1">
        <error code="401" text="Username or password is incorrect - FAILED local authentication"/>
        </imdata>
        '''
        xml_result = dict()
        aci_response_xml(xml_result, xml_response)
        self.assertEqual(json_result, xml_result)

    def test_valid_aci_login(self):
        self.maxDiff = None

        expected_result = {
            u'error_code': 0,
            u'error_text': u'Success',
            u'imdata': [{
                u'aaaLogin': {
                    u'attributes': {
                        u'token': u'ZldYAsoO9d0FfAQM8xaEVWvQPSOYwpnqzhwpIC1r4MaToknJjlIuAt9+TvXqrZ8lWYIGPj6VnZkWiS8nJfaiaX/AyrdD35jsSxiP3zydh+849xym7ALCw/fFNsc7b5ik1HaMuSUtdrN8fmCEUy7Pq/QNpGEqkE8m7HaxAuHpmvXgtdW1bA+KKJu2zY1c/tem',  # NOQA
                        u'siteFingerprint': u'NdxD72K/uXaUK0wn',
                        u'refreshTimeoutSeconds': u'600',
                        u'maximumLifetimeSeconds': u'86400',
                        u'guiIdleTimeoutSeconds': u'1200',
                        u'restTimeoutSeconds': u'90',
                        u'creationTime': u'1500134817',
                        u'firstLoginTime': u'1500134817',
                        u'userName': u'admin',
                        u'remoteUser': u'false',
                        u'unixUserId': u'15374',
                        u'sessionId': u'o7hObsqNTfCmDGcZI5c4ng==',
                        u'lastName': u'',
                        u'firstName': u'',
                        u'version': u'2.0(2f)',
                        u'buildTime': u'Sat Aug 20 23:07:07 PDT 2016',
                        u'node': u'topology/pod-1/node-1',
                    },
                    u'children': [{
                        u'aaaUserDomain': {
                            u'attributes': {
                                u'name': u'all',
                                u'rolesR': u'admin',
                                u'rolesW': u'admin',
                            },
                            u'children': [{
                                u'aaaReadRoles': {
                                    u'attributes': {},
                                },
                            }, {
                                u'aaaWriteRoles': {
                                    u'attributes': {},
                                    u'children': [{
                                        u'role': {
                                            u'attributes': {
                                                u'name': u'admin',
                                            },
                                        },
                                    }],
                                },
                            }],
                        },
                    }, {
                        u'DnDomainMapEntry': {
                            u'attributes': {
                                u'dn': u'uni/tn-common',
                                u'readPrivileges': u'admin',
                                u'writePrivileges': u'admin',
                            },
                        },
                    }, {
                        u'DnDomainMapEntry': {
                            u'attributes': {
                                u'dn': u'uni/tn-infra',
                                u'readPrivileges': u'admin',
                                u'writePrivileges': u'admin',
                            },
                        },
                    }, {
                        u'DnDomainMapEntry': {
                            u'attributes': {
                                u'dn': u'uni/tn-mgmt',
                                u'readPrivileges': u'admin',
                                u'writePrivileges': u'admin',
                            },
                        },
                    }],
                },
            }],
            u'totalCount': u'1',
        }

        json_response = '{"totalCount":"1","imdata":[{"aaaLogin":{"attributes":{"token":"ZldYAsoO9d0FfAQM8xaEVWvQPSOYwpnqzhwpIC1r4MaToknJjlIuAt9+TvXqrZ8lWYIGPj6VnZkWiS8nJfaiaX/AyrdD35jsSxiP3zydh+849xym7ALCw/fFNsc7b5ik1HaMuSUtdrN8fmCEUy7Pq/QNpGEqkE8m7HaxAuHpmvXgtdW1bA+KKJu2zY1c/tem","siteFingerprint":"NdxD72K/uXaUK0wn","refreshTimeoutSeconds":"600","maximumLifetimeSeconds":"86400","guiIdleTimeoutSeconds":"1200","restTimeoutSeconds":"90","creationTime":"1500134817","firstLoginTime":"1500134817","userName":"admin","remoteUser":"false","unixUserId":"15374","sessionId":"o7hObsqNTfCmDGcZI5c4ng==","lastName":"","firstName":"","version":"2.0(2f)","buildTime":"Sat Aug 20 23:07:07 PDT 2016","node":"topology/pod-1/node-1"},"children":[{"aaaUserDomain":{"attributes":{"name":"all","rolesR":"admin","rolesW":"admin"},"children":[{"aaaReadRoles":{"attributes":{}}},{"aaaWriteRoles":{"attributes":{},"children":[{"role":{"attributes":{"name":"admin"}}}]}}]}},{"DnDomainMapEntry":{"attributes":{"dn":"uni/tn-common","readPrivileges":"admin","writePrivileges":"admin"}}},{"DnDomainMapEntry":{"attributes":{"dn":"uni/tn-infra","readPrivileges":"admin","writePrivileges":"admin"}}},{"DnDomainMapEntry":{"attributes":{"dn":"uni/tn-mgmt","readPrivileges":"admin","writePrivileges":"admin"}}}]}}]}'  # NOQA
        json_result = dict()
        aci_response_json(json_result, json_response)
        self.assertEqual(expected_result, json_result)

        # Python 2.7+ is needed for xmljson
        if sys.version_info < (2, 7):
            return

        xml_response = '<?xml version="1.0" encoding="UTF-8"?><imdata totalCount="1">\n<aaaLogin token="ZldYAsoO9d0FfAQM8xaEVWvQPSOYwpnqzhwpIC1r4MaToknJjlIuAt9+TvXqrZ8lWYIGPj6VnZkWiS8nJfaiaX/AyrdD35jsSxiP3zydh+849xym7ALCw/fFNsc7b5ik1HaMuSUtdrN8fmCEUy7Pq/QNpGEqkE8m7HaxAuHpmvXgtdW1bA+KKJu2zY1c/tem" siteFingerprint="NdxD72K/uXaUK0wn" refreshTimeoutSeconds="600" maximumLifetimeSeconds="86400" guiIdleTimeoutSeconds="1200" restTimeoutSeconds="90" creationTime="1500134817" firstLoginTime="1500134817" userName="admin" remoteUser="false" unixUserId="15374" sessionId="o7hObsqNTfCmDGcZI5c4ng==" lastName="" firstName="" version="2.0(2f)" buildTime="Sat Aug 20 23:07:07 PDT 2016" node="topology/pod-1/node-1">\n<aaaUserDomain name="all" rolesR="admin" rolesW="admin">\n<aaaReadRoles/>\n<aaaWriteRoles>\n<role name="admin"/>\n</aaaWriteRoles>\n</aaaUserDomain>\n<DnDomainMapEntry dn="uni/tn-common" readPrivileges="admin" writePrivileges="admin"/>\n<DnDomainMapEntry dn="uni/tn-infra" readPrivileges="admin" writePrivileges="admin"/>\n<DnDomainMapEntry dn="uni/tn-mgmt" readPrivileges="admin" writePrivileges="admin"/>\n</aaaLogin></imdata>\n'''  # NOQA
        xml_result = dict()
        aci_response_xml(xml_result, xml_response)
        self.assertEqual(json_result, xml_result)

    def test_invalid_input(self):
        self.maxDiff = None

        expected_result = {
            u'error_code': u'401',
            u'error_text': u'Username or password is incorrect - FAILED local authentication',
            u'imdata': [{
                u'error': {
                    u'attributes': {
                        u'code': u'401',
                        u'text': u'Username or password is incorrect - FAILED local authentication',
                    },
                },
            }],
            u'totalCount': '1',
        }

        json_response = '{"totalCount":"1","imdata":[{"error":{"attributes":{"code":"401","text":"Username or password is incorrect - FAILED local authentication"}}}]}'  # NOQA
        json_result = dict()
        aci_response_json(json_result, json_response)
        self.assertEqual(expected_result, json_result)

        # Python 2.7+ is needed for xmljson
        if sys.version_info < (2, 7):
            return

        xml_response = '''<?xml version="1.0" encoding="UTF-8"?><imdata totalCount="1">
        <error code="401" text="Username or password is incorrect - FAILED local authentication"/>
        </imdata>
        '''
        xml_result = dict()
        aci_response_xml(xml_result, xml_response)
        self.assertEqual(json_result, xml_result)

    def test_empty_response(self):
        self.maxDiffi = None

        if sys.version_info < (3, 0):
            expected_json_result = {
                'error_code': -1,
                'error_text': "Unable to parse output as JSON, see 'raw' output. No JSON object could be decoded",
                'raw': '',
            }

        else:
            expected_json_result = {
                u'error_code': -1,
                u'error_text': u"Unable to parse output as JSON, see 'raw' output. Expecting value: line 1 column 1 (char 0)",
                u'raw': u'',
            }

        json_response = ''
        json_result = dict()
        aci_response_json(json_result, json_response)
        self.assertEqual(expected_json_result, json_result)

        # Python 2.7+ is needed for xmljson
        if sys.version_info < (2, 7):
            return

        elif etree.LXML_VERSION < (3, 3, 0, 0):
            expected_xml_result = {
                'error_code': -1,
                'error_text': "Unable to parse output as XML, see 'raw' output. None",
                'raw': '',
            }

        elif sys.version_info < (3, 0):
            expected_xml_result = {
                'error_code': -1,
                'error_text': "Unable to parse output as XML, see 'raw' output. None (line 0)",
                'raw': '',
            }

        else:
            expected_xml_result = {
                u'error_code': -1,
                u'error_text': u"Unable to parse output as XML, see 'raw' output. None (line 0)",
                u'raw': u'',
            }

        xml_response = ''
        xml_result = dict()
        aci_response_xml(xml_result, xml_response)
        self.assertEqual(expected_xml_result, xml_result)

    def test_invalid_response(self):
        self.maxDiff = None

        if sys.version_info < (2, 7):
            expected_json_result = {
                'error_code': -1,
                'error_text': "Unable to parse output as JSON, see 'raw' output. Expecting object: line 1 column 8 (char 8)",
                'raw': '{ "aaa":',
            }

        elif sys.version_info < (3, 0):
            expected_json_result = {
                'error_code': -1,
                'error_text': "Unable to parse output as JSON, see 'raw' output. No JSON object could be decoded",
                'raw': '{ "aaa":',
            }

        else:
            expected_json_result = {
                u'error_code': -1,
                u'error_text': u"Unable to parse output as JSON, see 'raw' output. Expecting value: line 1 column 9 (char 8)",
                u'raw': u'{ "aaa":',
            }

        json_response = '{ "aaa":'
        json_result = dict()
        aci_response_json(json_result, json_response)
        self.assertEqual(expected_json_result, json_result)

        # Python 2.7+ is needed for xmljson
        if sys.version_info < (2, 7):
            return

        elif etree.LXML_VERSION < (3, 3, 0, 0):
            expected_xml_result = {
                'error_code': -1,
                'error_text': "Unable to parse output as XML, see 'raw' output. Couldn't find end of Start Tag aaa line 1, line 1, column 5",  # NOQA
                'raw': '<aaa ',
            }

        elif sys.version_info < (3, 0):
            expected_xml_result = {
                'error_code': -1,
                'error_text': u"Unable to parse output as XML, see 'raw' output. Couldn't find end of Start Tag aaa line 1, line 1, column 6 (line 1)",  # NOQA
                'raw': u'<aaa ',
            }

        else:
            expected_xml_result = {
                u'error_code': -1,
                u'error_text': u"Unable to parse output as XML, see 'raw' output. Couldn't find end of Start Tag aaa line 1, line 1, column 6 (<string>, line 1)",  # NOQA
                u'raw': u'<aaa ',
            }

        xml_response = '<aaa '
        xml_result = dict()
        aci_response_xml(xml_result, xml_response)
        self.assertEqual(expected_xml_result, xml_result)
