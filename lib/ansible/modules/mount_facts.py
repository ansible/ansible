# -*- coding: utf-8 -*-
# Copyright (c) 2024 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = """
---
module: mount_facts
version_added: 2.18
short_description: Retrieve mount information.
description:
  - Retrieve information about mounts from preferred sources and filter the results based on the filesystem type and device.
options:
  devices:
    description: A list of fnmatch patterns to filter mounts by the special device or remote file system.
    default:
      - "*"
    type: list
    elements: str
  fstypes:
    description: A list of fnmatch patterns to filter mounts by the type of the file system.
    default:
      - "*"
    type: list
    elements: str
  sources:
    default:
      - all
    description:
      - A list of files to use when collecting mount information, or the special values V(all), V(static), and V(dynamic).
      - V(dynamic) contains V(/etc/mtab), V(/proc/mounts), V(/etc/mnttab), and if none are found, falls back to O(mount_binary).
      - V(static) contains V(/etc/fstab), V(/etc/vfstab), and V(/etc/filesystems).
      - Note that V(/etc/filesystems) is AIX-specific and the Linux file by this name will be ignored.
    type: list
    elements: str
  mount_binary:
    description:
      - The O(mount_binary) is used if O(sources) contain the same value, or if O(sources) contains a dynamic
        source, and none were found (as can be expected on BSD or AIX hosts).
      - Set to V(null) to stop after no dynamic file source is found instead.
    type: raw
    default: mount
  timeout:
    description:
      - This is the maximum number of seconds to query for each mount. When this is V(null), wait indefinitely.
      - Configure in conjunction with O(on_timeout) to try to skip unresponsive mounts.
      - This timeout also applies to the O(mount_binary) command to list mounts.
      - If the module is configured to run during the play's fact gathering stage, set a timeout using module_defaults to prevent a hang (see example).
    type: int
  on_timeout:
    description:
      - The action to take when listing mounts or mount information exceeds O(timeout).
    type: str
    default: error
    choices:
      - error
      - warn
      - ignore
extends_documentation_fragment:
  - action_common_attributes
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
  platform:
    platforms: posix
author:
  - Ansible Core Team
  - Sloane Hertel (@s-hertel)
"""

EXAMPLES = """
- name: Get non-local devices
  mount_facts:
    devices: "[!/]*"

- name: Get FUSE subtype mounts
  mount_facts:
    fstypes:
      - "fuse.*"

- name: Get NFS mounts during gather_facts with timeout
  hosts: all
  gather_facts: true
  vars:
    ansible_facts_modules:
      - ansible.builtin.mount_facts
  module_default:
    ansible.builtin.mount_facts:
      timeout: 10
      fstypes:
        - nfs
        - nfs4

- name: Get mounts from a non-default location
  mount_facts:
    sources:
      - /usr/etc/fstab

- name: Get mounts from the mount binary
  mount_facts:
    sources:
      - /sbin/mount
    mount_binary: /sbin/mount
"""

RETURN = """
ansible_facts:
    description:
      - An ansible_facts dictionary containing a dictionary of C(extended_mounts).
      - Each key in C(extended_mounts) is a mount point, and the value contains mount information (similar to C(ansible_facts["mounts"])).
        Each value also contains the key C(ansible_context), with details about the source and line(s) corresponding to the parsed mount point.
    returned: on success
    type: dict
    sample:
      extended_mounts:
        /mnt/mount:
          ansible_context:
            source: /proc/mounts
            source_data: "hostname:/srv/sshfs on /mnt/mount type fuse.sshfs (rw,nosuid,nodev,relatime,user_id=0,group_id=0)"
          block_available: 3242510
          block_size: 4096
          block_total: 3789825
          block_used: 547315
          device: hostname:/srv/sshfs
          fstype: fuse.sshfs
          inode_available: 1875503
          inode_total: 1966080
          mount: /mnt/mount
          options: "rw,nosuid,nodev,relatime,user_id=0,group_id=0"
          size_available: 13281320960
          size_total: 15523123200
          uuid: N/A
"""

from ansible.module_utils.basic import AnsibleModule as _AnsibleModule
from ansible.module_utils.facts import timeout as _timeout
from ansible.module_utils.facts.hardware.linux import LinuxHardware as _LinuxHardware, _replace_octal_escapes
from ansible.module_utils.facts.utils import get_mount_size as _get_mount_size, get_file_content as _get_file_content

from collections.abc import Callable as _Callable, Generator as _Generator
from contextlib import suppress as _suppress
from fnmatch import fnmatch as _fnmatch
from functools import wraps as _wraps

import datetime as _datetime
import re as _re
import subprocess as _subprocess

_STATIC_SOURCES = ["/etc/fstab", "/etc/vfstab", "/etc/filesystems"]
_DYNAMIC_SOURCES = ["/etc/mtab", "/proc/mounts", "/etc/mnttab"]

# AIX and BSD don't have a file-based dynamic source, so the module also supports running a mount binary to collect these.
# Pattern for Linux, including OpenBSD and NetBSD
_LINUX_MOUNT_RE = _re.compile(r"^(?P<device>\S+) on (?P<mount>\S+) type (?P<fstype>\S+) \((?P<options>.+)\)$")
# Pattern for other BSD including FreeBSD, DragonFlyBSD, and MacOS
_BSD_MOUNT_RE = _re.compile(r"^(?P<device>\S+) on (?P<mount>\S+) \((?P<fstype>.+)\)$")
# Pattern for AIX, example in https://www.ibm.com/docs/en/aix/7.2?topic=m-mount-command
_AIX_MOUNT_RE = _re.compile(r"^(?P<node>\S*)\s+(?P<mounted>\S+)\s+(?P<mount>\S+)\s+(?P<fstype>\S+)\s+(?P<time>\S+\s+\d+\s+\d+:\d+)\s+(?P<options>.*)$")


def _handle_timeout(module, default=None):
    """Decorator to catch timeout exceptions and handle failing, warning, and ignoring the timeout."""
    def decorator(func):
        @_wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (_subprocess.TimeoutExpired, _timeout.TimeoutError) as e:
                if module.params["on_timeout"] == "error":
                    module.fail_json(msg=str(e))
                elif module.params["on_timeout"] == "warn":
                    module.warn(str(e))
                return default
        return wrapper
    return decorator


def _run_mount_bin(module: _AnsibleModule, mount_bin: str) -> str:  # type: ignore # Missing return statement
    """Execute the specified mount binary with optional timeout."""
    mount_bin = module.get_bin_path(mount_bin, required=True)
    try:
        return _handle_timeout(module, default="")(_subprocess.check_output)(
            mount_bin, text=True, timeout=module.params["timeout"]
        )
    except _subprocess.CalledProcessError as e:
        module.fail_json(msg=f"Failed to execute {mount_bin}: {str(e)}")


def _get_mount_pattern(stdout: str):
    lines = stdout.splitlines()
    pattern = None
    if any(_LINUX_MOUNT_RE.match(line) for line in lines):
        pattern = _LINUX_MOUNT_RE
    elif any(_BSD_MOUNT_RE.match(line) for line in lines):
        pattern = _BSD_MOUNT_RE
    elif any(_AIX_MOUNT_RE.match(line) for line in lines):
        pattern = _AIX_MOUNT_RE
    return pattern


def _gen_mounts_from_stdout(stdout: str) -> _Generator[tuple[str, str, dict[str, str]]]:
    """List mount dictionaries from mount stdout."""
    if not (pattern := _get_mount_pattern(stdout)):
        stdout = ""

    for line in stdout.splitlines():
        if not (match := pattern.match(line)):
            # AIX has a couple header lines for some reason
            # MacOS "map" lines are skipped (e.g. "map auto_home on /System/Volumes/Data/home (autofs, automounted, nobrowse)")
            # TODO: include MacOS lines
            continue

        mount = match.groupdict()["mount"]
        if pattern is _LINUX_MOUNT_RE:
            mount_info = match.groupdict()
        elif pattern is _BSD_MOUNT_RE:
            # the group containing fstype is comma separated, and may include whitespace
            mount_info = match.groupdict()
            parts = _re.split(r"\s*,\s*", match.group("fstype"), 1)
            if len(parts) == 1:
                mount_info["fstype"] = parts[0]
            else:
                mount_info.update({"fstype": parts[0], "options": parts[1]})
        elif pattern is _AIX_MOUNT_RE:
            mount_info = match.groupdict()
            device = mount_info.pop("mounted")
            node = mount_info.pop("node")
            if device and node:
                device = f"{node}:{device}"
            mount_info["device"] = device

        yield mount, line, mount_info


def _gen_fstab_entries(lines: list[str]) -> _Generator[tuple[str, str, dict[str, str | int]]]:
    """Yield tuples from /etc/fstab https://man7.org/linux/man-pages/man5/fstab.5.html.

    Each tuple contains the mount point, line of origin, and the dictionary of the parsed line.
    """
    for line in lines:
        if not (line := line.strip()) or line.startswith("#"):
            continue
        fields = [_replace_octal_escapes(field) for field in line.split()]
        mount_info = {
            "device": fields[0],
            "mount": fields[1],
            "fstype": fields[2],
            "options": fields[3],
        }
        with _suppress(IndexError):
            # the last two fields are optional
            mount_info["dump"] = int(fields[4])
            mount_info["passno"] = int(fields[5])
        yield fields[1], line, mount_info


def _gen_vfstab_entries(lines: list[str]) -> _Generator[tuple[str, str, dict[str, str | int]]]:
    """Yield tuples from /etc/vfstab https://docs.oracle.com/cd/E36784_01/html/E36882/vfstab-4.html.

    Each tuple contains the mount point, line of origin, and the dictionary of the parsed line.
    """
    for line in lines:
        if not line.strip() or line.strip().startswith("#"):
            continue
        fields = line.split()
        passno: str | int = fields[4]
        with _suppress(ValueError):
            passno = int(passno)
        mount_info: dict[str, str | int] = {
            "device": fields[0],
            "device_to_fsck": fields[1],
            "mount": fields[2],
            "fstype": fields[3],
            "passno": passno,
            "mount_at_boot": fields[5],
            "options": fields[6],
        }
        yield fields[2], line, mount_info


def _list_aix_filesystems_stanzas(lines: list[str]) -> list[list[str]]:
    """Parse stanzas from /etc/filesystems according to https://www.ibm.com/docs/hu/aix/7.2?topic=files-filesystems-file."""
    stanzas = []
    for line in lines:
        if line.startswith("*") or not line.strip().rstrip():
            continue
        if line.rstrip().endswith(":"):
            stanzas.append([line])
        else:
            if "=" not in line:
                # Expected for Linux, return an empty list since this doesn't appear to be AIX /etc/filesystems
                stanzas = []
                break
            stanzas[-1].append(line)
    return stanzas


def _gen_aix_filesystems_entries(lines: list[str]) -> _Generator[tuple[str, str, dict[str, str]]]:
    """Yield tuples from /etc/filesystems https://www.ibm.com/docs/hu/aix/7.2?topic=files-filesystems-file.

    Each tuple contains the mount point, lines of origin, and the dictionary of the parsed lines.
    """
    for stanza in _list_aix_filesystems_stanzas(lines):
        original = "\n".join(stanza)
        mount = stanza.pop(0)[:-1]  # snip trailing :
        mount_info = {}
        for line in stanza:
            attr, value = line.split("=", 1)
            mount_info[attr.strip().rstrip()] = value.strip().rstrip()

        device = ""
        if (nodename := mount_info.get("nodename")):
            device = nodename
        if (dev := mount_info.get("dev")):
            if device:
                device += ":"
            device += dev

        mount_info["device"] = device or "unknown"
        mount_info["fstype"] = mount_info.get("vfs") or "unknown"

        # mount_info may contain the AIX /etc/filesystems attribute "mount", not to be confused with the mount point
        yield mount, original, mount_info


def _gen_mnttab_entries(lines: list[str]) -> _Generator[tuple[str, str, dict[str, str | int]]]:
    """Yield tuples from /etc/mnttab columns https://docs.oracle.com/cd/E36784_01/html/E36882/mnttab-4.html.

    Each tuple contains the mount point, line of origin, and the dictionary of the parsed line.
    """
    if not any(len(fields[4]) == 10 for line in lines for fields in [line.split()]):
        raise ValueError
    for line in lines:
        fields = line.split()
        _datetime.date.fromtimestamp(int(fields[4]))
        mount_info: dict[str, str | int] = {
            "device": fields[0],
            "mount": fields[1],
            "fstype": fields[2],
            "options": fields[3],
            "time": int(fields[4]),
        }
        yield fields[1], line, mount_info


def _gen_mounts_by_file(sources: list[str]):
    """Yield parsed mount entries from the first successful generator for each source.

    Generators are tried in the following order to minimize false positives:
    - /etc/vfstab: 7 columns
    - /etc/mnttab: 5 columns (mnttab[4] must contain UNIX timestamp)
    - /etc/fstab: 4-6 columns (fstab[4] is optional and historically 0-9, but can be any int)
    - /etc/filesystems: multi-line, not column-based, and specific to AIX
    """
    seen = set()
    for file in sources:
        if file in seen:
            continue
        seen.add(file)

        if not (lines := _get_file_content(file, "").splitlines()):
            continue

        for gen_mounts in [_gen_vfstab_entries, _gen_mnttab_entries, _gen_fstab_entries, _gen_aix_filesystems_entries]:
            with _suppress(IndexError, ValueError):
                yield from [(file, _mnt, _line, _info) for _mnt, _line, _info in gen_mounts(lines)]
                break


def _get_file_sources(module: _AnsibleModule) -> list[str]:
    """Return a list of filenames from the requested sources."""
    sources: list[str] = []
    for source in module.params["sources"]:
        if not source:
            module.fail_json(msg="sources contains an empty string")

        if source in {"static", "all"}:
            sources.extend(_STATIC_SOURCES)
        if source in {"dynamic", "all"}:
            sources.extend(_DYNAMIC_SOURCES)

        elif source not in {"static", "dynamic", "all", module.params["mount_binary"]}:
            sources.append(source)
    return sources


def _gen_mounts_by_source(module: _AnsibleModule):
    """Iterate over the sources and yield tuples containing the source, mount point, source line(s), and the parsed result."""
    sources = _get_file_sources(module)

    if len(set(sources)) < len(sources):
        module.warn(f"mount_facts option 'sources' contains duplicate entries, repeat sources will be ignored: {sources}")

    collected = set()
    for mount_tuple in _gen_mounts_by_file(sources):
        collected.add(mount_tuple[0])
        yield mount_tuple

    if (mount_binary := module.params["mount_binary"]) and (mount_binary in module.params["sources"] or (
        set(sources).intersection(_DYNAMIC_SOURCES)
        and not collected.intersection(_DYNAMIC_SOURCES)
    )):
        stdout = _run_mount_bin(module, mount_binary)
        yield from [(mount_binary, *mount_info) for mount_info in _gen_mounts_from_stdout(stdout)]


def _get_mount_facts(module: _AnsibleModule, uuids: dict, udevadm_uuid: _Callable):
    """List and filter mounts, returning a dictionary containing mount points as the keys (last listed wins)."""
    seconds = module.params["timeout"]

    # merge sources based on the mount point (last source wins)
    facts = {}
    for source, mount, origin, fields in _gen_mounts_by_source(module):
        device = fields["device"]
        fstype = fields["fstype"]

        if not any(_fnmatch(device, pattern) for pattern in module.params["devices"]):
            continue
        if not any(_fnmatch(fstype, pattern) for pattern in module.params["fstypes"]):
            continue

        timed_func = _timeout.timeout(seconds, f"Timed out getting mount size for mount {mount} (type {fstype})")(_get_mount_size)
        if mount_size := _handle_timeout(module)(timed_func)(mount):
            fields.update(mount_size)

        timed_func = _timeout.timeout(seconds, f"Timed out getting uuid for mount {mount} (type {fstype})")(udevadm_uuid)
        uuid = uuids.get(device, _handle_timeout(module)(timed_func)(device))

        fields.update({"ansible_context": {"source": source, "source_data": origin}, "uuid": uuid or "N/A"})
        facts[mount] = fields

    return facts


def _get_argument_spec():
    """Helper returning the argument spec."""
    return dict(
        sources=dict(type="list", elements="str", default=["all"]),
        mount_binary=dict(default="mount", type="raw"),
        devices=dict(type="list", elements="str", default=["*"]),
        fstypes=dict(type="list", elements="str", default=["*"]),
        timeout=dict(type="int"),
        on_timeout=dict(choices=["error", "warn", "ignore"], default="error"),
    )


def main():
    module = _AnsibleModule(
        argument_spec=_get_argument_spec(),
        supports_check_mode=True,
    )
    if (seconds := module.params["timeout"]) is not None and seconds <= 0:
        module.fail_json(msg="argument 'timeout' must be a positive integer or null, not {seconds}")
    if (mount_binary := module.params["mount_binary"]) is not None and not isinstance(mount_binary, str):
        module.fail_json(msg=f"argument 'mount_binary' must be a string or null, not {mount_binary}")

    hardware = _LinuxHardware(module)
    mounts = _get_mount_facts(module, hardware._lsblk_uuid(), hardware._udevadm_uuid)
    module.exit_json(ansible_facts={"extended_mounts": mounts})


if __name__ == "__main__":
    main()
