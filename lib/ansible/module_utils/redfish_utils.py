# Copyright 2017-2018, Jose Delarosa <jose.e.delarosa@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

try:
    import requests
except ImportError:
    module.fail_json(msg="Python module requests not found.")

import os
import json
import re
import xml.etree.ElementTree as ET
from distutils.version import LooseVersion
from datetime import datetime

HEADERS = {'content-type': 'application/json'}


class RedfishUtils(object):

    def __init__(self, creds, root_uri):
        self.root_uri = root_uri
        self.creds = creds
        self._init_session()
        self.default_system_id = None
        self.default_chassis_id = None
        self.default_manager_id = None
        return

    # The following functions are to send GET/POST/PATCH/DELETE requests
    def send_get_request(self, uri):
        headers = {}
        if 'token' in self.creds:
            headers = {"X-Auth-Token": self.creds['token']}
        try:
            response = requests.get(uri, headers, verify=False, auth=(self.creds['user'], self.creds['pswd']))
        except:
            raise
        return response

    def send_post_request(self, uri, pyld, hdrs, fileName=None):
        headers = {}
        if 'token' in self.creds:
            headers = {"X-Auth-Token": self.creds['token']}
        try:
            response = requests.post(uri, data=json.dumps(pyld), headers=hdrs, files=fileName, verify=False, auth=(self.creds['user'], self.creds['pswd']))
        except:
            raise
        return response

    def send_patch_request(self, uri, pyld, hdrs):
        headers = {}
        if 'token' in self.creds:
            headers = {"X-Auth-Token": self.creds['token']}
        try:
            response = requests.patch(uri, data=json.dumps(pyld), headers=hdrs, verify=False, auth=(self.creds['user'], self.creds['pswd']))
        except:
            raise
        return response

    def send_delete_request(self, uri, pyld, hdrs):
        headers = {}
        if 'token' in self.creds:
            headers = {"X-Auth-Token": self.creds['token']}
        try:
            response = requests.delete(uri, verify=False, auth=(self.creds['user'], self.creds['pswd']))
        except:
            raise
        return response

    def _init_session(self):
        pass

    def _find_accountservice_resource(self, uri):
        response = self.send_get_request(self.root_uri + uri)
        data = response.json()
        if 'AccountService' not in data:
            return {'ret': False, 'msg': "AccountService resource not found"}
        else:
            account_service = data["AccountService"]["@odata.id"]
            response = self.send_get_request(self.root_uri + account_service)
            data = response.json()
            accounts = data['Accounts']['@odata.id']
            if accounts[-1:] == '/':
                accounts = accounts[:-1]
            self.accounts_uri = accounts
            return {'ret': True}

    def _find_systems_resource(self, uri):
        response = self.send_get_request(self.root_uri + uri)
        data = response.json()
        if 'Systems' not in data:
            return {'ret': False, 'msg': "Systems resource not found"}
        else:
            systems = data["Systems"]["@odata.id"]
            response = self.send_get_request(self.root_uri + systems)
            data = response.json()
            for member in data[u'Members']:
                systems_service = member[u'@odata.id']
            self.systems_uri = systems_service
            return {'ret': True}

    def _find_updateservice_resource(self, uri):
        response = self.send_get_request(self.root_uri + uri)
        data = response.json()
        if 'UpdateService' not in data:
            return {'ret': False, 'msg': "UpdateService resource not found"}
        else:
            update = data["UpdateService"]["@odata.id"]
            self.update_uri = update
            response = self.send_get_request(self.root_uri + update)
            data = response.json()
            firmware_inventory = data['FirmwareInventory'][u'@odata.id']
            self.firmware_uri = firmware_inventory
            return {'ret': True}

    def _find_chassis_resource(self, uri):
        response = self.send_get_request(self.root_uri + uri)
        data = response.json()
        if 'Chassis' not in data:
            return {'ret': False, 'msg': "Chassis resource not found"}
        else:
            chassis = data["Chassis"]["@odata.id"]
            response = self.send_get_request(self.root_uri + chassis)
            data = response.json()
            for member in data[u'Members']:
                chassis_service = member[u'@odata.id']
            self.chassis_uri = chassis_service
            return {'ret': True}

    def _find_managers_resource(self, uri):
        response = self.send_get_request(self.root_uri + uri)
        data = response.json()
        if 'Managers' not in data:
            return {'ret': False, 'msg': "Manager resource not found"}
        else:
            manager = data["Managers"]["@odata.id"]
            response = self.send_get_request(self.root_uri + manager)
            data = response.json()
            for member in data[u'Members']:
                manager_service = member[u'@odata.id']
            self.manager_uri = manager_service
            return {'ret': True}

    def get_logs(self):
        log_svcs_uri_list = []
        list_of_logs = []
        result = {}

        # Find LogService
        response = self.send_get_request(self.root_uri + self.manager_uri)
        data = response.json()

        if 'LogServices' not in data:
            return {'ret': False, 'msg': "LogServices resource not found"}
        else:
            logs_uri = data["LogServices"]["@odata.id"]

        # Find all entries in LogServices
        response = self.send_get_request(self.root_uri + logs_uri)
        # I should really be checking for response.status_code
        data = response.json()
        for log_svcs_entry in data[u'Members']:
            response = self.send_get_request(self.root_uri + log_svcs_entry[u'@odata.id'])
            _data = response.json()
            log_svcs_uri_list.append(_data['Entries'][u'@odata.id'])

        # For each entry in LogServices, get log name and all log entries
        for log_svcs_uri in log_svcs_uri_list:
            logs = {}
            list_of_log_entries = []
            response = self.send_get_request(self.root_uri + log_svcs_uri)
            data = response.json()
            logs['Description'] = data['Description']
            # Get all log entries for each type of log found
            for logEntry in data[u'Members']:
                entry = {}
                # I only extract some fields - Are these entry names standard?
                entry['Name'] = logEntry[u'Name']
                entry['Created'] = logEntry[u'Created']
                entry['Message'] = logEntry[u'Message']
                entry['Severity'] = logEntry[u'Severity']
                list_of_log_entries.append(entry)
            logs['entries'] = list_of_log_entries
            list_of_logs.append(logs)
        result['ret'] = True		# setting to True since we're successful
        result['list_of_logs'] = list_of_logs
        return result         # list_of_logs[logs{list_of_log_entries[entry{}]}]

    def clear_logs(self):
        result = {}

        # Find LogService
        response = self.send_get_request(self.root_uri + self.manager_uri)
        data = response.json()

        if 'LogServices' not in data:
            return {'ret': False, 'msg': "LogServices resource not found"}
        else:
            logs_uri = data["LogServices"]["@odata.id"]

        # Find all entries in LogServices
        response = self.send_get_request(self.root_uri + logs_uri)
        # I should really be checking for response.status_code
        data = response.json()
        for log_svcs_entry in data[u'Members']:
            response = self.send_get_request(self.root_uri + log_svcs_entry["@odata.id"])
            _data = response.json()
            # Check to make sure option is available, otherwise error is ugly
            if "Actions" in _data:
                if "#LogService.ClearLog" in _data[u"Actions"]:
                    self.send_post_request(self.root_uri + _data[u"Actions"]["#LogService.ClearLog"]["target"], {}, HEADERS)
        result['ret'] = True		# assume we're successful
        return result

    def get_storage_controller_info(self):
        result = {}
        controllers_details = []
        controller_list = []

        # Find Storage service
        response = self.send_get_request(self.root_uri + self.systems_uri)
        data = response.json()
        if 'SimpleStorage' not in data:
            return {'ret': False, 'msg': "SimpleStorage resource not found"}
        else:
            storage_uri = data["SimpleStorage"]["@odata.id"]

        # Get a list of all storage controllers and build respective URIs
        response = self.send_get_request(self.root_uri + storage_uri)
        if response.status_code == 200:             # success
            result['ret'] = True
            data = response.json()

            for controller in data[u'Members']:
                controller_list.append(controller[u'@odata.id'])

            for c in controller_list:
                uri = self.root_uri + c
                response = self.send_get_request(uri)
                if response.status_code == 200:             # success
                    data = response.json()

                    controller = {}
                    controller['Name'] = data[u'Name']      # Name of storage controller
                    controller['Health'] = data[u'Status'][u'Health']
                    controllers_details.append(controller)
                else:
                    result = {'ret': False, 'msg': "Error code %s" % response.status_code}
                    return result		# no need to go through the whole loop

            result["entries"] = controllers_details
        else:
            result = {'ret': False, 'msg': "Error code %s" % response.status_code}
        return result

    def get_disk_info(self):
        result = {}
        disks_details = []
        controller_list = []

        # Find Storage service
        response = self.send_get_request(self.root_uri + self.systems_uri)
        data = response.json()
        if 'SimpleStorage' not in data:
            return {'ret': False, 'msg': "SimpleStorage resource not found"}
        else:
            storage_uri = data["SimpleStorage"]["@odata.id"]

        # Get a list of all storage controllers and build respective URIs
        response = self.send_get_request(self.root_uri + storage_uri)
        if response.status_code == 200:             # success
            result['ret'] = True
            data = response.json()

            for controller in data[u'Members']:
                controller_list.append(controller[u'@odata.id'])

            for c in controller_list:
                uri = self.root_uri + c
                response = self.send_get_request(uri)
                if response.status_code == 200:             # success
                    data = response.json()

                    for device in data[u'Devices']:
                        disk = {}
                        disk['Controller'] = data[u'Name']  # Name of storage controller
                        disk['Name'] = device[u'Name']
                        disk['Manufacturer'] = device[u'Manufacturer']
                        disk['Model'] = device[u'Model']
                        disk['State'] = device[u'Status'][u'State']
                        disk['Health'] = device[u'Status'][u'Health']
                        disks_details.append(disk)
                else:
                    result = {'ret': False, 'msg': "Error code %s" % response.status_code}
                    return result		# no need to go through the whole loop

            result["entries"] = disks_details
        else:
            result = {'ret': False, 'msg': "Error code %s" % response.status_code}
        return result

    def restart_manager_gracefully(self, uri):
        result = {}
        payload = {'ResetType': 'GracefulRestart'}
        response = self.send_post_request(self.root_uri + self.manager_uri + uri, payload, HEADERS)
        if response.status_code == 204:		# success
            result['ret'] = True
        else:
            result = {'ret': False, 'msg': "Error code %s" % response.status_code}
        return result

    def manage_system_power(self, uri, command):
        result = {}
        if command == "PowerOn":
            payload = {'ResetType': 'On'}
            response = self.send_post_request(self.root_uri + self.systems_uri + uri, payload, HEADERS)

        elif command == "PowerForceOff":
            payload = {'ResetType': 'ForceOff'}
            response = self.send_post_request(self.root_uri + self.systems_uri + uri, payload, HEADERS)

        elif command == "PowerGracefulRestart":
            payload = {'ResetType': 'GracefulRestart'}
            response = self.send_post_request(self.root_uri + self.systems_uri + uri, payload, HEADERS)

        elif command == "PowerGracefulShutdown":
            payload = {'ResetType': 'GracefulShutdown'}
            response = self.send_post_request(self.root_uri + self.systems_uri + uri, payload, HEADERS)

        else:
            result = {'ret': False, 'msg': 'Invalid Command'}

        if response.status_code == 204:		# success
            result['ret'] = True
        elif response.status_code == 400:
            result = {'ret': False, 'msg': 'Not supported on this platform'}
        elif response.status_code == 405:
            result = {'ret': False, 'msg': "Resource not supported"}
        elif response.status_code == 409:		# verify this
            result = {'ret': False, 'msg': "Action already implemented"}
        else:
            result = {'ret': False, 'msg': "Error code %s" % response.status_code}
        return result

    def list_users(self, user):
        result = {}
        allusers = []
        allusers_details = []

        response = self.send_get_request(self.root_uri + self.accounts_uri)
        if response.status_code == 200:                # success
            result['ret'] = True
            data = response.json()
            for users in data[u'Members']:
                allusers.append(users[u'@odata.id'])   # Here user_list[] are URIs

            # for each user, get details
            for uri in allusers:
                response = self.send_get_request(self.root_uri + uri)
                # return {'ret': True, 'msg': self.root_uri + uri}

                # check status_code again?
                data = response.json()
                if not data[u'UserName'] == "":        # only care if name is not empty
                    user = {}
                    user['Id'] = data[u'Id']
                    user['Name'] = data[u'Name']
                    user['UserName'] = data[u'UserName']
                    user['RoleId'] = data[u'RoleId']
                    allusers_details.append(user)
                result["entries"] = allusers_details
        else:
            result = {'ret': False, 'msg': "Error code %s" % response.status_code}
        return result

    def add_user(self, user):
        result = {}
        uri = self.root_uri + self.accounts_uri + "/" + user['userid']
        username = {'UserName': user['username']}
        pswd = {'Password': user['userpswd']}
        roleid = {'RoleId': user['userrole']}
        enabled = {'Enabled': True}
        for payload in username, pswd, roleid, enabled:
            response = self.send_patch_request(uri, payload, HEADERS)
            if response.status_code == 200:		# success
                result['ret'] = True
            else:
                result = {'ret': False, 'msg': "Error code %s" % response.status_code}
        return result

    def enable_user(self, user):
        result = {}
        uri = self.root_uri + self.accounts_uri + "/" + user['userid']
        payload = {'Enabled': True}
        response = self.send_patch_request(uri, payload, HEADERS)
        if response.status_code == 200:		# success
            result['ret'] = True
        else:
            result = {'ret': False, 'msg': "Error code %s" % response.status_code}
        return result

    def delete_user(self, user):
        result = {}
        uri = self.root_uri + self.accounts_uri + "/" + user['userid']
        payload = {'UserName': ""}
        response = self.send_patch_request(uri, payload, HEADERS)
        if response.status_code == 200:		# success
            result['ret'] = True
        else:
            result = {'ret': False, 'msg': "Error code %s" % response.status_code}
        return result

    def disable_user(self, user):
        result = {}
        uri = self.root_uri + self.accounts_uri + "/" + user['userid']
        payload = {'Enabled': False}
        response = self.send_patch_request(uri, payload, HEADERS)
        if response.status_code == 200:		# success
            result['ret'] = True
        else:
            result = {'ret': False, 'msg': "Error code %s" % response.status_code}
        return result

    def update_user_role(self, user):
        result = {}
        uri = self.root_uri + self.accounts_uri + "/" + user['userid']
        payload = {'RoleId': user['userrole']}
        response = self.send_patch_request(uri, payload, HEADERS)
        if response.status_code == 200:		# success
            result['ret'] = True
        else:
            result = {'ret': False, 'msg': "Error code %s" % response.status_code}
        return result

    def update_user_password(self, user):
        result = {}
        uri = self.root_uri + self.accounts_uri + "/" + user['userid']
        payload = {'Password': user['userpswd']}
        response = self.send_patch_request(uri, payload, HEADERS)
        if response.status_code == 200:		# success
            result['ret'] = True
        else:
            result = {'ret': False, 'msg': "Error code %s" % response.status_code}
        return result

    def get_firmware_inventory(self):
        result = {}
        devices = []
        response = self.send_get_request(self.root_uri + self.firmware_uri)
        if response.status_code == 200:		# success
            result['ret'] = True
            data = response.json()
            for device in data[u'Members']:
                d = device[u'@odata.id']
                d = d.replace(self.firmware_uri, "")    # leave just device name
                if "Installed" in d:
                    # Get details for each device that is relevant
                    uri = self.root_uri + self.firmware_uri + d
                    response = self.send_get_request(uri)
                    if response.status_code == 200:     # success
                        data = response.json()
                        result[data[u'Name']] = data[u'Version']

        # PropertyValueTypeError
        elif response.status_code == 400:
            result = {'ret': False, 'msg': 'Not supported on this platform'}
        else:
            result = {'ret': False, 'msg': "Error code %s" % response.status_code}
        return result

    def get_manager_attributes(self, uri):
        result = {}
        response = self.send_get_request(self.root_uri + self.manager_uri + uri)
        if response.status_code == 200:             # success
            data = response.json()
            for attribute in data[u'Attributes'].items():
                result[attribute[0]] = attribute[1]
            result['ret'] = True
        # PropertyValueTypeError
        elif response.status_code == 400:
            result = {'ret': False, 'msg': 'Not supported on this platform'}
        else:
            result = {'ret': False, 'msg': "Error code %s" % response.status_code}
        return result

    def get_bios_attributes(self, uri):
        result = {}
        response = self.send_get_request(self.root_uri + self.systems_uri + uri)
        if response.status_code == 200:		# success
            data = response.json()
            for attribute in data[u'Attributes'].items():
                result[attribute[0]] = attribute[1]
            result['ret'] = True
        # PropertyValueTypeError
        elif response.status_code == 400:
            result = {'ret': False, 'msg': 'Not supported on this platform'}
        else:
            result = {'ret': False, 'msg': "Error code %s" % response.status_code}
        return result

    def get_bios_boot_order(self, uri1, uri2):
        # Get boot mode first as it will determine what attribute to read
        result = {}
        response = self.send_get_request(self.root_uri + self.systems_uri + uri1)
        if response.status_code == 200:		# success
            result['ret'] = True
            data = response.json()
            boot_mode = data[u'Attributes']["BootMode"]
            response = self.send_get_request(self.root_uri + self.systems_uri + uri2)
            if response.status_code == 200:		# success
                data = response.json()
                if boot_mode == "Uefi":
                    boot_seq = "UefiBootSeq"
                else:
                    boot_seq = "BootSeq"
                boot_devices = data[u'Attributes'][boot_seq]
                for b in boot_devices:
                    result["device%s" % b[u'Index']] = b[u'Name']
        # PropertyValueTypeError
        elif response.status_code == 400:
            result = {'ret': False, 'msg': 'Not supported on this platform'}
        else:
            result = {'ret': False, 'msg': "Error code %s" % response.status_code}
        return result

    def get_fan_inventory(self, uri):
        result = {}
        fan_details = []
        response = self.send_get_request(self.root_uri + self.chassis_uri + uri)
        if response.status_code == 200:             # success
            result['ret'] = True
            data = response.json()
            for device in data[u'Fans']:
                # There is more information available but this is most important
                fan = {}
                fan['Name'] = device[u'FanName']
                fan['RPMs'] = device[u'Reading']
                fan['State'] = device[u'Status'][u'State']
                fan['Health'] = device[u'Status'][u'Health']
                fan_details.append(fan)
            result["entries"] = fan_details

        elif response.status_code == 400:
            result = {'ret': False, 'msg': 'Not supported on this platform'}
        else:
            result = {'ret': False, 'msg': "Error code %s" % response.status_code}
        return result

    def set_bios_default_settings(self, uri):
        result = {}
        payload = {}
        response = self.send_post_request(self.root_uri + self.systems_uri + uri, payload, HEADERS)
        if response.status_code == 200:		# success
            result = {'ret': True, 'msg': 'SetBiosDefaultSettings completed'}
        elif response.status_code == 405:
            result = {'ret': False, 'msg': "Resource not supported"}
        else:
            result = {'ret': False, 'msg': "Error code %s" % response.status_code}
        return result

    def set_one_time_boot_device(self, bootdevice, uri):
        result = {}
        response = self.send_get_request(self.root_uri + self.systems_uri + uri)
        if response.status_code == 200:		# success
            data = response.json()
            boot_mode = data[u'Attributes']["BootMode"]
            if boot_mode == "Uefi":
                payload = {"Boot": {"BootSourceOverrideTarget": "UefiTarget", "UefiTargetBootSourceOverride": bootdevice}}
            else:
                payload = {"Boot": {"BootSourceOverrideTarget": bootdevice}}
        else:
            result = {'ret': False, 'msg': "Error code %s" % response.status_code}
            return result

        response = self.send_patch_request(self.root_uri + self.systems_uri, payload, HEADERS)
        if response.status_code == 200:		# success
            result = {'ret': True, 'msg': 'SetOneTimeBoot completed'}
        else:
            result = {'ret': False, 'msg': "Error code %s" % response.status_code}
        return result

    def set_manager_attributes(self, uri, attributes):
        result = {}
        # Example: manager_attributes = {\"name\":\"value\"}
        # Check if value is a number. If so, convert to int.
        if attributes['mgr_attr_value'].isdigit():
            manager_attributes = '{{ "{}": {} }}'.format(attributes['mgr_attr_name'], int(attributes['mgr_attr_value']))
        else:
            manager_attributes = '{{ "{}": "{}" }}'.format(attributes['mgr_attr_name'], attributes['mgr_attr_value'])

        payload = {"Attributes": json.loads(manager_attributes)}
        response = self.send_patch_request(self.root_uri + self.manager_uri + uri, payload, HEADERS)
        if response.status_code == 200:
            result = {'ret': True, 'msg': 'Manager attributes set as pending values'}
        elif response.status_code == 405:
            result = {'ret': False, 'msg': "Resource not supported"}
        else:
            pp = response.json()
            result = {'ret': False, 'msg': "Error code %s" % str(pp)}
        return result

    def set_bios_attributes(self, uri, attributes):
        result = {}
        # Example: bios_attributes = {\"name\":\"value\"}
        bios_attributes = "{\"" + attributes['bios_attr_name'] + "\":\"" + attributes['bios_attr_value'] + "\"}"
        payload = {"Attributes": json.loads(bios_attributes)}
        response = self.send_patch_request(self.root_uri + self.systems_uri + uri, payload, HEADERS)
        if response.status_code == 200:
            result = {'ret': True, 'msg': 'BIOS Attributes set as pending values'}
        elif response.status_code == 400:
            result = {'ret': False, 'msg': 'Not supported on this platform'}
        elif response.status_code == 405:
            result = {'ret': False, 'msg': "Resource not supported"}
        else:
            result = {'ret': False, 'msg': "Error code %s" % str(response.status_code)}
        return result

    def create_bios_config_job(self, uri1, uri2):
        payload = {"TargetSettingsURI": self.systems_uri + uri1, "RebootJobType": "PowerCycle"}
        response = self.send_post_request(self.root_uri + self.manager_uri + uri2, payload, HEADERS)
        if response.status_code == 200:
            convert_to_string = str(response.__dict__)
            jobid_search = re.search("JID_.+?,", convert_to_string).group()
            job_id = re.sub("[,']", "", jobid_search)

            result = {'ret': True, 'msg': 'Config job created', 'job_id': job_id}
        elif response.status_code == 400:
            result = {'ret': False, 'msg': 'Not supported on this platform'}
        elif response.status_code == 405:
            result = {'ret': False, 'msg': "Resource not supported"}
        else:
            result = {'ret': False, 'msg': "Error code %s" % str(response.status_code)}
        return result

    def get_cpu_inventory(self, uri):
        result = {}
        cpu_details = []

        # Get a list of all CPUs and build respective URIs
        cpu_list = []
        response = self.send_get_request(self.root_uri + self.systems_uri + uri)
        if response.status_code == 200:		# success
            result['ret'] = True
            data = response.json()

            for cpu in data[u'Members']:
                cpu_list.append(cpu[u'@odata.id'])
            for c in cpu_list:
                uri = self.root_uri + c
                response = self.send_get_request(uri)
                if response.status_code == 200:             # success
                    data = response.json()
                    cpu = {}
                    cpu['Name'] = data[u'Id']
                    cpu['Manufacturer'] = data[u'Manufacturer']
                    cpu['Model'] = data[u'Model']
                    cpu['MaxSpeedMHz'] = data[u'MaxSpeedMHz']
                    cpu['TotalCores'] = data[u'TotalCores']
                    cpu['TotalThreads'] = data[u'TotalThreads']
                    cpu['State'] = data[u'Status'][u'State']
                    cpu['Health'] = data[u'Status'][u'Health']
                    cpu_details.append(cpu)

                else:
                    result = {'ret': False, 'msg': "Error code %s" % response.status_code}
                    return result           # no need to go through the whole loop

            result["entries"] = cpu_details
        else:
            result = {'ret': False, 'msg': "Error code %s" % response.status_code}
        return result

    def get_nic_inventory(self, uri):
        result = {}
        nic_details = []

        # Get a list of all network controllers and build respective URIs
        nic_list = []
        response = self.send_get_request(self.root_uri + self.systems_uri + uri)
        if response.status_code == 200:		# success
            result['ret'] = True
            data = response.json()

            for nic in data[u'Members']:
                nic_list.append(nic[u'@odata.id'])

            for n in nic_list:
                uri = self.root_uri + n
                response = self.send_get_request(uri)
                if response.status_code == 200:             # success
                    data = response.json()
                    nic = {}
                    nic['Name'] = data[u'Name']
                    nic['FQDN'] = data[u'FQDN']
                    for d in data[u'IPv4Addresses']:
                        nic['IPv4'] = d[u'Address']
                        nic['Gateway'] = d[u'GateWay']
                        nic['SubnetMask'] = d[u'SubnetMask']
                    for d in data[u'IPv6Addresses']:
                        nic['IPv6'] = d[u'Address']
                    for d in data[u'NameServers']:
                        nic['NameServers'] = d
                    nic['MACAddress'] = data[u'PermanentMACAddress']
                    nic['SpeedMbps'] = data[u'SpeedMbps']
                    nic['MTU'] = data[u'MTUSize']
                    nic['AutoNeg'] = data[u'AutoNeg']
                    if 'Status' in data:    # not available when power is off
                        nic['Health'] = data[u'Status'][u'Health']
                        nic['State'] = data[u'Status'][u'State']
                    nic_details.append(nic)
                else:
                    result = {'ret': False, 'msg': "Error code %s" % response.status_code}
                    return result           # no need to go through the whole loop

            result["entries"] = nic_details
        else:
            result = {'ret': False, 'msg': "Error code %s" % response.status_code}
        return result

    def get_psu_inventory(self):
        result = {}
        psu_details = []

        # Get a list of all PSUs and build respective URIs
        psu_list = []
        response = self.send_get_request(self.root_uri + self.systems_uri)
        if response.status_code == 200:		# success
            result['ret'] = True
            data = response.json()

            for psu in data[u'Links'][u'PoweredBy']:
                psu_list.append(psu[u'@odata.id'])

            for p in psu_list:
                uri = self.root_uri + p
                response = self.send_get_request(uri)
                if response.status_code == 200:             # success
                    data = response.json()
                    psu = {}
                    psu['Name'] = data[u'Name']
                    psu['Model'] = data[u'Model']
                    psu['SerialNumber'] = data[u'SerialNumber']
                    psu['PartNumber'] = data[u'PartNumber']
                    if 'Manufacturer' in data:   # not available in all generations
                        psu['Manufacturer'] = data[u'Manufacturer']
                    psu['FirmwareVersion'] = data[u'FirmwareVersion']
                    psu['PowerCapacityWatts'] = data[u'PowerCapacityWatts']
                    psu['PowerSupplyType'] = data[u'PowerSupplyType']
                    psu['Status'] = data[u'Status'][u'State']
                    psu['Health'] = data[u'Status'][u'Health']
                    psu_details.append(psu)
                else:
                    result = {'ret': False, 'msg': "Error code %s" % response.status_code}
                    return result           # no need to go through the whole loop
            result["entries"] = psu_details
        else:
            result = {'ret': False, 'msg': "Error code %s" % response.status_code}
        return result

    def get_system_inventory(self):
        result = {}
        response = self.send_get_request(self.root_uri + self.systems_uri)
        if response.status_code == 200:		# success
            result['ret'] = True
            data = response.json()

            # There could be more information to extract
            result['Status'] = data[u'Status'][u'Health']
            result['HostName'] = data[u'HostName']
            result['PowerState'] = data[u'PowerState']
            result['Model'] = data[u'Model']
            result['Manufacturer'] = data[u'Manufacturer']
            result['PartNumber'] = data[u'PartNumber']
            result['SystemType'] = data[u'SystemType']
            result['AssetTag'] = data[u'AssetTag']
            result['ServiceTag'] = data[u'SKU']
            result['SerialNumber'] = data[u'SerialNumber']
            result['BiosVersion'] = data[u'BiosVersion']
            result['MemoryTotal'] = data[u'MemorySummary'][u'TotalSystemMemoryGiB']
            result['MemoryHealth'] = data[u'MemorySummary'][u'Status'][u'Health']
            result['CpuCount'] = data[u'ProcessorSummary'][u'Count']
            result['CpuModel'] = data[u'ProcessorSummary'][u'Model']
            result['CpuHealth'] = data[u'ProcessorSummary'][u'Status'][u'Health']

            datadict = data[u'Boot']
            if 'BootSourceOverrideMode' in datadict.keys():
                result['BootSourceOverrideMode'] = data[u'Boot'][u'BootSourceOverrideMode']
            else:
                # Not available in earlier server generations
                result['BootSourceOverrideMode'] = "Not available"

            if 'TrustedModules' in data:
                for d in data[u'TrustedModules']:
                    if 'InterfaceType' in d.keys():
                        result['TPMInterfaceType'] = d[u'InterfaceType']
                    result['TPMStatus'] = d[u'Status'][u'State']
            else:
                # Not available in earlier server generations
                result['TPMInterfaceType'] = "Not available"
                result['TPMStatus'] = "Not available"
        else:
            result = {'ret': False, 'msg': "Error code %s" % response.status_code}
        return result
