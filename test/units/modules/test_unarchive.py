from __future__ import absolute_import, division, print_function

__metaclass__ = type


import pytest

from ansible.modules.unarchive import ZipArchive, TgzArchive


class AnsibleModuleExit(Exception):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class ExitJson(AnsibleModuleExit):
    pass


class FailJson(AnsibleModuleExit):
    pass


@pytest.fixture
def fake_ansible_module():
    return FakeAnsibleModule()


class FakeAnsibleModule:
    def __init__(self):
        self.params = {}
        self.tmpdir = None

    def exit_json(self, *args, **kwargs):
        raise ExitJson(*args, **kwargs)

    def fail_json(self, *args, **kwargs):
        raise FailJson(*args, **kwargs)


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


class TestCaseTgzArchive:
    def test_no_tar_binary(self, mocker, fake_ansible_module):
        mocker.patch("ansible.modules.unarchive.get_bin_path", side_effect=ValueError)
        fake_ansible_module.params = {
            "extra_opts": "",
            "exclude": "",
            "include": "",
        }
        fake_ansible_module.check_mode = False

        t = TgzArchive(
            src="",
            b_dest="",
            file_args="",
            module=fake_ansible_module,
        )
        can_handle, reason = t.can_handle_archive()

        assert can_handle is False
        assert 'Unable to find required' in reason
        assert t.cmd_path is None
        assert t.tar_type is None
