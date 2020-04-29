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


class VirtualSysctlDetectionMixin(object):
    def detect_sysctl(self):
        self.sysctl_path = self.module.get_bin_path('sysctl')

    def detect_virt_product(self, key):
        virtual_product_facts = {}
        self.detect_sysctl()
        if self.sysctl_path:
            rc, out, err = self.module.run_command("%s -n %s" % (self.sysctl_path, key))
            if rc == 0:
                if re.match('(KVM|kvm|Bochs|SmartDC).*', out):
                    virtual_product_facts['virtualization_type'] = 'kvm'
                    virtual_product_facts['virtualization_role'] = 'guest'
                elif re.match('.*VMware.*', out):
                    virtual_product_facts['virtualization_type'] = 'VMware'
                    virtual_product_facts['virtualization_role'] = 'guest'
                elif out.rstrip() == 'VirtualBox':
                    virtual_product_facts['virtualization_type'] = 'virtualbox'
                    virtual_product_facts['virtualization_role'] = 'guest'
                elif out.rstrip() == 'HVM domU':
                    virtual_product_facts['virtualization_type'] = 'xen'
                    virtual_product_facts['virtualization_role'] = 'guest'
                elif out.rstrip() == 'Parallels':
                    virtual_product_facts['virtualization_type'] = 'parallels'
                    virtual_product_facts['virtualization_role'] = 'guest'
                elif out.rstrip() == 'RHEV Hypervisor':
                    virtual_product_facts['virtualization_type'] = 'RHEV'
                    virtual_product_facts['virtualization_role'] = 'guest'
                elif (key == 'security.jail.jailed') and (out.rstrip() == '1'):
                    virtual_product_facts['virtualization_type'] = 'jails'
                    virtual_product_facts['virtualization_role'] = 'guest'

        return virtual_product_facts

    def detect_virt_vendor(self, key):
        virtual_vendor_facts = {}
        self.detect_sysctl()
        if self.sysctl_path:
            rc, out, err = self.module.run_command("%s -n %s" % (self.sysctl_path, key))
            if rc == 0:
                if out.rstrip() == 'QEMU':
                    virtual_vendor_facts['virtualization_type'] = 'kvm'
                    virtual_vendor_facts['virtualization_role'] = 'guest'
                if out.rstrip() == 'OpenBSD':
                    virtual_vendor_facts['virtualization_type'] = 'vmm'
                    virtual_vendor_facts['virtualization_role'] = 'guest'

        return virtual_vendor_facts
