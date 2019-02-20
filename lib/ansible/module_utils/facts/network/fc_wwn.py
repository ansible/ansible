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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import glob

from ansible.module_utils.facts.utils import get_file_lines
from ansible.module_utils.facts.collector import BaseFactCollector


class FcWwnInitiatorFactCollector(BaseFactCollector):
    name = 'fibre_channel_wwn'
    _fact_ids = set()

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
            """
            on solaris 10 or solaris 11 should use `fcinfo hba-port`
            on solaris 9, `prtconf -pv`
            """
            cmd = module.get_bin_path('fcinfo')
            cmd = cmd + " hba-port | grep 'Port WWN'"
            rc, fcinfo_out, err = module.run_command(cmd, use_unsafe_shell=True)
            """
            # fcinfo hba-port  | grep "Port WWN"
            HBA Port WWN: 10000090fa1658de
            """
            if fcinfo_out:
                for line in fcinfo_out.splitlines():
                    data = line.split(' ')
                    fc_facts['fibre_channel_wwn'].append(data[-1].rstrip())
        return fc_facts
