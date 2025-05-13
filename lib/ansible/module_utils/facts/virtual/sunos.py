# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os

from ansible.module_utils.facts.virtual.base import Virtual, VirtualCollector


class SunOSVirtual(Virtual):
    """
    This is a SunOS-specific subclass of Virtual.  It defines
    - virtualization_type
    - virtualization_role
    - container
    """
    platform = 'SunOS'

    def get_virtual_facts(self):
        virtual_facts = {}
        host_tech = set()
        guest_tech = set()

        # Check if it's a zone
        zonename = self.module.get_bin_path('zonename')
        if zonename:
            rc, out, err = self.module.run_command(zonename)
            if rc == 0:
                if out.rstrip() == "global":
                    host_tech.add('zone')
                else:
                    guest_tech.add('zone')
                    virtual_facts['container'] = 'zone'

        # Check if it's a branded zone (i.e. Solaris 8/9 zone)
        if os.path.isdir('/.SUNWnative'):
            guest_tech.add('zone')
            virtual_facts['container'] = 'zone'

        # If it's a zone check if we can detect if our global zone is itself virtualized.
        # Relies on the "guest tools" (e.g. vmware tools) to be installed
        if 'container' in virtual_facts and virtual_facts['container'] == 'zone':
            modinfo = self.module.get_bin_path('modinfo')
            if modinfo:
                rc, out, err = self.module.run_command(modinfo)
                if rc == 0:
                    for line in out.splitlines():
                        if 'VMware' in line:
                            guest_tech.add('vmware')
                            virtual_facts['virtualization_type'] = 'vmware'
                            virtual_facts['virtualization_role'] = 'guest'
                        if 'VirtualBox' in line:
                            guest_tech.add('virtualbox')
                            virtual_facts['virtualization_type'] = 'virtualbox'
                            virtual_facts['virtualization_role'] = 'guest'

        if os.path.exists('/proc/vz'):
            guest_tech.add('virtuozzo')
            virtual_facts['virtualization_type'] = 'virtuozzo'
            virtual_facts['virtualization_role'] = 'guest'

        # Detect domaining on Sparc hardware
        virtinfo = self.module.get_bin_path('virtinfo')
        if virtinfo:
            # The output of virtinfo is different whether we are on a machine with logical
            # domains ('LDoms') on a T-series or domains ('Domains') on a M-series. Try LDoms first.
            rc, out, err = self.module.run_command([virtinfo, '-p'])
            # The output contains multiple lines with different keys like this:
            #   DOMAINROLE|impl=LDoms|control=false|io=false|service=false|root=false
            # The output may also be not formatted and the returncode is set to 0 regardless of the error condition:
            #   virtinfo can only be run from the global zone
            if rc == 0:
                try:
                    for line in out.splitlines():
                        fields = line.split('|')
                        if fields[0] == 'DOMAINROLE' and fields[1] == 'impl=LDoms':
                            guest_tech.add('ldom')
                            virtual_facts['virtualization_type'] = 'ldom'
                            virtual_facts['virtualization_role'] = 'guest'
                            hostfeatures = []
                            for field in fields[2:]:
                                arg = field.split('=')
                                if arg[1] == 'true':
                                    hostfeatures.append(arg[0])
                            if len(hostfeatures) > 0:
                                virtual_facts['virtualization_role'] = 'host (' + ','.join(hostfeatures) + ')'
                except ValueError:
                    pass

        else:
            smbios = self.module.get_bin_path('smbios')
            if not smbios:
                return
            rc, out, err = self.module.run_command(smbios)
            if rc == 0:
                for line in out.splitlines():
                    if 'VMware' in line:
                        guest_tech.add('vmware')
                        virtual_facts['virtualization_type'] = 'vmware'
                        virtual_facts['virtualization_role'] = 'guest'
                    elif 'Parallels' in line:
                        guest_tech.add('parallels')
                        virtual_facts['virtualization_type'] = 'parallels'
                        virtual_facts['virtualization_role'] = 'guest'
                    elif 'VirtualBox' in line:
                        guest_tech.add('virtualbox')
                        virtual_facts['virtualization_type'] = 'virtualbox'
                        virtual_facts['virtualization_role'] = 'guest'
                    elif 'HVM domU' in line:
                        guest_tech.add('xen')
                        virtual_facts['virtualization_type'] = 'xen'
                        virtual_facts['virtualization_role'] = 'guest'
                    elif 'KVM' in line:
                        guest_tech.add('kvm')
                        virtual_facts['virtualization_type'] = 'kvm'
                        virtual_facts['virtualization_role'] = 'guest'

        virtual_facts['virtualization_tech_guest'] = guest_tech
        virtual_facts['virtualization_tech_host'] = host_tech
        return virtual_facts


class SunOSVirtualCollector(VirtualCollector):
    _fact_class = SunOSVirtual
    _platform = 'SunOS'
