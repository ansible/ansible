from __future__ import absolute_import, division, print_function

__metaclass__ = type


from ansible.modules.unarchive import ZipArchive, TgzArchive


class TestCaseZipArchive:
    def test_no_zip_binary(self, mocker):
        fake_ansible_module = mocker.Mock()
        fake_ansible_module.get_bin_path = mocker.Mock(return_value=None)
        fake_ansible_module.params = {
            "extra_opts": "",
            "exclude": "",
            "include": "",
        }

        zip_obj = ZipArchive(
            src="",
            b_dest="",
            file_args="",
            module=fake_ansible_module,
        )
        status, msg = zip_obj.can_handle_archive()
        assert not status
        assert 'Command "unzip"' in msg


class TestCaseTgzArchive:
    def test_no_tar_binary(self, mocker):
        fake_ansible_module = mocker.Mock()
        fake_ansible_module.get_bin_path = mocker.Mock(return_value=None)
        fake_ansible_module.check_mode = False
        fake_ansible_module.params = {
            "extra_opts": "",
            "exclude": "",
            "include": "",
        }
        tgz_obj = TgzArchive(
            src="",
            b_dest="",
            file_args="",
            module=fake_ansible_module,
        )

        status, msg = tgz_obj.can_handle_archive()
        assert not status
        assert 'Command "gtar"' in msg
