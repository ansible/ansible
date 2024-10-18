# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import re

import pytest

from ansible.module_utils.facts.system.platform import PlatformFactCollector

SOLARIS_I86_RE_PATTERN = re.compile(r"i([3456]86|86pc)")


class TestPlatformFacts:
    def test_platform_system(self, mocker):
        mocker.patch("platform.system", return_value="Darwin")
        mocker.patch("platform.release", return_value="23.5.0")
        mocker.patch("platform.python_version", return_value="3.11.4")
        mocker.patch("socket.getfqdn", return_value="localhost.localdomain")
        mocker.patch("platform.node", return_value="localhost.localdomain")
        mac_kernel_ver = "Darwin Kernel Version 23.5.0: Wed May  1 20:12:58 PDT 2024; root:xnu-10063.121.3~5/RELEASE_ARM64_T6000"
        mocker.patch("platform.version", return_value=mac_kernel_ver)
        mocker.patch("platform.machine", return_value="arm64")
        mock_machine_id = "fe31eab802474047fd1e9f8ca050234b"
        mocker.patch(
            "ansible.module_utils.facts.system.platform.get_file_content",
            return_value=mock_machine_id,
        )
        platform_facts = PlatformFactCollector().collect()

        assert "system" in platform_facts
        assert "kernel" in platform_facts
        assert "kernel_version" in platform_facts
        assert "python_version" in platform_facts
        assert "fqdn" in platform_facts
        assert "hostname" in platform_facts
        assert "nodename" in platform_facts
        assert "domain" in platform_facts
        assert "machine" in platform_facts
        assert "architecture" in platform_facts

        assert platform_facts["system"] == "Darwin"
        assert platform_facts["kernel"] == "23.5.0"
        assert "Darwin" in platform_facts["kernel_version"]
        assert platform_facts["python_version"] == "3.11.4"
        assert platform_facts["fqdn"] == "localhost.localdomain"
        assert platform_facts["hostname"] == "localhost"
        assert platform_facts["nodename"] == "localhost.localdomain"
        assert platform_facts["domain"] == "localdomain"
        assert platform_facts["machine"] == "arm64"
        assert platform_facts["architecture"] == "arm64"
        assert platform_facts["machine_id"] == mock_machine_id

    @pytest.mark.parametrize(
        "platform_machine",
        [
            pytest.param("AMD64", id="amd64"),
            pytest.param("aarch64", id="arm64"),
            pytest.param("aarch64", id="armhf"),
            pytest.param("armv7l", id="armhf"),
            pytest.param("ppc", id="powerpc"),
            pytest.param("ppc64le", id="ppc64el"),
            pytest.param("x86_64", id="amd64"),
            pytest.param("x86_64", id="i386"),
            pytest.param("s390x", id="s390x"),
            pytest.param("riscv64", id="riscv64"),
            pytest.param("unknownarch", id="unknown-arch"),
            pytest.param("i386", id="solaris-i386"),
            pytest.param("i386", id="solaris-i386-64"),
        ],
    )
    def test_platform_machine(self, mocker, platform_machine):
        platform_facts = PlatformFactCollector().collect()
        mocker.patch("platform.machine", return_value=platform_machine)
        assert "machine" in platform_facts
        assert "userspace_bits" in platform_facts
        assert "architecture" in platform_facts

        if platform_facts["machine"] == "x86_64":
            assert platform_facts["architecture"] == platform_facts["machine"]
            assert "userspace_architecture" in platform_facts
            if platform_facts["userspace_bits"] == "64":
                assert platform_facts["userspace_architecture"] == "x86_64"
            elif platform_facts["userspace_bits"] == "32":
                assert platform_facts["userspace_architecture"] == "i386"
        elif SOLARIS_I86_RE_PATTERN.search(platform_facts["machine"]):
            assert platform_facts["architecture"] == "i386"
            if platform_facts["userspace_bits"] == "64":
                assert platform_facts["userspace_architecture"] == "x86_64"
            elif platform_facts["userspace_bits"] == "32":
                assert platform_facts["userspace_architecture"] == "i386"
        else:
            assert platform_facts["architecture"] == platform_facts["machine"]

    def test_platform_aix(self, mocker):
        module = mocker.MagicMock()
        mocker.patch("platform.system", return_value="AIX")
        mocker.patch.object(module, "get_bin_path", return_value="/usr/bin/getconf")
        mocker.patch.object(module, "run_command", return_value=(0, "chrp\n", ""))
        platform_facts = PlatformFactCollector().collect(module=module)
        assert platform_facts["architecture"] == "chrp"

        mocker.patch.object(module, "get_bin_path", side_effect=[None, "fake/bootinfo"])
        platform_facts = PlatformFactCollector().collect(module=module)
        assert platform_facts["architecture"] == "chrp"

    def test_platform_openbsd(self, mocker):
        module = mocker.MagicMock()
        mocker.patch("platform.system", return_value="OpenBSD")
        mocker.patch("platform.release", return_value="7.4")
        mocker.patch("platform.version", return_value="7.4")
        mocker.patch("socket.getfqdn", return_value="localhost.localdomain")
        mocker.patch("platform.node", return_value="localhost.localdomain")
        mocker.patch("platform.architecture", return_value=("64bit", "ELF"))
        mocker.patch("platform.machine", return_value="amd64")
        mocker.patch(
            "platform.uname",
            return_value=["OpenBSD", "openbsd", "7.4", "7.4", "amd64", "amd64"],
        )
        platform_facts = PlatformFactCollector().collect(module=module)
        assert platform_facts["architecture"] == "amd64"
