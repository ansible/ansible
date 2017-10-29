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
    """
    platform = 'Darwin'

    def populate(self, collected_facts=None):
        hardware_facts = {}

        self.sysctl = get_sysctl(self.module, ['hw', 'machdep', 'kern'])
        mac_facts = self.get_mac_facts()
        cpu_facts = self.get_cpu_facts()
        memory_facts = self.get_memory_facts()

        hardware_facts.update(mac_facts)
        hardware_facts.update(cpu_facts)
        hardware_facts.update(memory_facts)

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
        rc, out, err = self.module.run_command("sysctl hw.model")
        if rc == 0:
            mac_facts['model'] = out.splitlines()[-1].split()[1]
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
        memory_facts = {}

        memory_facts['memtotal_mb'] = int(self.sysctl['hw.memsize']) // 1024 // 1024

        rc, out, err = self.module.run_command("sysctl hw.usermem")
        if rc == 0:
            memory_facts['memfree_mb'] = int(out.splitlines()[-1].split()[1]) // 1024 // 1024

        return memory_facts


class DarwinHardwareCollector(HardwareCollector):
    _fact_class = DarwinHardware
    _platform = 'Darwin'
