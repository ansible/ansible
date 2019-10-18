# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys

from units.compat import unittest
from ansible.module_utils.network.aci.aci import ACIModule
from ansible.module_utils.six import PY2
from ansible.module_utils._text import to_native

import pytest


class AltModule():
    params = dict(
        hostname='dummy',
        port=123,
        protocol='https',
        state='present',
    )


class AltACIModule(ACIModule):
    def __init__(self):
        self.result = dict(changed=False)
        self.module = AltModule
        self.params = self.module.params


aci = AltACIModule()


try:
    from lxml import etree
    if sys.version_info >= (2, 7):
        from xmljson import cobra
except ImportError:
    pytestmark = pytest.mark.skip("ACI Ansible modules require the lxml and xmljson Python libraries")


class AciRest(unittest.TestCase):

    def test_invalid_aci_login(self):
        self.maxDiff = None

        error = dict(
            code='401',
            text='Username or password is incorrect - FAILED local authentication',
        )

        imdata = [{
            'error': {
                'attributes': {
                    'code': '401',
                    'text': 'Username or password is incorrect - FAILED local authentication',
                },
            },
        }]

        totalCount = 1

        json_response = '{"totalCount":"1","imdata":[{"error":{"attributes":{"code":"401","text":"Username or password is incorrect - FAILED local authentication"}}}]}'  # NOQA
        json_result = dict()
        aci.response_json(json_response)
        self.assertEqual(aci.error, error)
        self.assertEqual(aci.imdata, imdata)
        self.assertEqual(aci.totalCount, totalCount)

        # Python 2.7+ is needed for xmljson
        if sys.version_info < (2, 7):
            return

        xml_response = '''<?xml version="1.0" encoding="UTF-8"?><imdata totalCount="1">
        <error code="401" text="Username or password is incorrect - FAILED local authentication"/>
        </imdata>
        '''
        xml_result = dict()
        aci.response_xml(xml_response)
        self.assertEqual(aci.error, error)
        self.assertEqual(aci.imdata, imdata)
        self.assertEqual(aci.totalCount, totalCount)

    def test_valid_aci_login(self):
        self.maxDiff = None

        imdata = [{
            'aaaLogin': {
                'attributes': {
                    'token': 'ZldYAsoO9d0FfAQM8xaEVWvQPSOYwpnqzhwpIC1r4MaToknJjlIuAt9+TvXqrZ8lWYIGPj6VnZkWiS8nJfaiaX/AyrdD35jsSxiP3zydh+849xym7ALCw/fFNsc7b5ik1HaMuSUtdrN8fmCEUy7Pq/QNpGEqkE8m7HaxAuHpmvXgtdW1bA+KKJu2zY1c/tem',  # NOQA
                    'siteFingerprint': 'NdxD72K/uXaUK0wn',
                    'refreshTimeoutSeconds': '600',
                    'maximumLifetimeSeconds': '86400',
                    'guiIdleTimeoutSeconds': '1200',
                    'restTimeoutSeconds': '90',
                    'creationTime': '1500134817',
                    'firstLoginTime': '1500134817',
                    'userName': 'admin',
                    'remoteUser': 'false',
                    'unixUserId': '15374',
                    'sessionId': 'o7hObsqNTfCmDGcZI5c4ng==',
                    'lastName': '',
                    'firstName': '',
                    'version': '2.0(2f)',
                    'buildTime': 'Sat Aug 20 23:07:07 PDT 2016',
                    'node': 'topology/pod-1/node-1',
                },
                'children': [{
                    'aaaUserDomain': {
                        'attributes': {
                            'name': 'all',
                            'rolesR': 'admin',
                            'rolesW': 'admin',
                        },
                        'children': [{
                            'aaaReadRoles': {
                                'attributes': {},
                            },
                        }, {
                            'aaaWriteRoles': {
                                'attributes': {},
                                'children': [{
                                    'role': {
                                        'attributes': {
                                            'name': 'admin',
                                        },
                                    },
                                }],
                            },
                        }],
                    },
                }, {
                    'DnDomainMapEntry': {
                        'attributes': {
                            'dn': 'uni/tn-common',
                            'readPrivileges': 'admin',
                            'writePrivileges': 'admin',
                        },
                    },
                }, {
                    'DnDomainMapEntry': {
                        'attributes': {
                            'dn': 'uni/tn-infra',
                            'readPrivileges': 'admin',
                             'writePrivileges': 'admin',
                        },
                    },
                }, {
                    'DnDomainMapEntry': {
                        'attributes': {
                            'dn': 'uni/tn-mgmt',
                            'readPrivileges': 'admin',
                            'writePrivileges': 'admin',
                        },
                    },
                }],
            },
        }]

        totalCount = 1

        json_response = '{"totalCount":"1","imdata":[{"aaaLogin":{"attributes":{"token":"ZldYAsoO9d0FfAQM8xaEVWvQPSOYwpnqzhwpIC1r4MaToknJjlIuAt9+TvXqrZ8lWYIGPj6VnZkWiS8nJfaiaX/AyrdD35jsSxiP3zydh+849xym7ALCw/fFNsc7b5ik1HaMuSUtdrN8fmCEUy7Pq/QNpGEqkE8m7HaxAuHpmvXgtdW1bA+KKJu2zY1c/tem","siteFingerprint":"NdxD72K/uXaUK0wn","refreshTimeoutSeconds":"600","maximumLifetimeSeconds":"86400","guiIdleTimeoutSeconds":"1200","restTimeoutSeconds":"90","creationTime":"1500134817","firstLoginTime":"1500134817","userName":"admin","remoteUser":"false","unixUserId":"15374","sessionId":"o7hObsqNTfCmDGcZI5c4ng==","lastName":"","firstName":"","version":"2.0(2f)","buildTime":"Sat Aug 20 23:07:07 PDT 2016","node":"topology/pod-1/node-1"},"children":[{"aaaUserDomain":{"attributes":{"name":"all","rolesR":"admin","rolesW":"admin"},"children":[{"aaaReadRoles":{"attributes":{}}},{"aaaWriteRoles":{"attributes":{},"children":[{"role":{"attributes":{"name":"admin"}}}]}}]}},{"DnDomainMapEntry":{"attributes":{"dn":"uni/tn-common","readPrivileges":"admin","writePrivileges":"admin"}}},{"DnDomainMapEntry":{"attributes":{"dn":"uni/tn-infra","readPrivileges":"admin","writePrivileges":"admin"}}},{"DnDomainMapEntry":{"attributes":{"dn":"uni/tn-mgmt","readPrivileges":"admin","writePrivileges":"admin"}}}]}}]}'  # NOQA
        json_result = dict()
        aci.response_json(json_response)
        self.assertEqual(aci.imdata, imdata)
        self.assertEqual(aci.totalCount, totalCount)

        # Python 2.7+ is needed for xmljson
        if sys.version_info < (2, 7):
            return

        xml_response = '<?xml version="1.0" encoding="UTF-8"?><imdata totalCount="1">\n<aaaLogin token="ZldYAsoO9d0FfAQM8xaEVWvQPSOYwpnqzhwpIC1r4MaToknJjlIuAt9+TvXqrZ8lWYIGPj6VnZkWiS8nJfaiaX/AyrdD35jsSxiP3zydh+849xym7ALCw/fFNsc7b5ik1HaMuSUtdrN8fmCEUy7Pq/QNpGEqkE8m7HaxAuHpmvXgtdW1bA+KKJu2zY1c/tem" siteFingerprint="NdxD72K/uXaUK0wn" refreshTimeoutSeconds="600" maximumLifetimeSeconds="86400" guiIdleTimeoutSeconds="1200" restTimeoutSeconds="90" creationTime="1500134817" firstLoginTime="1500134817" userName="admin" remoteUser="false" unixUserId="15374" sessionId="o7hObsqNTfCmDGcZI5c4ng==" lastName="" firstName="" version="2.0(2f)" buildTime="Sat Aug 20 23:07:07 PDT 2016" node="topology/pod-1/node-1">\n<aaaUserDomain name="all" rolesR="admin" rolesW="admin">\n<aaaReadRoles/>\n<aaaWriteRoles>\n<role name="admin"/>\n</aaaWriteRoles>\n</aaaUserDomain>\n<DnDomainMapEntry dn="uni/tn-common" readPrivileges="admin" writePrivileges="admin"/>\n<DnDomainMapEntry dn="uni/tn-infra" readPrivileges="admin" writePrivileges="admin"/>\n<DnDomainMapEntry dn="uni/tn-mgmt" readPrivileges="admin" writePrivileges="admin"/>\n</aaaLogin></imdata>\n'''  # NOQA
        xml_result = dict()
        aci.response_xml(xml_response)
        self.assertEqual(aci.imdata, imdata)
        self.assertEqual(aci.totalCount, totalCount)

    def test_invalid_input(self):
        self.maxDiff = None

        error = dict(
            code='401',
            text='Username or password is incorrect - FAILED local authentication',
        )

        imdata = [{
            'error': {
                'attributes': {
                    'code': '401',
                    'text': 'Username or password is incorrect - FAILED local authentication',
                },
            },
        }]

        totalCount = 1

        json_response = '{"totalCount":"1","imdata":[{"error":{"attributes":{"code":"401","text":"Username or password is incorrect - FAILED local authentication"}}}]}'  # NOQA
        json_result = dict()
        aci.response_json(json_response)
        self.assertEqual(aci.error, error)
        self.assertEqual(aci.imdata, imdata)
        self.assertEqual(aci.totalCount, totalCount)

        # Python 2.7+ is needed for xmljson
        if sys.version_info < (2, 7):
            return

        xml_response = '''<?xml version="1.0" encoding="UTF-8"?><imdata totalCount="1">
        <error code="401" text="Username or password is incorrect - FAILED local authentication"/>
        </imdata>
        '''
        xml_result = dict()
        aci.response_xml(xml_response)
        self.assertEqual(aci.error, error)
        self.assertEqual(aci.imdata, imdata)
        self.assertEqual(aci.totalCount, totalCount)

    def test_empty_response(self):
        self.maxDiffi = None

        if PY2:
            error_text = "Unable to parse output as JSON, see 'raw' output. No JSON object could be decoded"
        else:
            error_text = "Unable to parse output as JSON, see 'raw' output. Expecting value: line 1 column 1 (char 0)"

        error = dict(
            code=-1,
            text=error_text,
        )
        raw = ''

        json_response = ''
        json_result = dict()
        aci.response_json(json_response)
        self.assertEqual(aci.error, error)
        self.assertEqual(aci.result['raw'], raw)

        # Python 2.7+ is needed for xmljson
        if sys.version_info < (2, 7):
            return

        elif etree.LXML_VERSION < (3, 3, 0, 0):
            error_text = "Unable to parse output as XML, see 'raw' output. None",
        elif etree.LXML_VERSION < (4, 0, 0, 0):
            error_text = to_native(u"Unable to parse output as XML, see 'raw' output. None (line 0)", errors='surrogate_or_strict')
        elif PY2:
            error_text = "Unable to parse output as XML, see 'raw' output. Document is empty, line 1, column 1 (line 1)"
        elif sys.version_info >= (3, 8):
            error_text = "Unable to parse output as XML, see 'raw' output. None (line 0)"
        else:
            error_text = "Unable to parse output as XML, see 'raw' output. Document is empty, line 1, column 1 (<string>, line 1)"

        error = dict(
            code=-1,
            text=error_text,
        )

        raw = ''

        xml_response = ''
        xml_result = dict()
        aci.response_xml(xml_response)
        self.assertEqual(aci.error, error)
        self.assertEqual(aci.result['raw'], raw)

    def test_invalid_response(self):
        self.maxDiff = None

        if sys.version_info < (2, 7):
            error_text = "Unable to parse output as JSON, see 'raw' output. Expecting object: line 1 column 8 (char 8)"
        elif PY2:
            error_text = "Unable to parse output as JSON, see 'raw' output. No JSON object could be decoded"
        else:
            error_text = "Unable to parse output as JSON, see 'raw' output. Expecting value: line 1 column 9 (char 8)"

        error = dict(
            code=-1,
            text=error_text,
        )

        raw = '{ "aaa":'

        json_response = '{ "aaa":'
        json_result = dict()
        aci.response_json(json_response)
        self.assertEqual(aci.error, error)
        self.assertEqual(aci.result['raw'], raw)

        # Python 2.7+ is needed for xmljson
        if sys.version_info < (2, 7):
            return

        elif etree.LXML_VERSION < (3, 3, 0, 0):
            error_text = "Unable to parse output as XML, see 'raw' output. Couldn't find end of Start Tag aaa line 1, line 1, column 5"  # NOQA

        elif PY2:
            error_text = "Unable to parse output as XML, see 'raw' output. Couldn't find end of Start Tag aaa line 1, line 1, column 6 (line 1)"  # NOQA

        else:
            error_text = "Unable to parse output as XML, see 'raw' output. Couldn't find end of Start Tag aaa line 1, line 1, column 6 (<string>, line 1)"  # NOQA

        error = dict(
            code=-1,
            text=error_text,
        )

        raw = '<aaa '

        xml_response = '<aaa '
        xml_result = dict()
        aci.response_xml(xml_response)
        self.assertEqual(aci.error, error)
        self.assertEqual(aci.result['raw'], raw)
