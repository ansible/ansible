#!/usr/bin/env python

# (c) 2012, Marco Vito Moscaritolo <marco@agavee.com>
#     modified by Tomas Karasek <tomas.karasek@digile.fi>
#
# This file is part of Ansible,
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import sys
import re
import os
import argparse
import subprocess
import yaml
import time
import md5
import itertools
import novaclient.client
import ansible.module_utils.openstack

try:
    import json
except ImportError:
    import simplejson as json

# This is a script getting dynamic inventory from Nova. Features:
# - you can refer to instances by their nova name in ansible{-playbook} calls
# - you can refer to single tenants, regions and openstack environments in
#   ansible{-playbook} calls
# - you can refer to a hostgroup when you pass the arbitrary --meta group=
#   in "nova boot"
# - it caches the state of the cloud
# - it tries to guess ansible_ssh_user based on name of image
#   ('\cubuntu' -> 'ubuntu', '\ccentos' -> 'cloud-user', ...)
# - allows to access machines by their private ip *
# - it will work with no additional configuration, just handling single tenant
#   from set OS_* environment variables (just like python-novaclient).
# - you can choose to heavy-configure it for multiple environments
# - it's configured from simple YAML (I dislike ConfigParser). See nova.yml
# - Nodes can be listed in inventory either by DNS name or IP address based
#   on setting.
#
# * I took few ideas and some code from other pull requests
# - https://github.com/ansible/ansible/pull/8657 by Monty Taylor
# - https://github.com/ansible/ansible/pull/7444 by Carson Gee
#
# If Ansible fails to parse JSON, please run this with --list and observe.
#
# HOW CACHING WORKS:
# Cache of list of servers is kept per combination of (auth_url, region_name,
# project_id). Default max age is 300 seconds. You can set the age per section
# (openstack envrionment) in config.
#
# If you want to build the cache from cron, consider:
# */5 * * * * . /home/tomk/os/openrc.sh && \
#               ANSIBLE_NOVA_CONFIG=/home/tomk/.nova.yml \
#               /home/tomk/ansible/plugins/inventory/nova.py --refresh-cache
#
# HOW IS NOVA INVENTORY CONFIGURED:
# (Note: if you have env vars set from openrc.sh, you can run this without
# writing the config file. Defaults are sane. The values in the config file
# will rewrite the defaults.)
#
# To load configuration from a file, you must have the config file path in
# environment variable ANSIBLE_NOVA_CONFIG.
#
# IN THE CONFIG FILE:
# The keys in the top level dict are names for different OS environments.
# The keys in a dict for OS environment can be:
#  - auth_url
#  - region_name (can be a list)
#  - project_id (can be a list)
#  - username
#  - api_key
#  - service_type
#  - auth_system
#  - prefer_private (connect using private IPs)
#  - cache_max_age (how long to consider cached data. In seconds)
#  - resolve_ips (translate IP addresses to domain names)
#
# If you have a list in region and/or project, all the combinations of
# will be listed.
#
# If you don't have configfile, there will be one cloud section created called
# 'openstack'.
#
# WHAT IS AVAILABLE AS A GROUP FOR ANSIBLE CALLS (how are nodes grouped):
# tenants, regions, clouds (top config section), groups by metadata key (nova
# boot --meta group=<name>).


CONFIG_ENV_VAR_NAME = 'ANSIBLE_NOVA_CONFIG'


NOVA_DEFAULTS = {
    'auth_system': os.environ.get('OS_AUTH_SYSTEM'),
    'service_type': 'compute',
    'username': os.environ.get('OS_USERNAME'),
    'api_key': os.environ.get('OS_PASSWORD'),
    'auth_url': os.environ.get('OS_AUTH_URL'),
    'project_id': os.environ.get('OS_TENANT_NAME'),
    'region_name': os.environ.get('OS_REGION_NAME'),
    'prefer_private': False,
    'version': '2',
    'cache_max_age': 300,
    'resolve_ips': True,
}


DEFAULT_CONFIG_KEY = 'openstack'


CACHE_DIR = '~/.ansible/tmp'


CONFIG = {}


def load_config():
    global CONFIG
    _config_file = os.environ.get(CONFIG_ENV_VAR_NAME)
    if _config_file:
        with open(_config_file) as f:
            CONFIG = yaml.load(f.read())
    if not CONFIG:
        CONFIG = {DEFAULT_CONFIG_KEY: {}}
    for section in CONFIG.values():
        for key in NOVA_DEFAULTS:
            if (key not in section):
                section[key] = NOVA_DEFAULTS[key]


def push(data, key, element):
    ''' Assist in items to a dictionary of lists '''
    if (not element) or (not key):
        return

    if key in data:
        data[key].append(element)
    else:
        data[key] = [element]


def to_safe(word):
    '''
    Converts 'bad' characters in a string to underscores so they can
    be used as Ansible groups
    '''
    return re.sub(r"[^A-Za-z0-9\-]", "_", word)


def get_access_ip(server, prefer_private):
    ''' Find an IP for Ansible SSH for a host. '''
    private = ansible.module_utils.openstack.openstack_find_nova_addresses(
              getattr(server, 'addresses'), 'fixed', 'private')
    public = ansible.module_utils.openstack.openstack_find_nova_addresses(
              getattr(server, 'addresses'), 'floating', 'public')
    if prefer_private:
        return private[0]
    if server.accessIPv4:
        return server.accessIPv4
    if public:
        return public[0]
    else:
        return private[0]


def get_metadata(server):
    ''' Returns dictionary of all host metadata '''
    results = {}
    for key in vars(server):
        # Extract value
        value = getattr(server, key)

        # Generate sanitized key
        key = 'os_' + re.sub(r"[^A-Za-z0-9\-]", "_", key).lower()

        # Att value to instance result (exclude manager class)
        #TODO: maybe use value.__class__ or similar inside of key_name
        if key != 'os_manager':
            results[key] = value
    return results


def get_ssh_user(server, nova_client):
    ''' Try to guess ansible_ssh_user based on image name. '''
    try:
        image_name = nova_client.images.get(server.image['id']).name
        if 'ubuntu' in image_name.lower():
            return 'ubuntu'
        if 'centos' in  image_name.lower():
            return 'cloud-user'
        if 'debian' in  image_name.lower():
            return 'debian'
        if 'coreos' in  image_name.lower():
            return 'coreos'
    except:
        pass


def get_nova_client(combination):
    '''
    There is a bit more info in the combination than we need for nova client,
    so we need to create a copy and delete keys that are not relevant.
    '''
    kwargs = dict(combination)
    del kwargs['name']
    del kwargs['prefer_private']
    del kwargs['cache_max_age']
    del kwargs['resolve_ips']
    return novaclient.client.Client(**kwargs)


def merge_update_to_result(result, update):
    '''
    This will merge data from a nova servers.list call (in update) into
    aggregating dict (in result)
    '''
    for host, specs in update['_meta']['hostvars'].items():
        # Can same host be in two differnt listings? I hope not.
        result['_meta']['hostvars'][host] = dict(specs)
    # groups must be copied if not present, otherwise merged
    for group in update:
        if group == '_meta':
            continue
        if group not in result:
            # copy the list over
            result[group] = update[group][:]
        else:
            result[group] = list(set(update[group]) | set(result[group]))


def get_name(ip):
    ''' Gets the shortest domain name for IP address'''
    # I first did this with gethostbyaddr but that did not return all the names
    # Also, this won't work on Windows. But it can be turned of by setting
    # resolve_ips to false
    command = "host %s" % ip
    p = subprocess.Popen(command.split(), stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, _ = p.communicate()
    if p.returncode != 0:
        return None
    names = []
    for l in stdout.split('\n'):
        if 'domain name pointer' not in l:
            continue
        names.append(l.split()[-1])
    return min(names, key=len)


def get_update(call_params):
    '''
    Fetch host dicts and groups from single nova_client.servers.list call.
    This is called for each element in "cartesian product" of openstack e
    environments, tenants and regions.
    '''
    update = {'_meta': {'hostvars': {}}}
    # Cycle on servers
    nova_client = get_nova_client(call_params)
    for server in nova_client.servers.list():
        access_ip = get_access_ip(server, call_params['prefer_private'])
        access_identifier = access_ip
        if call_params['resolve_ips']:
            dns_name = get_name(access_ip)
            if dns_name:
                access_identifier = dns_name

        # Push to a group for its name. This way we can use the nova name as
        # a target for ansible{-playbook}
        push(update, server.name, access_identifier)

        # Run through each metadata item and add instance to it
        for key, value in server.metadata.iteritems():
            composed_key = to_safe('tag_{0}_{1}'.format(key, value))
            push(update, composed_key, access_identifier)

        # Do special handling of group for backwards compat
        # inventory update
        group = 'undefined'
        if 'group' in server.metadata:
            group = server.metadata['group']
        push(update, group, access_identifier)

        # Add vars to _meta key for performance optimization in
        # Ansible 1.3+
        update['_meta']['hostvars'][access_identifier] = get_metadata(server)

        # guess username based on image name
        ssh_user = get_ssh_user(server, nova_client)
        if ssh_user:
            host_record = update['_meta']['hostvars'][access_identifier]
            host_record['ansible_ssh_user'] = ssh_user

        push(update, call_params['name'], access_identifier)
        push(update, call_params['project_id'], access_identifier)
        if call_params['region_name']:
            push(update, call_params['region_name'], access_identifier)
    return update


def expand_to_product(d):
    '''
    this will transform
    {1: [2, 3, 4], 5: [6, 7]}
    to
    [{1: 2, 5: 6}, {1: 2, 5: 7}, {1: 3, 5: 6}, {1: 3, 5: 7}, {1: 4, 5: 6},
     {1: 4, 5: 7}]
    '''
    return (dict(itertools.izip(d, x)) for x in
            itertools.product(*d.itervalues()))


def get_list_of_kwarg_combinations():
    '''
    This will transfrom
    CONFIG = {'openstack':{version:'2', project_id:['tenant1', tenant2'],...},
              'openstack_dev':{version:'2', project_id:'tenant3',...},
    into
    [{'name':'openstack', version:'2', project_id: 'tenant1', ...},
     {'name':'openstack', version:'2', project_id: 'tenant2', ...},
     {'name':'openstack_dev', version:'2', project_id: 'tenant3', ...}]

    The elements in the returned list can be (with little customization) used
    as **kwargs for nova client.
    '''
    l = []
    for section in CONFIG:
        d = dict(CONFIG[section])
        d['name'] = section
        for key in d:
            # all single elements must become list for the product to work
            if type(d[key]) is not list:
                d[key] = [d[key]]
        for one_call_kwargs in expand_to_product(d):
            l.append(one_call_kwargs)
    return l


def get_cache_filename(call_params):
    '''
    cache filename is
    ~/.ansible/tmp/<md5(auth_url,project_id,region_name)>.nova.json
    '''
    id_to_hash = ("region_name: %(region_name)s, auth_url:%(auth_url)s,"
                  "project_id: %(project_id)s, resolve_ips: %(resolve_ips)s"
                  % call_params)
    return os.path.join(os.path.expanduser(CACHE_DIR),
                 md5.new(id_to_hash).hexdigest() + ".nova.json")


def cache_valid(call_params):
    ''' cache file is specific for (auth_url, project_id, region_name) '''
    cache_path = get_cache_filename(call_params)
    if os.path.isfile(cache_path):
        mod_time = os.path.getmtime(cache_path)
        current_time = time.time()
        if (mod_time + call_params['cache_max_age']) > current_time:
            return True
    return False


def update_cache(call_params):
    fn = get_cache_filename(call_params)
    content = get_update(call_params)
    with open(fn, 'w') as f:
        f.write(json.dumps(content, sort_keys=True, indent=2))


def load_from_cache(call_params):
    fn = get_cache_filename(call_params)
    with open(fn) as f:
        return json.loads(f.read())


def get_args(args_list):
    parser = argparse.ArgumentParser(
        description='Nova dynamic inventory for Ansible')
    g = parser.add_mutually_exclusive_group()
    g.add_argument('--list', action='store_true', default=True,
                       help='List instances (default: True)')
    g.add_argument('--host', action='store',
                       help='Get all the variables about a specific instance')
    parser.add_argument('--refresh-cache', action='store_true', default=False,
                       help=('Force refresh of cache by making API requests to'
                             'Nova (default: False - use cache files)'))
    return parser.parse_args(args_list)


def main(args_list):
    load_config()

    args = get_args(args_list)

    if args.host:
        print(json.dumps({}))
        return 0

    if args.list:

        output = {'_meta': {'hostvars': {}}}

        # we have to deal with every combination of # (cloud, region, project).
        for c in get_list_of_kwarg_combinations():
            if args.refresh_cache or (not cache_valid(c)):
                update_cache(c)
            update = load_from_cache(c)
            merge_update_to_result(output, update)

        print(json.dumps(output, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
