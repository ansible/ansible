from __future__ import annotations

import sys
import types

import pytest

if sys.platform == "win32":
    basic = types.ModuleType("ansible.module_utils.basic")
    basic.AnsibleModule = object
    basic.missing_required_lib = lambda library, reason=None: library
    sys.modules["ansible.module_utils.basic"] = basic

from ansible.modules import get_url


class ModuleExit(Exception):
    def __init__(self, kwargs):
        self.kwargs = kwargs


class FakeModule:
    check_mode = False

    def __init__(self, params):
        self.params = params

    def load_file_common_arguments(self, params, path=None):
        return {"path": path}

    def set_fs_attributes_if_different(self, file_args, changed):
        return False

    def exit_json(self, **kwargs):
        raise ModuleExit(kwargs)

    def fail_json(self, **kwargs):
        raise AssertionError(kwargs)


def test_force_false_existing_dest_without_checksum_skips_download(
    monkeypatch, tmp_path
):
    dest = tmp_path / "existing.txt"
    dest.write_text("already here")
    module = FakeModule(
        {
            "url": "https://example.invalid/existing.txt",
            "dest": str(dest),
            "backup": False,
            "force": False,
            "checksum": "",
            "use_proxy": True,
            "timeout": 10,
            "headers": None,
            "tmp_dest": None,
            "unredirected_headers": [],
            "decompress": True,
            "ciphers": None,
            "use_netrc": True,
        }
    )

    monkeypatch.setattr(get_url, "AnsibleModule", lambda **kwargs: module)

    def fail_url_get(*args, **kwargs):
        raise AssertionError("url_get should not run when force is false")

    monkeypatch.setattr(get_url, "url_get", fail_url_get)

    with pytest.raises(ModuleExit) as exc:
        get_url.main()

    assert exc.value.kwargs["changed"] is False
    assert exc.value.kwargs["msg"] == "file already exists"
