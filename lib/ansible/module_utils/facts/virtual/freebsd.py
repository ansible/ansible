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

import os

from ansible.module_utils.facts.virtual.base import Virtual, VirtualCollector
from ansible.module_utils.facts.virtual.sysctl import VirtualSysctlDetectionMixin


class FreeBSDVirtual(Virtual, VirtualSysctlDetectionMixin):
    """
    This is a FreeBSD-specific subclass of Virtual.  It defines
    - virtualization_type
    - virtualization_role
    """
    platform = 'FreeBSD'

    def get_virtual_facts(self):
        virtual_facts = {}
        host_tech = set()
        guest_tech = set()

        # Set empty values as default
        virtual_facts['virtualization_type'] = ''
        virtual_facts['virtualization_role'] = ''

        if os.path.exists('/dev/xen/xenstore'):
            guest_tech.add('xen')
            virtual_facts['virtualization_type'] = 'xen'
            virtual_facts['virtualization_role'] = 'guest'

        kern_vm_guest = self.detect_virt_product('kern.vm_guest')
        guest_tech.update(kern_vm_guest['virtualization_tech_guest'])
        host_tech.update(kern_vm_guest['virtualization_tech_host'])

        hw_hv_vendor = self.detect_virt_product('hw.hv_vendor')
        guest_tech.update(hw_hv_vendor['virtualization_tech_guest'])
        host_tech.update(hw_hv_vendor['virtualization_tech_host'])

        sec_jail_jailed = self.detect_virt_product('security.jail.jailed')
        guest_tech.update(sec_jail_jailed['virtualization_tech_guest'])
        host_tech.update(sec_jail_jailed['virtualization_tech_host'])

        if virtual_facts['virtualization_type'] == '':
            sysctl = kern_vm_guest or hw_hv_vendor or sec_jail_jailed
            # We call update here, then re-set virtualization_tech_host/guest
            # later.
            virtual_facts.update(sysctl)

        virtual_vendor_facts = self.detect_virt_vendor('hw.model')
        guest_tech.update(virtual_vendor_facts['virtualization_tech_guest'])
        host_tech.update(virtual_vendor_facts['virtualization_tech_host'])

        if virtual_facts['virtualization_type'] == '':
            virtual_facts.update(virtual_vendor_facts)

        virtual_facts['virtualization_tech_guest'] = guest_tech
        virtual_facts['virtualization_tech_host'] = host_tech
        return virtual_facts


class FreeBSDVirtualCollector(VirtualCollector):
    _fact_class = FreeBSDVirtual
    _platform = 'FreeBSD'
