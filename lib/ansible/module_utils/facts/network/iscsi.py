# iSCSI initiator related facts collection for Ansible.
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
import subprocess

from ansible.module_utils.facts.utils import get_file_content
from ansible.module_utils.facts.network.base import NetworkCollector


class IscsiInitiatorNetworkCollector(NetworkCollector):
    name = 'iscsi'
    _fact_ids = set()

    def collect(self, module=None, collected_facts=None):
        """
        Example of contents of /etc/iscsi/initiatorname.iscsi:

        ## DO NOT EDIT OR REMOVE THIS FILE!
        ## If you remove this file, the iSCSI daemon will not start.
        ## If you change the InitiatorName, existing access control lists
        ## may reject this initiator.  The InitiatorName must be unique
        ## for each iSCSI initiator.  Do NOT duplicate iSCSI InitiatorNames.
        InitiatorName=iqn.1993-08.org.debian:01:44a42c8ddb8b

        Example of output from the AIX lsattr command:

        # lsattr -E -l iscsi0
        disc_filename  /etc/iscsi/targets            Configuration file                            False
        disc_policy    file                          Discovery Policy                              True
        initiator_name iqn.localhost.hostid.7f000002 iSCSI Initiator Name                          True
        isns_srvnames  auto                          iSNS Servers IP Addresses                     True
        isns_srvports                                iSNS Servers Port Numbers                     True
        max_targets    16                            Maximum Targets Allowed                       True
        num_cmd_elems  200                           Maximum number of commands to queue to driver True

        Example of output from the HP-UX iscsiutil command:

        #iscsiutil -l
        Initiator Name             : iqn.1986-03.com.hp:mcel_VMhost3.1f355cf6-e2db-11e0-a999-b44c0aef5537
        Initiator Alias            :

        Authentication Method      : None
        CHAP Method                : CHAP_UNI
        Initiator CHAP Name        :
        CHAP Secret                :
        NAS Hostname               :
        NAS Secret                 :
        Radius Server Hostname     :
        Header Digest              : None, CRC32C (default)
        Data Digest                : None, CRC32C (default)
        SLP Scope list for iSLPD   :
        """

        iscsi_facts = {}
        iscsi_facts['iscsi_iqn'] = ""
        if sys.platform.startswith('linux') or sys.platform.startswith('sunos'):
            for line in get_file_content('/etc/iscsi/initiatorname.iscsi', '').splitlines():
                if line.startswith('#') or line.startswith(';') or line.strip() == '':
                    continue
                if line.startswith('InitiatorName='):
                    iscsi_facts['iscsi_iqn'] = line.split('=', 1)[1]
                    break
        elif sys.platform.startswith('aix'):
            if module is not None:
                rc, out, err = module.run_command('/usr/sbin/lsattr -E -l iscsi0 | grep initiator_name')
                if out:
                    iscsi_facts['iscsi_iqn'] = out.split()[1].rstrip()
            else:
                aixcmd = '/usr/sbin/lsattr -E -l iscsi0 | grep initiator_name'
                aixret = subprocess.check_output(aixcmd, shell=True)
                if aixret[0].isalpha():
                    iscsi_facts['iscsi_iqn'] = aixret.split()[1].rstrip()
        elif sys.platform.startswith('hp-ux'):
            if module is not None:
                rc, out, err = module.run_command("/opt/iscsi/bin/iscsiutil -l | grep 'Initiator Name'",
                                                  use_unsafe_shell=True)
                if out:
                    iscsi_facts['iscsi_iqn'] = out.split(":", 1)[1].rstrip()
            else:
                hpuxcmd = "/opt/iscsi/bin/iscsiutil -l | grep 'Initiator Name'"
                hpuxret = subprocess.check_output(hpuxcmd, shell=True)
                if hpuxret[0].isalpha():
                    iscsi_facts['iscsi_iqn'] = hpuxret.split(":", 1)[1].rstrip()
        return iscsi_facts
