# -*- coding: utf-8 -*-
# (c) 2016 Toshio Kuratomi <tkuratomi@ansible.com>
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

"""Tests for the monit.py monitoring module"""

# Stdlib
from __future__ import (
    absolute_import, division, print_function, unicode_literals
)
import sys
try:
    import mock
except ImportError:
    from unittest import mock

# Third party
import pytest

# Local
from ansible.modules.monitoring import monit


# Keep tests from lasting forever
monit.SLEEP_TIME = 0


@pytest.fixture()
def module(monkeypatch):
    """Replace AnsibleModule with a mock object"""
    mock_module = mock.MagicMock(name='AnsibleModuleMock')

    mock_module.params = {
        'name': 'monit_test',
        'timeout': 5,
    }
    mock_module.check_mode = False

    monkeypatch.setattr(
        monit, 'AnsibleModule', mock.MagicMock(return_value=mock_module)
    )

    mock_module.exit_json.side_effect = lambda *x, **y: sys.exit()
    mock_module.fail_json.side_effect = lambda *x, **y: sys.exit()

    return mock_module


class TestMonitModule:
    """Tests for the monit module"""

    @pytest.mark.parametrize('cmd_output, fail', [
        (  # Reload, good status
            [
                (0, '', ''),
                (0, "Program 'monit_test' Status ok", '')
            ],
            False
        ),
        (  # Reload, failed status (doesn't care)
            [
                (0, '', ''),
                (0, "Program 'monit_test' Status failed", '')
            ],
            False
        ),
        (  # Reload, running status
            [
                (0, '', ''),
                (0, "Process 'monit_test' Running", '')
            ],
            False
        ),
        (  # Reload, not monitored (doesn't care)
            [
                (0, '', ''),
                (0, "Process 'monit_test' Not monitored", '')
            ],
            False
        ),
        (  # Reload, initializing; should call again in wait loop
            [
                (0, '', ''),
                (0, "Process 'monit_test' Initializing", ''),
                (0, "Process 'monit_test' Running", '')
            ],
            False
        ),
        (  # Reload, pending; should call again in wait loop
            [
                (0, '', ''),
                (0, "Process 'monit_test' Pending", ''),
                (0, "Process 'monit_test' Running", ''),
            ],
            False
        ),
        (  # Reload, bad RC
                [(1, '', ''), ],
                True
        ),
        (  # Reload, bad RC
                [(2, '', ''), ],
                True
        ),
    ])
    def test_reloaded(self, module, cmd_output, fail):
        # type: (mock.MagicMock, tuple, bool) -> None
        """Test when state == reloaded

        :param cmd_output: a list of return tuples that should be
            returned, in order, from module.check_command
        :param fail: whether module.fail_json() is expected to be called
        """
        module.params['state'] = 'reloaded'
        module.run_command.side_effect = cmd_output

        with pytest.raises(SystemExit):
            monit.main()

        # Assert we had all expected calls
        assert len(module.run_command.mock_calls) == len(cmd_output)

        if fail:
            module.fail_json.assert_called_once_with(
                msg='monit reload failed',
                stdout=cmd_output[0][1],
                stderr=cmd_output[0][2]
            )
        else:
            module.exit_json.assert_called_once_with(
                changed=True, name=module.params['name'], state='reloaded'
            )

    @pytest.mark.parametrize('cmd_output, fail, fail_msg', [
        (  # Not present, immediately good after reload
            [
                (0, '', ''),
                (0, '', ''),
                (0, "Program 'monit_test' Status ok", ''),
            ],
            False,
            None,
        ),
        (  # Not present, immediately good after reload
            [
                (0, '', ''),
                (0, '', ''),
                (0, "Process 'monit_test' Running", ''),
            ],
            False,
            None,
        ),
        (  # Not present, not present after reload, good on second try
            [
                (0, '', ''),
                (0, '', ''),
                (0, '', ''),
                (0, "Process 'monit_test' Running", ''),
            ],
            False,
            None,
        ),
        (  # Not present, not present after reload, good on second try
            [
                (0, '', ''),
                (0, '', ''),
                (0, '', ''),
                (0, "Program 'monit_test' Status ok", ''),
            ],
            False,
            None,
        ),
        (  # Not present, not present after reload, then pending, then good
            [
                (0, '', ''),
                (0, '', ''),
                (0, '', ''),
                (0, "Process 'monit_test' Pending", ''),
                (0, "Process 'monit_test' Running", ''),
            ],
            False,
            None,
        ),
        (  # Not present, not present after reload, then pending, then good
            [
                (0, '', ''),
                (0, '', ''),
                (0, '', ''),
                (0, "Program 'monit_test' Initializing", ''),
                (0, "Program 'monit_test' Status ok", ''),
            ],
            False,
            None,
        ),
    ])
    def test_present_reload(self, module, cmd_output, fail, fail_msg):
        # type: (mock.MagicMock, tuple, bool, str) -> None
        """Test when state == present and item is not already present

        :param cmd_output: a list of return tuples that should be
            returned, in order, from module.check_command
        :param fail: whether module.fail_json() is expected to be called
        :param fail_msg: expected value of the msg kwarg in the call to
            module.fail_json()
        """
        module.params['state'] = 'present'
        module.run_command.side_effect = cmd_output

        with pytest.raises(SystemExit):
            monit.main()

        # Assert we had all expected calls
        assert len(module.run_command.mock_calls) == len(cmd_output)

        if fail:
            module.fail_json.assert_called_once_with(msg=fail_msg)
            assert not module.exit_json.mock_calls
        else:
            assert not module.fail_json.mock_calls
            module.exit_json.assert_called_once_with(
                changed=True, name=module.params['name'], state='present'
            )

    @pytest.mark.parametrize('cmd_output', [
        [(0, "Process 'monit_test' Running", ''), ],
        [(0, "Process 'monit_test' Running - restart pending", ''), ],
        [(0, "Process 'monit_test' Not monitored", ''), ],
        [(0, "Process 'monit_test' Initializing", ''), ],
        [(0, "Process 'monit_test' Pending", ''), ],
        [(0, "Program 'monit_test' Status ok", ''), ],
        [(0, "Program 'monit_test' Status failed", ''), ],
        [(0, "Program 'monit_test' Not monitored", ''), ],
        [(0, "Program 'monit_test' Initializing", ''), ],
        [(0, "Program 'monit_test' Pending", ''), ],
    ])
    def test_present_present(self, module, cmd_output):
        # type: (mock.MagicMock, tuple) -> None
        """Test when state == present and item is already present

        :param cmd_output: a list of return tuples that should be
            returned, in order, from module.check_command
        """
        module.params['state'] = 'present'
        module.run_command.side_effect = cmd_output

        with pytest.raises(SystemExit):
            monit.main()

        # Assert we had all expected calls
        assert len(module.run_command.mock_calls) == len(cmd_output)

        assert not module.fail_json.mock_calls

        module.exit_json.assert_called_once_with(
            changed=False, name=module.params['name'], state='present'
        )

    @pytest.mark.parametrize('state, cmd_output', [
        ('started', [(0, "Process 'monit_test' Running", '')]),
        ('started', [(0, "Program 'monit_test' Status ok", '')]),
        ('running', [(0, "Process 'monit_test' Running", '')]),
        ('running', [(0, "Program 'monit_test' Status ok", '')]),
    ])
    def test_started_monitored_running(self, module, state, cmd_output):
        # type: (mock.MagicMock, str, tuple) -> None
        """Test when state is monitored or started and item is already running

        :param state: desired module state
        :param cmd_output: a list of return tuples that should be
            returned, in order, from module.check_command
        """
        module.params['state'] = state
        module.run_command.side_effect = cmd_output

        with pytest.raises(SystemExit):
            monit.main()

        # Assert we had all expected calls
        assert len(module.run_command.mock_calls) == len(cmd_output)

        assert not module.fail_json.mock_calls

        module.exit_json.assert_called_once_with(
            changed=False, name=module.params['name'], state=state
        )

    @pytest.mark.parametrize('cmd_output, fail, fail_status', [
        (
            [
                (0, "Process 'monit_test' Running", ''),
                (0, '', ''),
                (0, "Process 'monit_test' Not monitored", ''),
            ],
            False,
            None
        ),
        (
            [
                (0, "Process 'monit_test' Running", ''),
                (0, '', ''),
                (0, "Process 'monit_test' Running - stop pending", ''),
            ],
            False,
            None
        ),
        (
            [
                (0, "Program 'monit_test' Status ok", ''),
                (0, '', ''),
                (0, "Process 'monit_test' Not monitored", ''),
            ],
            False,
            None
        ),
        (
            [
                (0, "Program 'monit_test' Status ok", ''),
                (0, '', ''),
                (0, "Program 'monit_test' Status ok - stop pending", ''),
            ],
            False,
            None
        ),
        (
            [
                (0, "Process 'monit_test' Running", ''),
                (0, '', ''),
                (0, "Process 'monit_test' Running", ''),
            ],
            True,
            'running'
        ),
        (
            [
                (0, "Program 'monit_test' Status ok", ''),
                (0, '', ''),
                (0, "Program 'monit_test' Status ok", ''),
            ],
            True,
            'status ok'
        ),
    ])
    def test_stopped(self, module, cmd_output, fail, fail_status):
        # type: (mock.MagicMock, tuple, bool, str) -> None
        """Test when state == stopped

        :param cmd_output: a list of return tuples that should be
            returned, in order, from module.check_command
        :param fail: whether ``module.fail_json()`` is expected to be
            called
        :param fail_status: expected kwarg for ``status`` in call to
            ``module.fail_json()``
        """
        module.params['state'] = 'stopped'
        module.run_command.side_effect = cmd_output

        with pytest.raises(SystemExit):
            monit.main()

        # Assert we had all expected calls
        assert len(module.run_command.mock_calls) == len(cmd_output)

        if fail:
            module.fail_json.assert_called_once_with(
                msg='monit_test process not stopped',
                status=fail_status
            )
        else:
            module.exit_json.assert_called_once_with(
                changed=True, name=module.params['name'], state='stopped'
            )

    @pytest.mark.parametrize('cmd_output, fail, fail_status', [
        (
                [
                    (0, "Process 'monit_test' Running", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Not monitored", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Process 'monit_test' Running", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Running - unmonitor pending", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Program 'monit_test' Status ok", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Not monitored", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Program 'monit_test' Status ok", ''),
                    (0, '', ''),
                    (0, "Program 'monit_test' Status ok - unmonitor pending", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Process 'monit_test' Running", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Running", ''),
                ],
                True,
                'running'
        ),
        (
                [
                    (0, "Program 'monit_test' Status ok", ''),
                    (0, '', ''),
                    (0, "Program 'monit_test' Status ok", ''),
                ],
                True,
                'status ok'
        ),
    ])
    def test_unmonitored(self, module, cmd_output, fail, fail_status):
        # type: (mock.MagicMock, tuple, bool, str) -> None
        """Test when state == unmonitored

        :param cmd_output: a list of return tuples that should be
            returned, in order, from module.check_command
        :param fail: whether ``module.fail_json()`` is expected to be
            called
        :param fail_status: expected kwarg for ``status`` in call to
            ``module.fail_json()``
        """
        module.params['state'] = 'unmonitored'
        module.run_command.side_effect = cmd_output

        with pytest.raises(SystemExit):
            monit.main()

        # Assert we had all expected calls
        assert len(module.run_command.mock_calls) == len(cmd_output)

        if fail:
            module.fail_json.assert_called_once_with(
                msg='monit_test process not unmonitored',
                status=fail_status
            )
        else:
            module.exit_json.assert_called_once_with(
                changed=True, name=module.params['name'], state='unmonitored'
            )

    @pytest.mark.parametrize('cmd_output, fail, fail_status', [
        (
                [
                    (0, "Process 'monit_test' Running", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Running", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Process 'monit_test' Running", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Initializing", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Process 'monit_test' Running", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Running - restart pending", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Program 'monit_test' Status ok", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Status ok", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Program 'monit_test' Status ok", ''),
                    (0, '', ''),
                    (0, "Program 'monit_test' Initializing", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Program 'monit_test' Status ok", ''),
                    (0, '', ''),
                    (0, "Program 'monit_test' Status ok - restart pending", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Process 'monit_test' Running", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Stopped", ''),
                ],
                True,
                'stopped'
        ),
        (
                [
                    (0, "Program 'monit_test' Status ok", ''),
                    (0, '', ''),
                    (0, "Program 'monit_test' Status failed", ''),
                ],
                True,
                'status failed'
        ),
    ])
    def test_restarted(self, module, cmd_output, fail, fail_status):
        # type: (mock.MagicMock, tuple, bool, str) -> None
        """Test when state == restarted

        :param cmd_output: a list of return tuples that should be
            returned, in order, from module.check_command
        :param fail: whether ``module.fail_json()`` is expected to be
            called
        :param fail_status: expected kwarg for ``status`` in call to
            ``module.fail_json()``
        """
        module.params['state'] = 'restarted'
        module.run_command.side_effect = cmd_output

        with pytest.raises(SystemExit):
            monit.main()

        # Assert we had all expected calls
        assert len(module.run_command.mock_calls) == len(cmd_output)

        if fail:
            module.fail_json.assert_called_once_with(
                msg='monit_test process not restarted',
                status=fail_status
            )
        else:
            module.exit_json.assert_called_once_with(
                changed=True, name=module.params['name'], state='restarted'
            )

    @pytest.mark.parametrize('cmd_output, fail, fail_status', [
        (
                [
                    (0, "Process 'monit_test' Stopped", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Running", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Process 'monit_test' Not monitored", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Running", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Process 'monit_test' Stopped", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Initializing", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Process 'monit_test' Stopped", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Running - start pending", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Program 'monit_test' Status failed", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Status ok", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Program 'monit_test' Status failed", ''),
                    (0, '', ''),
                    (0, "Program 'monit_test' Initializing", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Process 'monit_test' Stopped", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Stopped", ''),
                ],
                True,
                'stopped'
        ),
        (
                [
                    (0, "Program 'monit_test' Status failed", ''),
                    (0, '', ''),
                    (0, "Program 'monit_test' Status failed", ''),
                ],
                True,
                'status failed'
        ),
    ])
    def test_restarted(self, module, cmd_output, fail, fail_status):
        # type: (mock.MagicMock, tuple, bool, str) -> None
        """Test when state == started

        :param cmd_output: a list of return tuples that should be
            returned, in order, from module.check_command
        :param fail: whether ``module.fail_json()`` is expected to be
            called
        :param fail_status: expected kwarg for ``status`` in call to
            ``module.fail_json()``
        """
        module.params['state'] = 'started'
        module.run_command.side_effect = cmd_output

        with pytest.raises(SystemExit):
            monit.main()

        # Assert we had all expected calls
        assert len(module.run_command.mock_calls) == len(cmd_output)

        if fail:
            module.fail_json.assert_called_once_with(
                msg='monit_test process not started',
                status=fail_status
            )
        else:
            module.exit_json.assert_called_once_with(
                changed=True, name=module.params['name'], state='started'
            )

    @pytest.mark.parametrize('cmd_output, fail, fail_status', [
        (
                [
                    (0, "Process 'monit_test' Not monitored", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Running", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Process 'monit_test' Stopped", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Running", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Process 'monit_test' Stopped", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Stopped", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Process 'monit_test' Not monitored", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Initializing", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Process 'monit_test' Not monitored", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Running - start pending", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Program 'monit_test' Status failed", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Status ok", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Program 'monit_test' Status failed", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Status failed", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Program 'monit_test' Not monitored", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Status ok", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Program 'monit_test' Status failed", ''),
                    (0, '', ''),
                    (0, "Program 'monit_test' Initializing", ''),
                ],
                False,
                None
        ),
        (
                [
                    (0, "Program 'monit_test' Not monitored", ''),
                    (0, '', ''),
                    (0, "Program 'monit_test' Not monitored", ''),
                ],
                True,
                'not monitored'
        ),
        (
                [
                    (0, "Process 'monit_test' Not monitored", ''),
                    (0, '', ''),
                    (0, "Process 'monit_test' Not monitored", ''),
                ],
                True,
                'not monitored'
        ),
    ])
    def test_restarted(self, module, cmd_output, fail, fail_status):
        # type: (mock.MagicMock, tuple, bool, str) -> None
        """Test when state == started

        :param cmd_output: a list of return tuples that should be
            returned, in order, from module.check_command
        :param fail: whether ``module.fail_json()`` is expected to be
            called
        :param fail_status: expected kwarg for ``status`` in call to
            ``module.fail_json()``
        """
        module.params['state'] = 'monitored'
        module.run_command.side_effect = cmd_output

        with pytest.raises(SystemExit):
            monit.main()

        # Assert we had all expected calls
        assert len(module.run_command.mock_calls) == len(cmd_output)

        if fail:
            module.fail_json.assert_called_once_with(
                msg='monit_test process not monitored',
                status=fail_status
            )
        else:
            module.exit_json.assert_called_once_with(
                changed=True, name=module.params['name'], state='monitored'
            )
