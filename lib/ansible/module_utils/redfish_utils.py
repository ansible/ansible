# Copyright (c) 2017-2018 Dell EMC Inc.
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
from ansible.module_utils.urls import open_url
from ansible.module_utils._text import to_text
from ansible.module_utils.six.moves import http_client
from ansible.module_utils.six.moves.urllib.error import URLError, HTTPError

GET_HEADERS = {'accept': 'application/json', 'OData-Version': '4.0'}
POST_HEADERS = {'content-type': 'application/json', 'accept': 'application/json',
                'OData-Version': '4.0'}
PATCH_HEADERS = {'content-type': 'application/json', 'accept': 'application/json',
                 'OData-Version': '4.0'}
DELETE_HEADERS = {'accept': 'application/json', 'OData-Version': '4.0'}


class RedfishUtils(object):

    def __init__(self, creds, root_uri, timeout):
        self.root_uri = root_uri
        self.creds = creds
        self.timeout = timeout
        self._init_session()
        return

    # The following functions are to send GET/POST/PATCH/DELETE requests
    def get_request(self, uri):
        try:
            resp = open_url(uri, method="GET", headers=GET_HEADERS,
                            url_username=self.creds['user'],
                            url_password=self.creds['pswd'],
                            force_basic_auth=True, validate_certs=False,
                            follow_redirects='all',
                            use_proxy=False, timeout=self.timeout)
            data = json.loads(resp.read())
        except HTTPError as e:
            msg = self._get_extended_message(e)
            return {'ret': False,
                    'msg': "HTTP Error %s on GET request to '%s', extended message: '%s'"
                           % (e.code, uri, msg)}
        except URLError as e:
            return {'ret': False, 'msg': "URL Error on GET request to '%s': '%s'"
                                         % (uri, e.reason)}
        # Almost all errors should be caught above, but just in case
        except Exception as e:
            return {'ret': False,
                    'msg': "Failed GET request to '%s': '%s'" % (uri, to_text(e))}
        return {'ret': True, 'data': data}

    def post_request(self, uri, pyld):
        try:
            resp = open_url(uri, data=json.dumps(pyld),
                            headers=POST_HEADERS, method="POST",
                            url_username=self.creds['user'],
                            url_password=self.creds['pswd'],
                            force_basic_auth=True, validate_certs=False,
                            follow_redirects='all',
                            use_proxy=False, timeout=self.timeout)
        except HTTPError as e:
            msg = self._get_extended_message(e)
            return {'ret': False,
                    'msg': "HTTP Error %s on POST request to '%s', extended message: '%s'"
                           % (e.code, uri, msg)}
        except URLError as e:
            return {'ret': False, 'msg': "URL Error on POST request to '%s': '%s'"
                                         % (uri, e.reason)}
        # Almost all errors should be caught above, but just in case
        except Exception as e:
            return {'ret': False,
                    'msg': "Failed POST request to '%s': '%s'" % (uri, to_text(e))}
        return {'ret': True, 'resp': resp}

    def patch_request(self, uri, pyld):
        try:
            resp = open_url(uri, data=json.dumps(pyld),
                            headers=PATCH_HEADERS, method="PATCH",
                            url_username=self.creds['user'],
                            url_password=self.creds['pswd'],
                            force_basic_auth=True, validate_certs=False,
                            follow_redirects='all',
                            use_proxy=False, timeout=self.timeout)
        except HTTPError as e:
            msg = self._get_extended_message(e)
            return {'ret': False,
                    'msg': "HTTP Error %s on PATCH request to '%s', extended message: '%s'"
                           % (e.code, uri, msg)}
        except URLError as e:
            return {'ret': False, 'msg': "URL Error on PATCH request to '%s': '%s'"
                                         % (uri, e.reason)}
        # Almost all errors should be caught above, but just in case
        except Exception as e:
            return {'ret': False,
                    'msg': "Failed PATCH request to '%s': '%s'" % (uri, to_text(e))}
        return {'ret': True, 'resp': resp}

    def delete_request(self, uri, pyld):
        try:
            resp = open_url(uri, data=json.dumps(pyld),
                            headers=DELETE_HEADERS, method="DELETE",
                            url_username=self.creds['user'],
                            url_password=self.creds['pswd'],
                            force_basic_auth=True, validate_certs=False,
                            follow_redirects='all',
                            use_proxy=False, timeout=self.timeout)
        except HTTPError as e:
            msg = self._get_extended_message(e)
            return {'ret': False,
                    'msg': "HTTP Error %s on DELETE request to '%s', extended message: '%s'"
                           % (e.code, uri, msg)}
        except URLError as e:
            return {'ret': False, 'msg': "URL Error on DELETE request to '%s': '%s'"
                                         % (uri, e.reason)}
        # Almost all errors should be caught above, but just in case
        except Exception as e:
            return {'ret': False,
                    'msg': "Failed DELETE request to '%s': '%s'" % (uri, to_text(e))}
        return {'ret': True, 'resp': resp}

    @staticmethod
    def _get_extended_message(error):
        """
        Get Redfish ExtendedInfo message from response payload if present
        :param error: an HTTPError exception
        :type error: HTTPError
        :return: the ExtendedInfo message if present, else standard HTTP error
        """
        msg = http_client.responses.get(error.code, '')
        if error.code >= 400:
            try:
                body = error.read().decode('utf-8')
                data = json.loads(body)
                ext_info = data['error']['@Message.ExtendedInfo']
                msg = ext_info[0]['Message']
            except Exception:
                pass
        return msg

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
        response = self.get_request(self.root_uri + data['Systems']['@odata.id'])
        if response['ret'] is False:
            return response
        self.systems_uris = [
            i['@odata.id'] for i in response['data'].get('Members', [])]
        if not self.systems_uris:
            return {
                'ret': False,
                'msg': "ComputerSystem's Members array is either empty or missing"}
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
                    self.post_request(self.root_uri + _data[u"Actions"]["#LogService.ClearLog"]["target"], {})
                    if response['ret'] is False:
                        return response
        return {'ret': True}

    def aggregate(self, func):
        ret = True
        entries = []
        for systems_uri in self.systems_uris:
            inventory = func(systems_uri)
            ret = inventory.pop('ret') and ret
            if 'entries' in inventory:
                entries.append(({'systems_uri': systems_uri},
                                inventory['entries']))
        return dict(ret=ret, entries=entries)

    def get_storage_controller_inventory(self, systems_uri):
        result = {}
        controller_list = []
        controller_results = []
        # Get these entries, but does not fail if not found
        properties = ['CacheSummary', 'FirmwareVersion', 'Identifiers',
                      'Location', 'Manufacturer', 'Model', 'Name',
                      'PartNumber', 'SerialNumber', 'SpeedGbps', 'Status']
        key = "StorageControllers"

        # Find Storage service
        response = self.get_request(self.root_uri + systems_uri)
        if response['ret'] is False:
            return response
        data = response['data']

        if 'Storage' not in data:
            return {'ret': False, 'msg': "Storage resource not found"}

        # Get a list of all storage controllers and build respective URIs
        storage_uri = data['Storage']["@odata.id"]
        response = self.get_request(self.root_uri + storage_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        # Loop through Members and their StorageControllers
        # and gather properties from each StorageController
        if data[u'Members']:
            for storage_member in data[u'Members']:
                storage_member_uri = storage_member[u'@odata.id']
                response = self.get_request(self.root_uri + storage_member_uri)
                data = response['data']

                if key in data:
                    controller_list = data[key]
                    for controller in controller_list:
                        controller_result = {}
                        for property in properties:
                            if property in controller:
                                controller_result[property] = controller[property]
                        controller_results.append(controller_result)
                result['entries'] = controller_results
            return result
        else:
            return {'ret': False, 'msg': "Storage resource not found"}

    def get_multi_storage_controller_inventory(self):
        return self.aggregate(self.get_storage_controller_inventory)

    def get_disk_inventory(self, systems_uri):
        result = {'entries': []}
        controller_list = []
        disk_results = []
        # Get these entries, but does not fail if not found
        properties = ['BlockSizeBytes', 'CapableSpeedGbs', 'CapacityBytes',
                      'EncryptionAbility', 'EncryptionStatus',
                      'FailurePredicted', 'HotspareType', 'Id', 'Identifiers',
                      'Manufacturer', 'MediaType', 'Model', 'Name',
                      'PartNumber', 'PhysicalLocation', 'Protocol', 'Revision',
                      'RotationSpeedRPM', 'SerialNumber', 'Status']

        # Find Storage service
        response = self.get_request(self.root_uri + systems_uri)
        if response['ret'] is False:
            return response
        data = response['data']

        if 'SimpleStorage' not in data and 'Storage' not in data:
            return {'ret': False, 'msg': "SimpleStorage and Storage resource \
                     not found"}

        if 'Storage' in data:
            # Get a list of all storage controllers and build respective URIs
            storage_uri = data[u'Storage'][u'@odata.id']
            response = self.get_request(self.root_uri + storage_uri)
            if response['ret'] is False:
                return response
            result['ret'] = True
            data = response['data']

            if data[u'Members']:
                for controller in data[u'Members']:
                    controller_list.append(controller[u'@odata.id'])
                for c in controller_list:
                    uri = self.root_uri + c
                    response = self.get_request(uri)
                    if response['ret'] is False:
                        return response
                    data = response['data']
                    if 'Drives' in data:
                        for device in data[u'Drives']:
                            disk_uri = self.root_uri + device[u'@odata.id']
                            response = self.get_request(disk_uri)
                            data = response['data']

                            disk_result = {}
                            for property in properties:
                                if property in data:
                                    if data[property] is not None:
                                        disk_result[property] = data[property]
                            disk_results.append(disk_result)
                result["entries"].append(disk_results)

        if 'SimpleStorage' in data:
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
                    disk_result = {}
                    for property in properties:
                        if property in device:
                            disk_result[property] = device[property]
                    disk_results.append(disk_result)
            result["entries"].append(disk_results)

        return result

    def get_multi_disk_inventory(self):
        return self.aggregate(self.get_disk_inventory)

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
        response = self.post_request(self.root_uri + action_uri, payload)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def manage_indicator_led(self, command):
        result = {}
        key = 'IndicatorLED'

        payloads = {'IndicatorLedOn': 'Lit', 'IndicatorLedOff': 'Off', "IndicatorLedBlink": 'Blinking'}

        result = {}
        for chassis_uri in self.chassis_uri_list:
            response = self.get_request(self.root_uri + chassis_uri)
            if response['ret'] is False:
                return response
            result['ret'] = True
            data = response['data']
            if key not in data:
                return {'ret': False, 'msg': "Key %s not found" % key}

            if command in payloads.keys():
                payload = {'IndicatorLED': payloads[command]}
                response = self.patch_request(self.root_uri + chassis_uri, payload)
                if response['ret'] is False:
                    return response
            else:
                return {'ret': False, 'msg': 'Invalid command'}

        return result

    def manage_system_power(self, command):
        result = {}
        key = "Actions"

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + self.systems_uris[0])
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']
        power_state = data["PowerState"]
        reset_action = data[key]["#ComputerSystem.Reset"]
        action_uri = reset_action["target"]
        allowable_vals = reset_action.get("ResetType@Redfish.AllowableValues", [])
        restart_cmd = "GracefulRestart"
        if "ForceRestart" in allowable_vals and "GracefulRestart" not in allowable_vals:
            restart_cmd = "ForceRestart"

        # Define payload accordingly
        if command == "PowerOn":
            payload = {'ResetType': 'On'}
        elif command == "PowerForceOff":
            payload = {'ResetType': 'ForceOff'}
        elif command == "PowerGracefulRestart":
            payload = {'ResetType': 'GracefulRestart'}
        elif command == "PowerGracefulShutdown":
            payload = {'ResetType': 'GracefulShutdown'}
        elif command == "PowerReboot":
            if power_state == "On":
                payload = {'ResetType': restart_cmd}
            else:
                payload = {'ResetType': "On"}
        else:
            return {'ret': False, 'msg': 'Invalid Command'}

        response = self.post_request(self.root_uri + action_uri, payload)
        if response['ret'] is False:
            return response
        result['ret'] = True
        return result

    def list_users(self):
        result = {}
        # listing all users has always been slower than other operations, why?
        user_list = []
        users_results = []
        # Get these entries, but does not fail if not found
        properties = ['Id', 'Name', 'UserName', 'RoleId', 'Locked', 'Enabled']

        response = self.get_request(self.root_uri + self.accounts_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        for users in data[u'Members']:
            user_list.append(users[u'@odata.id'])   # user_list[] are URIs

        # for each user, get details
        for uri in user_list:
            user = {}
            response = self.get_request(self.root_uri + uri)
            if response['ret'] is False:
                return response
            data = response['data']

            for property in properties:
                if property in data:
                    user[property] = data[property]

            users_results.append(user)
        result["entries"] = users_results
        return result

    def add_user(self, user):
        uri = self.root_uri + self.accounts_uri + "/" + user['userid']
        username = {'UserName': user['username']}
        pswd = {'Password': user['userpswd']}
        roleid = {'RoleId': user['userrole']}
        enabled = {'Enabled': True}
        for payload in username, pswd, roleid, enabled:
            response = self.patch_request(uri, payload)
            if response['ret'] is False:
                return response
        return {'ret': True}

    def enable_user(self, user):
        uri = self.root_uri + self.accounts_uri + "/" + user['userid']
        payload = {'Enabled': True}
        response = self.patch_request(uri, payload)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def delete_user(self, user):
        uri = self.root_uri + self.accounts_uri + "/" + user['userid']
        payload = {'UserName': ""}
        response = self.patch_request(uri, payload)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def disable_user(self, user):
        uri = self.root_uri + self.accounts_uri + "/" + user['userid']
        payload = {'Enabled': False}
        response = self.patch_request(uri, payload)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def update_user_role(self, user):
        uri = self.root_uri + self.accounts_uri + "/" + user['userid']
        payload = {'RoleId': user['userrole']}
        response = self.patch_request(uri, payload)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def update_user_password(self, user):
        uri = self.root_uri + self.accounts_uri + "/" + user['userid']
        payload = {'Password': user['userpswd']}
        response = self.patch_request(uri, payload)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def get_firmware_inventory(self):
        result = {}
        response = self.get_request(self.root_uri + self.firmware_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        result['entries'] = []
        for device in data[u'Members']:
            uri = self.root_uri + device[u'@odata.id']
            # Get details for each device
            response = self.get_request(uri)
            if response['ret'] is False:
                return response
            result['ret'] = True
            data = response['data']
            firmware = {}
            # Get these standard properties if present
            for key in ['Name', 'Id', 'Status', 'Version', 'Updateable',
                        'SoftwareId', 'LowestSupportedVersion', 'Manufacturer',
                        'ReleaseDate']:
                if key in data:
                    firmware[key] = data.get(key)
            result['entries'].append(firmware)
        return result

    def get_bios_attributes(self, systems_uri):
        result = {}
        bios_attributes = {}
        key = "Bios"

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + systems_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        if key not in data:
            return {'ret': False, 'msg': "Key %s not found" % key}

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

    def get_multi_bios_attributes(self):
        return self.aggregate(self.get_bios_attributes)

    def get_boot_order(self, systems_uri):
        result = {}
        # Get these entries from BootOption, if present
        properties = ['DisplayName', 'BootOptionReference']

        # Retrieve System resource
        response = self.get_request(self.root_uri + systems_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        # Confirm needed Boot properties are present
        if 'Boot' not in data or 'BootOrder' not in data['Boot']:
            return {'ret': False, 'msg': "Key BootOrder not found"}

        boot = data['Boot']
        boot_order = boot['BootOrder']

        # Retrieve BootOptions if present
        if 'BootOptions' in boot and '@odata.id' in boot['BootOptions']:
            boot_options_uri = boot['BootOptions']["@odata.id"]
            # Get BootOptions resource
            response = self.get_request(self.root_uri + boot_options_uri)
            if response['ret'] is False:
                return response
            data = response['data']

            # Retrieve Members array
            if 'Members' not in data:
                return {'ret': False,
                        'msg': "Members not found in BootOptionsCollection"}
            members = data['Members']
        else:
            members = []

        # Build dict of BootOptions keyed by BootOptionReference
        boot_options_dict = {}
        for member in members:
            if '@odata.id' not in member:
                return {'ret': False,
                        'msg': "@odata.id not found in BootOptions"}
            boot_option_uri = member['@odata.id']
            response = self.get_request(self.root_uri + boot_option_uri)
            if response['ret'] is False:
                return response
            data = response['data']
            if 'BootOptionReference' not in data:
                return {'ret': False,
                        'msg': "BootOptionReference not found in BootOption"}
            boot_option_ref = data['BootOptionReference']

            # fetch the props to display for this boot device
            boot_props = {}
            for prop in properties:
                if prop in data:
                    boot_props[prop] = data[prop]

            boot_options_dict[boot_option_ref] = boot_props

        # Build boot device list
        boot_device_list = []
        for ref in boot_order:
            boot_device_list.append(
                boot_options_dict.get(ref, {'BootOptionReference': ref}))

        result["entries"] = boot_device_list
        return result

    def get_multi_boot_order(self):
        return self.aggregate(self.get_boot_order)

    def set_bios_default_settings(self):
        result = {}
        key = "Bios"

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + self.systems_uris[0])
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        if key not in data:
            return {'ret': False, 'msg': "Key %s not found" % key}

        bios_uri = data[key]["@odata.id"]

        # Extract proper URI
        response = self.get_request(self.root_uri + bios_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']
        reset_bios_settings_uri = data["Actions"]["#Bios.ResetBios"]["target"]

        response = self.post_request(self.root_uri + reset_bios_settings_uri, {})
        if response['ret'] is False:
            return response
        return {'ret': True, 'changed': True, 'msg': "Set BIOS to default settings"}

    def set_one_time_boot_device(self, bootdevice):
        result = {}
        key = "Bios"

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + self.systems_uris[0])
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        if key not in data:
            return {'ret': False, 'msg': "Key %s not found" % key}

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

        response = self.patch_request(self.root_uri + self.systems_uris[0], payload)
        if response['ret'] is False:
            return response
        return {'ret': True}

    def set_bios_attributes(self, attr):
        result = {}
        key = "Bios"

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + self.systems_uris[0])
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        if key not in data:
            return {'ret': False, 'msg': "Key %s not found" % key}

        bios_uri = data[key]["@odata.id"]

        # Extract proper URI
        response = self.get_request(self.root_uri + bios_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        # First, check if BIOS attribute exists
        if attr['bios_attr_name'] not in data[u'Attributes']:
            return {'ret': False, 'msg': "BIOS attribute not found"}

        # Find out if value is already set to what we want. If yes, return
        if data[u'Attributes'][attr['bios_attr_name']] == attr['bios_attr_value']:
            return {'ret': True, 'changed': False, 'msg': "BIOS attribute already set"}

        set_bios_attr_uri = data["@Redfish.Settings"]["SettingsObject"]["@odata.id"]

        # patch_request() will use json.dumps() on the payload, we can pass a
        # python dict as our payload.
        payload = {"Attributes": {attr['bios_attr_name']: attr['bios_attr_value']}}
        response = self.patch_request(self.root_uri + set_bios_attr_uri, payload)
        if response['ret'] is False:
            return response
        return {'ret': True, 'changed': True, 'msg': "Modified BIOS attribute"}

    def get_fan_inventory(self):
        result = {}
        fan_results = []
        key = "Thermal"
        # Get these entries, but does not fail if not found
        properties = ['FanName', 'Reading', 'ReadingUnits', 'Status']

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
                    fan = {}
                    for property in properties:
                        if property in device:
                            fan[property] = device[property]
                    fan_results.append(fan)
        result["entries"] = fan_results
        return result

    def get_cpu_inventory(self, systems_uri):
        result = {}
        cpu_list = []
        cpu_results = []
        key = "Processors"
        # Get these entries, but does not fail if not found
        properties = ['Id', 'Manufacturer', 'Model', 'MaxSpeedMHz', 'TotalCores',
                      'TotalThreads', 'Status']

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + systems_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        if key not in data:
            return {'ret': False, 'msg': "Key %s not found" % key}

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
            cpu = {}
            uri = self.root_uri + c
            response = self.get_request(uri)
            if response['ret'] is False:
                return response
            data = response['data']

            for property in properties:
                if property in data:
                    cpu[property] = data[property]

            cpu_results.append(cpu)
        result["entries"] = cpu_results
        return result

    def get_multi_cpu_inventory(self):
        return self.aggregate(self.get_cpu_inventory)

    def get_memory_inventory(self, systems_uri):
        result = {}
        memory_list = []
        memory_results = []
        key = "Memory"
        # Get these entries, but does not fail if not found
        properties = ['SerialNumber', 'MemoryDeviceType', 'PartNuber',
                      'MemoryLocation', 'RankCount', 'CapacityMiB', 'OperatingMemoryModes', 'Status', 'Manufacturer', 'Name']

        # Search for 'key' entry and extract URI from it
        response = self.get_request(self.root_uri + systems_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        if key not in data:
            return {'ret': False, 'msg': "Key %s not found" % key}

        memory_uri = data[key]["@odata.id"]

        # Get a list of all DIMMs and build respective URIs
        response = self.get_request(self.root_uri + memory_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        for dimm in data[u'Members']:
            memory_list.append(dimm[u'@odata.id'])

        for m in memory_list:
            dimm = {}
            uri = self.root_uri + m
            response = self.get_request(uri)
            if response['ret'] is False:
                return response
            data = response['data']

            if "Status" in data:
                if "State" in data["Status"]:
                    if data["Status"]["State"] == "Absent":
                        continue
            else:
                continue

            for property in properties:
                if property in data:
                    dimm[property] = data[property]

            memory_results.append(dimm)
        result["entries"] = memory_results
        return result

    def get_multi_memory_inventory(self):
        return self.aggregate(self.get_memory_inventory)

    def get_nic_inventory(self, resource_uri):
        result = {}
        nic_list = []
        nic_results = []
        key = "EthernetInterfaces"
        # Get these entries, but does not fail if not found
        properties = ['Description', 'FQDN', 'IPv4Addresses', 'IPv6Addresses',
                      'NameServers', 'PermanentMACAddress', 'SpeedMbps', 'MTUSize',
                      'AutoNeg', 'Status']

        response = self.get_request(self.root_uri + resource_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        if key not in data:
            return {'ret': False, 'msg': "Key %s not found" % key}

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

            for property in properties:
                if property in data:
                    nic[property] = data[property]

            nic_results.append(nic)
        result["entries"] = nic_results
        return result

    def get_multi_nic_inventory(self, resource_type):
        ret = True
        entries = []

        #  Given resource_type, use the proper URI
        if resource_type == 'Systems':
            resource_uris = self.systems_uris
        elif resource_type == 'Manager':
            # put in a list to match what we're doing with systems_uris
            resource_uris = [self.manager_uri]

        for resource_uri in resource_uris:
            inventory = self.get_nic_inventory(resource_uri)
            ret = inventory.pop('ret') and ret
            if 'entries' in inventory:
                entries.append(({'resource_uri': resource_uri},
                               inventory['entries']))
        return dict(ret=ret, entries=entries)

    def get_psu_inventory(self):
        result = {}
        psu_list = []
        psu_results = []
        key = "PowerSupplies"
        # Get these entries, but does not fail if not found
        properties = ['Name', 'Model', 'SerialNumber', 'PartNumber', 'Manufacturer',
                      'FirmwareVersion', 'PowerCapacityWatts', 'PowerSupplyType',
                      'Status']

        # Get a list of all Chassis and build URIs, then get all PowerSupplies
        # from each Power entry in the Chassis
        chassis_uri_list = self.chassis_uri_list
        for chassis_uri in chassis_uri_list:
            response = self.get_request(self.root_uri + chassis_uri)
            if response['ret'] is False:
                return response

            result['ret'] = True
            data = response['data']

            if 'Power' in data:
                power_uri = data[u'Power'][u'@odata.id']
            else:
                continue

            response = self.get_request(self.root_uri + power_uri)
            data = response['data']

            if key not in data:
                return {'ret': False, 'msg': "Key %s not found" % key}

            psu_list = data[key]
            for psu in psu_list:
                psu_not_present = False
                psu_data = {}
                for property in properties:
                    if property in psu:
                        if psu[property] is not None:
                            if property == 'Status':
                                if 'State' in psu[property]:
                                    if psu[property]['State'] == 'Absent':
                                        psu_not_present = True
                            psu_data[property] = psu[property]
                if psu_not_present:
                    continue
                psu_results.append(psu_data)

        result["entries"] = psu_results
        if not result["entries"]:
            return {'ret': False, 'msg': "No PowerSupply objects found"}
        return result

    def get_multi_psu_inventory(self):
        return self.aggregate(self.get_psu_inventory)

    def get_system_inventory(self, systems_uri):
        result = {}
        inventory = {}
        # Get these entries, but does not fail if not found
        properties = ['Status', 'HostName', 'PowerState', 'Model', 'Manufacturer',
                      'PartNumber', 'SystemType', 'AssetTag', 'ServiceTag',
                      'SerialNumber', 'SKU', 'BiosVersion', 'MemorySummary',
                      'ProcessorSummary', 'TrustedModules']

        response = self.get_request(self.root_uri + systems_uri)
        if response['ret'] is False:
            return response
        result['ret'] = True
        data = response['data']

        for property in properties:
            if property in data:
                inventory[property] = data[property]

        result["entries"] = inventory
        return result

    def get_multi_system_inventory(self):
        return self.aggregate(self.get_system_inventory)
