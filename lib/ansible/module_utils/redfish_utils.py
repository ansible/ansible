# Copyright (c) 2017-2018 Dell EMC Inc.
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import re
from ansible.module_utils.urls import open_url
from ansible.module_utils.six.moves.urllib.error import URLError, HTTPError

HEADERS = {'content-type': 'application/json'}


class RedfishUtils(object):

    def __init__(self, creds, root_uri):
        self.root_uri = root_uri
        self.creds = creds
        self._init_session()
        return

    # The following functions are to send GET/POST/PATCH/DELETE requests
    def get_request(self, uri):
        try:
            resp = open_url(uri, method="GET",
                            url_username=self.creds['user'],
                            url_password=self.creds['pswd'],
                            force_basic_auth=True, validate_certs=False,
                            timeout=10, use_proxy=False)
            data = json.loads(resp.read())
        except HTTPError as e:
            return {'ret': False, 'msg': "HTTP Error: %s" % e.code}
        except URLError as e:
            return {'ret': False, 'msg': "URL Error: %s" % e.reason}
        # Almost all errors should be caught above, but just in case
        except:
            return {'ret': False, 'msg': "Unknown error"}
        return {'ret': True, 'data': data}

    def post_request(self, uri, pyld, hdrs):
        try:
            resp = open_url(uri, data=json.dumps(pyld),
                            headers=hdrs, method="POST",
                            url_username=self.creds['user'],
                            url_password=self.creds['pswd'],
                            force_basic_auth=True, validate_certs=False,
                            use_proxy=False)
        except HTTPError as e:
            return {'ret': False, 'msg': "HTTP Error: %s" % e.code}
        except URLError as e:
            return {'ret': False, 'msg': "URL Error: %s" % e.reason}
        # Almost all errors should be caught above, but just in case
        except:
            return {'ret': False, 'msg': "Unknown error"}
        return {'ret': True, 'resp': resp}

    def patch_request(self, uri, pyld, hdrs):
        try:
            resp = open_url(uri, data=json.dumps(pyld),
                            headers=hdrs, method="PATCH",
                            url_username=self.creds['user'],
                            url_password=self.creds['pswd'],
                            force_basic_auth=True, validate_certs=False,
                            use_proxy=False)
        except HTTPError as e:
            return {'ret': False, 'msg': "HTTP Error: %s" % e.code}
        except URLError as e:
            return {'ret': False, 'msg': "URL Error: %s" % e.reason}
        # Almost all errors should be caught above, but just in case
        except:
            return {'ret': False, 'msg': "Unknown error"}
        return {'ret': True, 'resp': resp}

    def delete_request(self, uri, pyld, hdrs):
        try:
            resp = open_url(uri, data=json.dumps(pyld),
                            headers=hdrs, method="DELETE",
                            url_username=self.creds['user'],
                            url_password=self.creds['pswd'],
                            force_basic_auth=True, validate_certs=False,
                            use_proxy=False)
        except HTTPError as e:
            return {'ret': False, 'msg': "HTTP Error: %s" % e.code}
        except URLError as e:
            return {'ret': False, 'msg': "URL Error: %s" % e.reason}
        # Almost all errors should be caught above, but just in case
        except:
            return {'ret': False, 'msg': "Unknown error"}
        return {'ret': True, 'resp': resp}

    def _init_session(self):
        pass

    def _find_accountservice_resource(self, uri):
        response = self.get_request(self.root_uri + uri)
        if response['ret'] is False:
            return response
        data = response['data']
        if 'AccountService' not in data:
            return {'ret': False, 'msg': "AccountService resource not found"}
        else:
            account_service = data["AccountService"]["@odata.id"]
            response = self.get_request(self.root_uri + account_service)
            if response['ret'] is False:
                return response
            data = response['data']
            accounts = data['Accounts']['@odata.id']
            if accounts[-1:] == '/':
                accounts = accounts[:-1]
            self.accounts_uri = accounts
        return {'ret': True}

    def _find_systems_resource(self, uri):
        response = self.get_request(self.root_uri + uri)
        if response['ret'] is False:
            return response
        data = response['data']
        if 'Systems' not in data:
            return {'ret': False, 'msg': "Systems resource not found"}
        else:
            systems = data["Systems"]["@odata.id"]
            response = self.get_request(self.root_uri + systems)
            if response['ret'] is False:
                return response
            data = response['data']
            for member in data[u'Members']:
                systems_service = member[u'@odata.id']
            self.systems_uri = systems_service
            return {'ret': True}

    def _find_updateservice_resource(self, uri):
        response = self.get_request(self.root_uri + uri)
        if response['ret'] is False:
            return response
        data = response['data']
        if 'UpdateService' not in data:
            return {'ret': False, 'msg': "UpdateService resource not found"}
        else:
            update = data["UpdateService"]["@odata.id"]
            self.update_uri = update
            response = self.get_request(self.root_uri + update)
            if response['ret'] is False:
                return response
            data = response['data']
            firmware_inventory = data['FirmwareInventory'][u'@odata.id']
            self.firmware_uri = firmware_inventory
            return {'ret': True}

    def _find_chassis_resource(self, uri):
        chassis_service = []
        response = self.get_request(self.root_uri + uri)
        if response['ret'] is False:
            return response
        data = response['data']
        if 'Chassis' not in data:
            return {'ret': False, 'msg': "Chassis resource not found"}
        else:
            chassis = data["Chassis"]["@odata.id"]
            response = self.get_request(self.root_uri + chassis)
            if response['ret'] is False:
                return response
            data = response['data']
            for member in data[u'Members']:
                chassis_service.append(member[u'@odata.id'])
            self.chassis_uri_list = chassis_service
            return {'ret': True}

    def _find_managers_resource(self, uri):
        response = self.get_request(self.root_uri + uri)
        if response['ret'] is False:
            return response
        data = response['data']
        if 'Managers' not in data:
            return {'ret': False, 'msg': "Manager resource not found"}
        else:
            manager = data["Managers"]["@odata.id"]
            response = self.get_request(self.root_uri + manager)
            if response['ret'] is False:
                return response
            data = response['data']
            for member in data[u'Members']:
                manager_service = member[u'@odata.id']
            self.manager_uri = manager_service
            return {'ret': True}

    def get_logs(self):
        log_svcs_uri_list = []
        list_of_logs = []

        # Find LogService
        response = self.get_request(self.root_uri + self.manager_uri)
        if response['ret'] is False:
            return response
        data = response['data']
        if 'LogServices' not in data:
            return {'ret': False, 'msg': "LogServices resource not found"}

        # Find all entries in LogServices
        logs_uri = data["LogServices"]["@odata.id"]
        response = self.get_request(self.root_uri + logs_uri)
        if response['ret'] is False:
            return response
        data = response['data']
        for log_svcs_entry in data[u'Members']:
            response = self.get_request(self.root_uri + log_svcs_entry[u'@odata.id'])
            if response['ret'] is False:
                return response
            _data = response['data']
            log_svcs_uri_list.append(_data['Entries'][u'@odata.id'])

        # For each entry in LogServices, get log name and all log entries
        for log_svcs_uri in log_svcs_uri_list:
            logs = {}
            list_of_log_entries = []
            response = self.get_request(self.root_uri + log_svcs_uri)
            if response['ret'] is False:
                return response
            data = response['data']
            logs['Description'] = data['Description']
            # Get all log entries for each type of log found
            for logEntry in data[u'Members']:
                # I only extract some fields - Are these entry names standard?
                list_of_log_entries.append(dict(
                    Name=logEntry[u'Name'],
                    Created=logEntry[u'Created'],
                    Message=logEntry[u'Message'],
                    Severity=logEntry[u'Severity']))
            log_name = log_svcs_uri.split('/')[-1]
            logs[log_name] = list_of_log_entries
            list_of_logs.append(logs)

        # list_of_logs[logs{list_of_log_entries[entry{}]}]
        return {'ret': True, 'entries': list_of_logs}

    def clear_logs(self):
        # Find LogService
        response = self.get_request(self.root_uri + self.manager_uri)
        if response['ret'] is False:
            return response
        data = response['data']
        if 'LogServices' not in data:
            return {'ret': False, 'msg': "LogServices resource not found"}

        # Find all entries in LogServices
        logs_uri = data["LogServices"]["@odata.id"]
        response = self.get_request(self.root_uri + logs_uri)
        if response['ret'] is False:
            return response
        data = response['data']

        for log_svcs_entry in data[u'Members']:
            response = self.get_request(self.root_uri + log_svcs_entry["@odata.id"])
            if response['ret'] is False:
                return response
            _data = response['data']
            # Check to make sure option is available, otherwise error is ugly
            if "Actions" in _data:
                if "#LogService.ClearLog" in _data[u"Actions"]:
                    self.post_request(self.root_uri + _data[u"Actions"]["#LogService.ClearLog"]["target"], {}, HEADERS)
                    if response['ret'] is False:
                        return response
        return {'ret': True}

    def get_storage_controller_inventory(self):
        result = {}
        controllers_details = []
        controller_list = []

        # Find Storage service
        response = self.get_request(self.root_uri + self.systems_uri)
        if response['ret'] is False:
            return response
        data = response['data']

        if 'SimpleStorage' not in data:
            return {'ret': False, 'msg': "SimpleStorage resource not found"}

        # Get a list of all storage controllers and build respective URIs
        storage_uri = data["SimpleStorage"]["@odata.id"]
        response = self.get_request(self.root_uri + storage_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        for controller in data[u'Members']:
            controller_list.append(controller[u'@odata.id'])

        for c in controller_list:
            uri = self.root_uri + c
            response = self.get_request(uri)
            if response['ret'] is False:
                return response
            data = response['data']
            controllers_details.append(dict(
                Name=data[u'Name'],
                Health=data[u'Status'][u'Health']))
        result["entries"] = controllers_details
        return result

    def get_disk_inventory(self):
        result = {}
        disks_details = []
        controller_list = []

        # Find Storage service
        response = self.get_request(self.root_uri + self.systems_uri)
        if response['ret'] is False:
            return response
        data = response['data']

        if 'SimpleStorage' not in data:
            return {'ret': False, 'msg': "SimpleStorage resource not found"}

        # Get a list of all storage controllers and build respective URIs
        storage_uri = data["SimpleStorage"]["@odata.id"]
        response = self.get_request(self.root_uri + storage_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        for controller in data[u'Members']:
            controller_list.append(controller[u'@odata.id'])

        for c in controller_list:
            uri = self.root_uri + c
            response = self.get_request(uri)
            if response['ret'] is False:
                return response
            data = response['data']

            for device in data[u'Devices']:
                disks_details.append(dict(
                    Controller=data[u'Name'],
                    Name=device[u'Name'],
                    Manufacturer=device[u'Manufacturer'],
                    Model=device[u'Model'],
                    State=device[u'Status'][u'State'],
                    Health=device[u'Status'][u'Health']))
        result["entries"] = disks_details
        return result

    def restart_manager_gracefully(self):
        result = {}
        key = "Actions"

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + self.manager_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']
        action_uri = data[key]["#Manager.Reset"]["target"]

        payload = {'ResetType': 'GracefulRestart'}
        response = self.post_request(self.root_uri + action_uri, payload, HEADERS)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def manage_system_power(self, command):
        result = {}
        key = "Actions"

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + self.systems_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']
        action_uri = data[key]["#ComputerSystem.Reset"]["target"]

        # Define payload accordingly
        if command == "PowerOn":
            payload = {'ResetType': 'On'}
        elif command == "PowerForceOff":
            payload = {'ResetType': 'ForceOff'}
        elif command == "PowerGracefulRestart":
            payload = {'ResetType': 'GracefulRestart'}
        elif command == "PowerGracefulShutdown":
            payload = {'ResetType': 'GracefulShutdown'}
        else:
            return {'ret': False, 'msg': 'Invalid Command'}

        response = self.post_request(self.root_uri + action_uri, payload, HEADERS)
        if response['ret'] is False:
            return response
        result['ret'] = True
        return result

    def list_users(self):
        result = {}
        # listing all users has always been slower than other operations, why?
        allusers = []
        allusers_details = []
        response = self.get_request(self.root_uri + self.accounts_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        for users in data[u'Members']:
            allusers.append(users[u'@odata.id'])   # allusers[] are URIs

        # for each user, get details
        for uri in allusers:
            response = self.get_request(self.root_uri + uri)
            if response['ret'] is False:
                return response
            data = response['data']

            if not data[u'UserName'] == "":        # only care if name is not empty
                allusers_details.append(dict(
                    Id=data[u'Id'],
                    Name=data[u'Name'],
                    UserName=data[u'UserName'],
                    RoleId=data[u'RoleId']))
        result["entries"] = allusers_details
        return result

    def add_user(self, user):
        uri = self.root_uri + self.accounts_uri + "/" + user['userid']
        username = {'UserName': user['username']}
        pswd = {'Password': user['userpswd']}
        roleid = {'RoleId': user['userrole']}
        enabled = {'Enabled': True}
        for payload in username, pswd, roleid, enabled:
            response = self.patch_request(uri, payload, HEADERS)
            if response['ret'] is False:
                return response
        return {'ret': True}

    def enable_user(self, user):
        uri = self.root_uri + self.accounts_uri + "/" + user['userid']
        payload = {'Enabled': True}
        response = self.patch_request(uri, payload, HEADERS)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def delete_user(self, user):
        uri = self.root_uri + self.accounts_uri + "/" + user['userid']
        payload = {'UserName': ""}
        response = self.patch_request(uri, payload, HEADERS)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def disable_user(self, user):
        uri = self.root_uri + self.accounts_uri + "/" + user['userid']
        payload = {'Enabled': False}
        response = self.patch_request(uri, payload, HEADERS)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def update_user_role(self, user):
        uri = self.root_uri + self.accounts_uri + "/" + user['userid']
        payload = {'RoleId': user['userrole']}
        response = self.patch_request(uri, payload, HEADERS)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def update_user_password(self, user):
        uri = self.root_uri + self.accounts_uri + "/" + user['userid']
        payload = {'Password': user['userpswd']}
        response = self.patch_request(uri, payload, HEADERS)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def get_firmware_inventory(self):
        result = {}
        firmware = {}
        response = self.get_request(self.root_uri + self.firmware_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        for device in data[u'Members']:
            d = device[u'@odata.id']
            d = d.replace(self.firmware_uri, "")    # leave just device name
            if "Installed" in d:
                uri = self.root_uri + self.firmware_uri + d
                # Get details for each device that is relevant
                response = self.get_request(uri)
                if response['ret'] is False:
                    return response
                result['ret'] = True
                data = response['data']
                firmware[data[u'Name']] = data[u'Version']
        result["entries"] = firmware
        return result

    def get_manager_attributes(self):
        result = {}
        manager_attributes = {}
        attributes_id = "Attributes"

        response = self.get_request(self.root_uri + self.manager_uri + "/" + attributes_id)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']
        for attribute in data[u'Attributes'].items():
            manager_attributes[attribute[0]] = attribute[1]
        result["entries"] = manager_attributes
        return result

    def get_bios_attributes(self):
        result = {}
        bios_attributes = {}
        key = "Bios"

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + self.systems_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']
        bios_uri = data[key]["@odata.id"]

        response = self.get_request(self.root_uri + bios_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']
        for attribute in data[u'Attributes'].items():
            bios_attributes[attribute[0]] = attribute[1]
        result["entries"] = bios_attributes
        return result

    def get_bios_boot_order(self):
        result = {}
        boot_device_list = []
        boot_device_details = []
        key = "Bios"
        bootsources = "BootSources"

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + self.systems_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']
        bios_uri = data[key]["@odata.id"]

        # Get boot mode first as it will determine what attribute to read
        response = self.get_request(self.root_uri + bios_uri)
        if response['ret'] is False:
            return response
        data = response['data']
        boot_mode = data[u'Attributes']["BootMode"]
        if boot_mode == "Uefi":
            boot_seq = "UefiBootSeq"
        else:
            boot_seq = "BootSeq"

        response = self.get_request(self.root_uri + self.systems_uri + "/" + bootsources)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        boot_device_list = data[u'Attributes'][boot_seq]
        for b in boot_device_list:
            boot_device = {}
            boot_device["Index"] = b[u'Index']
            boot_device["Name"] = b[u'Name']
            boot_device["Enabled"] = b[u'Enabled']
            boot_device_details.append(boot_device)
        result["entries"] = boot_device_details
        return result

    def set_bios_default_settings(self):
        result = {}
        key = "Bios"

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + self.systems_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']
        bios_uri = data[key]["@odata.id"]

        # Extract proper URI
        response = self.get_request(self.root_uri + bios_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']
        reset_bios_settings_uri = data["Actions"]["#Bios.ResetBios"]["target"]

        response = self.post_request(self.root_uri + reset_bios_settings_uri, {}, HEADERS)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def set_one_time_boot_device(self, bootdevice):
        result = {}
        key = "Bios"

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + self.systems_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']
        bios_uri = data[key]["@odata.id"]

        response = self.get_request(self.root_uri + bios_uri)
        if response['ret'] is False:
            return response
        data = response['data']

        boot_mode = data[u'Attributes']["BootMode"]
        if boot_mode == "Uefi":
            payload = {"Boot": {"BootSourceOverrideTarget": "UefiTarget", "UefiTargetBootSourceOverride": bootdevice}}
        else:
            payload = {"Boot": {"BootSourceOverrideTarget": bootdevice}}

        response = self.patch_request(self.root_uri + self.systems_uri, payload, HEADERS)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def set_manager_attributes(self, attr):
        attributes = "Attributes"

        # Example: manager_attr = {\"name\":\"value\"}
        # Check if value is a number. If so, convert to int.
        if attr['mgr_attr_value'].isdigit():
            manager_attr = "{\"%s\": %i}" % (attr['mgr_attr_name'], int(attr['mgr_attr_value']))
        else:
            manager_attr = "{\"%s\": \"%s\"}" % (attr['mgr_attr_name'], attr['mgr_attr_value'])

        payload = {"Attributes": json.loads(manager_attr)}
        response = self.patch_request(self.root_uri + self.manager_uri + "/" + attributes, payload, HEADERS)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def set_bios_attributes(self, attr):
        result = {}
        key = "Bios"

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + self.systems_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']
        bios_uri = data[key]["@odata.id"]

        # Extract proper URI
        response = self.get_request(self.root_uri + bios_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']
        set_bios_attr_uri = data["@Redfish.Settings"]["SettingsObject"]["@odata.id"]

        # Example: bios_attr = {\"name\":\"value\"}
        bios_attr = "{\"" + attr['bios_attr_name'] + "\":\"" + attr['bios_attr_value'] + "\"}"
        payload = {"Attributes": json.loads(bios_attr)}
        response = self.patch_request(self.root_uri + set_bios_attr_uri, payload, HEADERS)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def create_bios_config_job(self):
        result = {}
        key = "Bios"
        jobs = "Jobs"

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + self.systems_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']
        bios_uri = data[key]["@odata.id"]

        # Extract proper URI
        response = self.get_request(self.root_uri + bios_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']
        set_bios_attr_uri = data["@Redfish.Settings"]["SettingsObject"]["@odata.id"]

        payload = {"TargetSettingsURI": set_bios_attr_uri, "RebootJobType": "PowerCycle"}
        response = self.post_request(self.root_uri + self.manager_uri + "/" + jobs, payload, HEADERS)
        if response['ret'] is False:
            return response

        response_output = response['resp'].__dict__
        job_id = response_output["headers"]["Location"]
        job_id = re.search("JID_.+", job_id).group()
        return {'ret': True, 'msg': 'Config job created', 'job_id': job_id}

    def get_fan_inventory(self):
        result = {}
        fan_details = []
        key = "Thermal"

        # Go through list
        for chassis_uri in self.chassis_uri_list:
            response = self.get_request(self.root_uri + chassis_uri)
            if response['ret'] is False:
                return response
            result['ret'] = True
            data = response['data']
            if key in data:
                # match: found an entry for "Thermal" information = fans
                thermal_uri = data[key]["@odata.id"]
                response = self.get_request(self.root_uri + thermal_uri)
                if response['ret'] is False:
                    return response
                result['ret'] = True
                data = response['data']

                for device in data[u'Fans']:
                    fan_details.append(dict(
                        # There is more information available but this is most important
                        Name=device[u'FanName'],
                        RPMs=device[u'Reading'],
                        State=device[u'Status'][u'State'],
                        Health=device[u'Status'][u'Health']))
                result["entries"] = fan_details
        return result

    def get_cpu_inventory(self):
        result = {}
        cpu_details = []
        cpu_list = []
        key = "Processors"

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + self.systems_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        processors_uri = data[key]["@odata.id"]

        # Get a list of all CPUs and build respective URIs
        response = self.get_request(self.root_uri + processors_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        for cpu in data[u'Members']:
            cpu_list.append(cpu[u'@odata.id'])
        for c in cpu_list:
            uri = self.root_uri + c
            response = self.get_request(uri)
            if response['ret'] is False:
                return response
            data = response['data']
            cpu_details.append(dict(
                Name=data[u'Id'],
                Manufacturer=data[u'Manufacturer'],
                Model=data[u'Model'],
                MaxSpeedMHz=data[u'MaxSpeedMHz'],
                TotalCores=data[u'TotalCores'],
                TotalThreads=data[u'TotalThreads'],
                State=data[u'Status'][u'State'],
                Health=data[u'Status'][u'Health']))
        result["entries"] = cpu_details
        return result

    def get_nic_inventory(self):
        result = {}
        nic_details = []
        nic_list = []
        key = "EthernetInterfaces"

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + self.systems_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        ethernetinterfaces_uri = data[key]["@odata.id"]

        # Get a list of all network controllers and build respective URIs
        response = self.get_request(self.root_uri + ethernetinterfaces_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        for nic in data[u'Members']:
            nic_list.append(nic[u'@odata.id'])

        for n in nic_list:
            nic = {}
            uri = self.root_uri + n
            response = self.get_request(uri)
            if response['ret'] is False:
                return response
            data = response['data']

            nic['Name'] = data[u'Name']
            nic['FQDN'] = data[u'FQDN']
            for d in data[u'IPv4Addresses']:
                nic['IPv4'] = d[u'Address']
                if 'GateWay' in d:   # not always available
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
        result["entries"] = nic_details
        return result

    def get_psu_inventory(self):
        result = {}
        psu_details = []
        psu_list = []

        # Get a list of all PSUs and build respective URIs
        response = self.get_request(self.root_uri + self.systems_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        for psu in data[u'Links'][u'PoweredBy']:
            psu_list.append(psu[u'@odata.id'])

        for p in psu_list:
            uri = self.root_uri + p
            response = self.get_request(uri)
            if response['ret'] is False:
                return response

            result['ret'] = True
            data = response['data']

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
        result["entries"] = psu_details
        return result

    def get_system_inventory(self):
        result = {}
        inventory = {}
        response = self.get_request(self.root_uri + self.systems_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        # There could be more information to extract
        inventory['Status'] = data[u'Status'][u'Health']
        inventory['HostName'] = data[u'HostName']
        inventory['PowerState'] = data[u'PowerState']
        inventory['Model'] = data[u'Model']
        inventory['Manufacturer'] = data[u'Manufacturer']
        inventory['PartNumber'] = data[u'PartNumber']
        inventory['SystemType'] = data[u'SystemType']
        inventory['AssetTag'] = data[u'AssetTag']
        inventory['ServiceTag'] = data[u'SKU']
        inventory['SerialNumber'] = data[u'SerialNumber']
        inventory['BiosVersion'] = data[u'BiosVersion']
        inventory['MemoryTotal'] = data[u'MemorySummary'][u'TotalSystemMemoryGiB']
        inventory['MemoryHealth'] = data[u'MemorySummary'][u'Status'][u'Health']
        inventory['CpuCount'] = data[u'ProcessorSummary'][u'Count']
        inventory['CpuModel'] = data[u'ProcessorSummary'][u'Model']
        inventory['CpuHealth'] = data[u'ProcessorSummary'][u'Status'][u'Health']

        datadict = data[u'Boot']
        if 'BootSourceOverrideMode' in datadict.keys():
            inventory['BootSourceOverrideMode'] = data[u'Boot'][u'BootSourceOverrideMode']
        else:
            # Not available in earlier server generations
            inventory['BootSourceOverrideMode'] = "Not available"

        if 'TrustedModules' in data:
            for d in data[u'TrustedModules']:
                if 'InterfaceType' in d.keys():
                    inventory['TPMInterfaceType'] = d[u'InterfaceType']
                inventory['TPMStatus'] = d[u'Status'][u'State']
        else:
            # Not available in earlier server generations
            inventory['TPMInterfaceType'] = "Not available"
            inventory['TPMStatus'] = "Not available"

        result["entries"] = inventory
        return result
