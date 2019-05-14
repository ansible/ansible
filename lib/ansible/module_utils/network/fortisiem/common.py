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
<<<<<<< HEAD
<<<<<<< HEAD
import datetime
import struct
import ssl
import json
import xml.dom.minidom
import re
import xmltodict


# BEGIN STATIC DATA / MESSAGES
class FSMMethods:
    """
    A static list of methods.
    """
=======
import ssl
=======
import datetime
>>>>>>> Full FSM Commit. Ready for shippable tests.
import struct
import ssl
import json
import xml.dom.minidom
import re


# BEGIN STATIC DATA / MESSAGES
class FSMMethods:
<<<<<<< HEAD
>>>>>>> Full FSM Commit
=======
    """
    A static list of methods.
    """
>>>>>>> Full FSM Commit. Ready for shippable tests.
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

<<<<<<< HEAD
<<<<<<< HEAD

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
=======
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
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
>>>>>>> Full FSM Commit


# FSM URL ENDPOINTS
class FSMEndpoints:
<<<<<<< HEAD
<<<<<<< HEAD
    """
    UNIVERSAL REFERENCE TO ENDPOINTS. CHANGE HERE AND CHANGE FOR ALL MODULES.
    """
=======
>>>>>>> Full FSM Commit
=======
    """
    UNIVERSAL REFERENCE TO ENDPOINTS. CHANGE HERE AND CHANGE FOR ALL MODULES.
    """
>>>>>>> Full FSM Commit. Ready for shippable tests.
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

<<<<<<< HEAD

=======
>>>>>>> Full FSM Commit
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
<<<<<<< HEAD
                          "Try again in a few moments."}
DEFAULT_EXIT_MSG = {"msg": "Module ended without a call to fsm.govern_response() that resulted in an exit. "
                           "This shouldn't happen. Please report to @ftntcorecse on Github."}

=======
                   "Try again in a few moments."}
DEFAULT_EXIT_MSG = {"msg": "Module ended without a call to fsm.govern_response() that resulted in an exit. "
                           "This shouldn't happen. Please report to @ftntcorecse on Github."}

<<<<<<< HEAD
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

>>>>>>> Full FSM Commit
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.

# BEGIN ERROR EXCEPTIONS
class FSMBaseException(Exception):
    """Wrapper to catch the unexpected"""

    def __init__(self, msg=None, *args, **kwargs):
        if msg is None:
            msg = "An exception occurred within the fortisiem.py httpapi connection plugin."
        super(FSMBaseException, self).__init__(msg, *args)

<<<<<<< HEAD

# END ERROR CLASSES


<<<<<<< HEAD
# try:
#     import xmltodict
#
#     HAS_XML2DICT = True
# except ImportError as err:
#     HAS_XML2DICT = False
#     raise FSMBaseException(
#         "You don't really want to use XML for responses, do you? We use with JSON in these parts. "
#         "XML2DICT Package is not installed. Please use 'pip install xmltodict. ")
=======
try:
    import xmltodict
    HAS_XML2DICT = True
except ImportError as err:
    HAS_XML2DICT = False
    raise FSMBaseException(
        "You don't really want to use XML for responses, do you? We use with JSON in these parts. "
        "XML2DICT Package is not installed. Please use 'pip install xmltodict. ")
>>>>>>> Full FSM Commit. Ready for shippable tests.


# BEGIN CLASSES
class FSMCommon(object):
    """
    A collection of static methods that are commonly used between FortiSIEM modules.
    """
<<<<<<< HEAD
=======
# END ERROR CLASSES


# BEGIN CLASSES
class FSMCommon(object):
>>>>>>> Full FSM Commit
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.

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
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.
        """
        Creates a local log entry in the linux computer running this. Logs through ansible module methods.

        :param module: the module object to log through
        :param msg: the message to log
        """
<<<<<<< HEAD
=======
>>>>>>> Full FSM Commit
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.
        try:
            module.log(msg=msg)
        except BaseException:
            pass

    @staticmethod
    def get_ip_list_from_range(start, end):
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.
        """
        Take an IP range like this: x.x.x.x-x.x.x.x and turns it into a list of individual IPs in the range specified.

        :param start: start ip address of range
        :param end: end ip address of range
        :return: list
        """
<<<<<<< HEAD
=======
>>>>>>> Full FSM Commit
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.
        ipstruct = struct.Struct('>I')
        start, = ipstruct.unpack(socket.inet_aton(start))
        end, = ipstruct.unpack(socket.inet_aton(end))
        return [socket.inet_ntoa(ipstruct.pack(i)) for i in range(start, end + 1)]

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.
    @staticmethod
    def score_device_verification(return_dict):
        """
        Takes the results from fsm_verify_device module, and scores them.

        :param return_dict: the formatted dictionary results from the fsm_verify_device module.

        :return: dict
        """

        points_per_100_events = 10
        points_per_event_types = 10
        points_per_discover_methods = 20
        points_per_missing_item = -10
        points_per_present_item = 10
        bad_score = 100
        ok_score = 200
        good_score = 300
        great_score = 500

        score = 0
        try:
            score += (points_per_100_events * (return_dict["json_results"]["Num of Events"] / 100))
        except BaseException:
            pass
        try:
            score += (points_per_event_types * (return_dict["json_results"]["Distinct Event Types"]))
        except BaseException:
            pass
        try:
            discover_methods = str(return_dict["json_results"]["Discover Methods"])
            score += (points_per_discover_methods * len((discover_methods.split(","))))
        except BaseException:
            pass
        try:
            score += (points_per_missing_item * (len(return_dict["json_results"]["missing_items"])))
        except BaseException:
            pass
        try:
            score += (points_per_present_item * (len(return_dict["json_results"]["present_items"])))
        except BaseException:
            pass
        verified_dict = return_dict
        verified_dict["json_results"]["score"] = score
        if score < 0:
            verified_dict["json_results"]["verified_status"] = "MISSING"
        if score > 0 and score < bad_score:
            verified_dict["json_results"]["verified_status"] = "BAD"
        if score > bad_score and score < ok_score:
            verified_dict["json_results"]["verified_status"] = "OK"
        if score > ok_score and score < good_score:
            verified_dict["json_results"]["verified_status"] = "GOOD"
        if score > good_score and score < great_score:
            verified_dict["json_results"]["verified_status"] = "GREAT"
        if score > great_score:
            verified_dict["json_results"]["verified_status"] = "AWESOME"
        return verified_dict

    @staticmethod
    def append_file_with_device_results(results, file_path):
        """
        Specific to fsm_verify_device module. Writes the results of a devices score, to a file, in append mode.

        :param results: results to write.
        :param file_path: file path to append to.
        """
        # CHECK IF FILE EXISTS
        fh_contents = None
        try:
            fh = open(file_path, 'r')
            fh_contents = fh.read()
            fh.close()
        except:
            pass
        # BASED ON THAT TEST, EITHER APPEND, OR OPEN A NEW FILE AND WRITE THE CSV HEADER
        if fh_contents:
            f = open(file_path, "a+")
            append_string = str(results["json_results"]["Access IP"]) + \
                            "," + str(results["json_results"]["score"]) + \
                            "," + str(results["json_results"]["verified_status"]) + \
                            "," + str(results["json_results"]["Name"]) + \
                            "," + str(results["json_results"]["Distinct Event Types"]) + \
                            "," + str(results["json_results"]["Num of Events"])
            try:
                missing_list = results["json_results"]["missing_items"]
                append_string = append_string + "," + "-".join(missing_list)
            except:
                pass
            try:
                present_list = results["json_results"]["present_items"]
                append_string = append_string + "," + "-".join(present_list)
            except:
                pass
            append_string = append_string + "\n"
            f.write(append_string)
            f.close()
        else:
            f = open(file_path, "w")
            f.write("ip, score, verified_status, Name, DistinctEventTypes, NumOfEvents, missing, present\n")
            append_string = str(results["json_results"]["Access IP"]) + \
                            "," + str(results["json_results"]["score"]) + \
                            "," + str(results["json_results"]["verified_status"]) + \
                            "," + str(results["json_results"]["Name"]) + \
                            "," + str(results["json_results"]["Distinct Event Types"]) + \
                            "," + str(results["json_results"]["Num of Events"])
            try:
                missing_list = results["json_results"]["missing_items"]
                append_string = append_string + "," + "-".join(missing_list)
            except:
                pass
            try:
                present_list = results["json_results"]["present_items"]
                append_string = append_string + "," + "-".join(present_list)
            except:
                pass
            append_string = append_string + "\n"
            f.write(append_string)
            f.close()

    @staticmethod
    def get_event_count_for_specific_ip(events):
        """
        Specific to fsm_verify_device module.
        Counts a list that's really a dictionary of events. So we're counting dictionaries. Returns count of events.

        :param events: event dictionary to count
        :return: int
        """
        event_count = 0
        try:
            for item in events["json_results"]:
                try:
                    current_count = int(item["COUNT(*)"])
                    event_count += current_count
                except:
                    pass
        except:
            pass

        return event_count

    @staticmethod
    def get_events_info_for_specific_ip(events):
        """
        Specific to fsm_verify_device module.
        Converts a dictionary of events into a list of events.

        :param events: dict
        :return: list
        """
        return_events = []
        try:
            for item in events["json_results"]:
                event_dict = {
                    "event_type": item["eventType"],
                    "event_name": item["eventName"],
                    "count": item["COUNT(*)"]
                }
                return_events.append(event_dict)
        except:
            pass

        return return_events

    @staticmethod
    def get_monitors_summary_for_short_all(results):
        """
        Adds monitor-specific counters to the results from this modules output, but for a range of devices.

        :param results: dict
        :return: dict
        """
        return_dict = results
        num_of_event_pulling_devices = 0
        num_of_event_pulling_monitors = 0
        num_of_perf_mon_devices = 0
        num_of_perf_mon_monitors = 0
        try:
            for event_device in results["json_results"]["monitoredDevices"]["perfMonDevices"]["device"]:
                num_of_event_pulling_devices += 1
                for monitor in event_device["monitors"]["monitor"]:
                    num_of_event_pulling_monitors += 1
        except:
            pass
        try:
            for perf_mon_device in results["json_results"]["monitoredDevices"]["eventPullingDevices"]["device"]:
                num_of_perf_mon_devices += 1
                for monitor in event_device["monitors"]["monitor"]:
                    num_of_perf_mon_monitors += 1
        except:
            pass

        return_dict["json_results"]["summary"] = {
            "num_of_event_pulling_devices": str(num_of_event_pulling_devices),
            "num_of_event_pulling_monitors": str(num_of_event_pulling_monitors),
            "num_of_perf_mon_devices": str(num_of_perf_mon_devices),
            "num_of_perf_mon_monitors": str(num_of_perf_mon_monitors),
        }

        return return_dict

    @staticmethod
    def get_monitors_info_for_specific_ip(monitors, ip_to_verify):
        """
        Adds monitor-specific counters to the results for a specific IP. Because we have to return all monitors, we
        have to search for a specific IP in the results returned.

        :param monitors: a list of monitors
        :param ip_to_verify: the ip address to pick out of the list of monitors
        :return: list
        """
        return_monitors = []
        try:
            event_pulling_devices = monitors["json_results"]["monitoredDevices"]["eventPullingDevices"]["device"]
            for item in event_pulling_devices:
                if str(item["accessIp"]) == ip_to_verify:
                    return_monitors.append({"access_ip": str(item["accessIp"]),
                                            "monitors": item["monitors"]["monitor"]})
        except:
            pass

        try:
            perf_mon_devices = monitors["json_results"]["monitoredDevices"]["perfMonDevices"]["device"]
            for item in perf_mon_devices:
                if str(item["accessIp"]) == ip_to_verify:
                    return_monitors.append({"access_ip": str(item["accessIp"]),
                                            "monitors": item["monitors"]["monitor"]})
        except:
            pass

        return return_monitors

    @staticmethod
    def prepare_report_xml_query(xml_report):
        """
        Removes a specific element from a report XML input if needed.

        :param xml_report: string xml report to "strip" of the elements.
        :return: xml
        """
        try:
            doc = xml.dom.minidom.parseString(xml_report)
            t = doc.toxml()
            if '<DataRequest' in t:
                t1 = t.replace("<DataRequest", "<Reports><Report")
            else:
                t1 = t
            if '</DataRequest>' in t1:
                t2 = t1.replace("</DataRequest>", "</Report></Reports>")
            else:
                t2 = t1
        except BaseException as err:
            raise FSMBaseException(err)
        return t2

    @staticmethod
    def merge_xml_from_list_to_string(input_list):
        """
        Specific to fsm_report_query.
        Concats multiple pages of XML, into one contiguous XML file/string.
        Removes un-needed headers in each page, etc.

        :param input_list: List of XML pages to concat
        :return: xml
        """
        out_string = ""
        loop_count = 1
        list_len = len(input_list)
        for item in input_list:
            if loop_count == 1:
                out_string = out_string + item.replace('</events>\n', '').replace('</queryResult>\n', '')
                out_string = re.sub(u'(?imu)^\s*\n', u'', out_string)
            if loop_count > 1 and loop_count <= list_len:
                stripped_item = item.replace('</events>\n', '').replace('</queryResult>\n', '')
                stripped_item = stripped_item.replace('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n', '')
                stripped_item = re.sub("<queryResult.*\n", "", stripped_item)
                stripped_item = re.sub("<events>\n", "", stripped_item)
                out_string = out_string + stripped_item
            if loop_count == list_len:
                out_string = out_string + "\n    </events>\n</queryResult>"
            loop_count += 1
        return out_string

    @staticmethod
    def xml2dict(xml_in):
        """
        Converts an XML structure to JSON.

        :param xml_in: xml to convert
        :return: dict
        """
        xml_out = xmltodict.parse(str(xml_in), process_namespaces=True)
        json_out = json.dumps(xml_out)
        dict_out = json.loads(json_out)
        return dict_out

    @staticmethod
    def dict2xml(dict_in):
        """
        Converts a JSON dictionary to XML.

        :param dict_in: dict to convert
        :return: xml
        """
        xml_out = xmltodict.unparse(dict_in, pretty=True)
        return xml_out

    @staticmethod
    def report_result_to_csv(param):
        """
        Takes a list of dictionaries and turns it into a CSV. Used with reports.

        :param param: list
        :return: csv string
        """
        return_string = ""
        if len(param) == 0:
            return_string = "No records found. Exit"
            exit()
        else:
            keys = param[0].keys()
            return_string = return_string + ','.join(keys)
            return_string = return_string + "\n"
            for item in param:
                itemKeys = item.keys()
                value = []
                for key in keys:
                    if key not in itemKeys:
                        value.append('')
                    else:
                        value.append(item[key])
                return_string = return_string + ','.join(value)
                return_string = return_string + "\n"
        return return_string

    @staticmethod
    def validate_xml(input_xml):
        """
        Attempts to use the parseString method in xml.dom.minidom to help validate the XML.
        If the XML can't be parsed, it raises an error.

        :param input_xml: xml to be parsed
        """
        try:
            doc = xml.dom.minidom.parseString(input_xml)
        except BaseException as err:
            raise FSMBaseException(err)

    @staticmethod
    def dump_xml(xml_list):
        """
        Specific to fsm_report_query.
        Takes a list of XML strings (events) and converts them to one contiguous XML string

        :param xml_list: list of xml strings to concat
        :return: xml
        """
        param = []
        for item in xml_list:
            doc = xml.dom.minidom.parseString(item.encode('ascii', 'xmlcharrefreplace'))
            for node in doc.getElementsByTagName("events"):
<<<<<<< HEAD
                for node1 in node.getElementsByTagName("event"):
                    mapping = {}
                    for node2 in node1.getElementsByTagName("attributes"):
                        for node3 in node2.getElementsByTagName("attribute"):
                            itemName = node3.getAttribute("name")
                            for node4 in node3.childNodes:
                                if node4.nodeType == node.TEXT_NODE:
                                    message = node4.data
                                    if '\n' in message:
                                        message = message.replace('\n', '')
                                    mapping[itemName] = message
                    param.append(mapping)
=======
                    for node1 in node.getElementsByTagName("event"):
                        mapping = {}
                        for node2 in node1.getElementsByTagName("attributes"):
                            for node3 in node2.getElementsByTagName("attribute"):
                                itemName = node3.getAttribute("name")
                                for node4 in node3.childNodes:
                                    if node4.nodeType == node.TEXT_NODE:
                                        message = node4.data
                                        if '\n' in message:
                                            message = message.replace('\n', '')
                                        mapping[itemName] = message
                        param.append(mapping)
>>>>>>> Full FSM Commit. Ready for shippable tests.
        return param

    @staticmethod
    def get_current_datetime():
        """
        Returns current timestamp in specific format.

        :return: datetime
        """
        return_datetime = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        return return_datetime

    @staticmethod
    def convert_epoch_to_datetime(epoch):
        """
        Returns epoch timestamp to datetime format.

        :param epoch: epoch to convert
        :return: datetime
        """
        return_time = datetime.datetime.fromtimestamp(float(epoch)).strftime('%m/%d/%Y %H:%M:%S')
        return_time_utc = datetime.datetime.utcfromtimestamp(float(epoch)).strftime('%m/%d/%Y %H:%M:%S')
        return return_time, return_time_utc

    @staticmethod
    def convert_timestamp_to_epoch(timestamp):
        """
        Converts a timestamp to epoch.

        :param timestamp: datetime timestamp to convert
        :return: epoch
        """
        parsed_date = re.findall(r'\d{2}\/\d{2}\/\d{4}\s', timestamp)
        parsed_date2 = parsed_date[0].split("/")
        parsed_month = parsed_date2[0]
        parsed_day = parsed_date2[1]
        parsed_year = parsed_date2[2]

        parsed_time = re.findall(r'\s\d{6}', timestamp)
        if not parsed_time:
            parsed_time = re.findall(r'\s\d{2}:\d{2}:\d{2}', timestamp)
        if not parsed_time:
            parsed_time = re.findall(r'\s\d{4}', timestamp)
        if not parsed_time:
            parsed_time = re.findall(r'\s\d{2}:\d{2}', timestamp)
        parsed_time2 = re.findall(r'\d{2}', parsed_time[0])
        parsed_hour = parsed_time2[0]
        parsed_mins = parsed_time2[1]
        try:
            parsed_secs = parsed_time2[2]
        except:
            parsed_secs = "00"
            pass

        epoch = datetime.datetime(int(parsed_year), int(parsed_month), int(parsed_day),
                                  int(parsed_hour), int(parsed_mins), int(parsed_secs)).strftime('%s')
        return epoch

<<<<<<< HEAD
=======
>>>>>>> Full FSM Commit
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.

class SendSyslog(object):
    """
    A syslog client that logs to a remote server via multiple protocols.
    """

    def __init__(self,
                 host="localhost",
                 port=514,
<<<<<<< HEAD
<<<<<<< HEAD
                 facility=SyslogFacility.USER,
                 level=SyslogLevel.INFO,
                 protocol="",
                 ssl_context=None, ):
        self.host = host
        self.port = port
        self.facility = facility
        self.level = level
=======
                 facility=SyslogFacility.DAEMON,
=======
                 facility=SyslogFacility.USER,
                 level=SyslogLevel.INFO,
>>>>>>> Full FSM Commit. Ready for shippable tests.
                 protocol="",
                 ssl_context=None,):
        self.host = host
        self.port = port
        self.facility = facility
<<<<<<< HEAD
>>>>>>> Full FSM Commit
=======
        self.level = level
>>>>>>> Full FSM Commit. Ready for shippable tests.
        self.protocol = protocol
        self.ssl_context = ssl_context
        self.create_socket()

    def create_socket(self):
        """
<<<<<<< HEAD
<<<<<<< HEAD
        Creates the socket for the SendSyslog class upon init().

        :return: socket
=======

        :return:
>>>>>>> Full FSM Commit
=======
        Creates the socket for the SendSyslog class upon init().

        :return: socket
>>>>>>> Full FSM Commit. Ready for shippable tests.
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

<<<<<<< HEAD
<<<<<<< HEAD
    def send(self, header, message):
        """
        Actually sends the syslog. Returns an appropriate error message based on the network protocol picked.

        :param header: custom header, if any
        :param message: message.

        :return: dict
        """
        data = "<%d> %s" % (self.level + self.facility * 8,
                            str(header + " host:" + socket.gethostname() + " | " + message))

=======

    def create_full_message(self, header, message, level):
=======
    def send(self, header, message):
>>>>>>> Full FSM Commit. Ready for shippable tests.
        """
        Actually sends the syslog. Returns an appropriate error message based on the network protocol picked.

        :param header: custom header, if any
        :param message: message.

        :return: dict
        """
        data = "<%d> %s" % (self.level + self.facility * 8,
                           str(header + " host:" + socket.gethostname() + " | " + message))

<<<<<<< HEAD
        :param header:
        :param message:
        :param level:
        :return:
        """
        data = self.create_full_message(header, message, level)
>>>>>>> Full FSM Commit
=======
>>>>>>> Full FSM Commit. Ready for shippable tests.
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

<<<<<<< HEAD
<<<<<<< HEAD

=======
>>>>>>> Full FSM Commit
=======

>>>>>>> Full FSM Commit. Ready for shippable tests.
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
