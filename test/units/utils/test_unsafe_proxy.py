# -*- coding: utf-8 -*-
# (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.six import PY3
from ansible.utils.unsafe_proxy import AnsibleUnsafe, AnsibleUnsafeText, UnsafeProxy, wrap_var


def test_UnsafeProxy():
    assert isinstance(UnsafeProxy({}), dict)
    assert not isinstance(UnsafeProxy({}), AnsibleUnsafe)

    assert isinstance(UnsafeProxy('foo'), AnsibleUnsafeText)


def test_wrap_var_string():
    assert isinstance(wrap_var('foo'), AnsibleUnsafeText)
    assert isinstance(wrap_var(u'foo'), AnsibleUnsafeText)
    if PY3:
        assert isinstance(wrap_var(b'foo'), type(b''))
        assert not isinstance(wrap_var(b'foo'), AnsibleUnsafe)
    else:
        assert isinstance(wrap_var(b'foo'), AnsibleUnsafeText)


def test_wrap_var_dict():
    assert isinstance(wrap_var(dict(foo='bar')), dict)
    assert not isinstance(wrap_var(dict(foo='bar')), AnsibleUnsafe)
    assert isinstance(wrap_var(dict(foo='bar'))['foo'], AnsibleUnsafeText)


def test_wrap_var_dict_None():
    assert wrap_var(dict(foo=None))['foo'] is None
    assert not isinstance(wrap_var(dict(foo=None))['foo'], AnsibleUnsafe)


def test_wrap_var_list():
    assert isinstance(wrap_var(['foo']), list)
    assert not isinstance(wrap_var(['foo']), AnsibleUnsafe)
    assert isinstance(wrap_var(['foo'])[0], AnsibleUnsafeText)


def test_wrap_var_list_None():
    assert wrap_var([None])[0] is None
    assert not isinstance(wrap_var([None])[0], AnsibleUnsafe)


def test_wrap_var_set():
    assert isinstance(wrap_var(set(['foo'])), set)
    assert not isinstance(wrap_var(set(['foo'])), AnsibleUnsafe)
    for item in wrap_var(set(['foo'])):
        assert isinstance(item, AnsibleUnsafeText)


def test_wrap_var_set_None():
    for item in wrap_var(set([None])):
        assert item is None
        assert not isinstance(item, AnsibleUnsafe)


def test_wrap_var_tuple():
    assert isinstance(wrap_var(('foo',)), tuple)
    assert not isinstance(wrap_var(('foo',)), AnsibleUnsafe)
    assert isinstance(wrap_var(('foo',))[0], type(''))
    assert not isinstance(wrap_var(('foo',))[0], AnsibleUnsafe)


def test_wrap_var_None():
    assert wrap_var(None) is None
    assert not isinstance(wrap_var(None), AnsibleUnsafe)


def test_wrap_var_unsafe():
    assert isinstance(wrap_var(AnsibleUnsafeText(u'foo')), AnsibleUnsafeText)


def test_AnsibleUnsafeText():
    assert isinstance(AnsibleUnsafeText(u'foo'), AnsibleUnsafe)
