from __future__ import annotations

from unittest import mock

from ansible.executor import interpreter_discovery


def test_discover_interpreter_uses_delegated_host_for_warning():
    """When the task uses delegate_to, display messages should name the delegated host."""
    action = mock.MagicMock()
    action._task.delegate_to = "delegated.example"

    task_vars = {"inventory_hostname": "playhost.example"}

    real_display = interpreter_discovery.display

    captured_warnings = []

    with mock.patch.object(real_display, "warning", side_effect=lambda msg, **kw: captured_warnings.append(msg)), \
         mock.patch.object(real_display, "vvv") as vvv_mock, \
         mock.patch.object(real_display, "debug"), \
         mock.patch.object(interpreter_discovery.C.config, "get_config_value", return_value=["/usr/bin/python3"]):
        action._low_level_execute_command.return_value = {
            "stdout": "FOUND\n/usr/bin/python3.42\nENDFOUND",
            "stderr": "",
        }

        result = interpreter_discovery.discover_interpreter(
            action=action,
            interpreter_name="python",
            discovery_mode="auto",
            task_vars=task_vars,
        )

    assert result == "/usr/bin/python3.42"

    # The vvv "Attempting discovery" message should name the delegated host.
    vvv_call = vvv_mock.call_args
    assert vvv_call.kwargs["host"] == "delegated.example"

    # The warning should also name the delegated host, not inventory_hostname.
    assert any("delegated.example" in m for m in captured_warnings), captured_warnings
    assert not any("playhost.example" in m for m in captured_warnings), captured_warnings


def test_discover_interpreter_uses_inventory_host_without_delegation():
    """Without delegate_to, display messages should name the inventory host as before."""
    action = mock.MagicMock()
    action._task.delegate_to = None

    task_vars = {"inventory_hostname": "playhost.example"}

    real_display = interpreter_discovery.display

    captured_warnings = []

    with mock.patch.object(real_display, "warning", side_effect=lambda msg, **kw: captured_warnings.append(msg)), \
         mock.patch.object(real_display, "vvv") as vvv_mock, \
         mock.patch.object(real_display, "debug"), \
         mock.patch.object(interpreter_discovery.C.config, "get_config_value", return_value=["/usr/bin/python3"]):
        action._low_level_execute_command.return_value = {
            "stdout": "FOUND\n/usr/bin/python3.99\nENDFOUND",
            "stderr": "",
        }

        result = interpreter_discovery.discover_interpreter(
            action=action,
            interpreter_name="python",
            discovery_mode="auto",
            task_vars=task_vars,
        )

    assert result == "/usr/bin/python3.99"

    vvv_call = vvv_mock.call_args
    assert vvv_call.kwargs["host"] == "playhost.example"

    assert any("playhost.example" in m for m in captured_warnings), captured_warnings
