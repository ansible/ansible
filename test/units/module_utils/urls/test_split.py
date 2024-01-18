# -*- coding: utf-8 -*-
# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils.urls import _split_multiext


@pytest.mark.parametrize(
    'name, expected',
    (
        ('', ('', '')),
        ('a', ('a', '')),
        ('file.tar', ('file', '.tar')),
        ('file.tar.', ('file.tar.', '')),
        ('file.hidden', ('file.hidden', '')),
        ('file.tar.gz', ('file', '.tar.gz')),
        ('yaml-0.2.5.tar.gz', ('yaml-0.2.5', '.tar.gz')),
        ('yaml-0.2.5.zip', ('yaml-0.2.5', '.zip')),
        ('yaml-0.2.5.zip.hidden', ('yaml-0.2.5.zip.hidden', '')),
        ('geckodriver-v0.26.0-linux64.tar', ('geckodriver-v0.26.0-linux64', '.tar')),
        ('/var/lib/geckodriver-v0.26.0-linux64.tar', ('/var/lib/geckodriver-v0.26.0-linux64', '.tar')),
        ('https://acme.com/drivers/geckodriver-v0.26.0-linux64.tar', ('https://acme.com/drivers/geckodriver-v0.26.0-linux64', '.tar')),
        ('https://acme.com/drivers/geckodriver-v0.26.0-linux64.tar.bz', ('https://acme.com/drivers/geckodriver-v0.26.0-linux64', '.tar.bz')),
    )
)
def test__split_multiext(name, expected):
    assert expected == _split_multiext(name)


@pytest.mark.parametrize(
    'args, expected',
    (
        (('base-v0.26.0-linux64.tar.gz', 4, 4), ('base-v0.26.0-linux64.tar.gz', '')),
        (('base-v0.26.0.hidden', 1, 7), ('base-v0.26', '.0.hidden')),
        (('base-v0.26.0.hidden', 3, 4), ('base-v0.26.0.hidden', '')),
        (('base-v0.26.0.hidden.tar', 1, 7), ('base-v0.26.0', '.hidden.tar')),
        (('base-v0.26.0.hidden.tar.gz', 1, 7), ('base-v0.26.0.hidden', '.tar.gz')),
        (('base-v0.26.0.hidden.tar.gz', 4, 7), ('base-v0.26.0.hidden.tar.gz', '')),
    )
)
def test__split_multiext_min_max(args, expected):
    assert expected == _split_multiext(*args)


@pytest.mark.parametrize(
    'kwargs, expected', (
        (({'name': 'base-v0.25.0.tar.gz', 'count': 1}), ('base-v0.25.0.tar', '.gz')),
        (({'name': 'base-v0.25.0.tar.gz', 'count': 2}), ('base-v0.25.0', '.tar.gz')),
        (({'name': 'base-v0.25.0.tar.gz', 'count': 3}), ('base-v0.25.0', '.tar.gz')),
        (({'name': 'base-v0.25.0.tar.gz', 'count': 4}), ('base-v0.25.0', '.tar.gz')),
        (({'name': 'base-v0.25.foo.tar.gz', 'count': 3}), ('base-v0.25', '.foo.tar.gz')),
        (({'name': 'base-v0.25.foo.tar.gz', 'count': 4}), ('base-v0', '.25.foo.tar.gz')),
    )
)
def test__split_multiext_count(kwargs, expected):
    assert expected == _split_multiext(**kwargs)


@pytest.mark.parametrize(
    'name',
    (
        list(),
        tuple(),
        dict(),
        set(),
        1.729879,
        247,
    )
)
def test__split_multiext_invalid(name):
    with pytest.raises((TypeError, AttributeError)):
        _split_multiext(name)
