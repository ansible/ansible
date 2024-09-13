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
    default: ~
    type: list
    elements: str
  fstypes:
    description: A list of fnmatch patterns to filter mounts by the type of the file system.
    default: ~
    type: list
    elements: str
  sources:
    description:
      - A list of sources used to determine the mounts. Missing file sources (or empty files) are skipped.
      - By default, mounts are retrieved from all of the standard locations, which have the predefined aliases V(all)/V(static)/V(dynamic).
      - V(all) contains V(static) and V(dynamic).
      - V(static) contains V(/etc/fstab), V(/etc/vfstab), and V(/etc/filesystems).
        Note that V(/etc/filesystems) is specific to AIX. The Linux file by this name has a different format/purpose and is ignored.
      - V(dynamic) contains V(/etc/mtab), V(/proc/mounts), and V(/etc/mnttab).
      - If any of the files in V(dynamic) are configured as sources and none found, the module will fall back to using the O(mount_binary).
        This allows platforms like BSD or AIX, which don't have an equivalent to V(/proc/mounts), to collect the current mounts by default.
        See the O(mount_binary) option to disable the fall back or configure a different executable.
      - The value of O(mount_binary) can be configured as a source, which will cause it to always execute.
        Depending on the other sources configured, this could be inefficient/redundant.
        For example, if V(/proc/mounts) and V(mount) are listed as O(sources), Linux hosts will retrieve the same mounts twice.
    default: ~
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
    type: float
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.facts import timeout as _timeout
from ansible.module_utils.facts.utils import get_mount_size, get_file_content

from contextlib import suppress
from dataclasses import astuple, dataclass
from fnmatch import fnmatch

import codecs
import datetime
import functools
import os
import re
import subprocess
import typing as t

STATIC_SOURCES = ["/etc/fstab", "/etc/vfstab", "/etc/filesystems"]
DYNAMIC_SOURCES = ["/etc/mtab", "/proc/mounts", "/etc/mnttab"]

# AIX and BSD don't have a file-based dynamic source, so the module also supports running a mount binary to collect these.
# Pattern for Linux, including OpenBSD and NetBSD
LINUX_MOUNT_RE = re.compile(r"^(?P<device>\S+) on (?P<mount>\S+) type (?P<fstype>\S+) \((?P<options>.+)\)$")
# Pattern for other BSD including FreeBSD, DragonFlyBSD, and MacOS
BSD_MOUNT_RE = re.compile(r"^(?P<device>\S+) on (?P<mount>\S+) \((?P<fstype>.+)\)$")
# Pattern for AIX, example in https://www.ibm.com/docs/en/aix/7.2?topic=m-mount-command
AIX_MOUNT_RE = re.compile(r"^(?P<node>\S*)\s+(?P<mounted>\S+)\s+(?P<mount>\S+)\s+(?P<fstype>\S+)\s+(?P<time>\S+\s+\d+\s+\d+:\d+)\s+(?P<options>.*)$")


@dataclass
class MountInfo:
    mount_point: str
    line: str
    fields: dict[str, str | int]


def replace_octal_escapes(value: str) -> str:
    return re.sub(r"(\\[0-7]{3})", lambda m: codecs.decode(m.group(0), "unicode_escape"), value)


@functools.lru_cache(maxsize=None)
def get_device_by_uuid(module: AnsibleModule, uuid : str) -> str | None:
    """Get device information by UUID."""
    blkid_output = None
    if (blkid_binary := module.get_bin_path("blkid")):
        cmd = [blkid_binary, "--uuid", uuid]
        with suppress(subprocess.CalledProcessError):
            blkid_output = handle_timeout(module)(subprocess.check_output)(cmd, text=True, timeout=module.params["timeout"])
    return blkid_output


@functools.lru_cache(maxsize=None)
def list_uuids_linux() -> list[str]:
    """List UUIDs from the system."""
    with suppress(OSError):
        return os.listdir("/dev/disk/by-uuid")
    return []


@functools.lru_cache(maxsize=None)
def run_lsblk(module : AnsibleModule) -> list[list[str]]:
    """Return device, UUID pairs from lsblk."""
    lsblk_output = ""
    if (lsblk_binary := module.get_bin_path("lsblk")):
        cmd = [lsblk_binary, "--list", "--noheadings", "--paths", "--output", "NAME,UUID", "--exclude", "2"]
        lsblk_output = subprocess.check_output(cmd, text=True, timeout=module.params["timeout"])
    return [line.split() for line in lsblk_output.splitlines() if len(line.split()) == 2]


@functools.lru_cache(maxsize=None)
def get_udevadm_device_uuid(module : AnsibleModule, device : str) -> str | None:
    """Fallback to get the device's UUID for lsblk <= 2.23 which doesn't have the --paths option."""
    udevadm_output = ""
    if (udevadm_binary := module.get_bin_path("udevadm")):
        cmd = [udevadm_binary, "info", "--query", "property", "--name", device]
        udevadm_output = subprocess.check_output(cmd, text=True, timeout=module.params["timeout"])
    uuid = None
    for line in udevadm_output.splitlines():
        # a snippet of the output of the udevadm command below will be:
        # ...
        # ID_FS_TYPE=ext4
        # ID_FS_USAGE=filesystem
        # ID_FS_UUID=57b1a3e7-9019-4747-9809-7ec52bba9179
        # ...
        if line.startswith("ID_FS_UUID="):
            uuid = line.split("=", 1)[1]
            break
    return uuid


def get_partition_uuid(module: AnsibleModule, partname : str) -> str | None:
    """Get the UUID of a partition by its name."""
    # TODO: NetBSD and FreeBSD can have UUIDs in /etc/fstab,
    # but none of these methods work (mount always displays the label though)
    for uuid in list_uuids_linux():
        dev = os.path.realpath(os.path.join("/dev/disk/by-uuid", uuid))  # type: ignore[arg-type]
        if partname == dev:
            return uuid
    for dev, uuid in handle_timeout(module, default=[])(run_lsblk)(module):
        if partname == dev:
            return uuid
    return handle_timeout(module)(get_udevadm_device_uuid)(module, partname)


def handle_timeout(module, default=None):
    """Decorator to catch timeout exceptions and handle failing, warning, and ignoring the timeout."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (subprocess.TimeoutExpired, _timeout.TimeoutError) as e:
                if module.params["on_timeout"] == "error":
                    module.fail_json(msg=str(e))
                elif module.params["on_timeout"] == "warn":
                    module.warn(str(e))
                return default
        return wrapper
    return decorator


def run_mount_bin(module: AnsibleModule, mount_bin: str) -> str:  # type: ignore # Missing return statement
    """Execute the specified mount binary with optional timeout."""
    mount_bin = module.get_bin_path(mount_bin, required=True)
    try:
        return handle_timeout(module, default="")(subprocess.check_output)(
            mount_bin, text=True, timeout=module.params["timeout"]
        )
    except subprocess.CalledProcessError as e:
        module.fail_json(msg=f"Failed to execute {mount_bin}: {str(e)}")


def get_mount_pattern(stdout: str):
    lines = stdout.splitlines()
    pattern = None
    if any(LINUX_MOUNT_RE.match(line) for line in lines):
        pattern = LINUX_MOUNT_RE
    elif any(BSD_MOUNT_RE.match(line) for line in lines):
        pattern = BSD_MOUNT_RE
    elif any(AIX_MOUNT_RE.match(line) for line in lines):
        pattern = AIX_MOUNT_RE
    return pattern


def gen_mounts_from_stdout(stdout: str) -> t.Iterable[MountInfo]:
    """List mount dictionaries from mount stdout."""
    if not (pattern := get_mount_pattern(stdout)):
        stdout = ""

    for line in stdout.splitlines():
        if not (match := pattern.match(line)):
            # AIX has a couple header lines for some reason
            # MacOS "map" lines are skipped (e.g. "map auto_home on /System/Volumes/Data/home (autofs, automounted, nobrowse)")
            # TODO: include MacOS lines
            continue

        mount = match.groupdict()["mount"]
        if pattern is LINUX_MOUNT_RE:
            mount_info = match.groupdict()
        elif pattern is BSD_MOUNT_RE:
            # the group containing fstype is comma separated, and may include whitespace
            mount_info = match.groupdict()
            parts = re.split(r"\s*,\s*", match.group("fstype"), 1)
            if len(parts) == 1:
                mount_info["fstype"] = parts[0]
            else:
                mount_info.update({"fstype": parts[0], "options": parts[1]})
        elif pattern is AIX_MOUNT_RE:
            mount_info = match.groupdict()
            device = mount_info.pop("mounted")
            node = mount_info.pop("node")
            if device and node:
                device = f"{node}:{device}"
            mount_info["device"] = device

        yield MountInfo(mount, line, mount_info)


def gen_fstab_entries(lines: list[str]) -> t.Iterable[MountInfo]:
    """Yield tuples from /etc/fstab https://man7.org/linux/man-pages/man5/fstab.5.html.

    Each tuple contains the mount point, line of origin, and the dictionary of the parsed line.
    """
    for line in lines:
        if not (line := line.strip()) or line.startswith("#"):
            continue
        fields = [replace_octal_escapes(field) for field in line.split()]
        mount_info: dict[str, str | int] = {
            "device": fields[0],
            "mount": fields[1],
            "fstype": fields[2],
            "options": fields[3],
        }
        with suppress(IndexError):
            # the last two fields are optional
            mount_info["dump"] = int(fields[4])
            mount_info["passno"] = int(fields[5])
        yield MountInfo(fields[1], line, mount_info)


def gen_vfstab_entries(lines: list[str]) -> t.Iterable[MountInfo]:
    """Yield tuples from /etc/vfstab https://docs.oracle.com/cd/E36784_01/html/E36882/vfstab-4.html.

    Each tuple contains the mount point, line of origin, and the dictionary of the parsed line.
    """
    for line in lines:
        if not line.strip() or line.strip().startswith("#"):
            continue
        fields = line.split()
        passno: str | int = fields[4]
        with suppress(ValueError):
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
        yield MountInfo(fields[2], line, mount_info)


def list_aix_filesystems_stanzas(lines: list[str]) -> list[list[str]]:
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


def gen_aix_filesystems_entries(lines: list[str]) -> t.Iterable[MountInfo]:
    """Yield tuples from /etc/filesystems https://www.ibm.com/docs/hu/aix/7.2?topic=files-filesystems-file.

    Each tuple contains the mount point, lines of origin, and the dictionary of the parsed lines.
    """
    for stanza in list_aix_filesystems_stanzas(lines):
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
        # arg-type: Argument 3 to "MountInfo" has incompatible type "dict[str, str]"; expected "dict[str, str | int]
        # why is this a problem here and not gen_mounts_from_stdout?
        yield MountInfo(mount, original, mount_info)  # type: ignore[arg-type]


def gen_mnttab_entries(lines: list[str]) -> t.Iterable[MountInfo]:
    """Yield tuples from /etc/mnttab columns https://docs.oracle.com/cd/E36784_01/html/E36882/mnttab-4.html.

    Each tuple contains the mount point, line of origin, and the dictionary of the parsed line.
    """
    if not any(len(fields[4]) == 10 for line in lines for fields in [line.split()]):
        raise ValueError
    for line in lines:
        fields = line.split()
        datetime.date.fromtimestamp(int(fields[4]))
        mount_info: dict[str, str | int] = {
            "device": fields[0],
            "mount": fields[1],
            "fstype": fields[2],
            "options": fields[3],
            "time": int(fields[4]),
        }
        yield MountInfo(fields[1], line, mount_info)


def gen_mounts_by_file(sources: list[str]):
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

        if not (lines := get_file_content(file, "").splitlines()):
            continue

        for gen_mounts in [gen_vfstab_entries, gen_mnttab_entries, gen_fstab_entries, gen_aix_filesystems_entries]:
            with suppress(IndexError, ValueError):
                yield from [(file, *astuple(mount_info)) for mount_info in gen_mounts(lines)]
                break


def get_file_sources(module: AnsibleModule) -> list[str]:
    """Return a list of filenames from the requested sources."""
    sources: list[str] = []
    for source in module.params["sources"] or ["all"]:
        if not source:
            module.fail_json(msg="sources contains an empty string")

        if source in {"static", "all"}:
            sources.extend(STATIC_SOURCES)
        if source in {"dynamic", "all"}:
            sources.extend(DYNAMIC_SOURCES)

        elif source not in {"static", "dynamic", "all", module.params["mount_binary"]}:
            sources.append(source)
    return sources


def gen_mounts_by_source(module: AnsibleModule):
    """Iterate over the sources and yield tuples containing the source, mount point, source line(s), and the parsed result."""
    sources = get_file_sources(module)

    if len(set(sources)) < len(sources):
        module.warn(f"mount_facts option 'sources' contains duplicate entries, repeat sources will be ignored: {sources}")

    collected = set()
    for mount_tuple in gen_mounts_by_file(sources):
        collected.add(mount_tuple[0])
        yield mount_tuple

    mount_binary = module.params["mount_binary"]
    explicit_mount_source = mount_binary and mount_binary in (module.params["sources"] or [])
    implicit_mount_source = mount_binary and set(sources).intersection(DYNAMIC_SOURCES) and not collected.intersection(DYNAMIC_SOURCES)
    if explicit_mount_source or implicit_mount_source:
        stdout = run_mount_bin(module, mount_binary)
        yield from [(mount_binary, *astuple(mount_info)) for mount_info in gen_mounts_from_stdout(stdout)]


def get_mount_facts(module: AnsibleModule):
    """List and filter mounts, returning a dictionary containing mount points as the keys (last listed wins)."""
    seconds = module.params["timeout"]

    # merge sources based on the mount point (last source wins)
    facts = {}
    for source, mount, origin, fields in gen_mounts_by_source(module):
        device = fields["device"]
        fstype = fields["fstype"]

        # Convert UUIDs in Linux /etc/fstab to device paths
        # TODO need similar for OpenBSD which lists UUIDS (without the UUID= prefix) in /etc/fstab, needs another approach though.
        uuid = None
        if device.startswith("UUID="):
            uuid = device.split("=", 1)[1]
            device = get_device_by_uuid(module, uuid) or device

        if not any(fnmatch(device, pattern) for pattern in module.params["devices"] or ["*"]):
            continue
        if not any(fnmatch(fstype, pattern) for pattern in module.params["fstypes"] or ["*"]):
            continue

        timed_func = _timeout.timeout(seconds, f"Timed out getting mount size for mount {mount} (type {fstype})")(get_mount_size)
        if mount_size := handle_timeout(module)(timed_func)(mount):
            fields.update(mount_size)

        if uuid is None:
            with suppress(subprocess.CalledProcessError):
                uuid = get_partition_uuid(module, device)

        fields.update({"ansible_context": {"source": source, "source_data": origin}, "uuid": uuid or "N/A"})
        facts[mount] = fields

    return facts


def get_argument_spec():
    """Helper returning the argument spec."""
    return dict(
        sources=dict(type="list", elements="str", default=None),
        mount_binary=dict(default="mount", type="raw"),
        devices=dict(type="list", elements="str", default=None),
        fstypes=dict(type="list", elements="str", default=None),
        timeout=dict(type="float"),
        on_timeout=dict(choices=["error", "warn", "ignore"], default="error"),
    )


def main():
    module = AnsibleModule(
        argument_spec=get_argument_spec(),
        supports_check_mode=True,
    )
    if (seconds := module.params["timeout"]) is not None and seconds <= 0:
        module.fail_json(msg="argument 'timeout' must be a positive integer or null, not {seconds}")
    if (mount_binary := module.params["mount_binary"]) is not None and not isinstance(mount_binary, str):
        module.fail_json(msg=f"argument 'mount_binary' must be a string or null, not {mount_binary}")

    mounts = get_mount_facts(module)
    module.exit_json(ansible_facts={"extended_mounts": mounts})


if __name__ == "__main__":
    main()
