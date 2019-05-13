# Copyright (c) 2018 Remy Leone
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = '''
    name: netbox
    plugin_type: inventory
    author:
        - Remy Leone (@sieben)
        - Anthony Ruhier (@Anthony25)
        - Nikhil Singh Baliyan (@nikkytub)
    short_description: NetBox inventory source
    description:
        - Get inventory hosts from NetBox
    extends_documentation_fragment:
        - constructed
    options:
        plugin:
            description: token that ensures this is a source file for the 'netbox' plugin.
            required: True
            choices: ['netbox']
        api_endpoint:
            description: Endpoint of the NetBox API
            required: True
            env:
                - name: NETBOX_API
        validate_certs:
            description:
                - Allows connection when SSL certificates are not valid. Set to C(false) when certificates are not trusted.
            default: True
            type: boolean
        config_context:
            description:
                - If True, it adds config-context in host vars.
                - Config-context enables the association of arbitrary data to devices and virtual machines grouped by
                  region, site, role, platform, and/or tenant. Please check official netbox docs for more info.
            default: False
            type: boolean
        token:
            required: True
            description: NetBox token.
            env:
                # in order of precedence
                - name: NETBOX_TOKEN
                - name: NETBOX_API_KEY
        group_by:
            description: Keys used to create groups.
            type: list
            choices:
                - sites
                - tenants
                - racks
                - tags
                - device_roles
                - device_types
                - manufacturers
                - platforms
            default: []
        query_filters:
            description: List of parameters passed to the query string (Multiple values may be separated by commas)
            type: list
            default: []
        timeout:
            description: Timeout for Netbox requests in seconds
            type: int
            default: 60
        compose:
            description: List of custom ansible host vars to create from the device object fetched from NetBox
            default: {}
            type: dict
'''

EXAMPLES = '''
# netbox_inventory.yml file in YAML format
# Example command line: ansible-inventory -v --list -i netbox_inventory.yml

plugin: netbox
api_endpoint: http://localhost:8000
validate_certs: True
config_context: False
group_by:
  - device_roles
query_filters:
  - role: network-edge-router

# Query filters are passed directly as an argument to the fetching queries.
# You can repeat tags in the query string.

query_filters:
  - role: server
  - tag: web
  - tag: production

# See the NetBox documentation at https://netbox.readthedocs.io/en/latest/api/overview/
# the query_filters work as a logical **OR**
#
# Prefix any custom fields with cf_ and pass the field value with the regular NetBox query string

query_filters:
  - cf_foo: bar

# NetBox inventory plugin also supports Constructable semantics
# You can fill your hosts vars using the compose option:

plugin: netbox
compose:
  foo: last_updated
  bar: display_name
  nested_variable: rack.display_name
'''

import json
import uuid
from sys import version as python_version
from threading import Thread
from itertools import chain

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable
from ansible.module_utils.ansible_release import __version__ as ansible_version
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_text
from ansible.module_utils.urls import open_url
from ansible.module_utils.six.moves.urllib.parse import urljoin, urlencode
from ansible.module_utils.compat.ipaddress import ip_interface

ALLOWED_DEVICE_QUERY_PARAMETERS = (
    "asset_tag",
    "cluster_id",
    "device_type_id",
    "has_primary_ip",
    "is_console_server",
    "is_full_depth",
    "is_network_device",
    "is_pdu",
    "mac_address",
    "manufacturer",
    "manufacturer_id",
    "model",
    "name",
    "platform",
    "platform_id",
    "position",
    "rack_group_id",
    "rack_id",
    "role",
    "role_id",
    "serial",
    "site",
    "site_id",
    "status",
    "tag",
    "tenant",
    "tenant_id",
    "virtual_chassis_id",
)


class InventoryModule(BaseInventoryPlugin, Constructable):
    NAME = 'netbox'

    def _fetch_information(self, url):
        response = open_url(url, headers=self.headers, timeout=self.timeout, validate_certs=self.validate_certs)

        try:
            raw_data = to_text(response.read(), errors='surrogate_or_strict')
        except UnicodeError:
            raise AnsibleError("Incorrect encoding of fetched payload from NetBox API.")

        try:
            return json.loads(raw_data)
        except ValueError:
            raise AnsibleError("Incorrect JSON payload: %s" % raw_data)

    def get_resource_list(self, api_url):
        """Retrieves resource list from netbox API.
         Returns:
            A list of all resource from netbox API.
        """
        if not api_url:
            raise AnsibleError("Please check API URL in script configuration file.")

        hosts_list = []
        # Pagination.
        while api_url:
            self.display.v("Fetching: " + api_url)
            # Get hosts list.
            api_output = self._fetch_information(api_url)
            hosts_list += api_output["results"]
            api_url = api_output["next"]

        # Get hosts list.
        return hosts_list

    @property
    def group_extractors(self):
        return {
            "sites": self.extract_site,
            "tenants": self.extract_tenant,
            "racks": self.extract_rack,
            "tags": self.extract_tags,
            "disk": self.extract_disk,
            "memory": self.extract_memory,
            "vcpus": self.extract_vcpus,
            "device_roles": self.extract_device_role,
            "platforms": self.extract_platform,
            "device_types": self.extract_device_type,
            "config_context": self.extract_config_context,
            "manufacturers": self.extract_manufacturer
        }

    def extract_disk(self, host):
        return host.get("disk")

    def extract_vcpus(self, host):
        return host.get("vcpus")

    def extract_memory(self, host):
        return host.get("memory")

    def extract_platform(self, host):
        try:
            return [self.platforms_lookup[host["platform"]["id"]]]
        except Exception:
            return

    def extract_device_type(self, host):
        try:
            return [self.device_types_lookup[host["device_type"]["id"]]]
        except Exception:
            return

    def extract_rack(self, host):
        try:
            return [self.racks_lookup[host["rack"]["id"]]]
        except Exception:
            return

    def extract_site(self, host):
        try:
            return [self.sites_lookup[host["site"]["id"]]]
        except Exception:
            return

    def extract_tenant(self, host):
        try:
            return [self.tenants_lookup[host["tenant"]["id"]]]
        except Exception:
            return

    def extract_device_role(self, host):
        try:
            if 'device_role' in host:
                return [self.device_roles_lookup[host["device_role"]["id"]]]
            elif 'role' in host:
                return [self.device_roles_lookup[host["role"]["id"]]]
        except Exception:
            return

    def extract_config_context(self, host):
        try:
            if self.config_context:
                url = self.api_endpoint + "/api/dcim/devices/" + str(host["id"])
                device_lookup = self._fetch_information(url)
                return [device_lookup["config_context"]]
        except Exception:
            return

    def extract_manufacturer(self, host):
        try:
            return [self.manufacturers_lookup[host["device_type"]["manufacturer"]["id"]]]
        except Exception:
            return

    def extract_primary_ip(self, host):
        try:
            address = host["primary_ip"]["address"]
            return str(ip_interface(address).ip)
        except Exception:
            return

    def extract_primary_ip4(self, host):
        try:
            address = host["primary_ip4"]["address"]
            return str(ip_interface(address).ip)
        except Exception:
            return

    def extract_primary_ip6(self, host):
        try:
            address = host["primary_ip6"]["address"]
            return str(ip_interface(address).ip)
        except Exception:
            return

    def extract_tags(self, host):
        return host["tags"]

    def refresh_platforms_lookup(self):
        url = self.api_endpoint + "/api/dcim/platforms/?limit=0"
        platforms = self.get_resource_list(api_url=url)
        self.platforms_lookup = dict((platform["id"], platform["name"]) for platform in platforms)

    def refresh_sites_lookup(self):
        url = self.api_endpoint + "/api/dcim/sites/?limit=0"
        sites = self.get_resource_list(api_url=url)
        self.sites_lookup = dict((site["id"], site["name"]) for site in sites)

    def refresh_regions_lookup(self):
        url = self.api_endpoint + "/api/dcim/regions/?limit=0"
        regions = self.get_resource_list(api_url=url)
        self.regions_lookup = dict((region["id"], region["name"]) for region in regions)

    def refresh_tenants_lookup(self):
        url = self.api_endpoint + "/api/tenancy/tenants/?limit=0"
        tenants = self.get_resource_list(api_url=url)
        self.tenants_lookup = dict((tenant["id"], tenant["name"]) for tenant in tenants)

    def refresh_racks_lookup(self):
        url = self.api_endpoint + "/api/dcim/racks/?limit=0"
        racks = self.get_resource_list(api_url=url)
        self.racks_lookup = dict((rack["id"], rack["name"]) for rack in racks)

    def refresh_device_roles_lookup(self):
        url = self.api_endpoint + "/api/dcim/device-roles/?limit=0"
        device_roles = self.get_resource_list(api_url=url)
        self.device_roles_lookup = dict((device_role["id"], device_role["name"]) for device_role in device_roles)

    def refresh_device_types_lookup(self):
        url = self.api_endpoint + "/api/dcim/device-types/?limit=0"
        device_types = self.get_resource_list(api_url=url)
        self.device_types_lookup = dict((device_type["id"], device_type["model"]) for device_type in device_types)

    def refresh_manufacturers_lookup(self):
        url = self.api_endpoint + "/api/dcim/manufacturers/?limit=0"
        manufacturers = self.get_resource_list(api_url=url)
        self.manufacturers_lookup = dict((manufacturer["id"], manufacturer["name"]) for manufacturer in manufacturers)

    def refresh_lookups(self):
        lookup_processes = (
            self.refresh_sites_lookup,
            self.refresh_regions_lookup,
            self.refresh_tenants_lookup,
            self.refresh_racks_lookup,
            self.refresh_device_roles_lookup,
            self.refresh_platforms_lookup,
            self.refresh_device_types_lookup,
            self.refresh_manufacturers_lookup,
        )

        thread_list = []
        for p in lookup_processes:
            t = Thread(target=p)
            thread_list.append(t)
            t.start()

        for thread in thread_list:
            thread.join()

    def validate_query_parameters(self, x):
        if not (isinstance(x, dict) and len(x) == 1):
            self.display.warning("Warning query parameters %s not a dict with a single key." % x)
            return

        k = tuple(x.keys())[0]
        v = tuple(x.values())[0]

        if not (k in ALLOWED_DEVICE_QUERY_PARAMETERS or k.startswith("cf_")):
            msg = "Warning: %s not in %s or starting with cf (Custom field)" % (k, ALLOWED_DEVICE_QUERY_PARAMETERS)
            self.display.warning(msg=msg)
            return
        return k, v

    def refresh_url(self):
        query_parameters = [("limit", 0)]
        if self.query_filters:
            query_parameters.extend(filter(lambda x: x,
                                           map(self.validate_query_parameters, self.query_filters)))
        self.device_url = self.api_endpoint + "/api/dcim/devices/?" + urlencode(query_parameters)
        self.virtual_machines_url = self.api_endpoint + "/api/virtualization/virtual-machines/?" + urlencode(query_parameters)

    def fetch_hosts(self):
        return chain(
            self.get_resource_list(self.device_url),
            self.get_resource_list(self.virtual_machines_url),
        )

    def extract_name(self, host):
        # An host in an Ansible inventory requires an hostname.
        # name is an unique but not required attribute for a device in NetBox
        # We default to an UUID for hostname in case the name is not set in NetBox
        return host["name"] or str(uuid.uuid4())

    def add_host_to_groups(self, host, hostname):
        for group in self.group_by:
            sub_groups = self.group_extractors[group](host)

            if not sub_groups:
                continue

            for sub_group in sub_groups:
                group_name = "_".join([group, sub_group])
                self.inventory.add_group(group=group_name)
                self.inventory.add_host(group=group_name, host=hostname)

    def _fill_host_variables(self, host, hostname):
        for attribute, extractor in self.group_extractors.items():
            if not extractor(host):
                continue
            self.inventory.set_variable(hostname, attribute, extractor(host))

        if self.extract_primary_ip(host):
            self.inventory.set_variable(hostname, "ansible_host", self.extract_primary_ip(host=host))

        if self.extract_primary_ip4(host):
            self.inventory.set_variable(hostname, "primary_ip4", self.extract_primary_ip4(host=host))

        if self.extract_primary_ip6(host):
            self.inventory.set_variable(hostname, "primary_ip6", self.extract_primary_ip6(host=host))

    def main(self):
        self.refresh_lookups()
        self.refresh_url()
        hosts_list = self.fetch_hosts()

        for host in hosts_list:
            hostname = self.extract_name(host=host)
            self.inventory.add_host(host=hostname)
            self._fill_host_variables(host=host, hostname=hostname)

            strict = self.get_option("strict")

            # Composed variables
            self._set_composite_vars(self.get_option('compose'), host, hostname, strict=strict)
            # Complex groups based on jinja2 conditionals, hosts that meet the conditional are added to group
            self._set_composite_vars(self.get_option('compose'), host, hostname, strict=strict)

            # Create groups based on variable values and add the corresponding hosts to it
            self._add_host_to_keyed_groups(self.get_option('keyed_groups'), host, hostname, strict=strict)
            self.add_host_to_groups(host=host, hostname=hostname)

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        self._read_config_data(path=path)

        # Netbox access
        token = self.get_option("token")
        # Handle extra "/" from api_endpoint configuration and trim if necessary, see PR#49943
        self.api_endpoint = self.get_option("api_endpoint").strip('/')
        self.timeout = self.get_option("timeout")
        self.validate_certs = self.get_option("validate_certs")
        self.config_context = self.get_option("config_context")
        self.headers = {
            'Authorization': "Token %s" % token,
            'User-Agent': "ansible %s Python %s" % (ansible_version, python_version.split(' ')[0]),
            'Content-type': 'application/json'
        }

        # Filter and group_by options
        self.group_by = self.get_option("group_by")
        self.query_filters = self.get_option("query_filters")
        self.main()
