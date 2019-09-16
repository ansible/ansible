#!/usr/bin/python
#
# Copyright (c) 2019 Yuwei Zhou, <yuwzho@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_iotdevice
version_added: "2.9"
short_description: Manage Azure IoT hub device
description:
    - Create, delete an Azure IoT hub device.
options:
    hub:
        description:
            - Name of IoT Hub.
        type: str
        required: true
    hub_policy_name:
        description:
            - Policy name of the IoT Hub which will be used to query from IoT hub.
            - This policy should have 'RegistryWrite, ServiceConnect, DeviceConnect' accesses. You may get 401 error when you lack any of these.
        type: str
        required: true
    hub_policy_key:
        description:
            - Key of the I(hub_policy_name).
        type: str
        required: true
    name:
        description:
            - Name of the IoT hub device identity.
        type: str
        required: true
    state:
        description:
            - State of the IoT hub. Use C(present) to create or update an IoT hub device and C(absent) to delete an IoT hub device.
        type: str
        default: present
        choices:
            - absent
            - present
    auth_method:
        description:
            - The authorization type an entity is to be created with.
        type: str
        choices:
            - sas
            - certificate_authority
            - self_signed
        default: sas
    primary_key:
        description:
            - Explicit self-signed certificate thumbprint to use for primary key.
            - Explicit Shared Private Key to use for primary key.
        type: str
        aliases:
            - primary_thumbprint
    secondary_key:
        description:
            - Explicit self-signed certificate thumbprint to use for secondary key.
            - Explicit Shared Private Key to use for secondary key.
        type: str
        aliases:
            - secondary_thumbprint
    status:
        description:
            - Set device status upon creation.
        type: bool
    edge_enabled:
        description:
            - Flag indicating edge enablement.
            - Not supported in IoT Hub with Basic tier.
        type: bool
    twin_tags:
        description:
            - A section that the solution back end can read from and write to.
            - Tags are not visible to device apps.
            - "The tag can be nested dictionary, '.', '$', '#', ' ' is not allowed in the key."
            - List is not supported.
            - Not supported in IoT Hub with Basic tier.
        type: dict
    desired:
        description:
            - Used along with reported properties to synchronize device configuration or conditions.
            - "The tag can be nested dictionary, '.', '$', '#', ' ' is not allowed in the key."
            - List is not supported.
            - Not supported in IoT Hub with Basic tier.
        type: dict
extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - Yuwei Zhou (@yuwzho)

'''

EXAMPLES = '''
- name: Create simplest Azure IoT Hub device
  azure_rm_iotdevice:
    hub: myHub
    name: Testing
    hub_policy_name: iothubowner
    hub_policy_key: "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

- name: Create Azure IoT Edge device
  azure_rm_iotdevice:
    hub: myHub
    name: Testing
    hub_policy_name: iothubowner
    hub_policy_key: "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    edge_enabled: yes

- name: Create Azure IoT Hub device with device twin properties and tag
  azure_rm_iotdevice:
    hub: myHub
    name: Testing
    hub_policy_name: iothubowner
    hub_policy_key: "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    twin_tags:
        location:
            country: US
            city: Redmond
        sensor: humidity
    desired:
        period: 100
'''

RETURN = '''
device:
    description:
        - IoT Hub device.
    returned: always
    type: dict
    sample: {
        "authentication": {
            "symmetricKey": {
                "primaryKey": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "secondaryKey": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
            },
            "type": "sas",
            "x509Thumbprint": {
                "primaryThumbprint": null,
                "secondaryThumbprint": null
            }
        },
        "capabilities": {
            "iotEdge": false
        },
        "changed": true,
        "cloudToDeviceMessageCount": 0,
        "connectionState": "Disconnected",
        "connectionStateUpdatedTime": "0001-01-01T00:00:00",
        "deviceId": "Testing",
        "etag": "NzA2NjU2ODc=",
        "failed": false,
        "generationId": "636903014505613307",
        "lastActivityTime": "0001-01-01T00:00:00",
        "modules": [
            {
                "authentication": {
                    "symmetricKey": {
                        "primaryKey": "XXXXXXXXXXXXXXXXXXX",
                        "secondaryKey": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
                    },
                    "type": "sas",
                    "x509Thumbprint": {
                        "primaryThumbprint": null,
                        "secondaryThumbprint": null
                    }
                },
                "cloudToDeviceMessageCount": 0,
                "connectionState": "Disconnected",
                "connectionStateUpdatedTime": "0001-01-01T00:00:00",
                "deviceId": "testdevice",
                "etag": "MjgxOTE5ODE4",
                "generationId": "636903840872788074",
                "lastActivityTime": "0001-01-01T00:00:00",
                "managedBy": null,
                "moduleId": "test"
            }
        ],
        "properties": {
            "desired": {
                "$metadata": {
                    "$lastUpdated": "2019-04-10T05:00:46.2702079Z",
                    "$lastUpdatedVersion": 8,
                    "period": {
                        "$lastUpdated": "2019-04-10T05:00:46.2702079Z",
                        "$lastUpdatedVersion": 8
                    }
                },
                "$version": 1,
                "period": 100
            },
            "reported": {
                "$metadata": {
                    "$lastUpdated": "2019-04-08T06:24:10.5613307Z"
                },
                "$version": 1
            }
        },
        "status": "enabled",
        "statusReason": null,
        "statusUpdatedTime": "0001-01-01T00:00:00",
        "tags": {
            "location": {
                "country": "us",
                "city": "Redmond"
            },
            "sensor": "humidity"
        }
    }
'''  # NOQA

import json
import copy
import re

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, format_resource_id
from ansible.module_utils.common.dict_transformations import _snake_to_camel

try:
    from msrestazure.tools import parse_resource_id
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMIoTDevice(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            name=dict(type='str', required=True),
            hub_policy_name=dict(type='str', required=True),
            hub_policy_key=dict(type='str', required=True),
            hub=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            status=dict(type='bool'),
            edge_enabled=dict(type='bool'),
            twin_tags=dict(type='dict'),
            desired=dict(type='dict'),
            auth_method=dict(type='str', choices=['self_signed', 'sas', 'certificate_authority'], default='sas'),
            primary_key=dict(type='str', no_log=True, aliases=['primary_thumbprint']),
            secondary_key=dict(type='str', no_log=True, aliases=['secondary_thumbprint'])
        )

        self.results = dict(
            changed=False,
            id=None
        )

        self.name = None
        self.hub = None
        self.hub_policy_key = None
        self.hub_policy_name = None
        self.state = None
        self.status = None
        self.edge_enabled = None
        self.twin_tags = None
        self.desired = None
        self.auth_method = None
        self.primary_key = None
        self.secondary_key = None

        required_if = [
            ['auth_method', 'self_signed', ['certificate_authority']]
        ]

        self._base_url = None
        self._mgmt_client = None
        self.query_parameters = {
            'api-version': '2018-06-30'
        }
        self.header_parameters = {
            'Content-Type': 'application/json; charset=utf-8',
            'accept-language': 'en-US'
        }
        super(AzureRMIoTDevice, self).__init__(self.module_arg_spec, supports_check_mode=True, required_if=required_if)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec.keys():
            setattr(self, key, kwargs[key])

        self._base_url = '{0}.azure-devices.net'.format(self.hub)
        config = {
            'base_url': self._base_url,
            'key': self.hub_policy_key,
            'policy': self.hub_policy_name
        }
        self._mgmt_client = self.get_data_svc_client(**config)

        changed = False

        device = self.get_device()
        if self.state == 'present':
            if not device:
                changed = True
                auth = {'type': _snake_to_camel(self.auth_method)}
                if self.auth_method == 'self_signed':
                    auth['x509Thumbprint'] = {
                        'primaryThumbprint': self.primary_key,
                        'secondaryThumbprint': self.secondary_key
                    }
                elif self.auth_method == 'sas':
                    auth['symmetricKey'] = {
                        'primaryKey': self.primary_key,
                        'secondaryKey': self.secondary_key
                    }
                device = {
                    'deviceId': self.name,
                    'capabilities': {'iotEdge': self.edge_enabled or False},
                    'authentication': auth
                }
                if self.status is not None and not self.status:
                    device['status'] = 'disabled'
            else:
                if self.edge_enabled is not None and self.edge_enabled != device['capabilities']['iotEdge']:
                    changed = True
                    device['capabilities']['iotEdge'] = self.edge_enabled
                if self.status is not None:
                    status = 'enabled' if self.status else 'disabled'
                    if status != device['status']:
                        changed = True
                        device['status'] = status
            if changed and not self.check_mode:
                device = self.create_or_update_device(device)
            twin = self.get_twin()
            if twin:
                if not twin.get('tags'):
                    twin['tags'] = dict()
                twin_change = False
                if self.twin_tags and not self.is_equal(self.twin_tags, twin['tags']):
                    twin_change = True
                if self.desired and not self.is_equal(self.desired, twin['properties']['desired']):
                    twin_change = True
                if twin_change and not self.check_mode:
                    self.update_twin(twin)
                changed = changed or twin_change
                device['tags'] = twin.get('tags') or dict()
                device['properties'] = twin['properties']
                device['modules'] = self.list_device_modules()
            elif self.twin_tags or self.desired:
                self.fail("Device twin is not supported in IoT Hub with basic tier.")
        elif device:
            if not self.check_mode:
                self.delete_device(device['etag'])
            changed = True
            device = None
        self.results = device or dict()
        self.results['changed'] = changed
        return self.results

    def is_equal(self, updated, original):
        changed = False
        if not isinstance(updated, dict):
            self.fail('The Property or Tag should be a dict')
        for key in updated.keys():
            if re.search(r'[.|$|#|\s]', key):
                self.fail("Property or Tag name has invalid characters: '.', '$', '#' or ' '. Got '{0}'".format(key))
            original_value = original.get(key)
            updated_value = updated[key]
            if isinstance(updated_value, dict):
                if not isinstance(original_value, dict):
                    changed = True
                    original[key] = updated_value
                elif not self.is_equal(updated_value, original_value):
                    changed = True
            elif original_value != updated_value:
                changed = True
                original[key] = updated_value
        return not changed

    def create_or_update_device(self, device):
        try:
            url = '/devices/{0}'.format(self.name)
            headers = copy.copy(self.header_parameters)
            if device.get('etag'):
                headers['If-Match'] = '"{0}"'.format(device['etag'])
            request = self._mgmt_client.put(url, self.query_parameters)
            response = self._mgmt_client.send(request=request, headers=headers, content=device)
            if response.status_code not in [200, 201, 202]:
                raise CloudError(response)
            return json.loads(response.text)
        except Exception as exc:
            if exc.status_code in [403] and self.edge_enabled:
                self.fail('Edge device is not supported in IoT Hub with Basic tier.')
            else:
                self.fail('Error when creating or updating IoT Hub device {0}: {1}'.format(self.name, exc.message or str(exc)))

    def delete_device(self, etag):
        try:
            url = '/devices/{0}'.format(self.name)
            headers = copy.copy(self.header_parameters)
            headers['If-Match'] = '"{0}"'.format(etag)
            request = self._mgmt_client.delete(url, self.query_parameters)
            response = self._mgmt_client.send(request=request, headers=headers)
            if response.status_code not in [204]:
                raise CloudError(response)
        except Exception as exc:
            self.fail('Error when deleting IoT Hub device {0}: {1}'.format(self.name, exc.message or str(exc)))

    def get_device(self):
        try:
            url = '/devices/{0}'.format(self.name)
            device = self._https_get(url, self.query_parameters, self.header_parameters)
            return device
        except Exception as exc:
            if exc.status_code in [404]:
                return None
            else:
                self.fail('Error when getting IoT Hub device {0}: {1}'.format(self.name, exc.message or str(exc)))

    def get_twin(self):
        try:
            url = '/twins/{0}'.format(self.name)
            return self._https_get(url, self.query_parameters, self.header_parameters)
        except Exception as exc:
            if exc.status_code in [403]:
                # The Basic sku has nothing to to with twin
                return None
            else:
                self.fail('Error when getting IoT Hub device {0} twin: {1}'.format(self.name, exc.message or str(exc)))

    def update_twin(self, twin):
        try:
            url = '/twins/{0}'.format(self.name)
            headers = copy.copy(self.header_parameters)
            headers['If-Match'] = '"{0}"'.format(twin['etag'])
            request = self._mgmt_client.patch(url, self.query_parameters)
            response = self._mgmt_client.send(request=request, headers=headers, content=twin)
            if response.status_code not in [200]:
                raise CloudError(response)
            return json.loads(response.text)
        except Exception as exc:
            self.fail('Error when creating or updating IoT Hub device twin {0}: {1}'.format(self.name, exc.message or str(exc)))

    def list_device_modules(self):
        try:
            url = '/devices/{0}/modules'.format(self.name)
            return self._https_get(url, self.query_parameters, self.header_parameters)
        except Exception as exc:
            self.fail('Error when listing IoT Hub device {0} modules: {1}'.format(self.name, exc.message or str(exc)))

    def _https_get(self, url, query_parameters, header_parameters):
        request = self._mgmt_client.get(url, query_parameters)
        response = self._mgmt_client.send(request=request, headers=header_parameters, content=None)
        if response.status_code not in [200]:
            raise CloudError(response)
        return json.loads(response.text)


def main():
    AzureRMIoTDevice()


if __name__ == '__main__':
    main()
