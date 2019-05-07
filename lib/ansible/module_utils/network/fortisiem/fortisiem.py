# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2019 Fortinet, Inc
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
#

from ansible.module_utils.network.fortisiem.common import FSM_RC
from ansible.module_utils.network.fortisiem.common import FSMEndpoints
from ansible.module_utils.network.fortisiem.common import FSMBaseException
from ansible.module_utils.network.fortisiem.common import FSMCommon
<<<<<<< HEAD
from ansible.module_utils.network.fortisiem.common import SyslogLevel
from ansible.module_utils.network.fortisiem.common import SendSyslog
from ansible.module_utils.network.fortisiem.common import scrub_dict
from ansible.module_utils.network.fortisiem.fsm_xml_generators import FSMXMLGenerators
=======
from ansible.module_utils.network.fortisiem.common import SyslogFacility
from ansible.module_utils.network.fortisiem.common import SyslogLevel
from ansible.module_utils.network.fortisiem.common import SendSyslog
from ansible.module_utils.network.fortisiem.common import scrub_dict
>>>>>>> Full FSM Commit

import base64
import urllib2
import ssl
import json
import xml.dom.minidom
import re
<<<<<<< HEAD


# BEGIN HANDLER CLASSES


class FortiSIEMHandler(object):
    """
    This class handles every aspect of FortiSIEM modules that could be considered re-usable or repeated code.
    It also makes extensive use of self.<attribute> methodology to keep track of variables and trade them
    between the various methods that perform the work.
    """

    def __init__(self, module):
        self._module = module
        self._tools = FSMCommon
        self._xml = FSMXMLGenerators(module)
=======
import datetime
from xml.dom.minidom import parseString
from xml.etree import ElementTree as ET
from xml.dom import minidom

import pydevd


# check for xmltodict
try:
    import xmltodict
    HAS_XML2DICT = True
except ImportError as err:
    HAS_XML2DICT = False
    raise FSMBaseException("You don't really want to use XML for responses, do you? We use with JSON in these parts. "
                           "XML2DICT Package is not installed. Please use 'pip install xmltodict. ")


# BEGIN HANDLER CLASSES
class FortiSIEMHandler(object):
    def __init__(self, module):
        self._module = module
        self._tools = FSMCommon
>>>>>>> Full FSM Commit
        self.ssl_context = self.create_ssl_context()
        self.last_http_return_code = None
        self.last_http_return_headers = None
        self.last_http_return_url = None
        self.next_http_auth = None
        try:
            self.export_json_to_screen = module.paramgram["export_json_to_screen"]
            self.export_json_to_file_path = module.paramgram["export_json_to_file_path"]
            self.export_xml_to_file_path = module.paramgram["export_xml_to_file_path"]
            self.export_csv_to_file_path = module.paramgram["export_csv_to_file_path"]
<<<<<<< HEAD
        except BaseException:
=======
        except:
>>>>>>> Full FSM Commit
            self.export_json_to_screen = None
            self.export_json_to_file_path = None
            self.export_xml_to_file_path = None
            self.export_csv_to_file_path = None
        self.report_xml_source = None
        self.report_query_id = None
        self.report_length = None

    def get_organizations(self):
        """
<<<<<<< HEAD
        Gets a list of organizations from a target FortiSIEM Supervisor.

        :return: dict
=======

        :return:
>>>>>>> Full FSM Commit
        """
        url = "https://" + self._module.paramgram["host"] + FSMEndpoints.GET_ORGS
        auth = self.create_auth_header()
        output_xml = self.submit_simple_request(auth, url)
<<<<<<< HEAD
        output_json = self._tools.xml2dict(output_xml)
        formatted_output_dict = self.format_results(output_json, output_xml)
        return formatted_output_dict

    def create_ssl_context(self):
        """
        Creates the SSL context for handling certificates.

        :return: ssl context object
=======
        output_json = self.xml2dict(output_xml)
        formatted_output_dict = self.format_results(output_json, output_xml)
        return formatted_output_dict

    def create_org_payload(self):
        """

        :return:
        """
        organizations = ET.Element("organizations")
        organization = ET.Element("organization")
        organizations.append(organization)
        name = ET.SubElement(organization, "name")
        name.text = self._module.paramgram["org_name"]
        fullName = ET.SubElement(organization, "fullName")
        fullName.text = self._module.paramgram["org_display_name"]
        description = ET.SubElement(organization, "description")
        description.text = self._module.paramgram["org_description"]
        if self._module.paramgram["uri"] == FSMEndpoints.ADD_ORGS:
            adminUser = ET.SubElement(organization, "adminUser")
            adminUser.text = self._module.paramgram["org_admin_username"]
            adminPwd = ET.SubElement(organization, "adminPwd")
            adminPwd.text = self._module.paramgram["org_admin_password"]
            adminEmail = ET.SubElement(organization, "adminEmail")
            adminEmail.text = self._module.paramgram["org_admin_email"]
        includeRange = ET.SubElement(organization, "includeRange")
        includeRange.text = self._module.paramgram["org_include_ip_range"]
        excludeRange = ET.SubElement(organization, "excludeRange")
        excludeRange.text = self._module.paramgram["org_exclude_ip_range"]
        if self._module.paramgram["uri"] == FSMEndpoints.ADD_ORGS:
            custResource = ET.Element("custResource")
            organization.append(custResource)
            eps = ET.SubElement(custResource, "eps")
            eps.text = self._module.paramgram["org_eps"]

        # CONCAT COLLECTORS BEFORE APPENDING IF SPECIFIED
        if self._module.paramgram["org_collectors"]:
            # EXPECTS A LIST
            collector_data = self._module.paramgram["org_collectors"]
            if isinstance(collector_data, list):
                #collector_xml = "<collectors>"
                collectors = ET.Element("collectors")
                organization.append(collectors)
                for col in collector_data:
                    collector = ET.SubElement(collectors, "collector")
                    col_eps = ET.SubElement(collector, "eps")
                    col_eps.text = col["eps"]
                    col_name = ET.SubElement(collector, "name")
                    col_name.text = col["name"]

        # OR IF A SINGLE COLLECTOR VIA PARAMETERS IS DEFINED
        elif self._module.paramgram["org_collector_name"] and self._module.paramgram["org_collector_eps"]:
            collectors = ET.Element("collectors")
            organization.append(collectors)
            collector = ET.SubElement(collectors, "collector")
            col_eps = ET.SubElement(collector, "eps")
            col_eps.text = self._module.paramgram["org_collector_eps"]
            col_name = ET.SubElement(collector, "name")
            col_name.text = self._module.paramgram["org_collector_name"]

        xmlstr = ET.tostring(organizations, 'utf-8')
        return xmlstr

    def create_credential_payload(self):
        """

        :return:
        """
        accessConfigs = ET.Element("accessConfigs")
        accessMethods = ET.Element("accessMethods")
        accessConfigs.append(accessMethods)
        accessMethod = ET.Element("accessMethod")
        accessMethods.append(accessMethod)
        name = ET.SubElement(accessMethod, "name")
        name.text = self._module.paramgram["friendly_name"]
        accessProtocol = ET.SubElement(accessMethod, "accessProtocol")
        accessProtocol.text = str(self._module.paramgram["access_protocol"]).upper()
        description = ET.SubElement(accessMethod, "description")
        description.text = self._module.paramgram["description"]
        port = ET.SubElement(accessMethod, "port")
        port.text = self._module.paramgram["port"]
        pwdType = ET.SubElement(accessMethod, "pwdType")
        pwdType.text = self._module.paramgram["password_type"]
        baseDN = ET.SubElement(accessMethod, "baseDN")

        pullInterval = ET.SubElement(accessMethod, "pullInterval")
        pullInterval.text = self._module.paramgram["pull_interval"]

        # ADD CREDENTIAL
        credential = ET.Element("credential")
        accessMethod.append(credential)
        password = ET.SubElement(credential, "password")
        password.text = self._module.paramgram["cred_password"]
        principal = ET.SubElement(credential, "principal")
        principal.text = self._module.paramgram["cred_username"]
        suPassword = ET.SubElement(credential, "suPassword")
        if self._module.paramgram["super_password"]:
            suPassword.text = self._module.paramgram["super_password"]

        # ADD DEV TYPE
        deviceType = ET.Element("deviceType")
        accessMethod.append(deviceType)
        accessProtocols = ET.SubElement(deviceType, "accessProtocols")
        accessProtocols.text = self._module.paramgram["access_protocol"]
        model = ET.SubElement(deviceType, "model")
        model.text = "Generic"
        vendor = ET.SubElement(deviceType, "vendor")
        vendor.text = "Generic"
        version = ET.SubElement(deviceType, "version")
        version.text = "ANY"

        # ADD IP ACCESS MAPPINGS
        if self._module.paramgram["ip_range"]:
            ipAccessMappings = ET.Element("ipAccessMappings")
            accessConfigs.append(ipAccessMappings)
            ipAccessMapping = ET.Element("ipAccessMapping")
            ipAccessMappings.append(ipAccessMapping)
            if self._module.paramgram["access_id"]:
                ipAccessMethodId = ET.SubElement(ipAccessMapping, "accessMethodId")
                ipAccessMethodId.text = self._module.paramgram["access_id"]
            ipRange = ET.SubElement(ipAccessMapping, "ipRange")
            ipRange.text = self._module.paramgram["ip_range"]
        else:
            ipAccessMappings = ET.Element("ipAccessMappings")
            accessConfigs.append(ipAccessMappings)

        xmlstr = ET.tostring(accessConfigs, 'utf-8')
        return xmlstr

    def create_discover_payload(self):
        #pydevd.settrace('10.0.0.151', port=54654, stdoutToServer=True, stderrToServer=True)
        discoverRequest = ET.Element("discoverRequest")
        type = ET.SubElement(discoverRequest, "type")
        type.text = self._module.paramgram["type"]
        if self._module.paramgram["root_ip"] and self._module.paramgram["type"] == "SmartScan":
            rootIP = ET.SubElement(discoverRequest, "rootIP")
            rootIP.text = self._module.paramgram["root_ip"]
        includeRange = ET.SubElement(discoverRequest, "includeRange")
        includeRange.text = self._module.paramgram["include_range"]
        excludeRange = ET.SubElement(discoverRequest, "excludeRange")
        excludeRange.text = self._module.paramgram["exclude_range"]
        # PROCESS OPTIONS
        noPing = ET.SubElement(discoverRequest, "noPing")
        noPing.text = str(self._module.paramgram["no_ping"]).lower()
        onlyPing = ET.SubElement(discoverRequest, "onlyPing")
        onlyPing.text = str(self._module.paramgram["only_ping"]).lower()

        delta = ET.SubElement(discoverRequest, "delta")
        delta.text = str(self._module.paramgram["delta"]).lower()

        vmOff = ET.SubElement(discoverRequest, "vmOff")
        vmOff.text = str(self._module.paramgram["vm_off"]).lower()

        vmTemplate = ET.SubElement(discoverRequest, "vmTemplate")
        vmTemplate.text = str(self._module.paramgram["vm_templates"]).lower()

        discoverRoute = ET.SubElement(discoverRequest, "discoverRoute")
        discoverRoute.text = str(self._module.paramgram["discover_routes"]).lower()

        winexeBased = ET.SubElement(discoverRequest, "winexeBased")
        winexeBased.text = str(self._module.paramgram["winexe_based"]).lower()

        unmanaged = ET.SubElement(discoverRequest, "unmanaged")
        unmanaged.text = str(self._module.paramgram["unmanaged"]).lower()

        monitorWinEvents = ET.SubElement(discoverRequest, "monitorWinEvents")
        monitorWinEvents.text = str(self._module.paramgram["monitor_win_events"]).lower()

        monitorWinPatch = ET.SubElement(discoverRequest, "monitorWinPatch")
        monitorWinPatch.text = str(self._module.paramgram["monitor_win_patches"]).lower()

        monitorInstSw = ET.SubElement(discoverRequest, "monitorInstSw")
        monitorInstSw.text = str(self._module.paramgram["monitor_installed_sw"]).lower()

        nameResolutionDnsFirst = ET.SubElement(discoverRequest, "nameResolutionDnsFirst")
        nameResolutionDnsFirst.text = str(self._module.paramgram["name_resolution_dns_first"]).lower()

        #pydevd.settrace('10.0.0.151', port=54654, stdoutToServer=True, stderrToServer=True)
        xmlstr = ET.tostring(discoverRequest, 'utf-8')
        return xmlstr

    def create_maint_payload(self):
        """

        :return:
        """
        MaintSchedules = ET.Element("MaintSchedules")
        MaintSchedule = ET.Element("MaintSchedule")
        MaintSchedules.append(MaintSchedule)
        name = ET.SubElement(MaintSchedule, "name")
        name.text = self._module.paramgram["name"]
        description = ET.SubElement(MaintSchedule, "description")
        description.text = self._module.paramgram["description"]
        fireIncidents = ET.SubElement(MaintSchedule, "fireIncidents")
        fireIncidents.text = str(self._module.paramgram["fire_incidents"]).lower()
        timeZoneId = ET.SubElement(MaintSchedule, "timeZoneId")
        timeZoneId.text = self._module.paramgram["time_zone_id"]

        # ADD DEVICES, LOOP IF NEEDED
        devices = ET.SubElement(MaintSchedule, "devices")
        device = ET.SubElement(devices, "device")
        device.text = self._module.paramgram["devices"]

        # ADD GROUPS, LOOP IF NEEDED
        if self._module.paramgram["groups"]:
            groups = ET.SubElement(MaintSchedule, "groups")
            group = ET.SubElement(groups, "group")
            group.text = self._module.paramgram["groups"]
        else:
            groups = ET.SubElement(MaintSchedule, "groups")

        # ADD SCHEDULE
        schedule = ET.Element("schedule")
        MaintSchedule.append(schedule)
        startHour = ET.SubElement(schedule, "startHour")
        startHour.text = self._module.paramgram["start_hour"]
        startMin = ET.SubElement(schedule, "startMin")
        startMin.text = self._module.paramgram["start_min"]
        duration = ET.SubElement(schedule, "duration")
        duration.text = self._module.paramgram["duration"]
        timeZone = ET.SubElement(schedule, "timeZone")
        timeZone.text = self._module.paramgram["time_zone"]
        startDate = ET.SubElement(schedule, "startDate")
        startDate.text = self._module.paramgram["start_date"]
        endDate = ET.SubElement(schedule, "endDate")
        endDate.text = self._module.paramgram["end_date"]
        endDateOpen = ET.SubElement(schedule, "endDateOpen")
        endDateOpen.text = "false"
        if self._module.paramgram["end_date_open"]:
            endDateOpen.text = "true"

        xmlstr = ET.tostring(MaintSchedules, 'utf-8')
        return xmlstr

    def create_ssl_context(self):
        """

        :return:
>>>>>>> Full FSM Commit
        """
        ignore_ssl_setting = None
        ctx = None
        try:
            ignore_ssl_setting = self._module.paramgram["ignore_ssl_errors"]
        except BaseException as err:
<<<<<<< HEAD
            FSMBaseException(msg="create_ssl_context() failed to ignore ssl setting" + str(err))
=======
            FSMBaseException(err)
>>>>>>> Full FSM Commit

        if ignore_ssl_setting == "enable":
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        else:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_REQUIRED
        return ctx

    def create_auth_header(self):
        """
<<<<<<< HEAD
        Creates authentication header for FortiSIEM API calls based on username and password.

        :return: Base64 Encoded string
        """
        encode_password = base64.b64encode(self._module.paramgram["username"] + ":" +
                                           self._module.paramgram["password"])
        auth = "Basic %s" % encode_password
=======

        :return:
        """
        encodePassword = base64.b64encode(self._module.paramgram["username"] + ":" +
                                          self._module.paramgram["password"])
        auth = "Basic %s" % encodePassword
>>>>>>> Full FSM Commit
        return auth

    def create_endpoint_url(self):
        """
<<<<<<< HEAD
        Joins the host and URI into a full URL for the FortiSIEMHandler class to use.

        :return: string
=======

        :return:
>>>>>>> Full FSM Commit
        """
        url = "https://" + self._module.paramgram["host"] + self._module.paramgram["uri"]
        return url

    def submit_simple_request(self, auth, url):
        """
<<<<<<< HEAD
        Submits a simple GET request without an XML payload.

        :param auth: Authentication header created in create_auth_header()
        :param url: URL created in create_endpoint_url()

        :return: xml
=======

        :param auth:
        :param url:
        :return:
>>>>>>> Full FSM Commit
        """
        req = urllib2.Request(url, None, {"Authorization": auth})
        out_xml = None
        try:
            handle = urllib2.urlopen(req, context=self.ssl_context)
            out_xml = handle.read()
            try:
                self.last_http_return_code = handle.getcode()
                self.last_http_return_headers = handle.info()
                self.last_http_return_url = url
            except BaseException as err:
<<<<<<< HEAD
                raise FSMBaseException(msg="submit_simple_request() failed to get http codes. Error: " + str(err))
        except BaseException as err:
            raise FSMBaseException(msg="submit_simple_request() failed" + str(err))
=======
                raise FSMBaseException(err)
        except BaseException as err:
            raise FSMBaseException(err)
>>>>>>> Full FSM Commit
        return out_xml

    def submit_simple_payload_request(self, auth, url, payload):
        """
<<<<<<< HEAD
        Submits a simple GET request with an XML payload.

        :param auth: Authentication header created in create_auth_header()
        :param url: URL created in create_endpoint_url()
        :param payload: XML payload in string form

        :return: xml
=======

        :param auth:
        :param url:
        :param payload:
        :return:
>>>>>>> Full FSM Commit
        """
        req = urllib2.Request(url, payload, {"Authorization": auth,
                                             "Content-Type": "text/xml",
                                             "Content-Length": len(payload),
                                             })

        req.get_method = lambda: 'PUT'
        out_xml = None
        try:
            opener = urllib2.build_opener(urllib2.HTTPSHandler(debuglevel=False, context=self.ssl_context))
            urllib2.install_opener(opener)
            handle = urllib2.urlopen(req)
            out_xml = handle.read()
            try:
                self.last_http_return_code = handle.getcode()
                self.last_http_return_headers = handle.info()
                self.last_http_return_url = url
            except BaseException as err:
<<<<<<< HEAD
                raise FSMBaseException(msg="submit_simple_payload_request() couldn't "
                                           "get the HTTP codes. Error: " + str(err))
        except urllib2.HTTPError as err:
            error_msg = err.read()
            if "HTTP Status 500" in error_msg:
                raise FSMBaseException(msg="submit_simple_payload_request(): "
                                           "500 Internal Server Error. In our experience, "
                                           "this means the object exists or doesn't. "
                                           "If that doesn't work, double check your inputs. "
                                           "Perhaps it already exists? "
                                           "You should change the mode, most likely. "
                                           "HTTP Error: " + str(error_msg))
            raise FSMBaseException(msg="submit_simple_payload_request() HTTP Error: " + str(error_msg))
=======
                raise FSMBaseException(err)
        except urllib2.HTTPError as err:
            error_msg = err.read()
            if "HTTP Status 500" in error_msg:
                msg = "500 Internal Server Error. In our experience, this means the object exists or doesn't. " \
                      "If that doesn't work, double check your inputs. Perhaps it already exists? " \
                      "You should change the mode, most likely. Error: " + str(err)
                raise FSMBaseException(msg)
            raise FSMBaseException(err)
>>>>>>> Full FSM Commit
        return out_xml

    def handle_simple_request(self):
        """
<<<<<<< HEAD
        Handles the "simple" get request without an XML payload, from end-to-end, including result formatting.

        :return: dict
        """
        formatted_output_dict = None
=======

        :return:
        """
>>>>>>> Full FSM Commit
        auth = self.create_auth_header()
        url = self.create_endpoint_url()
        output_xml = self.submit_simple_request(auth, url)
        try:
            if "<password>" in output_xml:
                output_xml = re.sub(r'(<password>.*?<\/password>)', '', output_xml)
                output_xml = re.sub(r'(<suPassword>.*?<\/suPassword>)', '', output_xml)
<<<<<<< HEAD
        except BaseException as err:
            pass
        if output_xml:
            try:
                output_json = self._tools.xml2dict(output_xml)
=======
        except:
            pass
        if output_xml:
            try:
                output_json = self.xml2dict(output_xml)
>>>>>>> Full FSM Commit
                formatted_output_dict = self.format_results(output_json, output_xml)
            except BaseException as err:
                try:
                    output_json = {"fsm_response": str(output_xml)}
                    output_xml = "<fsm_response>" + str(output_xml + "</fsm_response>")
                    formatted_output_dict = self.format_results(output_json, output_xml)
                except BaseException as err:
<<<<<<< HEAD
                    raise FSMBaseException(msg="handle_simple_request() couldn't deal with the response. "
                                               "Error:" + str(err))
=======
                    raise FSMBaseException(err)
>>>>>>> Full FSM Commit

        elif not output_xml:
            output_json = {"status": "OK"}
            output_xml = "<status>OK</status>"
            formatted_output_dict = self.format_results(output_json, output_xml)
        return formatted_output_dict

    def handle_simple_payload_request(self, payload):
        """
<<<<<<< HEAD
        Handles the  get request with an XML payload, from end-to-end, including result formatting.

        :return: dict
        """
        formatted_output_dict = None
        auth = self.create_auth_header()
        url = self.create_endpoint_url()
=======

        :param payload:
        :return:
        """
        auth = self.create_auth_header()
        url = self.create_endpoint_url()
        #pydevd.settrace('10.0.0.151', port=54654, stdoutToServer=True, stderrToServer=True)
>>>>>>> Full FSM Commit
        output_xml = self.submit_simple_payload_request(auth, url, payload)
        try:
            if "<password>" in output_xml:
                output_xml = re.sub(r'(<password>.*?<\/password>)', '', output_xml)
                output_xml = re.sub(r'(<suPassword>.*?<\/suPassword>)', '', output_xml)
<<<<<<< HEAD
        except BaseException as err:
            pass
        if output_xml:
            try:
                output_json = self._tools.xml2dict(output_xml)
=======
        except:
            pass
        if output_xml:
            try:
                output_json = self.xml2dict(output_xml)
>>>>>>> Full FSM Commit
                formatted_output_dict = self.format_results(output_json, output_xml)
                formatted_output_dict["payload"] = payload
            except BaseException as err:
                try:
                    output_json = {"fsm_response": str(output_xml)}
                    output_xml = "<fsm_response>" + str(output_xml + "</fsm_response>")
                    formatted_output_dict = self.format_results(output_json, output_xml)
                    formatted_output_dict["payload"] = payload
                except BaseException as err:
<<<<<<< HEAD
                    raise FSMBaseException(msg="handle_simple_payload_request() couldn't deal with the response. "
                                               "Error:" + str(err))
=======
                    raise FSMBaseException(err)
>>>>>>> Full FSM Commit

        elif not output_xml:
            output_json = {"status": "OK"}
            output_xml = "<status>OK</status>"
            formatted_output_dict = self.format_results(output_json, output_xml)

        return formatted_output_dict

    def handle_syslog_request(self):
<<<<<<< HEAD
        """
        Handles a syslog request from end-to-end, and reports on the results.

        :return: dict
        """
=======
>>>>>>> Full FSM Commit
        output_dict = {"status": "FAILED", "message": "None"}
        try:
            log = SendSyslog(host=self._module.paramgram["syslog_host"],
                             port=self._module.paramgram["network_port"],
                             protocol=self._module.paramgram["network_protocol"],
<<<<<<< HEAD
                             level=self._module.paramgram["syslog_level"],
                             facility=self._module.paramgram["syslog_facility"],
                             ssl_context=self.create_ssl_context(),
                             )
            output_dict = log.send(header=self._module.paramgram["syslog_header"],
                                   message=self._module.paramgram["syslog_message"])
        except BaseException as err:
            raise FSMBaseException(msg="handle_syslog_request() couldn't send the syslog. Error: " + str(err))
=======
                             ssl_context=self.create_ssl_context(),
                             )
            output_dict = log.send(header=self._module.paramgram["syslog_header"],
                          message=self._module.paramgram["syslog_message"],
                          level=SyslogLevel.NOTICE)
        except BaseException(err):
            raise FSMBaseException(err)
>>>>>>> Full FSM Commit
        return output_dict

    def format_results(self, json_results, xml_results):
        """
<<<<<<< HEAD
        Takes the JSON and XML results from multiple "handlers" and formats them into a structured return dictionary.

        :param json_results: The results from an API call, in JSON form
        :param xml_results: The results from an API call, in XML form

        :return:dict
        """

=======
        Formats the payload from the module, into a payload exit_json() can work with, and that we can rely on.

        :param method: The preferred API Request method (GET, ADD, POST, etc....)
        :type method: basestring
        :param results: JSON Package of the results
        :type results: dict

        :return: Properly formatted dictionary payload exit_json() can work with, and that we can rely on.
        :rtype: dict
        """
>>>>>>> Full FSM Commit
        formatted_results = dict()
        formatted_results["rc"] = self.last_http_return_code
        formatted_results["http_metadata"] = {
            "status": {
                "code": self.last_http_return_code,
                "message": FSM_RC["fsm_return_codes"][formatted_results["rc"]]["msg"]
            },
            "url": self.last_http_return_url,

        }
        # IF HEADERS ARE PRESENT, TRY TO ADD THEM
        try:
            formatted_results["http_metadata"]["headers"] = self.last_http_return_headers
        except BaseException as err:
            pass

        # ADD THE RESULTS
        try:
            if json_results:
                formatted_results["json_results"] = json_results
            else:
                formatted_results["json_results"] = None
        except BaseException as err:
            pass
        # ADD THE XML RESULTS
        try:
            if xml_results:
                formatted_results["xml_results"] = xml_results
            else:
                formatted_results["xml_results"] = None
        except BaseException as err:
            pass
        return formatted_results

    def format_verify_judge_device_results(self, ip_to_verify, cmdb, events, monitors):
        """
<<<<<<< HEAD
        Does the same as format_results(), however, it is specific to the fsm_verify_device module.
        These calls require careful formatting.

        :param ip_to_verify: an ip address that was verified
        :param cmdb: cmdb results from verification
        :param events: event results from verification
        :param monitors: monitor results from verifiction

        :return: dict
        """

        return_dict = dict()
=======

        :param ip_to_verify:
        :param cmdb:
        :param events:
        :param monitors:
        :return:
        """
        #pydevd.settrace('10.0.0.151', port=54654, stdoutToServer=True, stderrToServer=True)

        return_dict = {}
>>>>>>> Full FSM Commit
        return_dict["device"] = {}
        return_dict["json_results"] = {}
        missing = []
        present = []
        if not cmdb:
            missing.append("cmdb")
        else:
            present.append("cmdb")
            try:
                return_dict["device"]["cmdb_results"] = cmdb["json_results"]["device"]
<<<<<<< HEAD
            except BaseException as err:
=======
            except:
>>>>>>> Full FSM Commit
                return_dict["device"]["cmdb_results"] = None
        if not events:
            missing.append("events")
        else:
            present.append("events")
<<<<<<< HEAD
            return_dict["device"]["event_results"] = \
                self._tools.get_events_info_for_specific_ip(events)
=======
            return_dict["device"]["event_results"] =\
                self.get_events_info_for_specific_ip(events)
>>>>>>> Full FSM Commit
        if not monitors:
            missing.append("monitors")
        else:
            present.append("monitors")
            return_dict["device"]["monitor_results"] = \
<<<<<<< HEAD
                self._tools.get_monitors_info_for_specific_ip(monitors, ip_to_verify)
=======
                self.get_monitors_info_for_specific_ip(monitors, ip_to_verify)
>>>>>>> Full FSM Commit

        return_dict["rc"] = self.last_http_return_code
        return_dict["http_metadata"] = {
            "status": {
                "code": self.last_http_return_code,
                "message": FSM_RC["fsm_return_codes"][return_dict["rc"]]["msg"]
            },
            "url": self.last_http_return_url,

        }

        try:
            return_dict["json_results"]["Name"] = return_dict["device"]["cmdb_results"]["name"]
<<<<<<< HEAD
        except BaseException as err:
            return_dict["json_results"]["Name"] = "Not Found"
        try:
            return_dict["json_results"]["Access IP"] = return_dict["device"]["cmdb_results"]["accessIp"]
        except BaseException as err:
            return_dict["json_results"]["Access IP"] = self._module.paramgram["ip_to_verify"]
        try:
            return_dict["json_results"]["Discover Methods"] = return_dict["device"]["cmdb_results"]["discoverMethod"]
        except BaseException as err:
            return_dict["json_results"]["Discover Methods"] = "Not Found"
        try:
            return_dict["json_results"]["Distinct Event Types"] = len(return_dict["device"]["event_results"])
        except BaseException as err:
            return_dict["json_results"]["Distinct Event Types"] = None
        try:
            return_dict["json_results"]["Num of Events"] = self._tools.get_event_count_for_specific_ip(events)
        except BaseException as err:
            return_dict["json_results"]["Num of Events"] = None
        try:
            return_dict["json_results"]["missing_items"] = missing
        except BaseException as err:
            pass
        try:
            return_dict["json_results"]["present_items"] = present
        except BaseException as err:
            pass
        # SCORE IT
        scored_dict = self._tools.score_device_verification(return_dict)

        return scored_dict

    def json_results_to_file_path(self, json_results):
        """
        Writes results to a JSON file. Formats the JSON.

        :param json_results: json to write to file
=======
        except:
            return_dict["json_results"]["Name"] = "Not Found"
        try:
            return_dict["json_results"]["Access IP"] = return_dict["device"]["cmdb_results"]["accessIp"]
        except:
            return_dict["json_results"]["Access IP"] = self._module.paramgram["ip_to_verify"]
        try:
            return_dict["json_results"]["Discover Methods"] = return_dict["device"]["cmdb_results"]["discoverMethod"]
        except:
            return_dict["json_results"]["Discover Methods"] = "Not Found"
        try:
            return_dict["json_results"]["Distinct Event Types"] = len(return_dict["device"]["event_results"])
        except:
            return_dict["json_results"]["Distinct Event Types"] = None
        try:
            return_dict["json_results"]["Num of Events"] = self.get_event_count_for_specific_ip(events)
        except:
            return_dict["json_results"]["Num of Events"] = None
        try:
            return_dict["json_results"]["missing_items"] = missing
        except:
            pass
        try:
            return_dict["json_results"]["present_items"] = present
        except:
            pass
        # SCORE IT
        scored_dict = self.score_device_verification(return_dict)

        return scored_dict

    @staticmethod
    def score_device_verification(return_dict):
        """

        :param return_dict:
        :return:
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
        except BaseException as err:
            pass
        try:
            score += (points_per_event_types * (return_dict["json_results"]["Distinct Event Types"]))
        except BaseException as err:
            pass
        try:
            discover_methods = str(return_dict["json_results"]["Discover Methods"])
            score += (points_per_discover_methods * len((discover_methods.split(","))))
        except BaseException as err:
            pass
        try:
            score += (points_per_missing_item * (len(return_dict["json_results"]["missing_items"])))
        except BaseException as err:
            pass
        try:
            score += (points_per_present_item * (len(return_dict["json_results"]["present_items"])))
        except BaseException as err:
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

        :param results:
        :param file_path:
        :return:
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

        :param events:
        :return:
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

        :param events:
        :return:
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

        :param monitors:
        :param ip_to_verify:
        :return:
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

    def json_results_to_file_path(self, json_results):
        """

        :param json_results:
        :return:
>>>>>>> Full FSM Commit
        """
        try:
            f = open(self.export_json_to_file_path, "w")
            f.write(json.dumps(json_results, indent=4, sort_keys=True))
            f.close()
        except BaseException as err:
<<<<<<< HEAD
            raise FSMBaseException(msg="JSON Failed to write to file: " + str(self.export_json_to_file_path) +
                                       "| Error: " + str(err))

    def xml_results_to_file_path(self, xml_results):
        """
        Writes results to a XML file. Pretty-Prints the XML.

        :param xml_results: xml to write to file
=======
            raise FSMBaseException(err)

    def xml_results_to_file_path(self, xml_results):
        """

        :param xml_results:
        :return:
>>>>>>> Full FSM Commit
        """
        try:
            xml_out = xml.dom.minidom.parseString(xml_results)
            xml_pretty = xml_out.toprettyxml()
            f = open(self.export_xml_to_file_path, "w")
            f.write(xml_pretty)
            f.close()
        except BaseException as err:
<<<<<<< HEAD
            raise FSMBaseException(msg="XML Failed to write to file: " + str(self.export_xml_to_file_path) +
                                       "| Error: " + str(err))

    def csv_results_to_file_path(self, csv_results):
        """
        Writes results to a CSV file

        :param csv_results: csv to write to file
=======
            raise FSMBaseException(err)

    def csv_results_to_file_path(self, csv_results):
        """

        :param csv_results:
        :return:
>>>>>>> Full FSM Commit
        """
        try:
            f = open(self.export_csv_to_file_path, "w")
            f.write(csv_results)
            f.close()
        except BaseException as err:
<<<<<<< HEAD
            raise FSMBaseException(msg="CSV Failed to write to file: " + str(self.export_csv_to_file_path) +
                                       "| Error: " + str(err))

    def get_file_contents(self, file_path):
        """
        Gets the contents of a file. Commonly used with modules that allow custom XML files.

        :param file_path: path of file to collect contents

        :return: string of file contents
        """

        source = None
        try:
            f = open(file_path, "r")
            source = f.read()
            f.close()
            self.report_xml_source = source
        except BaseException as err:
            FSMBaseException(msg="Failed to get file contents at path: " + str(self.export_json_to_file_path) +
                                 "| Error: " + str(err))

        return source

    def handle_report_submission(self):
        """
        End-to-End handler for submitting a report. Sends report, waits for finish, and gets results.

        :return: xml
=======
            raise FSMBaseException(err)

    def get_report_source_from_file_path(self, report_file_path):
        """

        :param report_file_path:
        :return:
        """
        try:
            f = open(report_file_path, "r")
            report_source = f.read()
            f.close()
            self.report_xml_source = report_source
        except BaseException as err:
            FSMBaseException(err)

        return report_source

    def handle_report_submission(self):
        """

        :return:
>>>>>>> Full FSM Commit
        """
        self.post_report_get_query_id()
        self.wait_for_query_finish()
        report_out = self.retrieve_finished_query()
        return report_out

    def post_report_get_query_id(self):
        """
<<<<<<< HEAD
        Submits report XML for query, and returns the query ID.

        No return. Writes query_id to self.
        """
        self.next_http_auth = self.create_auth_header()
        url = self.create_endpoint_url()
        report_xml = self._tools.prepare_report_xml_query(self._module.paramgram["input_xml"])
=======

        :return:
        """
        self.next_http_auth = self.create_auth_header()
        url = self.create_endpoint_url()
        report_xml = self.prepare_report_xml_query(self._module.paramgram["input_xml"])
>>>>>>> Full FSM Commit
        query_id = self.submit_report_request(self.next_http_auth, url, report_xml)
        self.report_query_id = query_id

        if 'error code="255"' in query_id:
            raise FSMBaseException(msg="Query Error, debug XML file being sent, it caused an error.")

    def wait_for_query_finish(self):
        """
<<<<<<< HEAD
        Waits for a specified query ID to reach 100% completion, then exits the time loop.
=======

        :return:
>>>>>>> Full FSM Commit
        """
        query_id = self.report_query_id
        self._module.paramgram["uri"] = FSMEndpoints.GET_REPORT_PROGRESS + str(query_id)
        url = self.create_endpoint_url()
        query_progress = 0
        while query_progress != 100:
            returned_progress = self.get_query_progress(self.next_http_auth, url)
            query_progress = int(returned_progress)

    def retrieve_finished_query(self):
        """
<<<<<<< HEAD
        Gets results from a finished report. Formats results for return.

        :return: dict
=======

        :return:
>>>>>>> Full FSM Commit
        """
        query_id = self.report_query_id
        self._module.paramgram["uri"] = FSMEndpoints.GET_REPORT_RESULTS + str(query_id) + "/0/1000"
        url = self.create_endpoint_url()
        out_xml = []
        first_results = self.get_query_results(self.next_http_auth, url)
        out_xml.append(first_results.decode("utf-8"))
        try:
            p = re.compile('totalCount="\d+"')
            mlist = p.findall(out_xml[0])
            mm = mlist[0].replace('"', '')
            row_count = mm.split("=")[-1]
            row_count = int(row_count)
        except BaseException as err:
<<<<<<< HEAD
            raise FSMBaseException(msg="retrieve_finished_query() couldn't count the rows. "
                                       "This suggest a major change in API return format. Error: " + str(err))
=======
            raise FSMBaseException(err)
>>>>>>> Full FSM Commit

        if row_count > 1000:
            pages = int(row_count) / 1000
            if pages > 0:
                for i in range(pages):
                    self._module.paramgram["uri"] = FSMEndpoints.GET_REPORT_RESULTS + str(query_id) \
                                                    + "/" + str((i + 1) * 1000) + '/1000'
                    url = self.create_endpoint_url()
                    out_xml_append = self.get_query_results(self.next_http_auth, url)
                    if out_xml_append != '':
                        out_xml.append(out_xml_append.decode("utf-8"))

        # FORMAT THE RETURN DICTIONARY
<<<<<<< HEAD
        if row_count > 0:
            combined_xml_string = self._tools.merge_xml_from_list_to_string(out_xml)
            raw_output_json = self._tools.xml2dict(combined_xml_string)
            output_json = self._tools.dump_xml(out_xml)
            output_csv = self._tools.report_result_to_csv(output_json)
            formatted_output_dict = self.format_results(output_json, combined_xml_string)
            formatted_output_dict["csv_results"] = output_csv
            formatted_output_dict["json_results_raw"] = raw_output_json
            formatted_output_dict["xml_results_raw"] = combined_xml_string
            formatted_output_dict["row_count"] = row_count
            formatted_output_dict["report_rc"] = formatted_output_dict["json_results_raw"]["queryResult"]["@errorCode"]
            formatted_output_dict["query_id"] = query_id
            formatted_output_dict["xml_query"] = self.report_xml_source
        elif row_count == 0:
            combined_xml_string = out_xml[0]
            output_json = self._tools.xml2dict(combined_xml_string)
            formatted_output_dict = self.format_results(output_json, combined_xml_string)
            formatted_output_dict["csv_results"] = None
            formatted_output_dict["row_count"] = "0"
            formatted_output_dict["query_id"] = query_id
            formatted_output_dict["xml_query"] = self.report_xml_source
=======
        combined_xml_string = self.merge_xml_from_list_to_string(out_xml)
        raw_output_json = self.xml2dict(combined_xml_string)
        output_json = self.dump_xml(out_xml)
        output_csv = self.report_result_to_csv(output_json)
        formatted_output_dict = self.format_results(output_json, combined_xml_string)
        formatted_output_dict["csv_results"] = output_csv
        formatted_output_dict["json_results_raw"] = raw_output_json
        formatted_output_dict["xml_results_raw"] = combined_xml_string
        formatted_output_dict["row_count"] = row_count
        formatted_output_dict["report_rc"] = formatted_output_dict["json_results_raw"]["queryResult"]["@errorCode"]
        formatted_output_dict["query_id"] = formatted_output_dict["json_results_raw"]["queryResult"]["@queryId"]
        formatted_output_dict["xml_query"] = self.report_xml_source
>>>>>>> Full FSM Commit

        return formatted_output_dict

    def submit_report_request(self, auth, url, report_xml):
        """
<<<<<<< HEAD
        Submits the report request to the API.

        :param auth: Authentication header created in create_auth_header()
        :param url: URL created in create_endpoint_url()
        :param report_xml: string format of the report XML to be submitted.

        :return: xml
=======

        :param auth:
        :param url:
        :param report_xml:
        :return:
>>>>>>> Full FSM Commit
        """
        headers = {'Content-Type': 'text/xml', 'Authorization': auth}
        req = urllib2.Request(url, report_xml, headers)
        out_xml = None
        try:
            handle = urllib2.urlopen(req, context=self.ssl_context)
            out_xml = handle.read()
            try:
                self.last_http_return_code = handle.getcode()
                self.last_http_return_headers = handle.info()
                self.last_http_return_url = url
            except BaseException as err:
<<<<<<< HEAD
                raise FSMBaseException(msg="submit_report_request() failed to get last HTTP codes. Error: " + str(err))
        except BaseException as err:
            raise FSMBaseException(msg="submit_report_request() failed. Error: " + str(err))
=======
                raise FSMBaseException(err)
        except BaseException as err:
            raise FSMBaseException(err)
>>>>>>> Full FSM Commit
        return out_xml

    def get_query_progress(self, auth, url):
        """
<<<<<<< HEAD
        Checks on the progress of a query ID.

        :param auth: Authentication header created in create_auth_header()
        :param url: URL created in create_endpoint_url()

        :return: xml
=======

        :param auth:
        :param url:
        :return:
>>>>>>> Full FSM Commit
        """

        headers = {'Content-Type': 'text/xml', 'Authorization': auth}
        req = urllib2.Request(url, None, headers)
        out_xml = None
        try:
            handle = urllib2.urlopen(req, context=self.ssl_context)
            out_xml = handle.read()
            if 'error code="255"' in out_xml:
                raise FSMBaseException(msg="Query Error, invalid query_id used to query progress.")
        except BaseException as err:
<<<<<<< HEAD
            raise FSMBaseException(msg="get_query_progress() failed. Error: " + str(err))
=======
            raise FSMBaseException(err)
>>>>>>> Full FSM Commit
        return out_xml

    def get_query_results(self, auth, url):
        """
<<<<<<< HEAD
        Gets the results of a specific query ID.

        :param auth: Authentication header created in create_auth_header()
        :param url: URL created in create_endpoint_url()

        :return: xml
=======

        :param auth:
        :param url:
        :return:
>>>>>>> Full FSM Commit
        """
        headers = {'Content-Type': 'text/xml', 'Authorization': auth}
        req = urllib2.Request(url, None, headers)
        out_xml = None
        try:
            handle = urllib2.urlopen(req, context=self.ssl_context)
            out_xml = handle.read()
            if 'error code="255"' in out_xml:
                raise FSMBaseException(msg="Query Error.")
        except BaseException as err:
<<<<<<< HEAD
            raise FSMBaseException(msg="get_query_results() failed. Error: " + str(err))
        return out_xml

    def get_relative_epoch(self, relative_mins):
        """
        Returns an EPOCH value which has subtracted X relative_mins.
        :param relative_mins: Number of minutes to subtract from current time before converting to epoch
        :return: epoch
        """
        current_datetime = self._tools.get_current_datetime()
        current_epoch = self._tools.convert_timestamp_to_epoch(current_datetime)
=======
            raise FSMBaseException(err)
        return out_xml

    @staticmethod
    def prepare_report_xml_query(xml_report):
        """

        :param xml_report:
        :return:
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

        :param input_list:
        :return:
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

        :param xml_in:
        :return:
        """
        xml_out = xmltodict.parse(xml_in, process_namespaces=True)
        json_out = json.dumps(xml_out)
        dict_out = json.loads(json_out)
        return dict_out

    @staticmethod
    def dict2xml(dict_in):
        xml_out = xmltodict.unparse(dict_in, pretty=True)
        return xml_out

    @staticmethod
    def print_report_result(param):
        """

        :param param:
        :return:
        """
        if len(param) == 0:
            print "No records found. Exit"
            exit()
        else:
            print "Total records %d" % len(param)
            keys = param[0].keys()
            print ','.join(keys)
            for item in param:
                itemKeys = item.keys()
                value = []
                for key in keys:
                    if key not in itemKeys:
                        value.append('')
                    else:
                        value.append(item[key])
                print ','.join(value)

    @staticmethod
    def report_result_to_csv(param):
        """

        :param param:
        :return:
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

        :param input_xml:
        :return:
        """
        try:
            doc = xml.dom.minidom.parseString(input_xml)
        except BaseException as err:
            raise FSMBaseException(err)

    @staticmethod
    def dump_xml(xml_list):
        """

        :param xml_list:
        :return:
        """
        param = []
        for item in xml_list:
            doc = xml.dom.minidom.parseString(item.encode('ascii', 'xmlcharrefreplace'))
            for node in doc.getElementsByTagName("events"):
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
        return param

    @staticmethod
    def get_current_datetime():
        return_datetime = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        return return_datetime

    def get_relative_epoch(self, relative_mins):
        current_datetime = self.get_current_datetime()
        current_epoch = self.convert_timestamp_to_epoch(current_datetime)
>>>>>>> Full FSM Commit
        subtract_seconds = relative_mins * 60
        relative_epoch = float(current_epoch) - float(subtract_seconds)
        return relative_epoch

    def get_absolute_epoch(self):
<<<<<<< HEAD
        """
        Returns two epoch values, begin and end dates. Dates are specified in absolute parameters in the
        fsm_report_query module. These epoch values are then "slipped" into the XML before submitting.

        :return: two epoch values, begin and end dates.
        """
        start_epoch = None
        end_epoch = None
        # BUILD THE TIMESTAMP
        begin_timestamp = self._module.paramgram["report_absolute_begin_date"] \
                          + " " + self._module.paramgram["report_absolute_begin_time"]
        end_timestamp = self._module.paramgram["report_absolute_end_date"] \
                        + " " + self._module.paramgram["report_absolute_end_time"]
        start_epoch = self._tools.convert_timestamp_to_epoch(begin_timestamp)
        end_epoch = self._tools.convert_timestamp_to_epoch(end_timestamp)

        return start_epoch, end_epoch

    def replace_fsm_report_timestamp_absolute(self):
        """
        Takes an absolute timestamp from the fsm_report_query module and replaces report XML with the proper values.

        :return: xml
        """
        # GET DESIRED ABSOLUTE TIME
        low_epoch = self._tools.convert_timestamp_to_epoch(self._module.paramgram["report_absolute_begin_date"] + " " +
                                                           self._module.paramgram["report_absolute_begin_time"])
        high_epoch = self._tools.convert_timestamp_to_epoch(self._module.paramgram["report_absolute_end_date"] + " " +
                                                            self._module.paramgram["report_absolute_end_time"])
=======
        start_epoch = None
        end_epoch = None
        # BUILD THE TIMESTAMP
        begin_timestamp = self._module.paramgram["report_absolute_begin_date"] + " " + \
                          self._module.paramgram["report_absolute_begin_time"]
        end_timestamp = self._module.paramgram["report_absolute_end_date"] + " " + \
                        self._module.paramgram["report_absolute_end_time"]
        start_epoch = self.convert_timestamp_to_epoch(begin_timestamp)
        end_epoch = self.convert_timestamp_to_epoch(end_timestamp)

        return start_epoch, end_epoch

    @staticmethod
    def convert_epoch_to_datetime(epoch):
        return_time = datetime.datetime.fromtimestamp(float(epoch)).strftime('%m/%d/%Y %H:%M:%S')
        return_time_utc = datetime.datetime.utcfromtimestamp(float(epoch)).strftime('%m/%d/%Y %H:%M:%S')
        return return_time, return_time_utc

    @staticmethod
    def convert_timestamp_to_epoch(timestamp):
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

    def replace_fsm_report_timestamp_absolute(self):
        # GET DESIRED ABSOLUTE TIME
        low_epoch = self.convert_timestamp_to_epoch(self._module.paramgram["report_absolute_begin_date"] + " " +
                                                    self._module.paramgram["report_absolute_begin_time"])
        high_epoch = self.convert_timestamp_to_epoch(self._module.paramgram["report_absolute_end_date"] + " " +
                                                     self._module.paramgram["report_absolute_end_time"])
>>>>>>> Full FSM Commit
        new_xml = self._module.paramgram["input_xml"]
        if "<ReportInterval>" in new_xml:
            new_xml = re.sub(r'<Low>.*</Low>', '<Low>' + str(low_epoch) + '</Low>', new_xml)
            new_xml = re.sub(r'<High>.*</High>', '<High>' + str(high_epoch) + '</High>', new_xml)
        else:
            add_xml = '<ReportInterval><Low>' + str(low_epoch) + '</Low>'
            add_xml = add_xml + '<High>' + str(high_epoch) + '</High></ReportInterval></Report>'
            new_xml = new_xml.replace("</Report>", add_xml)
        return new_xml

    def replace_fsm_report_timestamp_relative(self):
<<<<<<< HEAD
        """
        Takes a relative timestamp from the fsm_report_query module and replaces report XML with the proper values.

        :return: xml
        """
        high_epoch = self._tools.convert_timestamp_to_epoch(self._tools.get_current_datetime())
=======
        high_epoch = self.convert_timestamp_to_epoch(self.get_current_datetime())
>>>>>>> Full FSM Commit
        low_epoch = self.get_relative_epoch(self._module.paramgram["report_relative_mins"])
        new_xml = self._module.paramgram["input_xml"]
        if "<ReportInterval>" in new_xml:
            new_xml = re.sub(r'<Low>.*</Low>', '<Low>' + str(low_epoch) + '</Low>', new_xml)
            new_xml = re.sub(r'<High>.*</High>', '<High>' + str(high_epoch) + '</High>', new_xml)
            new_xml = new_xml.replace(".0</Low>", "</Low>")
            new_xml = new_xml.replace(".0</High>", "</High>")
        else:
            add_xml = '<ReportInterval><Low>' + str(low_epoch) + '</Low>'
            add_xml = add_xml + '<High>' + str(high_epoch) + '</High></ReportInterval></Report>'
            new_xml = new_xml.replace("</Report>", add_xml)
            new_xml = new_xml.replace(".0</Low>", "</Low>")
            new_xml = new_xml.replace(".0</High>", "</High>")
        return new_xml

<<<<<<< HEAD
    ###########################
    # BEGIN EXIT HANDLING CODE
    ###########################
=======
>>>>>>> Full FSM Commit

    def govern_response(self, module, results, msg=None, good_codes=None,
                        stop_on_fail=None, stop_on_success=None, skipped=None,
                        changed=None, unreachable=None, failed=None, success=None, changed_if_success=None,
                        ansible_facts=None):
        """
        This function will attempt to apply default values to canned responses from FortiSIEM we know of.
        This saves time, and turns the response in the module into a "one-liner", while still giving us...
        the flexibility to directly use return_response in modules if we have too. This function saves repeated code.

        :param module: The Ansible Module CLASS object, used to run fail/exit json
        :type module: object
        :param msg: An overridable custom message from the module that called this.
        :type msg: string
        :param results: A dictionary object containing an API call results
        :type results: dict
        :param good_codes: A list of exit codes considered successful from FortiSIEM
        :type good_codes: list
        :param stop_on_fail: If true, stops playbook run when return code is NOT IN good codes (default: true)
        :type stop_on_fail: boolean
        :param stop_on_success: If true, stops playbook run when return code is IN good codes (default: false)
        :type stop_on_success: boolean
        :param changed: If True, tells Ansible that object was changed (default: false)
        :type skipped: boolean
        :param skipped: If True, tells Ansible that object was skipped (default: false)
        :type skipped: boolean
        :param unreachable: If True, tells Ansible that object was unreachable (default: false)
        :type unreachable: boolean
        :param failed: If True, tells Ansible that execution was a failure. Overrides good_codes. (default: false)
        :type unreachable: boolean
        :param success: If True, tells Ansible that execution was a success. Overrides good_codes. (default: false)
        :type unreachable: boolean
        :param changed_if_success: If True, defaults to changed if successful if you specify or not"
        :type changed_if_success: boolean
        :param ansible_facts: A prepared dictionary of ansible facts from the execution.
        :type ansible_facts: dict
        """
        if module is None and results is None:
            raise FSMBaseException("govern_response() was called without a module and/or results tuple! Fix!")
        # Get the Return code from results
        try:
            rc = results["rc"]
        except BaseException:
            raise FSMBaseException("govern_response() was called without the return code at results[rc]")

        # init a few items
        rc_data = None

        # Get the default values for the said return code.
        try:
            rc_codes = FSM_RC.get('fsm_return_codes')
            rc_data = rc_codes.get(rc)
        except BaseException:
            pass

        if not rc_data:
            rc_data = {}
        # ONLY add to overrides if not none -- This is very important that the keys aren't added at this stage
        # if they are empty. And there aren't that many, so let's just do a few if then statements.
        if good_codes is not None:
            rc_data["good_codes"] = good_codes
        if stop_on_fail is not None:
            rc_data["stop_on_fail"] = stop_on_fail
        if stop_on_success is not None:
            rc_data["stop_on_success"] = stop_on_success
        if skipped is not None:
            rc_data["skipped"] = skipped
        if changed is not None:
            rc_data["changed"] = changed
        if unreachable is not None:
            rc_data["unreachable"] = unreachable
        if failed is not None:
            rc_data["failed"] = failed
        if success is not None:
            rc_data["success"] = success
        if changed_if_success is not None:
            rc_data["changed_if_success"] = changed_if_success
        if msg is not None:
            rc_data["msg"] = msg
        if ansible_facts is None:
            rc_data["ansible_facts"] = {}
        else:
            rc_data["ansible_facts"] = ansible_facts

        # PROCESS OUTPUTS TO FILES
        if self.export_json_to_file_path:
            try:
<<<<<<< HEAD
                if results["json_results"]:
                    self.json_results_to_file_path(results["json_results"])
            except BaseException as err:
                raise FSMBaseException(msg="Writing JSON results to file failed. Error: " + str(err))
        if self.export_xml_to_file_path:
            try:
                if results["xml_results"]:
                    self.xml_results_to_file_path(results["xml_results"])
            except BaseException as err:
                raise FSMBaseException(msg="Writing XML results to file failed. Error: " + str(err))
        if self.export_csv_to_file_path:
            try:
                if results["csv_results"]:
                    self.csv_results_to_file_path(results["csv_results"])
            except BaseException as err:
                raise FSMBaseException(msg="Writing CSV results to file failed. Error: " + str(err))
=======
                self.json_results_to_file_path(results["json_results"])
            except BaseException as err:
                raise FSMBaseException(err)
        if self.export_xml_to_file_path:
            try:
                self.xml_results_to_file_path(results["xml_results"])
            except BaseException as err:
                raise FSMBaseException(err)
        if self.export_csv_to_file_path:
            try:
                self.csv_results_to_file_path(results["csv_results"])
            except BaseException as err:
                raise FSMBaseException(err)
>>>>>>> Full FSM Commit

        return self.return_response(module=module,
                                    results=results,
                                    msg=rc_data.get("msg", "NULL"),
                                    good_codes=rc_data.get("good_codes", (200,)),
                                    stop_on_fail=rc_data.get("stop_on_fail", True),
                                    stop_on_success=rc_data.get("stop_on_success", False),
                                    skipped=rc_data.get("skipped", False),
                                    changed=rc_data.get("changed", False),
                                    changed_if_success=rc_data.get("changed_if_success", False),
                                    unreachable=rc_data.get("unreachable", False),
                                    failed=rc_data.get("failed", False),
                                    success=rc_data.get("success", False),
                                    ansible_facts=rc_data.get("ansible_facts", dict()),
                                    export_json_to_screen=self.export_json_to_screen
                                    )

    @staticmethod
    def return_response(module, results, msg="NULL", good_codes=(200,),
                        stop_on_fail=True, stop_on_success=False, skipped=False,
                        changed=False, unreachable=False, failed=False, success=False, changed_if_success=True,
                        ansible_facts=(), export_json_to_screen=None):
        """
        This function controls the logout and error reporting after an method or function runs. The exit_json for
        ansible comes from logic within this function. If this function returns just the msg, it means to continue
        execution on the playbook. It is called from the ansible module, or from the self.govern_response function.

        :param module: The Ansible Module CLASS object, used to run fail/exit json
        :type module: object
        :param msg: An overridable custom message from the module that called this.
        :type msg: string
        :param results: A dictionary object containing an API call results
        :type results: dict
        :param good_codes: A list of exit codes considered successful from FortiSIEM
        :type good_codes: list
        :param stop_on_fail: If true, stops playbook run when return code is NOT IN good codes (default: true)
        :type stop_on_fail: boolean
        :param stop_on_success: If true, stops playbook run when return code is IN good codes (default: false)
        :type stop_on_success: boolean
        :param changed: If True, tells Ansible that object was changed (default: false)
        :type skipped: boolean
        :param skipped: If True, tells Ansible that object was skipped (default: false)
        :type skipped: boolean
        :param unreachable: If True, tells Ansible that object was unreachable (default: false)
        :type unreachable: boolean
        :param failed: If True, tells Ansible that execution was a failure. Overrides good_codes. (default: false)
        :type unreachable: boolean
        :param success: If True, tells Ansible that execution was a success. Overrides good_codes. (default: false)
        :type unreachable: boolean
        :param changed_if_success: If True, defaults to changed if successful if you specify or not"
        :type changed_if_success: boolean
        :param ansible_facts: A prepared dictionary of ansible facts from the execution.
        :type ansible_facts: dict
        :param export_json_to_screen: If enabled/true, we will export the json results to screen.
        :type export_json_to_screen: bool

        :return: A string object that contains an error message
        :rtype: str
        """
<<<<<<< HEAD
        return_results = None
=======
>>>>>>> Full FSM Commit
        # VALIDATION ERROR
        if (len(results) == 0) or (failed and success) or (changed and unreachable):
            module.exit_json(msg="Handle_response was called with no results, or conflicting failed/success or "
                                 "changed/unreachable parameters. Fix the exit code on module. "
                                 "Generic Failure", failed=True)

        # IDENTIFY SUCCESS/FAIL IF NOT DEFINED
        if not failed and not success:
            if len(results) > 0:
                if results["rc"] not in good_codes:
                    failed = True
                elif results["rc"] in good_codes:
                    success = True

        if len(results) > 0:
            # IF NO MESSAGE WAS SUPPLIED, GET IT FROM THE RESULTS, IF THAT DOESN'T WORK, THEN WRITE AN ERROR MESSAGE
            if msg == "NULL":
                try:
                    msg = results["http_metadata"]['status']['message']
                except BaseException:
                    msg = "No status message returned at results[http_metadata][status][message], " \
                          "and none supplied to msg parameter for handle_response."
                    raise FSMBaseException(msg)

            # PROCESS PRINT TO SCREEN OPTION
            if export_json_to_screen == "enable":
                return_results = results["json_results"]
            elif export_json_to_screen == "disable":
                return_results = "Results printing to screen is disabled " \
                                 "from export_json_to_screen = disable in playbook. We also remove from " \
                                 "Ansible_facts so if you need that data pipeline, re-enable export json to screen"
                del ansible_facts["response"]
            if failed:
                # BECAUSE SKIPPED/FAILED WILL OFTEN OCCUR ON CODES THAT DON'T GET INCLUDED, THEY ARE CONSIDERED FAILURES
                # HOWEVER, THEY ARE MUTUALLY EXCLUSIVE, SO IF IT IS MARKED SKIPPED OR UNREACHABLE BY THE MODULE LOGIC
                # THEN REMOVE THE FAILED FLAG SO IT DOESN'T OVERRIDE THE DESIRED STATUS OF SKIPPED OR UNREACHABLE.
                if failed and skipped:
                    failed = False
                if failed and unreachable:
                    failed = False
                if stop_on_fail:
                    module.exit_json(msg=msg, failed=failed, changed=changed,
                                     unreachable=unreachable, skipped=skipped,
                                     results=return_results, ansible_facts=ansible_facts,
                                     invocation={"module_args": ansible_facts["ansible_params"]})
            elif success:
                if changed_if_success:
                    changed = True
                    success = False
                if stop_on_success:
                    module.exit_json(msg=msg, success=success, changed=changed, unreachable=unreachable,
                                     skipped=skipped, results=return_results,
                                     ansible_facts=ansible_facts,
                                     invocation={"module_args": ansible_facts["ansible_params"]})

        return msg

<<<<<<< HEAD
    @staticmethod
    def construct_ansible_facts(response, ansible_params, paramgram, *args, **kwargs):
=======
    def construct_ansible_facts(self, response, ansible_params, paramgram, *args, **kwargs):
>>>>>>> Full FSM Commit
        """
        Constructs a dictionary to return to ansible facts, containing various information about the execution.

        :param response: Contains the response from the FortiSIEM.
        :type response: dict
        :param ansible_params: Contains the parameters Ansible was called with.
        :type ansible_params: dict
        :param paramgram: Contains the paramgram passed to the modules' local modify function.
        :type paramgram: dict
        :param args: Free-form arguments that could be added.
        :param kwargs: Free-form keyword arguments that could be added.

        :return: A dictionary containing lots of information to append to Ansible Facts.
        :rtype: dict
        """

        facts = {
            "response": response,
            "ansible_params": scrub_dict(ansible_params),
            "paramgram": scrub_dict(paramgram),
        }

        if args:
            facts["custom_args"] = args
        if kwargs:
            facts.update(kwargs)

        return facts
<<<<<<< HEAD
=======


>>>>>>> Full FSM Commit
