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

HAS_ITOOLKIT = True
HAS_IBM_DB = True

try:
    from itoolkit import iToolKit
    from itoolkit import iSqlFree
    from itoolkit import iSqlFetch
    from itoolkit import iSqlQuery
    from itoolkit import iCmd
    from itoolkit import iCmd5250
    from itoolkit.transport import DatabaseTransport
    from itoolkit.transport import DirectTransport
except ImportError:
    HAS_ITOOLKIT = False

try:
    import ibm_db_dbi as dbi
except ImportError:
    HAS_IBM_DB = False


IBMi_COMMAND_RC_SUCCESS = 0
IBMi_COMMAND_RC_UNEXPECTED = 999
IBMi_COMMAND_RC_ERROR = 255
IBMi_COMMAND_RC_ITOOLKIT_NO_KEY_JOBLOG = 256
IBMi_COMMAND_RC_ITOOLKIT_NO_KEY_ERROR = 257
IBMi_COMMAND_RC_UNEXPECTED_ROW_COUNT = 258
IBMi_COMMAND_RC_INVALID_EXPECTED_ROW_COUNT = 259


def interpret_return_code(rc):
    if rc == IBMi_COMMAND_RC_SUCCESS:
        return 'Success'
    elif rc == IBMi_COMMAND_RC_ERROR:
        return 'Generic failure'
    elif rc == IBMi_COMMAND_RC_UNEXPECTED:
        return 'Unexpected error'
    elif rc == IBMi_COMMAND_RC_ITOOLKIT_NO_KEY_JOBLOG:
        return "iToolKit result dict does not have key 'joblog'"
    elif rc == IBMi_COMMAND_RC_ITOOLKIT_NO_KEY_ERROR:
        return "iToolKit result dict does not have key 'error'"
    else:
        return "Unknown error"


def itoolkit_run_sql(conn, sql):
    out_list = []
    rc = ''
    try:
        itransport = DatabaseTransport(conn)
        itool = iToolKit()
        itool.add(iSqlQuery('query', sql, {'error': 'on'}))
        itool.add(iSqlFetch('fetch'))
        itool.add(iSqlFree('free'))
        itool.call(itransport)
        command_output = itool.dict_out('fetch')
        command_error = ''
        error = ''
        out = ''
        if 'error' not in command_output:
            rc = IBMi_COMMAND_RC_SUCCESS
            out = command_output['row']
            if isinstance(out, dict):
                out_list.append(out)
            elif isinstance(out, list):
                out_list = out
        else:
            command_error = command_output['error']
            if 'joblog' in command_error:
                rc = IBMi_COMMAND_RC_ERROR
                error = command_error['joblog']
            else:
                # should not be here, must xmlservice has internal error
                rc = IBMi_COMMAND_RC_ITOOLKIT_NO_KEY_JOBLOG
                error = "iToolKit result dict does not have key 'joblog', the output is %s" % command_output
    except Exception as e_db_connect:
        raise Exception(str(e_db_connect))
    return rc, interpret_return_code(rc), out_list, error


class IBMiVirtual(Virtual):
    """
    This is a IBMi-specific subclass of Virtual.
    """
    platform = 'OS400'

    def get_virtual_facts(self):
        if HAS_ITOOLKIT:
            virtual_facts = {}
            connection = dbi.connect()
            sql = "SELECT SYSTEM_VALUE_NAME,CURRENT_NUMERIC_VALUE,CURRENT_CHARACTER_VALUE FROM QSYS2.SYSTEM_VALUE_INFO"
            rc, rc_msg, out, error = itoolkit_run_sql(connection, sql)
            system_values = {}
            for item in out:
                system_values[item["SYSTEM_VALUE_NAME"]] = item["CURRENT_CHARACTER_VALUE"] if item["CURRENT_CHARACTER_VALUE"] else item["CURRENT_NUMERIC_VALUE"]
            virtual_facts["OS400_SYSTEM_VALUES"] = system_values
            rc, rc_msg, out, error = itoolkit_run_sql(connection, "SELECT * FROM QSYS2.SYSCATALOGS")
            virtual_facts['OS400_RDBDIRE'] = out
            rc, rc_msg, out, error = itoolkit_run_sql(connection, "SELECT * FROM QSYS2.SYSTEM_STATUS_INFO")
            virtual_facts['OS400_SYSTEM_STATUS_INFO'] = out
            rc, rc_msg, out, error = itoolkit_run_sql(connection, "SELECT * FROM QSYS2.NETSTAT_INTERFACE_INFO")
            virtual_facts['OS400_NETSTAT_INTERFACE_INFO'] = out
            rc, rc_msg, out, error = itoolkit_run_sql(connection, "SELECT * FROM QSYS2.GROUP_PTF_INFO")
            virtual_facts['OS400_GROUP_PTF_INFO'] = out

            connection.close()
            return virtual_facts


class IBMiVirtualCollector(VirtualCollector):
    _fact_class = IBMiVirtual
    _platform = 'OS400'
