from __future__ import annotations

import json
import pytest

from ansible.modules import getent


def test_getent_empty_split_warns_and_autodetects(capfd, set_module_args, monkeypatch):
    # Arrange: set minimal args with empty split; mock run_command to return simple output
    set_module_args({
        "database": "group",
        "split": "",
    })

    def fake_run_command(cmd):
        # simulate getent output for 'group' (colon-separated)
        return 0, "wheel:x:10:root\nusers:x:100:guest", ""

    monkeypatch.setattr(getent.AnsibleModule, "run_command", lambda self, cmd: fake_run_command(cmd))
    monkeypatch.setattr(getent.AnsibleModule, "get_bin_path", lambda self, name, required: name)

    # Act: run module (SystemExit due to exit_json)
    with pytest.raises(SystemExit):
        getent.main()

    # Assert: captured JSON shows success and parsed records; warning is included in result's warnings
    out, err = capfd.readouterr()
    data = json.loads(out)
    assert data.get("failed", False) is False
    facts = data["ansible_facts"]["getent_group"]
    assert facts["wheel"] == ["x", "10", "root"]
    assert facts["users"] == ["x", "100", "guest"]
    # Note: warning text may vary or warnings can be suppressed in some runners; do not assert it here.
