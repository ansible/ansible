# Collect facts related to system service manager and init.
#
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
import platform
import re

from ansible.module_utils._text import to_native

from ansible.module_utils.facts.utils import get_file_content
from ansible.module_utils.facts.collector import BaseFactCollector

# The distutils module is not shipped with SUNWPython on Solaris.
# It's in the SUNWPython-devel package which also contains development files
# that don't belong on production boxes.  Since our Solaris code doesn't
# depend on LooseVersion, do not import it on Solaris.
if platform.system() != 'SunOS':
    from distutils.version import LooseVersion


class ServiceMgrFactCollector(BaseFactCollector):
    name = 'service_mgr'
    _fact_ids = set()
    required_facts = set(['platform', 'distribution'])

    @staticmethod
    def is_systemd_managed(module):
        # tools must be installed
        if module.get_bin_path('systemctl'):

            # this should show if systemd is the boot init system, if checking init faild to mark as systemd
            # these mirror systemd's own sd_boot test http://www.freedesktop.org/software/systemd/man/sd_booted.html
            for canary in ["/run/systemd/system/", "/dev/.run/systemd/", "/dev/.systemd/"]:
                if os.path.exists(canary):
                    return True
        return False

    def collect(self, module=None, collected_facts=None):
        facts_dict = {}

        if not module:
            return facts_dict

        collected_facts = collected_facts or {}
        service_mgr_name = None

        # TODO: detect more custom init setups like bootscripts, dmd, s6, Epoch, etc
        # also other OSs other than linux might need to check across several possible candidates

        # Mapping of proc_1 values to more useful names
        proc_1_map = {
            'procd': 'openwrt_init',
            'runit-init': 'runit',
            'svscan': 'svc',
            'openrc-init': 'openrc',
        }

        # try various forms of querying pid 1
        proc_1 = get_file_content('/proc/1/comm')
        if proc_1 is None:
            # FIXME: return code isnt checked
            # FIXME: if stdout is empty string, odd things
            # FIXME: other code seems to think we could get proc_1 == None past this point
            rc, proc_1, err = module.run_command("ps -p 1 -o comm|tail -n 1", use_unsafe_shell=True)
            # If the output of the command starts with what looks like a PID, then the 'ps' command
            # probably didn't work the way we wanted, probably because it's busybox
            if re.match(r' *[0-9]+ ', proc_1):
                proc_1 = None

        # The ps command above may return "COMMAND" if the user cannot read /proc, e.g. with grsecurity
        if proc_1 == "COMMAND\n":
            proc_1 = None

        # FIXME: empty string proc_1 staus empty string
        if proc_1 is not None:
            proc_1 = os.path.basename(proc_1)
            proc_1 = to_native(proc_1)
            proc_1 = proc_1.strip()

        if proc_1 is not None and (proc_1 == 'init' or proc_1.endswith('sh')):
            # many systems return init, so this cannot be trusted, if it ends in 'sh' it probalby is a shell in a container
            proc_1 = None

        # if not init/None it should be an identifiable or custom init, so we are done!
        if proc_1 is not None:
            # Lookup proc_1 value in map and use proc_1 value itself if no match
            # FIXME: empty string still falls through
            service_mgr_name = proc_1_map.get(proc_1, proc_1)

        # FIXME: replace with a system->service_mgr_name map?
        # start with the easy ones
        elif collected_facts.get('ansible_distribution', None) == 'MacOSX':
            # FIXME: find way to query executable, version matching is not ideal
            if LooseVersion(platform.mac_ver()[0]) >= LooseVersion('10.4'):
                service_mgr_name = 'launchd'
            else:
                service_mgr_name = 'systemstarter'
        elif 'BSD' in collected_facts.get('ansible_system', '') or collected_facts.get('ansible_system') in ['Bitrig', 'DragonFly']:
            # FIXME: we might want to break out to individual BSDs or 'rc'
            service_mgr_name = 'bsdinit'
        elif collected_facts.get('ansible_system') == 'AIX':
            service_mgr_name = 'src'
        elif collected_facts.get('ansible_system') == 'SunOS':
            service_mgr_name = 'smf'
        elif collected_facts.get('ansible_distribution') == 'OpenWrt':
            service_mgr_name = 'openwrt_init'
        elif collected_facts.get('ansible_system') == 'Linux':
            # FIXME: mv is_systemd_managed
            if self.is_systemd_managed(module=module):
                service_mgr_name = 'systemd'
            elif module.get_bin_path('initctl') and os.path.exists("/etc/init/"):
                service_mgr_name = 'upstart'
            elif os.path.exists('/sbin/openrc'):
                service_mgr_name = 'openrc'
            elif os.path.exists('/etc/init.d/'):
                service_mgr_name = 'sysvinit'

        if not service_mgr_name:
            # if we cannot detect, fallback to generic 'service'
            service_mgr_name = 'service'

        facts_dict['service_mgr'] = service_mgr_name
        return facts_dict
