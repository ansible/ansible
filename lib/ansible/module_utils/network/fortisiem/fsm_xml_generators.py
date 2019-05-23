<<<<<<< HEAD
=======

>>>>>>> Added XML Generators
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

from ansible.module_utils.network.fortisiem.common import FSMEndpoints
from xml.etree import ElementTree as ET


class FSMXMLGenerators(object):
    """
    This class is responsible for generating XML to be used by FortiSIEM modules. Due to the sheer size of these
    methods they were separated to their own class.
    """
<<<<<<< HEAD

=======
>>>>>>> Added XML Generators
    def __init__(self, module):
        self.report_xml_source = None
        self.report_query_id = None
        self.report_length = None
        self._module = module

    # STATIC REPORTS ONLY A FEW TOKENS TO CHANGE

    # ALL DEVICES EVENT TYPES AND COUNT LAST 12 HOURS
    RPT_ALL_DEVICES_EVENT_TYPE_COUNTS = '<?xml version="1.0" encoding="UTF-8"?><Reports>' \
                                        '<Report baseline="" rsSync="">' \
                                        '<Name>All Devices Reporting Events Last 12 Hours</Name>' \
                                        '<Description>All Devices ' \
                                        'Reporting Events Last 12 Hours</Description>' \
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

    def create_org_payload(self):
        """
        Creates an appropriate XML payload to add or update organizations in FortiSIEM.

        :return: xml
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
            max_devices = ET.SubElement(custResource, "configItem")
            max_devices.text = str(self._module.paramgram["org_max_devices"])

        # CONCAT COLLECTORS BEFORE APPENDING IF SPECIFIED
        if self._module.paramgram["org_collectors"]:
            # EXPECTS A LIST
            collector_data = self._module.paramgram["org_collectors"]
            if isinstance(collector_data, list):
<<<<<<< HEAD
                # collector_xml = "<collectors>"
=======
                #collector_xml = "<collectors>"
>>>>>>> Added XML Generators
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
        Creates an appropriate XML payload to add or update credentials in FortiSIEM.

        :return: xml
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
        """
        Creates an appropriate XML payload to discover devices in FortiSIEM.

        :return: xml
        """
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

        xmlstr = ET.tostring(discoverRequest, 'utf-8')
        return xmlstr

    def create_maint_payload(self):
        """
        Creates an appropriate XML payload to add or delete maintenance calendar entries in FortiSIEM.

        :return: xml
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
<<<<<<< HEAD
        return xmlstr
=======
        return xmlstr
>>>>>>> Added XML Generators
