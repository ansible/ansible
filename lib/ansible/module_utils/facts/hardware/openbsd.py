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

import re
import time

from ansible.module_utils._text import to_text

from ansible.module_utils.facts.hardware.base import Hardware, HardwareCollector
from ansible.module_utils.facts import timeout

from ansible.module_utils.facts.utils import get_file_content, get_mount_size
from ansible.module_utils.facts.sysctl import get_sysctl


class OpenBSDHardware(Hardware):
    """
    OpenBSD-specific subclass of Hardware. Defines memory, CPU and device facts:
    - memfree_mb
    - memtotal_mb
    - swapfree_mb
    - swaptotal_mb
    - processor (a list)
    - processor_cores
    - processor_count
    - processor_speed
    - uptime_seconds

    In addition, it also defines number of DMI facts and device facts.
    """
    platform = 'OpenBSD'

    def populate(self, collected_facts=None):
        hardware_facts = {}
        self.sysctl = get_sysctl(self.module, ['hw'])

        hardware_facts.update(self.get_processor_facts())
        hardware_facts.update(self.get_memory_facts())
        hardware_facts.update(self.get_device_facts())
        hardware_facts.update(self.get_dmi_facts())
        hardware_facts.update(self.get_uptime_facts())

        # storage devices notorioslly prone to hang/block so they are under a timeout
        try:
            hardware_facts.update(self.get_mount_facts())
        except timeout.TimeoutError:
            pass

        return hardware_facts

    @timeout.timeout()
    def get_mount_facts(self):
        mount_facts = {}

        mount_facts['mounts'] = []
        fstab = get_file_content('/etc/fstab')
        if fstab:
            for line in fstab.splitlines():
                if line.startswith('#') or line.strip() == '':
                    continue
                fields = re.sub(r'\s+', ' ', line).split()
                if fields[1] == 'none' or fields[3] == 'xx':
                    continue
                mount_statvfs_info = get_mount_size(fields[1])
                mount_info = {'mount': fields[1],
                              'device': fields[0],
                              'fstype': fields[2],
                              'options': fields[3]}
                mount_info.update(mount_statvfs_info)
                mount_facts['mounts'].append(mount_info)
        return mount_facts

    def get_memory_facts(self):
        memory_facts = {}
        # Get free memory. vmstat output looks like:
        #  procs    memory       page                    disks    traps          cpu
        #  r b w    avm     fre  flt  re  pi  po  fr  sr wd0 fd0  int   sys   cs us sy id
        #  0 0 0  47512   28160   51   0   0   0   0   0   1   0  116    89   17  0  1 99
        rc, out, err = self.module.run_command("/usr/bin/vmstat")
        if rc == 0:
            memory_facts['memfree_mb'] = int(out.splitlines()[-1].split()[4]) // 1024
            memory_facts['memtotal_mb'] = int(self.sysctl['hw.usermem']) // 1024 // 1024

        # Get swapctl info. swapctl output looks like:
        # total: 69268 1K-blocks allocated, 0 used, 69268 available
        # And for older OpenBSD:
        # total: 69268k bytes allocated = 0k used, 69268k available
        rc, out, err = self.module.run_command("/sbin/swapctl -sk")
        if rc == 0:
            swaptrans = {ord(u'k'): None,
                         ord(u'm'): None,
                         ord(u'g'): None}
            data = to_text(out, errors='surrogate_or_strict').split()
            memory_facts['swapfree_mb'] = int(data[-2].translate(swaptrans)) // 1024
            memory_facts['swaptotal_mb'] = int(data[1].translate(swaptrans)) // 1024

        return memory_facts

    def get_uptime_facts(self):
        # On openbsd, we need to call it with -n to get this value as an int.
        sysctl_cmd = self.module.get_bin_path('sysctl')
        cmd = [sysctl_cmd, '-n', 'kern.boottime']

        rc, out, err = self.module.run_command(cmd)

        if rc != 0:
            return {}

        kern_boottime = out.strip()
        if not kern_boottime.isdigit():
            return {}

        return {
            'uptime_seconds': int(time.time() - int(kern_boottime)),
        }

    def get_processor_facts(self):
        cpu_facts = {}
        processor = []
        for i in range(int(self.sysctl['hw.ncpuonline'])):
            processor.append(self.sysctl['hw.model'])

        cpu_facts['processor'] = processor
        # The following is partly a lie because there is no reliable way to
        # determine the number of physical CPUs in the system. We can only
        # query the number of logical CPUs, which hides the number of cores.
        # On amd64/i386 we could try to inspect the smt/core/package lines in
        # dmesg, however even those have proven to be unreliable.
        # So take a shortcut and report the logical number of processors in
        # 'processor_count' and 'processor_cores' and leave it at that.
        cpu_facts['processor_count'] = self.sysctl['hw.ncpuonline']
        cpu_facts['processor_cores'] = self.sysctl['hw.ncpuonline']

        return cpu_facts

    def get_device_facts(self):
        device_facts = {}
        devices = []
        devices.extend(self.sysctl['hw.disknames'].split(','))
        device_facts['devices'] = devices

        return device_facts

    def get_dmi_facts(self):
        dmi_facts = {}
        # We don't use dmidecode(8) here because:
        # - it would add dependency on an external package
        # - dmidecode(8) can only be ran as root
        # So instead we rely on sysctl(8) to provide us the information on a
        # best-effort basis. As a bonus we also get facts on non-amd64/i386
        # platforms this way.
        sysctl_to_dmi = {
            'hw.product': 'product_name',
            'hw.version': 'product_version',
            'hw.uuid': 'product_uuid',
            'hw.serialno': 'product_serial',
            'hw.vendor': 'system_vendor',
        }

        for mib in sysctl_to_dmi:
            if mib in self.sysctl:
                dmi_facts[sysctl_to_dmi[mib]] = self.sysctl[mib]

        return dmi_facts


class OpenBSDHardwareCollector(HardwareCollector):
    _fact_class = OpenBSDHardware
    _platform = 'OpenBSD'
