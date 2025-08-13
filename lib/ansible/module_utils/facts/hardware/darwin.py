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


from __future__ import annotations

import struct
import time

from ansible.module_utils.facts.hardware.base import Hardware, HardwareCollector
from ansible.module_utils.facts.sysctl import get_sysctl


class DarwinHardware(Hardware):
    """
    Darwin-specific subclass of Hardware.  Defines memory and CPU facts:
    - processor
    - processor_cores
    - memtotal_mb
    - memfree_mb
    - model
    - osversion
    - osrevision
    - uptime_seconds
    """
    platform = 'Darwin'

    def populate(self, collected_facts=None):
        hardware_facts = {}

        self.sysctl = get_sysctl(self.module, ['hw', 'machdep', 'kern', 'hw.model'])
        mac_facts = self.get_mac_facts()
        cpu_facts = self.get_cpu_facts()
        memory_facts = self.get_memory_facts()
        uptime_facts = self.get_uptime_facts()

        hardware_facts.update(mac_facts)
        hardware_facts.update(cpu_facts)
        hardware_facts.update(memory_facts)
        hardware_facts.update(uptime_facts)

        return hardware_facts

    def get_system_profile(self):
        rc, out, err = self.module.run_command(["/usr/sbin/system_profiler", "SPHardwareDataType"])
        if rc != 0:
            return dict()
        system_profile = dict()
        for line in out.splitlines():
            if ': ' in line:
                (key, value) = line.split(': ', 1)
                system_profile[key.strip()] = ' '.join(value.strip().split())
        return system_profile

    def get_mac_facts(self):
        mac_facts = {}
        if 'hw.model' in self.sysctl:
            mac_facts['model'] = mac_facts['product_name'] = self.sysctl['hw.model']
        mac_facts['osversion'] = self.sysctl['kern.osversion']
        mac_facts['osrevision'] = self.sysctl['kern.osrevision']

        return mac_facts

    def get_cpu_facts(self):
        cpu_facts = {}
        if 'machdep.cpu.brand_string' in self.sysctl:  # Intel
            cpu_facts['processor'] = self.sysctl['machdep.cpu.brand_string']
            cpu_facts['processor_cores'] = self.sysctl['machdep.cpu.core_count']
        else:  # PowerPC
            system_profile = self.get_system_profile()
            cpu_facts['processor'] = '%s @ %s' % (system_profile['Processor Name'], system_profile['Processor Speed'])
            cpu_facts['processor_cores'] = self.sysctl['hw.physicalcpu']
        cpu_facts['processor_vcpus'] = self.sysctl.get('hw.logicalcpu') or self.sysctl.get('hw.ncpu') or ''

        return cpu_facts

    def get_memory_facts(self):
        memory_facts = {
            'memtotal_mb': int(self.sysctl['hw.memsize']) // 1024 // 1024,
            'memfree_mb': 0,
        }

        total_used = 0
        page_size = int(self.sysctl.get('hw.pagesize', 4096))

        vm_stat_command = self.module.get_bin_path('vm_stat')
        if vm_stat_command is None:
            return memory_facts

        if vm_stat_command:
            rc, out, err = self.module.run_command(vm_stat_command)
            if rc == 0:
                # Free = Total - (Wired + active + inactive)
                # Get a generator of tuples from the command output so we can later
                # turn it into a dictionary
                memory_stats = (line.rstrip('.').split(':', 1) for line in out.splitlines())

                # Strip extra left spaces from the value
                memory_stats = dict((k, v.lstrip()) for k, v in memory_stats)

                for k, v in memory_stats.items():
                    try:
                        memory_stats[k] = int(v)
                    except ValueError:
                        # Most values convert cleanly to integer values but if the field does
                        # not convert to an integer, just leave it alone.
                        pass

                if memory_stats.get('Pages wired down'):
                    total_used += memory_stats['Pages wired down'] * page_size
                if memory_stats.get('Pages active'):
                    total_used += memory_stats['Pages active'] * page_size
                if memory_stats.get('Pages inactive'):
                    total_used += memory_stats['Pages inactive'] * page_size

                memory_facts['memfree_mb'] = memory_facts['memtotal_mb'] - (total_used // 1024 // 1024)

        return memory_facts

    def get_uptime_facts(self):

        # On Darwin, the default format is annoying to parse.
        # Use -b to get the raw value and decode it.
        sysctl_cmd = self.module.get_bin_path('sysctl')
        if not sysctl_cmd:
            return {}

        cmd = [sysctl_cmd, '-b', 'kern.boottime']

        # We need to get raw bytes, not UTF-8.
        rc, out, err = self.module.run_command(cmd, encoding=None)

        # kern.boottime returns seconds and microseconds as two 64-bits
        # fields, but we are only interested in the first field.
        struct_format = '@L'
        struct_size = struct.calcsize(struct_format)
        if rc != 0 or len(out) < struct_size:
            return {}

        (kern_boottime, ) = struct.unpack(struct_format, out[:struct_size])

        return {
            'uptime_seconds': int(time.time() - kern_boottime),
        }


class DarwinHardwareCollector(HardwareCollector):
    _fact_class = DarwinHardware
    _platform = 'Darwin'
