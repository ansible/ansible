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
from ansible.module_utils.network.fortisiem.common import SyslogLevel
from ansible.module_utils.network.fortisiem.common import SendSyslog
from ansible.module_utils.network.fortisiem.common import scrub_dict
from ansible.module_utils.network.fortisiem.fsm_xml_generators import FSMXMLGenerators

import base64
import urllib2
import ssl
import json
import xml.dom.minidom
import re

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
        except BaseException:
            self.export_json_to_screen = None
            self.export_json_to_file_path = None
            self.export_xml_to_file_path = None
            self.export_csv_to_file_path = None
        self.report_xml_source = None
        self.report_query_id = None
        self.report_length = None

    def get_organizations(self):
        """
        Gets a list of organizations from a target FortiSIEM Supervisor.

        :return: dict
        """
        url = "https://" + self._module.paramgram["host"] + FSMEndpoints.GET_ORGS
        auth = self.create_auth_header()
        output_xml = self.submit_simple_request(auth, url)
        output_json = self._tools.xml2dict(output_xml)
        formatted_output_dict = self.format_results(output_json, output_xml)
        return formatted_output_dict

    def create_ssl_context(self):
        """
        Creates the SSL context for handling certificates.

        :return: ssl context object
        """
        ignore_ssl_setting = None
        ctx = None
        try:
            ignore_ssl_setting = self._module.paramgram["ignore_ssl_errors"]
        except BaseException as err:
            FSMBaseException(msg="create_ssl_context() failed to ignore ssl setting" + str(err))

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
        Creates authentication header for FortiSIEM API calls based on username and password.

        :return: Base64 Encoded string
        """
        encode_password = base64.b64encode(self._module.paramgram["username"] + ":" +
                                           self._module.paramgram["password"])
        auth = "Basic %s" % encode_password
        return auth

    def create_endpoint_url(self):
        """
        Joins the host and URI into a full URL for the FortiSIEMHandler class to use.

        :return: string
        """
        url = "https://" + self._module.paramgram["host"] + self._module.paramgram["uri"]
        return url

    def submit_simple_request(self, auth, url):
        """
        Submits a simple GET request without an XML payload.

        :param auth: Authentication header created in create_auth_header()
        :param url: URL created in create_endpoint_url()

        :return: xml
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
                raise FSMBaseException(msg="submit_simple_request() failed to get http codes. Error: " + str(err))
        except BaseException as err:
            raise FSMBaseException(msg="submit_simple_request() failed" + str(err))
        return out_xml

    def submit_simple_payload_request(self, auth, url, payload):
        """
        Submits a simple GET request with an XML payload.

        :param auth: Authentication header created in create_auth_header()
        :param url: URL created in create_endpoint_url()
        :param payload: XML payload in string form

        :return: xml
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
        return out_xml

    def handle_simple_request(self):
        """
        Handles the "simple" get request without an XML payload, from end-to-end, including result formatting.

        :return: dict
        """
        formatted_output_dict = None
        auth = self.create_auth_header()
        url = self.create_endpoint_url()
        output_xml = self.submit_simple_request(auth, url)
        try:
            if "<password>" in output_xml:
                output_xml = re.sub(r'(<password>.*?<\/password>)', '', output_xml)
                output_xml = re.sub(r'(<suPassword>.*?<\/suPassword>)', '', output_xml)
        except BaseException as err:
            pass
        if output_xml:
            try:
                output_json = self._tools.xml2dict(output_xml)
                formatted_output_dict = self.format_results(output_json, output_xml)
            except BaseException as err:
                try:
                    output_json = {"fsm_response": str(output_xml)}
                    output_xml = "<fsm_response>" + str(output_xml + "</fsm_response>")
                    formatted_output_dict = self.format_results(output_json, output_xml)
                except BaseException as err:
                    raise FSMBaseException(msg="handle_simple_request() couldn't deal with the response. "
                                               "Error:" + str(err))

        elif not output_xml:
            output_json = {"status": "OK"}
            output_xml = "<status>OK</status>"
            formatted_output_dict = self.format_results(output_json, output_xml)
        return formatted_output_dict

    def handle_simple_payload_request(self, payload):
        """
        Handles the  get request with an XML payload, from end-to-end, including result formatting.

        :return: dict
        """
        formatted_output_dict = None
        auth = self.create_auth_header()
        url = self.create_endpoint_url()
        output_xml = self.submit_simple_payload_request(auth, url, payload)
        try:
            if "<password>" in output_xml:
                output_xml = re.sub(r'(<password>.*?<\/password>)', '', output_xml)
                output_xml = re.sub(r'(<suPassword>.*?<\/suPassword>)', '', output_xml)
        except BaseException as err:
            pass
        if output_xml:
            try:
                output_json = self._tools.xml2dict(output_xml)
                formatted_output_dict = self.format_results(output_json, output_xml)
                formatted_output_dict["payload"] = payload
            except BaseException as err:
                try:
                    output_json = {"fsm_response": str(output_xml)}
                    output_xml = "<fsm_response>" + str(output_xml + "</fsm_response>")
                    formatted_output_dict = self.format_results(output_json, output_xml)
                    formatted_output_dict["payload"] = payload
                except BaseException as err:
                    raise FSMBaseException(msg="handle_simple_payload_request() couldn't deal with the response. "
                                               "Error:" + str(err))

        elif not output_xml:
            output_json = {"status": "OK"}
            output_xml = "<status>OK</status>"
            formatted_output_dict = self.format_results(output_json, output_xml)

        return formatted_output_dict

    def handle_syslog_request(self):
        """
        Handles a syslog request from end-to-end, and reports on the results.

        :return: dict
        """
        output_dict = {"status": "FAILED", "message": "None"}
        try:
            log = SendSyslog(host=self._module.paramgram["syslog_host"],
                             port=self._module.paramgram["network_port"],
                             protocol=self._module.paramgram["network_protocol"],
                             level=self._module.paramgram["syslog_level"],
                             facility=self._module.paramgram["syslog_facility"],
                             ssl_context=self.create_ssl_context(),
                             )
            output_dict = log.send(header=self._module.paramgram["syslog_header"],
                                   message=self._module.paramgram["syslog_message"])
        except BaseException as err:
            raise FSMBaseException(msg="handle_syslog_request() couldn't send the syslog. Error: " + str(err))
        return output_dict

    def format_results(self, json_results, xml_results):
        """
        Takes the JSON and XML results from multiple "handlers" and formats them into a structured return dictionary.

        :param json_results: The results from an API call, in JSON form
        :param xml_results: The results from an API call, in XML form

        :return:dict
        """

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
        Does the same as format_results(), however, it is specific to the fsm_verify_device module.
        These calls require careful formatting.

        :param ip_to_verify: an ip address that was verified
        :param cmdb: cmdb results from verification
        :param events: event results from verification
        :param monitors: monitor results from verifiction

        :return: dict
        """

        return_dict = dict()
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
            except BaseException as err:
                return_dict["device"]["cmdb_results"] = None
        if not events:
            missing.append("events")
        else:
            present.append("events")
            return_dict["device"]["event_results"] = \
                self._tools.get_events_info_for_specific_ip(events)
        if not monitors:
            missing.append("monitors")
        else:
            present.append("monitors")
            return_dict["device"]["monitor_results"] = \
                self._tools.get_monitors_info_for_specific_ip(monitors, ip_to_verify)

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
        """
        try:
            f = open(self.export_json_to_file_path, "w")
            f.write(json.dumps(json_results, indent=4, sort_keys=True))
            f.close()
        except BaseException as err:
            raise FSMBaseException(msg="JSON Failed to write to file: " + str(self.export_json_to_file_path) +
                                       "| Error: " + str(err))

    def xml_results_to_file_path(self, xml_results):
        """
        Writes results to a XML file. Pretty-Prints the XML.

        :param xml_results: xml to write to file
        """
        try:
            xml_out = xml.dom.minidom.parseString(xml_results)
            xml_pretty = xml_out.toprettyxml()
            f = open(self.export_xml_to_file_path, "w")
            f.write(xml_pretty)
            f.close()
        except BaseException as err:
            raise FSMBaseException(msg="XML Failed to write to file: " + str(self.export_xml_to_file_path) +
                                       "| Error: " + str(err))

    def csv_results_to_file_path(self, csv_results):
        """
        Writes results to a CSV file

        :param csv_results: csv to write to file
        """
        try:
            f = open(self.export_csv_to_file_path, "w")
            f.write(csv_results)
            f.close()
        except BaseException as err:
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
        """
        self.post_report_get_query_id()
        self.wait_for_query_finish()
        report_out = self.retrieve_finished_query()
        return report_out

    def post_report_get_query_id(self):
        """
        Submits report XML for query, and returns the query ID.

        No return. Writes query_id to self.
        """
        self.next_http_auth = self.create_auth_header()
        url = self.create_endpoint_url()
        report_xml = self._tools.prepare_report_xml_query(self._module.paramgram["input_xml"])
        query_id = self.submit_report_request(self.next_http_auth, url, report_xml)
        self.report_query_id = query_id

        if 'error code="255"' in query_id:
            raise FSMBaseException(msg="Query Error, debug XML file being sent, it caused an error.")

    def wait_for_query_finish(self):
        """
        Waits for a specified query ID to reach 100% completion, then exits the time loop.
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
        Gets results from a finished report. Formats results for return.

        :return: dict
        """
        query_id = self.report_query_id
        self._module.paramgram["uri"] = FSMEndpoints.GET_REPORT_RESULTS + str(query_id) + "/0/1000"
        url = self.create_endpoint_url()
        out_xml = []
        first_results = self.get_query_results(self.next_http_auth, url)
        out_xml.append(first_results.decode("utf-8"))
        try:
            p = re.compile(r'totalCount="\d+"')
            mlist = p.findall(out_xml[0])
            mm = mlist[0].replace('"', '')
            row_count = mm.split("=")[-1]
            row_count = int(row_count)
        except BaseException as err:
            raise FSMBaseException(msg="retrieve_finished_query() couldn't count the rows. "
                                       "This suggest a major change in API return format. Error: " + str(err))

        if row_count > 1000:
            pages = int(row_count) / 1000
            if pages > 0:
                for i in range(pages):
                    self._module.paramgram["uri"] = FSMEndpoints.GET_REPORT_RESULTS + str(query_id) + \
                        "/" + str((i + 1) * 1000) + '/1000'
                    url = self.create_endpoint_url()
                    out_xml_append = self.get_query_results(self.next_http_auth, url)
                    if out_xml_append != '':
                        out_xml.append(out_xml_append.decode("utf-8"))

        # FORMAT THE RETURN DICTIONARY
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
            try:
                formatted_output_dict["report_rc"] = \
                    formatted_output_dict["json_results_raw"]["@queryResult"]["errorCode"]
            except KeyError:
                try:
                    formatted_output_dict["report_rc"] = \
                        formatted_output_dict["json_results_raw"]["queryResult"]["@errorCode"]
                except BaseException:
                    formatted_output_dict["report_rc"] = "Unknown"
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

        return formatted_output_dict

    def submit_report_request(self, auth, url, report_xml):
        """
        Submits the report request to the API.

        :param auth: Authentication header created in create_auth_header()
        :param url: URL created in create_endpoint_url()
        :param report_xml: string format of the report XML to be submitted.

        :return: xml
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
                raise FSMBaseException(msg="submit_report_request() failed to get last HTTP codes. Error: " + str(err))
        except BaseException as err:
            raise FSMBaseException(msg="submit_report_request() failed. Error: " + str(err))
        return out_xml

    def get_query_progress(self, auth, url):
        """
        Checks on the progress of a query ID.

        :param auth: Authentication header created in create_auth_header()
        :param url: URL created in create_endpoint_url()

        :return: xml
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
            raise FSMBaseException(msg="get_query_progress() failed. Error: " + str(err))
        return out_xml

    def get_query_results(self, auth, url):
        """
        Gets the results of a specific query ID.

        :param auth: Authentication header created in create_auth_header()
        :param url: URL created in create_endpoint_url()

        :return: xml
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
        subtract_seconds = relative_mins * 60
        relative_epoch = float(current_epoch) - float(subtract_seconds)
        return relative_epoch

    def get_absolute_epoch(self):
        """
        Returns two epoch values, begin and end dates. Dates are specified in absolute parameters in the
        fsm_report_query module. These epoch values are then "slipped" into the XML before submitting.

        :return: two epoch values, begin and end dates.
        """
        start_epoch = None
        end_epoch = None
        # BUILD THE TIMESTAMP
        begin_timestamp = self._module.paramgram["report_absolute_begin_date"] + " " + \
            self._module.paramgram["report_absolute_begin_time"]
        end_timestamp = self._module.paramgram["report_absolute_end_date"] + " " + \
            self._module.paramgram["report_absolute_end_time"]
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
        """
        Takes a relative timestamp from the fsm_report_query module and replaces report XML with the proper values.

        :return: xml
        """
        high_epoch = self._tools.convert_timestamp_to_epoch(self._tools.get_current_datetime())
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

    ###########################
    # BEGIN EXIT HANDLING CODE
    ###########################

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
        return_results = None
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

    @staticmethod
    def construct_ansible_facts(response, ansible_params, paramgram, *args, **kwargs):
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
