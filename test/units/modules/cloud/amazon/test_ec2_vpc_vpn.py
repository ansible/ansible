# (c) 2017 Red Hat Inc.
#
# This file is part of Ansible
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

import pytest
import os
from units.utils.amazon_placebo_fixtures import placeboify, maybe_sleep
from ansible.modules.cloud.amazon import ec2_vpc_vpn
from ansible.module_utils._text import to_text
from ansible.module_utils.ec2 import get_aws_connection_info, boto3_conn, boto3_tag_list_to_ansible_dict


class FakeModule(object):
    def __init__(self, **kwargs):
        self.params = kwargs

    def fail_json(self, *args, **kwargs):
        self.exit_args = args
        self.exit_kwargs = kwargs
        raise Exception('FAIL')

    def exit_json(self, *args, **kwargs):
        self.exit_args = args
        self.exit_kwargs = kwargs


def get_vgw(connection):
    # see if two vgw exist and return them if so
    vgw = connection.describe_vpn_gateways(Filters=[{'Name': 'tag:Ansible_VPN', 'Values': ['Test']}])
    if len(vgw['VpnGateways']) >= 2:
        return [vgw['VpnGateways'][0]['VpnGatewayId'], vgw['VpnGateways'][1]['VpnGatewayId']]
    # otherwise create two and return them
    vgw_1 = connection.create_vpn_gateway(Type='ipsec.1')
    vgw_2 = connection.create_vpn_gateway(Type='ipsec.1')
    for resource in (vgw_1, vgw_2):
        connection.create_tags(Resources=[resource['VpnGateway']['VpnGatewayId']], Tags=[{'Key': 'Ansible_VPN', 'Value': 'Test'}])
    return [vgw_1['VpnGateway']['VpnGatewayId'], vgw_2['VpnGateway']['VpnGatewayId']]


def get_cgw(connection):
    # see if two cgw exist and return them if so
    cgw = connection.describe_customer_gateways(DryRun=False, Filters=[{'Name': 'state', 'Values': ['available']},
                                                                       {'Name': 'tag:Name', 'Values': ['Ansible-CGW']}])
    if len(cgw['CustomerGateways']) >= 2:
        return [cgw['CustomerGateways'][0]['CustomerGatewayId'], cgw['CustomerGateways'][1]['CustomerGatewayId']]
    # otherwise create and return them
    cgw_1 = connection.create_customer_gateway(DryRun=False, Type='ipsec.1', PublicIp='9.8.7.6', BgpAsn=65000)
    cgw_2 = connection.create_customer_gateway(DryRun=False, Type='ipsec.1', PublicIp='5.4.3.2', BgpAsn=65000)
    for resource in (cgw_1, cgw_2):
        connection.create_tags(Resources=[resource['CustomerGateway']['CustomerGatewayId']], Tags=[{'Key': 'Ansible-CGW', 'Value': 'Test'}])
    return [cgw_1['CustomerGateway']['CustomerGatewayId'], cgw_2['CustomerGateway']['CustomerGatewayId']]


def get_dependencies():
    if os.getenv('PLACEBO_RECORD'):
        module = FakeModule(**{})
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        connection = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_kwargs)
        vgw = get_vgw(connection)
        cgw = get_cgw(connection)
    else:
        vgw = ["vgw-35d70c2b", "vgw-32d70c2c"]
        cgw = ["cgw-6113c87f", "cgw-9e13c880"]

    return cgw, vgw


def setup_mod_conn(placeboify, params):
    conn = placeboify.client('ec2')
    m = FakeModule(**params)
    return m, conn


def make_params(cgw, vgw, tags=None, filters=None, routes=None):
    tags = {} if tags is None else tags
    filters = {} if filters is None else filters
    routes = [] if routes is None else routes

    return {'customer_gateway_id': cgw,
            'static_only': True,
            'vpn_gateway_id': vgw,
            'connection_type': 'ipsec.1',
            'purge_tags': True,
            'tags': tags,
            'filters': filters,
            'routes': routes,
            'delay': 15,
            'wait_timeout': 600}


def make_conn(placeboify, module, connection):
    customer_gateway_id = module.params['customer_gateway_id']
    static_only = module.params['static_only']
    vpn_gateway_id = module.params['vpn_gateway_id']
    connection_type = module.params['connection_type']
    check_mode = module.params['check_mode']
    changed = True
    vpn = ec2_vpc_vpn.create_connection(connection, customer_gateway_id, static_only, vpn_gateway_id, connection_type)
    return changed, vpn


def tear_down_conn(placeboify, connection, vpn_connection_id):
    ec2_vpc_vpn.delete_connection(connection, vpn_connection_id, delay=15, max_attempts=40)


def test_find_connection_vpc_conn_id(placeboify, maybe_sleep):
    # setup dependencies for 2 vpn connections
    dependencies = setup_req(placeboify, 2)
    dep1, dep2 = dependencies[0], dependencies[1]
    params1, vpn1, m1, conn1 = dep1['params'], dep1['vpn'], dep1['module'], dep1['connection']
    params2, vpn2, m2, conn2 = dep2['params'], dep2['vpn'], dep2['module'], dep2['connection']

    # find the connection with a vpn_connection_id and assert it is the expected one
    assert vpn1['VpnConnectionId'] == ec2_vpc_vpn.find_connection(conn1, params1, vpn1['VpnConnectionId'])['VpnConnectionId']

    tear_down_conn(placeboify, conn1, vpn1['VpnConnectionId'])
    tear_down_conn(placeboify, conn2, vpn2['VpnConnectionId'])


def test_find_connection_filters(placeboify, maybe_sleep):
    # setup dependencies for 2 vpn connections
    dependencies = setup_req(placeboify, 2)
    dep1, dep2 = dependencies[0], dependencies[1]
    params1, vpn1, m1, conn1 = dep1['params'], dep1['vpn'], dep1['module'], dep1['connection']
    params2, vpn2, m2, conn2 = dep2['params'], dep2['vpn'], dep2['module'], dep2['connection']

    # update to different tags
    params1.update(tags={'Wrong': 'Tag'})
    params2.update(tags={'Correct': 'Tag'})
    ec2_vpc_vpn.ensure_present(conn1, params1)
    ec2_vpc_vpn.ensure_present(conn2, params2)

    # create some new parameters for a filter
    params = {'filters': {'tags': {'Correct': 'Tag'}}}

    # find the connection that has the parameters above
    found = ec2_vpc_vpn.find_connection(conn1, params)

    # assert the correct connection was found
    assert found['VpnConnectionId'] == vpn2['VpnConnectionId']

    # delete the connections
    tear_down_conn(placeboify, conn1, vpn1['VpnConnectionId'])
    tear_down_conn(placeboify, conn2, vpn2['VpnConnectionId'])


def test_find_connection_insufficient_filters(placeboify, maybe_sleep):
    # get list of customer gateways and virtual private gateways
    cgw, vgw = get_dependencies()

    # create two connections with the same tags
    params = make_params(cgw[0], vgw[0], tags={'Correct': 'Tag'})
    params2 = make_params(cgw[1], vgw[1], tags={'Correct': 'Tag'})
    m, conn = setup_mod_conn(placeboify, params)
    m2, conn2 = setup_mod_conn(placeboify, params2)
    _, vpn1 = ec2_vpc_vpn.ensure_present(conn, m.params)
    _, vpn2 = ec2_vpc_vpn.ensure_present(conn2, m2.params)

    # reset the parameters so only filtering by tags will occur
    m.params = {'filters': {'tags': {'Correct': 'Tag'}}}

    # assert that multiple matching connections have been found
    with pytest.raises(Exception) as error_message:
        ec2_vpc_vpn.find_connection(conn, m.params)
        assert error_message == "More than one matching VPN connection was found.To modify or delete a VPN please specify vpn_connection_id or add filters."

    # delete the connections
    tear_down_conn(placeboify, conn, vpn1['VpnConnectionId'])
    tear_down_conn(placeboify, conn, vpn2['VpnConnectionId'])


def test_find_connection_nonexistent(placeboify, maybe_sleep):
    # create parameters but don't create a connection with them
    params = {'filters': {'tags': {'Correct': 'Tag'}}}
    m, conn = setup_mod_conn(placeboify, params)

    # try to find a connection with matching parameters and assert None are found
    assert ec2_vpc_vpn.find_connection(conn, m.params) is None


def test_create_connection(placeboify, maybe_sleep):
    # get list of customer gateways and virtual private gateways
    cgw, vgw = get_dependencies()

    # create a connection
    params = make_params(cgw[0], vgw[0])
    m, conn = setup_mod_conn(placeboify, params)
    changed, vpn = ec2_vpc_vpn.ensure_present(conn, m.params)

    # assert that changed is true and that there is a connection id
    assert changed is True
    assert 'VpnConnectionId' in vpn

    # delete connection
    tear_down_conn(placeboify, conn, vpn['VpnConnectionId'])


def test_create_connection_that_exists(placeboify, maybe_sleep):
    # setup dependencies for 1 vpn connection
    dependencies = setup_req(placeboify, 1)
    params, vpn, m, conn = dependencies['params'], dependencies['vpn'], dependencies['module'], dependencies['connection']

    # try to recreate the same connection
    changed, vpn2 = ec2_vpc_vpn.ensure_present(conn, params)

    # nothing should have changed
    assert changed is False
    assert vpn['VpnConnectionId'] == vpn2['VpnConnectionId']

    # delete connection
    tear_down_conn(placeboify, conn, vpn['VpnConnectionId'])


def test_modify_deleted_connection(placeboify, maybe_sleep):
    # setup dependencies for 1 vpn connection
    dependencies = setup_req(placeboify, 1)
    params, vpn, m, conn = dependencies['params'], dependencies['vpn'], dependencies['module'], dependencies['connection']

    # delete it
    tear_down_conn(placeboify, conn, vpn['VpnConnectionId'])

    # try to update the deleted connection
    m.params.update(vpn_connection_id=vpn['VpnConnectionId'])
    with pytest.raises(Exception) as error_message:
        ec2_vpc_vpn.ensure_present(conn, m.params)
        assert error_message == "There is no VPN connection available or pending with that id. Did you delete it?"


def test_delete_connection(placeboify, maybe_sleep):
    # setup dependencies for 1 vpn connection
    dependencies = setup_req(placeboify, 1)
    params, vpn, m, conn = dependencies['params'], dependencies['vpn'], dependencies['module'], dependencies['connection']

    # delete it
    changed, vpn = ec2_vpc_vpn.ensure_absent(conn, m.params)

    assert changed is True
    assert vpn == {}


def test_delete_nonexistent_connection(placeboify, maybe_sleep):
    # create parameters and ensure any connection matching (None) is deleted
    params = {'filters': {'tags': {'ThisConnection': 'DoesntExist'}}, 'delay': 15, 'wait_timeout': 600}
    m, conn = setup_mod_conn(placeboify, params)
    changed, vpn = ec2_vpc_vpn.ensure_absent(conn, m.params)

    assert changed is False
    assert vpn == {}


def test_check_for_update_tags(placeboify, maybe_sleep):
    # setup dependencies for 1 vpn connection
    dependencies = setup_req(placeboify, 1)
    params, vpn, m, conn = dependencies['params'], dependencies['vpn'], dependencies['module'], dependencies['connection']

    # add and remove a number of tags
    m.params['tags'] = {'One': 'one', 'Two': 'two'}
    ec2_vpc_vpn.ensure_present(conn, m.params)
    m.params['tags'] = {'Two': 'two', 'Three': 'three', 'Four': 'four'}
    changes = ec2_vpc_vpn.check_for_update(conn, m.params, vpn['VpnConnectionId'])

    flat_dict_changes = boto3_tag_list_to_ansible_dict(changes['tags_to_add'])
    correct_changes = boto3_tag_list_to_ansible_dict([{'Key': 'Three', 'Value': 'three'}, {'Key': 'Four', 'Value': 'four'}])
    assert flat_dict_changes == correct_changes
    assert changes['tags_to_remove'] == ['One']

    # delete connection
    tear_down_conn(placeboify, conn, vpn['VpnConnectionId'])


def test_check_for_update_nonmodifiable_attr(placeboify, maybe_sleep):
    # setup dependencies for 1 vpn connection
    dependencies = setup_req(placeboify, 1)
    params, vpn, m, conn = dependencies['params'], dependencies['vpn'], dependencies['module'], dependencies['connection']
    current_vgw = params['vpn_gateway_id']

    # update a parameter that isn't modifiable
    m.params.update(vpn_gateway_id="invalidchange")

    err = 'You cannot modify vpn_gateway_id, the current value of which is {0}. Modifiable VPN connection attributes are tags.'.format(current_vgw)
    with pytest.raises(Exception) as error_message:
        ec2_vpc_vpn.check_for_update(m, conn, vpn['VpnConnectionId'])
        assert error_message == err

    # delete connection
    tear_down_conn(placeboify, conn, vpn['VpnConnectionId'])


def test_add_tags(placeboify, maybe_sleep):
    # setup dependencies for 1 vpn connection
    dependencies = setup_req(placeboify, 1)
    params, vpn, m, conn = dependencies['params'], dependencies['vpn'], dependencies['module'], dependencies['connection']

    # add a tag to the connection
    ec2_vpc_vpn.add_tags(conn, vpn['VpnConnectionId'], add=[{'Key': 'Ansible-Test', 'Value': 'VPN'}])

    # assert tag is there
    current_vpn = ec2_vpc_vpn.find_connection(conn, params)
    assert current_vpn['Tags'] == [{'Key': 'Ansible-Test', 'Value': 'VPN'}]

    # delete connection
    tear_down_conn(placeboify, conn, vpn['VpnConnectionId'])


def test_remove_tags(placeboify, maybe_sleep):
    # setup dependencies for 1 vpn connection
    dependencies = setup_req(placeboify, 1)
    params, vpn, m, conn = dependencies['params'], dependencies['vpn'], dependencies['module'], dependencies['connection']

    # remove a tag from the connection
    ec2_vpc_vpn.remove_tags(conn, vpn['VpnConnectionId'], remove=['Ansible-Test'])

    # assert the tag is gone
    current_vpn = ec2_vpc_vpn.find_connection(conn, params)
    assert 'Tags' not in current_vpn

    # delete connection
    tear_down_conn(placeboify, conn, vpn['VpnConnectionId'])


def test_add_routes(placeboify, maybe_sleep):
    # setup dependencies for 1 vpn connection
    dependencies = setup_req(placeboify, 1)
    params, vpn, m, conn = dependencies['params'], dependencies['vpn'], dependencies['module'], dependencies['connection']

    # create connection with a route
    ec2_vpc_vpn.add_routes(conn, vpn['VpnConnectionId'], ['195.168.2.0/24', '196.168.2.0/24'])

    # assert both routes are there
    current_vpn = ec2_vpc_vpn.find_connection(conn, params)
    assert set(each['DestinationCidrBlock'] for each in current_vpn['Routes']) == set(['195.168.2.0/24', '196.168.2.0/24'])

    # delete connection
    tear_down_conn(placeboify, conn, vpn['VpnConnectionId'])


def setup_req(placeboify, number_of_results=1):
    ''' returns dependencies for VPN connections '''
    assert number_of_results in (1, 2)
    results = []
    cgw, vgw = get_dependencies()
    for each in range(0, number_of_results):
        params = make_params(cgw[each], vgw[each])
        m, conn = setup_mod_conn(placeboify, params)
        _, vpn = ec2_vpc_vpn.ensure_present(conn, params)

        results.append({'module': m, 'connection': conn, 'vpn': vpn, 'params': params})
    if number_of_results == 1:
        return results[0]
    else:
        return results[0], results[1]
