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
module: azure_rm_webappslot
version_added: "2.8"
short_description: Manage Azure Web App slot.
description:
    - Create, update and delete Azure Web App slot.

options:
    resource_group:
        description:
            - Name of the resource group to which the resource belongs.
        required: True
    name:
        description:
            - Unique name of the deployment slot to create or update.
        required: True
    webapp_name:
        description:
            - Web app name which this deployment slot belongs to.
        required: True
    location:
        description:
            - Resource location. If not set, location from the resource group will be used as default.
    configuration_source:
        description:
            - Source slot to clone configurations from when creating slot. Use webapp's name to refer to the production slot.
    auto_swap_slot_name:
        description:
            - Used to configure target slot name to auto swap, or disable auto swap.
            - Set it target slot name to auto swap.
            - Set it to False to disable auto slot swap.
    swap:
        description:
            - Swap deployment slots of a web app.
        suboptions:
            action:
                description:
                    - Swap types.
                    - preview is to apply target slot settings on source slot first.
                    - swap is to complete swapping.
                    - reset is to reset the swap.
                choices:
                    - preview
                    - swap
                    - reset
                default: preview
            target_slot:
                description:
                    - Name of target slot to swap. If set to None, then swap with production slot.
            preserve_vnet:
                description:
                    - True to preserve virtual network to the slot during swap. Otherwise False.
                type: bool
                default: True
    frameworks:
        description:
            - Set of run time framework settings. Each setting is a dictionary.
            - See U(https://docs.microsoft.com/en-us/azure/app-service/app-service-web-overview) for more info.
        suboptions:
            name:
                description:
                    - Name of the framework.
                    - Supported framework list for Windows web app and Linux web app is different.
                    - For Windows web app, supported names(June 2018) java, net_framework, php, python, node. Multiple framework can be set at same time.
                    - For Linux web app, supported names(June 2018) java, ruby, php, dotnetcore, node. Only one framework can be set.
                    - Java framework is mutually exclusive with others.
                choices:
                    - java
                    - net_framework
                    - php
                    - python
                    - ruby
                    - dotnetcore
                    - node
            version:
                description:
                    - Version of the framework. For Linux web app supported value, see U(https://aka.ms/linux-stacks) for more info.
                    - net_framework supported value sample, 'v4.0' for .NET 4.6 and 'v3.0' for .NET 3.5.
                    - php supported value sample, 5.5, 5.6, 7.0.
                    - python supported value sample, e.g., 5.5, 5.6, 7.0.
                    - node supported value sample, 6.6, 6.9.
                    - dotnetcore supported value sample, 1.0, 1,1, 1.2.
                    - ruby supported value sample, 2.3.
                    - java supported value sample, 1.8, 1.9 for windows web app. 8 for linux web app.
            settings:
                description:
                    - List of settings of the framework.
                suboptions:
                    java_container:
                        description: Name of Java container. This is supported by specific framework C(java) only. e.g. Tomcat, Jetty.
                    java_container_version:
                        description:
                            - Version of Java container. This is supported by specific framework C(java) only.
                            - For Tomcat, e.g. 8.0, 8.5, 9.0. For Jetty, e.g. 9.1, 9.3.
    container_settings:
        description: Web app slot container settings.
        suboptions:
            name:
                description: Name of container. eg. "imagename:tag"
            registry_server_url:
                description: Container registry server url. eg. mydockerregistry.io
            registry_server_user:
                description: The container registry server user name.
            registry_server_password:
                description:
                    - The container registry server password.
    startup_file:
        description:
            - The slot startup file.
            - This only applies for linux web app slot.
    app_settings:
        description:
            - Configure web app slot application settings. Suboptions are in key value pair format.
    purge_app_settings:
        description:
            - Purge any existing application settings. Replace slot application settings with app_settings.
        type: bool
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
    app_state:
        description:
            - Start/Stop/Restart the slot.
        type: str
        choices:
            - started
            - stopped
            - restarted
        default: started
    state:
      description:
        - Assert the state of the Web App deployment slot.
        - Use C(present) to create or update a  slot and C(absent) to delete it.
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
  - name: Create a webapp slot
    azure_rm_webapp_slot:
      resource_group: myResourceGroup
      webapp_name: myJavaWebApp
      name: stage
      configuration_source: myJavaWebApp
      app_settings:
        testkey: testvalue

  - name: swap the slot with production slot
    azure_rm_webapp_slot:
      resource_group: myResourceGroup
      webapp_name: myJavaWebApp
      name: stage
      swap:
        action: swap

  - name: stop the slot
    azure_rm_webapp_slot:
      resource_group: myResourceGroup
      webapp_name: myJavaWebApp
      name: stage
      app_state: stopped

  - name: udpate a webapp slot app settings
    azure_rm_webapp_slot:
      resource_group: myResourceGroup
      webapp_name: myJavaWebApp
      name: stage
      app_settings:
        testkey: testvalue2

  - name: udpate a webapp slot frameworks
    azure_rm_webapp_slot:
      resource_group: myResourceGroup
      webapp_name: myJavaWebApp
      name: stage
      frameworks:
        - name: "node"
          version: "10.1"
'''

RETURN = '''
id:
    description: Id of current slot.
    returned: always
    type: str
    sample: /subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/myResourceGroup/providers/Microsoft.Web/sites/testapp/slots/stage1
'''

import time
from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from msrest.polling import LROPoller
    from msrest.serialization import Model
    from azure.mgmt.web.models import (
        site_config, app_service_plan, Site,
        AppServicePlan, SkuDescription, NameValuePair
    )
except ImportError:
    # This is handled in azure_rm_common
    pass

swap_spec = dict(
    action=dict(
        type='str',
        choices=[
            'preview',
            'swap',
            'reset'
        ],
        default='preview'
    ),
    target_slot=dict(
        type='str'
    ),
    preserve_vnet=dict(
        type='bool',
        default=True
    )
)

container_settings_spec = dict(
    name=dict(type='str', required=True),
    registry_server_url=dict(type='str'),
    registry_server_user=dict(type='str'),
    registry_server_password=dict(type='str', no_log=True)
)

deployment_source_spec = dict(
    url=dict(type='str'),
    branch=dict(type='str')
)


framework_settings_spec = dict(
    java_container=dict(type='str', required=True),
    java_container_version=dict(type='str', required=True)
)


framework_spec = dict(
    name=dict(
        type='str',
        required=True,
        choices=['net_framework', 'java', 'php', 'node', 'python', 'dotnetcore', 'ruby']),
    version=dict(type='str', required=True),
    settings=dict(type='dict', options=framework_settings_spec)
)


def webapp_to_dict(webapp):
    return dict(
        id=webapp.id,
        name=webapp.name,
        location=webapp.location,
        client_cert_enabled=webapp.client_cert_enabled,
        enabled=webapp.enabled,
        reserved=webapp.reserved,
        client_affinity_enabled=webapp.client_affinity_enabled,
        server_farm_id=webapp.server_farm_id,
        host_names_disabled=webapp.host_names_disabled,
        https_only=webapp.https_only if hasattr(webapp, 'https_only') else None,
        skip_custom_domain_verification=webapp.skip_custom_domain_verification if hasattr(webapp, 'skip_custom_domain_verification') else None,
        ttl_in_seconds=webapp.ttl_in_seconds if hasattr(webapp, 'ttl_in_seconds') else None,
        state=webapp.state,
        tags=webapp.tags if webapp.tags else None
    )


def slot_to_dict(slot):
    return dict(
        id=slot.id,
        resource_group=slot.resource_group,
        server_farm_id=slot.server_farm_id,
        target_swap_slot=slot.target_swap_slot,
        enabled_host_names=slot.enabled_host_names,
        slot_swap_status=slot.slot_swap_status,
        name=slot.name,
        location=slot.location,
        enabled=slot.enabled,
        reserved=slot.reserved,
        host_names_disabled=slot.host_names_disabled,
        state=slot.state,
        repository_site_name=slot.repository_site_name,
        default_host_name=slot.default_host_name,
        kind=slot.kind,
        site_config=slot.site_config,
        tags=slot.tags if slot.tags else None
    )


class Actions:
    NoAction, CreateOrUpdate, UpdateAppSettings, Delete = range(4)


class AzureRMWebAppSlots(AzureRMModuleBase):
    """Configuration class for an Azure RM Web App slot resource"""

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
            webapp_name=dict(
                type='str',
                required=True
            ),
            location=dict(
                type='str'
            ),
            configuration_source=dict(
                type='str'
            ),
            auto_swap_slot_name=dict(
                type='raw'
            ),
            swap=dict(
                type='dict',
                options=swap_spec
            ),
            frameworks=dict(
                type='list',
                elements='dict',
                options=framework_spec
            ),
            container_settings=dict(
                type='dict',
                options=container_settings_spec
            ),
            deployment_source=dict(
                type='dict',
                options=deployment_source_spec
            ),
            startup_file=dict(
                type='str'
            ),
            app_settings=dict(
                type='dict'
            ),
            purge_app_settings=dict(
                type='bool',
                default=False
            ),
            app_state=dict(
                type='str',
                choices=['started', 'stopped', 'restarted'],
                default='started'
            ),
            state=dict(
                type='str',
                default='present',
                choices=['present', 'absent']
            )
        )

        mutually_exclusive = [['container_settings', 'frameworks']]

        self.resource_group = None
        self.name = None
        self.webapp_name = None
        self.location = None

        self.auto_swap_slot_name = None
        self.swap = None
        self.tags = None
        self.startup_file = None
        self.configuration_source = None
        self.clone = False

        # site config, e.g app settings, ssl
        self.site_config = dict()
        self.app_settings = dict()
        self.app_settings_strDic = None

        # siteSourceControl
        self.deployment_source = dict()

        # site, used at level creation, or update.
        self.site = None

        # property for internal usage, not used for sdk
        self.container_settings = None

        self.purge_app_settings = False
        self.app_state = 'started'

        self.results = dict(
            changed=False,
            id=None,
        )
        self.state = None
        self.to_do = Actions.NoAction

        self.frameworks = None

        # set site_config value from kwargs
        self.site_config_updatable_frameworks = ["net_framework_version",
                                                 "java_version",
                                                 "php_version",
                                                 "python_version",
                                                 "linux_fx_version"]

        self.supported_linux_frameworks = ['ruby', 'php', 'dotnetcore', 'node', 'java']
        self.supported_windows_frameworks = ['net_framework', 'php', 'python', 'node', 'java']

        super(AzureRMWebAppSlots, self).__init__(derived_arg_spec=self.module_arg_spec,
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

        old_response = None
        response = None
        to_be_updated = False

        # set location
        resource_group = self.get_resource_group(self.resource_group)
        if not self.location:
            self.location = resource_group.location

        # get web app
        webapp_response = self.get_webapp()

        if not webapp_response:
            self.fail("Web app {0} does not exist in resource group {1}.".format(self.webapp_name, self.resource_group))

        # get slot
        old_response = self.get_slot()

        # set is_linux
        is_linux = True if webapp_response['reserved'] else False

        if self.state == 'present':
            if self.frameworks:
                # java is mutually exclusive with other frameworks
                if len(self.frameworks) > 1 and any(f['name'] == 'java' for f in self.frameworks):
                    self.fail('Java is mutually exclusive with other frameworks.')

                if is_linux:
                    if len(self.frameworks) != 1:
                        self.fail('Can specify one framework only for Linux web app.')

                    if self.frameworks[0]['name'] not in self.supported_linux_frameworks:
                        self.fail('Unsupported framework {0} for Linux web app.'.format(self.frameworks[0]['name']))

                    self.site_config['linux_fx_version'] = (self.frameworks[0]['name'] + '|' + self.frameworks[0]['version']).upper()

                    if self.frameworks[0]['name'] == 'java':
                        if self.frameworks[0]['version'] != '8':
                            self.fail("Linux web app only supports java 8.")

                        if self.frameworks[0].get('settings', {}) and self.frameworks[0]['settings'].get('java_container', None) and \
                           self.frameworks[0]['settings']['java_container'].lower() != 'tomcat':
                            self.fail("Linux web app only supports tomcat container.")

                        if self.frameworks[0].get('settings', {}) and self.frameworks[0]['settings'].get('java_container', None) and \
                           self.frameworks[0]['settings']['java_container'].lower() == 'tomcat':
                            self.site_config['linux_fx_version'] = 'TOMCAT|' + self.frameworks[0]['settings']['java_container_version'] + '-jre8'
                        else:
                            self.site_config['linux_fx_version'] = 'JAVA|8-jre8'
                else:
                    for fx in self.frameworks:
                        if fx.get('name') not in self.supported_windows_frameworks:
                            self.fail('Unsupported framework {0} for Windows web app.'.format(fx.get('name')))
                        else:
                            self.site_config[fx.get('name') + '_version'] = fx.get('version')

                        if 'settings' in fx and fx['settings'] is not None:
                            for key, value in fx['settings'].items():
                                self.site_config[key] = value

            if not self.app_settings:
                self.app_settings = dict()

            if self.container_settings:
                linux_fx_version = 'DOCKER|'

                if self.container_settings.get('registry_server_url'):
                    self.app_settings['DOCKER_REGISTRY_SERVER_URL'] = 'https://' + self.container_settings['registry_server_url']

                    linux_fx_version += self.container_settings['registry_server_url'] + '/'

                linux_fx_version += self.container_settings['name']

                self.site_config['linux_fx_version'] = linux_fx_version

                if self.container_settings.get('registry_server_user'):
                    self.app_settings['DOCKER_REGISTRY_SERVER_USERNAME'] = self.container_settings['registry_server_user']

                if self.container_settings.get('registry_server_password'):
                    self.app_settings['DOCKER_REGISTRY_SERVER_PASSWORD'] = self.container_settings['registry_server_password']

            # set auto_swap_slot_name
            if self.auto_swap_slot_name and isinstance(self.auto_swap_slot_name, str):
                self.site_config['auto_swap_slot_name'] = self.auto_swap_slot_name
            if self.auto_swap_slot_name is False:
                self.site_config['auto_swap_slot_name'] = None

            # init site
            self.site = Site(location=self.location, site_config=self.site_config)

            # check if the slot already present in the webapp
            if not old_response:
                self.log("Web App slot doesn't exist")

                to_be_updated = True
                self.to_do = Actions.CreateOrUpdate
                self.site.tags = self.tags

                # if linux, setup startup_file
                if self.startup_file:
                    self.site_config['app_command_line'] = self.startup_file

                # set app setting
                if self.app_settings:
                    app_settings = []
                    for key in self.app_settings.keys():
                        app_settings.append(NameValuePair(name=key, value=self.app_settings[key]))

                    self.site_config['app_settings'] = app_settings

                # clone slot
                if self.configuration_source:
                    self.clone = True

            else:
                # existing slot, do update
                self.log("Web App slot already exists")

                self.log('Result: {0}'.format(old_response))

                update_tags, self.site.tags = self.update_tags(old_response.get('tags', None))

                if update_tags:
                    to_be_updated = True

                # check if site_config changed
                old_config = self.get_configuration_slot(self.name)

                if self.is_site_config_changed(old_config):
                    to_be_updated = True
                    self.to_do = Actions.CreateOrUpdate

                self.app_settings_strDic = self.list_app_settings_slot(self.name)

                # purge existing app_settings:
                if self.purge_app_settings:
                    to_be_updated = True
                    self.to_do = Actions.UpdateAppSettings
                    self.app_settings_strDic = dict()

                # check if app settings changed
                if self.purge_app_settings or self.is_app_settings_changed():
                    to_be_updated = True
                    self.to_do = Actions.UpdateAppSettings

                    if self.app_settings:
                        for key in self.app_settings.keys():
                            self.app_settings_strDic[key] = self.app_settings[key]

        elif self.state == 'absent':
            if old_response:
                self.log("Delete Web App slot")
                self.results['changed'] = True

                if self.check_mode:
                    return self.results

                self.delete_slot()

                self.log('Web App slot deleted')

            else:
                self.log("Web app slot {0} not exists.".format(self.name))

        if to_be_updated:
            self.log('Need to Create/Update web app')
            self.results['changed'] = True

            if self.check_mode:
                return self.results

            if self.to_do == Actions.CreateOrUpdate:
                response = self.create_update_slot()

                self.results['id'] = response['id']

                if self.clone:
                    self.clone_slot()

            if self.to_do == Actions.UpdateAppSettings:
                self.update_app_settings_slot()

        slot = None
        if response:
            slot = response
        if old_response:
            slot = old_response

        if slot:
            if (slot['state'] != 'Stopped' and self.app_state == 'stopped') or \
               (slot['state'] != 'Running' and self.app_state == 'started') or \
               self.app_state == 'restarted':

                self.results['changed'] = True
                if self.check_mode:
                    return self.results

                self.set_state_slot(self.app_state)

            if self.swap:
                self.results['changed'] = True
                if self.check_mode:
                    return self.results

                self.swap_slot()

        return self.results

    # compare site config
    def is_site_config_changed(self, existing_config):
        for fx_version in self.site_config_updatable_frameworks:
            if self.site_config.get(fx_version):
                if not getattr(existing_config, fx_version) or \
                        getattr(existing_config, fx_version).upper() != self.site_config.get(fx_version).upper():
                    return True

        if self.auto_swap_slot_name is False and existing_config.auto_swap_slot_name is not None:
            return True
        elif self.auto_swap_slot_name and self.auto_swap_slot_name != getattr(existing_config, 'auto_swap_slot_name', None):
            return True
        return False

    # comparing existing app setting with input, determine whether it's changed
    def is_app_settings_changed(self):
        if self.app_settings:
            if len(self.app_settings_strDic) != len(self.app_settings):
                return True

            if self.app_settings_strDic != self.app_settings:
                return True
        return False

    # comparing deployment source with input, determine wheather it's changed
    def is_deployment_source_changed(self, existing_webapp):
        if self.deployment_source:
            if self.deployment_source.get('url') \
                    and self.deployment_source['url'] != existing_webapp.get('site_source_control')['url']:
                return True

            if self.deployment_source.get('branch') \
                    and self.deployment_source['branch'] != existing_webapp.get('site_source_control')['branch']:
                return True

        return False

    def create_update_slot(self):
        '''
        Creates or updates Web App slot with the specified configuration.

        :return: deserialized Web App instance state dictionary
        '''
        self.log(
            "Creating / Updating the Web App slot {0}".format(self.name))

        try:
            response = self.web_client.web_apps.create_or_update_slot(resource_group_name=self.resource_group,
                                                                      slot=self.name,
                                                                      name=self.webapp_name,
                                                                      site_envelope=self.site)
            if isinstance(response, LROPoller):
                response = self.get_poller_result(response)

        except CloudError as exc:
            self.log('Error attempting to create the Web App slot instance.')
            self.fail("Error creating the Web App slot: {0}".format(str(exc)))
        return slot_to_dict(response)

    def delete_slot(self):
        '''
        Deletes specified Web App slot in the specified subscription and resource group.

        :return: True
        '''
        self.log("Deleting the Web App slot {0}".format(self.name))
        try:
            response = self.web_client.web_apps.delete_slot(resource_group_name=self.resource_group,
                                                            name=self.webapp_name,
                                                            slot=self.name)
        except CloudError as e:
            self.log('Error attempting to delete the Web App slot.')
            self.fail(
                "Error deleting the Web App slots: {0}".format(str(e)))

        return True

    def get_webapp(self):
        '''
        Gets the properties of the specified Web App.

        :return: deserialized Web App instance state dictionary
        '''
        self.log(
            "Checking if the Web App instance {0} is present".format(self.webapp_name))

        response = None

        try:
            response = self.web_client.web_apps.get(resource_group_name=self.resource_group,
                                                    name=self.webapp_name)

            # Newer SDK versions (0.40.0+) seem to return None if it doesn't exist instead of raising CloudError
            if response is not None:
                self.log("Response : {0}".format(response))
                self.log("Web App instance : {0} found".format(response.name))
                return webapp_to_dict(response)

        except CloudError as ex:
            pass

        self.log("Didn't find web app {0} in resource group {1}".format(
            self.webapp_name, self.resource_group))

        return False

    def get_slot(self):
        '''
        Gets the properties of the specified Web App slot.

        :return: deserialized Web App slot state dictionary
        '''
        self.log(
            "Checking if the Web App slot {0} is present".format(self.name))

        response = None

        try:
            response = self.web_client.web_apps.get_slot(resource_group_name=self.resource_group,
                                                         name=self.webapp_name,
                                                         slot=self.name)

            # Newer SDK versions (0.40.0+) seem to return None if it doesn't exist instead of raising CloudError
            if response is not None:
                self.log("Response : {0}".format(response))
                self.log("Web App slot: {0} found".format(response.name))
                return slot_to_dict(response)

        except CloudError as ex:
            pass

        self.log("Does not find web app slot {0} in resource group {1}".format(self.name, self.resource_group))

        return False

    def list_app_settings(self):
        '''
        List webapp application settings
        :return: deserialized list response
        '''
        self.log("List webapp application setting")

        try:

            response = self.web_client.web_apps.list_application_settings(
                resource_group_name=self.resource_group, name=self.webapp_name)
            self.log("Response : {0}".format(response))

            return response.properties
        except CloudError as ex:
            self.fail("Failed to list application settings for web app {0} in resource group {1}: {2}".format(
                self.name, self.resource_group, str(ex)))

    def list_app_settings_slot(self, slot_name):
        '''
        List application settings
        :return: deserialized list response
        '''
        self.log("List application setting")

        try:

            response = self.web_client.web_apps.list_application_settings_slot(
                resource_group_name=self.resource_group, name=self.webapp_name, slot=slot_name)
            self.log("Response : {0}".format(response))

            return response.properties
        except CloudError as ex:
            self.fail("Failed to list application settings for web app slot {0} in resource group {1}: {2}".format(
                self.name, self.resource_group, str(ex)))

    def update_app_settings_slot(self, slot_name=None, app_settings=None):
        '''
        Update application settings
        :return: deserialized updating response
        '''
        self.log("Update application setting")

        if slot_name is None:
            slot_name = self.name
        if app_settings is None:
            app_settings = self.app_settings_strDic
        try:
            response = self.web_client.web_apps.update_application_settings_slot(resource_group_name=self.resource_group,
                                                                                 name=self.webapp_name,
                                                                                 slot=slot_name,
                                                                                 kind=None,
                                                                                 properties=app_settings)
            self.log("Response : {0}".format(response))

            return response.as_dict()
        except CloudError as ex:
            self.fail("Failed to update application settings for web app slot {0} in resource group {1}: {2}".format(
                self.name, self.resource_group, str(ex)))

        return response

    def create_or_update_source_control_slot(self):
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
            response = self.web_client.web_client.create_or_update_source_control_slot(
                resource_group_name=self.resource_group,
                name=self.webapp_name,
                site_source_control=self.deployment_source,
                slot=self.name)
            self.log("Response : {0}".format(response))

            return response.as_dict()
        except CloudError as ex:
            self.fail("Failed to update site source control for web app slot {0} in resource group {1}: {2}".format(
                self.name, self.resource_group, str(ex)))

    def get_configuration(self):
        '''
        Get web app configuration
        :return: deserialized web app configuration response
        '''
        self.log("Get web app configuration")

        try:

            response = self.web_client.web_apps.get_configuration(
                resource_group_name=self.resource_group, name=self.webapp_name)
            self.log("Response : {0}".format(response))

            return response
        except CloudError as ex:
            self.fail("Failed to get configuration for web app {0} in resource group {1}: {2}".format(
                self.webapp_name, self.resource_group, str(ex)))

    def get_configuration_slot(self, slot_name):
        '''
        Get slot configuration
        :return: deserialized slot configuration response
        '''
        self.log("Get web app slot configuration")

        try:

            response = self.web_client.web_apps.get_configuration_slot(
                resource_group_name=self.resource_group, name=self.webapp_name, slot=slot_name)
            self.log("Response : {0}".format(response))

            return response
        except CloudError as ex:
            self.fail("Failed to get configuration for web app slot {0} in resource group {1}: {2}".format(
                slot_name, self.resource_group, str(ex)))

    def update_configuration_slot(self, slot_name=None, site_config=None):
        '''
        Update slot configuration
        :return: deserialized slot configuration response
        '''
        self.log("Update web app slot configuration")

        if slot_name is None:
            slot_name = self.name
        if site_config is None:
            site_config = self.site_config
        try:

            response = self.web_client.web_apps.update_configuration_slot(
                resource_group_name=self.resource_group, name=self.webapp_name, slot=slot_name, site_config=site_config)
            self.log("Response : {0}".format(response))

            return response
        except CloudError as ex:
            self.fail("Failed to update configuration for web app slot {0} in resource group {1}: {2}".format(
                slot_name, self.resource_group, str(ex)))

    def set_state_slot(self, appstate):
        '''
        Start/stop/restart web app slot
        :return: deserialized updating response
        '''
        try:
            if appstate == 'started':
                response = self.web_client.web_apps.start_slot(resource_group_name=self.resource_group, name=self.webapp_name, slot=self.name)
            elif appstate == 'stopped':
                response = self.web_client.web_apps.stop_slot(resource_group_name=self.resource_group, name=self.webapp_name, slot=self.name)
            elif appstate == 'restarted':
                response = self.web_client.web_apps.restart_slot(resource_group_name=self.resource_group, name=self.webapp_name, slot=self.name)
            else:
                self.fail("Invalid web app slot state {0}".format(appstate))

            self.log("Response : {0}".format(response))

            return response
        except CloudError as ex:
            request_id = ex.request_id if ex.request_id else ''
            self.fail("Failed to {0} web app slot {1} in resource group {2}, request_id {3} - {4}".format(
                appstate, self.name, self.resource_group, request_id, str(ex)))

    def swap_slot(self):
        '''
        Swap slot
        :return: deserialized response
        '''
        self.log("Swap slot")

        try:
            if self.swap['action'] == 'swap':
                if self.swap['target_slot'] is None:
                    response = self.web_client.web_apps.swap_slot_with_production(resource_group_name=self.resource_group,
                                                                                  name=self.webapp_name,
                                                                                  target_slot=self.name,
                                                                                  preserve_vnet=self.swap['preserve_vnet'])
                else:
                    response = self.web_client.web_apps.swap_slot_slot(resource_group_name=self.resource_group,
                                                                       name=self.webapp_name,
                                                                       slot=self.name,
                                                                       target_slot=self.swap['target_slot'],
                                                                       preserve_vnet=self.swap['preserve_vnet'])
            elif self.swap['action'] == 'preview':
                if self.swap['target_slot'] is None:
                    response = self.web_client.web_apps.apply_slot_config_to_production(resource_group_name=self.resource_group,
                                                                                        name=self.webapp_name,
                                                                                        target_slot=self.name,
                                                                                        preserve_vnet=self.swap['preserve_vnet'])
                else:
                    response = self.web_client.web_apps.apply_slot_configuration_slot(resource_group_name=self.resource_group,
                                                                                      name=self.webapp_name,
                                                                                      slot=self.name,
                                                                                      target_slot=self.swap['target_slot'],
                                                                                      preserve_vnet=self.swap['preserve_vnet'])
            elif self.swap['action'] == 'reset':
                if self.swap['target_slot'] is None:
                    response = self.web_client.web_apps.reset_production_slot_config(resource_group_name=self.resource_group,
                                                                                     name=self.webapp_name)
                else:
                    response = self.web_client.web_apps.reset_slot_configuration_slot(resource_group_name=self.resource_group,
                                                                                      name=self.webapp_name,
                                                                                      slot=self.swap['target_slot'])
                response = self.web_client.web_apps.reset_slot_configuration_slot(resource_group_name=self.resource_group,
                                                                                  name=self.webapp_name,
                                                                                  slot=self.name)

            self.log("Response : {0}".format(response))

            return response
        except CloudError as ex:
            self.fail("Failed to swap web app slot {0} in resource group {1}: {2}".format(self.name, self.resource_group, str(ex)))

    def clone_slot(self):
        if self.configuration_source:
            src_slot = None if self.configuration_source.lower() == self.webapp_name.lower() else self.configuration_source

            if src_slot is None:
                site_config_clone_from = self.get_configuration()
            else:
                site_config_clone_from = self.get_configuration_slot(slot_name=src_slot)

            self.update_configuration_slot(site_config=site_config_clone_from)

            if src_slot is None:
                app_setting_clone_from = self.list_app_settings()
            else:
                app_setting_clone_from = self.list_app_settings_slot(src_slot)

            if self.app_settings:
                app_setting_clone_from.update(self.app_settings)

            self.update_app_settings_slot(app_settings=app_setting_clone_from)


def main():
    """Main execution"""
    AzureRMWebAppSlots()


if __name__ == '__main__':
    main()
