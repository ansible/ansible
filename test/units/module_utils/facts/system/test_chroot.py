# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import stat
from collections import namedtuple

import pytest


from ansible.module_utils.facts.system.chroot import ChrootFactCollector

MOCKSTAT = namedtuple("mock_stat", ["st_dev", "st_ino", "st_size", "st_mtime"])


class TestChrootFacts:
    def test_debian_chroot(self, monkeypatch):
        monkeypatch.setenv("debian_chroot", "test")
        chroot_facts = ChrootFactCollector().collect()
        assert chroot_facts["is_chroot"]

    def test_detect_chroot(self, mocker):
        mocker.patch(
            "os.stat",
            side_effect=[
                MOCKSTAT(st_dev=stat.S_IFDIR, st_ino=2, st_size=0, st_mtime=0),
                MOCKSTAT(st_dev=stat.S_IFDIR, st_ino=3, st_size=1, st_mtime=0),
            ],
        )
        chroot_facts = ChrootFactCollector().collect()
        assert chroot_facts["is_chroot"] is True

    def _mock_os_stat_exception(self):
        raise Exception("fake os.stat exception")

    def test_detect_chroot_no_btrfs_no_xfs(self, mocker):
        mocker.patch(
            "os.stat",
            side_effect=[
                MOCKSTAT(st_dev=stat.S_IFDIR, st_ino=2, st_size=0, st_mtime=0),
                self._mock_os_stat_exception,
            ],
        )
        chroot_facts = ChrootFactCollector().collect()
        assert chroot_facts["is_chroot"] is False

    def test_detect_chroot_no_module(self, mocker):
        mocker.patch(
            "os.stat",
            side_effect=[
                MOCKSTAT(st_dev=stat.S_IFDIR, st_ino=2, st_size=0, st_mtime=0),
                self._mock_os_stat_exception,
            ],
        )

        chroot_facts = ChrootFactCollector().collect(module=None)
        assert chroot_facts["is_chroot"] is False

    @pytest.mark.parametrize(
        ("test_input"),
        [
            pytest.param(
                "btrfs",
                id="btrfs",
            ),
            pytest.param(
                "xfs",
                id="xfs",
            ),
        ],
    )
    def test_detect_chroot_fs(self, mocker, test_input):
        module = mocker.MagicMock()
        mocker.patch(
            "os.stat",
            side_effect=[
                MOCKSTAT(st_dev=stat.S_IFDIR, st_ino=2, st_size=0, st_mtime=0),
                self._mock_os_stat_exception,
            ],
        )
        mocker.patch.object(module, "get_bin_path", return_value="/usr/bin/stat")
        mocker.patch.object(module, "run_command", return_value=(0, test_input, ""))

        chroot_facts = ChrootFactCollector().collect(module=module)
        assert chroot_facts["is_chroot"] is True
