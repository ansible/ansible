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
    def test_no_zip_binary(self, mocker, fake_ansible_module):
        mocker.patch("ansible.modules.unarchive.get_bin_path", side_effect=ValueError)
        fake_ansible_module.params = {
            "extra_opts": "",
            "exclude": "",
            "include": "",
        }
        with pytest.raises(FailJson) as exec_info:
            z = ZipArchive(
                src="",
                b_dest="",
                file_args="",
                module=fake_ansible_module,
            )
        assert "Unable to find required" in exec_info.value.kwargs["msg"]


class TestCaseTgzArchive:
    def test_no_tar_binary(self, mocker, fake_ansible_module):
        mocker.patch("ansible.modules.unarchive.get_bin_path", side_effect=ValueError)
        fake_ansible_module.params = {
            "extra_opts": "",
            "exclude": "",
            "include": "",
        }
        fake_ansible_module.check_mode = False
        with pytest.raises(FailJson) as exec_info:
            z = TgzArchive(
                src="",
                b_dest="",
                file_args="",
                module=fake_ansible_module,
            )
        assert "Unable to find required" in exec_info.value.kwargs["msg"]
