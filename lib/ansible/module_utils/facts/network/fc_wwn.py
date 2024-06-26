# Fibre Channel WWN initiator related facts collection for ansible.
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

from __future__ import annotations

import sys
import glob

import ansible.module_utils.compat.typing as t

from ansible.module_utils.facts.utils import get_file_lines
from ansible.module_utils.facts.collector import BaseFactCollector


class FcWwnInitiatorFactCollector(BaseFactCollector):
    name = 'fibre_channel_wwn'
    _fact_ids = set()  # type: t.Set[str]

    def collect(self, module=None, collected_facts=None):
        """
        Example contents /sys/class/fc_host/*/port_name:

        0x21000014ff52a9bb

        """

        fc_facts = {}
        fc_facts['fibre_channel_wwn'] = []
        if sys.platform.startswith('linux'):
            for fcfile in glob.glob('/sys/class/fc_host/*/port_name'):
                for line in get_file_lines(fcfile):
                    fc_facts['fibre_channel_wwn'].append(line.rstrip()[2:])
        elif sys.platform.startswith('sunos'):
            # on solaris 10 or solaris 11 should use `fcinfo hba-port`
            # TBD (not implemented): on solaris 9 use `prtconf -pv`
            cmd = module.get_bin_path('fcinfo')
            if cmd:
                cmd = cmd + " hba-port"
                rc, fcinfo_out, err = module.run_command(cmd)
                # fcinfo hba-port  | grep "Port WWN"
                # HBA Port WWN: 10000090fa1658de
                if rc == 0 and fcinfo_out:
                    for line in fcinfo_out.splitlines():
                        if 'Port WWN' in line:
                            data = line.split(' ')
                            fc_facts['fibre_channel_wwn'].append(data[-1].rstrip())
        elif sys.platform.startswith('aix'):
            cmd = module.get_bin_path('lsdev')
            lscfg_cmd = module.get_bin_path('lscfg')
            if cmd and lscfg_cmd:
                # get list of available fibre-channel devices (fcs)
                cmd = cmd + " -Cc adapter -l fcs*"
                rc, lsdev_out, err = module.run_command(cmd)
                if rc == 0 and lsdev_out:
                    for line in lsdev_out.splitlines():
                        # if device is available (not in defined state), get its WWN
                        if 'Available' in line:
                            data = line.split(' ')
                            cmd = lscfg_cmd + " -vl %s" % data[0]
                            rc, lscfg_out, err = module.run_command(cmd)
                            # example output
                            # lscfg -vpl fcs3 | grep "Network Address"
                            #        Network Address.............10000090FA551509
                            if rc == 0 and lscfg_out:
                                for line in lscfg_out.splitlines():
                                    if 'Network Address' in line:
                                        data = line.split('.')
                                        fc_facts['fibre_channel_wwn'].append(data[-1].rstrip())
        elif sys.platform.startswith('hp-ux'):
            cmd = module.get_bin_path('ioscan')
            fcmsu_cmd = module.get_bin_path(
                'fcmsutil',
                opt_dirs=['/opt/fcms/bin'],
            )
            # go ahead if we have both commands available
            if cmd and fcmsu_cmd:
                # ioscan / get list of available fibre-channel devices (fcd)
                cmd = cmd + " -fnC FC"
                rc, ioscan_out, err = module.run_command(cmd)
                if rc == 0 and ioscan_out:
                    for line in ioscan_out.splitlines():
                        line = line.strip()
                        if '/dev/fcd' in line:
                            dev = line.split(' ')
                            # get device information
                            cmd = fcmsu_cmd + " %s" % dev[0]
                            rc, fcmsutil_out, err = module.run_command(cmd)
                            # lookup the following line
                            #             N_Port Port World Wide Name = 0x50060b00006975ec
                            if rc == 0 and fcmsutil_out:
                                for line in fcmsutil_out.splitlines():
                                    if 'N_Port Port World Wide Name' in line:
                                        data = line.split('=')
                                        fc_facts['fibre_channel_wwn'].append(data[-1].strip())
        return fc_facts
