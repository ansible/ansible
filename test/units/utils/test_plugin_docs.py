# -*- coding: utf-8 -*-
# (c) 2020 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import copy

import pytest

from ansible.utils.plugin_docs import (
    add_collection_to_versions_and_dates,
)


ADD_TESTS = [
    (
        # Module options
        True,
        False,
        {
            'author': 'x',
            'version_added': '1.0.0',
            'deprecated': {
                'removed_in': '2.0.0',
            },
            'options': {
                'test': {
                    'description': '',
                    'type': 'str',
                    'version_added': '1.1.0',
                    'deprecated': {
                        # should not be touched since this isn't a plugin
                        'removed_in': '2.0.0',
                    },
                    'env': [
                        # should not be touched since this isn't a plugin
                        {
                            'version_added': '1.3.0',
                            'deprecated': {
                                'version': '2.0.0',
                            },
                        },
                    ],
                    'ini': [
                        # should not be touched since this isn't a plugin
                        {
                            'version_added': '1.3.0',
                            'deprecated': {
                                'version': '2.0.0',
                            },
                        },
                    ],
                    'vars': [
                        # should not be touched since this isn't a plugin
                        {
                            'version_added': '1.3.0',
                            'deprecated': {
                                'removed_at_date': '2020-01-01',
                            },
                        },
                    ],
                },
                'subtest': {
                    'description': '',
                    'type': 'dict',
                    'deprecated': {
                        # should not be touched since this isn't a plugin
                        'version': '2.0.0',
                    },
                    'suboptions': {
                        'suboption': {
                            'description': '',
                            'type': 'int',
                            'version_added': '1.2.0',
                        }
                    },
                }
            },
        },
        {
            'author': 'x',
            'version_added': '1.0.0',
            'version_added_collection': 'foo.bar',
            'deprecated': {
                'removed_in': '2.0.0',
                'removed_from_collection': 'foo.bar',
            },
            'options': {
                'test': {
                    'description': '',
                    'type': 'str',
                    'version_added': '1.1.0',
                    'version_added_collection': 'foo.bar',
                    'deprecated': {
                        # should not be touched since this isn't a plugin
                        'removed_in': '2.0.0',
                    },
                    'env': [
                        # should not be touched since this isn't a plugin
                        {
                            'version_added': '1.3.0',
                            'deprecated': {
                                'version': '2.0.0',
                            },
                        },
                    ],
                    'ini': [
                        # should not be touched since this isn't a plugin
                        {
                            'version_added': '1.3.0',
                            'deprecated': {
                                'version': '2.0.0',
                            },
                        },
                    ],
                    'vars': [
                        # should not be touched since this isn't a plugin
                        {
                            'version_added': '1.3.0',
                            'deprecated': {
                                'removed_at_date': '2020-01-01',
                            },
                        },
                    ],
                },
                'subtest': {
                    'description': '',
                    'type': 'dict',
                    'deprecated': {
                        # should not be touched since this isn't a plugin
                        'version': '2.0.0',
                    },
                    'suboptions': {
                        'suboption': {
                            'description': '',
                            'type': 'int',
                            'version_added': '1.2.0',
                            'version_added_collection': 'foo.bar',
                        }
                    },
                }
            },
        },
    ),
    (
        # Module options
        True,
        False,
        {
            'author': 'x',
            'deprecated': {
                'removed_at_date': '2020-01-01',
            },
        },
        {
            'author': 'x',
            'deprecated': {
                'removed_at_date': '2020-01-01',
                'removed_from_collection': 'foo.bar',
            },
        },
    ),
    (
        # Plugin options
        False,
        False,
        {
            'author': 'x',
            'version_added': '1.0.0',
            'deprecated': {
                'removed_in': '2.0.0',
            },
            'options': {
                'test': {
                    'description': '',
                    'type': 'str',
                    'version_added': '1.1.0',
                    'deprecated': {
                        # should not be touched since this is the wrong name
                        'removed_in': '2.0.0',
                    },
                    'env': [
                        {
                            'version_added': '1.3.0',
                            'deprecated': {
                                'version': '2.0.0',
                            },
                        },
                    ],
                    'ini': [
                        {
                            'version_added': '1.3.0',
                            'deprecated': {
                                'version': '2.0.0',
                            },
                        },
                    ],
                    'vars': [
                        {
                            'version_added': '1.3.0',
                            'deprecated': {
                                'removed_at_date': '2020-01-01',
                            },
                        },
                    ],
                },
                'subtest': {
                    'description': '',
                    'type': 'dict',
                    'deprecated': {
                        'version': '2.0.0',
                    },
                    'suboptions': {
                        'suboption': {
                            'description': '',
                            'type': 'int',
                            'version_added': '1.2.0',
                        }
                    },
                }
            },
        },
        {
            'author': 'x',
            'version_added': '1.0.0',
            'version_added_collection': 'foo.bar',
            'deprecated': {
                'removed_in': '2.0.0',
                'removed_from_collection': 'foo.bar',
            },
            'options': {
                'test': {
                    'description': '',
                    'type': 'str',
                    'version_added': '1.1.0',
                    'version_added_collection': 'foo.bar',
                    'deprecated': {
                        # should not be touched since this is the wrong name
                        'removed_in': '2.0.0',
                    },
                    'env': [
                        {
                            'version_added': '1.3.0',
                            'version_added_collection': 'foo.bar',
                            'deprecated': {
                                'version': '2.0.0',
                                'collection_name': 'foo.bar',
                            },
                        },
                    ],
                    'ini': [
                        {
                            'version_added': '1.3.0',
                            'version_added_collection': 'foo.bar',
                            'deprecated': {
                                'version': '2.0.0',
                                'collection_name': 'foo.bar',
                            },
                        },
                    ],
                    'vars': [
                        {
                            'version_added': '1.3.0',
                            'version_added_collection': 'foo.bar',
                            'deprecated': {
                                'removed_at_date': '2020-01-01',
                                'collection_name': 'foo.bar',
                            },
                        },
                    ],
                },
                'subtest': {
                    'description': '',
                    'type': 'dict',
                    'deprecated': {
                        'version': '2.0.0',
                        'collection_name': 'foo.bar',
                    },
                    'suboptions': {
                        'suboption': {
                            'description': '',
                            'type': 'int',
                            'version_added': '1.2.0',
                            'version_added_collection': 'foo.bar',
                        }
                    },
                }
            },
        },
    ),
    (
        # Return values
        True,  # this value is is ignored
        True,
        {
            'rv1': {
                'version_added': '1.0.0',
                'type': 'dict',
                'contains': {
                    'srv1': {
                        'version_added': '1.1.0',
                    },
                    'srv2': {
                    },
                }
            },
        },
        {
            'rv1': {
                'version_added': '1.0.0',
                'version_added_collection': 'foo.bar',
                'type': 'dict',
                'contains': {
                    'srv1': {
                        'version_added': '1.1.0',
                        'version_added_collection': 'foo.bar',
                    },
                    'srv2': {
                    },
                }
            },
        },
    ),
]


@pytest.mark.parametrize('is_module,return_docs,fragment,expected_fragment', ADD_TESTS)
def test_add(is_module, return_docs, fragment, expected_fragment):
    fragment_copy = copy.deepcopy(fragment)
    add_collection_to_versions_and_dates(fragment_copy, 'foo.bar', is_module, return_docs)
    assert fragment_copy == expected_fragment
