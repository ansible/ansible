# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os
import json
import re
import struct
import time

from ansible.module_utils.facts.hardware.base import Hardware, HardwareCollector
from ansible.module_utils.facts.sysctl import get_sysctl
from ansible.module_utils.facts.timeout import TimeoutError, timeout
from ansible.module_utils.facts.utils import get_file_content, get_mount_size


class FreeBSDHardware(Hardware):
    """
    FreeBSD-specific subclass of Hardware.  Defines memory and CPU facts:
    - memfree_mb
    - memtotal_mb
    - swapfree_mb
    - swaptotal_mb
    - processor (a list)
    - processor_cores
    - processor_count
    - devices
    - uptime_seconds
    """
    platform = 'FreeBSD'
    DMESG_BOOT = '/var/run/dmesg.boot'

    def populate(self, collected_facts=None):
        hardware_facts = {}

        self.sysctl = get_sysctl(self.module, ['hw', 'vm.stats'])
        cpu_facts = self.get_cpu_facts()
        memory_facts = self.get_memory_facts()
        uptime_facts = self.get_uptime_facts()
        dmi_facts = self.get_dmi_facts()
        device_facts = self.get_device_facts()

        mount_facts = {}
        try:
            mount_facts = self.get_mount_facts()
        except TimeoutError:
            pass

        hardware_facts.update(cpu_facts)
        hardware_facts.update(memory_facts)
        hardware_facts.update(uptime_facts)
        hardware_facts.update(dmi_facts)
        hardware_facts.update(device_facts)
        hardware_facts.update(mount_facts)

        return hardware_facts

    def get_cpu_facts(self):
        cpu_facts = {}
        cpu_facts['processor'] = []
        cpu_facts['processor_count'] = self.sysctl.get('hw.ncpu') or ''

        dmesg_boot = get_file_content(FreeBSDHardware.DMESG_BOOT)
        if not dmesg_boot:
            dmesg_cmd = self.module.get_bin_path("dmesg")
            if dmesg_cmd is None:
                return cpu_facts
            try:
                rc, dmesg_boot, err = self.module.run_command(dmesg_cmd, check_rc=False)
            except Exception:
                dmesg_boot = ''

        for line in dmesg_boot.splitlines():
            if 'CPU:' in line:
                cpu = re.sub(r'CPU:\s+', r"", line)
                cpu_facts['processor'].append(cpu.strip())
            if 'Logical CPUs per core' in line:
                cpu_facts['processor_cores'] = line.split()[4]

        return cpu_facts

    def get_memory_facts(self):
        memory_facts = {}

        pagesize = pagecount = freecount = None
        if 'vm.stats.vm.v_page_size' in self.sysctl:
            pagesize = int(self.sysctl['vm.stats.vm.v_page_size'])
        if 'vm.stats.vm.v_page_count' in self.sysctl:
            pagecount = int(self.sysctl['vm.stats.vm.v_page_count'])
        if 'vm.stats.vm.v_free_count' in self.sysctl:
            freecount = int(self.sysctl['vm.stats.vm.v_free_count'])
        if pagesize is not None:
            if pagecount is not None:
                memory_facts['memtotal_mb'] = pagesize * pagecount // 1024 // 1024
            if freecount is not None:
                memory_facts['memfree_mb'] = pagesize * freecount // 1024 // 1024

        swapinfo_cmd = self.module.get_bin_path('swapinfo')
        if swapinfo_cmd is None:
            return memory_facts

        # Get swapinfo.  swapinfo output looks like:
        # Device          1M-blocks     Used    Avail Capacity
        # /dev/ada0p3        314368        0   314368     0%
        #
        rc, out, err = self.module.run_command("%s -k" % swapinfo_cmd)
        lines = out.splitlines()
        if len(lines[-1]) == 0:
            lines.pop()
        data = lines[-1].split()
        if data[0] != 'Device':
            memory_facts['swaptotal_mb'] = int(data[1]) // 1024
            memory_facts['swapfree_mb'] = int(data[3]) // 1024

        return memory_facts

    def get_uptime_facts(self):
        # On FreeBSD, the default format is annoying to parse.
        # Use -b to get the raw value and decode it.
        sysctl_cmd = self.module.get_bin_path('sysctl')
        if not sysctl_cmd:
            return {}
        cmd = [sysctl_cmd, '-b', 'kern.boottime']

        # We need to get raw bytes, not UTF-8.
        rc, out, dummy = self.module.run_command(cmd, encoding=None)

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

    @timeout()
    def get_mount_facts(self):
        mount_facts = {}

        mount_facts['mounts'] = []
        fstab = get_file_content('/etc/fstab')
        if fstab:
            for line in fstab.splitlines():
                if line.startswith('#') or line.strip() == '':
                    continue
                fields = re.sub(r'\s+', ' ', line).split()
                mount_statvfs_info = get_mount_size(fields[1])
                mount_info = {
                    'mount': fields[1],
                    'device': fields[0],
                    'fstype': fields[2],
                    'options': fields[3]
                }
                mount_info.update(mount_statvfs_info)
                mount_facts['mounts'].append(mount_info)

        return mount_facts

    def get_device_facts(self):
        device_facts = {}

        sysdir = '/dev'
        device_facts['devices'] = {}
        # TODO: rc, disks, err = self.module.run_command("/sbin/sysctl kern.disks")
        drives = re.compile(
            r"""(?x)(
              (?:
                ada?   # ATA/SATA disk device
                |da    # SCSI disk device
                |a?cd  # SCSI CDROM drive
                |amrd  # AMI MegaRAID drive
                |idad  # Compaq RAID array
                |ipsd  # IBM ServeRAID RAID array
                |md    # md(4) disk device
                |mfid  # LSI MegaRAID SAS array
                |mlxd  # Mylex RAID disk
                |twed  # 3ware ATA RAID array
                |vtbd  # VirtIO Block Device
              )\d+
            )
            """
        )

        slices = re.compile(
            r"""(?x)(
              (?:
                ada?   # ATA/SATA disk device
                |a?cd  # SCSI CDROM drive
                |amrd  # AMI MegaRAID drive
                |da    # SCSI disk device
                |idad  # Compaq RAID array
                |ipsd  # IBM ServeRAID RAID array
                |md    # md(4) disk device
                |mfid  # LSI MegaRAID SAS array
                |mlxd  # Mylex RAID disk
                |twed  # 3ware ATA RAID array
                |vtbd  # VirtIO Block Device
              )\d+[ps]\d+\w*
            )
            """
        )

        if os.path.isdir(sysdir):
            dirlist = sorted(os.listdir(sysdir))
            for device in dirlist:
                d = drives.match(device)
                if d and d.group(1) not in device_facts['devices']:
                    device_facts['devices'][d.group(1)] = []
                s = slices.match(device)
                if s:
                    device_facts['devices'][d.group(1)].append(s.group(1))

        return device_facts

    def get_dmi_facts(self):
        """ learn dmi facts from system

        Use dmidecode executable if available"""

        dmi_facts = {}

        # Fall back to using dmidecode, if available
        dmi_bin = self.module.get_bin_path('dmidecode')
        if not dmi_bin:
            return dmi_facts
        DMI_DICT = {
            'bios_date': 'bios-release-date',
            'bios_vendor': 'bios-vendor',
            'bios_version': 'bios-version',
            'board_asset_tag': 'baseboard-asset-tag',
            'board_name': 'baseboard-product-name',
            'board_serial': 'baseboard-serial-number',
            'board_vendor': 'baseboard-manufacturer',
            'board_version': 'baseboard-version',
            'chassis_asset_tag': 'chassis-asset-tag',
            'chassis_serial': 'chassis-serial-number',
            'chassis_vendor': 'chassis-manufacturer',
            'chassis_version': 'chassis-version',
            'form_factor': 'chassis-type',
            'product_name': 'system-product-name',
            'product_serial': 'system-serial-number',
            'product_uuid': 'system-uuid',
            'product_version': 'system-version',
            'system_vendor': 'system-manufacturer',
        }
        if dmi_bin is None:
            dmi_facts = dict.fromkeys(
                DMI_DICT.keys(),
                'NA'
            )
            return dmi_facts

        for (k, v) in DMI_DICT.items():
            (rc, out, err) = self.module.run_command('%s -s %s' % (dmi_bin, v))
            if rc == 0:
                # Strip out commented lines (specific dmidecode output)
                # FIXME: why add the fact and then test if it is json?
                dmi_facts[k] = ''.join([line for line in out.splitlines() if not line.startswith('#')])
                try:
                    json.dumps(dmi_facts[k])
                except UnicodeDecodeError:
                    dmi_facts[k] = 'NA'
            else:
                dmi_facts[k] = 'NA'

        return dmi_facts


class FreeBSDHardwareCollector(HardwareCollector):
    _fact_class = FreeBSDHardware
    _platform = 'FreeBSD'
