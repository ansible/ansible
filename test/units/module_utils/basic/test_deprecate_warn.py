# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import json

import pytest

from ansible.module_utils.serialization import get_module_decoder, Direction
from ansible.module_utils.common.messages import Detail, DeprecationSummary, WarningSummary

pytestmark = pytest.mark.usefixtures("module_env_mocker")


@pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
def test_warn(am, capfd):

    am.warn('warning1')

    with pytest.raises(SystemExit):
        am.exit_json(warnings=['warning2'])
    out, err = capfd.readouterr()
    actual = json.loads(out, cls=get_module_decoder('legacy', Direction.MODULE_TO_CONTROLLER))['warnings']
    expected = [WarningSummary._from_details(Detail(msg=msg)) for msg in ['warning1', 'warning2']]
    assert actual == expected


@pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
def test_deprecate(am, capfd):
    am.deprecate('deprecation1')  # pylint: disable=ansible-deprecated-no-version
    am.deprecate('deprecation2', '2.3')  # pylint: disable=ansible-deprecated-version
    am.deprecate('deprecation3', version='2.4')  # pylint: disable=ansible-deprecated-version
    am.deprecate('deprecation4', date='2020-03-10')
    am.deprecate('deprecation5', collection_name='ansible.builtin')  # pylint: disable=ansible-deprecated-no-version
    am.deprecate('deprecation6', '2.3', collection_name='ansible.builtin')  # pylint: disable=ansible-deprecated-version
    am.deprecate('deprecation7', version='2.4', collection_name='ansible.builtin')  # pylint: disable=ansible-deprecated-version
    am.deprecate('deprecation8', date='2020-03-10', collection_name='ansible.builtin')

    with pytest.raises(SystemExit):
        am.exit_json(deprecations=['deprecation9', ('deprecation10', '2.4')])

    out, err = capfd.readouterr()
    output = json.loads(out, cls=get_module_decoder('legacy', Direction.MODULE_TO_CONTROLLER))
    assert ('warnings' not in output or output['warnings'] == [])
    assert output['deprecations'] == [
        DeprecationSummary._from_details(Detail(msg='deprecation1'), version=None, collection_name=None),
        DeprecationSummary._from_details(Detail(msg='deprecation2'), version='2.3', collection_name=None),
        DeprecationSummary._from_details(Detail(msg='deprecation3'), version='2.4', collection_name=None),
        DeprecationSummary._from_details(Detail(msg='deprecation4'), date='2020-03-10', collection_name=None),
        DeprecationSummary._from_details(Detail(msg='deprecation5'), version=None, collection_name='ansible.builtin'),
        DeprecationSummary._from_details(Detail(msg='deprecation6'), version='2.3', collection_name='ansible.builtin'),
        DeprecationSummary._from_details(Detail(msg='deprecation7'), version='2.4', collection_name='ansible.builtin'),
        DeprecationSummary._from_details(Detail(msg='deprecation8'), date='2020-03-10', collection_name='ansible.builtin'),
        DeprecationSummary._from_details(Detail(msg='deprecation9'), version=None, collection_name=None),
        DeprecationSummary._from_details(Detail(msg='deprecation10'), version='2.4', collection_name=None),
    ]


@pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
def test_deprecate_without_list(am, capfd):
    with pytest.raises(SystemExit):
        am.exit_json(deprecations='Simple deprecation warning')

    out, err = capfd.readouterr()
    output = json.loads(out, cls=get_module_decoder('legacy', Direction.MODULE_TO_CONTROLLER))
    assert ('warnings' not in output or output['warnings'] == [])
    assert output['deprecations'] == [
        DeprecationSummary._from_details(Detail(msg='Simple deprecation warning'), version=None, collection_name=None),
    ]


@pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
def test_deprecate_without_list_version_date_not_set(am, capfd):
    with pytest.raises(AssertionError) as ctx:
        am.deprecate('Simple deprecation warning', date='', version='')  # pylint: disable=ansible-deprecated-no-version
    assert ctx.value.args[0] == "implementation error -- version and date must not both be set"
