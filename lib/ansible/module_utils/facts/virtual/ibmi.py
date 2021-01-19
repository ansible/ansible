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

import glob
import os
import re

from ansible.module_utils.facts.virtual.base import Virtual, VirtualCollector
from ansible.module_utils.facts.utils import get_file_content, get_file_lines
from ansible_collections.ibm.power_ibmi.plugins.module_utils.ibmi import ibmi_module as imodule


class IBMiVirtual(Virtual):
    """
    This is a IBMi-specific subclass of Virtual.
    """
    platform = 'OS400'

    def get_virtual_facts(self):
        virtual_facts = {}
        try:
            ibmi_module = imodule.IBMiModule()
        except Exception:
            return virtual_facts
        sql = "SELECT SYSTEM_VALUE_NAME,CURRENT_NUMERIC_VALUE,CURRENT_CHARACTER_VALUE FROM QSYS2.SYSTEM_VALUE_INFO;"
        rc, out, error, job_log = ibmi_module.itoolkit_run_sql_once(sql)
        system_values = {}
        for item in out:
            system_values[item["SYSTEM_VALUE_NAME"]] = item["CURRENT_CHARACTER_VALUE"] if item["CURRENT_CHARACTER_VALUE"] else item["CURRENT_NUMERIC_VALUE"]
        virtual_facts["OS400_SYSTEM_VALUES"] = system_values
        rc, out, error, job_log = ibmi_module.itoolkit_run_sql_once("SELECT * FROM QSYS2.SYSCATALOGS;")
        virtual_facts['OS400_RDBDIRE'] = out
        rc, out, error, job_log = ibmi_module.itoolkit_run_sql_once("SELECT * FROM QSYS2.SYSTEM_STATUS_INFO;")
        virtual_facts['OS400_SYSTEM_STATUS_INFO'] = out
        rc, out, error, job_log = ibmi_module.itoolkit_run_sql_once("SELECT * FROM QSYS2.NETSTAT_INTERFACE_INFO;")
        virtual_facts['OS400_TCPIP_INFO'] = out
        rc, out, error, job_log = ibmi_module.itoolkit_run_sql_once("SELECT * FROM QSYS2.GROUP_PTF_INFO;")
        virtual_facts['OS400_GROUP_PTF_INFO'] = out
        rc, out, error, job_log = ibmi_module.itoolkit_run_sql_once("SELECT CAST(data as VARCHAR(100)) FROM QUSRSYS.QATOCTCPIP WHERE KEYWORD='RMTNAMESV'")
        virtual_facts['OS400_DNS'] = out[0]['00001'].split()
        return virtual_facts


class IBMiVirtualCollector(VirtualCollector):
    _fact_class = IBMiVirtual
    _platform = 'OS400'
