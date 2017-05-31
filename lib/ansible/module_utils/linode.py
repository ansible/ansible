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


def linode_find_node(api, node_id=None, name=None):
    """Lookup and return a Node from the API.
    If node_id is present, lookup based on that.
    If not, lookup based on the name
    """

    if node_id:
        items = api.linode_list(LinodeId=node_id)
        return items[0] if items else None

    if name:
        nodebalancers = api.linode_list()
        for nb in nodebalancers:
            if nb['LABEL'] == name:
                return nb

    return None


def linode_get_instance_details(api, server):
    '''
    Return the details of an instance, populating IPs, etc.
    '''
    instance = {'id': server['LINODEID'],
                'name': server['LABEL'],
                'public': [],
                'private': []}

    # Populate with ips
    for ip in api.linode_ip_list(LinodeId=server['LINODEID']):
        if ip['ISPUBLIC'] and 'ipv4' not in instance:
            instance['ipv4'] = ip['IPADDRESS']
            instance['fqdn'] = ip['RDNS_NAME']
        if ip['ISPUBLIC']:
            instance['public'].append({'ipv4': ip['IPADDRESS'],
                                       'fqdn': ip['RDNS_NAME'],
                                       'ip_id': ip['IPADDRESSID']})
        else:
            instance['private'].append({'ipv4': ip['IPADDRESS'],
                                        'fqdn': ip['RDNS_NAME'],
                                        'ip_id': ip['IPADDRESSID']})
    return instance


def linode_find_nodebalancer(api, node_balancer_id=None, name=None):
    """Lookup and return a NodeBalancer from the API.
    If node_balancer_id is present, lookup based on that.
    If not, lookup based on the name
    """

    if node_balancer_id:
        items = api.nodebalancer_list(NodeBalancerID=node_balancer_id)
        return items[0] if items else None

    if name:
        nodebalancers = api.nodebalancer_list()
        for nb in nodebalancers:
            if nb['LABEL'] == name:
                return nb

    return None


def linode_find_nodebalancer_config(api, nodebalancer_id, config_id, port, protocol):
    """Lookup and return a NodeBalancer config from the API.
    If config_id is present, lookup based on that.
    If not, lookup based on the port and protocol
    """

    if nodebalancer_id:
        if config_id:
            items = api.nodebalancer_config_list(
                NodeBalancerID=nodebalancer_id,
                ConfigID=config_id
            )
            return items[0] if items else None

        all_configs = api.nodebalancer_config_list(
            NodeBalancerID=nodebalancer_id,
        )

        for config in all_configs:
            if config['PORT'] == port and config['PROTOCOL'] == protocol:
                return config

    return None


def linode_find_nodebalancer_node(api, config_id, node_id, node_name):
    """Lookup and return a node from the given NodeBalancer config_id
    If node_id is present lookup based on that.
    If not, lookup based on the node_name
    """

    if config_id:
        if node_id:
            items = api.nodebalancer_node_list(ConfigID=config_id,
                                              NodeID=node_id)
            return items[0] if items else None

        all_nodes = api.nodebalancer_node_list(ConfigID=config_id)

        for node in all_nodes:
            if node['LABEL'] == node_name:
                return node

    return None
