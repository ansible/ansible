#!/usr/bin/python
#coding: utf-8 -*-

# (c) 2013, Benno Joy <benno@ansible.com>
# (c) 2013, John Dewey <john@dewey.ws>
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

import operator
import os

try:
    from novaclient.v1_1 import client as nova_client
    from novaclient.v1_1 import floating_ips
    from novaclient import exceptions
    from novaclient import utils
    import time
except ImportError:
    print("failed=True msg='novaclient is required for this module'")

DOCUMENTATION = '''
---
module: nova_compute
version_added: "1.2"
short_description: Create/Delete VMs from OpenStack
description:
   - Create or Remove virtual machines from Openstack.
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
        - Name that has to be given to the instance
     required: true
     default: None
   image_id:
     description:
        - The id of the base image to boot. Mutually exclusive with image_name
     required: true
     default: None
   image_name:
     description:
        - The name of the base image to boot. Mutually exclusive with image_id
     required: true
     default: None
     version_added: "1.8"
   image_exclude:
     description:
        - Text to use to filter image names, for the case, such as HP, where there are multiple image names matching the common identifying portions. image_exclude is a negative match filter - it is text that may not exist in the image name. Defaults to "(deprecated)"
     version_added: "1.8"
   flavor_id:
     description:
        - The id of the flavor in which the new VM has to be created. Mutually exclusive with flavor_ram
     required: false
     default: 1
   flavor_ram:
     description:
        - The minimum amount of ram in MB that the flavor in which the new VM has to be created must have. Mutually exclusive with flavor_id
     required: false
     default: 1
     version_added: "1.8"
   flavor_include:
     description:
        - Text to use to filter flavor names, for the case, such as Rackspace, where there are multiple flavors that have the same ram count. flavor_include is a positive match filter - it must exist in the flavor name.
     version_added: "1.8"
   key_name:
     description:
        - The key pair name to be used when creating a VM
     required: false
     default: None
   security_groups:
     description:
        - The name of the security group to which the VM should be added
     required: false
     default: None
   nics:
     description:
        - A list of network id's to which the VM's interface should be attached
     required: false
     default: None
   auto_floating_ip:
     description:
        - Should a floating ip be auto created and assigned
     required: false
     default: 'no'
     version_added: "1.8"
   floating_ips:
     description:
        - list of valid floating IPs that pre-exist to assign to this node
     required: false
     default: None
     version_added: "1.8"
   floating_ip_pools:
     description:
        - list of floating IP pools from which to choose a floating IP
     required: false
     default: None
     version_added: "1.8"
   availability_zone:
     description:
        - Name of the availability zone
     required: false
     default: None
     version_added: "1.8"
   meta:
     description:
        - A list of key value pairs that should be provided as a metadata to the new VM
     required: false
     default: None
   wait:
     description:
        - If the module should wait for the VM to be created.
     required: false
     default: 'yes'
   wait_for:
     description:
        - The amount of time the module should wait for the VM to get into active state
     required: false
     default: 180
   config_drive:
     description:
        - Whether to boot the server with config drive enabled
     required: false
     default: 'no'
     version_added: "1.8"
   user_data:
     description:
        - Opaque blob of data which is made available to the instance
     required: false
     default: None
     version_added: "1.6"
   scheduler_hints:
     description:
        - Arbitrary key/value pairs to the scheduler for custom use
     required: false
     default: None
     version_added: "1.9"
requirements: ["novaclient"]
'''

EXAMPLES = '''
# Creates a new VM and attaches to a network and passes metadata to the instance
- nova_compute:
       state: present
       login_username: admin
       login_password: admin
       login_tenant_name: admin
       name: vm1
       image_id: 4f905f38-e52a-43d2-b6ec-754a13ffb529
       key_name: ansible_key
       wait_for: 200
       flavor_id: 4
       nics:
         - net-id: 34605f38-e52a-25d2-b6ec-754a13ffb723
       meta:
         hostname: test1
         group: uge_master

# Creates a new VM in HP Cloud AE1 region availability zone az2 and automatically assigns a floating IP
- name: launch a nova instance
  hosts: localhost
  tasks:
  - name: launch an instance
    nova_compute:
      state: present
      login_username: username
      login_password: Equality7-2521
      login_tenant_name: username-project1
      name: vm1
      auth_url: https://region-b.geo-1.identity.hpcloudsvc.com:35357/v2.0/
      region_name: region-b.geo-1
      availability_zone: az2
      image_id: 9302692b-b787-4b52-a3a6-daebb79cb498
      key_name: test
      wait_for: 200
      flavor_id: 101
      security_groups: default
      auto_floating_ip: yes

# Creates a new VM in HP Cloud AE1 region availability zone az2 and assigns a pre-known floating IP
- name: launch a nova instance
  hosts: localhost
  tasks:
  - name: launch an instance
    nova_compute:
      state: present
      login_username: username
      login_password: Equality7-2521
      login_tenant_name: username-project1
      name: vm1
      auth_url: https://region-b.geo-1.identity.hpcloudsvc.com:35357/v2.0/
      region_name: region-b.geo-1
      availability_zone: az2
      image_id: 9302692b-b787-4b52-a3a6-daebb79cb498
      key_name: test
      wait_for: 200
      flavor_id: 101
      floating-ips:
        - 12.34.56.79

# Creates a new VM with 4G of RAM on Ubuntu Trusty, ignoring deprecated images
- name: launch a nova instance
  hosts: localhost
  tasks:
  - name: launch an instance
    nova_compute:
      name: vm1
      state: present
      login_username: username
      login_password: Equality7-2521
      login_tenant_name: username-project1
      auth_url: https://region-b.geo-1.identity.hpcloudsvc.com:35357/v2.0/
      region_name: region-b.geo-1
      image_name: Ubuntu Server 14.04
      image_exclude: deprecated
      flavor_ram: 4096

# Creates a new VM with 4G of RAM on Ubuntu Trusty on a Rackspace Performance node in DFW
- name: launch a nova instance
  hosts: localhost
  tasks:
  - name: launch an instance
    nova_compute:
      name: vm1
      state: present
      login_username: username
      login_password: Equality7-2521
      login_tenant_name: username-project1
      auth_url: https://identity.api.rackspacecloud.com/v2.0/
      region_name: DFW
      image_name: Ubuntu 14.04 LTS (Trusty Tahr) (PVHVM)
      flavor_ram: 4096
      flavor_include: Performance
'''



def _delete_server(module, nova):
    name = None
    server_list = None
    try:
        server_list = nova.servers.list(True, {'name': module.params['name']})
        if server_list:
            server = [x for x in server_list if x.name == module.params['name']]
            nova.servers.delete(server.pop())
    except Exception, e:
        module.fail_json( msg = "Error in deleting vm: %s" % e.message)
    if module.params['wait'] == 'no':
        module.exit_json(changed = True, result = "deleted")
    expire = time.time() + int(module.params['wait_for'])
    while time.time() < expire:
        name = nova.servers.list(True, {'name': module.params['name']})
        if not name:
            module.exit_json(changed = True, result = "deleted")
        time.sleep(5)
    module.fail_json(msg = "Timed out waiting for server to get deleted, please check manually")


def _add_floating_ip_from_pool(module, nova, server):

    # instantiate FloatingIPManager object
    floating_ip_obj = floating_ips.FloatingIPManager(nova)

    # empty dict and list
    usable_floating_ips = {}
    pools = []

    # user specified
    pools = module.params['floating_ip_pools']

    # get the list of all floating IPs. Mileage may
    # vary according to Nova Compute configuration
    # per cloud provider
    all_floating_ips = floating_ip_obj.list()

    # iterate through all pools of IP address. Empty
    # string means all and is the default value
    for pool in pools:
        # temporary list per pool
        pool_ips = []
        # loop through all floating IPs
        for f_ip in all_floating_ips:
            # if not reserved and the correct pool, add
            if f_ip.instance_id is None and (f_ip.pool == pool):
                pool_ips.append(f_ip.ip)
                # only need one
                break

        # if the list is empty, add for this pool
        if not pool_ips:
            try:
                new_ip = nova.floating_ips.create(pool)
            except Exception, e: 
                module.fail_json(msg = "Unable to create floating ip: %s" % (e.message))
            pool_ips.append(new_ip.ip)
        # Add to the main list
        usable_floating_ips[pool] = pool_ips

    # finally, add ip(s) to instance for each pool
    for pool in usable_floating_ips:
        for ip in usable_floating_ips[pool]:
            try:
                server.add_floating_ip(ip)
                # We only need to assign one ip - but there is an inherent
                # race condition and some other cloud operation may have
                # stolen an available floating ip
                break
            except Exception, e:
                module.fail_json(msg = "Error attaching IP %s to instance %s: %s " % (ip, server.id, e.message))


def _add_floating_ip_list(module, server, ips):
    # add ip(s) to instance
    for ip in ips:
        try:
            server.add_floating_ip(ip)
        except Exception, e:
            module.fail_json(msg = "Error attaching IP %s to instance %s: %s " % (ip, server.id, e.message))


def _add_auto_floating_ip(module, nova, server):

    try:
        new_ip = nova.floating_ips.create()
    except Exception as e:
        module.fail_json(msg = "Unable to create floating ip: %s" % (e))

    try:
        server.add_floating_ip(new_ip)
    except Exception as e:
        # Clean up - we auto-created this ip, and it's not attached
        # to the server, so the cloud will not know what to do with it
        server.floating_ips.delete(new_ip)
        module.fail_json(msg = "Error attaching IP %s to instance %s: %s " % (ip, server.id, e.message))


def _add_floating_ip(module, nova, server):

    if module.params['floating_ip_pools']:
        _add_floating_ip_from_pool(module, nova, server)
    elif module.params['floating_ips']:
        _add_floating_ip_list(module, server, module.params['floating_ips'])
    elif module.params['auto_floating_ip']:
        _add_auto_floating_ip(module, nova, server)
    else:
        return server

    # this may look redundant, but if there is now a
    # floating IP, then it needs to be obtained from
    # a recent server object if the above code path exec'd
    try:
        server = nova.servers.get(server.id)
    except Exception, e:
        module.fail_json(msg = "Error in getting info from instance: %s " % e.message)
    return server


def _get_image_id(module, nova):
    if module.params['image_name']:
        for image in nova.images.list():
            if (module.params['image_name'] in image.name and (
                    not module.params['image_exclude']
                    or module.params['image_exclude'] not in image.name)):
                return image.id
        module.fail_json(msg = "Error finding image id from name(%s)" % module.params['image_name'])
    return module.params['image_id']


def _get_flavor_id(module, nova):
    if module.params['flavor_ram']:
        for flavor in sorted(nova.flavors.list(), key=operator.attrgetter('ram')):
            if (flavor.ram >= module.params['flavor_ram'] and
                    (not module.params['flavor_include'] or module.params['flavor_include'] in flavor.name)):
                return flavor.id
        module.fail_json(msg = "Error finding flavor with %sMB of RAM" % module.params['flavor_ram'])
    return module.params['flavor_id']


def _create_server(module, nova):
    image_id = _get_image_id(module, nova)
    flavor_id = _get_flavor_id(module, nova)
    bootargs = [module.params['name'], image_id, flavor_id]
    bootkwargs = {
                'nics' : module.params['nics'],
                'meta' : module.params['meta'],
                'security_groups': module.params['security_groups'].split(','),
                #userdata is unhyphenated in novaclient, but hyphenated here for consistency with the ec2 module:
                'userdata': module.params['user_data'],
                'config_drive': module.params['config_drive'],
    }

    for optional_param in ('region_name', 'key_name', 'availability_zone', 'scheduler_hints'):
        if module.params[optional_param]:
            bootkwargs[optional_param] = module.params[optional_param]
    try:
        server = nova.servers.create(*bootargs, **bootkwargs)
        server = nova.servers.get(server.id)
    except Exception, e:
            module.fail_json( msg = "Error in creating instance: %s " % e.message)
    if module.params['wait'] == 'yes':
        expire = time.time() + int(module.params['wait_for'])
        while time.time() < expire:
            try:
                server = nova.servers.get(server.id)
            except Exception, e:
                    module.fail_json( msg = "Error in getting info from instance: %s" % e.message)
            if server.status == 'ACTIVE':
                server = _add_floating_ip(module, nova, server)

                private = openstack_find_nova_addresses(getattr(server, 'addresses'), 'fixed', 'private')
                public = openstack_find_nova_addresses(getattr(server, 'addresses'), 'floating', 'public')

                # now exit with info
                module.exit_json(changed = True, id = server.id, private_ip=''.join(private), public_ip=''.join(public), status = server.status, info = server._info)

            if server.status == 'ERROR':
                module.fail_json(msg = "Error in creating the server, please check logs")
            time.sleep(2)

        module.fail_json(msg = "Timeout waiting for the server to come up.. Please check manually")
    if server.status == 'ERROR':
            module.fail_json(msg = "Error in creating the server.. Please check manually")
    private = openstack_find_nova_addresses(getattr(server, 'addresses'), 'fixed', 'private')
    public = openstack_find_nova_addresses(getattr(server, 'addresses'), 'floating', 'public')

    module.exit_json(changed = True, id = info['id'], private_ip=''.join(private), public_ip=''.join(public), status = server.status, info = server._info)


def _delete_floating_ip_list(module, nova, server, extra_ips):
    for ip in extra_ips:
        nova.servers.remove_floating_ip(server=server.id, address=ip)


def _check_floating_ips(module, nova, server):
    changed = False
    if module.params['floating_ip_pools'] or module.params['floating_ips'] or module.params['auto_floating_ip']:
        ips = openstack_find_nova_addresses(server.addresses, 'floating')
        if not ips:
            # If we're configured to have a floating but we don't have one,
            # let's add one
            server = _add_floating_ip(module, nova, server)
            changed = True
        elif module.params['floating_ips']:
            # we were configured to have specific ips, let's make sure we have
            # those
            missing_ips = []
            for ip in module.params['floating_ips']:
                if ip not in ips:
                    missing_ips.append(ip)
            if missing_ips:
                server = _add_floating_ip_list(module, server, missing_ips)
                changed = True
            extra_ips = []
            for ip in ips:
                if ip not in module.params['floating_ips']:
                    extra_ips.append(ip)
            if extra_ips:
                _delete_floating_ip_list(module, server, extra_ips)
                changed = True
    return (changed, server)


def _get_server_state(module, nova):
    server = None
    try:
        servers = nova.servers.list(True, {'name': module.params['name']})
        if servers:
            # the {'name': module.params['name']} will also return servers
            # with names that partially match the server name, so we have to
            # strictly filter here
            servers = [x for x in servers if x.name == module.params['name']]
            if servers:
                server = servers[0]
    except Exception, e:
        module.fail_json(msg = "Error in getting the server list: %s" % e.message)
    if server and module.params['state'] == 'present':
        if server.status != 'ACTIVE':
            module.fail_json( msg="The VM is available but not Active. state:" + server.status)
        (ip_changed, server) = _check_floating_ips(module, nova, server)
        private = openstack_find_nova_addresses(getattr(server, 'addresses'), 'fixed', 'private')
        public = openstack_find_nova_addresses(getattr(server, 'addresses'), 'floating', 'public')
        module.exit_json(changed = ip_changed, id = server.id, public_ip = public, private_ip = private, info = server._info)
    if server and module.params['state'] == 'absent':
        return True
    if module.params['state'] == 'absent':
        module.exit_json(changed = False, result = "not present")
    return True



def main():
    argument_spec = openstack_argument_spec()
    argument_spec.update(dict(
        name                            = dict(required=True),
        image_id                        = dict(default=None),
        image_name                      = dict(default=None),
        image_exclude                   = dict(default='(deprecated)'),
        flavor_id                       = dict(default=1),
        flavor_ram                      = dict(default=None, type='int'),
        flavor_include                  = dict(default=None),
        key_name                        = dict(default=None),
        security_groups                 = dict(default='default'),
        nics                            = dict(default=None),
        meta                            = dict(default=None),
        wait                            = dict(default='yes', choices=['yes', 'no']),
        wait_for                        = dict(default=180),
        state                           = dict(default='present', choices=['absent', 'present']),
        user_data                       = dict(default=None),
        config_drive                    = dict(default=False, type='bool'),
        auto_floating_ip                = dict(default=False, type='bool'),
        floating_ips                    = dict(default=None),
        floating_ip_pools               = dict(default=None),
        scheduler_hints                 = dict(default=None),
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ['auto_floating_ip','floating_ips'],
            ['auto_floating_ip','floating_ip_pools'],
            ['floating_ips','floating_ip_pools'],
            ['image_id','image_name'],
            ['flavor_id','flavor_ram'],
        ],
    )

    nova = nova_client.Client(module.params['login_username'],
                              module.params['login_password'],
                              module.params['login_tenant_name'],
                              module.params['auth_url'],
                              region_name=module.params['region_name'],
                              service_type='compute')
    try:
        nova.authenticate()
    except exceptions.Unauthorized, e:
        module.fail_json(msg = "Invalid OpenStack Nova credentials.: %s" % e.message)
    except exceptions.AuthorizationFailure, e:
        module.fail_json(msg = "Unable to authorize user: %s" % e.message)

    if module.params['state'] == 'present':
        if not module.params['image_id'] and not module.params['image_name']:
            module.fail_json( msg = "Parameter 'image_id' or `image_name` is required if state == 'present'")
        else:
            _get_server_state(module, nova)
            _create_server(module, nova)
    if module.params['state'] == 'absent':
        _get_server_state(module, nova)
        _delete_server(module, nova)

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
main()
