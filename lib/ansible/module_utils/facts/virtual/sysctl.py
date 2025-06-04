# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import re


class VirtualSysctlDetectionMixin:
    def detect_sysctl(self):
        self.sysctl_path = self.module.get_bin_path('sysctl')

    def detect_virt_product(self, key):
        virtual_product_facts = {}
        host_tech = set()
        guest_tech = set()

        # We do similar to what we do in linux.py -- We want to allow multiple
        # virt techs to show up, but maintain compatibility, so we have to track
        # when we would have stopped, even though now we go through everything.
        found_virt = False

        self.detect_sysctl()
        if self.sysctl_path:
            rc, out, err = self.module.run_command("%s -n %s" % (self.sysctl_path, key))
            if rc == 0:
                if re.match('(KVM|kvm|Bochs|SmartDC).*', out):
                    guest_tech.add('kvm')
                    if not found_virt:
                        virtual_product_facts['virtualization_type'] = 'kvm'
                        virtual_product_facts['virtualization_role'] = 'guest'
                        found_virt = True
                if re.match('.*VMware.*', out):
                    guest_tech.add('VMware')
                    if not found_virt:
                        virtual_product_facts['virtualization_type'] = 'VMware'
                        virtual_product_facts['virtualization_role'] = 'guest'
                        found_virt = True
                if out.rstrip() == 'VirtualBox':
                    guest_tech.add('virtualbox')
                    if not found_virt:
                        virtual_product_facts['virtualization_type'] = 'virtualbox'
                        virtual_product_facts['virtualization_role'] = 'guest'
                        found_virt = True
                if re.match('(HVM domU|XenPVH|XenPV|XenPVHVM).*', out):
                    guest_tech.add('xen')
                    if not found_virt:
                        virtual_product_facts['virtualization_type'] = 'xen'
                        virtual_product_facts['virtualization_role'] = 'guest'
                        found_virt = True
                if out.rstrip() == 'Hyper-V':
                    guest_tech.add('Hyper-V')
                    if not found_virt:
                        virtual_product_facts['virtualization_type'] = 'Hyper-V'
                        virtual_product_facts['virtualization_role'] = 'guest'
                        found_virt = True
                if out.rstrip() == 'Parallels':
                    guest_tech.add('parallels')
                    if not found_virt:
                        virtual_product_facts['virtualization_type'] = 'parallels'
                        virtual_product_facts['virtualization_role'] = 'guest'
                        found_virt = True
                if out.rstrip() == 'RHEV Hypervisor':
                    guest_tech.add('RHEV')
                    if not found_virt:
                        virtual_product_facts['virtualization_type'] = 'RHEV'
                        virtual_product_facts['virtualization_role'] = 'guest'
                        found_virt = True
                if (key == 'security.jail.jailed') and (out.rstrip() == '1'):
                    guest_tech.add('jails')
                    if not found_virt:
                        virtual_product_facts['virtualization_type'] = 'jails'
                        virtual_product_facts['virtualization_role'] = 'guest'
                        found_virt = True

        virtual_product_facts['virtualization_tech_guest'] = guest_tech
        virtual_product_facts['virtualization_tech_host'] = host_tech
        return virtual_product_facts

    def detect_virt_vendor(self, key):
        virtual_vendor_facts = {}
        host_tech = set()
        guest_tech = set()
        self.detect_sysctl()
        if self.sysctl_path:
            rc, out, err = self.module.run_command("%s -n %s" % (self.sysctl_path, key))
            if rc == 0:
                if out.rstrip() == 'QEMU':
                    guest_tech.add('kvm')
                    virtual_vendor_facts['virtualization_type'] = 'kvm'
                    virtual_vendor_facts['virtualization_role'] = 'guest'
                if out.rstrip() == 'OpenBSD':
                    guest_tech.add('vmm')
                    virtual_vendor_facts['virtualization_type'] = 'vmm'
                    virtual_vendor_facts['virtualization_role'] = 'guest'

        virtual_vendor_facts['virtualization_tech_guest'] = guest_tech
        virtual_vendor_facts['virtualization_tech_host'] = host_tech
        return virtual_vendor_facts
