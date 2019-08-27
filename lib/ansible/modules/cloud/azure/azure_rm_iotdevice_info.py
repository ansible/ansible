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
module: azure_rm_iotdevice_info
version_added: "2.9"
short_description: Facts of Azure IoT hub device
description:
    - Query, get Azure IoT hub device.
options:
    hub:
        description:
            - Name of IoT Hub.
        type: str
        required: true
    hub_policy_name:
        description:
            - Policy name of the IoT Hub which will be used to query from IoT hub.
            - This policy should have at least 'Registry Read' access.
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
        aliases:
            - device_id
    module_id:
        description:
            - Name of the IoT hub device module.
            - Must use with I(device_id) defined.
        type: str
    query:
        description:
            - Query an IoT hub to retrieve information regarding device twins using a SQL-like language.
            - "See U(https://docs.microsoft.com/en-us/azure/iot-hub/iot-hub-devguide-query-language)."
        type: str
    top:
        description:
            - Used when I(name) not defined.
            - List the top n devices in the query.
        type: int
extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - Yuwei Zhou (@yuwzho)
'''

EXAMPLES = '''
- name: Get the details of a device
  azure_rm_iotdevice_info:
      name: Testing
      hub: MyIoTHub
      hub_policy_name: registryRead
      hub_policy_key: XXXXXXXXXXXXXXXXXXXX

- name: Query all device modules in an IoT Hub
  azure_rm_iotdevice_info:
      query: "SELECT * FROM devices.modules"
      hub: MyIoTHub
      hub_policy_name: registryRead
      hub_policy_key: XXXXXXXXXXXXXXXXXXXX

- name: List all devices in an IoT Hub
  azure_rm_iotdevice_info:
      hub: MyIoTHub
      hub_policy_name: registryRead
      hub_policy_key: XXXXXXXXXXXXXXXXXXXX
'''

RETURN = '''
iot_devices:
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

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, format_resource_id
from ansible.module_utils.common.dict_transformations import _snake_to_camel, _camel_to_snake

try:
    from msrestazure.tools import parse_resource_id
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    # This is handled in azure_rm_common
    pass


class AzureRMIoTDeviceFacts(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            name=dict(type='str', aliases=['device_id']),
            module_id=dict(type='str'),
            query=dict(type='str'),
            hub=dict(type='str', required=True),
            hub_policy_name=dict(type='str', required=True),
            hub_policy_key=dict(type='str', required=True),
            top=dict(type='int')
        )

        self.results = dict(
            changed=False,
            iot_devices=[]
        )

        self.name = None
        self.module_id = None
        self.hub = None
        self.hub_policy_name = None
        self.hub_policy_key = None
        self.top = None

        self._mgmt_client = None
        self._base_url = None
        self.query_parameters = {
            'api-version': '2018-06-30'
        }
        self.header_parameters = {
            'Content-Type': 'application/json; charset=utf-8',
            'accept-language': 'en-US'
        }
        super(AzureRMIoTDeviceFacts, self).__init__(self.module_arg_spec, supports_check_mode=True)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec.keys():
            setattr(self, key, kwargs[key])

        self._base_url = '{0}.azure-devices.net'.format(self.hub)
        config = {
            'base_url': self._base_url,
            'key': self.hub_policy_key,
            'policy': self.hub_policy_name
        }
        if self.top:
            self.query_parameters['top'] = self.top
        self._mgmt_client = self.get_data_svc_client(**config)

        response = []
        if self.module_id:
            response = [self.get_device_module()]
        elif self.name:
            response = [self.get_device()]
        elif self.query:
            response = self.hub_query()
        else:
            response = self.list_devices()

        self.results['iot_devices'] = response
        return self.results

    def hub_query(self):
        try:
            url = '/devices/query'
            request = self._mgmt_client.post(url, self.query_parameters)
            query = {
                'query': self.query
            }
            response = self._mgmt_client.send(request=request, headers=self.header_parameters, content=query)
            if response.status_code not in [200]:
                raise CloudError(response)
            return json.loads(response.text)
        except Exception as exc:
            self.fail('Error when running query "{0}" in IoT Hub {1}: {2}'.format(self.query, self.hub, exc.message or str(exc)))

    def get_device(self):
        try:
            url = '/devices/{0}'.format(self.name)
            device = self._https_get(url, self.query_parameters, self.header_parameters)
            device['modules'] = self.list_device_modules()
            return device
        except Exception as exc:
            self.fail('Error when getting IoT Hub device {0}: {1}'.format(self.name, exc.message or str(exc)))

    def get_device_module(self):
        try:
            url = '/devices/{0}/modules/{1}'.format(self.name, self.module_id)
            return self._https_get(url, self.query_parameters, self.header_parameters)
        except Exception as exc:
            self.fail('Error when getting IoT Hub device {0}: {1}'.format(self.name, exc.message or str(exc)))

    def list_device_modules(self):
        try:
            url = '/devices/{0}/modules'.format(self.name)
            return self._https_get(url, self.query_parameters, self.header_parameters)
        except Exception as exc:
            self.fail('Error when getting IoT Hub device {0}: {1}'.format(self.name, exc.message or str(exc)))

    def list_devices(self):
        try:
            url = '/devices'
            return self._https_get(url, self.query_parameters, self.header_parameters)
        except Exception as exc:
            self.fail('Error when listing IoT Hub devices in {0}: {1}'.format(self.hub, exc.message or str(exc)))

    def _https_get(self, url, query_parameters, header_parameters):
        request = self._mgmt_client.get(url, query_parameters)
        response = self._mgmt_client.send(request=request, headers=header_parameters, content=None)
        if response.status_code not in [200]:
            raise CloudError(response)
        return json.loads(response.text)


def main():
    AzureRMIoTDeviceFacts()


if __name__ == '__main__':
    main()
