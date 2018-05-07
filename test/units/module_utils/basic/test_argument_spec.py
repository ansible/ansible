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

from ansible.compat.tests.mock import MagicMock, patch
from ansible.module_utils import basic
from ansible.module_utils.six import string_types
from ansible.module_utils.six.moves import builtins

from units.mock.procenv import ModuleTestCase, swap_stdin_and_argv


MOCK_VALIDATOR_FAIL = MagicMock(side_effect=TypeError("bad conversion"))
# Data is argspec, argument, expected
VALID_SPECS = (
    # Simple type=int
    ({'arg': {'type': 'int'}}, {'arg': 42}, 42),
    # Type=int with conversion from string
    ({'arg': {'type': 'int'}}, {'arg': '42'}, 42),
    # Simple type=float
    ({'arg': {'type': 'float'}}, {'arg': 42.0}, 42.0),
    # Type=float conversion from int
    ({'arg': {'type': 'float'}}, {'arg': 42}, 42.0),
    # Type=float conversion from string
    ({'arg': {'type': 'float'}}, {'arg': '42.0'}, 42.0),
    # Type=float conversion from string without decimal point
    ({'arg': {'type': 'float'}}, {'arg': '42'}, 42.0),
    # Simple type=bool
    ({'arg': {'type': 'bool'}}, {'arg': True}, True),
    # Type=int with conversion from string
    ({'arg': {'type': 'bool'}}, {'arg': 'yes'}, True),
    # Type=str converts to string
    ({'arg': {'type': 'str'}}, {'arg': 42}, '42'),
    # Type is implicit, converts to string
    ({'arg': {'type': 'str'}}, {'arg': 42}, '42'),
    # parameter is required
    ({'arg': {'required': True}}, {'arg': 42}, '42'),
)

INVALID_SPECS = (
    # Type is int; unable to convert this string
    ({'arg': {'type': 'int'}}, {'arg': "bad"}, "invalid literal for int() with base 10: 'bad'"),
    # Type is int; unable to convert float
    ({'arg': {'type': 'int'}}, {'arg': 42.1}, "'float'> cannot be converted to an int"),
    # type is a callable that fails to convert
    ({'arg': {'type': MOCK_VALIDATOR_FAIL}}, {'arg': "bad"}, "bad conversion"),
    # unknown parameter
    ({'arg': {'type': 'int'}}, {'other': 'bad', '_ansible_module_name': 'ansible_unittest'},
     'Unsupported parameters for (ansible_unittest) module: other Supported parameters include: arg'),
    # parameter is required
    ({'arg': {'required': True}}, {}, 'missing required arguments: arg'),
)


@pytest.fixture
def complex_argspec():
    arg_spec = dict(
        foo=dict(required=True, aliases=['dup']),
        bar=dict(),
        bam=dict(),
        baz=dict(fallback=(basic.env_fallback, ['BAZ'])),
        bar1=dict(type='bool'),
        zardoz=dict(choices=['one', 'two']),
        zardoz2=dict(type='list', choices=['one', 'two', 'three']),
    )
    mut_ex = (('bar', 'bam'),)
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
        bam=dict(),
        baz=dict(fallback=(basic.env_fallback, ['BAZ'])),
        bam1=dict(),
        bam2=dict(default='test'),
        bam3=dict(type='bool'),
    )

    arg_spec = dict(
        foobar=dict(
            type='list',
            elements='dict',
            options=options_spec,
            mutually_exclusive=[
                ['bam', 'bam1']
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
            ]
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
def options_argspec_dict():
    # should test ok, for options in dict format.
    kwargs = options_argspec_list()
    kwargs['argument_spec']['foobar']['type'] = 'dict'

    return kwargs


#
# Tests for one aspect of arg_spec
#

@pytest.mark.parametrize('argspec, expected, stdin', [(s[0], s[2], s[1]) for s in VALID_SPECS],
                         indirect=['stdin'])
def test_validator_basic_types(argspec, expected, stdin):

    am = basic.AnsibleModule(argspec)

    if 'type' in argspec['arg']:
        type_ = getattr(builtins, argspec['arg']['type'])
    else:
        type_ = str

    assert isinstance(am.params['arg'], type_)
    assert am.params['arg'] == expected


@pytest.mark.parametrize('stdin', [{'arg': 42}], indirect=['stdin'])
def test_validator_function(mocker, stdin):
    # Type is a callable
    MOCK_VALIDATOR_SUCCESS = mocker.MagicMock(return_value=27)
    argspec = {'arg': {'type': MOCK_VALIDATOR_SUCCESS}}
    am = basic.AnsibleModule(argspec)

    assert isinstance(am.params['arg'], int)
    assert am.params['arg'] == 27


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

    @pytest.mark.parametrize('stdin', [{'foo': 'hello', 'bam': 'test'}], indirect=['stdin'])
    def test_complex_type_fallback(self, mocker, stdin, complex_argspec):
        """Test that the complex argspec works if we get a required parameter via fallback"""
        environ = os.environ.copy()
        environ['BAZ'] = 'test data'
        mocker.patch('ansible.module_utils.basic.os.environ', environ)

        am = basic.AnsibleModule(**complex_argspec)

        assert isinstance(am.params['baz'], str)
        assert am.params['baz'] == 'test data'

    @pytest.mark.parametrize('stdin', [{'foo': 'hello', 'bar': 'bad', 'bam': 'bad2'}], indirect=['stdin'])
    def test_fail_mutually_exclusive(self, capfd, stdin, complex_argspec):
        """Fail because of mutually exclusive parameters"""
        with pytest.raises(SystemExit):
            am = basic.AnsibleModule(**complex_argspec)

        out, err = capfd.readouterr()
        results = json.loads(out)

        assert results['failed']
        assert results['msg'] == "parameters are mutually exclusive: bar, bam"

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


class TestComplexOptions:
    """Test arg spec options"""

    # (Paramaters, expected value of module.params['foobar'])
    OPTIONS_PARAMS_LIST = (
        ({'foobar': [{"foo": "hello", "bam": "good"}, {"foo": "test", "bar": "good"}]},
         [{'foo': 'hello', 'bam': 'good', 'bam2': 'test', 'bar': None, 'baz': None, 'bam1': None, 'bam3': None},
          {'foo': 'test', 'bam': None, 'bam2': 'test', 'bar': 'good', 'baz': None, 'bam1': None, 'bam3': None},
          ]),
        # Alias for required param
        ({'foobar': [{"dup": "test", "bar": "good"}]},
         [{'foo': 'test', 'dup': 'test', 'bam': None, 'bam2': 'test', 'bar': 'good', 'baz': None, 'bam1': None, 'bam3': None}]
         ),
        # Required_if utilizing default value of the requirement
        ({'foobar': [{"foo": "bam2", "bar": "required_one_of"}]},
         [{'bam': None, 'bam1': None, 'bam2': 'test', 'bam3': None, 'bar': 'required_one_of', 'baz': None, 'foo': 'bam2'}]
         ),
        # Check that a bool option is converted
        ({"foobar": [{"foo": "required", "bam": "good", "bam3": "yes"}]},
         [{'bam': 'good', 'bam1': None, 'bam2': 'test', 'bam3': True, 'bar': None, 'baz': None, 'foo': 'required'}]
         ),
    )

    # (Paramaters, expected value of module.params['foobar'])
    OPTIONS_PARAMS_DICT = (
        ({'foobar': {"foo": "hello", "bam": "good"}},
         {'foo': 'hello', 'bam': 'good', 'bam2': 'test', 'bar': None, 'baz': None, 'bam1': None, 'bam3': None}
         ),
        # Alias for required param
        ({'foobar': {"dup": "test", "bar": "good"}},
         {'foo': 'test', 'dup': 'test', 'bam': None, 'bam2': 'test', 'bar': 'good', 'baz': None, 'bam1': None, 'bam3': None}
         ),
        # Required_if utilizing default value of the requirement
        ({'foobar': {"foo": "bam2", "bar": "required_one_of"}},
         {'bam': None, 'bam1': None, 'bam2': 'test', 'bam3': None, 'bar': 'required_one_of', 'baz': None, 'foo': 'bam2'}
         ),
        # Check that a bool option is converted
        ({"foobar": {"foo": "required", "bam": "good", "bam3": "yes"}},
         {'bam': 'good', 'bam1': None, 'bam2': 'test', 'bam3': True, 'bar': None, 'baz': None, 'foo': 'required'}
         ),
    )

    # (Paramaters, failure message)
    FAILING_PARAMS_LIST = (
        # Missing required option
        ({'foobar': [{}]}, 'missing required arguments: foo found in foobar'),
        # Invalid option
        ({'foobar': [{"foo": "hello", "bam": "good", "invalid": "bad"}]}, 'module: invalid found in foobar. Supported parameters include'),
        # Mutually exclusive options found
        ({'foobar': [{"foo": "test", "bam": "bad", "bam1": "bad", "baz": "req_to"}]},
         'parameters are mutually exclusive: bam, bam1 found in foobar'),
        # required_if fails
        ({'foobar': [{"foo": "hello", "bar": "bad"}]},
         'foo is hello but all of the following are missing: bam found in foobar'),
        # Missing required_one_of option
        ({'foobar': [{"foo": "test"}]},
         'one of the following is required: bar, bam found in foobar'),
        # Missing required_together option
        ({'foobar': [{"foo": "test", "bar": "required_one_of", "bam1": "bad"}]},
         'parameters are required together: bam1, baz found in foobar'),
    )

    # (Paramaters, failure message)
    FAILING_PARAMS_DICT = (
        # Missing required option
        ({'foobar': {}}, 'missing required arguments: foo found in foobar'),
        # Invalid option
        ({'foobar': {"foo": "hello", "bam": "good", "invalid": "bad"}},
         'module: invalid found in foobar. Supported parameters include'),
        # Mutually exclusive options found
        ({'foobar': {"foo": "test", "bam": "bad", "bam1": "bad", "baz": "req_to"}},
         'parameters are mutually exclusive: bam, bam1 found in foobar'),
        # required_if fails
        ({'foobar': {"foo": "hello", "bar": "bad"}},
         'foo is hello but all of the following are missing: bam found in foobar'),
        # Missing required_one_of option
        ({'foobar': {"foo": "test"}},
         'one of the following is required: bar, bam found in foobar'),
        # Missing required_together option
        ({'foobar': {"foo": "test", "bar": "required_one_of", "bam1": "bad"}},
         'parameters are required together: bam1, baz found in foobar'),
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
