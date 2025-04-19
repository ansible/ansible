# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import json
import typing as t

import pytest

from ansible.module_utils._internal._ansiballz import _ModulePluginWrapper
from ansible.module_utils._internal._plugin_exec_context import PluginExecContext
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.json import Direction, get_module_decoder
from ansible.module_utils.common import warnings
from ansible.module_utils.common.messages import Detail, DeprecationSummary, WarningSummary, PluginInfo

from units.mock.messages import make_summary

pytestmark = pytest.mark.usefixtures("module_env_mocker")


@pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
def test_warn(am, capfd):

    am.warn('warning1')

    with pytest.raises(SystemExit):
        am.exit_json(warnings=['warning2'])
    out, err = capfd.readouterr()
    actual = json.loads(out, cls=get_module_decoder('legacy', Direction.MODULE_TO_CONTROLLER))['warnings']
    expected = [make_summary(WarningSummary, Detail(msg=msg)) for msg in ['warning1', 'warning2']]
    assert actual == expected


@pytest.mark.parametrize('kwargs,plugin_name,stdin', (
    (dict(msg='deprecation1'), None, {}),
    (dict(msg='deprecation3', version='2.4'), None, {}),
    (dict(msg='deprecation4', date='2020-03-10'), None, {}),
    (dict(msg='deprecation5'), 'ansible.builtin.ping', {}),
    (dict(msg='deprecation7', version='2.4'), 'ansible.builtin.ping', {}),
    (dict(msg='deprecation8', date='2020-03-10'), 'ansible.builtin.ping', {}),
), indirect=['stdin'])
def test_deprecate(am: AnsibleModule, capfd, kwargs: dict[str, t.Any], plugin_name: str | None) -> None:
    plugin_info = PluginInfo(requested_name=plugin_name, resolved_name=plugin_name, type='module') if plugin_name else None
    executing_plugin = _ModulePluginWrapper(plugin_info) if plugin_info else None
    collection_name = plugin_name.rpartition('.')[0] if plugin_name else None

    with PluginExecContext.when(bool(executing_plugin), executing_plugin=executing_plugin):
        am.deprecate(**kwargs)

        assert warnings.get_deprecation_messages() == (dict(collection_name=collection_name, **kwargs),)

        with pytest.raises(SystemExit):
            am.exit_json(deprecations=['deprecation9', ('deprecation10', '2.4')])

    out, err = capfd.readouterr()

    output = json.loads(out, cls=get_module_decoder('legacy', Direction.MODULE_TO_CONTROLLER))

    assert ('warnings' not in output or output['warnings'] == [])

    msg = kwargs.pop('msg')

    assert output['deprecations'] == [
        make_summary(DeprecationSummary, Detail(msg=msg), **kwargs, plugin=plugin_info),
        make_summary(DeprecationSummary, Detail(msg='deprecation9'), plugin=plugin_info),
        make_summary(DeprecationSummary, Detail(msg='deprecation10'), version='2.4', plugin=plugin_info),
    ]


@pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
def test_deprecate_without_list(am, capfd):
    with pytest.raises(SystemExit):
        am.exit_json(deprecations='Simple deprecation warning')

    out, err = capfd.readouterr()
    output = json.loads(out, cls=get_module_decoder('legacy', Direction.MODULE_TO_CONTROLLER))
    assert ('warnings' not in output or output['warnings'] == [])
    assert output['deprecations'] == [
        make_summary(DeprecationSummary, Detail(msg='Simple deprecation warning')),
    ]


@pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
def test_deprecate_without_list_version_date_not_set(am, capfd):
    with pytest.raises(AssertionError) as ctx:
        am.deprecate('Simple deprecation warning', date='', version='')  # pylint: disable=ansible-deprecated-no-version
    assert ctx.value.args[0] == "implementation error -- version and date must not both be set"
