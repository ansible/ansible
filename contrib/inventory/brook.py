#!/usr/bin/env python
# Copyright 2016 Doalitic.
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

"""
Brook.io external inventory script
==================================

Generates inventory that Ansible can understand by making API requests to Brook.io via the libbrook
library. Hence, such dependency must be installed in the system to run this script.

The default configuration file is named 'brook.ini' and is located alongside this script. You can
choose any other file by setting the BROOK_INI_PATH environment variable.

If param 'project_id' is left blank in 'brook.ini', the inventory includes all the instances in
projects where the requesting user belongs. Otherwise, only instances from the given project are
included, provided the requesting user belongs to it.

The following variables are established for every host. They can be retrieved from the hostvars
dictionary.
 - brook_pid: str
 - brook_name: str
 - brook_description: str
 - brook_project: str
 - brook_template: str
 - brook_region: str
 - brook_zone: str
 - brook_status: str
 - brook_tags: list(str)
 - brook_internal_ips: list(str)
 - brook_external_ips: list(str)
 - brook_created_at
 - brook_updated_at
 - ansible_ssh_host

Instances are grouped by the following categories:
 - tag:
   A group is created for each tag. E.g. groups 'tag_foo' and 'tag_bar' are created if there exist
   instances with tags 'foo' and/or 'bar'.
 - project:
   A group is created for each project. E.g. group 'project_test' is created if a project named
   'test' exist.
 - status:
   A group is created for each instance state. E.g. groups 'status_RUNNING' and 'status_PENDING'
   are created if there are instances in running and pending state.

Examples:
  Execute uname on all instances in project 'test'
  $ ansible -i brook.py project_test -m shell -a "/bin/uname -a"

  Install nginx on all debian web servers tagged with 'www'
  $ ansible -i brook.py tag_www -m apt -a "name=nginx state=present"

  Run site.yml playbook on web servers
  $ ansible-playbook -i brook.py site.yml -l tag_www

Support:
  This script is tested on Python 2.7 and 3.4. It may work on other versions though.

Author: Francisco Ros <fjros@doalitic.com>
Version: 0.2
"""


import sys
import os

try:
    from ConfigParser import SafeConfigParser as ConfigParser
except ImportError:
    from configparser import ConfigParser

try:
    import json
except ImportError:
    import simplejson as json

try:
    import libbrook
except:
    sys.exit('Brook.io inventory script requires libbrook. See https://github.com/doalitic/libbrook')


class BrookInventory:

    _API_ENDPOINT = 'https://api.brook.io'

    def __init__(self):
        self._configure_from_file()
        self.client = self.get_api_client()
        self.inventory = self.get_inventory()

    def _configure_from_file(self):
        """Initialize from .ini file.

        Configuration file is assumed to be named 'brook.ini' and to be located on the same
        directory than this file, unless the environment variable BROOK_INI_PATH says otherwise.
        """

        brook_ini_default_path = \
            os.path.join(os.path.dirname(os.path.realpath(__file__)), 'brook.ini')
        brook_ini_path = os.environ.get('BROOK_INI_PATH', brook_ini_default_path)

        config = ConfigParser(defaults={
            'api_token': '',
            'project_id': ''
        })
        config.read(brook_ini_path)
        self.api_token = config.get('brook', 'api_token')
        self.project_id = config.get('brook', 'project_id')

        if not self.api_token:
            sys.exit('You must provide (at least) your Brook.io API token to generate the dynamic '
                     'inventory.')

    def get_api_client(self):
        """Authenticate user via the provided credentials and return the corresponding API client.
        """

        # Get JWT token from API token
        #
        unauthenticated_client = libbrook.ApiClient(host=self._API_ENDPOINT)
        auth_api = libbrook.AuthApi(unauthenticated_client)
        api_token = libbrook.AuthTokenRequest()
        api_token.token = self.api_token
        jwt = auth_api.auth_token(token=api_token)

        # Create authenticated API client
        #
        return libbrook.ApiClient(host=self._API_ENDPOINT,
                                  header_name='Authorization',
                                  header_value='Bearer %s' % jwt.token)

    def get_inventory(self):
        """Generate Ansible inventory.
        """

        groups = dict()
        meta = dict()
        meta['hostvars'] = dict()

        instances_api = libbrook.InstancesApi(self.client)
        projects_api = libbrook.ProjectsApi(self.client)
        templates_api = libbrook.TemplatesApi(self.client)

        # If no project is given, get all projects the requesting user has access to
        #
        if not self.project_id:
            projects = [project.id for project in projects_api.index_projects()]
        else:
            projects = [self.project_id]

        # Build inventory from instances in all projects
        #
        for project_id in projects:
            project = projects_api.show_project(project_id=project_id)
            for instance in instances_api.index_instances(project_id=project_id):
                # Get template used for this instance if known
                template = templates_api.show_template(template_id=instance.template) if instance.template else None

                # Update hostvars
                try:
                    meta['hostvars'][instance.name] = \
                        self.hostvars(project, instance, template, instances_api)
                except libbrook.rest.ApiException:
                    continue

                # Group by project
                project_group = 'project_%s' % project.name
                if project_group in groups:
                    groups[project_group].append(instance.name)
                else:
                    groups[project_group] = [instance.name]

                # Group by status
                status_group = 'status_%s' % meta['hostvars'][instance.name]['brook_status']
                if status_group in groups:
                    groups[status_group].append(instance.name)
                else:
                    groups[status_group] = [instance.name]

                # Group by tags
                tags = meta['hostvars'][instance.name]['brook_tags']
                for tag in tags:
                    tag_group = 'tag_%s' % tag
                    if tag_group in groups:
                        groups[tag_group].append(instance.name)
                    else:
                        groups[tag_group] = [instance.name]

        groups['_meta'] = meta
        return groups

    def hostvars(self, project, instance, template, api):
        """Return the hostvars dictionary for the given instance.

        Raise libbrook.rest.ApiException if it cannot retrieve all required information from the
        Brook.io API.
        """

        hostvars = instance.to_dict()
        hostvars['brook_pid'] = hostvars.pop('pid')
        hostvars['brook_name'] = hostvars.pop('name')
        hostvars['brook_description'] = hostvars.pop('description')
        hostvars['brook_project'] = hostvars.pop('project')
        hostvars['brook_template'] = hostvars.pop('template')
        hostvars['brook_region'] = hostvars.pop('region')
        hostvars['brook_zone'] = hostvars.pop('zone')
        hostvars['brook_created_at'] = hostvars.pop('created_at')
        hostvars['brook_updated_at'] = hostvars.pop('updated_at')
        del hostvars['id']
        del hostvars['key']
        del hostvars['provider']
        del hostvars['image']

        # Substitute identifiers for names
        #
        hostvars['brook_project'] = project.name
        hostvars['brook_template'] = template.name if template else None

        # Retrieve instance state
        #
        status = api.status_instance(project_id=project.id, instance_id=instance.id)
        hostvars.update({'brook_status': status.state})

        # Retrieve instance tags
        #
        tags = api.instance_tags(project_id=project.id, instance_id=instance.id)
        hostvars.update({'brook_tags': tags})

        # Retrieve instance addresses
        #
        addresses = api.instance_addresses(project_id=project.id, instance_id=instance.id)
        internal_ips = [address.address for address in addresses if address.scope == 'internal']
        external_ips = [address.address for address in addresses
                        if address.address and address.scope == 'external']
        hostvars.update({'brook_internal_ips': internal_ips})
        hostvars.update({'brook_external_ips': external_ips})
        try:
            hostvars.update({'ansible_ssh_host': external_ips[0]})
        except IndexError:
            raise libbrook.rest.ApiException(status='502', reason='Instance without public IP')

        return hostvars


# Run the script
#
brook = BrookInventory()
print(json.dumps(brook.inventory))
