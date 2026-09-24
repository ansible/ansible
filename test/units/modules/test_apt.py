# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import collections
import datetime
import json
import shlex

from ansible.module_utils.testing import patch_module_args
from ansible.modules import apt
from ansible.modules.apt import expand_pkgspec_from_fnmatches
import pytest
import pytest_mock

FakePackage = collections.namedtuple("Package", ("name",))
fake_cache = [
    FakePackage("apt"),
    FakePackage("apt-utils"),
    FakePackage("not-selected"),
]


@pytest.mark.parametrize(
    ("test_input", "expected"),
    [
        pytest.param(
            ["apt"],
            ["apt"],
            id="trivial",
        ),
        pytest.param(
            ["apt=1.0*"],
            ["apt=1.0*"],
            id="version-wildcard",
        ),
        pytest.param(
            ["apt*=1.0*"],
            ["apt", "apt-utils"],
            id="pkgname-wildcard-version",
        ),
        pytest.param(
            ["apt*"],
            ["apt", "apt-utils"],
            id="pkgname-expands",
        ),
    ],
)
def test_expand_pkgspec_from_fnmatches(test_input, expected):
    """Test positive cases of ``expand_pkgspec_from_fnmatches``."""
    assert expand_pkgspec_from_fnmatches(None, test_input, fake_cache) == expected


@pytest.mark.parametrize('operation', ['autoremove', 'autoclean', None])
@pytest.mark.parametrize('cache_options', [
    {'update_cache': True},
    {'cache_valid_time': 3600},
    {'update_cache': True, 'cache_valid_time': 3600},
])
@pytest.mark.parametrize('check_mode', [False, True])
def test_cleanup_with_cache_options(
    operation: str | None,
    cache_options: dict[str, bool | int],
    check_mode: bool,
    mocker: pytest_mock.MockerFixture,
    capfd: pytest.CaptureFixture[str],
) -> None:
    """Cache options must not prevent a requested cleanup from running."""
    mocker.patch.object(apt, 'HAS_PYTHON_APT', True)
    apt_library = mocker.patch.object(apt, 'apt')
    apt_library.cache.LockFailedException = BlockingIOError
    apt_library.cache.FetchFailedException = ConnectionError
    cache = mocker.patch.object(apt, 'get_cache').return_value
    cache_time = datetime.datetime.now() if cache_options.get('cache_valid_time') else datetime.datetime(2000, 1, 1)
    mocker.patch.object(apt, 'get_updated_cache_time', return_value=(cache_time, 1234))
    mocker.patch.object(apt, 'get_best_parsable_locale', return_value='C')
    mocker.patch.object(apt.locale_module, 'setlocale')
    mocker.patch.object(apt.AnsibleModule, 'get_bin_path', return_value='/usr/bin/apt-get')
    output = 'Del hello 1.0 [10 kB]\n' if operation == 'autoclean' else 'The following packages will be REMOVED:\n  hello\n'
    run_command = mocker.patch.object(apt.AnsibleModule, 'run_command', return_value=(0, output, ''))
    args = dict(cache_options, _ansible_check_mode=check_mode)
    if operation:
        args[operation] = True

    with pytest.raises(SystemExit) as exception, patch_module_args(args):
        apt.main()

    assert exception.value.code == 0
    stdout = capfd.readouterr().out
    result = json.loads(stdout)
    if operation:
        run_command.assert_called_once()
        command = shlex.split(run_command.call_args.args[0])
        assert operation in command
        assert ('--simulate' in command) is check_mode
        assert result['changed'] is True
        assert result['stdout'] == output
    else:
        run_command.assert_not_called()
        assert result['cache_update_time'] == 1234
        assert result['cache_updated'] is (check_mode and not cache_options.get('cache_valid_time', 0))

    if not check_mode and not cache_options.get('cache_valid_time'):
        cache.update.assert_called_once()
    else:
        cache.update.assert_not_called()
