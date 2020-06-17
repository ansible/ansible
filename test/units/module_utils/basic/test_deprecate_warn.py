# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json

import pytest


@pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
def test_warn(am, capfd):

    am.warn('warning1')

    with pytest.raises(SystemExit):
        am.exit_json(warnings=['warning2'])
    out, err = capfd.readouterr()
    assert json.loads(out)['warnings'] == ['warning1', 'warning2']


@pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
def test_deprecate(am, capfd):
    am.deprecate('deprecation1')
    am.deprecate('deprecation2', '2.3')
    am.deprecate('deprecation3', '2.5', collection_name='foo.bar')  # Ansible 2.10 compatibility
    am.deprecate('deprecation4', date='2020-01-01')  # Ansible 2.10 compatibility
    am.deprecate('deprecation5', date='2020-01-01', collection_name='foo.bar')  # Ansible 2.10 compatibility

    with pytest.raises(SystemExit):
        am.exit_json(deprecations=['deprecation6', ('deprecation7', '2.4')])

    out, err = capfd.readouterr()
    output = json.loads(out)
    assert ('warnings' not in output or output['warnings'] == [])
    assert output['deprecations'] == [
        {u'msg': u'deprecation1', u'version': None},
        {u'msg': u'deprecation2', u'version': '2.3'},
        {u'msg': u'deprecation3', u'version': '2.5'},
        {u'msg': u'deprecation4', u'version': None},
        {u'msg': u'deprecation5', u'version': None},
        {u'msg': u'deprecation6', u'version': None},
        {u'msg': u'deprecation7', u'version': '2.4'},
    ]


@pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
def test_deprecate_without_list(am, capfd):
    with pytest.raises(SystemExit):
        am.exit_json(deprecations='Simple deprecation warning')

    out, err = capfd.readouterr()
    output = json.loads(out)
    assert ('warnings' not in output or output['warnings'] == [])
    assert output['deprecations'] == [
        {u'msg': u'Simple deprecation warning', u'version': None},
    ]
