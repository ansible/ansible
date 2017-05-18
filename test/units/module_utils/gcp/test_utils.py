# -*- coding: utf-8 -*-
# (c) 2016, Tom Melendez <tom@supertom.com>
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
import os
import sys

from ansible.compat.tests import mock, unittest
from ansible.module_utils.gcp import check_min_pkg_version, GCPUtils, GCPInvalidURLError


def build_distribution(version):
    obj = mock.MagicMock()
    obj.version = '0.5.0'
    return obj


class GCPUtilsTestCase(unittest.TestCase):
    params_dict = {
        'url_map_name': 'foo_url_map_name',
        'description': 'foo_url_map description',
        'host_rules': [
            {
                'description': 'host rules description',
                'hosts': [
                        'www.example.com',
                        'www2.example.com'
                ],
                'path_matcher': 'host_rules_path_matcher'
            }
        ],
        'path_matchers': [
            {
                'name': 'path_matcher_one',
                'description': 'path matcher one',
                'defaultService': 'bes-pathmatcher-one-default',
                'pathRules': [
                        {
                            'service': 'my-one-bes',
                            'paths': [
                                '/',
                                '/aboutus'
                            ]
                        }
                ]
            },
            {
                'name': 'path_matcher_two',
                'description': 'path matcher two',
                'defaultService': 'bes-pathmatcher-two-default',
                'pathRules': [
                        {
                            'service': 'my-two-bes',
                            'paths': [
                                '/webapp',
                                '/graphs'
                            ]
                        }
                ]
            }
        ]
    }

    @mock.patch("pkg_resources.get_distribution", side_effect=build_distribution)
    def test_check_minimum_pkg_version(self, mockobj):
        self.assertTrue(check_min_pkg_version('foobar', '0.4.0'))
        self.assertTrue(check_min_pkg_version('foobar', '0.5.0'))
        self.assertFalse(check_min_pkg_version('foobar', '0.6.0'))

    def test_parse_gcp_url(self):
        # region, resource, entity, method
        input_url = 'https://www.googleapis.com/compute/v1/projects/myproject/regions/us-east1/instanceGroupManagers/my-mig/recreateInstances'
        actual = GCPUtils.parse_gcp_url(input_url)
        self.assertEquals('compute', actual['service'])
        self.assertEquals('v1', actual['api_version'])
        self.assertEquals('myproject', actual['project'])
        self.assertEquals('us-east1', actual['region'])
        self.assertEquals('instanceGroupManagers', actual['resource_name'])
        self.assertEquals('my-mig', actual['entity_name'])
        self.assertEquals('recreateInstances', actual['method_name'])

        # zone, resource, entity, method
        input_url = 'https://www.googleapis.com/compute/v1/projects/myproject/zones/us-east1-c/instanceGroupManagers/my-mig/recreateInstances'
        actual = GCPUtils.parse_gcp_url(input_url)
        self.assertEquals('compute', actual['service'])
        self.assertEquals('v1', actual['api_version'])
        self.assertEquals('myproject', actual['project'])
        self.assertEquals('us-east1-c', actual['zone'])
        self.assertEquals('instanceGroupManagers', actual['resource_name'])
        self.assertEquals('my-mig', actual['entity_name'])
        self.assertEquals('recreateInstances', actual['method_name'])

        # global, resource
        input_url = 'https://www.googleapis.com/compute/v1/projects/myproject/global/urlMaps'
        actual = GCPUtils.parse_gcp_url(input_url)
        self.assertEquals('compute', actual['service'])
        self.assertEquals('v1', actual['api_version'])
        self.assertEquals('myproject', actual['project'])
        self.assertTrue('global' in actual)
        self.assertTrue(actual['global'])
        self.assertEquals('urlMaps', actual['resource_name'])

        # global, resource, entity
        input_url = 'https://www.googleapis.com/compute/v1/projects/myproject/global/urlMaps/my-url-map'
        actual = GCPUtils.parse_gcp_url(input_url)
        self.assertEquals('myproject', actual['project'])
        self.assertTrue('global' in actual)
        self.assertTrue(actual['global'])
        self.assertEquals('v1', actual['api_version'])
        self.assertEquals('compute', actual['service'])

        # global URL, resource, entity, method_name
        input_url = 'https://www.googleapis.com/compute/v1/projects/myproject/global/backendServices/mybackendservice/getHealth'
        actual = GCPUtils.parse_gcp_url(input_url)
        self.assertEquals('compute', actual['service'])
        self.assertEquals('v1', actual['api_version'])
        self.assertEquals('myproject', actual['project'])
        self.assertTrue('global' in actual)
        self.assertTrue(actual['global'])
        self.assertEquals('backendServices', actual['resource_name'])
        self.assertEquals('mybackendservice', actual['entity_name'])
        self.assertEquals('getHealth', actual['method_name'])

        # no location in URL
        input_url = 'https://www.googleapis.com/compute/v1/projects/myproject/targetHttpProxies/mytargetproxy/setUrlMap'
        actual = GCPUtils.parse_gcp_url(input_url)
        self.assertEquals('compute', actual['service'])
        self.assertEquals('v1', actual['api_version'])
        self.assertEquals('myproject', actual['project'])
        self.assertFalse('global' in actual)
        self.assertEquals('targetHttpProxies', actual['resource_name'])
        self.assertEquals('mytargetproxy', actual['entity_name'])
        self.assertEquals('setUrlMap', actual['method_name'])

        input_url = 'https://www.googleapis.com/compute/v1/projects/myproject/targetHttpProxies/mytargetproxy'
        actual = GCPUtils.parse_gcp_url(input_url)
        self.assertEquals('compute', actual['service'])
        self.assertEquals('v1', actual['api_version'])
        self.assertEquals('myproject', actual['project'])
        self.assertFalse('global' in actual)
        self.assertEquals('targetHttpProxies', actual['resource_name'])
        self.assertEquals('mytargetproxy', actual['entity_name'])

        input_url = 'https://www.googleapis.com/compute/v1/projects/myproject/targetHttpProxies'
        actual = GCPUtils.parse_gcp_url(input_url)
        self.assertEquals('compute', actual['service'])
        self.assertEquals('v1', actual['api_version'])
        self.assertEquals('myproject', actual['project'])
        self.assertFalse('global' in actual)
        self.assertEquals('targetHttpProxies', actual['resource_name'])

        # test exceptions
        no_projects_input_url = 'https://www.googleapis.com/compute/v1/not-projects/myproject/global/backendServices/mybackendservice/getHealth'
        no_resource_input_url = 'https://www.googleapis.com/compute/v1/not-projects/myproject/global'

        no_resource_no_loc_input_url = 'https://www.googleapis.com/compute/v1/not-projects/myproject'

        with self.assertRaises(GCPInvalidURLError) as cm:
            GCPUtils.parse_gcp_url(no_projects_input_url)
        self.assertTrue(cm.exception, GCPInvalidURLError)

        with self.assertRaises(GCPInvalidURLError) as cm:
            GCPUtils.parse_gcp_url(no_resource_input_url)
        self.assertTrue(cm.exception, GCPInvalidURLError)

        with self.assertRaises(GCPInvalidURLError) as cm:
            GCPUtils.parse_gcp_url(no_resource_no_loc_input_url)
        self.assertTrue(cm.exception, GCPInvalidURLError)

    def test_params_to_gcp_dict(self):

        expected = {
            'description': 'foo_url_map description',
            'hostRules': [
                {
                    'description': 'host rules description',
                    'hosts': [
                        'www.example.com',
                        'www2.example.com'
                    ],
                    'pathMatcher': 'host_rules_path_matcher'
                }
            ],
            'name': 'foo_url_map_name',
            'pathMatchers': [
                {
                    'defaultService': 'bes-pathmatcher-one-default',
                    'description': 'path matcher one',
                    'name': 'path_matcher_one',
                    'pathRules': [
                        {
                            'paths': [
                                '/',
                                '/aboutus'
                            ],
                            'service': 'my-one-bes'
                        }
                    ]
                },
                {
                    'defaultService': 'bes-pathmatcher-two-default',
                    'description': 'path matcher two',
                    'name': 'path_matcher_two',
                    'pathRules': [
                        {
                            'paths': [
                                '/webapp',
                                '/graphs'
                            ],
                            'service': 'my-two-bes'
                        }
                    ]
                }
            ]
        }

        actual = GCPUtils.params_to_gcp_dict(self.params_dict, 'url_map_name')
        self.assertEqual(expected, actual)

    def test_get_gcp_resource_from_methodId(self):
        input_data = 'compute.urlMaps.list'
        actual = GCPUtils.get_gcp_resource_from_methodId(input_data)
        self.assertEqual('urlMaps', actual)
        input_data = None
        actual = GCPUtils.get_gcp_resource_from_methodId(input_data)
        self.assertFalse(actual)
        input_data = 666
        actual = GCPUtils.get_gcp_resource_from_methodId(input_data)
        self.assertFalse(actual)

    def test_get_entity_name_from_resource_name(self):
        input_data = 'urlMaps'
        actual = GCPUtils.get_entity_name_from_resource_name(input_data)
        self.assertEqual('urlMap', actual)
        input_data = 'targetHttpProxies'
        actual = GCPUtils.get_entity_name_from_resource_name(input_data)
        self.assertEqual('targetHttpProxy', actual)
        input_data = 'globalForwardingRules'
        actual = GCPUtils.get_entity_name_from_resource_name(input_data)
        self.assertEqual('forwardingRule', actual)
        input_data = ''
        actual = GCPUtils.get_entity_name_from_resource_name(input_data)
        self.assertEqual(None, actual)
        input_data = 666
        actual = GCPUtils.get_entity_name_from_resource_name(input_data)
        self.assertEqual(None, actual)

    def test_are_params_equal(self):
        params1 = {'one': 1}
        params2 = {'one': 1}
        actual = GCPUtils.are_params_equal(params1, params2)
        self.assertTrue(actual)

        params1 = {'one': 1}
        params2 = {'two': 2}
        actual = GCPUtils.are_params_equal(params1, params2)
        self.assertFalse(actual)

        params1 = {'three': 3, 'two': 2, 'one': 1}
        params2 = {'one': 1, 'two': 2, 'three': 3}
        actual = GCPUtils.are_params_equal(params1, params2)
        self.assertTrue(actual)

        params1 = {
            "creationTimestamp": "2017-04-21T11:19:20.718-07:00",
            "defaultService": "https://www.googleapis.com/compute/v1/projects/myproject/global/backendServices/default-backend-service",
            "description": "",
            "fingerprint": "ickr_pwlZPU=",
            "hostRules": [
                {
                    "description": "",
                    "hosts": [
                        "*."
                    ],
                    "pathMatcher": "path-matcher-one"
                }
            ],
            "id": "8566395781175047111",
            "kind": "compute#urlMap",
            "name": "newtesturlmap-foo",
            "pathMatchers": [
                {
                    "defaultService": "https://www.googleapis.com/compute/v1/projects/myproject/global/backendServices/bes-pathmatcher-one-default",
                    "description": "path matcher one",
                    "name": "path-matcher-one",
                    "pathRules": [
                        {
                            "paths": [
                                "/data",
                                "/aboutus"
                            ],
                            "service": "https://www.googleapis.com/compute/v1/projects/myproject/global/backendServices/my-one-bes"
                        }
                    ]
                }
            ],
            "selfLink": "https://www.googleapis.com/compute/v1/projects/myproject/global/urlMaps/newtesturlmap-foo"
        }
        params2 = {
            "defaultService": "https://www.googleapis.com/compute/v1/projects/myproject/global/backendServices/default-backend-service",
            "hostRules": [
                {
                    "description": "",
                    "hosts": [
                        "*."
                    ],
                    "pathMatcher": "path-matcher-one"
                }
            ],
            "name": "newtesturlmap-foo",
            "pathMatchers": [
                {
                    "defaultService": "https://www.googleapis.com/compute/v1/projects/myproject/global/backendServices/bes-pathmatcher-one-default",
                    "description": "path matcher one",
                    "name": "path-matcher-one",
                    "pathRules": [
                        {
                            "paths": [
                                "/data",
                                "/aboutus"
                            ],
                            "service": "https://www.googleapis.com/compute/v1/projects/myproject/global/backendServices/my-one-bes"
                        }
                    ]
                }
            ],
        }

        # params1 has exclude fields, params2 doesn't. Should be equal
        actual = GCPUtils.are_params_equal(params1, params2)
        self.assertTrue(actual)

    def test_filter_gcp_fields(self):
        input_data = {
            u'kind': u'compute#httpsHealthCheck',
            u'description': u'',
            u'timeoutSec': 5,
            u'checkIntervalSec': 5,
            u'port': 443,
            u'healthyThreshold': 2,
            u'host': u'',
            u'requestPath': u'/',
            u'unhealthyThreshold': 2,
            u'creationTimestamp': u'2017-05-16T15:09:36.546-07:00',
            u'id': u'8727093129334146639',
            u'selfLink': u'https://www.googleapis.com/compute/v1/projects/myproject/global/httpsHealthChecks/myhealthcheck',
            u'name': u'myhealthcheck'}

        expected = {
            'name': 'myhealthcheck',
            'checkIntervalSec': 5,
            'port': 443,
            'unhealthyThreshold': 2,
            'healthyThreshold': 2,
            'host': '',
            'timeoutSec': 5,
            'requestPath': '/'}

        actual = GCPUtils.filter_gcp_fields(input_data)
        self.assertEquals(expected, actual)
