# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2017 Fortinet, Inc
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import socket
import ssl
import struct

import pydevd

# BEGIN STATIC DATA / MESSAGES
class FSMMethods:
    GET = "get"
    SET = "set"
    EXEC = "exec"
    EXECUTE = "exec"
    UPDATE = "update"
    ADD = "add"
    DELETE = "delete"
    REPLACE = "replace"
    CLONE = "clone"
    MOVE = "move"


BASE_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

class SyslogFacility:
  """Syslog facilities"""
  KERN, USER, MAIL, DAEMON, AUTH, SYSLOG, \
  LPR, NEWS, UUCP, CRON, AUTHPRIV, FTP = range(12)

  LOCAL0, LOCAL1, LOCAL2, LOCAL3, \
  LOCAL4, LOCAL5, LOCAL6, LOCAL7 = range(16, 24)

class SyslogLevel:
  """Syslog levels"""
  EMERG, ALERT, CRIT, ERR, \
  WARNING, NOTICE, INFO, DEBUG = range(8)


# FSM URL ENDPOINTS
class FSMEndpoints:
    GET_CMDB_SHORT = "/phoenix/rest/cmdbDeviceInfo/devices"
    GET_CMDB_IPRANGE = "/phoenix/rest/cmdbDeviceInfo/devices?includeIps="
    GET_CMDB_DETAILED_SINGLE = "/phoenix/rest/cmdbDeviceInfo/device?ip="
    PUT_SUBMIT_REPORT = "/phoenix/rest/query/eventQuery"
    GET_REPORT_PROGRESS = "/phoenix/rest/query/progress/"
    GET_REPORT_RESULTS = "/phoenix/rest/query/events/"
    GET_ORGS = "/phoenix/rest/config/Domain"
    ADD_ORGS = "/phoenix/rest/organization/add"
    UPDATE_ORGS = "/phoenix/rest/organization/update"
    GET_CREDS = "/phoenix/rest/config/credential"
    SET_CREDS = "/phoenix/rest/deviceMon/updateCredential"
    SET_DISCOVERY = "/phoenix/rest/deviceMon/discover"
    GET_DISCOVERY = "/phoenix/rest/deviceMon/status?taskId="
    GET_MONITORED_DEVICES = "/phoenix/rest/deviceInfo/monitoredDevices"
    UPDATE_DEVICE_MONITORING = "/phoenix/rest/deviceMon/updateMonitor"
    SET_MAINTENANCE = "/phoenix/rest/deviceMaint/update"
    DEL_MAINTENANCE = "/phoenix/rest/deviceMaint/delete"
    GET_USERS = "/phoenix/rest/config/user"
    GET_REPORTS = "/phoenix/rest/config/report"
    GET_NETWORKS = "/phoenix/rest/config/network"
    GET_GROUPS = "/phoenix/rest/config/group"
    GET_BIZSERVICES = "/phoenix/rest/cmdb/bizServices"

# FSM RETURN CODES
FSM_RC = {
    "fsm_return_codes": {
        100: {"msg": "Continue - Request received, please continue",
              "changed": False,
              "stop_on_success": True},
        101: {"msg": "Switching Protocols - Switching to new protocol; obey Upgrade header",
              "changed": False,
              "stop_on_success": True},
        200: {"msg": "OK - Request fulfilled, document follows",
              "changed": True,
              "stop_on_success": True},
        201: {"msg": "Created - Document created, URL follows",
              "changed": True,
              "stop_on_success": True},
        202: {"msg": "Accepted - Request accepted, processing continues off-line",
              "changed": True,
              "stop_on_success": True},
        203: {"msg": "Non-Authoritative Information - Request fulfilled from cache",
              "changed": True,
              "stop_on_success": True},
        204: {"msg": "No Content - Request fulfilled, nothing follows",
              "changed": True,
              "stop_on_success": True},
        205: {"msg": "Reset Content - Clear input form for further input.",
              "changed": True,
              "stop_on_success": True},
        206: {"msg": "Partial Content - Partial content follows.",
              "changed": True,
              "stop_on_success": True},
        300: {"msg": "Multiple Choices - Object has several resources -- see URI list",
              "changed": False,
              "stop_on_success": True},
        301: {"msg": "Moved Permanently - Object moved permanently -- see URI list",
              "changed": False,
              "stop_on_success": True},
        302: {"msg": "Found - Object moved temporarily -- see URI list",
              "changed": False,
              "stop_on_success": True},
        303: {"msg": "See Other - Object moved -- see Method and URL list",
              "changed": False,
              "stop_on_success": True},
        304: {"msg": "Not Modified - Document has not changed since given time",
              "changed": False,
              "stop_on_success": True},
        305: {"msg": "Use Proxy - You must use proxy specified in Location to access this resource.",
              "changed": False,
              "stop_on_success": True},
        307: {"msg": "Temporary Redirect - Object moved temporarily -- see URI list",
              "changed": False,
              "stop_on_success": True},
        400: {"msg": "Bad Request - Bad request syntax or unsupported method",
              "changed": False,
              "stop_on_success": True},
        401: {"msg": "Unauthorized - No permission -- see authorization schemes",
              "changed": False,
              "stop_on_success": True},
        402: {"msg": "Payment Required - No payment -- see charging schemes",
              "changed": False,
              "stop_on_success": True},
        403: {"msg": "Forbidden - Request forbidden -- authorization will not help",
              "changed": False,
              "stop_on_success": True},
        404: {"msg": "Not Found - Nothing matches the given URI",
              "changed": False,
              "stop_on_success": True},
        405: {"msg": "Method Not Allowed - Specified method is invalid for this server.",
              "changed": False,
              "stop_on_success": True},
        406: {"msg": "Not Acceptable - URI not available in preferred format.",
              "changed": False,
              "stop_on_success": True},
        407: {"msg": "Proxy Authentication Required - You must authenticate with this proxy before proceeding.",
              "changed": False,
              "stop_on_success": True},
        408: {"msg": "Request Timeout - Request timed out; try again later.",
              "changed": False,
              "stop_on_success": True},
        409: {"msg": "Conflict - Request conflict.",
              "changed": False,
              "stop_on_success": True},
        410: {"msg": "Gone - URI no longer exists and has been permanently removed.",
              "changed": False,
              "stop_on_success": True},
        411: {"msg": "Length Required - Client must specify Content-Length.",
              "changed": False,
              "stop_on_success": True},
        412: {"msg": "Precondition Failed - Precondition in headers is false.",
              "changed": False,
              "stop_on_success": True},
        413: {"msg": "Request Entity Too Large - Entity is too large.",
              "changed": False,
              "stop_on_success": True},
        414: {"msg": "Request-URI Too Long - URI is too long.",
              "changed": False,
              "stop_on_success": True},
        415: {"msg": "Unsupported Media Type - Entity body in unsupported format.",
              "changed": False,
              "stop_on_success": True},
        416: {"msg": "Requested Range Not Satisfiable - Cannot satisfy request range.",
              "changed": False,
              "stop_on_success": True},
        417: {"msg": "Expectation Failed - Expect condition could not be satisfied.",
              "changed": False,
              "stop_on_success": True},
        500: {"msg": "Internal Server Error - Server got itself in trouble",
              "changed": False,
              "stop_on_success": True},
        501: {"msg": "Not Implemented - Server does not support this operation",
              "changed": False,
              "stop_on_success": True},
        502: {"msg": "Bad Gateway - Invalid responses from another server/proxy.",
              "changed": False,
              "stop_on_success": True},
        503: {"msg": "Service Unavailable - The server cannot process the request due to a high load",
              "changed": False,
              "stop_on_success": True},
        504: {"msg": "Gateway Timeout - The gateway server did not receive a timely response",
              "changed": False,
              "stop_on_success": True},
        505: {"msg": "HTTP Version Not Supported - Cannot fulfill request.",
              "changed": False,
              "stop_on_success": True},
    }
}

# FSM GENERIC CREDENTIAL ACCESS METHODS
FSMCredentialAccessMethods = [
    'ftp',
    'ftp_over_ssl',
    'http',
    'https',
    'imap',
    'jdbc',
    'jmx',
    'kafka_api',
    'ldap',
    'ldaps',
    'ldap_start_tls',
    'pop3',
    'pop_over_ssl',
    'smtp',
    'smtp_over_ssl',
    'smtp_over_tls',
    'snmp',
    'snmp_v3',
    'ssh',
    'telnet',
    'vm_sdk'
]

DEFAULT_RESULT_OBJ = (-100000, {"msg": "Nothing Happened. Check that handle_response is being called!"})
FAIL_SOCKET_MSG = {"msg": "Socket Path Empty! The persistent connection manager is messed up. "
                   "Try again in a few moments."}
DEFAULT_EXIT_MSG = {"msg": "Module ended without a call to fsm.govern_response() that resulted in an exit. "
                           "This shouldn't happen. Please report to @ftntcorecse on Github."}

# DEFAULT REPORTS

# ## ALL DEVICES EVENT TYPES AND COUNT LAST 12 HOURS
RPT_ALL_DEVICES_EVENT_TYPE_COUNTS = '<?xml version="1.0" encoding="UTF-8"?><Reports><Report baseline="" rsSync="">' \
                                    '<Name>All Devices Reporting Events Last 12 Hours</Name><Description>All Devices ' \
                                    'Reporting Events Last 12 Hours - 05:07:22 PM Apr 16 2019</Description>' \
                                    '<CustomerScope groupByEachCustomer="true">' \
                                    '<Include>1</Include>' \
                                    '<Exclude/>' \
                                    '</CustomerScope>' \
                                    '<SelectClause>' \
                                    '<AttrList>reptDevIpAddr,eventType,eventName,COUNT(*)</AttrList>' \
                                    '</SelectClause>' \
                                    '<PatternClause>' \
                                    '<SubPattern id="2446600" name="">' \
                                    '<SingleEvtConstr>(reptDevIpAddr = <IP_TO_VERIFY>)' \
                                    '</SingleEvtConstr>' \
                                    '<GroupByAttr>reptDevIpAddr,eventType,eventName</GroupByAttr>' \
                                    '</SubPattern>' \
                                    '</PatternClause>' \
                                    '</Report>' \
                                    '</Reports>'


# BEGIN ERROR EXCEPTIONS
class FSMBaseException(Exception):
    """Wrapper to catch the unexpected"""

    def __init__(self, msg=None, *args, **kwargs):
        if msg is None:
            msg = "An exception occurred within the fortisiem.py httpapi connection plugin."
        super(FSMBaseException, self).__init__(msg, *args)

# END ERROR CLASSES


# BEGIN CLASSES
class FSMCommon(object):

    @staticmethod
    def split_comma_strings_into_lists(obj):
        """
        Splits a CSV String into a list.  Also takes a dictionary, and converts any CSV strings in any key, to a list.

        :param obj: object in CSV format to be parsed.
        :type obj: str or dict

        :return: A list containing the CSV items.
        :rtype: list
        """
        return_obj = ()
        if isinstance(obj, dict):
            if len(obj) > 0:
                for k, v in obj.items():
                    if isinstance(v, str):
                        new_list = list()
                        if "," in v:
                            new_items = v.split(",")
                            for item in new_items:
                                new_list.append(item.strip())
                            obj[k] = new_list
                return_obj = obj
        elif isinstance(obj, str):
            return_obj = obj.replace(" ", "").split(",")

        return return_obj

    @staticmethod
    def cidr_to_netmask(cidr):
        """
        Converts a CIDR Network string to full blown IP/Subnet format in decimal format.
        Decided not use IP Address module to keep includes to a minimum.

        :param cidr: String object in CIDR format to be processed
        :type cidr: str

        :return: A string object that looks like this "x.x.x.x/y.y.y.y"
        :rtype: str
        """
        if isinstance(cidr, str):
            cidr = int(cidr)
            mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
            return (str((0xff000000 & mask) >> 24) + '.'
                    + str((0x00ff0000 & mask) >> 16) + '.'
                    + str((0x0000ff00 & mask) >> 8) + '.'
                    + str((0x000000ff & mask)))

    @staticmethod
    def paramgram_child_list_override(list_overrides, paramgram, module):
        """
        If a list of items was provided to a "parent" paramgram attribute, the paramgram needs to be rewritten.
        The child keys of the desired attribute need to be deleted, and then that "parent" keys' contents is replaced
        With the list of items that was provided.

        :param list_overrides: Contains the response from the FortiSIEM.
        :type list_overrides: list
        :param paramgram: Contains the paramgram passed to the modules' local modify function.
        :type paramgram: dict
        :param module: Contains the Ansible Module Object being used by the module.
        :type module: classObject

        :return: A new "paramgram" refactored to allow for multiple entries being added.
        :rtype: dict
        """
        if len(list_overrides) > 0:
            for list_variable in list_overrides:
                try:
                    list_variable = list_variable.replace("-", "_")
                    override_data = module.params[list_variable]
                    if override_data:
                        del paramgram[list_variable]
                        paramgram[list_variable] = override_data
                except BaseException as e:
                    raise FSMBaseException("Error occurred merging custom lists for the paramgram parent: " + str(e))
        return paramgram

    @staticmethod
    def local_syslog(module, msg):
        try:
            module.log(msg=msg)
        except BaseException:
            pass

    @staticmethod
    def get_ip_list_from_range(start, end):
        ipstruct = struct.Struct('>I')
        start, = ipstruct.unpack(socket.inet_aton(start))
        end, = ipstruct.unpack(socket.inet_aton(end))
        return [socket.inet_ntoa(ipstruct.pack(i)) for i in range(start, end + 1)]


class SendSyslog(object):
    """
    A syslog client that logs to a remote server via multiple protocols.
    """

    def __init__(self,
                 host="localhost",
                 port=514,
                 facility=SyslogFacility.DAEMON,
                 protocol="",
                 ssl_context=None,):
        self.host = host
        self.port = port
        self.facility = facility
        self.protocol = protocol
        self.ssl_context = ssl_context
        self.create_socket()

    def create_socket(self):
        """

        :return:
        """
        if self.protocol == "udp":
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if self.protocol == "udp-tls1.2":
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                ssock = self.ssl_context.wrap_socket(sock)
                self.socket = ssock
            except BaseException as err:
                raise FSMBaseException(err)
        if self.protocol == "tcp":
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.protocol == "tcp-tls1.2":
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(15)
                ssock = self.ssl_context.wrap_socket(sock)
                self.socket = ssock
            except BaseException as err:
                raise FSMBaseException(err)


    def create_full_message(self, header, message, level):
        """

        :param header:
        :param message:
        :param level:
        :return:
        """
        message = "<%d>%s" % (level + self.facility * 8, str(header + " host:" + socket.gethostname() + " | " + message))
        return message

    def send(self, header, message, level):
        """

        :param header:
        :param message:
        :param level:
        :return:
        """
        data = self.create_full_message(header, message, level)
        if self.protocol in ["udp", "udp-tls1.2"]:
            try:
                self.socket.sendto(data, (self.host, self.port))
            except BaseException as err:
                raise FSMBaseException(msg="Failed to send datagram to UDP syslog server. Error: " + str(err))
        if self.protocol in ["tcp", "tcp-tls1.2"]:
            try:
                self.socket.connect((self.host, self.port))
            except BaseException as err:
                raise FSMBaseException(msg="Failed to connect to TCP syslog server. Error: " + str(err))
            try:
                self.socket.sendall(data)
            except BaseException as err:
                raise FSMBaseException(msg="Failed to send data to TCP syslog server. Error: " + str(err))
            try:
                self.socket.close()
            except BaseException as err:
                raise FSMBaseException(msg="Failed to close connection to TCP server. Error: " + str(err))

        return {"status": "OK", "message": str(data)}

# RECURSIVE FUNCTIONS START
def prepare_dict(obj):
    """
    Removes any keys from a dictionary that are only specific to our use in the module. FortiSIEM will reject
    requests with these empty/None keys in it.

    :param obj: Dictionary object to be processed.
    :type obj: dict

    :return: Processed dictionary.
    :rtype: dict
    """

    list_of_elems = ["mode", "adom", "host", "username", "password"]

    if isinstance(obj, dict):
        obj = dict((key, prepare_dict(value)) for (key, value) in obj.items() if key not in list_of_elems)
    return obj


def scrub_dict(obj):
    """
    Removes any keys from a dictionary that are EMPTY -- this includes parent keys. FortiSIEM doesn't
    like empty keys in dictionaries

    :param obj: Dictionary object to be processed.
    :type obj: dict

    :return: Processed dictionary.
    :rtype: dict
    """

    if isinstance(obj, dict):
        return dict((k, scrub_dict(v)) for k, v in obj.items() if v and scrub_dict(v))
    else:
        return obj
