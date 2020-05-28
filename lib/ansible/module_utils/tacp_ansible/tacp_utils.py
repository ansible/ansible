#!/usr/bin/python

# Copyright: (c) 2020, Lenovo
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import re
import tacp
from tacp.rest import ApiException

from ansible.module_utils.tacp_ansible.tacp_exceptions import ActionTimedOutException, InvalidActionUuidException
from ansible.module_utils.tacp_ansible.tacp_constants import Action
from uuid import UUID, uuid4
from time import sleep


class ApiResource(object):

    def __init__(self, api_client):
        self._api = self.model(api_client)
        self._api_client = api_client

    def get_all(self, *args, **kwargs):
        all_instances = self._get_all(args, kwargs)
        return all_instances

    def get_uuid_by_name(self, name):
        """ Return the UUID of an appplication instance if it exists
            given the name of the instance, None otherwise
        """
        all_instances = self._get_all()
        for instance in all_instances:
            if instance.name == name:
                return instance.uuid
        return None

    def get_by_uuid(self, uuid):
        return self._get_by_uuid(uuid).to_dict()

    def create(self, body):
        api_response = self._create(
            body)
        wait_for_action_to_complete(
            api_response.action_uuid)
        return api_response.object_uuid

    def delete(self, uuid):
        api_response = self._delete(uuid)
        wait_for_action_to_complete(
            api_response.action_uuid)
        return True

    def wait_for_action_to_complete(self, action_uuid):
        if action_uuid:
            api_instance = tacp.ActionsApi(self._api_client)
            action_incomplete = True

            timeout = 60
            time_spent = 0

            while action_incomplete and time_spent < timeout:
                api_response = api_instance.get_action_using_get(action_uuid)
                if api_response.status == 'Completed':
                    action_incomplete = False
                    return True
                else:
                    sleep(1)
                    time_spent += 1
            raise ActionTimedOutException
        raise InvalidActionUuidException


class ApplicationResource(ApiResource):

    model = tacp.ApplicationsApi

    def _get_all(self, *args, **kwargs):
        if kwargs:
            return self._api.get_applications_using_get(filters=";".join(kwargs))
        else:
            return self._api.get_applications_using_get()

    def _get_by_uuid(self, uuid):
        return self._api.get_application_using_get(uuid)

    def _create(self, body):
        return self._api.create_application_from_template_using_post(body)

    def _delete(self, uuid):
        return self._api.delete_application_using_delete(uuid)

    def power_action_on_instance_by_uuid(self, uuid, power_action):
        """ Performs a specified power operation on an application instance
            specified by UUID, returns bool of success/failure
        """
        power_action_dict = {
            Action.STARTED: self._api.start_application_using_put,
            Action.SHUTDOWN: self._api.shutdown_application_using_put,
            Action.STOPPED: self._api.stop_application_using_put,
            Action.RESTARTED: self._api.restart_application_using_put,
            Action.FORCE_RESTARTED: self._api.force_restart_application_using_put,
            Action.PAUSED: self._api.pause_application_using_put,
            Action.ABSENT: self._api.delete_application_using_delete,
            Action.RESUMED: self._api.resume_application_using_put
        }

        api_response = power_action_dict[power_action](uuid)
        self.wait_for_action_to_complete(
            api_response.action_uuid)
        return True


class VlanResource(ApiResource):

    model = tacp.VlansApi

    def _get_all(self, *args, **kwargs):
        if kwargs:
            return self._api.get_vlans_using_get(filters=";".join(kwargs))
        else:
            return self._api.get_vlans_using_get()

    def _get_by_uuid(self, uuid):
        return self._api.get_vlan_using_get(uuid)

    def _create(self, body):
        return self._api.create_vlan_using_post(body)

    def _delete(self, uuid):
        return self._api.delete_vlan_using_delete(uuid)


class VnetResource(ApiResource):

    model = tacp.VnetsApi

    def _get_all(self, *args, **kwargs):
        if kwargs:
            return self._api.get_vnets_using_get(filters=";".join(kwargs))
        else:
            return self._api.get_vnets_using_get()

    def _get_by_uuid(self, uuid):
        return self._api.get_vnet_using_get(uuid)

    def _create(self, body):
        return self._api.create_vnet_using_post(body)

    def _delete(self, uuid):
        return self._api.delete_vnet_using_delete(uuid)


def get_component_fields_by_name(name, component,
                                 api_client, fields=['name', 'uuid']):
    """
    Returns the UUID of a named component if it exists in a given
    ThinkAgile CP cloud, otherwise return None.

    :param name The name of the component that may or may not exist yet
    :type name str
    :param component The type of component in question, must be one of
    """

    valid_components = ["storage_pool", "application",
                        "template", "datacenter", "migration_zone",
                        "vnet", "vlan", "firewall_profile", "firewall_override"]

    if component not in valid_components:
        return "Invalid component"
    if component == "storage_pool":
        api_instance = tacp.FlashPoolsApi(api_client)
        try:
            # View flash pools for an organization
            api_response = api_instance.get_flash_pools_using_get(
                fields=fields)
        except ApiException as e:
            return "Exception when calling get_flash_pools_using_get: %s\n" % e
    elif component == "application":
        api_instance = tacp.ApplicationsApi(api_client)
        try:
            # View applications for an organization
            api_response = api_instance.get_applications_using_get(
                fields=fields)
        except ApiException as e:
            return "Exception when calling get_applications_using_get: %s\n" % e
    elif component == "template":
        api_instance = tacp.TemplatesApi(api_client)
        try:
            # View templates for an organization
            api_response = api_instance.get_templates_using_get(
                fields=fields)
        except ApiException as e:
            return "Exception when calling get_templates_using_get: %s\n" % e
    elif component == "datacenter":
        api_instance = tacp.DatacentersApi(api_client)
        try:
            # View datacenters for an organization
            api_response = api_instance.get_datacenters_using_get(
                fields=fields)
        except ApiException as e:
            return "Exception when calling get_datacenters_using_get: %s\n" % e
    elif component == "migration_zone":
        api_instance = tacp.MigrationZonesApi(api_client)
        try:
            # View migration zones for an organization
            api_response = api_instance.get_migration_zones_using_get(
                fields=fields)
        except ApiException as e:
            return "Exception when calling get_migration_zones_using_get: %s\n" % e
    elif component == "vlan":
        api_instance = tacp.VlansApi(api_client)
        try:
            # View VLAN networks for an organization
            api_response = api_instance.get_vlans_using_get(
                fields=fields)
        except ApiException as e:
            return "Exception when calling get_vlans_using_get: %s\n" % e
    elif component == "vnet":
        api_instance = tacp.VnetsApi(api_client)
        try:
            # View VNET networks for an organization
            api_response = api_instance.get_vnets_using_get(
                fields=fields)
        except ApiException as e:
            return "Exception when calling get_vnets_using_get: %s\n" % e
    elif component == "firewall_profile":
        api_instance = tacp.FirewallProfilesApi(api_client)
        try:
            # View Firewall profiles for an organization
            api_response = api_instance.get_firewall_profiles_using_get(
                fields=fields)
        except ApiException as e:
            return "Exception when calling get_firewall_profiles_using_get: %s\n" % e
    elif component == "firewall_override":
        # Need to get all datacenter UUIDs first
        api_instance = tacp.DatacentersApi(api_client)
        try:
            # View datacenters for an organization
            datacenter_list = api_instance.get_datacenters_using_get(
                fields=fields)
        except ApiException as e:
            return "Exception when calling get_datacenters_using_get: %s\n" % e

        api_response = []
        for datacenter in datacenter_list:
            api_instance = tacp.DatacentersApi(api_client)
            try:
                # View Firewall profiles for an organization
                api_response += api_instance.get_datacenter_firewall_overrides_using_get(
                    uuid=datacenter.uuid, fields=fields)
            except ApiException as e:
                return "Exception when calling get_firewall_profiles_using_get"

    if (api_response):
        if fields == ['name', 'uuid']:
            for result in api_response:
                if result.name == name:
                    return result.uuid
        if 'bootOrder' in fields:
            for result in api_response:
                if result.name == name:
                    boot_order = []
                    for order_item in result.boot_order:
                        str_dict = str(order_item).replace(
                            "\n", "").replace("'", '"').replace("None", '""')

                        json_dict = json.loads(str_dict)

                        disk_uuid = json_dict['disk_uuid'] if json_dict['disk_uuid'] else None
                        name = json_dict['name'] if json_dict['name'] else None
                        order = json_dict['order'] if json_dict['order'] else None
                        vnic_uuid = json_dict['vnic_uuid'] if json_dict['vnic_uuid'] else None

                        boot_order_payload = tacp.ApiBootOrderPayload(disk_uuid=disk_uuid,
                                                                      name=name,
                                                                      order=order,
                                                                      vnic_uuid=vnic_uuid)
                        boot_order.append(boot_order_payload)
                    return boot_order
        if 'nfvInstanceUuid' in fields:
            return api_response[0]
    return None


def convert_memory_abbreviation_to_bytes(value):
    """Validate memory argument. Returns the memory value in bytes."""
    MEMORY_RE = re.compile(
        r"^(?P<amount>[0-9]+)(?P<unit>t|tb|g|gb|m|mb|k|kb)?$")

    matches = MEMORY_RE.match(value.lower())
    if matches is None:
        raise ValueError(
            '%s is not a valid value for memory amount' % value)
    amount_str, unit = matches.groups()
    amount = int(amount_str)
    amount_in_bytes = amount
    if unit is None:
        amount_in_bytes = amount
    elif unit in ['k', 'kb', 'K', 'KB']:
        amount_in_bytes = amount * 1024
    elif unit in ['m', 'mb', 'M', 'MB']:
        amount_in_bytes = amount * 1024 * 1024
    elif unit in ['g', 'gb', 'G', 'GB']:
        amount_in_bytes = amount * 1024 * 1024 * 1024
    elif unit in ['t', 'tb', 'T', 'TB']:
        amount_in_bytes = amount * 1024 * 1024 * 1024 * 1024

    return amount_in_bytes