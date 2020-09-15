# Copyright (c) 2018 Fortinet and/or its affiliates.
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
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
author:
    - Luke Weighall (@lweighall)
    - Andrew Welsh (@Ghilli3)
    - Jim Huber (@p4r4n0y1ng)
httpapi : fortianalyzer
short_description: HttpApi Plugin for Fortinet FortiAnalyzer Appliance or VM
description:
  - This HttpApi plugin provides methods to connect to Fortinet FortiAnalyzer Appliance or VM via JSON RPC API
version_added: "2.9"

"""

import json
from ansible.plugins.httpapi import HttpApiBase
from ansible.module_utils.basic import to_text
from ansible.module_utils.network.fortianalyzer.common import BASE_HEADERS
from ansible.module_utils.network.fortianalyzer.common import FAZBaseException
from ansible.module_utils.network.fortianalyzer.common import FAZCommon
from ansible.module_utils.network.fortianalyzer.common import FAZMethods


class HttpApi(HttpApiBase):
    def __init__(self, connection):
        super(HttpApi, self).__init__(connection)
        self._req_id = 0
        self._sid = None
        self._url = "/jsonrpc"
        self._host = None
        self._tools = FAZCommon
        self._debug = False
        self._connected_faz = None
        self._last_response_msg = None
        self._last_response_code = None
        self._last_data_payload = None
        self._last_url = None
        self._last_response_raw = None
        self._locked_adom_list = list()
        self._locked_adoms_by_user = list()
        self._uses_workspace = False
        self._uses_adoms = False
        self._adom_list = list()
        self._logged_in_user = None

    def set_become(self, become_context):
        """
        ELEVATION IS NOT REQUIRED ON FORTINET DEVICES - SKIPPED
        :param become_context: Unused input.
        :return: None
        """
        return None

    def update_auth(self, response, response_data):
        """
        TOKENS ARE NOT USED SO NO NEED TO UPDATE AUTH
        :param response: Unused input.
        :param response_data Unused_input.
        :return: None
        """
        return None

    def login(self, username, password):
        """
        This function will log the plugin into FortiAnalyzer, and return the results.
        :param username: Username of FortiAnalyzer Admin
        :param password: Password of FortiAnalyzer Admin

        :return: Dictionary of status, if it logged in or not.
        """

        self._logged_in_user = username
        self.send_request(FAZMethods.EXEC, self._tools.format_request(FAZMethods.EXEC, "sys/login/user",
                                                                      passwd=password, user=username,))

        if "FortiAnalyzer object connected to FortiAnalyzer" in self.__str__():
            # If Login worked, then inspect the FortiAnalyzer for Workspace Mode, and it's system information.
            self.inspect_faz()
            return
        else:
            raise FAZBaseException(msg="Unknown error while logging in...connection was lost during login operation...."
                                       " Exiting")

    def inspect_faz(self):
        # CHECK FOR WORKSPACE MODE TO SEE IF WE HAVE TO ENABLE ADOM LOCKS
        status = self.get_system_status()
        if status[0] == -11:
            # THE CONNECTION GOT LOST SOMEHOW, REMOVE THE SID AND REPORT BAD LOGIN
            self.logout()
            raise FAZBaseException(msg="Error -11 -- the Session ID was likely malformed somehow. Contact authors."
                                       " Exiting")
        elif status[0] == 0:
            try:
                self.check_mode()
                if self._uses_adoms:
                    self.get_adom_list()
                if self._uses_workspace:
                    self.get_locked_adom_list()
                self._connected_faz = status[1]
                self._host = self._connected_faz["Hostname"]
            except BaseException:
                pass
        return

    def logout(self):
        """
        This function will logout of the FortiAnalyzer.
        """
        if self.sid is not None:
            # IF WE WERE USING WORKSPACES, THEN CLEAN UP OUR LOCKS IF THEY STILL EXIST
            if self.uses_workspace:
                self.get_lock_info()
                self.run_unlock()
            ret_code, response = self.send_request(FAZMethods.EXEC,
                                                   self._tools.format_request(FAZMethods.EXEC, "sys/logout"))
            self.sid = None
            return ret_code, response

    def send_request(self, method, params):
        """
        Responsible for actual sending of data to the connection httpapi base plugin. Does some formatting as well.
        :param params: A formatted dictionary that was returned by self.common_datagram_params()
        before being called here.
        :param method: The preferred API Request method (GET, ADD, POST, etc....)
        :type method: basestring

        :return: Dictionary of status, if it logged in or not.
        """

        try:
            if self.sid is None and params[0]["url"] != "sys/login/user":
                raise FAZBaseException("An attempt was made to login with the SID None and URL != login url.")
        except IndexError:
            raise FAZBaseException("An attempt was made at communicating with a FAZ with "
                                   "no valid session and an incorrectly formatted request.")
        except Exception:
            raise FAZBaseException("An attempt was made at communicating with a FAZ with "
                                   "no valid session and an unexpected error was discovered.")

        self._update_request_id()
        json_request = {
            "method": method,
            "params": params,
            "session": self.sid,
            "id": self.req_id,
            "verbose": 1
        }
        data = json.dumps(json_request, ensure_ascii=False).replace('\\\\', '\\')
        try:
            # Sending URL and Data in Unicode, per Ansible Specifications for Connection Plugins
            response, response_data = self.connection.send(path=to_text(self._url), data=to_text(data),
                                                           headers=BASE_HEADERS)
            # Get Unicode Response - Must convert from StringIO to unicode first so we can do a replace function below
            result = json.loads(to_text(response_data.getvalue()))
            self._update_self_from_response(result, self._url, data)
            return self._handle_response(result)
        except Exception as err:
            raise FAZBaseException(err)

    def _handle_response(self, response):
        self._set_sid(response)
        if isinstance(response["result"], list):
            result = response["result"][0]
        else:
            result = response["result"]
        if "data" in result:
            return result["status"]["code"], result["data"]
        else:
            return result["status"]["code"], result

    def _update_self_from_response(self, response, url, data):
        self._last_response_raw = response
        if isinstance(response["result"], list):
            result = response["result"][0]
        else:
            result = response["result"]
        if "status" in result:
            self._last_response_code = result["status"]["code"]
            self._last_response_msg = result["status"]["message"]
            self._last_url = url
            self._last_data_payload = data

    def _set_sid(self, response):
        if self.sid is None and "session" in response:
            self.sid = response["session"]

    def return_connected_faz(self):
        """
        Returns the data stored under self._connected_faz

        :return: dict
        """
        try:
            if self._connected_faz:
                return self._connected_faz
        except BaseException:
            raise FAZBaseException("Couldn't Retrieve Connected FAZ Stats")

    def get_system_status(self):
        """
        Returns the system status page from the FortiAnalyzer, for logging and other uses.
        return: status
        """
        status = self.send_request(FAZMethods.GET, self._tools.format_request(FAZMethods.GET, "sys/status"))
        return status

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, val):
        self._debug = val

    @property
    def req_id(self):
        return self._req_id

    @req_id.setter
    def req_id(self, val):
        self._req_id = val

    def _update_request_id(self, reqid=0):
        self.req_id = reqid if reqid != 0 else self.req_id + 1

    @property
    def sid(self):
        return self._sid

    @sid.setter
    def sid(self, val):
        self._sid = val

    def __str__(self):
        if self.sid is not None and self.connection._url is not None:
            return "FortiAnalyzer object connected to FortiAnalyzer: " + str(self.connection._url)
        return "FortiAnalyzer object with no valid connection to a FortiAnalyzer appliance."

    ##################################
    # BEGIN DATABASE LOCK CONTEXT CODE
    ##################################

    @property
    def uses_workspace(self):
        return self._uses_workspace

    @uses_workspace.setter
    def uses_workspace(self, val):
        self._uses_workspace = val

    @property
    def uses_adoms(self):
        return self._uses_adoms

    @uses_adoms.setter
    def uses_adoms(self, val):
        self._uses_adoms = val

    def add_adom_to_lock_list(self, adom):
        if adom not in self._locked_adom_list:
            self._locked_adom_list.append(adom)

    def remove_adom_from_lock_list(self, adom):
        if adom in self._locked_adom_list:
            self._locked_adom_list.remove(adom)

    def check_mode(self):
        """
        Checks FortiAnalyzer for the use of Workspace mode
        """
        url = "/cli/global/system/global"
        code, resp_obj = self.send_request(FAZMethods.GET,
                                           self._tools.format_request(FAZMethods.GET,
                                                                      url,
                                                                      fields=["workspace-mode", "adom-status"]))
        try:
            if resp_obj["workspace-mode"] == "workflow":
                self.uses_workspace = True
            elif resp_obj["workspace-mode"] == "disabled":
                self.uses_workspace = False
        except KeyError:
            self.uses_workspace = False
        except BaseException:
            raise FAZBaseException(msg="Couldn't determine workspace-mode in the plugin")
        try:
            if resp_obj["adom-status"] in [1, "enable"]:
                self.uses_adoms = True
            else:
                self.uses_adoms = False
        except KeyError:
            self.uses_adoms = False
        except BaseException:
            raise FAZBaseException(msg="Couldn't determine adom-status in the plugin")

    def run_unlock(self):
        """
        Checks for ADOM status, if locked, it will unlock
        """
        for adom_locked in self._locked_adoms_by_user:
            adom = adom_locked["adom"]
            self.unlock_adom(adom)

    def lock_adom(self, adom=None, *args, **kwargs):
        """
        Locks an ADOM for changes
        """
        if adom:
            if adom.lower() == "global":
                url = "/dvmdb/global/workspace/lock/"
            else:
                url = "/dvmdb/adom/{adom}/workspace/lock/".format(adom=adom)
        else:
            url = "/dvmdb/adom/root/workspace/lock"
        code, respobj = self.send_request(FAZMethods.EXEC, self._tools.format_request(FAZMethods.EXEC, url))
        if code == 0 and respobj["status"]["message"].lower() == "ok":
            self.add_adom_to_lock_list(adom)
        return code, respobj

    def unlock_adom(self, adom=None, *args, **kwargs):
        """
        Unlocks an ADOM after changes
        """
        if adom:
            if adom.lower() == "global":
                url = "/dvmdb/global/workspace/unlock/"
            else:
                url = "/dvmdb/adom/{adom}/workspace/unlock/".format(adom=adom)
        else:
            url = "/dvmdb/adom/root/workspace/unlock"
        code, respobj = self.send_request(FAZMethods.EXEC, self._tools.format_request(FAZMethods.EXEC, url))
        if code == 0 and respobj["status"]["message"].lower() == "ok":
            self.remove_adom_from_lock_list(adom)
        return code, respobj

    def commit_changes(self, adom=None, aux=False, *args, **kwargs):
        """
        Commits changes to an ADOM
        """
        if adom:
            if aux:
                url = "/pm/config/adom/{adom}/workspace/commit".format(adom=adom)
            else:
                if adom.lower() == "global":
                    url = "/dvmdb/global/workspace/commit/"
                else:
                    url = "/dvmdb/adom/{adom}/workspace/commit".format(adom=adom)
        else:
            url = "/dvmdb/adom/root/workspace/commit"
        return self.send_request(FAZMethods.EXEC, self._tools.format_request(FAZMethods.EXEC, url))

    def get_lock_info(self, adom=None):
        """
        Gets ADOM lock info so it can be displayed with the error messages. Or if determined to be locked by ansible
        for some reason, then unlock it.
        """
        if not adom or adom == "root":
            url = "/dvmdb/adom/root/workspace/lockinfo"
        else:
            if adom.lower() == "global":
                url = "/dvmdb/global/workspace/lockinfo/"
            else:
                url = "/dvmdb/adom/{adom}/workspace/lockinfo/".format(adom=adom)
        datagram = {}
        data = self._tools.format_request(FAZMethods.GET, url, **datagram)
        resp_obj = self.send_request(FAZMethods.GET, data)
        code = resp_obj[0]
        if code != 0:
            self._module.fail_json(msg=("An error occurred trying to get the ADOM Lock Info. Error: " + str(resp_obj)))
        elif code == 0:
            try:
                if resp_obj[1]["status"]["message"] == "OK":
                    self._lock_info = None
            except BaseException:
                self._lock_info = resp_obj[1]
        return resp_obj

    def get_adom_list(self):
        """
        Gets the list of ADOMs for the FortiAnalyzer
        """
        if self.uses_adoms:
            url = "/dvmdb/adom"
            datagram = {}
            data = self._tools.format_request(FAZMethods.GET, url, **datagram)
            resp_obj = self.send_request(FAZMethods.GET, data)
            code = resp_obj[0]
            if code != 0:
                self._module.fail_json(msg=("An error occurred trying to get the ADOM Info. Error: " + str(resp_obj)))
            elif code == 0:
                num_of_adoms = len(resp_obj[1])
                append_list = ['root', ]
                for adom in resp_obj[1]:
                    if adom["tab_status"] != "":
                        append_list.append(str(adom["name"]))
                self._adom_list = append_list
            return resp_obj

    def get_locked_adom_list(self):
        """
        Gets the list of locked adoms
        """
        try:
            locked_list = list()
            locked_by_user_list = list()
            for adom in self._adom_list:
                adom_lock_info = self.get_lock_info(adom=adom)
                try:
                    if adom_lock_info[1]["status"]["message"] == "OK":
                        continue
                except BaseException:
                    pass
                try:
                    if adom_lock_info[1][0]["lock_user"]:
                        locked_list.append(str(adom))
                    if adom_lock_info[1][0]["lock_user"] == self._logged_in_user:
                        locked_by_user_list.append({"adom": str(adom), "user": str(adom_lock_info[1][0]["lock_user"])})
                except BaseException as err:
                    raise FAZBaseException(err)
            self._locked_adom_list = locked_list
            self._locked_adoms_by_user = locked_by_user_list

        except BaseException as err:
            raise FAZBaseException(msg=("An error occurred while trying to get the locked adom list. Error: "
                                        + str(err)))

    ################################
    # END DATABASE LOCK CONTEXT CODE
    ################################
