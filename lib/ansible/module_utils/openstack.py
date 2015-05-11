# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os


def openstack_argument_spec():
    # DEPRECATED: This argument spec is only used for the deprecated old
    # OpenStack modules. It turns out that modern OpenStack auth is WAY
    # more complex than this.
    # Consume standard OpenStack environment variables.
    # This is mainly only useful for ad-hoc command line operation as
    # in playbooks one would assume variables would be used appropriately
    OS_AUTH_URL=os.environ.get('OS_AUTH_URL', 'http://127.0.0.1:35357/v2.0/')
    OS_PASSWORD=os.environ.get('OS_PASSWORD', None)
    OS_REGION_NAME=os.environ.get('OS_REGION_NAME', None)
    OS_USERNAME=os.environ.get('OS_USERNAME', 'admin')
    OS_TENANT_NAME=os.environ.get('OS_TENANT_NAME', OS_USERNAME)

    spec = dict(
        login_username                  = dict(default=OS_USERNAME),
        auth_url                        = dict(default=OS_AUTH_URL),
        region_name                     = dict(default=OS_REGION_NAME),
        availability_zone               = dict(default=None),
    )
    if OS_PASSWORD:
        spec['login_password'] = dict(default=OS_PASSWORD)
    else:
        spec['login_password'] = dict(required=True)
    if OS_TENANT_NAME:
        spec['login_tenant_name'] = dict(default=OS_TENANT_NAME)
    else:
        spec['login_tenant_name'] = dict(required=True)
    return spec

def openstack_find_nova_addresses(addresses, ext_tag, key_name=None):

    ret = []
    for (k, v) in addresses.iteritems():
        if key_name and k == key_name:
            ret.extend([addrs['addr'] for addrs in v])
        else:
            for interface_spec in v:
                if 'OS-EXT-IPS:type' in interface_spec and interface_spec['OS-EXT-IPS:type'] == ext_tag:
                    ret.append(interface_spec['addr'])
    return ret

def openstack_full_argument_spec(**kwargs):
    spec = dict(
        cloud=dict(default=None),
        auth_plugin=dict(default=None),
        auth=dict(default=None),
        auth_token=dict(default=None),
        region_name=dict(default=None),
        availability_zone=dict(default=None),
        state=dict(default='present', choices=['absent', 'present']),
        wait=dict(default=True, type='bool'),
        timeout=dict(default=180, type='int'),
        endpoint_type=dict(
            default='publicURL', choices=['publicURL', 'internalURL']
        )
    )
    spec.update(kwargs)
    return spec


def openstack_module_kwargs(**kwargs):
    ret = dict(
        mutually_exclusive=[
            ['auth', 'auth_token'],
            ['auth_plugin', 'auth_token'],
        ],
    )
    for key in ('mutually_exclusive', 'required_together', 'required_one_of'):
        if key in kwargs:
            if key in ret:
                ret[key].extend(kwargs[key])
            else:
                ret[key] = kwargs[key]

    return ret
