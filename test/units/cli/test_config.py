from __future__ import annotations

import os
import subprocess
import sys


def run_validate(cfg_path):

    env = os.environ.copy()
    env["ANSIBLE_CONFIG"] = str(cfg_path)  # force
    result = subprocess.run(
        [sys.executable, "-m", "ansible.cli.config", "validate", "--format", "ini"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    return result


def test_validate_accepts_ssh_connection_section(tmp_path):
    cfg = tmp_path / "ansible.cfg"
    cfg.write_text("[ssh_connection]\nssh_args = -o ControlMaster=auto\n", encoding="utf-8")

    result = run_validate(cfg)
    assert result.returncode == 0, result.stdout + "\n" + result.stderr


def test_validate_rejects_unknown_section(tmp_path):
    cfg = tmp_path / "ansible.cfg"
    cfg.write_text("[totally_unknown_section]\nfoo = bar\n", encoding="utf-8")

    result = run_validate(cfg)
    assert result.returncode == 1, result.stdout + "\n" + result.stderr
    assert "Found unknown section" in (result.stdout + result.stderr)
