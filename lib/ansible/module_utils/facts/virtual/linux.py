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

import glob
import os
import re

from ansible.module_utils.facts.virtual.base import Virtual, VirtualCollector
from ansible.module_utils.facts.utils import get_file_content, get_file_lines


class LinuxVirtual(Virtual):
    """
    This is a Linux-specific subclass of Virtual.  It defines
    - virtualization_type
    - virtualization_role
    """
    platform = 'Linux'

    # For more information, check: http://people.redhat.com/~rjones/virt-what/
    def get_virtual_facts(self):
        virtual_facts = {}
        # lxc/docker
        if os.path.exists('/proc/1/cgroup'):
            for line in get_file_lines('/proc/1/cgroup'):
                if re.search(r'/docker(/|-[0-9a-f]+\.scope)', line):
                    virtual_facts['virtualization_type'] = 'docker'
                    virtual_facts['virtualization_role'] = 'guest'
                    return virtual_facts
                if re.search('/lxc/', line) or re.search('/machine.slice/machine-lxc', line):
                    virtual_facts['virtualization_type'] = 'lxc'
                    virtual_facts['virtualization_role'] = 'guest'
                    return virtual_facts

        # lxc does not always appear in cgroups anymore but sets 'container=lxc' environment var, requires root privs
        if os.path.exists('/proc/1/environ'):
            for line in get_file_lines('/proc/1/environ'):
                if re.search('container=lxc', line):
                    virtual_facts['virtualization_type'] = 'lxc'
                    virtual_facts['virtualization_role'] = 'guest'
                    return virtual_facts

        if os.path.exists('/proc/vz') and not os.path.exists('/proc/lve'):
            virtual_facts['virtualization_type'] = 'openvz'
            if os.path.exists('/proc/bc'):
                virtual_facts['virtualization_role'] = 'host'
            else:
                virtual_facts['virtualization_role'] = 'guest'
            return virtual_facts

        systemd_container = get_file_content('/run/systemd/container')
        if systemd_container:
            virtual_facts['virtualization_type'] = systemd_container
            virtual_facts['virtualization_role'] = 'guest'
            return virtual_facts

        if os.path.exists("/proc/xen"):
            virtual_facts['virtualization_type'] = 'xen'
            virtual_facts['virtualization_role'] = 'guest'
            try:
                for line in get_file_lines('/proc/xen/capabilities'):
                    if "control_d" in line:
                        virtual_facts['virtualization_role'] = 'host'
            except IOError:
                pass
            return virtual_facts

        # assume guest for this block
        virtual_facts['virtualization_role'] = 'guest'

        product_name = get_file_content('/sys/devices/virtual/dmi/id/product_name')

        if product_name in ('KVM', 'Bochs'):
            virtual_facts['virtualization_type'] = 'kvm'
            return virtual_facts

        if product_name == 'RHEV Hypervisor':
            virtual_facts['virtualization_type'] = 'RHEV'
            return virtual_facts

        if product_name in ('VMware Virtual Platform', 'VMware7,1'):
            virtual_facts['virtualization_type'] = 'VMware'
            return virtual_facts

        if product_name in ('OpenStack Compute', 'OpenStack Nova'):
            virtual_facts['virtualization_type'] = 'openstack'
            return virtual_facts

        bios_vendor = get_file_content('/sys/devices/virtual/dmi/id/bios_vendor')

        if bios_vendor == 'Xen':
            virtual_facts['virtualization_type'] = 'xen'
            return virtual_facts

        if bios_vendor == 'innotek GmbH':
            virtual_facts['virtualization_type'] = 'virtualbox'
            return virtual_facts

        if bios_vendor in ('Amazon EC2', 'Hetzner'):
            virtual_facts['virtualization_type'] = 'kvm'
            return virtual_facts

        sys_vendor = get_file_content('/sys/devices/virtual/dmi/id/sys_vendor')

        KVM_SYS_VENDORS = ('QEMU', 'oVirt', 'Amazon EC2', 'Google', 'Scaleway')
        if sys_vendor in KVM_SYS_VENDORS:
            virtual_facts['virtualization_type'] = 'kvm'
            return virtual_facts

        # FIXME: This does also match hyperv
        if sys_vendor == 'Microsoft Corporation':
            virtual_facts['virtualization_type'] = 'VirtualPC'
            return virtual_facts

        if sys_vendor == 'Parallels Software International Inc.':
            virtual_facts['virtualization_type'] = 'parallels'
            return virtual_facts

        if sys_vendor == 'OpenStack Foundation':
            virtual_facts['virtualization_type'] = 'openstack'
            return virtual_facts

        # unassume guest
        del virtual_facts['virtualization_role']

        if os.path.exists('/proc/self/status'):
            for line in get_file_lines('/proc/self/status'):
                if re.match(r'^VxID:\s+\d+', line):
                    virtual_facts['virtualization_type'] = 'linux_vserver'
                    if re.match(r'^VxID:\s+0', line):
                        virtual_facts['virtualization_role'] = 'host'
                    else:
                        virtual_facts['virtualization_role'] = 'guest'
                    return virtual_facts

        if os.path.exists('/proc/cpuinfo'):
            for line in get_file_lines('/proc/cpuinfo'):
                if re.match('^model name.*QEMU Virtual CPU', line):
                    virtual_facts['virtualization_type'] = 'kvm'
                elif re.match('^vendor_id.*User Mode Linux', line):
                    virtual_facts['virtualization_type'] = 'uml'
                elif re.match('^model name.*UML', line):
                    virtual_facts['virtualization_type'] = 'uml'
                elif re.match('^machine.*CHRP IBM pSeries .emulated by qemu.', line):
                    virtual_facts['virtualization_type'] = 'kvm'
                elif re.match('^vendor_id.*PowerVM Lx86', line):
                    virtual_facts['virtualization_type'] = 'powervm_lx86'
                elif re.match('^vendor_id.*IBM/S390', line):
                    virtual_facts['virtualization_type'] = 'PR/SM'
                    lscpu = self.module.get_bin_path('lscpu')
                    if lscpu:
                        rc, out, err = self.module.run_command(["lscpu"])
                        if rc == 0:
                            for line in out.splitlines():
                                data = line.split(":", 1)
                                key = data[0].strip()
                                if key == 'Hypervisor':
                                    virtual_facts['virtualization_type'] = data[1].strip()
                    else:
                        virtual_facts['virtualization_type'] = 'ibm_systemz'
                else:
                    continue
                if virtual_facts['virtualization_type'] == 'PR/SM':
                    virtual_facts['virtualization_role'] = 'LPAR'
                else:
                    virtual_facts['virtualization_role'] = 'guest'
                return virtual_facts

        # Beware that we can have both kvm and virtualbox running on a single system
        if os.path.exists("/proc/modules") and os.access('/proc/modules', os.R_OK):
            modules = []
            for line in get_file_lines("/proc/modules"):
                data = line.split(" ", 1)
                modules.append(data[0])

            if 'kvm' in modules:
                virtual_facts['virtualization_type'] = 'kvm'
                virtual_facts['virtualization_role'] = 'host'

                if os.path.isdir('/rhev/'):
                    # Check whether this is a RHEV hypervisor (is vdsm running ?)
                    for f in glob.glob('/proc/[0-9]*/comm'):
                        try:
                            with open(f) as virt_fh:
                                comm_content = virt_fh.read().rstrip()
                            if comm_content == 'vdsm':
                                virtual_facts['virtualization_type'] = 'RHEV'
                                break
                        except Exception:
                            pass

                return virtual_facts

            if 'vboxdrv' in modules:
                virtual_facts['virtualization_type'] = 'virtualbox'
                virtual_facts['virtualization_role'] = 'host'
                return virtual_facts

            if 'virtio' in modules:
                virtual_facts['virtualization_type'] = 'kvm'
                virtual_facts['virtualization_role'] = 'guest'
                return virtual_facts

        # In older Linux Kernel versions, /sys filesystem is not available
        # dmidecode is the safest option to parse virtualization related values
        dmi_bin = self.module.get_bin_path('dmidecode')
        # We still want to continue even if dmidecode is not available
        if dmi_bin is not None:
            (rc, out, err) = self.module.run_command('%s -s system-product-name' % dmi_bin)
            if rc == 0:
                # Strip out commented lines (specific dmidecode output)
                vendor_name = ''.join([line.strip() for line in out.splitlines() if not line.startswith('#')])
                if vendor_name.startswith('VMware'):
                    virtual_facts['virtualization_type'] = 'VMware'
                    virtual_facts['virtualization_role'] = 'guest'
                    return virtual_facts

        # If none of the above matches, return 'NA' for virtualization_type
        # and virtualization_role. This allows for proper grouping.
        virtual_facts['virtualization_type'] = 'NA'
        virtual_facts['virtualization_role'] = 'NA'

        return virtual_facts


class LinuxVirtualCollector(VirtualCollector):
    _fact_class = LinuxVirtual
    _platform = 'Linux'
