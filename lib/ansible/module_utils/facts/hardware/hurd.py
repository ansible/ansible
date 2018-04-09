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

from ansible.module_utils.facts.timeout import TimeoutError
from ansible.module_utils.facts.hardware.base import HardwareCollector
from ansible.module_utils.facts.hardware.linux import LinuxHardware


class HurdHardware(LinuxHardware):
    """
    GNU Hurd specific subclass of Hardware. Define memory and mount facts
    based on procfs compatibility translator mimicking the interface of
    the Linux kernel.
    """

    platform = 'GNU'

    def populate(self, collected_facts=None):
        hardware_facts = {}
        uptime_facts = self.get_uptime_facts()
        memory_facts = self.get_memory_facts()

        mount_facts = {}
        try:
            mount_facts = self.get_mount_facts()
        except TimeoutError:
            pass

        hardware_facts.update(uptime_facts)
        hardware_facts.update(memory_facts)
        hardware_facts.update(mount_facts)

        return hardware_facts


class HurdHardwareCollector(HardwareCollector):
    _fact_class = HurdHardware
    _platform = 'GNU'
