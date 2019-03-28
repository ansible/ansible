# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by
# Ansible still belong to the author of the module, and may assign their own
# license to the complete work.
#
# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
import re
from uuid import UUID

from ansible.module_utils.six import text_type, binary_type

FINAL_STATUSES = ('ACTIVE', 'ERROR')
VOLUME_STATUS = ('available', 'attaching', 'creating', 'deleting', 'in-use',
                 'error', 'error_deleting')

CLB_ALGORITHMS = ['RANDOM', 'LEAST_CONNECTIONS', 'ROUND_ROBIN',
                  'WEIGHTED_LEAST_CONNECTIONS', 'WEIGHTED_ROUND_ROBIN']
CLB_PROTOCOLS = ['DNS_TCP', 'DNS_UDP', 'FTP', 'HTTP', 'HTTPS', 'IMAPS',
                 'IMAPv4', 'LDAP', 'LDAPS', 'MYSQL', 'POP3', 'POP3S', 'SMTP',
                 'TCP', 'TCP_CLIENT_FIRST', 'UDP', 'UDP_STREAM', 'SFTP']

NON_CALLABLES = (text_type, binary_type, bool, dict, int, list, type(None))
PUBLIC_NET_ID = "00000000-0000-0000-0000-000000000000"
SERVICE_NET_ID = "11111111-1111-1111-1111-111111111111"


def rax_slugify(value):
    """Prepend a key with rax_ and normalize the key name"""
    return 'rax_%s' % (re.sub(r'[^\w-]', '_', value).lower().lstrip('_'))


def rax_clb_node_to_dict(obj):
    """Function to convert a CLB Node object to a dict"""
    if not obj:
        return {}
    node = obj.to_dict()
    node['id'] = obj.id
    node['weight'] = obj.weight
    return node


def rax_to_dict(obj, obj_type='standard'):
    """Generic function to convert a pyrax object to a dict

    obj_type values:
        standard
        clb
        server

    """
    instance = {}
    for key in dir(obj):
        value = getattr(obj, key)
        if obj_type == 'clb' and key == 'nodes':
            instance[key] = []
            for node in value:
                instance[key].append(rax_clb_node_to_dict(node))
        elif (isinstance(value, list) and len(value) > 0 and
                not isinstance(value[0], NON_CALLABLES)):
            instance[key] = []
            for item in value:
                instance[key].append(rax_to_dict(item))
        elif (isinstance(value, NON_CALLABLES) and not key.startswith('_')):
            if obj_type == 'server':
                if key == 'image':
                    if not value:
                        instance['rax_boot_source'] = 'volume'
                    else:
                        instance['rax_boot_source'] = 'local'
                key = rax_slugify(key)
            instance[key] = value

    if obj_type == 'server':
        for attr in ['id', 'accessIPv4', 'name', 'status']:
            instance[attr] = instance.get(rax_slugify(attr))

    return instance


def rax_find_bootable_volume(module, rax_module, server, exit=True):
    """Find a servers bootable volume"""
    cs = rax_module.cloudservers
    cbs = rax_module.cloud_blockstorage
    server_id = rax_module.utils.get_id(server)
    volumes = cs.volumes.get_server_volumes(server_id)
    bootable_volumes = []
    for volume in volumes:
        vol = cbs.get(volume)
        if module.boolean(vol.bootable):
            bootable_volumes.append(vol)
    if not bootable_volumes:
        if exit:
            module.fail_json(msg='No bootable volumes could be found for '
                                 'server %s' % server_id)
        else:
            return False
    elif len(bootable_volumes) > 1:
        if exit:
            module.fail_json(msg='Multiple bootable volumes found for server '
                                 '%s' % server_id)
        else:
            return False

    return bootable_volumes[0]


def rax_find_image(module, rax_module, image, exit=True):
    """Find a server image by ID or Name"""
    cs = rax_module.cloudservers
    try:
        UUID(image)
    except ValueError:
        try:
            image = cs.images.find(human_id=image)
        except(cs.exceptions.NotFound,
               cs.exceptions.NoUniqueMatch):
            try:
                image = cs.images.find(name=image)
            except (cs.exceptions.NotFound,
                    cs.exceptions.NoUniqueMatch):
                if exit:
                    module.fail_json(msg='No matching image found (%s)' %
                                         image)
                else:
                    return False

    return rax_module.utils.get_id(image)


def rax_find_volume(module, rax_module, name):
    """Find a Block storage volume by ID or name"""
    cbs = rax_module.cloud_blockstorage
    try:
        UUID(name)
        volume = cbs.get(name)
    except ValueError:
        try:
            volume = cbs.find(name=name)
        except rax_module.exc.NotFound:
            volume = None
        except Exception as e:
            module.fail_json(msg='%s' % e)
    return volume


def rax_find_network(module, rax_module, network):
    """Find a cloud network by ID or name"""
    cnw = rax_module.cloud_networks
    try:
        UUID(network)
    except ValueError:
        if network.lower() == 'public':
            return cnw.get_server_networks(PUBLIC_NET_ID)
        elif network.lower() == 'private':
            return cnw.get_server_networks(SERVICE_NET_ID)
        else:
            try:
                network_obj = cnw.find_network_by_label(network)
            except (rax_module.exceptions.NetworkNotFound,
                    rax_module.exceptions.NetworkLabelNotUnique):
                module.fail_json(msg='No matching network found (%s)' %
                                     network)
            else:
                return cnw.get_server_networks(network_obj)
    else:
        return cnw.get_server_networks(network)


def rax_find_server(module, rax_module, server):
    """Find a Cloud Server by ID or name"""
    cs = rax_module.cloudservers
    try:
        UUID(server)
        server = cs.servers.get(server)
    except ValueError:
        servers = cs.servers.list(search_opts=dict(name='^%s$' % server))
        if not servers:
            module.fail_json(msg='No Server was matched by name, '
                                 'try using the Server ID instead')
        if len(servers) > 1:
            module.fail_json(msg='Multiple servers matched by name, '
                                 'try using the Server ID instead')

        # We made it this far, grab the first and hopefully only server
        # in the list
        server = servers[0]
    return server


def rax_find_loadbalancer(module, rax_module, loadbalancer):
    """Find a Cloud Load Balancer by ID or name"""
    clb = rax_module.cloud_loadbalancers
    try:
        found = clb.get(loadbalancer)
    except Exception:
        found = []
        for lb in clb.list():
            if loadbalancer == lb.name:
                found.append(lb)

        if not found:
            module.fail_json(msg='No loadbalancer was matched')

        if len(found) > 1:
            module.fail_json(msg='Multiple loadbalancers matched')

        # We made it this far, grab the first and hopefully only item
        # in the list
        found = found[0]

    return found


def rax_argument_spec():
    """Return standard base dictionary used for the argument_spec
    argument in AnsibleModule

    """
    return dict(
        api_key=dict(type='str', aliases=['password'], no_log=True),
        auth_endpoint=dict(type='str'),
        credentials=dict(type='path', aliases=['creds_file']),
        env=dict(type='str'),
        identity_type=dict(type='str', default='rackspace'),
        region=dict(type='str'),
        tenant_id=dict(type='str'),
        tenant_name=dict(type='str'),
        username=dict(type='str'),
        validate_certs=dict(type='bool', aliases=['verify_ssl']),
    )


def rax_required_together():
    """Return the default list used for the required_together argument to
    AnsibleModule"""
    return [['api_key', 'username']]


def setup_rax_module(module, rax_module, region_required=True):
    """Set up pyrax in a standard way for all modules"""
    rax_module.USER_AGENT = 'ansible/%s %s' % (module.ansible_version,
                                               rax_module.USER_AGENT)

    api_key = module.params.get('api_key')
    auth_endpoint = module.params.get('auth_endpoint')
    credentials = module.params.get('credentials')
    env = module.params.get('env')
    identity_type = module.params.get('identity_type')
    region = module.params.get('region')
    tenant_id = module.params.get('tenant_id')
    tenant_name = module.params.get('tenant_name')
    username = module.params.get('username')
    verify_ssl = module.params.get('validate_certs')

    if env is not None:
        rax_module.set_environment(env)

    rax_module.set_setting('identity_type', identity_type)
    if verify_ssl is not None:
        rax_module.set_setting('verify_ssl', verify_ssl)
    if auth_endpoint is not None:
        rax_module.set_setting('auth_endpoint', auth_endpoint)
    if tenant_id is not None:
        rax_module.set_setting('tenant_id', tenant_id)
    if tenant_name is not None:
        rax_module.set_setting('tenant_name', tenant_name)

    try:
        username = username or os.environ.get('RAX_USERNAME')
        if not username:
            username = rax_module.get_setting('keyring_username')
            if username:
                api_key = 'USE_KEYRING'
        if not api_key:
            api_key = os.environ.get('RAX_API_KEY')
        credentials = (credentials or os.environ.get('RAX_CREDENTIALS') or
                       os.environ.get('RAX_CREDS_FILE'))
        region = (region or os.environ.get('RAX_REGION') or
                  rax_module.get_setting('region'))
    except KeyError as e:
        module.fail_json(msg='Unable to load %s' % e.message)

    try:
        if api_key and username:
            if api_key == 'USE_KEYRING':
                rax_module.keyring_auth(username, region=region)
            else:
                rax_module.set_credentials(username, api_key=api_key,
                                           region=region)
        elif credentials:
            credentials = os.path.expanduser(credentials)
            rax_module.set_credential_file(credentials, region=region)
        else:
            raise Exception('No credentials supplied!')
    except Exception as e:
        if e.message:
            msg = str(e.message)
        else:
            msg = repr(e)
        module.fail_json(msg=msg)

    if region_required and region not in rax_module.regions:
        module.fail_json(msg='%s is not a valid region, must be one of: %s' %
                         (region, ','.join(rax_module.regions)))

    return rax_module
