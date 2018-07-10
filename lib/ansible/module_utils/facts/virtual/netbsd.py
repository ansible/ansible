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
        # Set empty values as default
        virtual_facts['virtualization_type'] = ''
        virtual_facts['virtualization_role'] = ''

        virtual_product_facts = self.detect_virt_product('machdep.dmi.system-product')
        virtual_facts.update(virtual_product_facts)

        if virtual_facts['virtualization_type'] == '':
            virtual_vendor_facts = self.detect_virt_vendor('machdep.dmi.system-vendor')
            virtual_facts.update(virtual_vendor_facts)

        if os.path.exists('/dev/xencons'):
            virtual_facts['virtualization_type'] = 'xen'
            virtual_facts['virtualization_role'] = 'guest'

        return virtual_facts


class NetBSDVirtualCollector(VirtualCollector):
    _fact_class = NetBSDVirtual
    _platform = 'NetBSD'
