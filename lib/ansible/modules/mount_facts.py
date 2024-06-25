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
      - An ansible_facts dictionary containing the key C(extended_mounts), and value matching the default structure of C(ansible_facts[mount_facts]).
    returned: always
    type: dict
    sample:
      extended_mounts:
        /mnt/mount:
          source: /proc/mounts
          info:
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

from fnmatch import fnmatch as _fnmatch
from collections.abc import Callable as _Callable
from contextlib import suppress as _suppress
from fnmatch import fnmatch as _fnmatch
from functools import wraps as _wraps

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
_AIX_MOUNT_RE = _re.compile(r"^(?P<node>\S+)?\s+(?P<mounted>\S+)\s+(?P<mount>\S+)\s+(?P<fstype>\S+)\s+(?P<time>\S+\s+\d+\s+\d+:\d+)\s+(?P<options>.*)$")


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


def _list_mounts_from_mount_stdout(stdout) -> list[dict[str, str]]:
    """List mount dictionaries from mount stdout."""
    lines = stdout.splitlines()
    if any(_LINUX_MOUNT_RE.match(line) for line in lines):
        pattern = _LINUX_MOUNT_RE
    elif any(_BSD_MOUNT_RE.match(line) for line in lines):
        pattern = _BSD_MOUNT_RE
    elif any(_AIX_MOUNT_RE.match(line) for line in lines):
        # AIX has a couple header lines for some reason
        pattern = _AIX_MOUNT_RE
    else:
        return []

    results: list[dict[str, str]] = []
    for line in lines:
        if not (match := pattern.match(line)):
            continue

        if pattern is _LINUX_MOUNT_RE:
            results.append(match.groupdict())
        elif pattern == _BSD_MOUNT_RE:
            # the group containing fstype is comma separated, and may include whitespace
            fields = match.groupdict()
            parts = _re.split(r"\s*,\s*", match.group("fstype"), 1)
            if len(parts) == 1:
                fields["fstype"] = parts[0]
            else:
                fields.update({"fstype": parts[0], "options": parts[1]})
            results.append(fields)
        elif pattern == _AIX_MOUNT_RE:
            fields = match.groupdict()
            device = fields.pop("mounted")
            node = fields.pop("node")
            if node:
                device = f"{node}:{device}"
            fields["device"] = device
            results.append(fields)

    return results


def _list_fstab_entries(lines: list[str]) -> list[dict[str, str]]:
    """List dictionaries from https://man7.org/linux/man-pages/man5/fstab.5.html."""
    entries: list[dict[str, str]] = []
    for line in lines:
        if not (line := line.strip()) or line.startswith("#"):
            continue
        fields = [_replace_octal_escapes(field) for field in line.split()]
        entries.append({
            "device": fields[0],
            "mount": fields[1],
            "fstype": fields[2],
            "options": fields[3],
        })
        with _suppress(IndexError):
            # the last two fields are optional
            entries[-1]["dump"] = fields[4]
            entries[-1]["passno"] = fields[5]
    return entries


def _list_vfstab_entries(lines: list[str]) -> list[dict[str, str]]:
    """List dictionaries from /etc/vfstab https://docs.oracle.com/cd/E36784_01/html/E36882/vfstab-4.html."""
    return [
        {
            "device": fields[0],
            "device_to_fsck": fields[1],
            "mount": fields[2],
            "fstype": fields[3],
            "passno": fields[4],
            "mount_at_boot": fields[5],
            "options": fields[6],
        }
        for line in lines
        if line.strip() and not line.strip().startswith("#")
        for fields in [line.split()]
    ]


def _list_aix_filesystem_entries(lines: list[str]) -> list[dict[str, str | dict[str, str]]]:
    """List dictionaries from /etc/filesystems https://www.ibm.com/docs/hu/aix/7.2?topic=files-filesystems-file."""
    # AIX comments start with *
    lines = [line for line in lines if not line.startswith("*")]

    results: list[dict[str, str | dict[str, str]]] = []
    for stanza in _re.split(r"\n\s*\n", "\n".join(lines)):
        stanza_lines = stanza.splitlines()
        header = stanza_lines.pop(0).strip()
        if any("=" not in line for line in stanza_lines):
            # Expected for Linux, return an empty list since this doesn't appear to be AIX /etc/filesystems
            results = []
            break

        mount_attrs: dict[str, str] = {
            mount_attr.strip().rstrip(): mount_attr_value.strip().rstrip()
            for line in stanza_lines
            for mount_attr, mount_attr_value in [line.split("=", 1)]
        }

        device = ""
        if "nodename" in mount_attrs:
            device = mount_attrs["nodename"]
        if "dev" in mount_attrs:
            if device:
                device += ":"
            device += mount_attrs["dev"]

        results.append({
            "mount": header[:-1],  # snip trailing :
            "fstype": mount_attrs.get("vfs") or "unknown",
            "device": device or "unknown",
            # return attrs as a value since it contains "mount" with a different value (automatic|true|false|removable|readonly)
            "attributes": mount_attrs,
        })
    return results


def _list_mnttab_entries(lines: list[str]) -> list[dict[str, str]]:
    """List dictionaries from /etc/mnttab columns https://docs.oracle.com/cd/E36784_01/html/E36882/mnttab-4.html."""
    if not any(len(fields[4]) == 10 for line in lines for fields in [line.split()]):
        # best effort to distinguish between mnttab timestamp and mtab dump fields
        # if none of these look like a UNIX timestamp, assume it's the latter
        # TODO: check any are a valid datetime.date.fromtimestamp for good measure, or is there a better approach?
        return []
    return [
        {
            "device": fields[0],
            "mount": fields[1],
            "fstype": fields[2],
            "options": fields[3],
            "time": fields[4],
        }
        for line in lines
        for fields in [line.split()]
    ]


def _get_mounts_by_source(module: _AnsibleModule):
    """Enumerate the requested sources and return a dictionary containing the parsed sources."""
    sources: list[str] = []
    use_mount_bin_explicit = False
    for source in module.params["sources"]:
        if not source:
            module.fail_json(msg="sources contains an empty string")

        if source in {"static", "all"}:
            sources.extend(_STATIC_SOURCES)
        if source in {"dynamic", "all"}:
            sources.extend(_DYNAMIC_SOURCES)

        if source == module.params["mount_binary"]:
            use_mount_bin_explicit = True
        elif source not in {"static", "dynamic", "all"}:
            sources.append(source)

    if len(set(sources)) < len(sources):
        module.warn(f"mount_facts option 'sources' contains duplicate entries, repeat sources will be ignored: {sources}")

    collected = {}
    for file in sources:
        if file in collected:
            continue
        if not (lines := _get_file_content(file, "").splitlines()):
            continue

        for list_mount_func in [_list_vfstab_entries, _list_mnttab_entries, _list_fstab_entries, _list_aix_filesystem_entries]:
            try:
                mounts = list_mount_func(lines)
            except IndexError:
                continue
            if mounts:
                collected[file] = mounts
                break
        else:
            module.debug(f"mount_facts source {file} exists, but contains an unsupported format.")

    mount_binary = module.params["mount_binary"]
    use_mount_bin_implicit = set(sources).intersection(_DYNAMIC_SOURCES) and not any(collected.get(src, []) for src in _DYNAMIC_SOURCES) and mount_binary
    if use_mount_bin_explicit or use_mount_bin_implicit:
        stdout = _run_mount_bin(module, mount_binary)
        mounts = _list_mounts_from_mount_stdout(stdout)
        if mounts:
            collected[mount_binary] = mounts

    return collected


def _get_mount_facts(module: _AnsibleModule, uuids: dict, udevadm_uuid: _Callable) -> dict[str, dict[str, str | dict[str, str]]]:
    """List and filter mounts, returning a dictionary containing mount points as the keys (last listed wins)."""
    seconds = module.params["timeout"]
    on_timeout = module.params["on_timeout"]

    facts = {}
    for source, mounts in _get_mounts_by_source(module).items():
        for fields in mounts:
            device = fields["device"]
            fstype = fields["fstype"]

            if not any(_fnmatch(device, pattern) for pattern in module.params["devices"]):
                continue
            if not any(_fnmatch(fstype, pattern) for pattern in module.params["fstypes"]):
                continue

            mount = fields["mount"]

            timed_func = _timeout.timeout(seconds, f"Timed out getting mount size for mount {mount} (type {fstype})")(_get_mount_size)
            if mount_size := _handle_timeout(module)(timed_func)(mount):
                fields.update(mount_size)

            timed_func = _timeout.timeout(seconds, f"Timed out getting uuid for mount {mount} (type {fstype})")(udevadm_uuid)
            uuid = uuids.get(device, _handle_timeout(module)(timed_func)(device))

            facts[mount] = {"info": fields, "uuid": uuid or "N/A", "source": source}
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
