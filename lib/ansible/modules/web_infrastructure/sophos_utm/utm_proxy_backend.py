#!/usr/bin/python

from __future__ import absolute_import, division, print_function

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url

from ansible.module_utils.utm_utils import lookup_entry, clean_result, is_object_changed

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
---
module: utm_proxy_backend

author: 
    - Johannes Brunswicker (@MatrixCrawler)

short_description: create, update or destroy reverse_proxy backend entry in Sophos UTM

description:
    - Create, update or destroy a reverse_proxy backend entry in SOPHOS UTM.
    - This module needs to have the REST Ability of the UTM to be activated.

version_added: "2.7" 

options:
    utm_host:
        description:
          - The REST Endpoint of the Sophos UTM
        required: true
    utm_port:
        description:
            - the port of the rest interface
        default: 4444
    utm_token:
        description:
          - The token used to identify at the REST-API.
            See U(https://www.sophos.com/en-us/medialibrary/PDFs/documentation/UTMonAWS/Sophos-UTM-RESTful-API.pdf?la=en), Chapter 2.4.2
        required: true
    utm_protocol:
        description:
          - The protocol of the REST Endpoint.
        default: https
    validate_certs: 
        description:
          - whether the rest interface's ssl certificate should be verified or not
        default: True
    name:
        description:
          - The name of the object. Will be used to identify the entry
        required: true
    state:
        description:
          - The desired state of the object
        default: present
    disable_backend_connection_pooling:
        description:
          - whether to disable the backend connection pooling
        default: False
    backend_host:
        description:
          - The reference name of the host object. Can be determined with utm_dns_entry
    comment:
        description:
          - An optional comment to add to the object
    keepalive:
        description:
          - Whether to enable the http keepalive
        default: False
    path:
        description:
          - The path for the site path routing
        default: /
    backend_port:
        description:
          - The port of the backend service
        required: True
    ssl:
        description:
          - whether to enable ssl or not
        default: False
    status: 
        description:
          - the status of the entry
        default: True
    timeout: 
        description:
          - The keepalive timeout in seconds
        default: 300
"""


class UTMBackendEntry:

    def __init__(self, url):
        self.request_url = url
        """
        The important_keys will be checked for changes to determine whether the object needs to be updated
        """
        self.important_keys = ["comment", "disable_backend_connection_pooling", "host", "keepalive", "path",
                               "port", "ssl", "status", "timeout"]

    def add(self, module):
        """
    adds or updates a host object on utm
        :param module:
        """
        is_changed = False
        info, result = lookup_entry(module, self.request_url)
        if info["status"] >= 400:
            module.fail_json(result=json.loads(info))
        else:
            if result is None:
                response, info = fetch_url(module, self.request_url, method="POST",
                                           headers={"Accept": "application/json", "Content-type": "application/json"},
                                           data=module.jsonify(module.params))
                if info["status"] >= 400:
                    module.fail_json(result=json.loads(info))
                is_changed = True
                result = clean_result(json.loads(response.read()))
            else:
                if is_object_changed(self.important_keys, module, result):
                    response, info = fetch_url(module, self.request_url + result['_ref'], method="PUT",
                                               headers={"Accept": "application/json",
                                                        "Content-type": "application/json"},
                                               data=module.jsonify(module.params))
                    if info['status'] >= 400:
                        module.fail_json(result=json.loads(info))
                    is_changed = True
                    result = clean_result(json.loads(response.read()))
            module.exit_json(result=result, changed=is_changed)

    def remove(self, module):
        is_changed = False
        info, result = lookup_entry(module, self.request_url)
        if result is not None:
            response, info = fetch_url(module, self.request_url + result['_ref'], method="DELETE",
                                       headers={"Accept": "application/json", "X-Restd-Err-Ack": "all"},
                                       data=module.jsonify(module.params))
            if info["status"] >= 400:
                module.fail_json(result=json.loads(info))
            else:
                is_changed = True
        module.exit_json(changed=is_changed)


def update_utm(module):
    request_url = module.params.get('utm_protocol') + "://" + module.params.get('utm_host') + ":" + str(
        module.params.get('utm_port')) + "/api/objects/reverse_proxy/backend/"
    utm_dns_entry = UTMBackendEntry(request_url)

    module.params['url_username'] = 'token'
    module.params['url_password'] = module.params.get('utm_token')

    if module.params.get('state') == 'present':
        utm_dns_entry.add(module)
    else:
        utm_dns_entry.remove(module)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            utm_host=dict(type='str', required=True),
            utm_port=dict(type='int', default=4444),
            utm_token=dict(type='str', required=True, no_log=True),
            utm_protocol=dict(type='str', required=False, default="https", choices=["https", "http"]),
            validate_certs=dict(type='bool', required=False, default=True),
            state=dict(default='present', choices=['present', 'absent']),
            name=dict(type='str', required=True),

            disable_backend_connection_pooling=dict(type='bool', required=False, default=False),
            host=dict(type='str', required=True),
            comment=dict(type='str', required=False, default=""),
            keepalive=dict(type='bool', required=False, default=False),
            path=dict(type='str', required=False, default="/"),
            port=dict(type='int', required=True),
            ssl=dict(type='bool', required=False, default=False),
            status=dict(type='bool', required=False, default=True),
            timeout=dict(type='int', required=False, default=300),
        ),
        supports_check_mode=False
    )
    try:
        update_utm(module)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
