#!/usr/bin/env python

'''
Azure external inventory script
=======================================

Generates inventory that Ansible can understand by making API request to Azure using the azure python library.

NOTE: This script assumes Ansible is being executed where azure is already
installed.

    pip install azure

Adapted from the ansible Linode plugin by Dan Slimmon.
'''

# (c) 2014, Martin Joehren
#
# This file is part of Ansible,
#
# Ansible is free software: you can redistribute it and/or modify
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

# #####################################################################

# Standard imports
import sys
import re
import argparse
import os
if sys.version_info < (3,):
    from urlparse import urlparse
    import ConfigParser
else:
    from configparser import ConfigParser
    from urllib.parse import urlparse

from time import time
try:
    import json
except ImportError:
    import simplejson as json

try:
    import azure
    from azure.servicemanagement import ServiceManagementService
    from azure import _USER_AGENT_STRING, _update_request_uri_query
    from azure.http import HTTPResponse
    from azure.http import HTTPError
except ImportError as e:
    print("failed=True msg='`azure` library required for this script'")
    sys.exit(1)

# monkey patch for temporary redirects until https://github.com/Azure/azure-sdk-for-python/issues/129 is fixed
def perform_request_new(self, request):
    connection = self.get_connection(request)
    try:
        connection.putrequest(request.method, request.path)

        if not self.use_httplib:
            if self.proxy_host and self.proxy_user:
                connection.set_proxy_credentials(
                    self.proxy_user, self.proxy_password)

        self.send_request_headers(connection, request.headers)
        self.send_request_body(connection, request.body)

        resp = connection.getresponse()
        self.status = int(resp.status)
        self.message = resp.reason
        self.respheader = headers = resp.getheaders()

        # for consistency across platforms, make header names lowercase
        for i, value in enumerate(headers):
            headers[i] = (value[0].lower(), value[1])

        respbody = None
        if resp.length is None:
            respbody = resp.read()
        elif resp.length > 0:
            respbody = resp.read(resp.length)
        response = HTTPResponse(
            int(resp.status), resp.reason, headers, respbody)
        if self.status == 307:
            print("Temporary redirect detected...")
            new_url = urlparse(dict(headers)['location'])
            request.host = new_url.hostname
            request.path = new_url.path
            if new_url.query:
                request.path += '?' + new_url.query
            request.path, request.query = _update_request_uri_query(request)
            return self.perform_request(request)
        if self.status >= 300:
            raise HTTPError(self.status, self.message,
                            self.respheader, respbody)

        return response
    finally:
        connection.close()

azure.http.httpclient._HTTPClient.perform_request = perform_request_new

class AzureInventory(object):

    def _empty_inventory(self):
        return {"_meta" : {"hostvars" : {}}}

    def __init__(self):
        """Main execution path."""
        # Inventory grouped by display group
        self.inventory = self._empty_inventory()
        # Index of deployment name -> host
        self.index = {}

        # all instance attributes
        self.subscription_id = u''
        self.certificate_path = u''
        self.cache_path_cache = u''
        self.cache_path_index = u''
        self.cache_max_age = 300

        # Read settings and parse CLI arguments
        self.read_settings()
        self.read_environment()
        self.parse_cli_args()

        # Initialize Azure ServiceManagementService
        self.sms = ServiceManagementService(self.subscription_id, self.certificate_path)

        # Cache
        if self.args.refresh_cache:
            self.do_api_calls_update_cache()
        elif not self.is_cache_valid():
            self.do_api_calls_update_cache()

        # Data to print
        if self.args.host:
            data_to_print = self.get_host_info()
        elif self.args.list:
            # Display list of roles for inventory
            if self.inventory == self._empty_inventory():
                data_to_print = self.get_inventory_from_cache()
            else:
                data_to_print = self.json_format_dict(self.inventory, True)

        print(data_to_print)

    def get_host_info(self):
        ''' Get variables about a specific host '''

        if len(self.index) == 0:
            # Need to load index from cache
            self.load_index_from_cache()

        if not self.args.host in self.index:
            # try updating the cache
            self.do_api_calls_update_cache()
            if not self.args.host in self.index:
                # host migh not exist anymore
                return self.json_format_dict({}, True)

        (cloud_service_name, deployment_name, public_dns_name) = self.index[self.args.host]

        role = self.sms.get_role(self.args.host, cloud_service_name, deployment_name)
        return self.get_host_info_dict_from_instance(role, public_dns_name)

    def is_cache_valid(self):
        """Determines if the cache file has expired, or if it is still valid."""
        if os.path.isfile(self.cache_path_cache):
            mod_time = os.path.getmtime(self.cache_path_cache)
            current_time = time()
            if (mod_time + self.cache_max_age) > current_time:
                if os.path.isfile(self.cache_path_index):
                    return True
        return False

    def read_settings(self):
        """Reads the settings from the .ini file."""
        config = ConfigParser.SafeConfigParser()
        config.read(os.path.dirname(os.path.realpath(__file__)) + '/windows_azure.ini')

        config = ConfigParser.SafeConfigParser()
        azure_default_ini_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'windows_azure.ini')
        azure_ini_path = os.environ.get('AZURE_INI_PATH', azure_default_ini_path)
        config.read(azure_ini_path)

        # Credentials related
        if config.has_option('azure', 'subscription_id'):
            self.subscription_id = config.get('azure', 'subscription_id')
        if config.has_option('azure', 'certificate_path'):
            self.certificate_path = config.get('azure', 'certificate_path')

        # Cache related
        if config.has_option('azure', 'cache_path'):
            cache_path = config.get('azure', 'cache_path')
            self.cache_path_cache = cache_path + "/ansible-azure.cache"
            self.cache_path_index = cache_path + "/ansible-azure.index"
        if config.has_option('azure', 'cache_max_age'):
            self.cache_max_age = config.getint('azure', 'cache_max_age')

    def read_environment(self):
        ''' Reads the settings from environment variables '''
        # Credentials
        if os.getenv("AZURE_SUBSCRIPTION_ID"):
            self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        if os.getenv("AZURE_MANAGEMENT_CERTIFICATE"):
            self.certificate_path = os.getenv("AZURE_MANAGEMENT_CERTIFICATE")


    def parse_cli_args(self):
        """Command line argument processing"""
        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on Azure')
        parser.add_argument('--list', action='store_true', default=True,
                            help='List roles (default: True)')
        parser.add_argument('--refresh-cache', action='store_true', default=False,
                            help='Force refresh of cache by making API requests to Azure (default: False - use cache files)')

        parser.add_argument('--host', action='store_true', default=False, help='Get all the variables about a specific role')
        self.args = parser.parse_args()

    def do_api_calls_update_cache(self):
        """Do API calls, and save data in cache files."""
        self.add_cloud_services()
        self.write_to_cache(self.inventory, self.cache_path_cache)
        self.write_to_cache(self.index, self.cache_path_index)

    def add_cloud_services(self):
        """Makes an Azure API call to get the list of cloud services."""
        try:
            for cloud_service in self.sms.list_hosted_services():
                self.add_deployments(cloud_service)
        except azure.WindowsAzureError as e:
            self._print_error_and_exit("Looks like Azure's API is down.", e)

    def add_deployments(self, cloud_service):
        """Makes an Azure API call to get the list of virtual machines associated with a cloud service"""
        try:
            for deployment in self.sms.get_hosted_service_properties(cloud_service.service_name, embed_detail=True).deployments.deployments:
                if deployment.deployment_slot == "Production":
                    for role in deployment.role_instance_list:
                        self.add_deployment(cloud_service, deployment, role)
        except azure.WindowsAzureError as e:
            self._print_error_and_exit("Looks like Azure's API is down.", e)

    def get_roles(self):
        deployment_info = None
        try:
            deployment_info = self.sms.get_deployment_by_name(self.cloud_service_name, self.deployment_name)
        except azure.WindowsAzureError:    #not  found
            pass
        roles = []
        if deployment_info:
            for role in deployment_info.role_instance_list:
                role_dict = dict(role_name=role.role_name)
                endpoints = []
                for endpoint in role.instance_endpoints:
                    if endpoint.name.lower() == "ssh":
                        role_dict['ssh'] = endpoint
                    endpoints.append(endpoint)
                role_dict['endpoints'] = endpoints
                role_dict['public_dns_name'] = urlparse(deployment_info.url).hostname
                roles.append(role_dict)
        return self.json_format_dict(roles)

    def add_deployment(self, cloud_service, deployment, role):
        """Adds a deployment to the inventory and index"""

        public_dns_name = urlparse(deployment.url).hostname
        dest = role.role_name

        # Add to index
        self.index[dest] = [cloud_service.service_name, deployment.name, public_dns_name]

        # List of all azure deployments
        self.push(self.inventory, "azure", dest)

        # Inventory: Group by service name
        self.push(self.inventory, self.to_safe(cloud_service.service_name), dest)

        # Inventory: Group by region
        self.push(self.inventory, self.to_safe(cloud_service.hosted_service_properties.location), dest)


        # Inventory: Group by affinity group
        self.push(self.inventory, self.to_safe(cloud_service.hosted_service_properties.affinity_group), dest)


        self.inventory["_meta"]["hostvars"][dest] = self.get_host_info_dict_from_instance(role, public_dns_name)

    def get_host_info_dict_from_instance(self, role, public_dns_name):
        instance_vars = {}
        instance_vars['ansible_ssh_port'] = public_dns_name
        for endpoint in role.instance_endpoints:
            if endpoint.name.lower() == "ssh":
                instance_vars['ansible_ssh_port'] = endpoint.public_port
                break
        instance_vars['ansible_ssh_user'] = "azureuser"
        instance_vars['ansible_ssh_private_key_file'] = self.certificate_path
        instance_vars['ansible_ssh_host'] = public_dns_name

        instance_vars['role'] = json.loads(json.dumps(role, default=lambda o: o.__dict__))

        return instance_vars

    def push(self, my_dict, key, element):
        """Pushed an element onto an array that may not have been defined in the dict."""
        if key in my_dict:
            my_dict[key].append(element);
        else:
            my_dict[key] = [element]

    def get_inventory_from_cache(self):
        """Reads the inventory from the cache file and returns it as a JSON object."""
        cache = open(self.cache_path_cache, 'r')
        json_inventory = cache.read()
        return json_inventory

    def load_index_from_cache(self):
        """Reads the index from the cache file and sets self.index."""
        cache = open(self.cache_path_index, 'r')
        json_index = cache.read()
        self.index = json.loads(json_index)

    def write_to_cache(self, data, filename):
        """Writes data in JSON format to a file."""
        json_data = self.json_format_dict(data, True)
        cache = open(filename, 'w')
        cache.write(json_data)
        cache.close()

    def to_safe(self, word):
        """Escapes any characters that would be invalid in an ansible group name."""
        return re.sub("[^A-Za-z0-9\-]", "_", word)

    def json_format_dict(self, data, pretty=False):
        """Converts a dict to a JSON object and dumps it as a formatted string."""
        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)

    def _print_error_and_exit(self, msg, error):
        print(msg)
        print("")
        print(unicode(error))
        sys.exit(1)


AzureInventory()
