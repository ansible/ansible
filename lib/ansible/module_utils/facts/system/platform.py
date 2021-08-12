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
import socket
import platform

from ansible.module_utils.facts.utils import get_file_content

from ansible.module_utils.facts.collector import BaseFactCollector

# i86pc is a Solaris and derivatives-ism
SOLARIS_I86_RE_PATTERN = r'i([3456]86|86pc)'
solaris_i86_re = re.compile(SOLARIS_I86_RE_PATTERN)


class PlatformFactCollector(BaseFactCollector):
    name = 'platform'
    _fact_ids = set(['system',
                     'kernel',
                     'kernel_version',
                     'machine',
                     'python_version',
                     'architecture',
                     'machine_id'])

    def _get_hostname_cli_info(self, module):
        r = {}
        HOSTNAMES = {'hostname': '', 'short': '-s', 'dnsdomainname': '-f', 'domainname': '-d', 'nisdomainname': '--nis', 'nodename': '-n', 'ypdomainname': '-y', 'ip': '-i'}
        hostname_bin = module.get_bin_path('hostname')
        if hostname_bin:
            r['info'] = hostname_bin
            for name in HOSTNAMES.keys():
                rc, out, err = module.run_command([hostname_bin, HOSTNAMES[name]])
                if rc !=0 or not out:
                    r[name] = ''
                else:
                    data = out.splitlines()
                    r[name]  = data[0]
        else:
            r['info'] = 'No hostname CLI found'
            for name in HOSTNAMES.keys():
                r[name] = ''
        return r

    def collect(self, module=None, collected_facts=None):
        platform_facts = {}
        # platform.system() can be Linux, Darwin, Java, or Windows
        platform_facts['system'] = platform.system()
        platform_facts['kernel'] = platform.release()
        platform_facts['kernel_version'] = platform.version()
        platform_facts['machine'] = platform.machine()

        platform_facts['python_version'] = platform.python_version()

        platform_facts['fqdn'] = socket.getfqdn()
        platform_facts['hostname'] = platform.node().split('.')[0]
        platform_facts['nodename'] = platform.node()

        platform_facts['domain'] = '.'.join(platform_facts['fqdn'].split('.')[1:])

        # because every method is inconsistent across platforms, lets try hostname cli also
        platform_facts['hostname_cli'] = self._get_hostname_cli_info(module)

        arch_bits = platform.architecture()[0]

        platform_facts['userspace_bits'] = arch_bits.replace('bit', '')
        if platform_facts['machine'] == 'x86_64':
            platform_facts['architecture'] = platform_facts['machine']
            if platform_facts['userspace_bits'] == '64':
                platform_facts['userspace_architecture'] = 'x86_64'
            elif platform_facts['userspace_bits'] == '32':
                platform_facts['userspace_architecture'] = 'i386'
        elif solaris_i86_re.search(platform_facts['machine']):
            platform_facts['architecture'] = 'i386'
            if platform_facts['userspace_bits'] == '64':
                platform_facts['userspace_architecture'] = 'x86_64'
            elif platform_facts['userspace_bits'] == '32':
                platform_facts['userspace_architecture'] = 'i386'
        else:
            platform_facts['architecture'] = platform_facts['machine']

        if platform_facts['system'] == 'AIX':
            # Attempt to use getconf to figure out architecture
            # fall back to bootinfo if needed
            getconf_bin = module.get_bin_path('getconf')
            if getconf_bin:
                rc, out, err = module.run_command([getconf_bin, 'MACHINE_ARCHITECTURE'])
                data = out.splitlines()
                platform_facts['architecture'] = data[0]
            else:
                bootinfo_bin = module.get_bin_path('bootinfo')
                rc, out, err = module.run_command([bootinfo_bin, '-p'])
                data = out.splitlines()
                platform_facts['architecture'] = data[0]
        elif platform_facts['system'] == 'OpenBSD':
            platform_facts['architecture'] = platform.uname()[5]

        machine_id = get_file_content("/var/lib/dbus/machine-id") or get_file_content("/etc/machine-id")
        if machine_id:
            machine_id = machine_id.splitlines()[0]
            platform_facts["machine_id"] = machine_id

        return platform_facts
