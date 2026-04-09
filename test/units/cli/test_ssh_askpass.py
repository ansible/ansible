from __future__ import annotations

from io import StringIO

import pytest

from ansible.cli._ssh_askpass import handle_prompt

HOST_KEY_PROMPT = (
    "The authenticity of host 'server (10.0.0.1)' can't be established.\n"
    "ECDSA key fingerprint is SHA256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.\n"
    "Are you sure you want to continue connecting (yes/no/[fingerprint])? "
)

IP_MISMATCH_PROMPT = (
    "Warning: the RSA host key for 'server' differs from the key for the IP address '10.0.0.1'\n"
    "Offending key for IP in /home/user/.ssh/known_hosts:1\n"
    "Matching host key in /home/user/.ssh/known_hosts:2\n"
    "Are you sure you want to continue connecting (yes/no)? "
)


def test_none(monkeypatch):
    monkeypatch.setenv('SSH_ASKPASS_PROMPT', 'none')
    stdout = StringIO()
    monkeypatch.setattr('sys.stdout', stdout)
    assert handle_prompt('some info message')
    assert stdout.getvalue() == ''


def test_confirm(monkeypatch):
    monkeypatch.setenv('SSH_ASKPASS_PROMPT', 'confirm')
    stdout = StringIO()
    monkeypatch.setattr('sys.stdout', stdout)
    assert handle_prompt(HOST_KEY_PROMPT)
    assert stdout.getvalue() == 'no'


@pytest.mark.parametrize('prompt', [HOST_KEY_PROMPT, IP_MISMATCH_PROMPT], ids=['host_key', 'ip_mismatch'])
def test_regex_fallback(monkeypatch, prompt):
    stdout = StringIO()
    monkeypatch.setattr('sys.stdout', stdout)
    assert handle_prompt(prompt)
    assert stdout.getvalue() == 'no'
