#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Ansible module to add boundary meters.

(c) 2013, curtis <curtis@serverascode.com>

This file is part of Ansible

Ansible is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Ansible is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
"""

DOCUMENTATION = '''

module: boundary_meter
short_description: Manage boundary meters
description:
    - This module manages boundary meters
version_added: "1.3"
author: "curtis (@ccollicutt)"
requirements:
    - Boundary API access
    - bprobe is required to send data, but not to register a meter
options:
    name:
        description:
            - meter name
        required: true
    state:
        description:
            - Whether to create or remove the client from boundary
        required: false
        default: true
        choices: ["present", "absent"]
    apiid:
        description:
            - Organizations boundary API ID
        required: true
    apikey:
        description:
            - Organizations boundary API KEY
        required: true
    validate_certs:
        description:
            - If C(no), SSL certificates will not be validated. This should only be used
              on personally controlled sites using self-signed certificates.
        required: false
        default: 'yes'
        choices: ['yes', 'no']
        version_added: 1.5.1

notes:
    - This module does not yet support boundary tags.

'''

EXAMPLES='''
- name: Create meter
  boundary_meter: apiid=AAAAAA api_key=BBBBBB state=present name={{ inventory_hostname }}"

- name: Delete meter
  boundary_meter: apiid=AAAAAA api_key=BBBBBB state=absent name={{ inventory_hostname }}"

'''

import base64
import os

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        # Let snippet from module_utils/basic.py return a proper error in this case
        pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


api_host = "api.boundary.com"
config_directory = "/etc/bprobe"


# "resource" like thing or apikey?
def auth_encode(apikey):
    auth = base64.standard_b64encode(apikey)
    auth.replace("\n", "")
    return auth


def build_url(name, apiid, action, meter_id=None, cert_type=None):
    if action == "create":
        return 'https://%s/%s/meters' % (api_host, apiid)
    elif action == "search":
        return "https://%s/%s/meters?name=%s" % (api_host, apiid, name)
    elif action == "certificates":
        return "https://%s/%s/meters/%s/%s.pem" % (api_host, apiid, meter_id, cert_type)
    elif action == "tags":
        return  "https://%s/%s/meters/%s/tags" % (api_host, apiid, meter_id)
    elif action == "delete":
        return  "https://%s/%s/meters/%s" % (api_host, apiid, meter_id)

def http_request(module, name, apiid, apikey, action, data=None, meter_id=None, cert_type=None):
    
    if meter_id is None:
        url = build_url(name, apiid, action)
    else:
        if cert_type is None:
            url = build_url(name, apiid, action, meter_id)
        else:
            url = build_url(name, apiid, action, meter_id, cert_type)

    headers = dict()
    headers["Authorization"] = "Basic %s" % auth_encode(apikey)
    headers["Content-Type"] = "application/json"

    return fetch_url(module, url, data=data, headers=headers)

def create_meter(module, name, apiid, apikey):

    meters = search_meter(module, name, apiid, apikey)

    if len(meters) > 0:
        # If the meter already exists, do nothing
        module.exit_json(status="Meter " + name + " already exists",changed=False)
    else:
        # If it doesn't exist, create it
        body = '{"name":"' + name + '"}'
        response, info = http_request(module, name, apiid, apikey, data=body, action="create")

        if info['status'] != 200:
            module.fail_json(msg="Failed to connect to api host to create meter")

        # If the config directory doesn't exist, create it
        if not os.path.exists(config_directory):
            try:
                os.makedirs(config_directory)
            except:
                module.fail_json("Could not create " + config_directory)


        # Download both cert files from the api host
        types = ['key', 'cert']
        for cert_type in types:
            try:
                # If we can't open the file it's not there, so we should download it
                cert_file = open('%s/%s.pem' % (config_directory,cert_type))
            except IOError:
                # Now download the file...
                rc = download_request(module, name, apiid, apikey, cert_type)
                if rc == False:
                    module.fail_json("Download request for " + cert_type + ".pem failed")

        return 0, "Meter " + name + " created"

def search_meter(module, name, apiid, apikey):

    response, info = http_request(module, name, apiid, apikey, action="search")

    if info['status'] != 200:
        module.fail_json("Failed to connect to api host to search for meter")

    # Return meters
    return json.loads(response.read())

def get_meter_id(module, name, apiid, apikey):
    # In order to delete the meter we need its id
    meters = search_meter(module, name, apiid, apikey)

    if len(meters) > 0:
        return meters[0]['id']
    else:
        return None

def delete_meter(module, name, apiid, apikey):

    meter_id = get_meter_id(module, name, apiid, apikey)

    if meter_id is None:
        return 1, "Meter does not exist, so can't delete it"
    else:
        response, info = http_request(module, name, apiid, apikey, action, meter_id)
        if info['status'] != 200:
            module.fail_json("Failed to delete meter")

        # Each new meter gets a new key.pem and ca.pem file, so they should be deleted
        types = ['cert', 'key']
        for cert_type in types:
            try:
                cert_file = '%s/%s.pem' % (config_directory,cert_type)
                os.remove(cert_file)
            except OSError:
                module.fail_json("Failed to remove " + cert_type + ".pem file")

    return 0, "Meter " + name + " deleted"

def download_request(module, name, apiid, apikey, cert_type):

    meter_id = get_meter_id(module, name, apiid, apikey)

    if meter_id is not None:
        action = "certificates"
        response, info = http_request(module, name, apiid, apikey, action, meter_id, cert_type)
        if info['status'] != 200:
            module.fail_json("Failed to connect to api host to download certificate")

        if result:
            try:
                cert_file_path = '%s/%s.pem' % (config_directory,cert_type)
                body = response.read()
                cert_file = open(cert_file_path, 'w')
                cert_file.write(body)
                cert_file.close()
                os.chmod(cert_file_path, int('0600', 8))
            except:
                module.fail_json("Could not write to certificate file")

        return True
    else:
        module.fail_json("Could not get meter id")

def main():

    module = AnsibleModule(
        argument_spec=dict(
        state=dict(required=True, choices=['present', 'absent']),
        name=dict(required=False),
        apikey=dict(required=True),
        apiid=dict(required=True),
        validate_certs = dict(default='yes', type='bool'),
        )
    )

    state = module.params['state']
    name= module.params['name']
    apikey = module.params['api_key']
    apiid = module.params['api_id']

    if state == "present":
        (rc, result) = create_meter(module, name, apiid, apikey)

    if state == "absent":
        (rc, result) = delete_meter(module, name, apiid, apikey)

    if rc != 0:
        module.fail_json(msg=result)

    module.exit_json(status=result,changed=True)


if __name__ == '__main__':
    main()

