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

import collections
import errno
import glob
import json
import os
import re
import sys

from ansible.module_utils.six import iteritems

from ansible.module_utils.basic import bytes_to_human

from ansible.module_utils.facts.hardware.base import Hardware, HardwareCollector
from ansible.module_utils.facts.utils import get_file_content, get_file_lines, get_mount_size

# import this as a module to ensure we get the same module isntance
from ansible.module_utils.facts import timeout


def get_partition_uuid(partname):
    try:
        uuids = os.listdir("/dev/disk/by-uuid")
    except OSError:
        return

    for uuid in uuids:
        dev = os.path.realpath("/dev/disk/by-uuid/" + uuid)
        if dev == ("/dev/" + partname):
            return uuid

    return None


class LinuxHardware(Hardware):
    """
    Linux-specific subclass of Hardware.  Defines memory and CPU facts:
    - memfree_mb
    - memtotal_mb
    - swapfree_mb
    - swaptotal_mb
    - processor (a list)
    - processor_cores
    - processor_count

    In addition, it also defines number of DMI facts and device facts.
    """

    platform = 'Linux'

    # Originally only had these four as toplevelfacts
    ORIGINAL_MEMORY_FACTS = frozenset(('MemTotal', 'SwapTotal', 'MemFree', 'SwapFree'))
    # Now we have all of these in a dict structure
    MEMORY_FACTS = ORIGINAL_MEMORY_FACTS.union(('Buffers', 'Cached', 'SwapCached'))

    # regex used against findmnt output to detect bind mounts
    BIND_MOUNT_RE = re.compile(r'.*\]')

    # regex used against mtab content to find entries that are bind mounts
    MTAB_BIND_MOUNT_RE = re.compile(r'.*bind.*"')

    def populate(self, collected_facts=None):
        hardware_facts = {}

        cpu_facts = self.get_cpu_facts(collected_facts=collected_facts)
        memory_facts = self.get_memory_facts()
        dmi_facts = self.get_dmi_facts()
        device_facts = self.get_device_facts()
        uptime_facts = self.get_uptime_facts()
        lvm_facts = self.get_lvm_facts()

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
        hardware_facts.update(lvm_facts)
        hardware_facts.update(mount_facts)

        return hardware_facts

    def get_memory_facts(self):
        memory_facts = {}
        if not os.access("/proc/meminfo", os.R_OK):
            return memory_facts

        memstats = {}
        for line in get_file_lines("/proc/meminfo"):
            data = line.split(":", 1)
            key = data[0]
            if key in self.ORIGINAL_MEMORY_FACTS:
                val = data[1].strip().split(' ')[0]
                memory_facts["%s_mb" % key.lower()] = int(val) // 1024

            if key in self.MEMORY_FACTS:
                val = data[1].strip().split(' ')[0]
                memstats[key.lower()] = int(val) // 1024

        if None not in (memstats.get('memtotal'), memstats.get('memfree')):
            memstats['real:used'] = memstats['memtotal'] - memstats['memfree']
        if None not in (memstats.get('cached'), memstats.get('memfree'), memstats.get('buffers')):
            memstats['nocache:free'] = memstats['cached'] + memstats['memfree'] + memstats['buffers']
        if None not in (memstats.get('memtotal'), memstats.get('nocache:free')):
            memstats['nocache:used'] = memstats['memtotal'] - memstats['nocache:free']
        if None not in (memstats.get('swaptotal'), memstats.get('swapfree')):
            memstats['swap:used'] = memstats['swaptotal'] - memstats['swapfree']

        memory_facts['memory_mb'] = {
            'real': {
                'total': memstats.get('memtotal'),
                'used': memstats.get('real:used'),
                'free': memstats.get('memfree'),
            },
            'nocache': {
                'free': memstats.get('nocache:free'),
                'used': memstats.get('nocache:used'),
            },
            'swap': {
                'total': memstats.get('swaptotal'),
                'free': memstats.get('swapfree'),
                'used': memstats.get('swap:used'),
                'cached': memstats.get('swapcached'),
            },
        }

        return memory_facts

    def get_cpu_facts(self, collected_facts=None):
        cpu_facts = {}
        collected_facts = collected_facts or {}

        i = 0
        vendor_id_occurrence = 0
        model_name_occurrence = 0
        physid = 0
        coreid = 0
        sockets = {}
        cores = {}

        xen = False
        xen_paravirt = False
        try:
            if os.path.exists('/proc/xen'):
                xen = True
            else:
                for line in get_file_lines('/sys/hypervisor/type'):
                    if line.strip() == 'xen':
                        xen = True
                    # Only interested in the first line
                    break
        except IOError:
            pass

        if not os.access("/proc/cpuinfo", os.R_OK):
            return cpu_facts

        cpu_facts['processor'] = []
        for line in get_file_lines('/proc/cpuinfo'):
            data = line.split(":", 1)
            key = data[0].strip()

            if xen:
                if key == 'flags':
                    # Check for vme cpu flag, Xen paravirt does not expose this.
                    #   Need to detect Xen paravirt because it exposes cpuinfo
                    #   differently than Xen HVM or KVM and causes reporting of
                    #   only a single cpu core.
                    if 'vme' not in data:
                        xen_paravirt = True

            # model name is for Intel arch, Processor (mind the uppercase P)
            # works for some ARM devices, like the Sheevaplug.
            if key in ['model name', 'Processor', 'vendor_id', 'cpu', 'Vendor']:
                if 'processor' not in cpu_facts:
                    cpu_facts['processor'] = []
                cpu_facts['processor'].append(data[1].strip())
                if key == 'vendor_id':
                    vendor_id_occurrence += 1
                if key == 'model name':
                    model_name_occurrence += 1
                i += 1
            elif key == 'physical id':
                physid = data[1].strip()
                if physid not in sockets:
                    sockets[physid] = 1
            elif key == 'core id':
                coreid = data[1].strip()
                if coreid not in sockets:
                    cores[coreid] = 1
            elif key == 'cpu cores':
                sockets[physid] = int(data[1].strip())
            elif key == 'siblings':
                cores[coreid] = int(data[1].strip())
            elif key == '# processors':
                cpu_facts['processor_cores'] = int(data[1].strip())

        # Skip for platforms without vendor_id/model_name in cpuinfo (e.g ppc64le)
        if vendor_id_occurrence > 0:
            if vendor_id_occurrence == model_name_occurrence:
                i = vendor_id_occurrence

        # FIXME
        if collected_facts.get('ansible_architecture') != 's390x':
            if xen_paravirt:
                cpu_facts['processor_count'] = i
                cpu_facts['processor_cores'] = i
                cpu_facts['processor_threads_per_core'] = 1
                cpu_facts['processor_vcpus'] = i
            else:
                if sockets:
                    cpu_facts['processor_count'] = len(sockets)
                else:
                    cpu_facts['processor_count'] = i

                socket_values = list(sockets.values())
                if socket_values and socket_values[0]:
                    cpu_facts['processor_cores'] = socket_values[0]
                else:
                    cpu_facts['processor_cores'] = 1

                core_values = list(cores.values())
                if core_values:
                    cpu_facts['processor_threads_per_core'] = core_values[0] // cpu_facts['processor_cores']
                else:
                    cpu_facts['processor_threads_per_core'] = 1 // cpu_facts['processor_cores']

                cpu_facts['processor_vcpus'] = (cpu_facts['processor_threads_per_core'] *
                                                cpu_facts['processor_count'] * cpu_facts['processor_cores'])

        return cpu_facts

    def get_dmi_facts(self):
        ''' learn dmi facts from system

        Try /sys first for dmi related facts.
        If that is not available, fall back to dmidecode executable '''

        dmi_facts = {}

        if os.path.exists('/sys/devices/virtual/dmi/id/product_name'):
            # Use kernel DMI info, if available

            # DMI SPEC -- http://www.dmtf.org/sites/default/files/standards/documents/DSP0134_2.7.0.pdf
            FORM_FACTOR = ["Unknown", "Other", "Unknown", "Desktop",
                           "Low Profile Desktop", "Pizza Box", "Mini Tower", "Tower",
                           "Portable", "Laptop", "Notebook", "Hand Held", "Docking Station",
                           "All In One", "Sub Notebook", "Space-saving", "Lunch Box",
                           "Main Server Chassis", "Expansion Chassis", "Sub Chassis",
                           "Bus Expansion Chassis", "Peripheral Chassis", "RAID Chassis",
                           "Rack Mount Chassis", "Sealed-case PC", "Multi-system",
                           "CompactPCI", "AdvancedTCA", "Blade"]

            DMI_DICT = {
                'bios_date': '/sys/devices/virtual/dmi/id/bios_date',
                'bios_version': '/sys/devices/virtual/dmi/id/bios_version',
                'form_factor': '/sys/devices/virtual/dmi/id/chassis_type',
                'product_name': '/sys/devices/virtual/dmi/id/product_name',
                'product_serial': '/sys/devices/virtual/dmi/id/product_serial',
                'product_uuid': '/sys/devices/virtual/dmi/id/product_uuid',
                'product_version': '/sys/devices/virtual/dmi/id/product_version',
                'system_vendor': '/sys/devices/virtual/dmi/id/sys_vendor'
            }

            for (key, path) in DMI_DICT.items():
                data = get_file_content(path)
                if data is not None:
                    if key == 'form_factor':
                        try:
                            dmi_facts['form_factor'] = FORM_FACTOR[int(data)]
                        except IndexError:
                            dmi_facts['form_factor'] = 'unknown (%s)' % data
                    else:
                        dmi_facts[key] = data
                else:
                    dmi_facts[key] = 'NA'

        else:
            # Fall back to using dmidecode, if available
            dmi_bin = self.module.get_bin_path('dmidecode')
            DMI_DICT = {
                'bios_date': 'bios-release-date',
                'bios_version': 'bios-version',
                'form_factor': 'chassis-type',
                'product_name': 'system-product-name',
                'product_serial': 'system-serial-number',
                'product_uuid': 'system-uuid',
                'product_version': 'system-version',
                'system_vendor': 'system-manufacturer'
            }
            for (k, v) in DMI_DICT.items():
                if dmi_bin is not None:
                    (rc, out, err) = self.module.run_command('%s -s %s' % (dmi_bin, v))
                    if rc == 0:
                        # Strip out commented lines (specific dmidecode output)
                        thisvalue = ''.join([line for line in out.splitlines() if not line.startswith('#')])
                        try:
                            json.dumps(thisvalue)
                        except UnicodeDecodeError:
                            thisvalue = "NA"

                        dmi_facts[k] = thisvalue
                    else:
                        dmi_facts[k] = 'NA'
                else:
                    dmi_facts[k] = 'NA'

        return dmi_facts

    def _run_lsblk(self, lsblk_path):
        # call lsblk and collect all uuids
        # --exclude 2 makes lsblk ignore floppy disks, which are slower to answer than typical timeouts
        # this uses the linux major device number
        # for details see https://www.kernel.org/doc/Documentation/devices.txt
        args = ['--list', '--noheadings', '--paths', '--output', 'NAME,UUID', '--exclude', '2']
        cmd = [lsblk_path] + args
        rc, out, err = self.module.run_command(cmd)
        return rc, out, err

    def _lsblk_uuid(self):
        uuids = {}
        lsblk_path = self.module.get_bin_path("lsblk")
        if not lsblk_path:
            return uuids

        rc, out, err = self._run_lsblk(lsblk_path)
        if rc != 0:
            return uuids

        # each line will be in format:
        # <devicename><some whitespace><uuid>
        # /dev/sda1  32caaec3-ef40-4691-a3b6-438c3f9bc1c0
        for lsblk_line in out.splitlines():
            if not lsblk_line:
                continue

            line = lsblk_line.strip()
            fields = line.rsplit(None, 1)

            if len(fields) < 2:
                continue

            device_name, uuid = fields[0].strip(), fields[1].strip()
            if device_name in uuids:
                continue
            uuids[device_name] = uuid

        return uuids

    def _run_findmnt(self, findmnt_path):
        args = ['--list', '--noheadings', '--notruncate']
        cmd = [findmnt_path] + args
        rc, out, err = self.module.run_command(cmd, errors='surrogate_then_replace')
        return rc, out, err

    def _find_bind_mounts(self):
        bind_mounts = set()
        findmnt_path = self.module.get_bin_path("findmnt")
        if not findmnt_path:
            return bind_mounts

        rc, out, err = self._run_findmnt(findmnt_path)
        if rc != 0:
            return bind_mounts

        # find bind mounts, in case /etc/mtab is a symlink to /proc/mounts
        for line in out.splitlines():
            fields = line.split()
            # fields[0] is the TARGET, fields[1] is the SOURCE
            if len(fields) < 2:
                continue

            # bind mounts will have a [/directory_name] in the SOURCE column
            if self.BIND_MOUNT_RE.match(fields[1]):
                bind_mounts.add(fields[0])

        return bind_mounts

    def _mtab_entries(self):
        mtab_file = '/etc/mtab'
        if not os.path.exists(mtab_file):
            mtab_file = '/proc/mounts'

        mtab = get_file_content(mtab_file, '')
        mtab_entries = []
        for line in mtab.splitlines():
            fields = line.split()
            if len(fields) < 4:
                continue
            mtab_entries.append(fields)
        return mtab_entries

    @timeout.timeout()
    def get_mount_facts(self):
        mount_facts = {}

        mount_facts['mounts'] = []

        bind_mounts = self._find_bind_mounts()
        uuids = self._lsblk_uuid()
        mtab_entries = self._mtab_entries()

        mounts = []
        for fields in mtab_entries:
            device, mount, fstype, options = fields[0], fields[1], fields[2], fields[3]

            if not device.startswith('/') and ':/' not in device:
                continue

            if fstype == 'none':
                continue

            mount_statvfs_info = get_mount_size(mount)

            if mount in bind_mounts:
                # only add if not already there, we might have a plain /etc/mtab
                if not self.MTAB_BIND_MOUNT_RE.match(options):
                    options += ",bind"

            mount_info = {'mount': mount,
                          'device': device,
                          'fstype': fstype,
                          'options': options,
                          'uuid': uuids.get(device, 'N/A')}

            mount_info.update(mount_statvfs_info)

            mounts.append(mount_info)

        mount_facts['mounts'] = mounts

        return mount_facts

    def get_device_links(self, link_dir):
        if not os.path.exists(link_dir):
            return {}
        try:
            retval = collections.defaultdict(set)
            for entry in os.listdir(link_dir):
                try:
                    target = os.path.basename(os.readlink(os.path.join(link_dir, entry)))
                    retval[target].add(entry)
                except OSError:
                    continue
            return dict((k, list(sorted(v))) for (k, v) in iteritems(retval))
        except OSError:
            return {}

    def get_all_device_owners(self):
        try:
            retval = collections.defaultdict(set)
            for path in glob.glob('/sys/block/*/slaves/*'):
                elements = path.split('/')
                device = elements[3]
                target = elements[5]
                retval[target].add(device)
            return dict((k, list(sorted(v))) for (k, v) in iteritems(retval))
        except OSError:
            return {}

    def get_all_device_links(self):
        return {
            'ids': self.get_device_links('/dev/disk/by-id'),
            'uuids': self.get_device_links('/dev/disk/by-uuid'),
            'labels': self.get_device_links('/dev/disk/by-label'),
            'masters': self.get_all_device_owners(),
        }

    def get_holders(self, block_dev_dict, sysdir):
        block_dev_dict['holders'] = []
        if os.path.isdir(sysdir + "/holders"):
            for folder in os.listdir(sysdir + "/holders"):
                if not folder.startswith("dm-"):
                    continue
                name = get_file_content(sysdir + "/holders/" + folder + "/dm/name")
                if name:
                    block_dev_dict['holders'].append(name)
                else:
                    block_dev_dict['holders'].append(folder)

    def get_device_facts(self):
        device_facts = {}

        device_facts['devices'] = {}
        lspci = self.module.get_bin_path('lspci')
        if lspci:
            rc, pcidata, err = self.module.run_command([lspci, '-D'], errors='surrogate_then_replace')
        else:
            pcidata = None

        try:
            block_devs = os.listdir("/sys/block")
        except OSError:
            return device_facts

        devs_wwn = {}
        try:
            devs_by_id = os.listdir("/dev/disk/by-id")
        except OSError:
            pass
        else:
            for link_name in devs_by_id:
                if link_name.startswith("wwn-"):
                    try:
                        wwn_link = os.readlink(os.path.join("/dev/disk/by-id", link_name))
                    except OSError:
                        continue
                    devs_wwn[os.path.basename(wwn_link)] = link_name[4:]

        links = self.get_all_device_links()
        device_facts['device_links'] = links

        for block in block_devs:
            virtual = 1
            sysfs_no_links = 0
            try:
                path = os.readlink(os.path.join("/sys/block/", block))
            except OSError:
                e = sys.exc_info()[1]
                if e.errno == errno.EINVAL:
                    path = block
                    sysfs_no_links = 1
                else:
                    continue
            sysdir = os.path.join("/sys/block", path)
            if sysfs_no_links == 1:
                for folder in os.listdir(sysdir):
                    if "device" in folder:
                        virtual = 0
                        break
            d = {}
            d['virtual'] = virtual
            d['links'] = {}
            for (link_type, link_values) in iteritems(links):
                d['links'][link_type] = link_values.get(block, [])
            diskname = os.path.basename(sysdir)
            for key in ['vendor', 'model', 'sas_address', 'sas_device_handle']:
                d[key] = get_file_content(sysdir + "/device/" + key)

            sg_inq = self.module.get_bin_path('sg_inq')

            if sg_inq:
                device = "/dev/%s" % (block)
                rc, drivedata, err = self.module.run_command([sg_inq, device])
                if rc == 0:
                    serial = re.search("Unit serial number:\s+(\w+)", drivedata)
                    if serial:
                        d['serial'] = serial.group(1)

            for key in ['vendor', 'model']:
                d[key] = get_file_content(sysdir + "/device/" + key)

            for key, test in [('removable', '/removable'),
                              ('support_discard', '/queue/discard_granularity'),
                              ]:
                d[key] = get_file_content(sysdir + test)

            if diskname in devs_wwn:
                d['wwn'] = devs_wwn[diskname]

            d['partitions'] = {}
            for folder in os.listdir(sysdir):
                m = re.search("(" + diskname + "\d+)", folder)
                if m:
                    part = {}
                    partname = m.group(1)
                    part_sysdir = sysdir + "/" + partname

                    part['links'] = {}
                    for (link_type, link_values) in iteritems(links):
                        part['links'][link_type] = link_values.get(partname, [])

                    part['start'] = get_file_content(part_sysdir + "/start", 0)
                    part['sectors'] = get_file_content(part_sysdir + "/size", 0)

                    part['sectorsize'] = get_file_content(part_sysdir + "/queue/logical_block_size")
                    if not part['sectorsize']:
                        part['sectorsize'] = get_file_content(part_sysdir + "/queue/hw_sector_size", 512)
                    part['size'] = bytes_to_human((float(part['sectors']) * float(part['sectorsize'])))
                    part['uuid'] = get_partition_uuid(partname)
                    self.get_holders(part, part_sysdir)

                    d['partitions'][partname] = part

            d['rotational'] = get_file_content(sysdir + "/queue/rotational")
            d['scheduler_mode'] = ""
            scheduler = get_file_content(sysdir + "/queue/scheduler")
            if scheduler is not None:
                m = re.match(".*?(\[(.*)\])", scheduler)
                if m:
                    d['scheduler_mode'] = m.group(2)

            d['sectors'] = get_file_content(sysdir + "/size")
            if not d['sectors']:
                d['sectors'] = 0
            d['sectorsize'] = get_file_content(sysdir + "/queue/logical_block_size")
            if not d['sectorsize']:
                d['sectorsize'] = get_file_content(sysdir + "/queue/hw_sector_size", 512)
            d['size'] = bytes_to_human(float(d['sectors']) * float(d['sectorsize']))

            d['host'] = ""

            # domains are numbered (0 to ffff), bus (0 to ff), slot (0 to 1f), and function (0 to 7).
            m = re.match(".+/([a-f0-9]{4}:[a-f0-9]{2}:[0|1][a-f0-9]\.[0-7])/", sysdir)
            if m and pcidata:
                pciid = m.group(1)
                did = re.escape(pciid)
                m = re.search("^" + did + "\s(.*)$", pcidata, re.MULTILINE)
                if m:
                    d['host'] = m.group(1)

            self.get_holders(d, sysdir)

            device_facts['devices'][diskname] = d

        return device_facts

    def get_uptime_facts(self):
        uptime_facts = {}
        uptime_file_content = get_file_content('/proc/uptime')
        if uptime_file_content:
            uptime_seconds_string = uptime_file_content.split(' ')[0]
            uptime_facts['uptime_seconds'] = int(float(uptime_seconds_string))

        return uptime_facts

    def _find_mapper_device_name(self, dm_device):
        dm_prefix = '/dev/dm-'
        mapper_device = dm_device
        if dm_device.startswith(dm_prefix):
            dmsetup_cmd = self.module.get_bin_path('dmsetup', True)
            mapper_prefix = '/dev/mapper/'
            rc, dm_name, err = self.module.run_command("%s info -C --noheadings -o name %s" % (dmsetup_cmd, dm_device))
            if rc == 0:
                mapper_device = mapper_prefix + dm_name.rstrip()
        return mapper_device

    def get_lvm_facts(self):
        """ Get LVM Facts if running as root and lvm utils are available """

        lvm_facts = {}

        if os.getuid() == 0 and self.module.get_bin_path('vgs'):
            lvm_util_options = '--noheadings --nosuffix --units g'

            vgs_path = self.module.get_bin_path('vgs')
            # vgs fields: VG #PV #LV #SN Attr VSize VFree
            vgs = {}
            if vgs_path:
                rc, vg_lines, err = self.module.run_command('%s %s' % (vgs_path, lvm_util_options))
                for vg_line in vg_lines.splitlines():
                    items = vg_line.split()
                    vgs[items[0]] = {'size_g': items[-2],
                                     'free_g': items[-1],
                                     'num_lvs': items[2],
                                     'num_pvs': items[1]}

            lvs_path = self.module.get_bin_path('lvs')
            # lvs fields:
            # LV VG Attr LSize Pool Origin Data% Move Log Copy% Convert
            lvs = {}
            if lvs_path:
                rc, lv_lines, err = self.module.run_command('%s %s' % (lvs_path, lvm_util_options))
                for lv_line in lv_lines.splitlines():
                    items = lv_line.split()
                    lvs[items[0]] = {'size_g': items[3], 'vg': items[1]}

            pvs_path = self.module.get_bin_path('pvs')
            # pvs fields: PV VG #Fmt #Attr PSize PFree
            pvs = {}
            if pvs_path:
                rc, pv_lines, err = self.module.run_command('%s %s' % (pvs_path, lvm_util_options))
                for pv_line in pv_lines.splitlines():
                    items = pv_line.split()
                    pvs[self._find_mapper_device_name(items[0])] = {
                        'size_g': items[4],
                        'free_g': items[5],
                        'vg': items[1]}

            lvm_facts['lvm'] = {'lvs': lvs, 'vgs': vgs, 'pvs': pvs}

        return lvm_facts


class LinuxHardwareCollector(HardwareCollector):
    _platform = 'Linux'
    _fact_class = LinuxHardware
