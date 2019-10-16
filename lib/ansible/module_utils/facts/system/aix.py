# AIX specific facts
# Copyright: (c) 2018, Christian Tremel (@flynn1973)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import sys
import shlex
import os
import platform
import re
import itertools
import subprocess
try:
    import json
except ImportError:
    import simplejson as json


from ansible.module_utils.facts.utils import get_file_content


from ansible.module_utils.facts.collector import BaseFactCollector


class AIXSystemFactCollector(BaseFactCollector):
    """
    Some handy AIX facts, more or less nice to haves
    """
    name = 'aix_system_facts'
    _fact_ids = set()
    _platform = 'AIX'

    def get_lssrc_facts(self, module=None, collected_facts=None):
        """
        'lssrc': [
                  {
                   'Subsystem': 'prngd',
                   'PID': '3211316',
                   'Group': 'prng',
                   'Status': 'active'
                   },
                  {
                   'Subsystem': 'syslogd',
                   'PID': '4849686',
                   'Group': 'ras',
                   'Status': 'active'
                   }
                   ],
        """
        lssrc_facts = {}

        lssrc_facts['lssrc'] = []

        lssrc = []

        rc, out, err = self.module.run_command(["/usr/bin/lssrc", "-a"])
        if rc != 0:
            self.module.fail_json(
                msg="ERROR: Could not run lssrc command",
                rc=rc,
                err=err)
        firstline = True
        for line in out.splitlines():
            for line in out.splitlines():
                if firstline:
                    keys = line.split()
                    firstline = False
                else:
                    values = [line[0:18].strip(), line[18:34].strip(),
                              line[34:48].strip(), line[48:60].strip()]
                    adict = dict(itertools.izip(keys, values))
                    lssrc.append(adict)
        lssrc_facts['lssrc'] = lssrc

        return lssrc_facts

    def get_niminfo_facts(self, module=None, collected_facts=None):
        """
        {'niminfo': [
                     {
                      'NIM_BOS_FORMAT': 'rte',
                      'NIM_CONFIGURATION': 'standalone',
                      'NIM_MOUNTS': '',
                      'NIM_MASTERID': '00FB1A6B4C00',
                      'NIM_NAME': 'aixbuildhostng',
                      'NIM_MASTER_HOSTNAME': 'nimmhs',
                      'NIM_HOSTNAME': 'aixbuildhostng',
                      'NIM_SHELL': 'nimsh',
                      'NIM_MASTER_PORT': '1058',
                      'NIM_HOSTS': '127.0.0.1:loopback:localhost  X.X.14.50:aixbuildhostng  X.X.14.211:nimmhs',
                      'NIM_REGISTRATION_PORT': '1059',
                      'NIM_FIPS_MODE': '0',
                      'NIM_BOS_IMAGE': '/SPOT/usr/sys/inst.images/installp/ppc/bos'
                      }
                      ],
        """
        file = '/etc/niminfo'
        niminfo_facts = {}

        niminfo_facts['niminfo'] = []

        niminfo = []

        try:
            if os.path.exists(file):
                niminfo = dict(
                    (k.strip(), v.strip(' "\n')) for k, v in (
                        line.split(
                            ' ', 1)[1].split(
                            '=', 1) for line in (
                            (l for l in open(
                                file, 'r') if l.startswith('export'))) if not re.match(
                                r'^\s*$', line)))
        except IOError as e:
            self.module.warnings.append('could not read /etc/niminfo')
            niminfo = {}
        niminfo_facts['niminfo'] = [niminfo]

        return niminfo_facts

    def get_lparstat_facts(self, module=None, collected_facts=None):
        """
        {'lparstat': [
                      {
                       'Desired_Virtual_CPUs': '2',
                       'Maximum_Memory': '16384',
                       'Unallocated_Capacity': '0.00',
                       'Partition_Number': '1',
                       'Online_Memory': '16384',
                       'Sub_Processor_Mode': '-',
                       'Maximum_Physical_CPUs_in_system': '12',
                       'Power_Saving_Mode': 'Disabled',
                       'Physical_CPU_Percentage': '10.00',
                       'Target_Memory_Expansion_Size': '16384',
                       'Type': 'Shared-SMT-4',
                       'Online_Virtual_CPUs': '2',
                       'Desired_Capacity': '0.20',
                       'Minimum_Memory': '2048',
                       'Partition_Group-ID': '32769',
                       'Hypervisor_Page_Size': '-',
                       'Active_Physical_CPUs_in_system': '12',
                       'Unallocated_Variable_Memory_Capacity_Weight': '-',
                       'Partition_Name': 'AIXBUILDHOSTNG',
                       'Total_I/O_Memory_Entitlement': '-',
                       'Memory_Group_ID_of_LPAR': '-',
                       'Memory_Mode': 'Dedicated-Expanded',
                       'Active_CPUs_in_Pool': '12',
                       'Maximum_Capacity': '0.50',
                       'Desired_Memory': '16384',
                       'Physical_Memory_in_the_Pool': '-',
                       'Capacity_Increment': '0.01',
                       'Mode': 'Uncapped',
                       'Entitled_Capacity': '0.20',
                       'Maximum_Capacity_of_Pool': '1200',
                       'Variable_Capacity_Weight': '64',
                       'Variable_Memory_Capacity_Weight': '-',
                       'Maximum_Virtual_CPUs': '2',
                       'Minimum_Virtual_CPUs': '1',
                       'Minimum_Capacity': '0.05',
                       'Target_Memory_Expansion_Factor': '1.00',
                       'Node_Name': 'aixbuildhostng',
                       'Memory_Pool_ID': '-',
                       'Desired_Variable_Capacity_Weight': '64',
                       'Shared_Physical_CPUs_in_system': '12',
                       'Unallocated_I/O_Memory_entitlement': '-',
                       'Shared_Pool_ID': '0',
                       'Entitled_Capacity_of_Pool': '110',
                       'Unallocated_Weight': '0'
                       }
                       ],
        """
        lparstat_facts = {}

        lparstat_facts['lparstat'] = []

        lparstat = []

        adict = {}

        rc, out, err = self.module.run_command(["/usr/bin/lparstat", "-i"])
        if rc != 0:
            self.module.fail_json(msg="ERROR: could not run lparstat command", rc=rc,
                                  err=err)
        for line in out.splitlines():
            key, value = line.split(":")
            key = key.strip().replace(' ', '_')
            value = value.strip().split(" ")
            value[0] = value[0].replace('%', '')
            if len(value) == 2:
                if value[1] == 'GB':
                    value[0] = float(value[0]) * 1024
            adict[key] = value[0]
        lparstat.append(adict)
        lparstat_facts['lparstat'] = lparstat

        return lparstat_facts

    def get_uname_facts(self, module=None, collected_facts=None):
        """
        {'uname': [
                   {
                   'model': '8284-22A',
                   'name': 'aixbuildhostng',
                   'lparname': 'AIXBUILDHOSTNG',
                   'lannumber': '4212812876',
                   'lparid': '1',
                   'version': '7',
                   'systemid': '8000020DFB100000',
                   'architecture': 'powerpc',
                   'release': '1',
                   'serial': '02781A6CX',
                   'os': 'AIX',
                   'id': '00FB1A6C4C00'
                   }
                   ],
        """
        options = {
                   "systemid": "-F",
                   "lannumber": "-l",
                   "lpar": "-L",
                   "id": "-m",
                   "model": "-M",
                   "name": "-n",
                   "architecture": "-p",
                   "release": "-r",
                   "os": "-s",
                   "serial": "-u",
                   "version": "-v",
                  }
        uname_facts = {}

        uname_facts['uname'] = []

        uname = {}

        for key in options:
            rc, out, err = self.module.run_command(["/usr/bin/uname", options[key]])
            if rc != 0:
                warning = "failed to execute uname %s" % options[key]
                self.module.warnings.append(warning)
                attribute_dict = {}
            else:
                if key == "lpar":
                    uname["lparid"] = out.strip().split()[0]
                    uname["lparname"] = out.strip().split()[1]
                elif key == "model":
                    uname["model"] = out.strip().split(",")[1]
                elif key == "serial":
                    uname["serial"] = out.strip().split(",")[1]
                else:
                    uname[key] = out.strip()
        uname_facts['uname'] = [uname]

        return uname_facts
