#
# (c) 2017 Serghei Anicheev, <serghei.anicheev@gmail.com>
#
# This file is part of Ansible
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
#

import json
import os
from time import sleep

try:
    from cm_api.endpoints.cms import *
    from cm_api.endpoints.clusters import *
    from cm_api.endpoints.services import *
    from cm_api.endpoints.types import *
    from cm_api.api_client import *
    python_cm_installed = True
except ImportError:
    python_cm_installed = False

class Cloudera(object):
    def __init__(self, module, host, port, username, password, api_version, use_tls):
        self.module = module
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.api_version = api_version
        self.use_tls = use_tls

### Checks if service type available
    def validate_service_type(self, cluster_obj, service_type):
        if service_type not in cluster_obj.get_service_types():
            raise Exception('Not valid service type - %s' % service_type)

### Checks if role type available
    def validate_role_type(self, service_obj, role_type):
        if role_type not in service_obj.get_role_types():
            raise Exception('Not valid role type - %s' % role_type)

### Reads configuration file specified by config_path and returns its content.
### File should be in JSON format.
    def load_config(self, config_path):
        config_content = None
        if os.path.exists(config_path):
            fd = open(config_path, 'r')
            config_content = json.load(fd)
            fd.close()
        else:
            self.module.log('No such configuration file -  %s or there are no read permissions' % config_path)
        return config_conten

### Checks if existing config is up-to-date
    def update_config(self, obj, current_config, config_path):
        updated_config = self.load_config(config_path)
        updated = False
        if updated_config is not None:
            if all(prop in current_config.items() for prop in updated_config.items()):
                self.module.log('Already have up-to-date config. Nothing to do')
            else:
                obj.update_config(updated_config)
                updated = True
        return updated

### Returns license info
    def license_state(self, cm):
        license = None
        try:
            license = cm.get_license()
        except Exception:
            self.module.log('Cloudera Manager is in express state!')
        return license

### Returns connection objec
    def connect(self):
        connection = ApiResource(
            self.host, server_port = self.port, username = self.username, password = self.password,
            use_tls = self.use_tls, version = self.api_version
        )
        return connection

### Returns instance of cloudera manager
    def cloudera_manager(self, connection):
        cm = connection.get_cloudera_manager()
        return cm

### Returns cluster objec
    def get_cluster(self, connection, cluster_name):
        cluster = None
        try:
            cluster = connection.get_cluster(cluster_name)
        except Exception:
            self.module.log('No cluster found with name - %s' % cluster_name)
        return cluster

### Returns service object if found.
    def get_service_by_type(self, obj, service_type):
        all_services = obj.get_all_services()
        service_info = filter(lambda svc: svc.type == service_type, all_services)
        if len(service_info) == 0:
            raise Exception('No service found with type - %s' % service_type)
        return service_info[0]

### Return list of host_ids for specific role_type
    def get_hostid_by_role_type(self, service_obj, role_type):
        role_objects_list = service_obj.get_roles_by_type(role_type)
        if len(role_objects_list) == 0:
            raise 'No existing role types found!'
        host_ids = map(lambda role_obj: role_obj.hostRef.hostId, role_objects_list)
        return host_ids

### Return host_id for specific hostname
    def get_hostid_by_hostname(self, connection, hostname):
        try:
            host_id = connection.get_host(hostname).hostId
        except Exception:
            raise Exception('No host found for hostname - %s' % hostname)
        return host_id

### Returnds dict of all provisioned hosts in form : { hostId : hostname }
    def get_hostid_hostname_mapping(self, connection):
        existing_host_ids = connection.get_all_hosts()
        mapping = {}
        for host_id in existing_host_ids:
            mapping[host_id.hostId] = host_id.hostname
        return mapping

### Returns host_ids of all hosts in cluster
    def list_cluster_member_ids(self, cluster_obj):
        cluster_members = cluster_obj.list_hosts()
        host_ids = map(lambda host_ref: host_ref.hostId, cluster_members)
        return host_ids

### Reverses dict { key:value } to { value:key }
    def reversed_dictionary(self, dictionary):
        rev = {}
        for key, value in dictionary.items():
            rev[value] = key
        return rev

### Removes specific keys from dic
    def filter_dictionary(self, dictionary, keys):
        filtered = filter(lambda key: dictionary.pop(key, None), keys)
        return filtered

###
    def installed_hosts_globally(self, connection, hostnames):
        mapping = self.get_hostid_hostname_mapping(connection)
        reversed_mapping = self.reversed_dictionary(mapping)
        installed_hosts = filter(lambda hostname: reversed_mapping.pop(hostname, None), hostnames)
        return installed_hosts

### Returns host_ids which is provisioned but not in the cluster
    def installed_hosts_not_in_cluster(self, connection, cluster_obj):
        mapping = self.get_hostid_hostname_mapping(connection)
        host_ids = self.list_cluster_member_ids(cluster_obj)
        for host_id in host_ids:
            mapping.pop(host_id, None)
        return mapping

### Returns service setup info
    def get_service_setup_info(self, service_name, service_type):
        service_info = ApiServiceSetupInfo(name=service_name, type=service_type)
        return service_info
