# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations


import time
import pytest

from ansible.modules.unarchive import ZipArchive, TgzArchive


class FakeAnsibleModule:
    def __init__(self):
        self.params = {}
        self.tmpdir = None
        self.check_mode = False
        self._name = 'unarchive'

    def fail_json(self, **kwargs):
        raise ValueError(kwargs.get('msg', ''))

    def exit_json(self, **kwargs):
        raise ValueError(kwargs.get('msg', ''))

    def debug(self, msg):
        pass

    def run_command(self, cmd, **kwargs):
        if '--version' in cmd:
            return 0, 'tar (GNU tar) 1.34', ''
        return 1, '', ''


@pytest.fixture
def fake_ansible_module():
    m = FakeAnsibleModule()
    m.params = {
        "extra_opts": [],
        "exclude": [],
        "include": [],
        "io_buffer_size": 65536,
    }
    return m


@pytest.fixture
def gnu_tar_environment(mocker):
    mocker.patch("ansible.modules.unarchive.get_bin_path", return_value="/bin/tar")


def max_zip_timestamp():
    """Return the max clamp value that will be selected."""
    try:
        return time.mktime(time.struct_time((2107, 12, 31, 23, 59, 59, 0, 0, 0)))
    except OverflowError:
        return time.mktime(time.struct_time((2038, 1, 1, 0, 0, 0, 0, 0, 0)))


@pytest.mark.parametrize('extra_opts', [
    [],
    ['--transform', 's/^xxx/yyy/'],
])
def test_reject_dangerous_gnu_tar_extra_opts_allows_safe_options(gnu_tar_environment, fake_ansible_module, extra_opts):
    fake_ansible_module.params['extra_opts'] = extra_opts
    TgzArchive(
        src="",
        b_dest="",
        file_args="",
        module=fake_ansible_module,
    )


@pytest.mark.parametrize('extra_opts, expected_msg', [
    (['--checkpoint-action=exec=id'], 'Refusing unsafe tar extra option: --checkpoint-action=exec=id'),
    (['--checkpoint-action', 'exec=id'], 'Refusing unsafe tar extra option: --checkpoint-action exec=id'),
    (['--to-command=/bin/sh'], 'Refusing unsafe tar extra option: --to-command=/bin/sh'),
    (['--to-command', '/bin/sh'], 'Refusing unsafe tar extra option: --to-command /bin/sh'),
    (['--use-compress-program=/bin/sh'], 'Refusing unsafe tar extra option: --use-compress-program=/bin/sh'),
    (['--use-compress-program', '/bin/sh'], 'Refusing unsafe tar extra option: --use-compress-program /bin/sh'),
    (['-I', '/bin/sh'], 'Refusing unsafe tar extra option: -I /bin/sh'),
])
def test_reject_dangerous_gnu_tar_extra_opts(gnu_tar_environment, fake_ansible_module, extra_opts, expected_msg):
    fake_ansible_module.params['extra_opts'] = extra_opts
    with pytest.raises(ValueError) as exc_info:
        TgzArchive(
            src="",
            b_dest="",
            file_args="",
            module=fake_ansible_module,
        )
    assert str(exc_info.value) == expected_msg


class TestCaseZipArchive:
    @pytest.mark.parametrize(
        'side_effect, expected_reason', (
            ([ValueError, '/bin/zipinfo'], "Unable to find required 'unzip'"),
            (ValueError, "Unable to find required 'unzip' or 'zipinfo'"),
        )
    )
    def test_no_zip_zipinfo_binary(self, mocker, fake_ansible_module, side_effect, expected_reason):
        mocker.patch("ansible.modules.unarchive.get_bin_path", side_effect=side_effect)
        fake_ansible_module.params = {
            "extra_opts": "",
            "exclude": "",
            "include": "",
            "io_buffer_size": 65536,
        }

        z = ZipArchive(
            src="",
            b_dest="",
            file_args="",
            module=fake_ansible_module,
        )
        can_handle, reason = z.can_handle_archive()

        assert can_handle is False
        assert expected_reason in reason
        assert z.cmd_path is None

    @pytest.mark.parametrize(
        ("test_input", "expected"),
        [
            pytest.param(
                "19800000.000000",
                time.mktime(time.struct_time((1980, 0, 0, 0, 0, 0, 0, 0, 0))),
                id="invalid-month-1980",
            ),
            pytest.param(
                "19791231.000000",
                time.mktime(time.struct_time((1980, 1, 1, 0, 0, 0, 0, 0, 0))),
                id="invalid-year-1979",
            ),
            pytest.param(
                "19810101.000000",
                time.mktime(time.struct_time((1981, 1, 1, 0, 0, 0, 0, 0, 0))),
                id="valid-datetime",
            ),
            pytest.param(
                "21081231.000000",
                max_zip_timestamp(),
                id="invalid-year-2108",
            ),
            pytest.param(
                "INVALID_TIME_DATE",
                time.mktime(time.struct_time((1980, 1, 1, 0, 0, 0, 0, 0, 0))),
                id="invalid-datetime",
            ),
        ],
    )
    def test_valid_time_stamp(self, mocker, fake_ansible_module, test_input, expected):
        mocker.patch(
            "ansible.modules.unarchive.get_bin_path",
            side_effect=["/bin/unzip", "/bin/zipinfo"],
        )
        fake_ansible_module.params = {
            "extra_opts": "",
            "exclude": "",
            "include": "",
            "io_buffer_size": 65536,
        }

        z = ZipArchive(
            src="",
            b_dest="",
            file_args="",
            module=fake_ansible_module,
        )
        assert z._valid_time_stamp(test_input) == expected


class TestCaseTgzArchive:
    def test_no_tar_binary(self, mocker, fake_ansible_module):
        mocker.patch("ansible.modules.unarchive.get_bin_path", side_effect=ValueError)
        fake_ansible_module.params = {
            "extra_opts": [],
            "exclude": [],
            "include": [],
            "io_buffer_size": 65536,
        }
        fake_ansible_module.check_mode = False

        with pytest.raises(ValueError, match='Unable to find required'):
            TgzArchive(
                src="",
                b_dest="",
                file_args="",
                module=fake_ansible_module,
            )

    def test_rejects_dangerous_extra_opts(self, gnu_tar_environment, fake_ansible_module):
        fake_ansible_module.params = {
            "extra_opts": ['--checkpoint-action=exec=id'],
            "exclude": [],
            "include": [],
            "io_buffer_size": 65536,
        }
        fake_ansible_module.check_mode = False

        with pytest.raises(ValueError, match='Refusing unsafe tar extra option'):
            TgzArchive(
                src="",
                b_dest="",
                file_args="",
                module=fake_ansible_module,
            )
