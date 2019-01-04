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
httpapi : fortimanager
short_description: HttpApi Plugin for Fortinet FortiManager Appliance or VM
description:
  - This HttpApi plugin provides methods to connect to Fortinet FortiManager Appliance or VM via JSON RPC API
version_added: "2.8"
options:
  host:
    type: str
    description:
      - The IP Address or Hostname of the FortiManager host to be used for the connection.
  username:
    type: str
    description:
      - The username to be used for the connection
  password:
    type: str
    description:
      - The password to be used for the connection.
  debug:
    type: bool
    description:
      - Enables Debug Flag.
    required: False
    default: False
  use_ssl:
    type: bool
    description:
      - Enables SSL.
    required: False
    default: True
  verify_ssl:
    type: bool
    description:
      - Enables SSL certification verification.
    required: False
    default: False
  timeout:
    type: int
    description:
      - Sets the timeout in seconds.
    required: False
    default: 300
  disable_request_warnings:
    type: bool
    description:
      - Disables Request library warnings.
    required: False
    default: False

"""

import json
from ansible.plugins.httpapi import HttpApiBase
from ansible.module_utils.basic import to_text
from ansible.module_utils.network.fortimanager.fortimanager import FMGLockContext
from ansible.module_utils.network.fortimanager.common import BASE_HEADERS
from ansible.module_utils.network.fortimanager.common import FMGBaseException
from ansible.module_utils.network.fortimanager.common import FMGValidSessionException
from ansible.module_utils.network.fortimanager.common import FMGValueError
from ansible.module_utils.network.fortimanager.common import FMGResponseNotFormedCorrect
from ansible.module_utils.network.fortimanager.common import FMGRCommon


class HttpApi(HttpApiBase):
    def __init__(self, connection):
        super(HttpApi, self).__init__(connection)
        self.connection = connection
        self._req_id = 0
        self._sid = None
        self._url = None
        self._host = None
        self._lock_ctx = FMGLockContext(self)
        self._tools = FMGRCommon
        self._debug = False
        self._connected_fmgr = None
        self._last_response_msg = None
        self._last_response_code = None
        self._last_data_payload = None
        self._last_url = None
        self._last_response_raw = None

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
        This function will log the plugin into FortiManager, and return the results.
        :param username: Username of FortiManager Admin
        :param password: Password of FortiManager Admin

        :return: Dictionary of status, if it logged in or not.
        """
        self._url = "/jsonrpc"
        self.execute("sys/login/user", login=True, passwd=password, user=username, )

        if "FortiManager object connected to FortiManager" in self.__str__():
            # If Login worked, then inspect the FortiManager for Workspace Mode, and it's system information.
            self.inspect_fmgr()
            return
        else:
            raise FMGBaseException(msg="Unknown error while logging in...connection was lost during login operation...."
                                       " Exiting")

    def inspect_fmgr(self):
        # CHECK FOR WORKSPACE MODE TO SEE IF WE HAVE TO ENABLE ADOM LOCKS
        self._lock_ctx.check_mode()
        # CHECK FOR SYSTEM STATUS -- SHOULD RETURN 0
        status = self.get_system_status()
        if status[0] == -11:
            # THE CONNECTION GOT LOST SOMEHOW, REMOVE THE SID AND REPORT BAD LOGIN
            self.logout()
            raise FMGBaseException(msg="Error -11 -- the Session ID was likely malformed somehow. Contact authors."
                                       " Exiting")
        elif status[0] == 0:
            try:
                self._connected_fmgr = status[1]
                self._host = self._connected_fmgr["Hostname"]
            except BaseException:
                pass
        return

    def logout(self):
        """
        This function will logout of the FortiManager.
        """
        if self.sid is not None:
            if self._lock_ctx.uses_workspace:
                self._lock_ctx.run_unlock()
            ret_code, response = self.execute("sys/logout")
            self.sid = None
            self.connection = None
            return ret_code, response

    def send_request(self, method, params, login=False):
        """
        Responsible for actual sending of data to the connection httpapi base plugin. Does some formatting as well.
        :param params: A formatted dictionary that was returned by self.common_datagram_params()
        before being called here.
        :param method: The preferred API Request method (GET, ADD, POST, etc....)
        :type method: basestring
        :param login: Tells the function that we're attempting a login, and that the self.sid should be empty,
        but to continue anyway. Do not use this unless being called from self.login().

        :return: Dictionary of status, if it logged in or not.
        """
        if self.sid is None and not login:
            raise FMGValidSessionException(method, params)
        self._update_request_id()
        json_request = {
            "method": method,
            "params": params,
            "session": self.sid,
            "id": self.req_id,
            "verbose": 1
        }
        data = json.dumps(json_request, ensure_ascii=False).replace('\\\\', '\\')
        url = str(self._url)
        try:
            # Sending URL and Data in Unicode, per Ansible Specifications for Connection Plugins
            response, response_data = self.connection.send(path=to_text(url), data=to_text(data),
                                                           headers=BASE_HEADERS)
            # Get Unicode Response
            value = self._tools.get_response_value(response_data)
            # Convert Unicode JSON to Dictionary, convert "null" to "None" if required.
            result = eval(value.replace("null", "None"))
            self._update_self_from_response(result, url, data)
            return self._handle_response(result)

        except ValueError as err:
            raise FMGValueError(err)
        except KeyError as err:
            raise FMGResponseNotFormedCorrect(err)
        except IndexError as err:
            raise FMGResponseNotFormedCorrect(err)
        except Exception as err:
            raise FMGBaseException(err)

    def get(self, url, *args, **kwargs):
        return self.send_request("get", self._tools.format_request("get", url, *args, **kwargs))

    def add(self, url, *args, **kwargs):
        return self.send_request("add", self._tools.format_request("add", url, *args, **kwargs))

    def update(self, url, *args, **kwargs):
        return self.send_request("update", self._tools.format_request("update", url, *args, **kwargs))

    def set(self, url, *args, **kwargs):
        return self.send_request("set", self._tools.format_request("set", url, *args, **kwargs))

    def delete(self, url, *args, **kwargs):
        return self.send_request("delete", self._tools.format_request("delete", url, *args, **kwargs))

    def replace(self, url, *args, **kwargs):
        return self.send_request("replace", self._tools.format_request("replace", url, *args, **kwargs))

    def clone(self, url, *args, **kwargs):
        return self.send_request("clone", self._tools.format_request("clone", url, *args, **kwargs))

    def execute(self, url, login=False, *args, **kwargs):
        return self.send_request("exec", self._tools.format_request("execute", url, *args, **kwargs), login)

    def move(self, url, *args, **kwargs):
        return self.send_request("move", self._tools.format_request("move", url, *args, **kwargs))

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

    @property
    def verify_ssl(self):
        return self._verify_ssl

    @verify_ssl.setter
    def verify_ssl(self, val):
        self._verify_ssl = val

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, val):
        self._timeout = val

    def lock_adom(self, adom=None, *args, **kwargs):
        return self._lock_ctx.lock_adom(adom, *args, **kwargs)

    def unlock_adom(self, adom=None, *args, **kwargs):
        return self._lock_ctx.unlock_adom(adom, *args, **kwargs)

    def commit_changes(self, adom=None, aux=False, *args, **kwargs):
        return self._lock_ctx.commit_changes(adom, aux, *args, **kwargs)

    def return_connected_fmgr(self):
        """
        Returns the data stored under self._connected_fmgr

        :return: dict
        """
        try:
            if self._connected_fmgr:
                return self._connected_fmgr
        except BaseException:
            raise FMGBaseException("Couldn't Retrieve Connected FMGR Stats")

    def get_system_status(self):
        """
        Returns the system status page from the FortiManager, for logging and other uses.
        return: status
        """
        status = self.get("sys/status")
        return status

    def __str__(self):
        if self.sid is not None and self.connection._url is not None:
            return "FortiManager object connected to FortiManager: " + str(self.connection._url)
        return "FortiManager object with no valid connection to a FortiManager appliance."
