# -*- coding: utf-8 -*-
# (c) 2020 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
from yaml import MappingNode, Mark, ScalarNode
from yaml.constructor import ConstructorError

import ansible.constants as C
from ansible.utils.display import Display
from ansible.parsing.yaml.constructor import AnsibleConstructor


@pytest.fixture
def dupe_node():
    tag = 'tag:yaml.org,2002:map'
    scalar_tag = 'tag:yaml.org,2002:str'
    mark = Mark(tag, 0, 0, 0, None, None)
    node = MappingNode(
        tag,
        [
            (
                ScalarNode(tag=scalar_tag, value='bar', start_mark=mark),
                ScalarNode(tag=scalar_tag, value='baz', start_mark=mark)
            ),
            (
                ScalarNode(tag=scalar_tag, value='bar', start_mark=mark),
                ScalarNode(tag=scalar_tag, value='qux', start_mark=mark)
            ),
        ],
        start_mark=mark
    )

    return node


class Capture:
    def __init__(self):
        self.called = False
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.called = True
        self.calls.append((
            args,
            kwargs
        ))


def test_duplicate_yaml_dict_key_ignore(dupe_node, monkeypatch):
    monkeypatch.setattr(C, 'DUPLICATE_YAML_DICT_KEY', 'ignore')
    cap = Capture()
    monkeypatch.setattr(Display(), 'warning', cap)
    ac = AnsibleConstructor()
    ac.construct_mapping(dupe_node)
    assert not cap.called


def test_duplicate_yaml_dict_key_warn(dupe_node, monkeypatch):
    monkeypatch.setattr(C, 'DUPLICATE_YAML_DICT_KEY', 'warn')
    cap = Capture()
    monkeypatch.setattr(Display(), 'warning', cap)
    ac = AnsibleConstructor()
    ac.construct_mapping(dupe_node)
    assert cap.called
    expected = [
        (
            (
                'While constructing a mapping from tag:yaml.org,2002:map, line 1, column 1, '
                'found a duplicate dict key (bar). Using last defined value only.',
            ),
            {}
        )
    ]
    assert cap.calls == expected


def test_duplicate_yaml_dict_key_error(dupe_node, monkeypatch, mocker):
    monkeypatch.setattr(C, 'DUPLICATE_YAML_DICT_KEY', 'error')
    ac = AnsibleConstructor()
    pytest.raises(ConstructorError, ac.construct_mapping, dupe_node)
