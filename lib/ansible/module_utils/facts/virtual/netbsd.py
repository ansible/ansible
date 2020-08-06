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

import os

from ansible.module_utils.facts.virtual.base import Virtual, VirtualCollector
from ansible.module_utils.facts.virtual.sysctl import VirtualSysctlDetectionMixin


class NetBSDVirtual(Virtual, VirtualSysctlDetectionMixin):
    platform = 'NetBSD'

    def get_virtual_facts(self):
        virtual_facts = {}
        host_tech = set()
        guest_tech = set()

        # Set empty values as default
        virtual_facts['virtualization_type'] = ''
        virtual_facts['virtualization_role'] = ''

        virtual_product_facts = self.detect_virt_product('machdep.dmi.system-product')
        guest_tech.update(virtual_product_facts['virtualization_tech_guest'])
        host_tech.update(virtual_product_facts['virtualization_tech_host'])
        virtual_facts.update(virtual_product_facts)

        virtual_vendor_facts = self.detect_virt_vendor('machdep.dmi.system-vendor')
        guest_tech.update(virtual_vendor_facts['virtualization_tech_guest'])
        host_tech.update(virtual_vendor_facts['virtualization_tech_host'])

        if virtual_facts['virtualization_type'] == '':
            virtual_facts.update(virtual_vendor_facts)

        # The above logic is tried first for backwards compatibility. If
        # something above matches, use it. Otherwise if the result is still
        # empty, try machdep.hypervisor.
        virtual_vendor_facts = self.detect_virt_vendor('machdep.hypervisor')
        guest_tech.update(virtual_vendor_facts['virtualization_tech_guest'])
        host_tech.update(virtual_vendor_facts['virtualization_tech_host'])

        if virtual_facts['virtualization_type'] == '':
            virtual_facts.update(virtual_vendor_facts)

        if os.path.exists('/dev/xencons'):
            guest_tech.add('xen')

            if virtual_facts['virtualization_type'] == '':
                virtual_facts['virtualization_type'] = 'xen'
                virtual_facts['virtualization_role'] = 'guest'

        virtual_facts['virtualization_tech_guest'] = guest_tech
        virtual_facts['virtualization_tech_host'] = host_tech
        return virtual_facts


class NetBSDVirtualCollector(VirtualCollector):
    _fact_class = NetBSDVirtual
    _platform = 'NetBSD'
