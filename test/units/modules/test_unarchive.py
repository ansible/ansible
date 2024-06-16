# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations


import time
import pytest

from ansible.modules.unarchive import ZipArchive, TgzArchive


@pytest.fixture
def fake_ansible_module():
    return FakeAnsibleModule()


class FakeAnsibleModule:
    def __init__(self):
        self.params = {}
        self.tmpdir = None


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

        mocker.patch.object(ZipArchive, "_parse_infolist", return_value="")
        z = ZipArchive(
            src="sample.zip",
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
                time.mktime(time.struct_time((2107, 12, 31, 23, 59, 59, 0, 0, 0))),
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
        mocker.patch.object(ZipArchive, "_parse_infolist", return_value="")
        fake_ansible_module.params = {
            "extra_opts": "",
            "exclude": "",
            "include": "",
            "io_buffer_size": 65536,
        }

        z = ZipArchive(
            src="sample.zip",
            b_dest="",
            file_args="",
            module=fake_ansible_module,
        )
        assert z._valid_time_stamp(test_input) == expected

    @pytest.mark.parametrize(
        ("test_input", "expected"),
        [
            pytest.param(
                [("foo.txt", 1, 1)],
                {
                    "foo.txt": 1,
                },
                id="utf-8-filename",
            ),
            pytest.param(
                [("Café.txt", 2048, 2)],
                {
                    "Café.txt": 2,
                },
                id="non-utf-8-filename",
            ),
            pytest.param(
                [("Caf├⌐.txt", 1, 3)],
                {
                    "Café.txt": 3,
                },
                id="cp437-filename",
            ),
            pytest.param(
                [("1.txt", 1, 4), ("2.txt", 1, 5)],
                {
                    "1.txt": 4,
                    "2.txt": 5,
                },
                id="multiple-filenames",
            ),
        ],
    )
    def test_parse_infolist(self, mocker, fake_ansible_module, test_input, expected):
        class FakeZipInfo:
            def __init__(self, filename, flag_bits, crc):
                self.filename = filename
                self.flag_bits = flag_bits
                self.CRC = crc

        class FakeZipFile:
            def __init__(self, src):
                pass

            def infolist(self):
                pass

            def close(self):
                pass

        mocker.patch(
            "ansible.modules.unarchive.get_bin_path",
            side_effect=["/bin/unzip", "/bin/zipinfo"],
        )
        mocker.patch("ansible.modules.unarchive.ZipFile", FakeZipFile)

        mocked_fake_zipinfo = []
        for input in test_input:
            mocked_fake_zipinfo.append(
                FakeZipInfo(
                    filename=input[0],
                    flag_bits=input[1],
                    crc=input[2],
                )
            )
        mocker.patch(
            "ansible.modules.unarchive.ZipFile.infolist",
            return_value=mocked_fake_zipinfo,
        )
        fake_ansible_module.params = {
            "extra_opts": "",
            "exclude": "",
            "include": "",
            "io_buffer_size": 65536,
        }
        z = ZipArchive(
            src="sample.zip",
            b_dest="",
            file_args="",
            module=fake_ansible_module,
        )
        z._parse_infolist()
        assert z.files_in_archive == list(expected.keys())
        for k, v in expected.items():
            assert z._crc32(k) == v


class TestCaseTgzArchive:
    def test_no_tar_binary(self, mocker, fake_ansible_module):
        mocker.patch("ansible.modules.unarchive.get_bin_path", side_effect=ValueError)
        fake_ansible_module.params = {
            "extra_opts": "",
            "exclude": "",
            "include": "",
            "io_buffer_size": 65536,
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
