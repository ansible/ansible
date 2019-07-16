#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Renato Orgito <orgito@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: spectrum_device
short_description: Creates/deletes devices in CA Spectrum.
description:
   - This module allows you to create and delete devices in CA Spectrum U(https://www.ca.com/us/products/ca-spectrum.html).
   - Tested on CA Spectrum 9.4.2, 10.1.1 and 10.2.1
version_added: "2.6"
author: "Renato Orgito (@orgito)"
options:
    device:
        aliases: [ host, name ]
        required: true
        description:
            - IP address of the device.
            - If a hostname is given, it will be resolved to the IP address.
    community:
        description:
            - SNMP community used for device discovery.
            - Required when C(state=present).
    landscape:
        required: true
        description:
            - Landscape handle of the SpectroServer to which add or remove the device.
    state:
        required: false
        description:
            - On C(present) creates the device when it does not exist.
            - On C(absent) removes the device when it exists.
        choices: ['present', 'absent']
        default: 'present'
    url:
        aliases: [ oneclick_url ]
        required: true
        description:
            - HTTP, HTTPS URL of the Oneclick server in the form (http|https)://host.domain[:port]
    url_username:
        aliases: [ oneclick_user ]
        required: true
        description:
            - Oneclick user name.
    url_password:
        aliases: [ oneclick_password ]
        required: true
        description:
            - Oneclick user password.
    use_proxy:
        required: false
        description:
            - if C(no), it will not use a proxy, even if one is defined in an environment
                variable on the target hosts.
        default: 'yes'
        type: bool
    validate_certs:
        required: false
        description:
            - If C(no), SSL certificates will not be validated. This should only be used
                on personally controlled sites using self-signed certificates.
        default: 'yes'
        type: bool
    agentport:
        required: false
        description:
            - UDP port used for SNMP discovery.
        default: 161
notes:
   -  The devices will be created inside the I(Universe) container of the specified landscape.
   -  All the operations will be performed only on the specified landscape.
'''

EXAMPLES = '''
- name: Add device to CA Spectrum
  local_action:
    module: spectrum_device
    device: '{{ ansible_host }}'
    community: secret
    landscape: '0x100000'
    oneclick_url: http://oneclick.example.com:8080
    oneclick_user: username
    oneclick_password: password
    state: present


- name: Remove device from CA Spectrum
  local_action:
    module: spectrum_device
    device: '{{ ansible_host }}'
    landscape: '{{ landscape_handle }}'
    oneclick_url: http://oneclick.example.com:8080
    oneclick_user: username
    oneclick_password: password
    use_proxy: no
    state: absent
'''

RETURN = '''
device:
  description: device data when state = present
  returned: success
  type: dict
  sample: {'model_handle': '0x1007ab', 'landscape': '0x100000', 'address': '10.10.5.1'}
'''

from socket import gethostbyname, gaierror
import xml.etree.ElementTree as ET

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


def request(resource, xml=None, method=None):
    headers = {
        "Content-Type": "application/xml",
        "Accept": "application/xml"
    }

    url = module.params['oneclick_url'] + '/spectrum/restful/' + resource

    response, info = fetch_url(module, url, data=xml, method=method, headers=headers, timeout=45)

    if info['status'] == 401:
        module.fail_json(msg="failed to authenticate to Oneclick server")

    if info['status'] not in (200, 201, 204):
        module.fail_json(msg=info['msg'])

    return response.read()


def post(resource, xml=None):
    return request(resource, xml=xml, method='POST')


def delete(resource):
    return request(resource, xml=None, method='DELETE')


def get_ip():
    try:
        device_ip = gethostbyname(module.params.get('device'))
    except gaierror:
        module.fail_json(msg="failed to resolve device ip address for '%s'" % module.params.get('device'))

    return device_ip


def get_device(device_ip):
    """Query OneClick for the device using the IP Address"""
    resource = '/models'
    landscape_min = "0x%x" % int(module.params.get('landscape'), 16)
    landscape_max = "0x%x" % (int(module.params.get('landscape'), 16) + 0x100000)

    xml = """<?xml version="1.0" encoding="UTF-8"?>
        <rs:model-request throttlesize="5"
        xmlns:rs="http://www.ca.com/spectrum/restful/schema/request"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.ca.com/spectrum/restful/schema/request ../../../xsd/Request.xsd">
            <rs:target-models>
            <rs:models-search>
                <rs:search-criteria xmlns="http://www.ca.com/spectrum/restful/schema/filter">
                    <action-models>
                        <filtered-models>
                            <and>
                                <equals>
                                    <model-type>SearchManager</model-type>
                                </equals>
                                <greater-than>
                                    <attribute id="0x129fa">
                                        <value>{mh_min}</value>
                                    </attribute>
                                </greater-than>
                                <less-than>
                                    <attribute id="0x129fa">
                                        <value>{mh_max}</value>
                                    </attribute>
                                </less-than>
                            </and>
                        </filtered-models>
                        <action>FIND_DEV_MODELS_BY_IP</action>
                        <attribute id="AttributeID.NETWORK_ADDRESS">
                            <value>{search_ip}</value>
                        </attribute>
                    </action-models>
                </rs:search-criteria>
            </rs:models-search>
            </rs:target-models>
            <rs:requested-attribute id="0x12d7f" /> <!--Network Address-->
        </rs:model-request>
        """.format(search_ip=device_ip, mh_min=landscape_min, mh_max=landscape_max)

    result = post(resource, xml=xml)

    root = ET.fromstring(result)

    if root.get('total-models') == '0':
        return None

    namespace = dict(ca='http://www.ca.com/spectrum/restful/schema/response')

    # get the first device
    model = root.find('ca:model-responses', namespace).find('ca:model', namespace)

    if model.get('error'):
        module.fail_json(msg="error checking device: %s" % model.get('error'))

    # get the attributes
    model_handle = model.get('mh')

    model_address = model.find('./*[@id="0x12d7f"]').text

    # derive the landscape handler from the model handler of the device
    model_landscape = "0x%x" % int(int(model_handle, 16) // 0x100000 * 0x100000)

    device = dict(
        model_handle=model_handle,
        address=model_address,
        landscape=model_landscape)

    return device


def add_device():
    device_ip = get_ip()
    device = get_device(device_ip)

    if device:
        module.exit_json(changed=False, device=device)

    if module.check_mode:
        device = dict(
            model_handle=None,
            address=device_ip,
            landscape="0x%x" % int(module.params.get('landscape'), 16))
        module.exit_json(changed=True, device=device)

    resource = 'model?ipaddress=' + device_ip + '&commstring=' + module.params.get('community')
    resource += '&landscapeid=' + module.params.get('landscape')

    if module.params.get('agentport', None):
        resource += '&agentport=' + str(module.params.get('agentport', 161))

    result = post(resource)
    root = ET.fromstring(result)

    if root.get('error') != 'Success':
        module.fail_json(msg=root.get('error-message'))

    namespace = dict(ca='http://www.ca.com/spectrum/restful/schema/response')
    model = root.find('ca:model', namespace)

    model_handle = model.get('mh')
    model_landscape = "0x%x" % int(int(model_handle, 16) // 0x100000 * 0x100000)

    device = dict(
        model_handle=model_handle,
        address=device_ip,
        landscape=model_landscape,
    )

    module.exit_json(changed=True, device=device)


def remove_device():
    device_ip = get_ip()
    device = get_device(device_ip)

    if device is None:
        module.exit_json(changed=False)

    if module.check_mode:
        module.exit_json(changed=True)

    resource = '/model/' + device['model_handle']
    result = delete(resource)

    root = ET.fromstring(result)

    namespace = dict(ca='http://www.ca.com/spectrum/restful/schema/response')
    error = root.find('ca:error', namespace).text

    if error != 'Success':
        error_message = root.find('ca:error-message', namespace).text
        module.fail_json(msg="%s %s" % (error, error_message))

    module.exit_json(changed=True)


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            device=dict(required=True, aliases=['host', 'name']),
            landscape=dict(required=True),
            state=dict(choices=['present', 'absent'], default='present'),
            community=dict(required=True, no_log=True),
            agentport=dict(type='int', default=161),
            url=dict(required=True, aliases=['oneclick_url']),
            url_username=dict(required=True, aliases=['oneclick_user']),
            url_password=dict(required=True, no_log=True, aliases=['oneclick_password']),
            use_proxy=dict(type='bool', default='yes'),
            validate_certs=dict(type='bool', default='yes'),
        ),
        required_if=[('state', 'present', ['community'])],
        supports_check_mode=True
    )

    if module.params.get('state') == 'present':
        add_device()
    else:
        remove_device()


if __name__ == '__main__':
    main()
