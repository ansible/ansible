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

from ansible.module_utils.facts.hardware.base import HardwareCollector
from ansible.module_utils.facts.hardware.freebsd import FreeBSDHardware


class DragonFlyHardwareCollector(HardwareCollector):
    # Note: This uses the freebsd fact class, there is no dragonfly hardware fact class
    _fact_class = FreeBSDHardware
    _platform = 'DragonFly'
