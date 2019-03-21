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

from ansible.module_utils.six.moves import reduce

from ansible.module_utils.common.text.formatters import bytes_to_human

from ansible.module_utils.facts.utils import get_file_content, get_mount_size

from ansible.module_utils.facts.hardware.base import Hardware, HardwareCollector
from ansible.module_utils.facts import timeout


class SunOSHardware(Hardware):
    """
    In addition to the generic memory and cpu facts, this also sets
    swap_reserved_mb and swap_allocated_mb that is available from *swap -s*.
    """
    platform = 'SunOS'

    def populate(self, collected_facts=None):
        hardware_facts = {}

        # FIXME: could pass to run_command(environ_update), but it also tweaks the env
        #        of the parent process instead of altering an env provided to Popen()
        # Use C locale for hardware collection helpers to avoid locale specific number formatting (#24542)
        self.module.run_command_environ_update = {'LANG': 'C', 'LC_ALL': 'C', 'LC_NUMERIC': 'C'}

        cpu_facts = self.get_cpu_facts()
        memory_facts = self.get_memory_facts()
        dmi_facts = self.get_dmi_facts()
        device_facts = self.get_device_facts()
        uptime_facts = self.get_uptime_facts()

        mount_facts = {}
        try:
            mount_facts = self.get_mount_facts()
        except timeout.TimeoutError:
            pass

        hardware_facts.update(cpu_facts)
        hardware_facts.update(memory_facts)
        hardware_facts.update(dmi_facts)
        hardware_facts.update(device_facts)
        hardware_facts.update(uptime_facts)
        hardware_facts.update(mount_facts)

        return hardware_facts

    def get_cpu_facts(self, collected_facts=None):
        physid = 0
        sockets = {}

        cpu_facts = {}
        collected_facts = collected_facts or {}

        rc, out, err = self.module.run_command("/usr/bin/kstat cpu_info")

        cpu_facts['processor'] = []

        for line in out.splitlines():
            if len(line) < 1:
                continue

            data = line.split(None, 1)
            key = data[0].strip()

            # "brand" works on Solaris 10 & 11. "implementation" for Solaris 9.
            if key == 'module:':
                brand = ''
            elif key == 'brand':
                brand = data[1].strip()
            elif key == 'clock_MHz':
                clock_mhz = data[1].strip()
            elif key == 'implementation':
                processor = brand or data[1].strip()
                # Add clock speed to description for SPARC CPU
                # FIXME
                if collected_facts.get('ansible_machine') != 'i86pc':
                    processor += " @ " + clock_mhz + "MHz"
                if 'ansible_processor' not in collected_facts:
                    cpu_facts['processor'] = []
                cpu_facts['processor'].append(processor)
            elif key == 'chip_id':
                physid = data[1].strip()
                if physid not in sockets:
                    sockets[physid] = 1
                else:
                    sockets[physid] += 1

        # Counting cores on Solaris can be complicated.
        # https://blogs.oracle.com/mandalika/entry/solaris_show_me_the_cpu
        # Treat 'processor_count' as physical sockets and 'processor_cores' as
        # virtual CPUs visisble to Solaris. Not a true count of cores for modern SPARC as
        # these processors have: sockets -> cores -> threads/virtual CPU.
        if len(sockets) > 0:
            cpu_facts['processor_count'] = len(sockets)
            cpu_facts['processor_cores'] = reduce(lambda x, y: x + y, sockets.values())
        else:
            cpu_facts['processor_cores'] = 'NA'
            cpu_facts['processor_count'] = len(cpu_facts['processor'])

        return cpu_facts

    def get_memory_facts(self):
        memory_facts = {}

        rc, out, err = self.module.run_command(["/usr/sbin/prtconf"])

        for line in out.splitlines():
            if 'Memory size' in line:
                memory_facts['memtotal_mb'] = int(line.split()[2])

        rc, out, err = self.module.run_command("/usr/sbin/swap -s")

        allocated = int(out.split()[1][:-1])
        reserved = int(out.split()[5][:-1])
        used = int(out.split()[8][:-1])
        free = int(out.split()[10][:-1])

        memory_facts['swapfree_mb'] = free // 1024
        memory_facts['swaptotal_mb'] = (free + used) // 1024
        memory_facts['swap_allocated_mb'] = allocated // 1024
        memory_facts['swap_reserved_mb'] = reserved // 1024

        return memory_facts

    @timeout.timeout()
    def get_mount_facts(self):
        mount_facts = {}
        mount_facts['mounts'] = []

        # For a detailed format description see mnttab(4)
        #   special mount_point fstype options time
        fstab = get_file_content('/etc/mnttab')

        if fstab:
            for line in fstab.splitlines():
                fields = line.split('\t')
                mount_statvfs_info = get_mount_size(fields[1])
                mount_info = {'mount': fields[1],
                              'device': fields[0],
                              'fstype': fields[2],
                              'options': fields[3],
                              'time': fields[4]}
                mount_info.update(mount_statvfs_info)
                mount_facts['mounts'].append(mount_info)

        return mount_facts

    def get_dmi_facts(self):
        dmi_facts = {}

        # On Solaris 8 the prtdiag wrapper is absent from /usr/sbin,
        # but that's okay, because we know where to find the real thing:
        rc, platform, err = self.module.run_command('/usr/bin/uname -i')
        platform_sbin = '/usr/platform/' + platform.rstrip() + '/sbin'

        prtdiag_path = self.module.get_bin_path("prtdiag", opt_dirs=[platform_sbin])
        rc, out, err = self.module.run_command(prtdiag_path)
        """
        rc returns 1
        """
        if out:
            system_conf = out.split('\n')[0]

            # If you know of any other manufacturers whose names appear in
            # the first line of prtdiag's output, please add them here:
            vendors = [
                "Fujitsu",
                "Oracle Corporation",
                "QEMU",
                "Sun Microsystems",
                "VMware, Inc.",
            ]
            vendor_regexp = "|".join(map(re.escape, vendors))
            system_conf_regexp = (r'System Configuration:\s+'
                                  + r'(' + vendor_regexp + r')\s+'
                                  + r'(?:sun\w+\s+)?'
                                  + r'(.+)')

            found = re.match(system_conf_regexp, system_conf)
            if found:
                dmi_facts['system_vendor'] = found.group(1)
                dmi_facts['product_name'] = found.group(2)

        return dmi_facts

    def get_device_facts(self):
        # Device facts are derived for sdderr kstats. This code does not use the
        # full output, but rather queries for specific stats.
        # Example output:
        # sderr:0:sd0,err:Hard Errors     0
        # sderr:0:sd0,err:Illegal Request 6
        # sderr:0:sd0,err:Media Error     0
        # sderr:0:sd0,err:Predictive Failure Analysis     0
        # sderr:0:sd0,err:Product VBOX HARDDISK   9
        # sderr:0:sd0,err:Revision        1.0
        # sderr:0:sd0,err:Serial No       VB0ad2ec4d-074a
        # sderr:0:sd0,err:Size    53687091200
        # sderr:0:sd0,err:Soft Errors     0
        # sderr:0:sd0,err:Transport Errors        0
        # sderr:0:sd0,err:Vendor  ATA

        device_facts = {}
        device_facts['devices'] = {}

        disk_stats = {
            'Product': 'product',
            'Revision': 'revision',
            'Serial No': 'serial',
            'Size': 'size',
            'Vendor': 'vendor',
            'Hard Errors': 'hard_errors',
            'Soft Errors': 'soft_errors',
            'Transport Errors': 'transport_errors',
            'Media Error': 'media_errors',
            'Predictive Failure Analysis': 'predictive_failure_analysis',
            'Illegal Request': 'illegal_request',
        }

        cmd = ['/usr/bin/kstat', '-p']

        for ds in disk_stats:
            cmd.append('sderr:::%s' % ds)

        d = {}
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            return device_facts

        sd_instances = frozenset(line.split(':')[1] for line in out.split('\n') if line.startswith('sderr'))
        for instance in sd_instances:
            lines = (line for line in out.split('\n') if ':' in line and line.split(':')[1] == instance)
            for line in lines:
                text, value = line.split('\t')
                stat = text.split(':')[3]

                if stat == 'Size':
                    d[disk_stats.get(stat)] = bytes_to_human(float(value))
                else:
                    d[disk_stats.get(stat)] = value.rstrip()

            diskname = 'sd' + instance
            device_facts['devices'][diskname] = d
            d = {}

        return device_facts

    def get_uptime_facts(self):
        uptime_facts = {}
        # On Solaris, unix:0:system_misc:snaptime is created shortly after machine boots up
        # and displays tiem in seconds. This is much easier than using uptime as we would
        # need to have a parsing procedure for translating from human-readable to machine-readable
        # format.
        # Example output:
        # unix:0:system_misc:snaptime     1175.410463590
        rc, out, err = self.module.run_command('/usr/bin/kstat -p unix:0:system_misc:snaptime')

        if rc != 0:
            return

        uptime_facts['uptime_seconds'] = int(float(out.split('\t')[1]))

        return uptime_facts


class SunOSHardwareCollector(HardwareCollector):
    _fact_class = SunOSHardware
    _platform = 'SunOS'

    required_facts = set(['platform'])
