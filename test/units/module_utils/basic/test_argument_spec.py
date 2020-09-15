# -*- coding: utf-8 -*-
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2016 Toshio Kuratomi <tkuratomi@ansible.com>
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import os

import pytest

from units.compat.mock import MagicMock
from ansible.module_utils import basic
from ansible.module_utils.api import basic_auth_argument_spec, rate_limit_argument_spec, retry_argument_spec
from ansible.module_utils.six import integer_types, string_types
from ansible.module_utils.six.moves import builtins


MOCK_VALIDATOR_FAIL = MagicMock(side_effect=TypeError("bad conversion"))
# Data is argspec, argument, expected
VALID_SPECS = (
    # Simple type=int
    ({'arg': {'type': 'int'}}, {'arg': 42}, 42),
    # Simple type=int with a large value (will be of type long under Python 2)
    ({'arg': {'type': 'int'}}, {'arg': 18765432109876543210}, 18765432109876543210),
    # Simple type=list, elements=int
    ({'arg': {'type': 'list', 'elements': 'int'}}, {'arg': [42, 32]}, [42, 32]),
    # Type=int with conversion from string
    ({'arg': {'type': 'int'}}, {'arg': '42'}, 42),
    # Type=list elements=int with conversion from string
    ({'arg': {'type': 'list', 'elements': 'int'}}, {'arg': ['42', '32']}, [42, 32]),
    # Simple type=float
    ({'arg': {'type': 'float'}}, {'arg': 42.0}, 42.0),
    # Simple type=list, elements=float
    ({'arg': {'type': 'list', 'elements': 'float'}}, {'arg': [42.1, 32.2]}, [42.1, 32.2]),
    # Type=float conversion from int
    ({'arg': {'type': 'float'}}, {'arg': 42}, 42.0),
    # type=list, elements=float conversion from int
    ({'arg': {'type': 'list', 'elements': 'float'}}, {'arg': [42, 32]}, [42.0, 32.0]),
    # Type=float conversion from string
    ({'arg': {'type': 'float'}}, {'arg': '42.0'}, 42.0),
    # type=list, elements=float conversion from string
    ({'arg': {'type': 'list', 'elements': 'float'}}, {'arg': ['42.1', '32.2']}, [42.1, 32.2]),
    # Type=float conversion from string without decimal point
    ({'arg': {'type': 'float'}}, {'arg': '42'}, 42.0),
    # Type=list elements=float conversion from string without decimal point
    ({'arg': {'type': 'list', 'elements': 'float'}}, {'arg': ['42', '32.2']}, [42.0, 32.2]),
    # Simple type=bool
    ({'arg': {'type': 'bool'}}, {'arg': True}, True),
    # Simple type=list elements=bool
    ({'arg': {'type': 'list', 'elements': 'bool'}}, {'arg': [True, 'true', 1, 'yes', False, 'false', 'no', 0]},
     [True, True, True, True, False, False, False, False]),
    # Type=int with conversion from string
    ({'arg': {'type': 'bool'}}, {'arg': 'yes'}, True),
    # Type=str converts to string
    ({'arg': {'type': 'str'}}, {'arg': 42}, '42'),
    # Type=list elements=str simple converts to string
    ({'arg': {'type': 'list', 'elements': 'str'}}, {'arg': ['42', '32']}, ['42', '32']),
    # Type is implicit, converts to string
    ({'arg': {'type': 'str'}}, {'arg': 42}, '42'),
    # Type=list elements=str implicit converts to string
    ({'arg': {'type': 'list', 'elements': 'str'}}, {'arg': [42, 32]}, ['42', '32']),
    # parameter is required
    ({'arg': {'required': True}}, {'arg': 42}, '42'),
)

INVALID_SPECS = (
    # Type is int; unable to convert this string
    ({'arg': {'type': 'int'}}, {'arg': "wolf"}, "is of type {0} and we were unable to convert to int: {0} cannot be converted to an int".format(type('bad'))),
    # Type is list elements is int; unable to convert this string
    ({'arg': {'type': 'list', 'elements': 'int'}}, {'arg': [1, "bad"]}, "is of type {0} and we were unable to convert to int: {0} cannot be converted to "
                                                                        "an int".format(type('int'))),
    # Type is int; unable to convert float
    ({'arg': {'type': 'int'}}, {'arg': 42.1}, "'float'> cannot be converted to an int"),
    # Type is list, elements is int; unable to convert float
    ({'arg': {'type': 'list', 'elements': 'int'}}, {'arg': [42.1, 32, 2]}, "'float'> cannot be converted to an int"),
    # type is a callable that fails to convert
    ({'arg': {'type': MOCK_VALIDATOR_FAIL}}, {'arg': "bad"}, "bad conversion"),
    # type is a list, elements is callable that fails to convert
    ({'arg': {'type': 'list', 'elements': MOCK_VALIDATOR_FAIL}}, {'arg': [1, "bad"]}, "bad conversion"),
    # unknown parameter
    ({'arg': {'type': 'int'}}, {'other': 'bad', '_ansible_module_name': 'ansible_unittest'},
     'Unsupported parameters for (ansible_unittest) module: other Supported parameters include: arg'),
    # parameter is required
    ({'arg': {'required': True}}, {}, 'missing required arguments: arg'),
)

BASIC_AUTH_VALID_ARGS = [
    {'api_username': 'user1', 'api_password': 'password1', 'api_url': 'http://example.com', 'validate_certs': False},
    {'api_username': 'user1', 'api_password': 'password1', 'api_url': 'http://example.com', 'validate_certs': True},
]

RATE_LIMIT_VALID_ARGS = [
    {'rate': 1, 'rate_limit': 1},
    {'rate': '1', 'rate_limit': 1},
    {'rate': 1, 'rate_limit': '1'},
    {'rate': '1', 'rate_limit': '1'},
]

RETRY_VALID_ARGS = [
    {'retries': 1, 'retry_pause': 1.5},
    {'retries': '1', 'retry_pause': '1.5'},
    {'retries': 1, 'retry_pause': '1.5'},
    {'retries': '1', 'retry_pause': 1.5},
]


@pytest.fixture
def complex_argspec():
    arg_spec = dict(
        foo=dict(required=True, aliases=['dup']),
        bar=dict(),
        bam=dict(),
        bing=dict(),
        bang=dict(),
        bong=dict(),
        baz=dict(fallback=(basic.env_fallback, ['BAZ'])),
        bar1=dict(type='bool'),
        bar3=dict(type='list', elements='path'),
        zardoz=dict(choices=['one', 'two']),
        zardoz2=dict(type='list', choices=['one', 'two', 'three']),
    )
    mut_ex = (('bar', 'bam'), ('bing', 'bang', 'bong'))
    req_to = (('bam', 'baz'),)

    kwargs = dict(
        argument_spec=arg_spec,
        mutually_exclusive=mut_ex,
        required_together=req_to,
        no_log=True,
        add_file_common_args=True,
        supports_check_mode=True,
    )
    return kwargs


@pytest.fixture
def options_argspec_list():
    options_spec = dict(
        foo=dict(required=True, aliases=['dup']),
        bar=dict(),
        bar1=dict(type='list', elements='str'),
        bar2=dict(type='list', elements='int'),
        bar3=dict(type='list', elements='float'),
        bar4=dict(type='list', elements='path'),
        bam=dict(),
        baz=dict(fallback=(basic.env_fallback, ['BAZ'])),
        bam1=dict(),
        bam2=dict(default='test'),
        bam3=dict(type='bool'),
        bam4=dict(type='str'),
    )

    arg_spec = dict(
        foobar=dict(
            type='list',
            elements='dict',
            options=options_spec,
            mutually_exclusive=[
                ['bam', 'bam1'],
            ],
            required_if=[
                ['foo', 'hello', ['bam']],
                ['foo', 'bam2', ['bam2']]
            ],
            required_one_of=[
                ['bar', 'bam']
            ],
            required_together=[
                ['bam1', 'baz']
            ],
            required_by={
                'bam4': ('bam1', 'bam3'),
            },
        )
    )

    kwargs = dict(
        argument_spec=arg_spec,
        no_log=True,
        add_file_common_args=True,
        supports_check_mode=True
    )
    return kwargs


@pytest.fixture
def options_argspec_dict(options_argspec_list):
    # should test ok, for options in dict format.
    kwargs = options_argspec_list
    kwargs['argument_spec']['foobar']['type'] = 'dict'
    kwargs['argument_spec']['foobar']['elements'] = None

    return kwargs


#
# Tests for one aspect of arg_spec
#

@pytest.mark.parametrize('argspec, expected, stdin', [(s[0], s[2], s[1]) for s in VALID_SPECS],
                         indirect=['stdin'])
def test_validator_basic_types(argspec, expected, stdin):

    am = basic.AnsibleModule(argspec)

    if 'type' in argspec['arg']:
        if argspec['arg']['type'] == 'int':
            type_ = integer_types
        else:
            type_ = getattr(builtins, argspec['arg']['type'])
    else:
        type_ = str

    assert isinstance(am.params['arg'], type_)
    assert am.params['arg'] == expected


@pytest.mark.parametrize('stdin', [{'arg': 42}, {'arg': 18765432109876543210}], indirect=['stdin'])
def test_validator_function(mocker, stdin):
    # Type is a callable
    MOCK_VALIDATOR_SUCCESS = mocker.MagicMock(return_value=27)
    argspec = {'arg': {'type': MOCK_VALIDATOR_SUCCESS}}
    am = basic.AnsibleModule(argspec)

    assert isinstance(am.params['arg'], integer_types)
    assert am.params['arg'] == 27


@pytest.mark.parametrize('stdin', BASIC_AUTH_VALID_ARGS, indirect=['stdin'])
def test_validate_basic_auth_arg(mocker, stdin):
    kwargs = dict(
        argument_spec=basic_auth_argument_spec()
    )
    am = basic.AnsibleModule(**kwargs)
    assert isinstance(am.params['api_username'], string_types)
    assert isinstance(am.params['api_password'], string_types)
    assert isinstance(am.params['api_url'], string_types)
    assert isinstance(am.params['validate_certs'], bool)


@pytest.mark.parametrize('stdin', RATE_LIMIT_VALID_ARGS, indirect=['stdin'])
def test_validate_rate_limit_argument_spec(mocker, stdin):
    kwargs = dict(
        argument_spec=rate_limit_argument_spec()
    )
    am = basic.AnsibleModule(**kwargs)
    assert isinstance(am.params['rate'], integer_types)
    assert isinstance(am.params['rate_limit'], integer_types)


@pytest.mark.parametrize('stdin', RETRY_VALID_ARGS, indirect=['stdin'])
def test_validate_retry_argument_spec(mocker, stdin):
    kwargs = dict(
        argument_spec=retry_argument_spec()
    )
    am = basic.AnsibleModule(**kwargs)
    assert isinstance(am.params['retries'], integer_types)
    assert isinstance(am.params['retry_pause'], float)


@pytest.mark.parametrize('stdin', [{'arg': '123'}, {'arg': 123}], indirect=['stdin'])
def test_validator_string_type(mocker, stdin):
    # Custom callable that is 'str'
    argspec = {'arg': {'type': str}}
    am = basic.AnsibleModule(argspec)

    assert isinstance(am.params['arg'], string_types)
    assert am.params['arg'] == '123'


@pytest.mark.parametrize('argspec, expected, stdin', [(s[0], s[2], s[1]) for s in INVALID_SPECS],
                         indirect=['stdin'])
def test_validator_fail(stdin, capfd, argspec, expected):
    with pytest.raises(SystemExit):
        basic.AnsibleModule(argument_spec=argspec)

    out, err = capfd.readouterr()
    assert not err
    assert expected in json.loads(out)['msg']
    assert json.loads(out)['failed']


class TestComplexArgSpecs:
    """Test with a more complex arg_spec"""

    @pytest.mark.parametrize('stdin', [{'foo': 'hello'}, {'dup': 'hello'}], indirect=['stdin'])
    def test_complex_required(self, stdin, complex_argspec):
        """Test that the complex argspec works if we give it its required param as either the canonical or aliased name"""
        am = basic.AnsibleModule(**complex_argspec)
        assert isinstance(am.params['foo'], str)
        assert am.params['foo'] == 'hello'

    @pytest.mark.parametrize('stdin', [{'foo': 'hello1', 'dup': 'hello2'}], indirect=['stdin'])
    def test_complex_duplicate_warning(self, stdin, complex_argspec):
        """Test that the complex argspec issues a warning if we specify an option both with its canonical name and its alias"""
        am = basic.AnsibleModule(**complex_argspec)
        assert isinstance(am.params['foo'], str)
        assert 'Both option foo and its alias dup are set.' in am._warnings
        assert am.params['foo'] == 'hello2'

    @pytest.mark.parametrize('stdin', [{'foo': 'hello', 'bam': 'test'}], indirect=['stdin'])
    def test_complex_type_fallback(self, mocker, stdin, complex_argspec):
        """Test that the complex argspec works if we get a required parameter via fallback"""
        environ = os.environ.copy()
        environ['BAZ'] = 'test data'
        mocker.patch('ansible.module_utils.basic.os.environ', environ)

        am = basic.AnsibleModule(**complex_argspec)

        assert isinstance(am.params['baz'], str)
        assert am.params['baz'] == 'test data'

    @pytest.mark.parametrize('stdin', [{'foo': 'hello', 'bar': 'bad', 'bam': 'bad2', 'bing': 'a', 'bang': 'b', 'bong': 'c'}], indirect=['stdin'])
    def test_fail_mutually_exclusive(self, capfd, stdin, complex_argspec):
        """Fail because of mutually exclusive parameters"""
        with pytest.raises(SystemExit):
            am = basic.AnsibleModule(**complex_argspec)

        out, err = capfd.readouterr()
        results = json.loads(out)

        assert results['failed']
        assert results['msg'] == "parameters are mutually exclusive: bar|bam, bing|bang|bong"

    @pytest.mark.parametrize('stdin', [{'foo': 'hello', 'bam': 'bad2'}], indirect=['stdin'])
    def test_fail_required_together(self, capfd, stdin, complex_argspec):
        """Fail because only one of a required_together pair of parameters was specified"""
        with pytest.raises(SystemExit):
            am = basic.AnsibleModule(**complex_argspec)

        out, err = capfd.readouterr()
        results = json.loads(out)

        assert results['failed']
        assert results['msg'] == "parameters are required together: bam, baz"

    @pytest.mark.parametrize('stdin', [{'foo': 'hello', 'bar': 'hi'}], indirect=['stdin'])
    def test_fail_required_together_and_default(self, capfd, stdin, complex_argspec):
        """Fail because one of a required_together pair of parameters has a default and the other was not specified"""
        complex_argspec['argument_spec']['baz'] = {'default': 42}
        with pytest.raises(SystemExit):
            am = basic.AnsibleModule(**complex_argspec)

        out, err = capfd.readouterr()
        results = json.loads(out)

        assert results['failed']
        assert results['msg'] == "parameters are required together: bam, baz"

    @pytest.mark.parametrize('stdin', [{'foo': 'hello'}], indirect=['stdin'])
    def test_fail_required_together_and_fallback(self, capfd, mocker, stdin, complex_argspec):
        """Fail because one of a required_together pair of parameters has a fallback and the other was not specified"""
        environ = os.environ.copy()
        environ['BAZ'] = 'test data'
        mocker.patch('ansible.module_utils.basic.os.environ', environ)

        with pytest.raises(SystemExit):
            am = basic.AnsibleModule(**complex_argspec)

        out, err = capfd.readouterr()
        results = json.loads(out)

        assert results['failed']
        assert results['msg'] == "parameters are required together: bam, baz"

    @pytest.mark.parametrize('stdin', [{'foo': 'hello', 'zardoz2': ['one', 'four', 'five']}], indirect=['stdin'])
    def test_fail_list_with_choices(self, capfd, mocker, stdin, complex_argspec):
        """Fail because one of the items is not in the choice"""
        with pytest.raises(SystemExit):
            basic.AnsibleModule(**complex_argspec)

        out, err = capfd.readouterr()
        results = json.loads(out)

        assert results['failed']
        assert results['msg'] == "value of zardoz2 must be one or more of: one, two, three. Got no match for: four, five"

    @pytest.mark.parametrize('stdin', [{'foo': 'hello', 'zardoz2': ['one', 'three']}], indirect=['stdin'])
    def test_list_with_choices(self, capfd, mocker, stdin, complex_argspec):
        """Test choices with list"""
        am = basic.AnsibleModule(**complex_argspec)
        assert isinstance(am.params['zardoz2'], list)
        assert am.params['zardoz2'] == ['one', 'three']

    @pytest.mark.parametrize('stdin', [{'foo': 'hello', 'bar3': ['~/test', 'test/']}], indirect=['stdin'])
    def test_list_with_elements_path(self, capfd, mocker, stdin, complex_argspec):
        """Test choices with list"""
        am = basic.AnsibleModule(**complex_argspec)
        assert isinstance(am.params['bar3'], list)
        assert am.params['bar3'][0].startswith('/')
        assert am.params['bar3'][1] == 'test/'


class TestComplexOptions:
    """Test arg spec options"""

    # (Parameters, expected value of module.params['foobar'])
    OPTIONS_PARAMS_LIST = (
        ({'foobar': [{"foo": "hello", "bam": "good"}, {"foo": "test", "bar": "good"}]},
         [{'foo': 'hello', 'bam': 'good', 'bam2': 'test', 'bar': None, 'baz': None, 'bam1': None, 'bam3': None, 'bam4': None,
           'bar1': None, 'bar2': None, 'bar3': None, 'bar4': None},
          {'foo': 'test', 'bam': None, 'bam2': 'test', 'bar': 'good', 'baz': None, 'bam1': None, 'bam3': None, 'bam4': None,
           'bar1': None, 'bar2': None, 'bar3': None, 'bar4': None}]
         ),
        # Alias for required param
        ({'foobar': [{"dup": "test", "bar": "good"}]},
         [{'foo': 'test', 'dup': 'test', 'bam': None, 'bam2': 'test', 'bar': 'good', 'baz': None, 'bam1': None, 'bam3': None, 'bam4': None,
           'bar1': None, 'bar2': None, 'bar3': None, 'bar4': None}]
         ),
        # Required_if utilizing default value of the requirement
        ({'foobar': [{"foo": "bam2", "bar": "required_one_of"}]},
         [{'bam': None, 'bam1': None, 'bam2': 'test', 'bam3': None, 'bam4': None, 'bar': 'required_one_of', 'baz': None, 'foo': 'bam2',
           'bar1': None, 'bar2': None, 'bar3': None, 'bar4': None}]
         ),
        # Check that a bool option is converted
        ({"foobar": [{"foo": "required", "bam": "good", "bam3": "yes"}]},
         [{'bam': 'good', 'bam1': None, 'bam2': 'test', 'bam3': True, 'bam4': None, 'bar': None, 'baz': None, 'foo': 'required',
           'bar1': None, 'bar2': None, 'bar3': None, 'bar4': None}]
         ),
        # Check required_by options
        ({"foobar": [{"foo": "required", "bar": "good", "baz": "good", "bam4": "required_by", "bam1": "ok", "bam3": "yes"}]},
         [{'bar': 'good', 'baz': 'good', 'bam1': 'ok', 'bam2': 'test', 'bam3': True, 'bam4': 'required_by', 'bam': None, 'foo': 'required',
           'bar1': None, 'bar2': None, 'bar3': None, 'bar4': None}]
         ),
        # Check for elements in sub-options
        ({"foobar": [{"foo": "good", "bam": "required_one_of", "bar1": [1, "good", "yes"], "bar2": ['1', 1], "bar3":['1.3', 1.3, 1]}]},
         [{'foo': 'good', 'bam1': None, 'bam2': 'test', 'bam3': None, 'bam4': None, 'bar': None, 'baz': None, 'bam': 'required_one_of',
           'bar1': ["1", "good", "yes"], 'bar2': [1, 1], 'bar3': [1.3, 1.3, 1.0], 'bar4': None}]
         ),
    )

    # (Parameters, expected value of module.params['foobar'])
    OPTIONS_PARAMS_DICT = (
        ({'foobar': {"foo": "hello", "bam": "good"}},
         {'foo': 'hello', 'bam': 'good', 'bam2': 'test', 'bar': None, 'baz': None, 'bam1': None, 'bam3': None, 'bam4': None,
          'bar1': None, 'bar2': None, 'bar3': None, 'bar4': None}
         ),
        # Alias for required param
        ({'foobar': {"dup": "test", "bar": "good"}},
         {'foo': 'test', 'dup': 'test', 'bam': None, 'bam2': 'test', 'bar': 'good', 'baz': None, 'bam1': None, 'bam3': None, 'bam4': None,
          'bar1': None, 'bar2': None, 'bar3': None, 'bar4': None}
         ),
        # Required_if utilizing default value of the requirement
        ({'foobar': {"foo": "bam2", "bar": "required_one_of"}},
         {'bam': None, 'bam1': None, 'bam2': 'test', 'bam3': None, 'bam4': None, 'bar': 'required_one_of', 'baz': None, 'foo': 'bam2',
          'bar1': None, 'bar2': None, 'bar3': None, 'bar4': None}
         ),
        # Check that a bool option is converted
        ({"foobar": {"foo": "required", "bam": "good", "bam3": "yes"}},
         {'bam': 'good', 'bam1': None, 'bam2': 'test', 'bam3': True, 'bam4': None, 'bar': None, 'baz': None, 'foo': 'required',
          'bar1': None, 'bar2': None, 'bar3': None, 'bar4': None}
         ),
        # Check required_by options
        ({"foobar": {"foo": "required", "bar": "good", "baz": "good", "bam4": "required_by", "bam1": "ok", "bam3": "yes"}},
         {'bar': 'good', 'baz': 'good', 'bam1': 'ok', 'bam2': 'test', 'bam3': True, 'bam4': 'required_by', 'bam': None,
          'foo': 'required', 'bar1': None, 'bar3': None, 'bar2': None, 'bar4': None}
         ),
        # Check for elements in sub-options
        ({"foobar": {"foo": "good", "bam": "required_one_of", "bar1": [1, "good", "yes"],
                     "bar2": ['1', 1], "bar3": ['1.3', 1.3, 1]}},
         {'foo': 'good', 'bam1': None, 'bam2': 'test', 'bam3': None, 'bam4': None, 'bar': None,
          'baz': None, 'bam': 'required_one_of',
          'bar1': ["1", "good", "yes"], 'bar2': [1, 1], 'bar3': [1.3, 1.3, 1.0], 'bar4': None}
         ),
    )

    # (Parameters, failure message)
    FAILING_PARAMS_LIST = (
        # Missing required option
        ({'foobar': [{}]}, 'missing required arguments: foo found in foobar'),
        # Invalid option
        ({'foobar': [{"foo": "hello", "bam": "good", "invalid": "bad"}]}, 'module: invalid found in foobar. Supported parameters include'),
        # Mutually exclusive options found
        ({'foobar': [{"foo": "test", "bam": "bad", "bam1": "bad", "baz": "req_to"}]},
         'parameters are mutually exclusive: bam|bam1 found in foobar'),
        # required_if fails
        ({'foobar': [{"foo": "hello", "bar": "bad"}]},
         'foo is hello but all of the following are missing: bam found in foobar'),
        # Missing required_one_of option
        ({'foobar': [{"foo": "test"}]},
         'one of the following is required: bar, bam found in foobar'),
        # Missing required_together option
        ({'foobar': [{"foo": "test", "bar": "required_one_of", "bam1": "bad"}]},
         'parameters are required together: bam1, baz found in foobar'),
        # Missing required_by options
        ({'foobar': [{"foo": "test", "bar": "required_one_of", "bam4": "required_by"}]},
         "missing parameter(s) required by 'bam4': bam1, bam3"),
    )

    # (Parameters, failure message)
    FAILING_PARAMS_DICT = (
        # Missing required option
        ({'foobar': {}}, 'missing required arguments: foo found in foobar'),
        # Invalid option
        ({'foobar': {"foo": "hello", "bam": "good", "invalid": "bad"}},
         'module: invalid found in foobar. Supported parameters include'),
        # Mutually exclusive options found
        ({'foobar': {"foo": "test", "bam": "bad", "bam1": "bad", "baz": "req_to"}},
         'parameters are mutually exclusive: bam|bam1 found in foobar'),
        # required_if fails
        ({'foobar': {"foo": "hello", "bar": "bad"}},
         'foo is hello but all of the following are missing: bam found in foobar'),
        # Missing required_one_of option
        ({'foobar': {"foo": "test"}},
         'one of the following is required: bar, bam found in foobar'),
        # Missing required_together option
        ({'foobar': {"foo": "test", "bar": "required_one_of", "bam1": "bad"}},
         'parameters are required together: bam1, baz found in foobar'),
        # Missing required_by options
        ({'foobar': {"foo": "test", "bar": "required_one_of", "bam4": "required_by"}},
         "missing parameter(s) required by 'bam4': bam1, bam3"),
    )

    @pytest.mark.parametrize('stdin, expected', OPTIONS_PARAMS_DICT, indirect=['stdin'])
    def test_options_type_dict(self, stdin, options_argspec_dict, expected):
        """Test that a basic creation with required and required_if works"""
        # should test ok, tests basic foo requirement and required_if
        am = basic.AnsibleModule(**options_argspec_dict)

        assert isinstance(am.params['foobar'], dict)
        assert am.params['foobar'] == expected

    @pytest.mark.parametrize('stdin, expected', OPTIONS_PARAMS_LIST, indirect=['stdin'])
    def test_options_type_list(self, stdin, options_argspec_list, expected):
        """Test that a basic creation with required and required_if works"""
        # should test ok, tests basic foo requirement and required_if
        am = basic.AnsibleModule(**options_argspec_list)

        assert isinstance(am.params['foobar'], list)
        assert am.params['foobar'] == expected

    @pytest.mark.parametrize('stdin, expected', FAILING_PARAMS_DICT, indirect=['stdin'])
    def test_fail_validate_options_dict(self, capfd, stdin, options_argspec_dict, expected):
        """Fail because one of a required_together pair of parameters has a default and the other was not specified"""
        with pytest.raises(SystemExit):
            am = basic.AnsibleModule(**options_argspec_dict)

        out, err = capfd.readouterr()
        results = json.loads(out)

        assert results['failed']
        assert expected in results['msg']

    @pytest.mark.parametrize('stdin, expected', FAILING_PARAMS_LIST, indirect=['stdin'])
    def test_fail_validate_options_list(self, capfd, stdin, options_argspec_list, expected):
        """Fail because one of a required_together pair of parameters has a default and the other was not specified"""
        with pytest.raises(SystemExit):
            am = basic.AnsibleModule(**options_argspec_list)

        out, err = capfd.readouterr()
        results = json.loads(out)

        assert results['failed']
        assert expected in results['msg']

    @pytest.mark.parametrize('stdin', [{'foobar': {'foo': 'required', 'bam1': 'test', 'bar': 'case'}}], indirect=['stdin'])
    def test_fallback_in_option(self, mocker, stdin, options_argspec_dict):
        """Test that the complex argspec works if we get a required parameter via fallback"""
        environ = os.environ.copy()
        environ['BAZ'] = 'test data'
        mocker.patch('ansible.module_utils.basic.os.environ', environ)

        am = basic.AnsibleModule(**options_argspec_dict)

        assert isinstance(am.params['foobar']['baz'], str)
        assert am.params['foobar']['baz'] == 'test data'

    @pytest.mark.parametrize('stdin',
                             [{'foobar': {'foo': 'required', 'bam1': 'test', 'baz': 'data', 'bar': 'case', 'bar4': '~/test'}}],
                             indirect=['stdin'])
    def test_elements_path_in_option(self, mocker, stdin, options_argspec_dict):
        """Test that the complex argspec works with elements path type"""

        am = basic.AnsibleModule(**options_argspec_dict)

        assert isinstance(am.params['foobar']['bar4'][0], str)
        assert am.params['foobar']['bar4'][0].startswith('/')

    @pytest.mark.parametrize('stdin,spec,expected', [
        ({},
         {'one': {'type': 'dict', 'apply_defaults': True, 'options': {'two': {'default': True, 'type': 'bool'}}}},
         {'two': True}),
        ({},
         {'one': {'type': 'dict', 'options': {'two': {'default': True, 'type': 'bool'}}}},
         None),
    ], indirect=['stdin'])
    def test_subspec_not_required_defaults(self, stdin, spec, expected):
        # Check that top level not required, processed subspec defaults
        am = basic.AnsibleModule(spec)
        assert am.params['one'] == expected


class TestLoadFileCommonArguments:
    @pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
    def test_smoketest_load_file_common_args(self, am):
        """With no file arguments, an empty dict is returned"""
        am.selinux_mls_enabled = MagicMock()
        am.selinux_mls_enabled.return_value = True
        am.selinux_default_context = MagicMock()
        am.selinux_default_context.return_value = 'unconfined_u:object_r:default_t:s0'.split(':', 3)

        assert am.load_file_common_arguments(params={}) == {}

    @pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
    def test_load_file_common_args(self, am, mocker):
        am.selinux_mls_enabled = MagicMock()
        am.selinux_mls_enabled.return_value = True
        am.selinux_default_context = MagicMock()
        am.selinux_default_context.return_value = 'unconfined_u:object_r:default_t:s0'.split(':', 3)

        base_params = dict(
            path='/path/to/file',
            mode=0o600,
            owner='root',
            group='root',
            seuser='_default',
            serole='_default',
            setype='_default',
            selevel='_default',
        )

        extended_params = base_params.copy()
        extended_params.update(dict(
            follow=True,
            foo='bar',
        ))

        final_params = base_params.copy()
        final_params.update(dict(
            path='/path/to/real_file',
            secontext=['unconfined_u', 'object_r', 'default_t', 's0'],
            attributes=None,
        ))

        # with the proper params specified, the returned dictionary should represent
        # only those params which have something to do with the file arguments, excluding
        # other params and updated as required with proper values which may have been
        # massaged by the method
        mocker.patch('os.path.islink', return_value=True)
        mocker.patch('os.path.realpath', return_value='/path/to/real_file')

        res = am.load_file_common_arguments(params=extended_params)

        assert res == final_params


@pytest.mark.parametrize("stdin", [{"arg_pass": "testing"}], indirect=["stdin"])
def test_no_log_true(stdin, capfd):
    """Explicitly mask an argument (no_log=True)."""
    arg_spec = {
        "arg_pass": {"no_log": True}
    }
    am = basic.AnsibleModule(arg_spec)
    # no_log=True is picked up by both am._log_invocation and list_no_log_values
    # (called by am._handle_no_log_values). As a result, we can check for the
    # value in am.no_log_values.
    assert "testing" in am.no_log_values


@pytest.mark.parametrize("stdin", [{"arg_pass": "testing"}], indirect=["stdin"])
def test_no_log_false(stdin, capfd):
    """Explicitly log and display an argument (no_log=False)."""
    arg_spec = {
        "arg_pass": {"no_log": False}
    }
    am = basic.AnsibleModule(arg_spec)
    assert "testing" not in am.no_log_values and not am._warnings


@pytest.mark.parametrize("stdin", [{"arg_pass": "testing"}], indirect=["stdin"])
def test_no_log_none(stdin, capfd):
    """Allow Ansible to make the decision by matching the argument name
    against PASSWORD_MATCH."""
    arg_spec = {
        "arg_pass": {}
    }
    am = basic.AnsibleModule(arg_spec)
    # Omitting no_log is only picked up by _log_invocation, so the value never
    # makes it into am.no_log_values. Instead we can check for the warning
    # emitted by am._log_invocation.
    assert len(am._warnings) > 0
