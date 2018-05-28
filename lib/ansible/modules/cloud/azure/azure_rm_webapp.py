#!/usr/bin/python
#
# Copyright (c) 2018 Yunge Zhu, <yungez@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_webapp
version_added: "2.7"
short_description: Manage Web App instance.
description:
    - Create, update and delete instance of Web App.

options:
    resource_group:
        description:
            - Name of the resource group to which the resource belongs.
        required: True
    name:
        description:
            - Unique name of the app to create or update. To create or update a deployment slot, use the {slot} parameter.
        required: True

    location:
        description:
            - Resource location. If not set, location from the resource group will be used as default.

    plan:
        description:
            - App service plan. Required for creation.
            - It can be name of existing app service plan in same resource group as web app.
            - "It can be resource id of existing app service plan. eg.,
              /subscriptions/<subs_id>/resourceGroups/<resource_group>/providers/Microsoft.Web/serverFarms/<plan_name>"
            - It can be a dict which contains C(name), C(resource_group), C(sku), C(is_linux) and C(number_of_workers).
              name.  Name of app service plan.
              resource_group. Resource group name of app service plan.
              sku. SKU of app service plan. For allowed sku, please refer to https://azure.microsoft.com/en-us/pricing/details/app-service/linux/.
              is_linux. Indicate is linux app service plan. type bool. default False.
              number_of_workers. Number of workers.

    windows_framework:
        description:
            - Describe windows web app framework. See https://docs.microsoft.com/en-us/azure/app-service/app-service-web-overview for more info.
            - Can set mulitple framework at same time.
            - Suboption java_version is mutually exclusive with other suboptions
        suboptions:
            net_framework_version:
                description:
                    - The version used to run your web app if using .NET Framework, e.g., 'v4.0' for .NET 4.6 and 'v3.0' for .NET 3.5
                    - Only applies for windows web app.
                    - Mutually exclusive with java_version

            java_version:
                description:
                    - The version used to run your web app if using Java, e.g., '1.7' for Java 7, '1.8' for Java 8.
                    - Only applies for windows web app.
                    - Mutually exclusive with other suboptions

            php_version:
                description:
                    - The version used to run your web app if using PHP, e.g., 5.5, 5.6, 7.0.
                    - Only applies for windows web app.
                    - Mutually exclusive with java_version

            python_version:
                description:
                    - The version used to run your web app if using Python, e.g., 2.7, 3.4.
                    - Only applies for windows web app.
                    - Mutually exclusive with java_version

            node_version:
                description:
                    - The version used to run your web app if using nodejs, e.g., 6.6, 6.9.
                    - Only applies for windows web app.
                    - Mutually exclusive with java_version


    linux_framework:
        description:
            - The runtime stack used for your linux-based webapp.
            - Only applies for linux web app. See https://aka.ms/linux-stacks for more info.
            - Mutually exclusive with windows_framework
        suboptions:
            name:
                description:
                    - Name of linux runtime framework.
                choices:
                    - ruby
                    - node
                    - php
                    - dotnetcore
                    - java
            version:
                description:
                    - Version of linux runtime framework.
                    - Please see https://aka.ms/linux-stacks for supported value.

    java_container_settings:
        description: Java container settings.
        suboptions:
            name:
                description: The java container, e.g., Tomcat, Jetty.
            value:
                description: The version of the java container, e.g., '8.0.23' for Tomcat.

    container_settings:
        description: Web app container settings.
        suboptions:
            name:
                description: Name of container. eg. imagename:tag
            registry_server_url:
                description: Container registry server url. eg. mydockerregistry.io
            registry_server_user:
                description: The container registry server user name.
            registry_server_password:
                description:
                    - The container registry server password.

    scm_type:
        description:
            - Repository type of deployment source. Eg. LocalGit, GitHub.

    deployment_source:
        description:
            - Deployment source for git
        suboptions:
            url:
                description:
                    - Repository url of deployment source.

            branch:
                description:
                    - The branch name of the repository.
    startup_file:
        description:
            - The web's startup file.
            - This only applies for linux web app.

    client_affinity_enabled:
        description:
            - "True to enable client affinity; False to stop sending session affinity cookies, which route client requests in the
              same session to the same instance."
        type: bool
        default: True

    https_only:
        description:
            - Configures web site to accept only https requests.
        type: bool

    dns_registration:
        description:
            - If true web app hostname is not registered with DNS on creation.
        type: bool

    skip_custom_domain_verification:
        description:
            - If true, custom (non *.azurewebsites.net) domains associated with web app are not verified.
        type: bool

    ttl_in_seconds:
        description:
            - Time to live in seconds for web app default domain name.

    app_settings:
        description:
            - Configure web app application settings. Suboptions are in key value pair format.

    purge_app_settings:
        description:
            - Purge any existing application settings. Replace web app application settings with app_settings.
        type: bool

    state:
      description:
        - Assert the state of the Web App.
        - Use 'present' to create or update an Web App and 'absent' to delete it.
      default: present
      choices:
        - absent
        - present

extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Yunge Zhu(@yungezz)"

'''

EXAMPLES = '''
    - name: Create a windows web app with non-exist app service plan
      azure_rm_webapp:
        resource_group: myresourcegroup
        name: mywinwebapp
        plan:
          resource_group: myappserviceplan_rg
          name: myappserviceplan
          is_linux: false
          sku: S1

    - name: Create a docker web app with some app settings, with docker image
      azure_rm_webapp:
        resource_group: myresourcegroup
        name: mydockerwebapp
        plan:
          resource_group: appserviceplan_test
          name: myappplan
          is_linux: true
          sku: S1
          number_of_workers: 2
        app_settings:
          testkey: testvalue
          testkey2: testvalue2
        container_settings:
          name: ansible/ansible:ubuntu1404

    - name: Create a docker web app with private acr registry
      azure_rm_webapp:
        resource_group: myresourcegroup
        name: mydockerwebapp
        plan: myappplan
        app_settings:
          testkey: testvalue
        container_settings:
          name: ansible/ubuntu1404
          registry_server_url: myregistry.io
          registry_server_user: user
          registry_server_password: pass

    - name: Create a linux web app with Node 6.6 framework
      azure_rm_webapp:
        resource_group: myresourcegroup
        name: mylinuxwebapp
        plan:
          resource_group: appserviceplan_test
          name: myappplan
        app_settings:
          testkey: testvalue
        linux_framework:
          name: node
          version: 6.6
'''

RETURN = '''
azure_webapp:
    description: Facts about the current state of the web app.
    returned: always
    type: dict
    sample: {
        "availability_state": "Normal",
        "client_affinity_enabled": true,
        "client_cert_enabled": false,
        "container_size": 0,
        "daily_memory_time_quota": 0,
        "default_host_name": "ansiblewindowsaaa.azurewebsites.net",
        "enabled": true,
        "enabled_host_names": [
            "ansiblewindowsaaa.azurewebsites.net",
            "ansiblewindowsaaa.scm.azurewebsites.net"
        ],
        "host_name_ssl_states": [
            {
                "host_type": "Standard",
                "name": "ansiblewindowsaaa.azurewebsites.net",
                "ssl_state": "Disabled"
            },
            {
                "host_type": "Repository",
                "name": "ansiblewindowsaaa.scm.azurewebsites.net",
                "ssl_state": "Disabled"
            }
        ],
        "host_names": [
            "ansiblewindowsaaa.azurewebsites.net"
        ],
        "host_names_disabled": false,
        "id": "/subscriptions/<subscription_id>/resourceGroups/ansiblewebapp1/providers/Microsoft.Web/sites/ansiblewindowsaaa",
        "kind": "app",
        "last_modified_time_utc": "2018-05-14T04:50:54.473333Z",
        "location": "East US",
        "name": "ansiblewindowsaaa",
        "outbound_ip_addresses": "52.170.7.25,52.168.75.147,52.179.5.98,52.179.1.81,52.179.4.232",
        "repository_site_name": "ansiblewindowsaaa",
        "reserved": false,
        "resource_group": "ansiblewebapp1",
        "scm_site_also_stopped": false,
        "server_farm_id": "/subscriptions/<subscription_id>/resourceGroups/test/providers/Microsoft.Web/serverfarms/plan1",
        "state": "Running",
        "tags": {},
        "type": "Microsoft.Web/sites",
        "usage_state": "Normal"
    }
'''

import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrestazure.azure_operation import AzureOperationPoller
    from msrest.serialization import Model
    from azure.mgmt.web.models import (
        site_config, app_service_plan, Site,
        AppServicePlan, SkuDescription, NameValuePair
    )
except ImportError:
    # This is handled in azure_rm_common
    pass

container_settings_spec = dict(
    name=dict(type='str', required=True),
    registry_server_url=dict(type='str'),
    registry_server_user=dict(type='str'),
    registry_server_password=dict(type='str')
)

java_container_settings_spec = dict(
    name=dict(type='str', required=True),
    version=dict(type='str', required=True)
)

deployment_source_spec = dict(
    url=dict(type='str'),
    branch=dict(type='str')
)

linux_framework_spec = dict(
    name=dict(type='str', required=True),
    version=dict(type='str', required=True)
)

windows_framework_spec = dict(
    net_framework_version=dict(type='str'),
    php_version=dict(type='str'),
    python_version=dict(type='str'),
    node_version=dict(type='str'),
    java_version=dict(type='str')
)


def _normalize_sku(sku):
    if sku is None:
        return sku

    sku = sku.upper()
    if sku == 'FREE':
        return 'F1'
    elif sku == 'SHARED':
        return 'D1'
    return sku


def get_sku_name(tier):
    tier = tier.upper()
    if tier == 'F1' or tier == "FREE":
        return 'FREE'
    elif tier == 'D1' or tier == "SHARED":
        return 'SHARED'
    elif tier in ['B1', 'B2', 'B3', 'BASIC']:
        return 'BASIC'
    elif tier in ['S1', 'S2', 'S3']:
        return 'STANDARD'
    elif tier in ['P1', 'P2', 'P3']:
        return 'PREMIUM'
    elif tier in ['P1V2', 'P2V2', 'P3V2']:
        return 'PREMIUMV2'
    else:
        return None


class Actions:
    NoAction, CreateOrUpdate, UpdateAppSettings, Delete = range(4)


class AzureRMWebApps(AzureRMModuleBase):
    """Configuration class for an Azure RM Web App resource"""

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str',
                required=True
            ),
            location=dict(
                type='str'
            ),
            plan=dict(
                type='raw'
            ),
            windows_framework=dict(
                type='dict'
            ),
            linux_framework=dict(
                type='dict',
                options=linux_framework_spec
            ),
            java_container_settings=dict(
                type='dict',
                options=java_container_settings_spec
            ),
            container_settings=dict(
                type='dict',
                options=container_settings_spec
            ),
            scm_type=dict(
                type='str',
            ),
            deployment_source=dict(
                type='dict',
                options=deployment_source_spec
            ),
            startup_file=dict(
                type='str'
            ),
            client_affinity_enabled=dict(
                type='bool',
                default=True
            ),
            dns_registration=dict(
                type='bool'
            ),
            https_only=dict(
                type='bool'
            ),
            skip_custom_domain_verification=dict(
                type='bool'
            ),
            ttl_in_seconds=dict(
                type='int'
            ),
            app_settings=dict(
                type='dict'
            ),
            purge_app_settings=dict(
                type='bool',
                default=False
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        mutually_exclusive = [['windows_framework', 'linux_framework']]

        self.resource_group = None
        self.name = None
        self.location = None

        # update in create_or_update as parameters
        self.client_affinity_enabled = True
        self.dns_registration = None
        self.skip_custom_domain_verification = None
        self.ttl_in_seconds = None
        self.https_only = None

        self.tags = None

        # site config, e.g app settings, ssl
        self.site_config = dict()
        self.app_settings = dict()
        self.app_settings_strDic = None

        # app service plan
        self.plan = None

        # siteSourceControl
        self.deployment_source = dict()

        # site, used at level creation, or update. e.g windows/linux, client_affinity etc first level args
        self.site = None

        # property for internal usage, not used for sdk
        self.container_settings = None

        self.purge_app_settings = False

        self.results = dict(
            changed=False,
            ansible_facts=dict(azure_webapp=None)
        )
        self.state = None
        self.to_do = Actions.NoAction

        self.windows_framework = None
        # set site_config value from kwargs
        self.site_config_updatable_properties = ["net_framework_version",
                                                 "java_version",
                                                 "php_version",
                                                 "python_version",
                                                 "scm_type"]

        # updatable_properties
        self.updatable_properties = ["client_affinity_enabled",
                                     "force_dns_registration",
                                     "https_only",
                                     "skip_custom_domain_verification",
                                     "ttl_in_seconds"]

        super(AzureRMWebApps, self).__init__(derived_arg_spec=self.module_arg_spec,
                                             mutually_exclusive=mutually_exclusive,
                                             supports_check_mode=True,
                                             supports_tags=True)

    def exec_module(self, **kwargs):
        """Main module execution method"""

        for key in list(self.module_arg_spec.keys()) + ['tags']:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif kwargs[key] is not None:
                if key == "scm_type":
                    self.site_config[key] = kwargs[key]

                # azure sdk linux_fx_version:
                # for docker web app, value is like DOCKER|imagename:tag
                # for linux web app, value is like NODE|6.6
                if key == "linux_framework":
                    self.site_config['linux_fx_version'] = (kwargs[key]['name'] + '|' + kwargs[key]['version']).upper()

                if key == "java_container_settings":
                    if 'name' in kwargs['java_container_settings']:
                        self.site_config['java_container'] = kwargs['java_container_settings']['name']
                    if 'version' in kwargs['java_container_settings']:
                        self.site_config['java_container_version'] = kwargs['java_container_settings']['version']

        old_response = None
        response = None
        to_be_updated = False

        if self.windows_framework is not None:
            if self.windows_framework.get('java_version', None) is not None and len(self.windows_framework) > 1:
                self.fail('java_version is mutually exclusive with other framework version in windows_framework.')
            for key in list(self.windows_framework.keys()):
                self.site_config[key] = self.windows_framework[key]

        if self.app_settings is None:
            self.app_settings = dict()

        if self.plan:
            self.plan = self.parse_resource_to_dict(self.plan)

        if self.container_settings is not None:
            if hasattr(self.site_config, 'linux_fx_version'):
                self.fail("Cannot set linux_framework with container_settings at same time.")

            linux_fx_version = 'DOCKER|'

            if self.container_settings.get('registry_server_url', None) is not None:
                self.app_settings['DOCKER_REGISTRY_SERVER_URL'] = 'https://' + self.container_settings['registry_server_url']

                linux_fx_version += self.container_settings['registry_server_url'] + '/'

            linux_fx_version += self.container_settings['name']

            self.site_config['linux_fx_version'] = linux_fx_version

            if self.container_settings.get('registry_server_user', None) is not None:
                self.app_settings['DOCKER_REGISTRY_SERVER_USERNAME'] = self.container_settings['registry_server_user']

            if self.container_settings.get('registry_server_password', None) is not None:
                self.app_settings['DOCKER_REGISTRY_SERVER_PASSWORD'] = self.container_settings['registry_server_password']

        # set location
        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            self.location = resource_group.location

        # init site
        self.site = Site(location=self.location, site_config=self.site_config)

        if self.https_only is not None:
            self.site.https_only = self.https_only

        if self.client_affinity_enabled:
            self.site.client_affinity_enabled = self.client_affinity_enabled

        # get existing web app
        old_response = self.get_webapp()

        # check if the web app already present in the resource group
        if not old_response:
            self.log("Web App instance doesn't exist")

            if self.state == "present":
                to_be_updated = True
                self.to_do = Actions.CreateOrUpdate

                # service plan is required for creation
                if not self.plan:
                    self.fail("Please specify app service plan in plan parameter.")

                # get app service plan
                old_plan = self.get_app_service_plan()

                if not old_plan:
                    # no existing service plan, create one
                    if (self.plan['name'] is None or self.plan['sku'] is None):
                        self.fail('Please specify name, is_linux, sku in plan')

                    if 'location' not in self.plan:
                        plan_resource_group = self.get_resource_group(self.plan['resource_group'])
                        self.plan['location'] = plan_resource_group.location

                    old_plan = self.create_app_service_plan()

                self.site.server_farm_id = old_plan['id']

                # if linux, setup startup_file
                if hasattr(old_plan, 'is_linux'):
                    if hasattr(self, 'startup_file'):
                        self.site_config['app_command_line'] = self.startup_file

                # set app setting
                if self.app_settings is not None:
                    app_settings = []
                    for key in self.app_settings.keys():
                        app_settings.append(NameValuePair(key, self.app_settings[key]))

                    self.site_config['app_settings'] = app_settings
        else:
            # existing web app, do update
            self.log("Web App instance already exists")

            if self.state == 'present':
                self.log('Result: {0}'.format(old_response))

                update_tags, old_response['tags'] = self.update_tags(
                    old_response.get('tags', dict()))

                if update_tags:
                    to_be_updated = True

                # check if root level property changed
                if self.is_updatable_property_changed(old_response):
                    to_be_updated = True
                    self.to_do = Actions.CreateOrUpdate

                # check if site_config changed
                old_config = self.get_webapp_configuration()

                if self.is_site_config_changed(old_config):
                    to_be_updated = True
                    self.to_do = Actions.CreateOrUpdate

                # check if linux_fx_version changed
                if old_config.linux_fx_version != self.site_config.get('linux_fx_version', None):
                    to_be_updated = True
                    self.to_do = Actions.CreateOrUpdate

                self.app_settings_strDic = self.list_app_settings()

                # purge existing app_settings:
                if self.purge_app_settings:
                    self.app_settings_strDic.properties = dict()

                # check if app settings changed
                if self.purge_app_settings or self.is_app_settings_changed():
                    to_be_updated = True
                    self.to_do = Actions.UpdateAppSettings

                    if self.app_settings is not None:
                        for key in self.app_settings.keys():
                            self.app_settings_strDic.properties[key] = self.app_settings[key]

        if old_response:
            self.results['ansible_facts']['azure_webapp'] = old_response

        if to_be_updated:
            self.log('Need to Create/Update web app')
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            if self.to_do == Actions.CreateOrUpdate:
                response = self.create_update_webapp()
                self.results['ansible_facts']['azure_webapp'] = response

            if self.to_do == Actions.UpdateAppSettings:
                response = self.update_app_settings()
                self.results['ansible_facts']['azure_webapp']['app_settings'] = response

        if self.state == 'absent' and old_response:
            self.log("Delete Web App instance")
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            self.delete_webapp()

            self.log('Web App instance deleted')

        return self.results

    # compare existing web app with input, determine weather it's update operation
    def is_updatable_property_changed(self, existing_webapp):
        for property_name in self.updatable_properties:
            if hasattr(self, property_name) and getattr(self, property_name) != existing_webapp.get(property_name, None):
                return True

        return False

    # compare xxx_version
    def is_site_config_changed(self, existing_config):
        for fx_version in self.site_config_updatable_properties:
            if self.site_config.get(fx_version, None) is not None:
                if not getattr(existing_config, fx_version) or \
                        getattr(existing_config, fx_version).upper() != self.site_config.get(fx_version).upper():
                            return True

        return False

    # comparing existing app setting with input, determine whether it's changed
    def is_app_settings_changed(self):
        if self.app_settings is not None:
            if len(self.app_settings_strDic.properties) != len(self.app_settings):
                return True

            elif self.app_settings_strDic.properties is not None and len(self.app_settings_strDic.properties) > 0:
                for key in self.app_settings.keys():
                    if self.app_settings_strDic.properties.get(key, None) is None \
                            or self.app_settings[key] != self.app_settings_strDic.properties[key]:
                        return True
        return False

    # comparing deployment source with input, determine wheather it's changed
    def is_deployment_source_changed(self, existing_webapp):
        if self.deployment_source is not None:
            if self.deployment_source.get('url', None) is not None \
                    and self.deployment_source['url'] != existing_webapp.get('site_source_control')['url']:
                return True

            if self.deployment_source.get('branch', None) is not None \
                    and self.deployment_source['branch'] != existing_webapp.get('site_source_control')['branch']:
                return True

        return False

    def create_update_webapp(self):
        '''
        Creates or updates Web App with the specified configuration.

        :return: deserialized Web App instance state dictionary
        '''
        self.log(
            "Creating / Updating the Web App instance {0}".format(self.name))

        try:
            skip_dns_registration = self.dns_registration
            force_dns_registration = None if self.dns_registration is None else not self.dns_registration

            response = self.web_client.web_apps.create_or_update(resource_group_name=self.resource_group,
                                                                 name=self.name,
                                                                 site_envelope=self.site,
                                                                 skip_dns_registration=skip_dns_registration,
                                                                 skip_custom_domain_verification=self.skip_custom_domain_verification,
                                                                 force_dns_registration=force_dns_registration,
                                                                 ttl_in_seconds=self.ttl_in_seconds)
            if isinstance(response, AzureOperationPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the Web App instance.')
            self.fail(
                "Error creating the Web App instance: {0}".format(str(exc)))
        return response.as_dict()

    def delete_webapp(self):
        '''
        Deletes specified Web App instance in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the Web App instance {0}".format(self.name))
        try:
            response = self.web_client.web_apps.delete(resource_group_name=self.resource_group,
                                                       name=self.name)
        except CloudError as e:
            self.log('Error attempting to delete the Web App instance.')
            self.fail(
                "Error deleting the Web App instance: {0}".format(str(e)))

        return True

    def get_webapp(self):
        '''
        Gets the properties of the specified Web App.

        :return: deserialized Web App instance state dictionary
        '''
        self.log(
            "Checking if the Web App instance {0} is present".format(self.name))

        response = None

        try:
            response = self.web_client.web_apps.get(resource_group_name=self.resource_group,
                                                    name=self.name)

            self.log("Response : {0}".format(response))
            self.log("Web App instance : {0} found".format(response.name))
            return response.as_dict()

        except CloudError as ex:
            self.log("Didn't find web app {0} in resource group {1}".format(
                self.name, self.resource_group))

        return False

    def get_app_service_plan(self):
        '''
        Gets app service plan
        :return: deserialized app service plan dictionary
        '''
        self.log("Get App Service Plan {0}".format(self.plan['name']))

        try:
            response = self.web_client.app_service_plans.get(
                self.plan['resource_group'], self.plan['name'])
            self.log("Response : {0}".format(response))
            self.log("App Service Plan : {0} found".format(response.name))

            return response.as_dict()
        except CloudError as ex:
            self.log("Didn't find app service plan {0} in resource group {1}".format(
                self.plan['name'], self.plan['resource_group']))

        return False

    def create_app_service_plan(self):
        '''
        Creates app service plan
        :return: deserialized app service plan dictionary
        '''
        self.log("Create App Service Plan {0}".format(self.plan['name']))

        try:
            # normalize sku
            sku = _normalize_sku(self.plan['sku'])

            sku_def = SkuDescription(tier=get_sku_name(
                sku), name=sku, capacity=(self.plan.get('number_of_workers', None)))
            plan_def = AppServicePlan(
                location=self.plan['location'], app_service_plan_name=self.plan['name'], sku=sku_def, reserved=(self.plan.get('is_linux', None)))

            poller = self.web_client.app_service_plans.create_or_update(
                self.plan['resource_group'], self.plan['name'], plan_def)

            if isinstance(poller, AzureOperationPoller):
                response = self.get_poller_result(poller)

            self.log("Response : {0}".format(response))

            return response.as_dict()
        except CloudError as ex:
            self.fail("Failed to create app service plan {0} in resource group {1}: {2}".format(
                self.plan['name'], self.plan['resource_group'], str(ex)))

    def list_app_settings(self):
        '''
        List application settings
        :return: deserialized list response
        '''
        self.log("List application setting")

        try:

            response = self.web_client.web_apps.list_application_settings(
                resource_group_name=self.resource_group, name=self.name)
            self.log("Response : {0}".format(response))

            return response
        except CloudError as ex:
            self.log("Failed to list application settings for web app {0} in resource group {1}".format(
                self.name, self.resource_group))

            return False

    def update_app_settings(self):
        '''
        Update application settings
        :return: deserialized updating response
        '''
        self.log("Update application setting")

        try:
            response = self.web_client.web_apps.update_application_settings(
                resource_group_name=self.resource_group, name=self.name, app_settings=self.app_settings_strDic)
            self.log("Response : {0}".format(response))

            return response.as_dict()
        except CloudError as ex:
            self.log("Failed to update application settings for web app {0} in resource group {1}".format(
                self.name, self.resource_group))

        return False

    def create_or_update_source_control(self):
        '''
        Update site source control
        :return: deserialized updating response
        '''
        self.log("Update site source control")

        if self.deployment_source is None:
            return False

        self.deployment_source['is_manual_integration'] = False
        self.deployment_source['is_mercurial'] = False

        try:
            response = self.web_client.web_client.create_or_update_source_control(
                self.resource_group, self.name, self.deployment_source)
            self.log("Response : {0}".format(response))

            return response.as_dict()
        except CloudError as ex:
            self.fail("Failed to update site source control for web app {0} in resource group {1}".format(
                self.name, self.resource_group))

    def get_webapp_configuration(self):
        '''
        Get  web app configuration
        :return: deserialized  web app configuration response
        '''
        self.log("Get web app configuration")

        try:

            response = self.web_client.web_apps.get_configuration(
                resource_group_name=self.resource_group, name=self.name)
            self.log("Response : {0}".format(response))

            return response
        except CloudError as ex:
            self.log("Failed to get configuration for web app {0} in resource group {1}: {2}".format(
                self.name, self.resource_group, str(ex)))

            return False


def main():
    """Main execution"""
    AzureRMWebApps()


if __name__ == '__main__':
    main()
