# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import json

import pytest

from ansible.module_utils import secrets
from ansible.module_utils._internal import _logging
from ansible.module_utils._internal._secrets import SecretMasker
from ansible.module_utils.common import sys_info
from ansible.modules import user


@pytest.fixture
def secret_masker(monkeypatch: pytest.MonkeyPatch) -> SecretMasker:
    masker = SecretMasker()
    monkeypatch.setattr(secrets, '_secret_masker', masker)
    return masker


@pytest.fixture
def module_log(mocker):
    return mocker.patch.object(_logging, 'log_to_system')


@pytest.fixture
def run_user(monkeypatch, set_module_args, capsys, module_env_mocker, module_log):
    def user_exists(self) -> bool:
        assert self.module.check_mode
        return False

    def run_command(*args, **kwargs):
        pytest.fail('The user module must not execute commands in this test')

    monkeypatch.setattr(user.User, 'user_exists', user_exists)
    monkeypatch.setattr(user.DarwinUser, 'user_exists', user_exists)
    monkeypatch.setattr(user.AnsibleModule, 'run_command', run_command)
    monkeypatch.setattr(sys_info, 'get_distribution', lambda: None)
    monkeypatch.setattr(user.socket, 'gethostname', lambda: 'test.example')

    def run(args: dict, platform: str = 'Linux', exit_code: int = 0) -> dict:
        monkeypatch.setattr(sys_info.platform, 'system', lambda: platform)
        set_module_args(dict(name='test-user', _ansible_check_mode=True, **args))
        with pytest.raises(SystemExit) as exc:
            user.main()
        assert exc.value.code == exit_code
        return json.loads(capsys.readouterr().out)

    return run


@pytest.mark.parametrize('password', ['*', '!', '*************'])
@pytest.mark.parametrize('platform', ['Linux', 'FreeBSD', 'Darwin'])
def test_password_lock_markers(run_user, secret_masker, module_log, password, platform) -> None:
    result = run_user({'password': password}, platform=platform)
    assert result['changed'] is True

    if platform == 'Darwin':
        assert secret_masker.mask_string(password) == '$REDACTED$'
        assert password in result['_ansible_new_secrets']
        assert module_log.call_args.kwargs['log_args']['password'] == '$REDACTED$'
    else:
        assert secret_masker.mask_string(f'before {password} after') == f'before {password} after'
        assert password not in result.get('_ansible_new_secrets', [])
        assert module_log.call_args.kwargs['log_args']['password'] == password


@pytest.mark.parametrize('password', ['$6$salt$' + 'a' * 86, '!$6$salt$' + 'a' * 86, '**', '!!', ' * '])
def test_other_password_values_remain_secret(run_user, secret_masker, module_log, password) -> None:
    result = run_user({'password': password})
    assert secret_masker.mask_string(password.strip()) == '$REDACTED$'
    assert password.strip() in result['_ansible_new_secrets']
    assert module_log.call_args.kwargs['log_args']['password'] == '$REDACTED$'


@pytest.mark.parametrize('password', ['*', '!', '*************'])
def test_password_lock_marker_is_still_a_secret_when_used_as_passphrase(run_user, secret_masker, module_log, password) -> None:
    result = run_user({'password': password, 'ssh_key_passphrase': password})
    assert secret_masker.mask_string(password) == '$REDACTED$'
    assert password in result['_ansible_new_secrets']
    assert module_log.call_args.kwargs['log_args']['ssh_key_passphrase'] == '$REDACTED$'


def test_password_lock_marker_does_not_unregister_existing_secret(run_user, secret_masker, module_log) -> None:
    secret_masker.register_secret_text('*')
    run_user({'password': '*'})
    assert secret_masker.mask_string('before * after') == 'before $REDACTED$ after'
    assert module_log.call_args.kwargs['log_args']['password'] == '$REDACTED$'


@pytest.mark.parametrize('password', ['synthetic-password', ['synthetic-password'], {'value': 'synthetic-password'}])
def test_invalid_arguments_preserve_password_secrecy(run_user, secret_masker, module_log, password) -> None:
    result = run_user({'password': password, 'state': 'synthetic-password'}, exit_code=1)
    assert result['failed'] is True
    assert 'state' in result['msg']
    assert secret_masker.mask_string('synthetic-password') == '$REDACTED$'
    assert 'synthetic-password' not in secret_masker.mask_string(result['msg'])
    assert 'synthetic-password' in result['_ansible_new_secrets']
    module_log.assert_not_called()


def test_task_no_log_still_suppresses_logging(run_user, secret_masker, module_log) -> None:
    result = run_user({'password': '*', '_ansible_no_log': True})
    assert result['changed'] is True
    module_log.assert_not_called()
