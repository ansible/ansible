# -*- coding: utf-8 -*-
# (c) 2018, Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import logging

import pytest

from ansible.compat.tests.mock import MagicMock
from ansible.errors import AnsibleError
from ansible.plugins.action.validate_arg_spec import ActionModule
from ansible.playbook.task import Task


log = logging.getLogger(__name__)


def test_validate_arg_spec_no_args():
    task = MagicMock(Task)
    task.args = {}
    task.async_val = False

    connection = MagicMock()

    play_context = MagicMock()
    play_context.check_mode = False

    plugin = ActionModule(task, connection, play_context, loader=None,
                          templar=None, shared_loader_obj=None)

    with pytest.raises(AnsibleError, match='"argument_spec" arg is required in args:.*'):
        plugin.run()


def test_validate_arg_spec_no_argument_spec():
    task = MagicMock(Task)
    task.args = {'argument_spec': {'argument_spec': {}}}
    task.async_val = False

    connection = MagicMock()

    play_context = MagicMock()
    play_context.check_mode = False

    plugin = ActionModule(task, connection, play_context, loader=None,
                          templar=None, shared_loader_obj=None)

    res = plugin.run(task_vars={})
    log.debug('res: %s', res)

    #  {'validate_args_context': {},
    #   'changed': False,
    #    'msg': 'The arg spec validation passed'}
    assert isinstance(res, dict)
    assert res['msg'] == 'The arg spec validation passed'
    assert res['validate_args_context'] == {}


def test_validate_arg_spec():
    task = MagicMock(Task)
    arg_spec = {'argument_spec': {'some_int': {'type': 'int',
                                               'required': True},
                                  'some_arg': None,
                                  'some_float': {'type': 'float'},
                                  'some_str': {'type': 'str'},
                                  'some_default_str': {'type': 'str',
                                                       'default': 'some_default_str_value'},
                                  'some_required_str': {'type': 'str',
                                                        'required': True},
                                  'some_list': {'type': 'list',
                                                'elements': 'list',
                                                'default': [],
                                                'aliases': ['some_array']},
                                  }
                }
    task.args = {'argument_spec': arg_spec,
                 'name': 'the_test_validate_arg_spec_unit_test',
                 'description': 'swampy with tannin undertones and a hint of despair'}
    task.async_val = False

    connection = MagicMock()

    play_context = MagicMock()
    play_context.check_mode = False

    templar = MagicMock()

    def faux_template(data):
        log.debug('ft data %s', data)
        return data
    templar.do_template = faux_template

    plugin = ActionModule(task, connection, play_context, loader=None,
                          templar=templar, shared_loader_obj=None)

    res = plugin.run(task_vars={'blip': True,
                                'some_arg': 'some_arg_value',
                                'some_str': 37.1,
                                'some_float': 'this_is_not_a_float',
                                # 'some_array': 37.2,
                                })
    log.debug('res: %s', res)

    # {'validate_args_context': {},
    # 'failed': True,
    # 'msg': 'Validation of arguments failed:\nmissing required arguments: some_int',
    # 'argument_spec_data': {'argument_spec': {'some_int': {'type': 'int',
    #                                                       'required': True}}},
    # 'argument_errors': ['missing required arguments: some_int']}

    assert isinstance(res, dict)
    assert res['failed']
    assert 'Validation of arguments failed' in res['msg']
    assert 'missing required arguments: some_int, some_required_str' in res['argument_errors'] or \
        'missing required arguments: some_required_str, some_int' in res['argument_errors']
    assert "argument some_float is of type <class 'str'> and we were unable to convert to float:"
    "could not convert string to float: 'this_is_not_a_float'" in res['argument_errors']
