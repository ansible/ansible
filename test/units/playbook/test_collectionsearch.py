# (c) 2020 Ansible Project
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

from __future__ import annotations

from ansible.errors import AnsibleParserError
from ansible.playbook.play import Play
from ansible.playbook.task import Task
from ansible.playbook.block import Block

import pytest


def test_collection_static_warning(capsys):
    """Test that collection name is not templated.

    Also, make sure that users see the warning message for the referenced name.
    """
    collection_name = "foo.{{bar}}"
    p = Play.load(dict(
        name="test play",
        hosts=['foo'],
        gather_facts=False,
        connection='local',
        collections=collection_name,
    ))
    assert collection_name in p.collections
    std_out, std_err = capsys.readouterr()
    assert '[WARNING]: "collections" is not templatable, but we found: %s' % collection_name in std_err
    assert '' == std_out


def test_collection_invalid_data_play():
    """Test that collection as a dict at the play level fails with parser error"""
    collection_name = {'name': 'foo'}
    with pytest.raises(AnsibleParserError):
        Play.load(dict(
            name="test play",
            hosts=['foo'],
            gather_facts=False,
            connection='local',
            collections=collection_name,
        ))


def test_collection_invalid_data_task():
    """Test that collection as a dict at the task level fails with parser error"""
    collection_name = {'name': 'foo'}
    with pytest.raises(AnsibleParserError):
        Task.load(dict(
            name="test task",
            collections=collection_name,
        ))


def test_collection_invalid_data_block():
    """Test that collection as a dict at the block level fails with parser error"""
    collection_name = {'name': 'foo'}
    with pytest.raises(AnsibleParserError):
        Block.load(dict(
            block=[dict(name="test task", collections=collection_name)]
        ))
