# Copyright (c) 2026 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible._internal import _task
from ansible._internal._templating._engine import TemplateEngine
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.block import Block
from ansible.playbook.play import Play
from ansible.playbook.task import Task
from ansible.plugins.strategy import Debugger


def test_update_task_keeps_register_projection() -> None:
    loader = DataLoader()
    play = Play.load(dict(name='test', hosts='all', gather_facts='no', tasks=[]), loader=loader)
    block = Block(play=play)
    task = Task.load(dict(name='test task', ping={}, register='out'), block=block, loader=loader)
    task.post_validate(TemplateEngine())
    debugger = Debugger(task, 'localhost', {}, None, None, None)

    debugger.do_update_task('')

    register = debugger.scope['task'].register

    assert isinstance(register, dict)
    assert register == {'out': _task.POLYMORPHIC_RESULT_EXPRESSION}
