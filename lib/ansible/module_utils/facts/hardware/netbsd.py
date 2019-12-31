# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re

from ansible.module_utils.six.moves import reduce

from ansible.module_utils.facts.hardware.base import Hardware, HardwareCollector
from ansible.module_utils.facts.timeout import TimeoutError, timeout

from ansible.module_utils.facts.utils import get_file_content, get_file_lines, get_mount_size
from ansible.module_utils.facts.sysctl import get_sysctl


class NetBSDHardware(Hardware):
    """
    NetBSD-specific subclass of Hardware.  Defines memory and CPU facts:
    - memfree_mb
    - memtotal_mb
    - swapfree_mb
    - swaptotal_mb
    - processor (a list)
    - processor_cores
    - processor_count
    - devices
    """
    platform = 'NetBSD'
    MEMORY_FACTS = ['MemTotal', 'SwapTotal', 'MemFree', 'SwapFree']

    def populate(self, collected_facts=None):
        hardware_facts = {}
        self.sysctl = get_sysctl(self.module, ['machdep'])
        cpu_facts = self.get_cpu_facts()
        memory_facts = self.get_memory_facts()

        mount_facts = {}
        try:
            mount_facts = self.get_mount_facts()
        except TimeoutError:
            pass

        dmi_facts = self.get_dmi_facts()
        device_facts = self.get_device_facts()

        hardware_facts.update(cpu_facts)
        hardware_facts.update(memory_facts)
        hardware_facts.update(mount_facts)
        hardware_facts.update(dmi_facts)
        hardware_facts.update(device_facts)

        return hardware_facts

    def get_cpu_facts(self):
        cpu_facts = {}

        i = 0
        physid = 0
        sockets = {}
        if not os.access("/proc/cpuinfo", os.R_OK):
            return cpu_facts
        cpu_facts['processor'] = []
        for line in get_file_lines("/proc/cpuinfo"):
            data = line.split(":", 1)
            key = data[0].strip()
            # model name is for Intel arch, Processor (mind the uppercase P)
            # works for some ARM devices, like the Sheevaplug.
            if key == 'model name' or key == 'Processor':
                if 'processor' not in cpu_facts:
                    cpu_facts['processor'] = []
                cpu_facts['processor'].append(data[1].strip())
                i += 1
            elif key == 'physical id':
                physid = data[1].strip()
                if physid not in sockets:
                    sockets[physid] = 1
            elif key == 'cpu cores':
                sockets[physid] = int(data[1].strip())
        if len(sockets) > 0:
            cpu_facts['processor_count'] = len(sockets)
            cpu_facts['processor_cores'] = reduce(lambda x, y: x + y, sockets.values())
        else:
            cpu_facts['processor_count'] = i
            cpu_facts['processor_cores'] = 'NA'

        return cpu_facts

    def get_memory_facts(self):
        memory_facts = {}
        if not os.access("/proc/meminfo", os.R_OK):
            return memory_facts
        for line in get_file_lines("/proc/meminfo"):
            data = line.split(":", 1)
            key = data[0]
            if key in NetBSDHardware.MEMORY_FACTS:
                val = data[1].strip().split(' ')[0]
                memory_facts["%s_mb" % key.lower()] = int(val) // 1024

        return memory_facts

    @timeout()
    def get_mount_facts(self):
        mount_facts = {}

        mount_facts['mounts'] = []
        fstab = get_file_content('/etc/fstab')

        if not fstab:
            return mount_facts

        for line in fstab.splitlines():
            if line.startswith('#') or line.strip() == '':
                continue
            fields = re.sub(r'\s+', ' ', line).split()
            mount_statvfs_info = get_mount_size(fields[1])
            mount_info = {'mount': fields[1],
                          'device': fields[0],
                          'fstype': fields[2],
                          'options': fields[3]}
            mount_info.update(mount_statvfs_info)
            mount_facts['mounts'].append(mount_info)
        return mount_facts

    def get_dmi_facts(self):
        dmi_facts = {}
        # We don't use dmidecode(8) here because:
        # - it would add dependency on an external package
        # - dmidecode(8) can only be ran as root
        # So instead we rely on sysctl(8) to provide us the information on a
        # best-effort basis. As a bonus we also get facts on non-amd64/i386
        # platforms this way.
        sysctl_to_dmi = {
            'machdep.dmi.system-product': 'product_name',
            'machdep.dmi.system-version': 'product_version',
            'machdep.dmi.system-uuid': 'product_uuid',
            'machdep.dmi.system-serial': 'product_serial',
            'machdep.dmi.system-vendor': 'system_vendor',
        }

        for mib in sysctl_to_dmi:
            if mib in self.sysctl:
                dmi_facts[sysctl_to_dmi[mib]] = self.sysctl[mib]

        return dmi_facts

    def get_device_facts(self):
        device_facts = {}
        device_facts['devices'] = {}
        drives = re.compile(r'(^ld?\d+|^sd\d+|^wd\d+)')
        dmesgboot = get_file_content('/var/run/dmesg.boot')
        if not dmesgboot:
            return device_facts
        for line in dmesgboot.splitlines():
            if line:
                words = line.strip().split()
                if drives.match(line):
                    disk = words[0].strip(":")
                    if words[1] == "at":
                        if disk not in device_facts['devices']:
                            device_facts['devices'][disk] = {}
                        if "host" not in device_facts['devices'][disk]:
                            device_facts['devices'][disk]["host"] = words[2]
                    elif words[1].startswith("<") and words[-1].endswith(">"):
                        if disk not in device_facts['devices']:
                            device_facts['devices'][disk] = {}
                        device_facts['devices'][disk]["model"] = " ".join(words[1:]).strip("<").strip(">")
                    elif words[-1] == "sectors":
                        if disk not in device_facts['devices']:
                            device_facts['devices'][disk] = {}
                        device_facts['devices'][disk]["size"] = words[1] + " " + words[2].strip(",")
                        device_facts['devices'][disk]["vendor"] = ""
                        if "host" not in device_facts['devices'][disk]:
                            device_facts['devices'][disk]["host"] = ""
                        if "model" not in device_facts['devices'][disk]:
                            device_facts['devices'][disk]["model"] = ""
                        device_facts['devices'][disk]["sectors"] = words[12]
                        device_facts['devices'][disk]["sectorsize"] = int(words[9])
                        device_facts['devices'][disk]["partitions"] = {}
                        rc, out, err = self.module.run_command(["/sbin/disklabel", "-A", disk])
                        for pline in out.splitlines():
                            if pline:
                                pwords = pline.strip().split()
                                if pwords[0] == "bytes/sector:":
                                    device_facts['devices'][disk]["sectorsize"] = int(pwords[-1])
                                elif pwords[0] == "total" and pwords[1] == "sectors:":
                                    device_facts['devices'][disk]["sectors"] = pwords[-1]
                                    device_facts['devices'][disk]["size"] = str(int(int(pwords[-1]) * int(device_facts['devices'][disk]["sectorsize"]) / 1024 / 1024)) + " MB"
                                elif pline[0] == " ":
                                    partition = disk + pwords[0].strip(":")
                                    device_facts['devices'][disk]["partitions"][partition] = {}
                                    device_facts['devices'][disk]["partitions"][partition]["sectors"] = pwords[1]
                                    device_facts['devices'][disk]["partitions"][partition]["sectorsize"] = device_facts['devices'][disk]["sectorsize"]
                                    device_facts['devices'][disk]["partitions"][partition]["size"] = pwords[1]
                                    device_facts['devices'][disk]["partitions"][partition]["start"] = pwords[2]
                                    device_facts['devices'][disk]["partitions"][partition]["fstype"] = pwords[3]
        return device_facts


class NetBSDHardwareCollector(HardwareCollector):
    _fact_class = NetBSDHardware
    _platform = 'NetBSD'
