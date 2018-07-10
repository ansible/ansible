import unittest

from ansible.modules.cloud.google.gcp_url_map import _build_path_matchers, _build_url_map_dict


class TestGCPUrlMap(unittest.TestCase):
    """Unit tests for gcp_url_map module."""
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

    def test__build_path_matchers(self):
        input_list = [
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
        expected = [
            {
                'defaultService': 'https://www.googleapis.com/compute/v1/projects/my-project/global/backendServices/bes-pathmatcher-one-default',
                'description': 'path matcher one',
                'name': 'path_matcher_one',
                'pathRules': [
                    {
                        'paths': [
                            '/',
                            '/aboutus'
                        ],
                        'service': 'https://www.googleapis.com/compute/v1/projects/my-project/global/backendServices/my-one-bes'
                    }
                ]
            },
            {
                'defaultService': 'https://www.googleapis.com/compute/v1/projects/my-project/global/backendServices/bes-pathmatcher-two-default',
                'description': 'path matcher two',
                'name': 'path_matcher_two',
                'pathRules': [
                    {
                        'paths': [
                            '/webapp',
                            '/graphs'
                        ],
                        'service': 'https://www.googleapis.com/compute/v1/projects/my-project/global/backendServices/my-two-bes'
                    }
                ]
            }
        ]
        actual = _build_path_matchers(input_list, 'my-project')
        self.assertEqual(expected, actual)

    def test__build_url_map_dict(self):

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
                    'defaultService': 'https://www.googleapis.com/compute/v1/projects/my-project/global/backendServices/bes-pathmatcher-one-default',
                    'description': 'path matcher one',
                    'name': 'path_matcher_one',
                    'pathRules': [
                        {
                            'paths': [
                                '/',
                                '/aboutus'
                            ],
                            'service': 'https://www.googleapis.com/compute/v1/projects/my-project/global/backendServices/my-one-bes'
                        }
                    ]
                },
                {
                    'defaultService': 'https://www.googleapis.com/compute/v1/projects/my-project/global/backendServices/bes-pathmatcher-two-default',
                    'description': 'path matcher two',
                    'name': 'path_matcher_two',
                    'pathRules': [
                        {
                            'paths': [
                                '/webapp',
                                '/graphs'
                            ],
                            'service': 'https://www.googleapis.com/compute/v1/projects/my-project/global/backendServices/my-two-bes'
                        }
                    ]
                }
            ]
        }
        actual = _build_url_map_dict(self.params_dict, 'my-project')
        self.assertEqual(expected, actual)
