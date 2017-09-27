#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: wascloud_instance
short_description: create, update or cancel an instance of WebSphere on Cloud
description:
  - Creates, updates or cancels WebSphere on Cloud instances. When created, optionally waits for it to be 'running'.
  - More information about WebSphere on Cloud in IBM Marketplace U(https://www.ibm.com/us-en/marketplace/application-server-on-cloud)
version_added: "2.5"
options:
  state:
    description:
      - Create, update or cancel instances
    required: false
    default: 'present'
    choices: ['present', 'absent', 'latest', 'reloaded']
  name:
    description:
      - Name of the WAS instance to be created, updated or cancelled
    required: true
  wait:
    description:
      - Whether to wait for instance creation to complete before continuing. Must be true to return instance details
    required: false
    default: false
  instance_type:
    description:
      - Type of WebSphere instance to create. Required when creating or reloading instance, but not when cancelling instance
      - Valid options when creating: C(LibertyCollective)/C(LibertyCore)/C(LibertyNDServer)/C(WASBase)/C(WASCell)/C(WASNDServer)
    required: false
  size:
    description:
      - T-Shirt size of WebSphere instance.
      - Required if I(state==present/latest/reloaded)when creating new instance, but not when cancelling instance
    required: false
  app_vms:
    description:
      - Number of application server VMs in a WAS Cell or Liberty Collective
      - Required if I(instance_type==WASCell/LibertyCollective)
    required: false
  controller_size:
    description:
      - T-Shirt size of controller VM in WAS Cell or Liberty Collective
      - Required only when provisioning new WAS Cell or Liberty Collective
    required: false
  software_level:
    description:
      - Version of Websphere to provision. If left blank when provisioning the latest version available will be selected by the WAS Broker
    required: false
  region:
    description:
      - Bluemix region to provision to.
    required: true
  org:
    description:
      - Bluemix organisation to authenticate and provision to
    required: true
  space:
    description:
      - Bluemix space to authenticate and provision to
    required: true
  apikey:
    description:
      - Bluemix API Key to authenticate with
    required: true
  public_ip:
    description:
      - Whether to request a public ip address when creating an instance
    required: false
    default: false

requirements:
    - "python >= 2.7"
    - "requests >= 2.11.0"
author: "Hans Kristian Moen (@hassenius)"
'''

EXAMPLES = '''
# Simple example that creates a WAS Base on a single VM
- wascloud_instance:
    state: present
    name: temp_dev_env
    instance_type: WASBase
    size: M
    region: <bluemix_region>
    org: <bluemix_org>
    space: <bluemix_space>
    apikey: <bluemix api key>
    wait: True
  register: was_instace

'''

RETURN = '''
instance_deleted:
  description: Whether an instance was deleted during the task run
  returned: always
  type: boolean
resources:
  description: List of resources in the WAS service instance. If the service instance is not ready an empty list is returned
  returned: always
  type: list
  sample: [
    {
      "WASaaSresourceID": "string",
      "disk": 0,
      "vcpu": 0,
      "memory": 0,
      "machinename": "string",
      "machinestatus": "string",
      "creationTime": "string",
      "expireTime": "string",
      "vpnConfigLink": "string",
      "waslink": "string",
      "wasAdminUser": "string",
      "wasAdminPass": "string",
      "ifixinfo": "string",
      "osType": "string",
      "osHostname": "string",
      "osAdminUser": "string",
      "osAdminPassword": "string",
      "virtuserPrivateSshKey": "string",
      "keyStorePassword": "string",
      "publicIpInfo": {
        "ipResourceStatus": "string",
        "publicIp": "string",
        "ipResourceId": "string",
        "open": true
      }
    }
  ]
public_ip:
  description: The public IP address for the service instance
  returned: When public_ip is set to True in playbook
  type: string
'''

from ansible.module_utils.basic import AnsibleModule
import time
import base64

from __future__ import absolute_import, division, print_function
__metaclass__ = type

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent', 'latest', 'reloaded']),
            name=dict(required=True),
            wait=dict(required=False, default=False, type='bool'),
            instance_type=dict(required=False),
            size=dict(required=False),
            app_vms=dict(required=False, type='int'),
            controller_size=dict(required=False),
            software_level=dict(required=False),
            region=dict(required=True),
            org=dict(required=True),
            space=dict(required=True),
            apikey=dict(required=True),
            public_ip=dict(required=False, default=False, type='bool')
        ),

        required_if=[
            ['instance_type', 'WASBase', ['size']],
            ['instance_type', 'WASCell', ['controller_size', 'app_vms', 'size']],
            ['instance_type', 'LibertyCollective', ['controller_size', 'app_vms', 'size']]
        ]
    )

    regionKey = module.params['region']
    organisation = module.params['org']
    space = module.params['space']
    instance_name = module.params['name']
    state = module.params['state']
    apiKey = module.params['apikey']
    instance_type = module.params['instance_type']
    size = module.params['size']
    software_level = module.params['software_level']
    wait = module.params['wait']
    public_ip = module.params['public_ip']

    if not HAS_REQUESTS:
        module.fail_json(msg='python requests package required for this module')

    # Get authorizatin token from Bluemix
    bx = BluemixAPI(region_key=regionKey, apiKey=apiKey)
    authorization = 'Bearer ' + bx.get_token()

    # Create a connection object for WebSphere in Bluemix broker
    was = WASaaSAPI(region_key=regionKey, org=organisation, space=space, si_name=instance_name, token=authorization)

    status = {}
    status['instance_deleted'] = False
    status['changed'] = False

    # basic validation that org/space is valid
    success, message = was.valid_connection()

    if not success:
        module.fail_json(msg=message, **status)

    # If the task includes delete, just delete right away
    if state in ['absent', 'reloaded', 'latest']:
        if was.instance_exists():
            # Attempt to delete the instance
            success, message = was.delete_instance()

            if success:
                status['instance_deleted'] = True
                status['changed'] = True
            else:
                module.fail_json(msg=message, **status)

            if state == 'absent':
                module.exit_json(msg=message, **status)

        else:
            if state == 'absent':
                module.exit_json(msg='Instance name not found', **status)

    # The instance creation part of the task
    if state in ['present', 'latest', 'reloaded']:
        status['debug_create_reached'] = True

        if was.instance_exists():

            if status['instance_deleted']:
                # We only get here with latest and reloaded when an instance already exists.
                # Wait for it to be properly deleted.
                while was.instance_exists():
                    time.sleep(10)
                # Some times details from the old instance can remain. Reset.
                was.reset_instance_object()
            else:
                # In state present we just return the resources list
                resources = was.get_resources_list()
                module.exit_json(msg='Instance by that name already exists', resources=resources, **status)

        # Basic configuration for creating service instances
        instance_config = {
            "Type": instance_type,
            "Name": instance_name,
            "ApplicationServerVMSize": size.upper()
        }

        if instance_type in ['WASCell', 'LibertyCollective']:
            instance_config['ControlServerVMSize'] = module.params['controller_size'].upper()
            instance_config['NumberOfApplicationVMs'] = module.params['app_vms']

        if instance_type in ['WASBase', 'WASNDServer', 'WASCell']:
            if module.params.get('software_level'):
                instance_config['software_level'] = module.params.get('software_level')

        if public_ip:
            # Force wait
            wait = True

        resources = []
        success, message = was.create_instance(instance_config, wait_until_ready=wait)
        if not success:
            status['fail_message'] = message
            module.fail_json(msg=message, **status)
        else:
            status['changed'] = True
            if public_ip:
                success, message = was.request_public_ip()
                if success:
                    status['public_ip'] = message
                else:
                    module.fail_json(msg=message, **status)

            resources = was.get_resources_list()
            module.exit_json(msg=message, resources=resources, **status)


class BluemixAPI(object):

    def __init__(self, region_key, apiKey):

        self.access_token = ''
        self.refresh_token = ''
        self.region_keys = ['ng', 'eu-gb']
        self.region_key = ''
        self.apiKey = ''

        self.region_key = region_key
        self.apiKey = apiKey
        self.fetch_token()

    def fetch_token(self):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'Authorization': 'Basic ' + base64.b64encode(b'bx:bx').decode('ascii')}

        data = 'apikey=%s&grant_type=urn:ibm:params:oauth:grant-type:apikey&response_type=cloud_iam,uaa&uaa_client_id=cf&uaa_client_secret=' % self.apiKey

        url = 'https://iam.%s.bluemix.net/oidc/token' % self.region_key

        r = requests.post(url, data=data, headers=headers)

        if r.status_code == 200:
            self.access_token = r.json()['uaa_token']
            self.refresh_token = r.json()['uaa_refresh_token']
        else:
            return False

    def get_token(self):
        if self.access_token == '':
            self.fetch_token()

        return self.access_token


class WASaaSAPI(object):

    def __init__(self, region_key, org, space, si_name='', token='', refresh_token=''):
        self.token = token
        self.si_name = si_name
        self.sid = ''
        self.resources_raw = []
        self.adminip = ''
        self.wsadmin_user = ''
        self.wsadmin_pass = ''
        self.vpnConfig_link = ''
        self.space = space
        self.org = org
        self.regionKey = region_key
        self.appserver_size = ''
        self.instance_type = ''
        self.software_level = ''
        self.public_ip = ''
        # Available Environments:
        # Dallas - https://wasaas-broker.ng.bluemix.net/wasaas-broker/api/v1
        # London - https://wasaas-broker.eu-gb.bluemix.net/wasaas-broker/api/v1
        # Sydney - https://wasaas-broker.au-syd.bluemix.net/wasaas-broker/api/v1
        # Frankfurt - https://wasaas-broker.eu-de.bluemix.net/wasaas-broker/api/v1
        regions = {
            'ng': 'https://wasaas-broker.ng.bluemix.net/wasaas-broker/api/v1',
            'eu-gb': 'https://wasaas-broker.eu-gb.bluemix.net/wasaas-broker/api/v1',
            'eu-de': 'https://wasaas-broker.eu-de.bluemix.net/wasaas-broker/api/v1',
            'au-syd': 'https://wasaas-broker.au-syd.bluemix.net/wasaas-broker/api/v1'
        }
        self.baseUrl = regions[self.regionKey]
        self._headers = {
            'User-Agent': 'ansible-wascloud 1.0',
            'authorization': self.token,
            'Accept': 'application/json'
        }

    def create_instance(self, config, wait_until_ready=False):

        url = self.baseUrl + '/organizations/{0}/spaces/{1}/serviceinstances'.format(self.org, self.space)
        r = requests.post(url, json=config, headers=self._headers)
        if r.status_code != 200:
            return False, r.text
        else:
            self.sid = r.json()['ServiceInstance']['ServiceInstanceID']
            if not wait_until_ready:
                return True, 'Instance requested'
            else:
                while not self.instance_ready():
                    time.sleep(30)
                return True, 'Instance ready'

    def request_public_ip(self):
        if len(self.resources_raw) == 0:
            self.fetch_resource_details()

        if len(self.resources_raw) == 1:
            primary_host_id = self.resources_raw[0]['WASaaSResourceID']
        else:
            primary_host_id = self.get_primary_host_id()

        if not primary_host_id:
            return False, 'Failed to find a primary host'

        # Request the IP
        url = self.baseUrl + '/organizations/%s/spaces/%s/serviceinstances/%s/resources/%s?action=requestip' % (self.org, self.space, self.sid, primary_host_id)
        r = requests.put(url, headers=self._headers)
        if r.status_code != 200:
            return False, str(r.status_code)

        # Open the IP
        url = self.baseUrl + '/organizations/%s/spaces/%s/serviceinstances/%s/resources/%s?action=openip' % (self.org, self.space, self.sid, primary_host_id)
        r = requests.put(url, headers=self._headers)
        if r.status_code != 200:
            return False, str(r.status_code)

        # Query primary host for IP
        url = self.baseUrl + '/organizations/%s/spaces/%s/serviceinstances/%s/resources/%s' % (self.org, self.space, self.sid, primary_host_id)
        resources = {}
        attempts = 0
        while 'publicIpInfo' not in resources:
            time.sleep(5)
            r = requests.get(url, headers=self._headers)
            if r.status_code == 200:
                resources = r.json()
            attempts += 1
            if attempts == 100:
                return False, "Failed to get public IP information"

        public_ip = ''
        if 'publicIpInfo' in resources:
            if 'publicIp' in resources['publicIpInfo']:
                public_ip = resources['publicIpInfo']['publicIp']
                self.public_ip = public_ip

        return True, public_ip

    def get_primary_host_id(self):
        for r in self.resources_raw:
            if 'waslink' in r:
                return r['WASaaSResourceID']
        return False

    def instance_ready(self):
        url = self.baseUrl + '/organizations/%s/spaces/%s/serviceinstances/%s/resources' % (self.org, self.space, self.sid)
        r = requests.get(url, headers=self._headers)
        if r.status_code != 200:
            # TODO: Implement some failure handling
            return False

        if len(r.json()) >= 1:
            return True
        else:
            return False

    def delete_instance(self):
        if self.sid == '':
            self.fetch_resource_details()

        url = self.baseUrl + '/organizations/%s/spaces/%s/serviceinstances/%s' % (self.org, self.space, self.sid)
        r = requests.delete(url, headers=self._headers)
        if r.status_code == 204:
            self.sid = ''
            self.resources_raw = []
            return True, 'Instance deleted'
        else:
            return False, r.text

    # Not used yet. Method for downloading zip with openvpn certificates and config for the region
    def get_vpnConfig_zip(self):
        if self.sid == '':
            self.fetch_resource_details()

        url = self.baseUrl + '/organizations/%s/spaces/%s/serviceinstances/%s/vpnconfig' % (self.org, self.space, self.sid)
        r = requests.get(url, headers=self._headers)
        if r.status_code != 200:
            # TODO Implement some error handling
            return False

        return r.json()['VpnConfig']

    # basic validation that org/space is valid
    def valid_connection(self):
        success, message = self.get_serviceinstances(self.org, self.space)
        if success:
            return True, ''
        else:
            return False, message

    def reset_instance_object(self):
        self.sid = ''
        self.resources_raw = []
        self.adminip = ''
        self.wsadmin_user = ''
        self.wsadmin_pass = ''
        self.vpnConfig_link = ''
        self.appserver_size = ''
        self.instance_type = ''
        self.software_level = ''

    def instance_exists(self):
        success, sis = self.get_serviceinstances(self.org, self.space)
        for s in sis:
            if 'Name' not in s['ServiceInstance']:
                # Some instance deployment types do not seem to have these
                continue
            if s['ServiceInstance']['Name'] == self.si_name:
                # Populate sid if does not already exist
                if self.sid == '':
                    self.sid = s['ServiceInstance']['ServiceInstanceID']
                return True

        return False

    def fetch_resource_details(self):

        if self.sid == '':
            success, sis = self.get_serviceinstances(self.org, self.space)
            si = False
            for s in sis:
                if s['ServiceInstance']['Name'] == self.si_name:
                    si = s
                    break

            if not si:
                # print("Could not find service instance with name %s " % self.si_name)
                return False

            # Ensure this is basic WAS as we don't support ND cluster yet
            if si['ServiceInstance']['ServiceType'] != 'WASBase':
                # print("Don't support the service instance type %s " % si['ServiceInstance']['ServiceType'])
                return False

            self.sid = si['ServiceInstance']['ServiceInstanceID']

        r = self.get_resources_list()

        self.resources_raw = r
        self.adminip = r[0]['osHostname']
        self.rootpassword = r[0]['osAdminPassword']
        self.wsadmin_user = r[0]['wasAdminUser']
        self.wsadmin_pass = r[0]['wasAdminPass']
        self.vpnConfig_link = r[0]['vpnConfigLink']

        return True

    def get_resources_list(self):
        if len(self.resources_raw) > 0:
            return self.resources_raw
        else:
            url = self.baseUrl + '/organizations/%s/spaces/%s/serviceinstances/%s/resources' % (self.org, self.space, self.sid)
            r = requests.get(url, headers=self._headers)
            if r.status_code == 404:
                # This generally means that we're in the middle of a create or delete. For now return false
                return False
            if r.status_code != 200:
                # Catch everything else
                # TODO Implement some error handling
                return False
            return r.json()

    def get_serviceinstances(self, organisation, space):

        url = self.baseUrl + '/organizations/%s/spaces/%s/serviceinstances' % (organisation, space)
        r = requests.get(url, headers=self._headers)
        if r.status_code == 200:
            return True, r.json()
        else:
            return False, r.text

if __name__ == '__main__':
    main()
