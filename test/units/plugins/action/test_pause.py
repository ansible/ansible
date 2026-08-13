# Copyright (c) 2026 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Tests for the pause action plugin."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ansible.errors import AnsibleActionFail, AnsibleError, AnsiblePromptInterrupt, AnsiblePromptNoninteractive
from ansible.playbook.task import Task
from ansible.plugins.action.pause import ActionModule as PauseAction


@pytest.fixture
def task_args(request):
    """Return playbook task args."""
    return getattr(request, 'param', {})


@pytest.fixture
def module_task(task_args):
    """Construct a task object for pause."""
    task = MagicMock(spec=Task)
    task.action = 'pause'
    task.args = task_args
    task.async_val = False
    task.check_mode = False
    task.diff = False
    task.get_name.return_value = 'pause'
    return task


@pytest.fixture
def play_context():
    """Construct a play context."""
    ctx = MagicMock()
    ctx.check_mode = False
    return ctx


@pytest.fixture
def action_plugin(play_context, module_task):
    """Initialize a pause action plugin with a fully mocked connection."""
    connection = MagicMock()
    return PauseAction(
        module_task,
        connection,
        play_context,
        loader=None,
        templar=None,
        shared_loader_obj=None,
    )


@pytest.mark.parametrize('task_args', [{'timeout_seconds': 30}], indirect=True)
def test_timeout_seconds_continue_on_expiry(mocker, action_plugin):
    """When timeout_seconds fires with no input, timed_out=True and user_input is empty (continue mode)."""
    mocker.patch('ansible.plugins.action.pause.display.display')
    mocker.patch('ansible.plugins.action.pause.display.prompt_until', return_value=b'')
    # Simulate elapsed time >= timeout_seconds so the empty return is treated as a real timeout,
    # not as the user pressing Enter immediately.
    # Call order in run(): (1) start=time.time(), (2) _prompt_start=time.time(),
    # (3) time.time()-_prompt_start [timeout check], (4) duration=time.time()-start.
    mocker.patch('ansible.plugins.action.pause.time.time', side_effect=[0.0, 0.0, 31.0, 32.0])

    result = action_plugin.run(task_vars={})

    assert result['timed_out'] is True
    assert result['user_input'] == ''
    assert 'failed' not in result or not result['failed']


@pytest.mark.parametrize('task_args', [{'timeout_seconds': 30}], indirect=True)
def test_timeout_seconds_user_responds_in_time(mocker, action_plugin):
    """When the user enters text before timeout_seconds, timed_out=False."""
    mocker.patch('ansible.plugins.action.pause.display.display')
    mocker.patch('ansible.plugins.action.pause.display.prompt_until', return_value=b'my answer')

    result = action_plugin.run(task_vars={})

    assert result['timed_out'] is False
    assert result['user_input'] == 'my answer'
    assert 'failed' not in result or not result['failed']


@pytest.mark.parametrize('task_args', [{'timeout_seconds': 30, 'timeout_action': 'abort'}], indirect=True)
def test_timeout_seconds_abort_on_expiry(mocker, action_plugin):
    """When timeout fires and timeout_action=abort, an AnsibleError is raised."""
    mocker.patch('ansible.plugins.action.pause.display.display')
    mocker.patch('ansible.plugins.action.pause.display.prompt_until', return_value=b'')
    # Simulate elapsed time >= timeout_seconds so the empty return is treated as a real timeout.
    # Call order in run(): (1) start=time.time(), (2) _prompt_start=time.time(),
    # (3) time.time()-_prompt_start [timeout check]. AnsibleError is raised before call (4).
    mocker.patch('ansible.plugins.action.pause.time.time', side_effect=[0.0, 0.0, 31.0])

    with pytest.raises(AnsibleError, match='Timed out waiting for user input'):
        action_plugin.run(task_vars={})


@pytest.mark.parametrize('task_args', [{'timeout_seconds': 30, 'timeout_action': 'abort'}], indirect=True)
def test_timeout_seconds_abort_not_triggered_when_input_given(mocker, action_plugin):
    """When the user answers before timeout, abort action is NOT triggered even when timeout_action=abort."""
    mocker.patch('ansible.plugins.action.pause.display.display')
    mocker.patch('ansible.plugins.action.pause.display.prompt_until', return_value=b'hello')

    result = action_plugin.run(task_vars={})

    assert result['timed_out'] is False
    assert result['user_input'] == 'hello'
    assert 'failed' not in result or not result['failed']


@pytest.mark.parametrize('task_args', [{'timeout_seconds': 0}], indirect=True)
def test_timeout_seconds_minimum_one(mocker, action_plugin):
    """timeout_seconds below 1 is clamped to 1."""
    mocker.patch('ansible.plugins.action.pause.display.display')
    prompt_mock = mocker.patch('ansible.plugins.action.pause.display.prompt_until', return_value=b'answer')

    action_plugin.run(task_vars={})

    # The call should have used seconds=1 (clamped), not 0
    call_kwargs = prompt_mock.call_args
    assert call_kwargs.kwargs['seconds'] == 1


@pytest.mark.parametrize('task_args', [{'timeout_seconds': 30}], indirect=True)
def test_timeout_seconds_noninteractive_warns(mocker, action_plugin):
    """In non-interactive mode, a warning is emitted and no error is raised."""
    mocker.patch('ansible.plugins.action.pause.display.display')
    warn_mock = mocker.patch('ansible.plugins.action.pause.display.warning')
    mocker.patch(
        'ansible.plugins.action.pause.display.prompt_until',
        side_effect=AnsiblePromptNoninteractive('not a tty'),
    )

    result = action_plugin.run(task_vars={})

    warn_mock.assert_called_once()
    assert 'failed' not in result or not result['failed']


@pytest.mark.parametrize('task_args', [{'timeout_seconds': 30}], indirect=True)
def test_timeout_seconds_ctrl_c_then_continue(mocker, action_plugin):
    """Ctrl+C during a timeout_seconds prompt leads to the C/A sub-prompt; 'c' continues the play."""
    mocker.patch('ansible.plugins.action.pause.display.display')
    mocker.patch(
        'ansible.plugins.action.pause.display.prompt_until',
        side_effect=[AnsiblePromptInterrupt('interrupt'), b''],
    )

    result = action_plugin.run(task_vars={})

    assert 'failed' not in result or not result['failed']


@pytest.mark.parametrize('task_args', [{'timeout_seconds': 30}], indirect=True)
def test_timeout_seconds_ctrl_c_then_abort(mocker, action_plugin):
    """Ctrl+C during a timeout_seconds prompt, then 'a' at sub-prompt aborts the run."""
    mocker.patch('ansible.plugins.action.pause.display.display')
    mocker.patch(
        'ansible.plugins.action.pause.display.prompt_until',
        side_effect=[AnsiblePromptInterrupt('interrupt'), AnsiblePromptInterrupt('abort')],
    )

    with pytest.raises(AnsibleError, match='user requested abort'):
        action_plugin.run(task_vars={})


@pytest.mark.parametrize('task_args', [{'timeout_seconds': 30}], indirect=True)
def test_timeout_seconds_present_in_result(mocker, action_plugin):
    """timed_out key is always included in result when timeout_seconds is specified."""
    mocker.patch('ansible.plugins.action.pause.display.display')
    mocker.patch('ansible.plugins.action.pause.display.prompt_until', return_value=b'hi')

    result = action_plugin.run(task_vars={})

    assert 'timed_out' in result


@pytest.mark.parametrize('task_args', [{}], indirect=True)
def test_no_timeout_timed_out_absent_from_result(mocker, action_plugin):
    """timed_out key must NOT appear in result when timeout_seconds is not specified."""
    mocker.patch('ansible.plugins.action.pause.display.display')
    mocker.patch('ansible.plugins.action.pause.display.prompt_until', return_value=b'hi')

    result = action_plugin.run(task_vars={})

    assert 'timed_out' not in result


@pytest.mark.parametrize('task_args', [{'timeout_seconds': 30, 'echo': False, 'prompt': 'My prompt'}], indirect=True)
def test_timeout_seconds_echo_false_does_not_append_hidden_suffix(mocker, action_plugin):
    """echo: false combined with timeout_seconds must not add '(output is hidden)' to the prompt.
    timeout_seconds always echoes input (private=False), so the suffix would be misleading."""
    mocker.patch('ansible.plugins.action.pause.display.display')
    prompt_mock = mocker.patch('ansible.plugins.action.pause.display.prompt_until', return_value=b'answer')

    action_plugin.run(task_vars={})

    called_prompt = prompt_mock.call_args.args[0]
    assert '(output is hidden)' not in called_prompt
    assert prompt_mock.call_args.kwargs.get('private') is False



@pytest.mark.parametrize('task_args', [{'seconds': 10, 'timeout_seconds': 5}], indirect=True)
def test_seconds_and_timeout_seconds_mutually_exclusive(mocker, action_plugin):
    """seconds and timeout_seconds must not be used together."""
    mocker.patch('ansible.plugins.action.pause.display.display')
    mocker.patch('ansible.plugins.action.pause.display.prompt_until', return_value=b'')

    with pytest.raises(AnsibleActionFail, match='mutually exclusive'):
        action_plugin.run(task_vars={})


@pytest.mark.parametrize('task_args', [{'minutes': 1, 'timeout_seconds': 5}], indirect=True)
def test_minutes_and_timeout_seconds_mutually_exclusive(mocker, action_plugin):
    """minutes and timeout_seconds must not be used together."""
    mocker.patch('ansible.plugins.action.pause.display.display')
    mocker.patch('ansible.plugins.action.pause.display.prompt_until', return_value=b'')

    with pytest.raises(AnsibleActionFail, match='mutually exclusive'):
        action_plugin.run(task_vars={})
