#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Benno Joy <benno@ansible.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: glance_image
version_added: "1.2"
short_description: Add/Delete images from glance
description:
   - Add or Remove images from the glance repository.
options:
   login_username:
     description:
        - login username to authenticate to keystone
     required: true
     default: admin
   login_password:
     description:
        - Password of login user
     required: true
     default: 'yes'
   login_tenant_name:
     description:
        - The tenant name of the login user
     required: true
     default: 'yes'
   auth_url:
     description:
        - The keystone url for authentication
     required: false
     default: 'http://127.0.0.1:35357/v2.0/'
   region_name:
     description:
        - Name of the region
     required: false
     default: None
   state:
     description:
        - Indicate desired state of the resource
     choices: ['present', 'absent']
     default: present
   name:
     description:
        - Name that has to be given to the image
     required: true
     default: None
   disk_format:
     description:
        - The format of the disk that is getting uploaded
     required: false
     default: qcow2
   container_format:
     description:
        - The format of the container
     required: false
     default: bare
   owner:
     description:
        - The owner of the image
     required: false
     default: None
   min_disk:
     description:
        - The minimum disk space required to deploy this image
     required: false
     default: None
   min_ram:
     description:
        - The minimum ram required to deploy this image
     required: false
     default: None
   is_public:
     description:
        - Whether the image can be accessed publicly
     required: false
     default: 'yes'
   copy_from:
     description:
        - A url from where the image can be downloaded, mutually exclusive with file parameter
     required: false
     default: None
   timeout:
     description:
        - The time to wait for the image process to complete in seconds
     required: false
     default: 180
   file:
     description:
        - The path to the file which has to be uploaded, mutually exclusive with copy_from
     required: false
     default: None
   endpoint_type:
     description:
        - The name of the glance service's endpoint URL type
     choices: [publicURL, internalURL]
     required: false
     default: publicURL
     version_added: "1.7"
requirements: ["glanceclient", "keystoneclient"]

'''

EXAMPLES = '''
# Upload an image from an HTTP URL
- glance_image: login_username=admin
                login_password=passme
                login_tenant_name=admin
                name=cirros
                container_format=bare
                disk_format=qcow2
                state=present
                copy_from=http:launchpad.net/cirros/trunk/0.3.0/+download/cirros-0.3.0-x86_64-disk.img
'''

import time
try:
    import glanceclient
    from keystoneclient.v2_0 import client as ksclient
except ImportError:
    print("failed=True msg='glanceclient and keystone client are required'")


def _get_ksclient(module, kwargs):
    try:
        client = ksclient.Client(username=kwargs.get('login_username'),
                                 password=kwargs.get('login_password'),
                                 tenant_name=kwargs.get('login_tenant_name'),
                                 auth_url=kwargs.get('auth_url'))
    except Exception, e:
        module.fail_json(msg="Error authenticating to the keystone: %s " % e.message)
    return client 


def _get_endpoint(module, client, endpoint_type):
    try:
        endpoint = client.service_catalog.url_for(service_type='image', endpoint_type=endpoint_type)
    except Exception, e:
        module.fail_json(msg="Error getting endpoint for glance: %s" % e.message)
    return endpoint


def _get_glance_client(module, kwargs):
    _ksclient = _get_ksclient(module, kwargs)
    token = _ksclient.auth_token
    endpoint =_get_endpoint(module, _ksclient, kwargs.get('endpoint_type'))
    kwargs = {
            'token': token,
    }
    try:
        client = glanceclient.Client('1', endpoint, **kwargs)
    except Exception, e:
        module.fail_json(msg="Error in connecting to glance: %s" % e.message)
    return client


def _glance_image_present(module, params, client):
    try:
        for image in client.images.list():
            if image.name == params['name']:
                return image.id 
        return None
    except Exception, e:
        module.fail_json(msg="Error in fetching image list: %s" % e.message)


def _glance_image_create(module, params, client):
    kwargs = {
                'name':             params.get('name'),
                'disk_format':      params.get('disk_format'),
                'container_format': params.get('container_format'),
                'owner':            params.get('owner'),
                'is_public':        params.get('is_public'),
                'copy_from':        params.get('copy_from'),
    }
    try:
        timeout = float(params.get('timeout'))
        expire = time.time() + timeout
        image = client.images.create(**kwargs)
        if not params['copy_from']:
            image.update(data=open(params['file'], 'rb'))
        while time.time() < expire:
            image = client.images.get(image.id)
            if image.status == 'active':
                break
            time.sleep(5)
    except Exception, e:
        module.fail_json(msg="Error in creating image: %s" % e.message)
    if image.status == 'active':
        module.exit_json(changed=True, result=image.status, id=image.id)
    else:
        module.fail_json(msg=" The module timed out, please check manually " + image.status)


def _glance_delete_image(module, params, client):
    try:
        for image in client.images.list():
            if image.name == params['name']:
                client.images.delete(image)
    except Exception, e:
        module.fail_json(msg="Error in deleting image: %s" % e.message)
    module.exit_json(changed=True, result="Deleted")


def main():

    argument_spec = openstack_argument_spec()
    argument_spec.update(dict(
        name              = dict(required=True),
        disk_format       = dict(default='qcow2', choices=['aki', 'vhd', 'vmdk', 'raw', 'qcow2', 'vdi', 'iso']),
        container_format  = dict(default='bare', choices=['aki', 'ari', 'bare', 'ovf']),
        owner             = dict(default=None),
        min_disk          = dict(default=None),
        min_ram           = dict(default=None),
        is_public         = dict(default=True),
        copy_from         = dict(default= None),
        timeout           = dict(default=180),
        file              = dict(default=None),
        endpoint_type     = dict(default='publicURL', choices=['publicURL', 'internalURL']),
        state             = dict(default='present', choices=['absent', 'present'])
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive = [['file','copy_from']],
    )
    if module.params['state'] == 'present':
        if not module.params['file'] and not module.params['copy_from']:
            module.fail_json(msg="Either file or copy_from variable should be set to create the image")
        client = _get_glance_client(module, module.params)
        id = _glance_image_present(module, module.params, client)
        if not id:
            _glance_image_create(module, module.params, client)
        module.exit_json(changed=False, id=id, result="success")

    if module.params['state'] == 'absent':
        client = _get_glance_client(module, module.params)
        id = _glance_image_present(module, module.params, client)
        if not id:
            module.exit_json(changed=False, result="Success")
        else:
            _glance_delete_image(module, module.params, client)

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
main()
