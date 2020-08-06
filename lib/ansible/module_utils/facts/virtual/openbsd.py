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

from ansible.module_utils.facts.virtual.base import Virtual, VirtualCollector
from ansible.module_utils.facts.virtual.sysctl import VirtualSysctlDetectionMixin

from ansible.module_utils.facts.utils import get_file_content


class OpenBSDVirtual(Virtual, VirtualSysctlDetectionMixin):
    """
    This is a OpenBSD-specific subclass of Virtual.  It defines
    - virtualization_type
    - virtualization_role
    """
    platform = 'OpenBSD'
    DMESG_BOOT = '/var/run/dmesg.boot'

    def get_virtual_facts(self):
        virtual_facts = {}
        host_tech = set()
        guest_tech = set()

        # Set empty values as default
        virtual_facts['virtualization_type'] = ''
        virtual_facts['virtualization_role'] = ''

        virtual_product_facts = self.detect_virt_product('hw.product')
        guest_tech.update(virtual_product_facts['virtualization_tech_guest'])
        host_tech.update(virtual_product_facts['virtualization_tech_host'])
        virtual_facts.update(virtual_product_facts)

        virtual_vendor_facts = self.detect_virt_vendor('hw.vendor')
        guest_tech.update(virtual_vendor_facts['virtualization_tech_guest'])
        host_tech.update(virtual_vendor_facts['virtualization_tech_host'])

        if virtual_facts['virtualization_type'] == '':
            virtual_facts.update(virtual_vendor_facts)

        # Check the dmesg if vmm(4) attached, indicating the host is
        # capable of virtualization.
        dmesg_boot = get_file_content(OpenBSDVirtual.DMESG_BOOT)
        for line in dmesg_boot.splitlines():
            match = re.match('^vmm0 at mainbus0: (SVM/RVI|VMX/EPT)$', line)
            if match:
                host_tech.add('vmm')
                virtual_facts['virtualization_type'] = 'vmm'
                virtual_facts['virtualization_role'] = 'host'

        virtual_facts['virtualization_tech_guest'] = guest_tech
        virtual_facts['virtualization_tech_host'] = host_tech
        return virtual_facts


class OpenBSDVirtualCollector(VirtualCollector):
    _fact_class = OpenBSDVirtual
    _platform = 'OpenBSD'
