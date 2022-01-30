"""Tests for the "shebang" sanity test"""

import pytest


def load_sanity_test(name, path):
    """see https://stackoverflow.com/a/67692/1947070"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestSkippedPaths:
    shebang = load_sanity_test("shebang", "test/lib/ansible_test/_util/controller/sanity/code-smell/shebang.py")

    def test_examples(self):
        assert self.shebang.is_excluded_path("examples/file.sh")

    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("roles/rolename/files/f.sh", True),
            ("roles/rolename/templates/f.sh", True),
            ("roles/name with spaces/files/f.sh", True),
            ("roles/rolename/defaults/files.sh", False),
            ("collection/name/roles/rolename/files/f.sh", True)
        ]
    )
    def test_roles(self, path, expected):
        assert self.shebang.is_excluded_path(path) is expected


class TestValidateModuleShebang:
    shebang = load_sanity_test("shebang", "test/lib/ansible_test/_util/controller/sanity/code-smell/shebang.py")

    def test_module_should_not_be_executable(self):
        """Even with a valid shebang, modules should not be executable"""
        assert not self.shebang.validate_module_shebang(b"#!/usr/bin/python", True, "script.py")

    def test_expected_shebang_matches(self):
        assert self.shebang.validate_module_shebang(b"#!/usr/bin/python", False, "script.py")

    def test_expected_shebang_doesnt_match(self):
        assert not self.shebang.validate_module_shebang(b"#!/usr/bin/env python3", False, "script.py")

    def test_no_expected_shebang(self):
        assert not self.shebang.validate_module_shebang(b"#!/usr/bin/env -S dhall --file", False, "script.dhall")


class TestValidateShebang:
    shebang = load_sanity_test("shebang", "test/lib/ansible_test/_util/controller/sanity/code-smell/shebang.py")
    non_executable_filemode = 33204

    def test_excluded_path_early_exit(self):
        assert self.shebang.validate_shebang(b"invalid shebang", 33268, "examples/file.sh")

    def test_included_path_no_early_exit_(self):
        assert not self.shebang.validate_shebang(b"invalid_shebang", 33268, "file.sh")

    def test_lib_not_executable_and_no_shebang(self):
        assert self.shebang.validate_shebang(b"# not a shebang", self.non_executable_filemode, "lib/file.py")
