#
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


from ansible.module_utils.facts.other.facter import FacterFactCollector
from ansible.module_utils.facts.other.ohai import OhaiFactCollector

from ansible.module_utils.facts.system.apparmor import ApparmorFactCollector
from ansible.module_utils.facts.system.caps import SystemCapabilitiesFactCollector
from ansible.module_utils.facts.system.cmdline import CmdLineFactCollector
from ansible.module_utils.facts.system.distribution import DistributionFactCollector
from ansible.module_utils.facts.system.date_time import DateTimeFactCollector
from ansible.module_utils.facts.system.env import EnvFactCollector
from ansible.module_utils.facts.system.dns import DnsFactCollector
from ansible.module_utils.facts.system.fips import FipsFactCollector
from ansible.module_utils.facts.system.local import LocalFactCollector
from ansible.module_utils.facts.system.lsb import LSBFactCollector
from ansible.module_utils.facts.system.pkg_mgr import PkgMgrFactCollector
from ansible.module_utils.facts.system.platform import PlatformFactCollector
from ansible.module_utils.facts.system.python import PythonFactCollector
from ansible.module_utils.facts.system.selinux import SelinuxFactCollector
from ansible.module_utils.facts.system.service_mgr import ServiceMgrFactCollector
from ansible.module_utils.facts.system.ssh_pub_keys import SshPubKeyFactCollector
from ansible.module_utils.facts.system.user import UserFactCollector

from ansible.module_utils.facts.hardware.base import HardwareCollector
from ansible.module_utils.facts.hardware.aix import AIXHardwareCollector
from ansible.module_utils.facts.hardware.darwin import DarwinHardwareCollector
from ansible.module_utils.facts.hardware.dragonfly import DragonFlyHardwareCollector
from ansible.module_utils.facts.hardware.freebsd import FreeBSDHardwareCollector
from ansible.module_utils.facts.hardware.hpux import HPUXHardwareCollector
from ansible.module_utils.facts.hardware.hurd import HurdHardwareCollector
from ansible.module_utils.facts.hardware.linux import LinuxHardwareCollector
from ansible.module_utils.facts.hardware.netbsd import NetBSDHardwareCollector
from ansible.module_utils.facts.hardware.openbsd import OpenBSDHardwareCollector
from ansible.module_utils.facts.hardware.sunos import SunOSHardwareCollector

from ansible.module_utils.facts.network.base import NetworkCollector
from ansible.module_utils.facts.network.aix import AIXNetworkCollector
from ansible.module_utils.facts.network.darwin import DarwinNetworkCollector
from ansible.module_utils.facts.network.dragonfly import DragonFlyNetworkCollector
from ansible.module_utils.facts.network.freebsd import FreeBSDNetworkCollector
from ansible.module_utils.facts.network.hpux import HPUXNetworkCollector
from ansible.module_utils.facts.network.hurd import HurdNetworkCollector
from ansible.module_utils.facts.network.linux import LinuxNetworkCollector
from ansible.module_utils.facts.network.netbsd import NetBSDNetworkCollector
from ansible.module_utils.facts.network.openbsd import OpenBSDNetworkCollector
from ansible.module_utils.facts.network.sunos import SunOSNetworkCollector

from ansible.module_utils.facts.virtual.base import VirtualCollector
from ansible.module_utils.facts.virtual.dragonfly import DragonFlyVirtualCollector
from ansible.module_utils.facts.virtual.freebsd import FreeBSDVirtualCollector
from ansible.module_utils.facts.virtual.hpux import HPUXVirtualCollector
from ansible.module_utils.facts.virtual.linux import LinuxVirtualCollector
from ansible.module_utils.facts.virtual.netbsd import NetBSDVirtualCollector
from ansible.module_utils.facts.virtual.openbsd import OpenBSDVirtualCollector
from ansible.module_utils.facts.virtual.sunos import SunOSVirtualCollector

# TODO: make config driven
collectors = [ApparmorFactCollector,
              CmdLineFactCollector,
              DateTimeFactCollector,
              DistributionFactCollector,
              DnsFactCollector,
              EnvFactCollector,
              FipsFactCollector,

              HardwareCollector,
              AIXHardwareCollector,
              DarwinHardwareCollector,
              DragonFlyHardwareCollector,
              FreeBSDHardwareCollector,
              HPUXHardwareCollector,
              HurdHardwareCollector,
              LinuxHardwareCollector,
              NetBSDHardwareCollector,
              OpenBSDHardwareCollector,
              SunOSHardwareCollector,
              LocalFactCollector,
              LSBFactCollector,

              NetworkCollector,
              AIXNetworkCollector,
              DarwinNetworkCollector,
              DragonFlyNetworkCollector,
              FreeBSDNetworkCollector,
              HPUXNetworkCollector,
              HurdNetworkCollector,
              LinuxNetworkCollector,
              NetBSDNetworkCollector,
              OpenBSDNetworkCollector,
              SunOSNetworkCollector,

              PkgMgrFactCollector,
              PlatformFactCollector,
              PythonFactCollector,
              SelinuxFactCollector,
              ServiceMgrFactCollector,
              SshPubKeyFactCollector,
              SystemCapabilitiesFactCollector,
              UserFactCollector,

              VirtualCollector,
              DragonFlyVirtualCollector,
              FreeBSDVirtualCollector,
              LinuxVirtualCollector,
              OpenBSDVirtualCollector,
              NetBSDVirtualCollector,
              SunOSVirtualCollector,
              HPUXVirtualCollector,

              FacterFactCollector,
              OhaiFactCollector]
