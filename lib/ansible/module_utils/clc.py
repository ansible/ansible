# -*- coding: utf-8 -*-

# Copyright (c) 2017 CenturyLink
#
# This file is part of Ansible.
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
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>
#
"""
This module adds support for common functionality using the
CenturyLink Cloud V2 API: https://www.ctl.io/api-docs/v2/

"""

import math
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode
try:
    from urllib.errors import URLError
except ImportError:
    from urllib2 import URLError

from ansible.module_utils.basic import os, sys, json, time, get_exception
from ansible.module_utils.urls import open_url, ssl


class ClcApiException(Exception):

    def __init__(self, message=None, code=None):
        if message is not None:
            super(self.__class__, self).__init__(message)
        else:
            super(self.__class__, self).__init__()
        self.code = code


class Group(object):

    def __init__(self, group_data):
        self.alias = None
        self.id = None
        self.name = None
        self.description = None
        self.parent = None
        self.children = []
        if group_data is not None:
            self.data = group_data
            for attr in ['id', 'name', 'description', 'type']:
                if attr in group_data:
                    setattr(self, attr, group_data[attr])


class Server(object):

    def __init__(self, server_data):
        self.id = None
        self.name = None
        self.description = None
        if server_data is not None:
            self.data = server_data
            for attr in ['id', 'name', 'description', 'status', 'powerState',
                         'locationId', 'groupId']:
                if attr in server_data:
                    setattr(self, attr, server_data[attr])
                elif ('details' in server_data and
                        attr in server_data['details']):
                    setattr(self, attr, server_data['details'][attr])
            try:
                self.data['details']['memoryGB'] = int(
                    math.floor(self.data['details']['memoryMB']/1024))
            except:
                pass


class Network(object):

    def __init__(self, network_data):
        self.id = None
        self.name = None
        self.cidr = None
        self.description = None
        self.type = None
        if network_data is not None:
            self.data = network_data
            for attr in ['id', 'name', 'description', 'type',
                         'cidr', 'gateway', 'netmask']:
                if attr in network_data:
                    setattr(self, attr, network_data[attr])


def _default_headers():
    # Helpful ansible open_url params
    # data, headers, http-agent
    headers = {}
    agent_string = 'ClcAnsibleModule'
    headers['Api-Client'] = agent_string
    headers['User-Agent'] = agent_string
    return headers


def call_clc_api(module, clc_auth, method, url, headers=None, data=None,
                 timeout=10, max_tries=3):
    """
    Make a request to the CLC API v2.0
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param method: HTTP method
    :param url: URL string to be appended to root api_url
    :param headers: Headers to be added to request
    :param data: Data to be sent with request
    :param timeout: Timeout in seconds
    :param max_tries: Maximum number of tries attempted if call times out
    :return response: JSON from HTTP response, or None if no content
    """
    if not isinstance(url, str):
        raise TypeError('URL for API request must be a string')
    if headers is None:
        headers = _default_headers()
    elif not isinstance(headers, dict):
        raise TypeError('Headers for API request must be a dict')
    else:
        headers = _default_headers().update(headers)
    if data is not None and not isinstance(data, (dict, list)):
        raise TypeError('Data for API request must be JSON Serializable')
    # Obtain Bearer token if we do not already have it
    if 'authentication/login' not in url:
        if 'v2_api_token' not in clc_auth:
            clc_auth = authenticate(module)
        headers['Authorization'] = 'Bearer {token}'.format(
            token=clc_auth['v2_api_token'])
    if data is not None:
        if method.upper() == 'GET':
            url += '?' + urlencode(data)
            data = None
        else:
            data = json.dumps(data)
            headers['Content-Type'] = 'application/json'
    tries = 0
    while tries < max_tries:
        tries += 1
        try:
            response = open_url(
                url='{endpoint}/{path}'.format(
                    endpoint=clc_auth['v2_api_url'].rstrip('/'),
                    path=url.lstrip('/')),
                method=method,
                headers=headers,
                data=data,
                timeout=timeout)
        except URLError:
            ex = get_exception()
            try:
                error_response = json.loads(ex.read())
                error_message = error_response['message']
            except (AttributeError, ValueError, KeyError):
                error_message = ex.reason
            api_ex = ClcApiException(
                message='Error calling CenturyLink Cloud API: {msg}'.format(
                    msg=error_message),
                code=ex.code)
            raise api_ex
        except ssl.SSLError:
            ex = get_exception()
            if tries >= max_tries:
                error_message = 'After {num} tries, {msg}'.format(
                    num=tries, msg=ex.message)
                raise ssl.SSLError(error_message)
            else:
                timeout *= 2
                continue
        if response.getcode() == 204:
            return None
        try:
            return json.loads(response.read())
        except:
            raise ClcApiException(
                'Error converting CenturyLink Cloud API response to JSON')


def operation_status(module, clc_auth, operation_id):
    """
    Call back to the CLC API to determine status
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param operation_id: Operation id for which to check the status
    :return: Status of the operation, one of the below values
    ('notStarted, 'executing', 'succeeded', 'failed', 'resumed', 'unknown')
    """
    response = call_clc_api(
        module, clc_auth,
        'GET', '/operations/{alias}/status/{id}'.format(
            alias=clc_auth['clc_alias'], id=operation_id))
    return response['status']


def operation_id_list(response_data):
    """
    Extract list of operation IDs from CLC API response
    :param response_data: JSON data from API response. A list of dicts.
    :return: List of operation IDs.
    """
    operation_ids = []
    for operation in response_data:
        # Operation ID format returned as part server operations
        if isinstance(operation, list):
            # Call recursively if response is a list of operations
            operation_ids.extend(operation_id_list(operation))
        elif 'links' in operation:
            operation_ids.extend([o['id'] for o in operation['links']
                                  if o['rel'] == 'status'])
        elif 'rel' in operation and operation['rel'] == 'status':
            operation_ids.extend([operation['id']])
        # Operation ID format returned as part of network operations
        elif 'operationId' in operation:
            operation_ids.extend([operation['operationId']])
    return operation_ids


def wait_on_completed_operations(module, clc_auth, operation_ids):
    """
    Wait for list of operations to complete
    :param module:
    :param clc_auth:
    :param operation_ids:
    :return:
    """
    ops_succeeded = []
    ops_failed = []
    for operation_id in operation_ids:
        try:
            _wait_until_complete(module, clc_auth, operation_id)
            ops_succeeded.append(operation_id)
        except ClcApiException:
            ops_failed.append(operation_id)
    return len(ops_failed)


def _wait_until_complete(module, clc_auth, operation_id, poll_freq=2):
    """
    Wail until CLC API operation is complete
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param operation_id: Operation id for which to wait for completion
    :param poll_freq: How frequently to poll the CLC API
    :return:
    """
    time_completed = None
    while not time_completed:
        try:
            status = operation_status(module, clc_auth, operation_id)
        except ssl.SSLError:
            continue
        if status == 'succeeded':
            time_completed = time.time()
        elif status == 'failed':
            time_completed = time.time()
            raise ClcApiException(
                'Execution of operation {id} {status}'.format(
                    id=operation_id, status=status))
        else:
            time.sleep(poll_freq)


def authenticate(module):
    """
    Authenticate against the CLC V2 API
    :param module: Ansible module being called
    :return: clc_auth - dict containing the needed parameters for authentication
    """
    v2_api_url = 'https://api.ctl.io/v2/'
    env = os.environ
    v2_api_token = env.get('CLC_V2_API_TOKEN', False)
    v2_api_username = env.get('CLC_V2_API_USERNAME', False)
    v2_api_passwd = env.get('CLC_V2_API_PASSWD', False)
    clc_alias = env.get('CLC_ACCT_ALIAS', False)
    clc_location = env.get('CLC_LOCATION', False)
    v2_api_url = env.get('CLC_V2_API_URL', v2_api_url)
    clc_auth = {'v2_api_url': v2_api_url}
    # Populate clc_auth, authenticating if needed
    if v2_api_token and clc_alias and clc_location:
        clc_auth.update({
            'v2_api_token': v2_api_token,
            'clc_alias': clc_alias,
            'clc_location': clc_location,
        })
    elif v2_api_username and v2_api_passwd:
        r = call_clc_api(
            module, clc_auth,
            'POST', '/authentication/login',
            data={'username': v2_api_username,
                  'password': v2_api_passwd})
        clc_auth.update({
            'v2_api_token': r['bearerToken'],
            'clc_alias': r['accountAlias'],
            'clc_location': r['locationAlias']
        })
    elif v2_api_token:
        message = ('In addition to the CLC_V2_API_TOKEN environment variable, '
                   'you must also set the CLC_ACCT_ALIAS and CLC_LOCATION '
                   'variables')
        if module is not None:
            return module.fail_json(msg=message)
        else:
            sys.stderr.write(message + '\n')
            sys.exit(1)
    else:
        message = ('You must set the CLC_V2_API_USERNAME and '
                   'CLC_V2_API_PASSWD environment variables')
        if module is not None:
            return module.fail_json(msg=message)
        else:
            sys.stderr.write(message + '\n')
            sys.exit(1)
    return clc_auth


def _walk_groups(parent_group, group_data):
    """
    Walk a parent-child tree of groups, starting with the provided child group
    :param parent_group: Group - Parent of group described by group_data
    :param group_data: dict - Dict of data from JSON API return
    :return: Group object from data, containing list of children
    """
    group = Group(group_data)
    group.parent = parent_group
    for child_data in group_data['groups']:
        if child_data['type'] != 'default':
            continue
        group.children.append(_walk_groups(group, child_data))
    return group


def group_tree(module, clc_auth, alias=None, datacenter=None):
    """
    Walk the tree of groups for a datacenter
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param alias: string - CLC account alias
    :param datacenter: string - the datacenter to walk (ex: 'UC1')
    :return: Group object for root group containing list of children
    """
    if datacenter is None:
        datacenter = clc_auth['clc_location']
    if alias is None:
        alias = clc_auth['clc_alias']
    r = call_clc_api(
        module, clc_auth,
        'GET', '/datacenters/{alias}/{location}'.format(
            alias=alias, location=datacenter),
        data={'GroupLinks': 'true'})

    root_group_id, root_group_name = [(obj['id'], obj['name'])
                                      for obj in r['links']
                                      if obj['rel'] == "group"][0]

    group_data = call_clc_api(
        module, clc_auth,
        'GET', '/groups/{alias}/{id}'.format(
            alias=alias, id=root_group_id))

    return _walk_groups(None, group_data)


def _find_group_recursive(search_group, group_info, parent_info=None):
    """
    :param search_group: Group under which to search
    :param group_info: Name or id of group to search for
    :param parent_info: Optional name or id of parent
    :return: List of groups found matching the described parameters
    """
    groups = []
    if group_info.lower() in [search_group.id.lower(),
                              search_group.name.lower()]:
        if parent_info is None:
            groups.append(search_group)
        elif (search_group.parent is not None and
                parent_info.lower() in [search_group.parent.id.lower(),
                                        search_group.parent.name.lower()]):
            groups.append(search_group)
    for child_group in search_group.children:
        groups += _find_group_recursive(child_group, group_info,
                                        parent_info=parent_info)
    return groups


def find_group(module, search_group, group_info, parent_info=None):
    """
    :param module: Ansible module being called
    :param search_group: Group under which to search
    :param group_info: Name or id of group to search for
    :param parent_info:  Optional name or id of parent
    :return: Group object found, or None if no groups found.
    Will return an error if multiple groups found matching parameters.
    """
    groups = _find_group_recursive(
        search_group, group_info, parent_info=parent_info)
    if len(groups) > 1:
        error_message = 'Found {num:d} groups with name: \"{name}\"'.format(
            num=len(groups), name=group_info)
        if parent_info is None:
            error_message += ', no parent group specified.'
        else:
            error_message += ' in group: \"{name}\".'.format(
                name=parent_info)
        error_message += ' Group ids: ' + ', '.join([g.id for g in groups])
        return module.fail_json(msg=error_message)
    elif len(groups) == 1:
        return groups[0]
    else:
        return None


def find_group_by_id(module, clc_auth, group_id):
    """
    Find server information based on server_id
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param group_id: ID for group for which to retrieve data
    :return: Server object
    """
    try:
        r = call_clc_api(
            module, clc_auth,
            'GET', 'groups/{alias}/{id}'.format(
                alias=clc_auth['clc_alias'], id=group_id))
        group = Group(r)
        return group
    except ClcApiException:
        return module.fail_json(
            msg='Failed to get group information '
                'for group id: {id}.'.format(id=group_id))


def group_path(group, group_id=False, delimiter='/'):
    """
    :param group: Group object for which to show full ancestry
    :param group_id: Optional flag to show group id hierarchy
    :param delimiter: Optional delimiter
    :return:
    """
    path_elements = []
    while group is not None:
        if group_id:
            path_elements.append(group.id)
        else:
            path_elements.append(group.name)
        group = group.parent
    return delimiter.join(reversed(path_elements))


def networks_in_datacenter(module, clc_auth, datacenter):
    """
    Return list of networks in datacenter
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param datacenter: the datacenter to search for a network id
    :return: A list of Network objects
    """
    networks = []
    if 'clc_location' not in clc_auth:
        clc_auth = authenticate(module)

    try:
        temp_auth = clc_auth.copy()
        temp_auth['v2_api_url'] = clc_auth['v2_api_url'].replace(
            '/v2/', '/v2-experimental/')
        response = call_clc_api(
            module, temp_auth,
            'GET', '/networks/{alias}/{location}'.format(
                alias=temp_auth['clc_alias'], location=datacenter))
        networks = [Network(n) for n in response]
        return networks
    except ClcApiException:
        return module.fail_json(
            msg=str(
                "Unable to find a network in location: " +
                datacenter))


def find_network(module, clc_auth, datacenter,
                 network_id_search=None, networks=None):
    """
    Validate the provided network id or return a default.
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param datacenter: the datacenter to search for a network id
    :param network_id_search: Network id for which to search for
    :param networks: List of networks in which to search. If None, call API.
    :return: A valid Network object
    """
    network_found = None
    # Validates provided network id
    # Allows lookup of network by id, name, or cidr notation
    if not networks:
        networks = networks_in_datacenter(module, clc_auth, datacenter)

    if network_id_search:
        for network in networks:
            if network_id_search.lower() in [network.id.lower(),
                                             network.name.lower(),
                                             network.cidr.lower()]:
                network_found = network
                break
    else:
        network_found = networks[0]
    return network_found


def find_server(module, clc_auth, server_id):
    """
    Find server information based on server_id
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param server_id: ID for server for which to retrieve data
    :return: Server object
    """
    try:
        r = call_clc_api(
            module, clc_auth,
            'GET', 'servers/{alias}/{id}'.format(
                alias=clc_auth['clc_alias'], id=server_id))
        server = Server(r)
        return server
    except ClcApiException:
        ex = get_exception()
        if module is None:
            raise ex
        else:
            return module.fail_json(
                msg='Failed to get server information '
                    'for server id: {id}:'.format(id=server_id))


def server_ip_addresses(module, clc_auth, server, poll_freq=2, retries=5):
    """
    Retrieve IP addresses for a CLC server, retrying if needed
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param server: Server object for which to retrieve IP addresses
    :param poll_freq: Poll frequency for retries
    :param retries:  Number of retries
    :return: Server object with IP addresses added to data dictionary
    """
    while 'ipAddresses' not in server.data['details']:
        if retries < 1:
            module.fail_json(
                msg='Unable to retrieve IP addresses for server: '
                    '{name}.'.format(
                        name=server.name))
        time.sleep(poll_freq)
        retries -= 1
        server = find_server(module, clc_auth, server.id)

    internal_ips = [ip['internal'] for ip
                    in server.data['details']['ipAddresses']
                    if 'internal' in ip]
    public_ips = [ip['public'] for ip
                  in server.data['details']['ipAddresses']
                  if 'public' in ip]
    if len(internal_ips) > 0:
        server.data['ipaddress'] = internal_ips[0]
    if len(public_ips) > 0:
        server.data['publicip'] = public_ips[0]

    return server


def servers_by_id(module, clc_auth, server_ids):
    """
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param server_ids: list of server IDs for which to retrieve data
    :return: List of server objects containing information from API Calls
    """
    servers = []
    for server_id in server_ids:
        servers.append(find_server(module, clc_auth, server_id))
    return servers


def servers_in_group(module, clc_auth, group):
    """
    Return a list of servers from
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param group: Group object to search for servers
    :return: List of server objects containing information from API Calls
    """
    server_lst = [obj['id'] for obj in group.data['links'] if
                  obj['rel'] == 'server']
    return servers_by_id(module, clc_auth, server_lst)


def _server_ids_in_group_recursive(group):
    server_ids = [obj['id'] for obj in group.data['links'] if
                  obj['rel'] == 'server']
    for child in group.children:
        server_ids.extend(_server_ids_in_group_recursive(child))
    return server_ids


def server_ids_in_datacenter(module, clc_auth, datacenter,
                             alias=None, root_group=None):
    """
    Return a list of servers ids in a provided datacenter
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param datacenter: the datacenter to search for a network id
    :param alias: string - CLC account alias
    :param root_group: Root group in datacenter, if present
    :return: List of server ids present in a datacenter
    """
    if root_group is None:
        root_group = group_tree(module, clc_auth,
                                alias=alias, datacenter=datacenter)

    return _server_ids_in_group_recursive(root_group)


def _check_policy_type(module, policy_type):
    """
    Check that policy type is supported
    :param module: Ansible module being called
    :param policy_type: Policy type to be checked
    :return: Long string corresponding to policy type
    """
    policy_types = {
        'antiAffinity': 'anti affinity',
        'alert': 'alert'
    }
    if policy_type not in policy_types:
        return module.fail_json(msg='Policy type: {type} not supported'.format(
            type=policy_type))
    return policy_types[policy_type]


def _get_policies(module, clc_auth, policy_type, location=None):
    """
    Get a list of policies matching a specific type in CenturyLink Cloud
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param policy_type: type of policy for which to search
    :param location: the datacenter to search for policy
    :return: List of policies found in the datacenter (if specified)
    """
    policy_str = _check_policy_type(module, policy_type)
    try:
        policies = call_clc_api(
            module, clc_auth,
            'GET', '/{type}Policies/{alias}'.format(
                type=policy_type, alias=clc_auth['clc_alias']))
    except ClcApiException:
        ex = get_exception()
        return module.fail_json(
            msg='Unable to fetch {type} policies for '
                'account: {alias}. {msg}'.format(
                    type=policy_str, alias=clc_auth['clc_alias'],
                    msg=ex.message))

    policies = policies['items']
    if location is not None:
        policies = [p for p in policies if p['location'] == location]

    return policies


def find_policy(module, clc_auth, search_key,
                policy_type=None, location=None, policies=None):
    """
    Find a policy that can be associated with a CenturyLink Cloud server
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param search_key: id or name of policy for which to search form
    :param policy_type: Type of policy to search for
    :param location: Location to search for policies
    :param policies: List of policies to search
    :return:
    """
    policy_str = _check_policy_type(module, policy_type)
    if policies is None:
        policies = _get_policies(module, clc_auth, policy_type,
                                 location=location)

    policies = [p for p in policies if search_key.lower()
                in (p['id'].lower(), p['name'].lower())]
    num_policies = len(policies)
    if num_policies > 1:
        return module.fail_json(
            msg='Multiple {type} policies matching: {search}. '
                'Policy ids: {ids}'.format(
                    type=policy_str, search=search_key,
                    ids=', '.join([p['id'] for p in policies])))
    if num_policies > 0:
        policy = policies[0]
    else:
        policy = None
    return policy


def loadbalancer_list(module, clc_auth, alias=None, location=None):
    """
    Retrieve a list of loadbalancers
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param location: the datacenter to search for a network id
    :param alias: string - CLC account alias
    :return: List of JSON data for all loadbalancers at datacenter
    """
    result = None
    if alias is None:
        alias = clc_auth['clc_alias']
    if location is None:
        location = clc_auth['clc_location']
    try:
        result = call_clc_api(
            module, clc_auth,
            'GET', '/sharedLoadBalancers/{alias}/{location}'.format(
                alias=alias, location=location))
    except ClcApiException:
        e = get_exception()
        module.fail_json(
            msg='Unable to fetch load balancers for account: {alias} '
                'in location: {location}. {msg}'.format(
                    alias=alias, location=location, msg=str(e.message)))
    return result


def find_loadbalancer(module, clc_auth, search_key, load_balancers=None,
                      alias=None, location=None):
    """
    Retrieves load balancer matching search key
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param search_key: Id or name of load balancer
    :param load_balancers: List of load balancers to search
    :param location: the datacenter to search for a network id
    :param alias: string - CLC account alias
    :return: Matching load balancer dictionary
    """
    lb_list = []
    if load_balancers is None:
        load_balancers = loadbalancer_list(module, clc_auth,)
    for lb in load_balancers:
        if search_key.lower() in (lb['id'].lower(), lb['name'].lower()):
            lb_list.append(lb)
    num_lb = len(lb_list)
    if num_lb > 1:
        return module.fail_json(
            msg='Multiple load balancers matching: {search}. '
                'Load balancer ids: {ids}'.format(
                    search=search_key,
                    ids=', '.join([l['id'] for l in lb_list])))
    if num_lb > 0:
        loadbalancer = lb_list[0]
    else:
        loadbalancer = None
    return loadbalancer


def modify_aa_policy_on_server(module, clc_auth, server_id, aa_policy_id):
    """
    Add an alert policy to a clc server
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param server_id: The clc server id
    :param aa_policy_id: Anti affinity policy id to be added to server
    :return: none
    """
    try:
        result = call_clc_api(
            module, clc_auth,
            'PUT', '/servers/{alias}/{server}/antiAffinityPolicy'.format(
                alias=clc_auth['clc_alias'], server=server_id),
            data={'id': aa_policy_id})
    except ClcApiException:
        e = get_exception()
        return module.fail_json(
            msg='Failed to add anti affinity policy: {policy} to '
                'server: {server}. {msg}'.format(
                    policy=aa_policy_id, server=server_id,
                    msg=str(e.message)))
    return result


def remove_aa_policy_from_server(module, clc_auth, server_id, aa_policy_id):
    """
    Add an alert policy to a clc server
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param server_id: The clc server id
    :param aa_policy_id: Anti affinity policy id to be removed from server
    :return: none
    """
    try:
        # Returns 200 OK, No Content
        result = call_clc_api(
            module, clc_auth,
            'DELETE', '/servers/{alias}/{server}/antiAffinityPolicy'.format(
                alias=clc_auth['clc_alias'], server=server_id),
            data={})
    except ClcApiException:
        e = get_exception()
        return module.fail_json(
            msg='Failed to remove anti affinity policy: {policy} from '
                'server: {server}. {msg}'.format(
                    policy=aa_policy_id, server=server_id,
                    msg=str(e.message)))
    return result


def add_alert_policy_to_server(module, clc_auth,
                               server_id, alert_policy_id):
    """
    Add an alert policy to a clc server
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param server_id: The clc server id
    :param alert_policy_id: the alert policy id to be associated to the server
    :return: none
    """
    try:
        result = call_clc_api(
            module, clc_auth,
            'POST', '/servers/{alias}/{server}/alertPolicies'.format(
                alias=clc_auth['clc_alias'], server=server_id),
            data={'id': alert_policy_id})
    except ClcApiException:
        e = get_exception()
        return module.fail_json(
            msg='Failed to add alert policy: {policy} to server: {server}.'
                ' {msg}'.format(policy=alert_policy_id, server=server_id,
                                msg=str(e.message)))
    return result


def remove_alert_policy_from_server(module, clc_auth,
                                    server_id, alert_policy_id):
    """
    Add an alert policy to a clc server
    :param module: Ansible module being called
    :param clc_auth: dict containing the needed parameters for authentication
    :param server_id: The clc server id
    :param alert_policy_id: the alert policy id to be associated to the server
    :return: none
    """
    try:
        # Returns 200 OK, No Content
        result = call_clc_api(
            module, clc_auth,
            'DELETE', '/servers/{alias}/{server}/alertPolicies/{policy}'.format(
                alias=clc_auth['clc_alias'], server=server_id,
                policy=alert_policy_id))
    except ClcApiException:
        e = get_exception()
        return module.fail_json(
            msg='Failed to remove alert policy: {policy} from server: {server}.'
                ' {msg}'.format(policy=alert_policy_id, server=server_id,
                                msg=str(e.message)))
    return result
