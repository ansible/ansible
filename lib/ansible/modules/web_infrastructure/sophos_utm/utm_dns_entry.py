#!/usr/bin/python
import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url

from lib.ansible.modules.web_infrastructure.sophos_utm.utm_utils import lookup_entry

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
---
module: utm_dns

author: 
    - Johannes Brunswicker (@MatrixCrawler)

short_description: create, update or destroy dns entry in Sophos UTM

description:
    - Create, update or destroy a dns entry in SOPHOS UTM.
    - This module needs to have the REST Ability of the UTM to be activated.

requirements:
    - requests

version_added: "2.7" 

options:
    host:
        description:
          - The REST Endpoint of the Sophos UTM
        required: true
    port:
        description:
            - the port of the rest interface
        default: 4444
    token:
        description:
          - The token used to identify at the REST-API.
            See U(https://www.sophos.com/en-us/medialibrary/PDFs/documentation/UTMonAWS/Sophos-UTM-RESTful-API.pdf?la=en), Chapter 2.4.2
        required: true
    name:
        description:
          - The name of the object. Will be used to identify the entry
        required: true
    address:
        description:
          - The IPV4 Address of the entry. Can be left empty for automatic resolving.
        default: 0.0.0.0
    address6:
        description:
          - The IPV6 Address of the entry. Can be left empty for automatic resolving.
        default: ::
    comment:
        description:
          - An optional comment to add to the dns host object
    hostname:
        description:
          - The hostname for the dns host object
        required: True
    interface:
        description:
          - The reference name of the interface to use. If not provided the default interface will be used
    protocol:
        description:
          - The protocol of the REST Endpoint.
        default: https
    resolved:
        description:
          - whether the hostname' s ipv4 address is already resolved or not
        default: False
    resolved6:
        description:
          - whether the hostname' s ipv6 address is already resolved or not
        default: False
    state:
        description:
          - The desired state of the object
        default: present
    timeout: 
        description:
          - the timeout for the utm to resolve the ip address for the hostname again
        default: 0
    validate_certs: 
        description:
          - whether the rest interface's ssl certificate should be verified or not
        default: True
"""


class UTMDnsEntry:

    def __init__(self, url):
        self.request_url = url

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
            else:
                if self.is_object_to_change(module, result):
                    response, info = fetch_url(module, self.request_url + result['_ref'], method="PUT",
                                               headers={"Accept": "application/json",
                                                        "Content-type": "application/json"},
                                               data=module.jsonify(module.params))
                    if info['status'] >= 400:
                        module.fail_json(result=json.loads(info))
                    is_changed = True
            module.exit_json(result=result, changed=is_changed)

    def is_object_to_change(module, result):
        if result['hostname'] != module.params.get('hostname') or \
                result['comment'] != module.params.get('comment') or \
                result['interface'] != module.params.get("interface"):
            return True
        return False

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
    request_url = module.params.get('protocol') + "://" + module.params.get('host') + ":" + str(
        module.params.get('port')) + "/api/objects/network/dns_host/"
    utm_dns_entry = UTMDnsEntry(request_url)

    module.params['url_username'] = 'token'
    module.params['url_password'] = module.params.get('token')

    if module.params.get('state') == 'present':
        utm_dns_entry.add(module)
    else:
        utm_dns_entry.remove(module)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            port=dict(type='int', default=4444),
            token=dict(type='str', required=True, no_log=True),
            name=dict(type='str', required=True),
            address=dict(type='str', required=False, default='0.0.0.0'),
            address6=dict(type='str', required=False, default='::'),
            comment=dict(type='str', required=False, default=""),
            hostname=dict(type='str', required=True),
            interface=dict(type='str', required=False, default=""),
            protocol=dict(type='str', required=False, default="https", choices=["https", "http"]),
            resolved=dict(type='bool', required=False, default=False),
            resolved6=dict(type='bool', required=False, default=False),
            state=dict(default='present', choices=['present', 'absent']),
            timeout=dict(type='int', required=False, default=0),
            validate_certs=dict(type='bool', required=False, default=True),
        ),
        supports_check_mode=False
    )
    try:
        update_utm(module)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
