#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import re
import socket
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.six.moves.urllib.parse import quote

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: azure_vm_metadata_facts
short_description: <
  Gathers facts (instance metadata) about remote hosts within Azure
version_added: "2.9"
author:
    - Devon Hubner (@DevoKun)
description:
    - This module fetches data from the instance metadata endpoint in Azure as per
      U(https://azure.microsoft.com/en-us/blog/announcing-general-availability-of-azure-instance-metadata-service/).
      The module must be called from within the Azure VM instance itself.
    - Based on the ec2_metadata_facts module.
'''

EXAMPLES = '''
# Gather Azure VM metadata facts
- azure_vm_metadata_facts:

- debug:
    msg:
      - "location: {{ ansible_facts.azure_vm.compute.location }}"
      - "location: {{ ansible_azure_vm_compute_location }}"
'''

RETURN = '''
ansible_facts:
    description: <
      Dictionary of new facts representing discovered
      properties of the Azure VM.
    returned:    changed
    type:        complex
    contains:

        azure_vm_compute_azenvironment:
            description: Azure environment
            type:        str
            sample:      "AzurePublicCloud"

        azure_vm_compute_customdata:
            description: Azure VM customdata
            type:        str
            sample:      ""

        azure_vm_compute_location:
            description: Azure VM location
            type:        str
            sample:      "eastus"

        azure_vm_compute_name:
            description: Azure VM name
            type:        str
            sample:      "t1"

        azure_vm_compute_offer:
            description: Azure VM offer
            type:        str
            sample:      "UbuntuServer"

        azure_vm_compute_ostype:
            description: Azure VM ostype
            type:        str
            sample:      "Linux"

        azure_vm_compute_placementgroupid:
            description: Azure VM placement group id
            type:        str
            sample:      ""

        azure_vm_compute_plan_name:
            description: Azure VM plan name
            type:        str
            sample:      ""

        azure_vm_compute_plan_product:
            description: Azure VM plan product
            type:        str
            sample:      ""

        azure_vm_compute_plan_publisher:
            description: Azure VM plan publisher
            type:        str
            sample:      ""

        azure_vm_compute_platformfaultdomain:
            description: Azure VM platform fault domain
            type:        str
            sample:      "0"

        azure_vm_compute_platformupdatedomain:
            description: Azure VM platform update domain
            type:        str
            sample:      "0"

        azure_vm_compute_provider:
            description: Azure VM provider
            type:        str
            sample:      "Microsoft.Compute"

        azure_vm_compute_publickeys_keydata:
            description: Azure VM publickeys keydata
            type:        str
            sample:      "ssh-rsa XXXXXXXXXXXXXX"

        azure_vm_compute_publickeys_path:
            description: Azure VM publickeys path
            type:        str
            sample:      "/home/USER/.ssh/authorized_keys"

        azure_vm_compute_publisher:
            description: Azure VM publisher
            type:        str
            sample:      "Canonical"

        azure_vm_compute_resourcegroupname:
            description: Azure VM resource group name
            type:        str
            sample:      "images"

        azure_vm_compute_sku:
            description: Azure VM sku
            type:        str
            sample:      "18.04-LTS"

        azure_vm_compute_subscriptionid:
            description: Azure VM subscription id
            type:        str
            sample:      "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

        azure_vm_compute_tags:
            description: Azure VM tags
            type:        str
            sample:      ""

        azure_vm_compute_version:
            description: Azure VM version
            type:        str
            sample:      "18.04.201904020"

        azure_vm_compute_vmid:
            description: Azure VM id
            type:        str
            sample:      "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

        azure_vm_compute_vmscalesetname:
            description: Azure VM vm scaleset name
            type:        str
            sample:      ""

        azure_vm_compute_vmsize:
            description: Azure VM vm size
            type:        str
            sample:      "Standard_B1s"

        azure_vm_compute_zone:
            description: Azure VM zone
            type:        str
            sample:      ""

        azure_vm_network_interface_ipv4_ipaddress_privateipaddress:
            description: Azure VM network IPv4 private address
            type:        str
            sample:      "x.x.x.x"

        azure_vm_network_interface_ipv4_ipaddress_publicipaddress:
            description: Azure VM network IPv4 public address
            type:        str
            sample:      ""

        azure_vm_network_interface_ipv4_subnet_address:
            description: Azure VM network_interface_ipv4_subnet_address
            type:        str
            sample:      "x.x.x.0"

        azure_vm_network_interface_ipv4_subnet_prefix:
            description: Azure VM network_interface_ipv4_subnet_prefix
            type:        str
            sample:      "24"

        azure_vm_network_interface_macaddress:
            description: Azure VM network_interface_macaddress
            type:        str
            sample:      "XXXXXXXXXXXX"

'''

socket.setdefaulttimeout(5)


class AzureVmMetadata(object):
    # Metadata URL comes from:
    # https://docs.microsoft.com/en-us/azure/virtual-machines/windows/instance-metadata-service
    azure_vm_metadata_uri = 'http://169.254.169.254/metadata/instance?api-version=2019-02-01'

    def __init__(self, module, azure_vm_metadata_uri=None):
        self.module = module
        self.uri_meta = azure_vm_metadata_uri or self.azure_vm_metadata_uri
        self._data = {}
        self._prefix = 'ansible_azure_vm%s'

    # Query the metadata URL and return the results as text.
    def _fetch(self, url):
        encoded_url = quote(url, safe='%/:=&?~#+!$,;\'@()*[]')
        response, info = fetch_url(self.module, encoded_url, method="GET", force=True, headers={'Metadata': 'true'})
        if info['status'] not in (200, 404):
            time.sleep(3)
            # Request failed.
            # Retry the request then fail...
            self.module.warn('Retrying query to metadata service. First attempt failed: {0}'.format(info['msg']))
            response, info = fetch_url(self.module, encoded_url, method="GET", force=True, headers={'Metadata': 'true'})
            if info['status'] not in (200, 404):
                # Second request failed.
                # Failure.
                self.module.warn('Second query to metadata service failed: {0}'.format(info['msg']))
                self.module.fail_json(msg='Failed to retrieve metadata from Azure: {0}'.format(info['msg']), response=info)
        if response:
            data = response.read()
        else:
            data = None
        return to_text(data)

    def _keyfix(self, fields):
        for key, val in fields.items():
            # Change ':'' and '-' to '_' to ensure valid template variable names
            newkey = re.sub(':|-', '_', key).lower()

            fields[newkey] = fields.pop(key)
            # if list, roll through the list and parse what is inside
            if isinstance(val, list):
                templist = []
                for l in val:
                    templist.append(self._keyfix(l))
                fields[newkey] = templist
            # if dictionary, recurse through
            elif isinstance(val, dict):
                fields[newkey] = self._keyfix(val)
            else:
                fields[newkey] = val

        return fields

    # Designed to create template-friendly variable names.
    # While keyfix just returns a dictionary, this function
    # seperates every key+value in to a variable.
    def _json_to_facts(self, fields, prefix_key=""):

        if (not prefix_key):
            prefix_key = (self._prefix % "_")

        for key, val in fields.items():

            # Change ':'' and '-' to '_' to ensure valid template variable names
            newkey = prefix_key + re.sub(':|-', '_', key).lower()
            # if list, roll through the list and parse what is inside
            if isinstance(val, list):
                for l in val:
                    self._json_to_facts(l, str(newkey) + "_")
            # if dictionary, recurse through
            elif isinstance(val, dict):
                self._json_to_facts(val, str(newkey) + "_")
            else:
                self._data[newkey] = val

    # Take Metadata results and parse JSON
    def fetch(self, uri):

        raw_results = self._fetch(uri)

        if not raw_results:
            return
        # There should not be any newlines.
        # Handle the newlines if they exist.
        raw_result = raw_results.split('\n')

        for result in raw_result:

            try:
                # Results should be a JSON string.
                # Load the JSON in to a dictionary.
                self._data[self._prefix % ""] = json.loads(result)
                for (key, val) in self._data.items():
                    newkey = re.sub(':|-', '_', key).lower()

                    # Change the key name to the ansible-friendly version
                    self._data[newkey] = self._data.pop(key)

                    if isinstance(val, dict):
                        self._data[newkey] = self._keyfix(val)
                self._json_to_facts(self._data[self._prefix % ""])

            except Exception as e:
                self.module.warn("Exception: " + str(e))

    def run(self):
        self.fetch(self.uri_meta)
        return self._data


def main():

    module = AnsibleModule(argument_spec={}, supports_check_mode=True)

    azure_vm_metadata_facts = AzureVmMetadata(module).run()
    azure_vm_metadata_facts_result = dict(changed=False, ansible_facts=azure_vm_metadata_facts)

    module.exit_json(**azure_vm_metadata_facts_result)


if __name__ == '__main__':
    main()