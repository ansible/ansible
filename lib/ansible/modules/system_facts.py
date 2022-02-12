#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, Ladislav Cabelka <@ibt23sec5>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
module: system_facts

short_description: Detailed information about host state and configuration

version_added: 0.0.1

description:
  - returns detailed information about host configuration
  - could be used for instantaneous informations like:
     - CPU usage
     - memory usage
     - disk usage
     - network connections
     - running processes including children

author: Ladislav Cabelka (@ibt23sec5)

attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
  facts:
    support: full
  platform:
    platforms: posix

requirements:
  - psutil

options:

  subsets:
    description:
      - List of available subsets
      - By default returns all subsets
    type: list
    required: false
    choices:
      - boot_time
      - cpu_count
      - cpu_freq
      - cpu_percent
      - cpu_stats
      - cpu_times
      - cpu_times_percent
      - disk_io_counters
      - disk_partitions
      - disk_usage
      - hosts
      - net_connections
      - net_if_addrs
      - net_if_stats
      - net_io_counters
      - pids
      - resolv_conf
      - sensors_battery
      - sensors_fans
      - sensors_temperatures
      - swap_memory
      - users
      - virtual_memory
  pid_columns:
    description:
      - List of columns for B(pids) subset
    type: list
    default:
      - pid
      - name
      - username
    required: false
    choices:
      - children
      - cpu_affinity
      - cwd
      - threads
      - username
      - environ
      - uids
      - exe
      - memory_full_info
      - connections
      - cpu_percent
      - open_files
      - memory_percent
      - cmdline
      - name
      - num_threads
      - io_counters
      - nice
      - num_ctx_switches
      - terminal
      - status
      - cpu_times
      - create_time
      - gids
      - ppid
      - ionice
      - cpu_num
      - pid
      - memory_info
      - num_fds
      - memory_maps

  net_connections_kind:
    description:
      - Filters connection types related to B(net_connections) subset
    type: list
    choices:
      - inet
      - inet4
      - inet6
      - tcp
      - tcp4
      - tcp6
      - udp
      - udp4
      - udp6
      - unix
      - all
    default: inet
    required: false
"""

EXAMPLES = r"""
# Return all system facts
- name: Get all system facts
  ansible.builtin.system_facts:

# Returns only cpu_percent and cpu_times subsets
- name: Get CPU metrics
  ansible.builtin.system_facts:
    subsets:
      - cpu_percent
      - cpu_times
"""

RETURN = r"""
ansible_facts:
  description: Facts to add to ansible_facts.
  returned: always
  type: complex
  contains:
    system:
      description: colection of specified or all defined subsets
      returned: always
      type: dict
      contains:
        boot_time:
          description: Server uptime.
          returned: when explicitely specified in B(subsets) field or B(subsets) empty
          type: int
        cpu_count:
          description: Number of logical CPUs.
          returned: when explicitely specified in B(subsets) field or B(subsets) empty
          type: int
        cpu_freq:
          description: CPU frequency including current, min and max frequencies expressed in Mhz.
          returned: when explicitely specified in B(subsets) field or B(subsets) empty
          type: dict
          contains:
            current:
              description: Current frequency
              returned: always
              type: float
            min:
              description: Minimal frequency
              returned: always
              type: float
            max:
              description: Maximal frequency
              returned: always
              type: float
        cpu_freq_percpu:
          description: Same as B(cpu_freq) but per logical CPU.
          returned: when explicitely specified in B(subsets) field or B(subsets) empty
          type: list
        cpu_percent:
          description: CPU utilization as a percentage.
          returned: when explicitely specified in B(subsets) field or B(subsets) empty
          type: float
        cpu_stats:
          description: CPU statistics.
          returned: when explicitely specified in B(subsets) field or B(subsets) empty
          type: dict
          contains:
            ctx_switches:
              description: number of context switches (voluntary + involuntary) since boot.
              returned: always
              type: int
            interrupts:
              description: number of interrupts since boot.
              returned: always
              type: int
            soft_interrupts:
              description: number of software interrupts since boot. Always set to 0 on Windows and SunOS.
              returned: always
              type: int
            syscalls:
              description: number of system calls since boot. Always set to 0 on Linux.
              returned: always
              type: int
        cpu_times:
          description: CPU times.
          returned: when explicitely specified in B(subsets) field or B(subsets) empty
          type: dict
          contains:
            nice:
              description: time spent by niced (prioritized) processes executing in user mode; on Linux this also includes guest_nice time
              returned: only on POSIX systems
              type: float
            iowait:
              description: time spent waiting for I/O to complete. This is not accounted in idle time counter.
              returned: only on Linux
              type: float
            irq:
              description: time spent for servicing hardware interrupts
              returned: only on Linux or BSD
              type: float
            softirq:
              description: time spent for servicing software interrupts
              returned: only on Linux
              type: float
            steal:
              description: time spent by other operating systems running in a virtualized environment
              returned: only on Linux
              type: float
            guest:
              description: time spent running a virtual CPU for guest operating systems under the control of the Linux kernel
              returned: only on Linux
              type: float
            guest_nice:
              description: time spent running a niced guest (virtual CPU for guest operating systems under the control of the Linux kernel)
              returned: only on Linux
              type: float
            interrupt:
              description: time spent for servicing hardware interrupts ( similar to “irq” on UNIX)
              returned: only on Windows
              type: float
            dpc:
              description: time spent servicing deferred procedure calls (DPCs); DPCs are interrupts that run at a lower priority than standard interrupts.
              returned: only on Windows
              type: float
        cpu_times_percent:
          description: CPU times in percent.
          returned: when explicitely specified in B(subsets) field or B(subsets) empty
          type: dict
        disk_io_counters_perdisk:
          description: system-wide I/O statistics per disk.
          returned: when explicitely specified in B(subsets) field or B(subsets) empty
          type: dict
          contains:
            read_count:
              description: number of reads
              returned: always
              type: int
            write_count:
              description: number of writes
              returned: always
              type: int
            read_bytes:
              description: number of bytes read
              returned: always
              type: int
            write_bytes:
              description: number of bytes written
              returned: always
              type: int
            read_time:
              description: time spent reading from disk (in milliseconds)
              returned: always except NetBSD and OpenBSD
              type: int
            write_time:
              description: time spent writing to disk (in milliseconds)
              returned: always except NetBSD and OpenBSD
              type: int
            busy_time:
              description: time spent doing actual I/Os (in milliseconds)
              returned: only Linux or FreeBSD
              type: int
            read_merged_count
              description: number of merged reads
              returned: only Linux
              type: int
            write_merged_count:
              description: number of merged writes
              returned: only Linux
              type: int
        disk_partitions_all:
          description: All mounted partitions.
          returned: when explicitely specified in B(subsets) field or B(subsets) empty
          type: list
          contains:
            device:
              description: the device path (e.g. "/dev/hda1"). On Windows this is the drive letter (e.g. "C:\\").
              returned: always
              type: str
            mountpoint:
              description: the mount point path (e.g. "/"). On Windows this is the drive letter (e.g. "C:\\").
              returned: always
              type: str
            fstype:
              description: the partition filesystem (e.g. "ext3" on UNIX or "NTFS" on Windows).
              returned: always
              type: str
            opts:
              description: a comma-separated string indicating different mount options for the drive/partition. Platform-dependent.
              returned: always
              type: str
            maxfile:
              description: the maximum length a file name can have.
              returned: always
              type: int
            maxpath:
              description: the maximum length a path name (directory name + base file name) can have.
               returned: always
              type: int
        disk_usage:
          description: Disk usage per partition.
          returned: when explicitely specified in B(subsets) field or B(subsets) empty
          type: dict
          contains:
            total:
              returned: always
              type: int
            used:
              returned: always
              type: int
            free:
              returned: always
              type: int
            percent:
              returned: always
              type: int
        hosts:
          description: Shows the content of /etc/hosts file as a dict.
          returned: when explicitely specified in B(subsets) field or B(subsets) empty (only POSIX)
          type: dict
        net_connections:
          description:
            - netstat-like list of socket connections.
            - The type of connection depends on parameter B(net_connections_kind)
          returned: when explicitely specified in B(subsets) field or B(subsets) empty
          type: list
          contains:
            family:
              description: address kind
              type: str
              returned: always
            laddr_ip:
              description: local IP address
              type: str
              returned: always
            laddr_port:
              description: local port
              type: int
              returned: always
            raddr_ip:
              description: remote IP address
              type: str
              returned: always
            raddr_port:
              description: remote port
              type: int
              returned: always
            type:
              description: the address type, either SOCK_STREAM, SOCK_DGRAM or SOCK_SEQPACKET.
              type: str
              returned: always
            fd:
              description: file descriptor
              type: int
              returned: always
            pid:
              description: process ID
              type: int
              returned: always
            status:
              description: socket status
              type: str
              returned: always
        net_if_addrs:
          description: List of addresses per NIC
          returned: when explicitely specified in B(subsets) field or B(subsets) empty
          type: dict
          contains:
            family:
              description: the address family, either AF_INET or AF_INET6 or psutil.AF_LINK, which refers to a MAC address.
              type: str
              returned: always
            address:
              description: the primary NIC IP address
              type: str
              returned: always
            netmask:
              description: the netmask address
              type: str
              returned: if exists
            broadcast:
              description: the broadcast address
              type: str
              returned: if exists
            ptp:
              description: point to point
              type: str
              returned: if exists
        net_if_stats:
          description: Stats per NIC
          returned: when explicitely specified in B(subsets) field or B(subsets) empty
          type: dict
          contains:
            isup:
              description: indicates if NIC is up or not.
              type: bool
              returned: always
            duplex:
              description: the duplex communication type; it can be either NIC_DUPLEX_FULL, NIC_DUPLEX_HALF or NIC_DUPLEX_UNKNOWN
              type: int
              returned: always
            speed:
              description: the NIC speed expressed in mega bits (MB)
              type: int
              returned: always
            mtu:
              description: NIC’s maximum transmission unit expressed in bytes.
              type: int
              returned: always
        net_io_counters:
          description: I/O statistics per NIC
          type: dict
          returned: when explicitely specified in B(subsets) field or B(subsets) empty
          contains:
            bytes_sent:
              description: number of bytes sent
              type: int
              returned: always
            bytes_recv:
              description: number of bytes received
              type: int
              returned: always
            packets_sent:
              description: number of packets sent
              type: int
              returned: always
            packets_recv:
              description: number of packets received
              type: int
              returned: always
            errin:
              description: total number of errors while receiving
              type: int
              returned: always
            errout:
              description: total number of errors while sending
              type: int
              returned: always
            dropin:
              description: total number of incoming packets which were dropped
              type: int
              returned: always
            dropout:
              description: total number of outgoing packets which were dropped
              type: int
              returned: always
        pids:
          description:
            - List of current PIDs.
            - To get a complete list of culumns, refer please to the parameter B(pid_columns).
            - If column B(children) mentionned, the complete process tree will be returned.
            - Some column retrievals could have a heavy impact to the performance (i.e. B(children)).
          returned: when explicitely specified in B(subsets) field or B(subsets) empty
          type: list
        resolv_conf:
          description: Returns the content of /etc/resolv.conf file.
          returned: when explicitely specified in B(subsets) field or B(subsets) empty (only POSIX)
          type: dict
          contains:
            search:
              type: list
            nameserver:
              type: list
        sensors_battery:
          description: battery status information.
          type: dict
          returned: when explicitely specified in B(subsets) field or B(subsets) empty (only POSIX)
          contains:
            percent:
              description: Battery power left as a percentage.
              type: float
              returned: always
            secsleft:
              description:
                - An approximation how many seconds are left before the battery runs out of power.
                - 'POWER_TIME_UNLIMITED' if power cable plugged.
              type: float or str
              returned: always
            power_plugged:
              description: Returns true if power cable plugged.
              type: bool
              returned: always
        sensors_fans:
          description:
            - Returns hardware fan speed.
            - For more information about returned please refer to https://psutil.readthedocs.io/en/latest/#psutil.sensors_fans
          returned: always
          type: dict
        sensors_temperatures:
            - Returns hardware temperatures.
            - For more information about returned please refer to https://psutil.readthedocs.io/en/latest/#psutil.sensors_temperatures
          returned: always
          type: dict
        virtual_memory:
          description: Return statistics about system memory usage expressed in bytes.
          type: dict
          returned: when explicitely specified in B(subsets) field or B(subsets) empty.
          contains:
            used:
              returned: always
              type: int
            free:
              returned: always
              type: int
            active:
              returned: only POSIX
              type: int
            inactive:
              returned: only POSIX
              type: int
            buffers:
              returned: only POSIX
              type: int
            cached:
              returned: only POSIX
              type: int
            shared:
              returned: only POSIX
              type: int
            slab:
              returned: only POSIX
              type: int
            wired:
              returned: only POSIX
              type: int

        swap_memory:
          description: Return statistics about swap memory usage expressed in bytes.
          type: dict
          returned: when explicitely specified in B(subsets) field or B(subsets) empty.
          contains:
            used:
              returned: always
              type: int
            free:
              returned: always
              type: int
            percent:
              description: he percentage usage calculated as C((total - available) / total * 100).
              returned: always
              type: int
            sin:
              description: the number of bytes the system has swapped in from disk (cumulative).
              returned: only POSIX
              type: int
            sout:
              description: the number of bytes the system has swapped out from disk (cumulative).
              returned: only POSIX
              type: int
        users:
          description: Return users currently connected on the system.
          type: list
          returned: when explicitely specified in B(subsets) field or B(subsets) empty.
          contains:
            name:
              description: the name of the user.
              type: str
              returned: always
            terminal:
              description: the tty or pseudo-tty associated with the user, if any, else None.
              type: str
              returned: always
            host:
              description: the host name associated with the entry, if any.
              type: str
              returned: always
            started:
              description: the creation time expressed in seconds since the epoch.
              type: float
              returned: always
            pid:
              description:
                - The PID of the login process (like sshd, tmux, gdm-session-worker, ...).
                - On Windows and OpenBSD this is always set to None.
              type: int
              returned: always
"""

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule

import os
import psutil
import socket
import json

DEFAULT_PID_COLUMNS = ["pid", "name", "username"]
# columns containing structured objects needed to extract
PID_COLLECTIONS = ["cpu_times",
                   "gids",
                   "memory_full_info",
                   "memory_info",
                   "num_ctx_switches",
                   "uids",
                   "parent",
                   ]


def get_sock_type(num):
    names = [name for (name, value) in socket.SocketKind.__members__.items() if value == num]
    if len(names) == 1:
        return names[0]
    else:
        return num


def get_sock_family(num):
    names = [name for (name, value) in socket.AddressFamily.__members__.items() if value == num]
    if len(names) == 1:
        return names[0]
    else:
        return num


class AbstractFacts:
    """
    Basic construction of Facts instance.

    All methods not starting by '_' (and not named 'get') are considered as a subset
    referred by the same name.

    Example:

    class MyFacts(AbstractFacts):
        def my_file_content(self):
            return my_content

        def list_processes(self):
            return some_processes

    >>> facts = MyFacts()
    >>> facts.get()
    {"my_file_content": "content of my file", "list_processes": [1, 6521, 2124]}
    """
    def __init__(self, subsets, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.subsets = subsets

    def _subset_choices(self):
        for name in dir(self):
            if callable(getattr(self, name)) and not name.startswith("_") and name != "get":
                if not self.subsets or name in self.subsets:
                    yield name

    def get(self):
        return {name: getattr(self, name)() for name in self._subset_choices()}


class FileFacts(AbstractFacts):
    """ Facts from some important files"""

    @classmethod
    def hosts(self):
        if os.path.exists("/etc/hosts"):
            with open("/etc/hosts") as f:
                hosts = {}
                for line in [s.split() for s in f.readlines() if not s.strip().startswith("#")]:
                    key = line.pop(0)
                    hosts[key] = line
                return hosts

    @classmethod
    def resolv_conf(self):
        if os.path.exists("/etc/resolv.conf"):
            with open("/etc/resolv.conf") as f:
                entries = {}
                for line in [s.split() for s in f.readlines() if not s.strip().startswith("#")]:
                    key = line.pop(0)
                    if key not in entries:
                        entries[key] = []
                    entries[key].extend(line)
                return entries


class PsutilFacts(AbstractFacts):
    """
    Facts comming from `psutil` module with custom parsing of returned values.

    Almost all methods are named as original `psutil` functions.
    """
    def disk_usage(self):
        usage = {}
        for part in psutil.disk_partitions():
            line = psutil.disk_usage(part.mountpoint)
            usage[part.mountpoint] = dict(line._asdict())
        return usage

    def net_connections(self):
        kind = self.kwargs.get("net_connections_kind", None)
        if kind:
            connections = psutil.net_connections(kind)
        else:
            connections = psutil.net_connections()
        cnns = []
        for cnn in connections:
            line = {}
            if hasattr(cnn, "family"):
                line["family"] = cnn.family.name
            if hasattr(cnn, "laddr") and cnn.laddr:
                if isinstance(cnn.laddr, str):
                    line["laddr"] = cnn.laddr
                else:
                    line["laddr_ip"] = cnn.laddr.ip
                    line["laddr_port"] = cnn.laddr.port
            if hasattr(cnn, "raddr") and cnn.raddr:
                if isinstance(cnn.raddr, str):
                    line["raddr"] = cnn.raddr
                else:
                    line["raddr_ip"] = cnn.raddr.ip
                    line["raddr_port"] = cnn.raddr.port
            if hasattr(cnn, "type") and cnn.type:
                if isinstance(cnn.type, socket.SocketKind):
                    line["type"] = cnn.type.name
                else:
                    line["type"] = get_sock_type(cnn.type)
            line["fd"] = cnn.fd
            line["pid"] = cnn.pid
            line["status"] = cnn.status
            cnns.append(line)
        return cnns

    def net_if_addrs(self):
        ifs = {}
        for name, lines in psutil.net_if_addrs().items():
            ifs[name] = []
            for _line in lines:
                line = dict(_line._asdict())
                if isinstance(_line.family, socket.AddressFamily):
                    line['family'] = _line.family.name
                ifs[name].append(line)

        return ifs

    def sensors_battery(self):
        state = psutil.sensors_battery()
        if state.secsleft < 0:
            secsleft = state.secsleft.name
        else:
            secsleft = state.secsleft
        return {"secsleft": secsleft,
                "percent": state.percent,
                "power_plugged": state.power_plugged,
                }

    def pids(self):
        pid_columns = self.kwargs.get("pid_columns", None)
        if "children" in pid_columns:
            pid_columns.pop(pid_columns.index("children"))
            show_children = True
        else:
            show_children = False
        processes = psutil.process_iter(pid_columns)

        return self._pids(processes, pid_columns, show_children)

    def _pids(self, processes, pid_columns, show_children):
        result = []
        if not hasattr(processes, "__iter__"):
            return None
        for process in processes:
            ps = process.as_dict(pid_columns)
            for attr in list(set(pid_columns) & set(PID_COLLECTIONS)):
                # extract structured columns
                value = ps.pop(attr)
                if value:
                    ps[attr] = {c: getattr(value, c) for c in value._fields}
            if pid_columns and "threads" in pid_columns:
                threads = []
                for ln in ps.pop("threads"):
                    threads.append({c: getattr(ln, c) for c in ln._fields})
                ps["threads"] = threads
            if show_children and hasattr(process, "children"):
                children = self._pids(process.children(), pid_columns, show_children)
                if children:
                    ps["children"] = children
            result.append(ps)
        return result


class Subsets:
    """
    Static declarations of known `psutil` functions by format of returned value.

    Those declarations allows to use the generic code bellow in `GenericPsutilFacts`.
    Each mentionned function name with the `args` and `kwargs` specifications
    is classed by already known format of returned collection.
    """
    SINGLE = [("cpu_percent", [], {}),
              ("cpu_count", [], {}),
              ("boot_time", [], {}),
              ]
    DICT = [("cpu_times", [], {}),
            ("cpu_times_percent", [], {}),
            ("cpu_stats", [], {}),
            ("cpu_freq", [], {}),
            ("virtual_memory", [], {}),
            ("swap_memory", [], {}),
            ]

    LIST_DICT = [("cpu_freq", [], {"percpu": True}),
                 ("disk_partitions", [], {"all": True}),
                 ("users", [], {}),
                 ]
    DICT_DICT = [("net_io_counters", [], {"pernic": True}),
                 ("net_if_stats", [], {}),
                 ("disk_io_counters", [], {"perdisk": True})
                 ]
    DICT_LIST_DICT = [("sensors_temperatures", [], {}),
                      ("sensors_fans", [], {}),
                      ]


class GenericPsutilFacts(AbstractFacts):
    """
    Generic facts comming from `psutil` module.

    The overriden method `get` returns all subsets declared in the `Subsets` class.
    As the format of returned value is already known, still to call all functions
    by format of returned collection value.
    """
    def _single(self, name, *args, **kwargs):
        method = getattr(psutil, name)
        try:
            result = method(*args, **kwargs)
        except Exception:
            # do not break facts collecting
            # TODO: log something
            result = {}
        if args or kwargs:
            if args:
                name = "{}_{}".format(name, "_".join([k for k in args]))
            else:
                name = "{}_{}".format(name, "_".join([k for k in kwargs.keys()]))
        return name, result

    def _dict(self, name, *args, **kwargs):
        name, result = self._single(name, *args, **kwargs)
        return name, dict(result._asdict())

    def _list_dict(self, name, *args, **kwargs):
        name, result = self._single(name, *args, **kwargs)
        return name, [dict(r._asdict()) for r in result]

    def _dict_dict(self, name, *args, **kwargs):
        name, result = self._single(name, *args, **kwargs)
        return name, {n: dict(r._asdict()) for (n, r) in result.items()}

    def _dict_list_dict(self, name, *args, **kwargs):
        name, result = self._single(name, *args, **kwargs)
        return name, {n: [dict(line._asdict()) for line in lines] for (n, lines) in result.items()}

    def get(self):
        single_facts = {}
        dict_facts = {}
        list_dict_facts = {}
        dict_dict_facts = {}
        dict_list_dict_facts = {}
        for (name, args, kwargs) in Subsets.SINGLE:
            if not self.subsets or name in self.subsets:
                new_name, result = self._single(name, *args, **kwargs)
                single_facts[new_name] = result
        for (name, args, kwargs) in Subsets.DICT:
            if not self.subsets or name in self.subsets:
                new_name, result = self._dict(name, *args, **kwargs)
                dict_facts[new_name] = result
        for (name, args, kwargs) in Subsets.LIST_DICT:
            if not self.subsets or name in self.subsets:
                new_name, result = self._list_dict(name, *args, **kwargs)
                list_dict_facts[new_name] = result
        for (name, args, kwargs) in Subsets.DICT_DICT:
            if not self.subsets or name in self.subsets:
                new_name, result = self._dict_dict(name, *args, **kwargs)
                dict_dict_facts[new_name] = result
        for (name, args, kwargs) in Subsets.DICT_LIST_DICT:
            if not self.subsets or name in self.subsets:
                new_name, result = self._dict_list_dict(name, *args, **kwargs)
                dict_list_dict_facts[new_name] = result

        return {**single_facts,
                **dict_facts,
                **list_dict_facts,
                **dict_dict_facts,
                **dict_list_dict_facts}


def main():
    module_args = dict(subsets=dict(type="list", elements="str"),
                       pid_columns=dict(type="list",
                                        elements="str",
                                        default=DEFAULT_PID_COLUMNS
                                        ),
                       net_connections_kind=dict(type="str"),
                       )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    classes = [FileFacts, PsutilFacts, GenericPsutilFacts]

    facts = {}
    result = dict(changed=False, ansible_facts={"system": facts})

    try:
        for _class in classes:
            facts.update(_class(**module.params).get())
    except Exception as exc:
        module.warn("Facts collection failed: %s" % (to_text(exc)))
        module.fail_json(msg=to_text(exc))

    if module.check_mode:
        module.exit_json(**result)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
