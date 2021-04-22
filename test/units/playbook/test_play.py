# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.errors import AnsibleAssertionError, AnsibleParserError
from ansible.playbook.block import Block
from ansible.playbook.play import Play

from units.mock.loader import DictDataLoader


def test_empty_play():
    p = Play.load({})

    assert str(p) == ''


def test_play_with_hosts_string():
    p = Play.load({'hosts': 'foo'})

    assert str(p) == 'foo'

    # Test the caching since self.name should be set by previous call.
    assert p.get_name() == 'foo'


def test_basic_play():
    p = Play.load(dict(
        name="test play",
        hosts=['foo'],
        gather_facts=False,
        connection='local',
        remote_user="root",
        become=True,
        become_user="testing",
    ))

    assert p.name == 'test play'
    assert p.hosts == ['foo']
    assert p.connection == 'local'


def test_play_with_remote_user():
    p = Play.load(dict(
        name="test play",
        hosts=['foo'],
        user="testing",
        gather_facts=False,
    ))

    assert p.remote_user == "testing"


def test_play_with_user_conflict():
    play_data = dict(
        name="test play",
        hosts=['foo'],
        user="testing",
        remote_user="testing",
    )

    with pytest.raises(AnsibleParserError):
        Play.load(play_data)


def test_play_with_bad_ds_type():
    play_data = []
    with pytest.raises(AnsibleAssertionError, match=r"while preprocessing data \(\[\]\), ds should be a dict but was a <(?:class|type) 'list'>"):
        Play.load(play_data)


def test_play_with_tasks():
    p = Play.load(dict(
        name="test play",
        hosts=['foo'],
        gather_facts=False,
        tasks=[dict(action='shell echo "hello world"')],
    ))

    assert len(p.tasks) == 1
    assert isinstance(p.tasks[0], Block)
    assert p.tasks[0].has_tasks() is True


def test_play_with_handlers():
    p = Play.load(dict(
        name="test play",
        hosts=['foo'],
        gather_facts=False,
        handlers=[dict(action='shell echo "hello world"')],
    ))

    assert len(p.handlers) >= 1
    assert isinstance(p.handlers[0], Block)
    assert p.handlers[0].has_tasks() is True


def test_play_with_pre_tasks():
    p = Play.load(dict(
        name="test play",
        hosts=['foo'],
        gather_facts=False,
        pre_tasks=[dict(action='shell echo "hello world"')],
    ))

    assert len(p.pre_tasks) >= 1
    assert isinstance(p.pre_tasks[0], Block)
    assert p.pre_tasks[0].has_tasks() is True


def test_play_with_post_tasks():
    p = Play.load(dict(
        name="test play",
        hosts=['foo'],
        gather_facts=False,
        post_tasks=[dict(action='shell echo "hello world"')],
    ))

    assert len(p.post_tasks) >= 1
    assert isinstance(p.post_tasks[0], Block)
    assert p.post_tasks[0].has_tasks() is True


def test_play_with_roles(mocker):
    mocker.patch('ansible.playbook.role.definition.RoleDefinition._load_role_path', return_value=('foo', '/etc/ansible/roles/foo'))
    fake_loader = DictDataLoader({
        '/etc/ansible/roles/foo/tasks.yml': """
        - name: role task
          shell: echo "hello world"
        """,
    })

    mock_var_manager = mocker.MagicMock()
    mock_var_manager.get_vars.return_value = {}

    p = Play.load(dict(
        name="test play",
        hosts=['foo'],
        gather_facts=False,
        roles=['foo'],
    ), loader=fake_loader, variable_manager=mock_var_manager)

    blocks = p.compile()
    assert len(blocks) > 1
    assert all(isinstance(block, Block) for block in blocks)


def test_play_compile():
    p = Play.load(dict(
        name="test play",
        hosts=['foo'],
        gather_facts=False,
        tasks=[dict(action='shell echo "hello world"')],
    ))

    blocks = p.compile()

    # with a single block, there will still be three
    # implicit meta flush_handler blocks inserted
    assert len(blocks) == 4


@pytest.mark.parametrize('value', ([], tuple(), set(), {}, ''))
def test_play_empty_hosts(value):
    with pytest.raises(AnsibleParserError) as exc:
        Play.load({'hosts': value})

    assert 'Hosts list cannot be empty' in exc.value.message


@pytest.mark.parametrize('value', ([None], (None,), ['one', None]))
def test_play_none_hosts(value):
    with pytest.raises(AnsibleParserError, match="Hosts list cannot contain values of 'None'"):
        Play.load({'hosts': value})


@pytest.mark.parametrize(
    'value',
    (
        {'one': None},
        {'one': 'two'},
    )
)
def test_play_invalid_hosts_sequence(value):
    with pytest.raises(AnsibleParserError, match='Hosts list must be a sequence'):
        Play.load({'hosts': value})


@pytest.mark.parametrize(
    'value',
    (
        [[1, 'two']],
        [{'one': None}],
        [set((None, 'one'))],
        ['one', 'two', {'three': None}],
        ['one', 'two', {'three': 'four'}],
    )
)
def test_play_invalid_hosts_value(value):
    with pytest.raises(AnsibleParserError, match='Hosts list contains an invalid host value'):
        Play.load({'hosts': value})
