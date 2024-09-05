# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

from ansible.module_utils.basic import AnsibleModule as _AnsibleModule
from ansible.modules import mount_facts as _mount_facts
from units.modules.utils import (
    AnsibleExitJson as _AnsibleExitJson,
    AnsibleFailJson as _AnsibleFailJson,
    exit_json as _exit_json,
    fail_json as _fail_json,
    set_module_args as _set_module_args
)
from units.modules._mount_facts_data import _aix7_2, _freebsd14_1, _openbsd6_4, _rhel9_4, _solaris11_2
from unittest.mock import MagicMock

import pytest
import time

_UUIDS = {}


def _get_mock_module(invocation):
    _set_module_args(invocation)
    module = _AnsibleModule(
        argument_spec=_mount_facts._get_argument_spec(),
        supports_check_mode=True,
    )
    return module


def _mock_callable(return_value=None):
    def func(*args, **kwargs):
        return return_value

    return func


@pytest.fixture
def _set_file_content(monkeypatch):
    def _set_file_content(data):
        def mock_get_file_content(filename, default=None):
            if filename in data:
                return data[filename]
            return default
        monkeypatch.setattr(_mount_facts, "_get_file_content", mock_get_file_content)
    return _set_file_content


def test_invocation(monkeypatch, _set_file_content):
    _set_file_content({})
    _set_module_args({})
    monkeypatch.setattr(_mount_facts, "_run_mount_bin", _mock_callable(return_value=""))
    monkeypatch.setattr(_AnsibleModule, "exit_json", _exit_json)
    with pytest.raises(_AnsibleExitJson, match="{'ansible_facts': {'extended_mounts': {}}}"):
        _mount_facts.main()


def test_invalid_timeout(monkeypatch):
    _set_module_args({"timeout": 0})
    monkeypatch.setattr(_AnsibleModule, "fail_json", _fail_json)
    with pytest.raises(_AnsibleFailJson, match="argument 'timeout' must be a positive integer or null"):
        _mount_facts.main()


@pytest.mark.parametrize("invalid_binary, error", [
    ("ansible_test_missing_binary", 'Failed to find required executable "ansible_test_missing_binary" in paths: .*'),
    ("false", "Failed to execute .*false: Command '[^']*false' returned non-zero exit status 1"),
    (["one", "two"], "argument 'mount_binary' must be a string or null, not \\['one', 'two'\\]"),
])
def test_invalid_mount_binary(monkeypatch, _set_file_content, invalid_binary, error):
    _set_file_content({})
    _set_module_args({"mount_binary": invalid_binary})
    monkeypatch.setattr(_AnsibleModule, "fail_json", _fail_json)
    with pytest.raises(_AnsibleFailJson, match=error):
        _mount_facts.main()


def test_invalid_source(monkeypatch):
    _set_module_args({"sources": [""]})
    monkeypatch.setattr(_AnsibleModule, "fail_json", _fail_json)
    with pytest.raises(_AnsibleFailJson, match="sources contains an empty string"):
        _mount_facts.main()


def test_duplicate_source(monkeypatch, _set_file_content):
    _set_file_content({"/etc/fstab": _rhel9_4.fstab})
    mock_warn = MagicMock()
    monkeypatch.setattr(_AnsibleModule, "warn", mock_warn)

    user_sources = ["static", "/etc/fstab"]
    resolved_sources = ["/etc/fstab", "/etc/vfstab", "/etc/filesystems", "/etc/fstab"]
    expected_warning = "mount_facts option 'sources' contains duplicate entries, repeat sources will be ignored:"

    module = _get_mock_module({"sources": user_sources})
    list(_mount_facts._gen_mounts_by_source(module))
    assert mock_warn.called
    assert len(mock_warn.call_args_list) == 1
    assert mock_warn.call_args_list[0].args == (f"{expected_warning} {resolved_sources}",)


@pytest.mark.parametrize("function, data, expected_result_data", [
    ("_gen_fstab_entries", _rhel9_4.fstab, _rhel9_4.fstab_parsed),
    ("_gen_fstab_entries", _rhel9_4.mtab, _rhel9_4.mtab_parsed),
    ("_gen_fstab_entries", _freebsd14_1.fstab, _freebsd14_1.fstab_parsed),
    ("_gen_vfstab_entries", _solaris11_2.vfstab, _solaris11_2.vfstab_parsed),
    ("_gen_mnttab_entries", _solaris11_2.mnttab, _solaris11_2.mnttab_parsed),
    ("_gen_aix_filesystems_entries", _aix7_2.filesystems, _aix7_2.filesystems_parsed),
])
def test_list_mounts(function, data, expected_result_data):
    func = getattr(_mount_facts, function)
    result = list(func(data.splitlines()))
    assert result == [(_mnt, _line, _info) for _src, _mnt, _line, _info in expected_result_data]


def test_etc_filesystems_linux(_set_file_content):
    not_aix_data = (
        "ext4\next3\next2\nnodev proc\nnodev devpts\niso9770\nvfat\nhfs\nhfsplus\n*"
    )
    _set_file_content({"/etc/filesystems": not_aix_data})
    module = _get_mock_module({"sources": ["/etc/filesystems"]})
    assert list(_mount_facts._gen_mounts_by_source(module)) == []


@pytest.mark.parametrize("mount_stdout, expected_result_data", [
    (_rhel9_4.mount, _rhel9_4.mount_parsed),
    (_freebsd14_1.mount, _freebsd14_1.mount_parsed),
    (_openbsd6_4.mount, _openbsd6_4.mount_parsed),
    (_aix7_2.mount, _aix7_2.mount_parsed),
])
def test_parse_mount_bin_stdout(mount_stdout, expected_result_data):
    expected_result = [(_mnt, _line, _info) for _src, _mnt, _line, _info in expected_result_data]
    assert list(_mount_facts._gen_mounts_from_stdout(mount_stdout)) == expected_result


def test_parse_mount_bin_stdout_unknown(monkeypatch, _set_file_content):
    _set_file_content({})
    _set_module_args({})
    monkeypatch.setattr(_mount_facts, "_run_mount_bin", _mock_callable(return_value="nonsense"))
    monkeypatch.setattr(_AnsibleModule, "exit_json", _exit_json)
    with pytest.raises(_AnsibleExitJson, match="{'ansible_facts': {'extended_mounts': {}}}"):
        _mount_facts.main()


_rhel_mock_fs = {"/etc/fstab": _rhel9_4.fstab, "/etc/mtab": _rhel9_4.mtab}
_freebsd_mock_fs = {"/etc/fstab": _freebsd14_1.fstab}
_aix_mock_fs = {"/etc/filesystems": _aix7_2.filesystems}
_openbsd_mock_fs = {"/etc/fstab": _openbsd6_4.fstab}
_solaris_mock_fs = {"/etc/mnttab": _solaris11_2.mnttab, "/etc/vfstab": _solaris11_2.vfstab}


@pytest.mark.parametrize("sources, file_data, mount_data, results", [
    (["static"], _rhel_mock_fs, _rhel9_4.mount, _rhel9_4.fstab_parsed),
    (["/etc/fstab"], _rhel_mock_fs, _rhel9_4.mount, _rhel9_4.fstab_parsed),
    (["dynamic"], _rhel_mock_fs, _rhel9_4.mount, _rhel9_4.mtab_parsed),
    (["/etc/mtab"], _rhel_mock_fs, _rhel9_4.mount, _rhel9_4.mtab_parsed),
    (["all"], _rhel_mock_fs, _rhel9_4.mount, _rhel9_4.fstab_parsed + _rhel9_4.mtab_parsed),
    (["mount"], _rhel_mock_fs, _rhel9_4.mount, _rhel9_4.mount_parsed),
    (["all"], _freebsd_mock_fs, _freebsd14_1.mount, _freebsd14_1.fstab_parsed + _freebsd14_1.mount_parsed),
    (["static"], _freebsd_mock_fs, _freebsd14_1.mount, _freebsd14_1.fstab_parsed),
    (["dynamic"], _freebsd_mock_fs, _freebsd14_1.mount, _freebsd14_1.mount_parsed),
    (["mount"], _freebsd_mock_fs, _freebsd14_1.mount, _freebsd14_1.mount_parsed),
    (["all"], _aix_mock_fs, _aix7_2.mount, _aix7_2.filesystems_parsed + _aix7_2.mount_parsed),
    (["all"], _openbsd_mock_fs, _openbsd6_4.mount, _openbsd6_4.fstab_parsed + _openbsd6_4.mount_parsed),
    (["all"], _solaris_mock_fs, "", _solaris11_2.vfstab_parsed + _solaris11_2.mnttab_parsed),
])
def test_gen_mounts_by_sources(monkeypatch, _set_file_content, sources, file_data, mount_data, results):
    _set_file_content(file_data)
    mock_run_mount = _mock_callable(return_value=mount_data)
    monkeypatch.setattr(_mount_facts, "_run_mount_bin", mock_run_mount)
    module = _get_mock_module({"sources": sources})

    assert list(_mount_facts._gen_mounts_by_source(module)) == results


@pytest.mark.parametrize("on_timeout, should_warn, should_raise", [
    (None, False, True),
    ("warn", True, False),
    ("ignore", False, False),
])
def test_gen_mounts_by_source_timeout(monkeypatch, _set_file_content, on_timeout, should_warn, should_raise):
    _set_file_content({})
    monkeypatch.setattr(_AnsibleModule, "fail_json", _fail_json)
    mock_warn = MagicMock()
    monkeypatch.setattr(_AnsibleModule, "warn", mock_warn)

    # hack to simulate a hang (module entrypoint requires >= 1 or None)
    params = {"timeout": 0}
    if on_timeout:
        params["on_timeout"] = on_timeout

    module = _get_mock_module(params)
    if should_raise:
        with pytest.raises(_AnsibleFailJson, match="Command '[^']*mount' timed out after 0 seconds"):
            list(_mount_facts._gen_mounts_by_source(module))
    else:
        assert list(_mount_facts._gen_mounts_by_source(module)) == []
    assert mock_warn.called == should_warn


@pytest.mark.parametrize("filter_name, filter_value, source, mount_info", [
    ("devices", "proc", _rhel9_4.mtab_parsed[0][2], _rhel9_4.mtab_parsed[0][-1]),
    ("fstypes", "proc", _rhel9_4.mtab_parsed[0][2], _rhel9_4.mtab_parsed[0][-1]),
])
def test_get_mounts_facts_filtering(monkeypatch, _set_file_content, filter_name, filter_value, source, mount_info):
    _set_file_content({"/etc/mtab": _rhel9_4.mtab})
    monkeypatch.setattr(_mount_facts, "_get_mount_size", _mock_callable(return_value=None))
    module = _get_mock_module({filter_name: [filter_value]})
    results = _mount_facts._get_mount_facts(module, _UUIDS, _mock_callable())
    expected_context = {"source": "/etc/mtab", "source_data": source}
    assert len(results) == 1
    assert list(results.values())[0]["ansible_context"] == expected_context
    assert list(results.values())[0] == dict(ansible_context=expected_context, uuid="N/A", **mount_info)


def test_get_mounts_size(monkeypatch, _set_file_content):
    def mock_get_mount_size(*args, **kwargs):
        return {
            "block_available": 3242510,
            "block_size": 4096,
            "block_total": 3789825,
            "block_used": 547315,
            "inode_available": 1875503,
            "inode_total": 1966080,
            "size_available": 13281320960,
            "size_total": 15523123200,
        }

    _set_file_content({"/etc/mtab": _rhel9_4.mtab})
    monkeypatch.setattr(_mount_facts, "_get_mount_size", mock_get_mount_size)
    module = _get_mock_module({})
    result = _mount_facts._get_mount_facts(module, _UUIDS, _mock_callable())
    assert len(result) == len(_rhel9_4.mtab_parsed)
    assert result == {
        _mnt: dict(ansible_context={"source": _src, "source_data": _line}, uuid="N/A", **_info, **mock_get_mount_size())
        for _src, _mnt, _line, _info in _rhel9_4.mtab_parsed
    }


@pytest.mark.parametrize("on_timeout, should_warn, should_raise, slow_function", [
    (None, False, True, "_get_mount_size"),
    ("error", False, True, "_get_mount_size"),
    ("warn", True, False, "_get_mount_size"),
    ("ignore", False, False, "_get_mount_size"),
    ("error", False, True, "_udevadm_uuid"),
    ("warn", True, False, "_udevadm_uuid"),
    ("ignore", False, False, "_udevadm_uuid"),
])
def test_get_mount_facts_timeout(monkeypatch, _set_file_content, on_timeout, should_warn, should_raise, slow_function):
    _set_file_content({"/etc/mtab": _rhel9_4.mtab})
    monkeypatch.setattr(_AnsibleModule, "fail_json", _fail_json)
    mock_warn = MagicMock()
    monkeypatch.setattr(_AnsibleModule, "warn", mock_warn)

    params = {"timeout": 1, "sources": ["dynamic"], "mount_binary": "mount"}
    if on_timeout:
        params["on_timeout"] = on_timeout

    module = _get_mock_module(params)

    def mock_slow_function(*args, **kwargs):
        time.sleep(1.1)
        raise Exception("Timeout failed")

    if slow_function == "_get_mount_size":
        monkeypatch.setattr(_mount_facts, "_get_mount_size", mock_slow_function)
        match = "Timed out getting mount size .*"
        mock_udevadm_uuid = _mock_callable()
    else:
        monkeypatch.setattr(_mount_facts, "_get_mount_size", _mock_callable())
        match = "Timed out getting uuid for mount .+ \\(type .+\\) after 1 seconds"
        mock_udevadm_uuid = mock_slow_function

    if should_raise:
        with pytest.raises(_AnsibleFailJson, match=match):
            _mount_facts._get_mount_facts(module, _UUIDS, mock_udevadm_uuid)
    else:
        results = _mount_facts._get_mount_facts(module, _UUIDS, mock_udevadm_uuid)
        assert len(results) == len(_rhel9_4.mtab_parsed)
        assert results == {
            _mnt: dict(ansible_context={"source": _src, "source_data": _line}, uuid="N/A", **_info)
            for _src, _mnt, _line, _info in _rhel9_4.mtab_parsed
        }
    assert mock_warn.called == should_warn
