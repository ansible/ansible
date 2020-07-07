#!/usr/bin/python

# Copyright: (c) 2020, Lenovo
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import re
import tacp

from functools import wraps

from tacp.rest import ApiException

from ansible.module_utils.tacp_ansible.tacp_exceptions import (
    ActionTimedOutException, InvalidActionUuidException,
    InvalidPowerActionException, UuidNotFoundException
)
from ansible.module_utils.tacp_ansible.tacp_constants import PlaybookState
from time import sleep


def get_configuration(api_key, portal_url):
    configuration = tacp.Configuration()
    configuration.host = portal_url
    configuration.api_key_prefix['Authorization'] = 'Bearer'
    configuration.api_key['Authorization'] = api_key
    return configuration


def wait_to_complete(method):
    """ Decorator to be used against methods that perform async operations.

    Returns the decorated method returned value. Decorated methods should
    return the api response and could have the following named arguments:

        _wait (bool): Wait for the action to be performed, defaults to True.
        _wait_timeout (int): How long before wait gives up, in seconds.

    Raises:
        ActionTimedOutException: if the action timed out
        InvalidActionUuidException: if the action uuid cant be found on the
            decorated method returned value
    """
    @wraps(method)
    def wrapper(self, *a, **kws):
        wait = kws.pop('_wait', True)
        wait_timeout = kws.pop('_wait_timeout', 120)

        try:
            method_api_response = method.__get__(self, type(self))(*a, **kws)
        except Exception as e:
            return e

        if not wait:
            return method_api_response

        action_uuid = getattr(method_api_response, 'action_uuid', None)

        if action_uuid:
            api_instance = tacp.ActionsApi(self._api_client)

            time_spent = 0

            while time_spent < wait_timeout:
                api_response = api_instance.get_action_using_get(action_uuid)
                if api_response.status == 'Completed':
                    return method_api_response

                sleep(1)
                time_spent += 1
            raise ActionTimedOutException
        raise InvalidActionUuidException
    return wrapper


class Resource(object):
    resource_class = None

    def __init__(self, client):
        assert self.resource_class is not None
        self.api = self.resource_class(client)
        self._api_client = client

    FILTER_OPERATORS = [
        '==', '!=', '=lt=', '<', '=le=', '<=', '=gt=', '>', '=ge=', '>=',
        '=in=', '=out='
    ]

    def get_filters_query_string(self, **kws):
        """
        Returns a string used as filters query string

        To use operators provide the value of a kwarg as two item tuple:
            (operator, actual_value)

        If the value of a kwarg is not a two item tuple then the default `==`
        operator is used.

        Operators:
            - Equal to: ==
            - Not equal to: !=
            - Less than: =lt= or <
            - Less than or equal to: =le= or <=
            - Greater than operator: =gt= or >
            - Greater than or equal to: =ge= or >=
            - In: =in=
            - Not in: =out=

        The following:
            name='some name'

        Is the same as:
            name=('==', 'some name')
        """
        if not kws:
            return ''

        filters = []
        allowed = self.FILTER_OPERATORS

        for k, v in kws.items():
            if isinstance(v, (list, tuple)):
                op, value = v[0], v[1:]
                if op not in allowed:
                    raise Exception('Invalid operator "{}". '
                                    'Allowed: {}'.format(op, allowed))
                if len(value) == 0:
                    raise Exception('Must provide at least one value')

                value = value[0]
                if op in ('=in=', '=out='):
                    value = ','.join(map(str, value))
                    value = '({})'.format(value)
            else:
                op = '=='
                value = v
            filters.append('{}{}{}'.format(k, op, value))

        return ';'.join(filters)

    def get_filters_kws(self, **filters):
        query_string = self.get_filters_query_string(**filters)
        if query_string:
            return {'filters': query_string}
        return {}

    def get_by_name(self, name):
        instances = self.filter(name=name)
        if instances:
            return instances[0]
        return None

    filter_method = None
    uuid_method = None

    def filter(self, **filters):
        if self.filter_method is None:
            raise Exception('Invalid self.filter_method')
        method = getattr(self.api, self.filter_method, None)
        if method is None:
            raise Exception('Invalid self.filter_method')

        return method(**self.get_filters_kws(**filters))

    def get_by_uuid(self, uuid):
        if self.uuid_method is None:
            raise Exception('Invalid self.uuid_method')
        method = getattr(self.api, self.uuid_method, None)
        if method is None:
            raise Exception('Invalid self.uuid_method')

        resource = method(uuid)
        if not resource:
            return None
        return resource

    def create(self, body):
        raise NotImplementedError

    def delete(self, uuid):
        raise NotImplementedError


class ApplicationResource(Resource):
    resource_class = tacp.ApplicationsApi

    filter_method = "get_applications_using_get"
    uuid_method = "get_application_using_get"

    @wait_to_complete
    def create(self, body):
        return self.api.create_application_from_template_using_post(body)

    @wait_to_complete
    def delete(self, uuid):
        return self.api.delete_application_using_delete(uuid)

    @wait_to_complete
    def power_action_on_instance_by_uuid(self, uuid, power_action):
        """ Performs a specified power operation on an application instance
            specified by UUID
        """
        power_action_dict = {
            PlaybookState.STARTED: self.api.start_application_using_put,
            PlaybookState.SHUTDOWN: self.api.shutdown_application_using_put,
            PlaybookState.STOPPED: self.api.stop_application_using_put,
            PlaybookState.RESTARTED: self.api.restart_application_using_put,
            PlaybookState.FORCE_RESTARTED: self.api.force_restart_application_using_put,  # noqa
            PlaybookState.PAUSED: self.api.pause_application_using_put,
            PlaybookState.ABSENT: self.api.delete_application_using_delete,
            PlaybookState.RESUMED: self.api.resume_application_using_put
        }
        if power_action not in power_action_dict:
            raise InvalidPowerActionException
        return power_action_dict[power_action](uuid)


class ApplicationUpdateResource(Resource):

    resource_class = tacp.EditApplicationsApi

    @wait_to_complete
    def create_disk(self, body, uuid):
        return self.api.create_application_disk_using_post(body, uuid)

    @wait_to_complete
    def create_vnic(self, body, uuid):
        return self.api.create_application_vnic_using_post(body, uuid)

    def edit_boot_order(self, body, uuid):
        return self.api.edit_application_boot_order_using_put(body, uuid)

    @wait_to_complete
    def edit_disk_name(self, disk_uuid, uuid, disk_name):
        body = tacp.ApiDiskSizePayload(name=disk_name, uuid=disk_uuid)
        return self.api.edit_application_disk_name_using_put(
            body, disk_uuid, uuid)

    @wait_to_complete
    def edit_disk_size(self, disk_uuid, uuid, disk_size):
        body = tacp.ApiDiskSizePayload(size=disk_size, uuid=disk_uuid)
        return self.api.edit_application_disk_size_using_put(
            body, disk_uuid, uuid)

    @wait_to_complete
    def edit_disk_bw_limit(self, disk_uuid, uuid, bw_limit):
        body = tacp.ApiDiskBandwidthPayload(
            bandwidth_limit=bw_limit, uuid=disk_uuid)
        return self.api.edit_application_disk_bandwidth_limit_using_put(
            body, disk_uuid, uuid)

    @wait_to_complete
    def edit_disk_iops_limit(self, disk_uuid, uuid, iops_limit):
        body = tacp.ApiDiskIopsPayload(iops_limit=iops_limit, uuid=disk_uuid)
        return self.api.edit_application_disk_iops_limit_using_put(
            body, disk_uuid, uuid)


class VlanResource(Resource):
    resource_class = tacp.VlansApi

    filter_method = "get_vlans_using_get"
    uuid_method = "get_vlan_using_get"

    @wait_to_complete
    def create(self, body):
        return self.api.create_vlan_using_post(body)

    @wait_to_complete
    def delete(self, uuid):
        return self.api.delete_vlan_using_delete(uuid)


class VnetResource(Resource):
    resource_class = tacp.VnetsApi

    filter_method = "get_vnets_using_get"
    uuid_method = "get_vnet_using_get"

    @wait_to_complete
    def create(self, body):
        return self.api.create_vnet_using_post(body)

    @wait_to_complete
    def delete(self, uuid):
        return self.api.delete_vnet_using_delete(uuid)


class StoragePoolResource(Resource):

    resource_class = tacp.FlashPoolsApi

    filter_method = "get_flash_pools_using_get"
    uuid_method = "get_flash_pool_using_get"


class DatacenterResource(Resource):

    resource_class = tacp.DatacentersApi

    filter_method = "get_datacenters_using_get"
    uuid_method = "get_datacenter_using_get"

    def get_firewall_override_by_name(self, datacenter_uuid,
                                      firewall_override_name):
        firewall_overrides = self.api.get_datacenter_firewall_overrides_using_get(  # noqa
            uuid=datacenter_uuid,
            filters='name=="{}"'.format(firewall_override_name))
        firewall_override = None

        if firewall_overrides:
            firewall_override = firewall_overrides[0]

        return firewall_override


class UserResource(Resource):

    resource_class = tacp.UsersApi

    filter_method = "get_users_using_get"
    uuid_method = "get_user_using_get"


class SiteResource(Resource):

    resource_class = tacp.LocationsApi

    filter_method = "get_locations_for_organization_using_get"
    uuid_method = "get_location_information_using_get"


class TemplateResource(Resource):

    resource_class = tacp.TemplatesApi

    filter_method = "get_templates_using_get"
    uuid_method = "get_template_using_get"


class TagResource(Resource):

    resource_class = tacp.TagsApi

    filter_method = "get_tags_using_get"
    uuid_method = "get_tag_using_get"


class MigrationZoneResource(Resource):

    resource_class = tacp.MigrationZonesApi

    filter_method = "get_migration_zones_using_get"
    uuid_method = "get_migration_zone_using_get"


class MarketplaceTemplateResource(Resource):

    resource_class = tacp.MarketplaceTemplatesApi

    filter_method = "get_marketplace_templates_using_get"
    uuid_method = "get_marketplace_template_using_get"


class ApplicationGroupResource(Resource):

    resource_class = tacp.ApplicationGroupsApi

    filter_method = "get_application_group_list_using_get"
    uuid_method = "get_application_group_information_using_get"


class CategoryResource(Resource):

    resource_class = tacp.CategoriesApi

    filter_method = "get_categories_using_get"
    uuid_method = "get_category_using_get"


class FirewallProfileResource(Resource):

    resource_class = tacp.FirewallProfilesApi

    filter_method = "get_firewall_profiles_using_get"


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
                        "vnet", "vlan", "firewall_profile",
                        "firewall_override"]

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
            return "Exception when calling get_applications_using_get: %s\n" % e  # noqa
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
            return "Exception when calling get_migration_zones_using_get: %s\n" % e  # noqa
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
            return "Exception when calling get_firewall_profiles_using_get: %s\n" % e  # noqa
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
                api_response += api_instance.get_datacenter_firewall_overrides_using_get(  # noqa
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

                        disk_uuid = json_dict['disk_uuid'] if json_dict['disk_uuid'] else None  # noqa
                        name = json_dict['name'] if json_dict['name'] else None
                        order = json_dict['order'] if json_dict['order'] else None  # noqa
                        vnic_uuid = json_dict['vnic_uuid'] if json_dict['vnic_uuid'] else None  # noqa

                        boot_order_payload = tacp.ApiBootOrderPayload(disk_uuid=disk_uuid,  # noqa
                                                                      name=name,            # noqa
                                                                      order=order,          # noqa
                                                                      vnic_uuid=vnic_uuid)  # noqa
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


def fill_in_missing_names_by_uuid(item, api_resource, key_name):
    if key_name == "applications":
        uuid_name = 'uuid'
    elif key_name == "categories":
        uuid_name = 'category_uuid'
    else:
        uuid_name = key_name[:-1] + "_uuid"
    uuids = [resource[uuid_name] for resource in item[key_name]]  # noqa
    resource_list = {resource.uuid: resource.name for resource in  # noqa
                        api_resource.filter(uuid=('=in=', uuids))}  # noqa
    for resource in item[key_name]:
        resource['name'] = resource_list[resource[uuid_name]]

    return item
