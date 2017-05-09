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
from . placebo_fixtures import placeboify, maybe_sleep
from ansible.modules.cloud.amazon import ec2_vpc_vpn as v
from ansible.module_utils._text import to_text
from ansible.module_utils.ec2 import get_aws_connection_info, boto3_conn


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
    cgw = connection.describe_customer_gateways(DryRun=False, Filters=[{'Name': 'state', 'Values': ['available']}, {'Name': 'tag:Name', 'Values': ['Ansible-CGW']}])
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


def make_params(cgw, vgw, tags={}, filters={}):
    return {'check_mode': False,
            'customer_gateway_id': cgw,
            'static_only': True,
            'vpn_gateway_id': vgw,
            'connection_type': 'ipsec.1',
            'purge_tags': True,
            'tags': tags,
            'filters': filters}


def make_conn(placeboify, module, connection):
    changed, vpn = v.create_connection(module, connection)
    return changed, vpn


def tear_down_conn(module, connection, vpn_connection_id):
    v.delete_connection(module, connection, vpn_connection_id)


def test_find_connection_vpc_conn_id(placeboify, maybe_sleep):
    # get list of customer gateways and virtual private gateways
    cgw, vgw = get_dependencies()

    # create two connections
    params = make_params(cgw[0], vgw[0], tags={})
    params2 = make_params(cgw[1], vgw[1], tags={})
    m, conn = setup_mod_conn(placeboify, params)
    m2, conn2 = setup_mod_conn(placeboify, params2)
    _, vpn1 = make_conn(placeboify, m, conn)
    _, vpn2 = make_conn(placeboify, m2, conn2)

    # find the connection with a vpn_connection_id and assert it is the expected one
    assert vpn1['VpnConnectionId'] == v.find_connection(m, conn, vpn1['VpnConnectionId'])['VpnConnectionId']


def test_find_connection_filters(placeboify, maybe_sleep):
    # get list of customer gateways and virtual private gateways
    cgw, vgw = get_dependencies()

    # create two connections with different tags
    params = make_params(cgw[0], vgw[0], tags={'Wrong': 'Tag'})
    params2 = make_params(cgw[1], vgw[1], tags={'Correct': 'Tag'})
    m, conn = setup_mod_conn(placeboify, params)
    m2, conn2 = setup_mod_conn(placeboify, params2)
    _, vpn1 = v.ensure_present(m, conn)
    _, vpn2 = v.ensure_present(m2, conn2)

    # reset the parameters so only filtering by tags will occur
    m.params = {'check_mode': False, 'filters': {'tag':{'Correct':'Tag'}}}

    # find the connection that has the parameters above
    found = v.find_connection(m, conn)

    # assert the correct connection was found
    assert found['VpnConnectionId'] == vpn2['VpnConnectionId']

    # delete the connections
    tear_down_conn(m, conn, vpn1['VpnConnectionId'])
    tear_down_conn(m, conn, vpn2['VpnConnectionId'])

def test_find_connection_insufficient_filters(placeboify, maybe_sleep):
    # get list of customer gateways and virtual private gateways
    cgw, vgw = get_dependencies()

    # create two connections with the same tags
    params = make_params(cgw[0], vgw[0], tags={'Correct': 'Tag'})
    params2 = make_params(cgw[1], vgw[1], tags={'Correct': 'Tag'})
    m, conn = setup_mod_conn(placeboify, params)
    m2, conn2 = setup_mod_conn(placeboify, params2)
    _, vpn1 = v.ensure_present(m, conn)
    _, vpn2 = v.ensure_present(m2, conn2)

    # reset the parameters so only filtering by tags will occur
    m.params = {'check_mode': False, 'filters': {'tag':{'Correct':'Tag'}}}

    # assert that multiple matching connections have been found
    with pytest.raises(Exception) as error_message:
        v.find_connection(m, conn)
        assert error_message == "More than one matching VPN connection was found.To modify or delete a VPN please specify vpn_connection_id or add filters."
    
    # delete the connections
    tear_down_conn(m, conn, vpn1['VpnConnectionId'])
    tear_down_conn(m, conn, vpn2['VpnConnectionId'])


def test_find_connection_nonexistent(placeboify, maybe_sleep):
    # create parameters but don't create a connection with them
    params = {'check_mode': False, 'filters': {'tag':{'Correct':'Tag'}}}
    m, conn = setup_mod_conn(placeboify, params)
    
    # try to find a connection with matching parameters and assert None are found
    assert v.find_connection(m, conn) is None


def test_create_connection(placeboify, maybe_sleep):
    # get list of customer gateways and virtual private gateways
    cgw, vgw = get_dependencies()

    # create a connection
    params = make_params(cgw[0], vgw[0])
    m, conn = setup_mod_conn(placeboify, params)
    changed, vpn = v.ensure_present(m, conn)

    # assert that changed is true and that there is a connection id
    assert changed == True
    assert 'VpnConnectionId' in vpn

    # delete connection
    tear_down_conn(m, conn, vpn['VpnConnectionId'])


def test_create_connection_that_exists(placeboify, maybe_sleep):
    # get list of customer gateways and virtual private gateways
    cgw, vgw = get_dependencies()

    # create a connection
    params = make_params(cgw[0], vgw[0])
    m, conn = setup_mod_conn(placeboify, params)
    changed, vpn1 = v.ensure_present(m, conn)

    # try to recreate the same connection
    changed, vpn2 = v.ensure_present(m, conn)

    # nothing should have changed
    assert changed == False
    assert vpn1['VpnConnectionId'] == vpn2['VpnConnectionId']

    # delete connection
    tear_down_conn(m, conn, vpn1['VpnConnectionId'])


def test_modify_deleted_connection(placeboify, maybe_sleep):
    # get list of customer gateways and virtual private gateways
    cgw, vgw = get_dependencies()

    # create and delete a connection
    params = make_params(cgw[0], vgw[0])
    m, conn = setup_mod_conn(placeboify, params)
    changed, vpn = v.ensure_present(m, conn)
    tear_down_conn(m, conn, vpn['VpnConnectionId'])

    # try to update the deleted connection
    m.params.update(vpn_connection_id=vpn['VpnConnectionId'])
    with pytest.raises(Exception) as error_message:
        v.ensure_present(m, conn)
        assert error_message == "There is no VPN connection available or pending with that id. Did you delete it?"


def test_delete_connection(placeboify, maybe_sleep):
    # get list of customer gateways and virtual private gateways
    cgw, vgw = get_dependencies()

    # create a connection
    params = make_params(cgw[0], vgw[0])
    m, conn = setup_mod_conn(placeboify, params)
    changed, vpn = v.ensure_present(m, conn)

    # delete it
    changed, vpn = v.ensure_absent(m, conn)

    assert changed == True
    assert vpn == {}


def test_delete_nonexistent_connection(placeboify, maybe_sleep):
    # create parameters and ensure any connection matching (None) is deleted
    params = {'check_mode': False, 'filters': {'tag':{'ThisConnection':'DoesntExist'}}}
    m, conn = setup_mod_conn(placeboify, params)
    changed, vpn = v.ensure_absent(m, conn)

    assert changed == False
    assert vpn == {}


def test_check_for_update_tags(placeboify, maybe_sleep):
    # get list of customer gateways and virtual private gateways
    cgw, vgw = get_dependencies()

    # create connection
    params = make_params(cgw[0], vgw[0], tags={'One': 'one', 'Two': 'two'})
    m, conn = setup_mod_conn(placeboify, params)
    changed, vpn = v.ensure_present(m, conn)

    # add and remove a number of tags
    m.params['tags'] = {'Two': 'two', 'Three': 'three', 'Four': 'four'}
    tags_to_add, tags_to_remove = v.check_for_update(m, conn, vpn['VpnConnectionId'])

    assert tags_to_add == {'Three': 'three', 'Four': 'four'}
    assert tags_to_remove == {'One': 'one'}

    # delete connection
    tear_down_conn(m, conn, vpn['VpnConnectionId'])


def test_check_for_update_nonmodifiable_attr(placeboify, maybe_sleep):
    # get list of customer gateways and virtual private gateways
    cgw, vgw = get_dependencies()

    # create connection
    params = make_params(cgw[0], vgw[0])
    m, conn = setup_mod_conn(placeboify, params)
    changed, vpn = v.ensure_present(m, conn)

    # update a parameter that isn't modifiable
    m.params.update(vpn_gateway_id=vgw[1])

    with pytest.raises(Exception) as error_message:
        v.check_for_update(m, conn, vpn['VpnConnectionId'])
        assert error_message == 'You cannot modify vpn_gateway_id, the current value of which is {0}. Modifiable VPN connection attributes are tags.'.format(vgw[0])

    # delete connection
    tear_down_conn(m, conn, vpn['VpnConnectionId'])


def test_tag_connection_add_tags(placeboify, maybe_sleep):
    # get list of customer gateways and virtual private gateways
    cgw, vgw = get_dependencies()

    # create connection
    params = make_params(cgw[0], vgw[0])
    m, conn = setup_mod_conn(placeboify, params)
    _, vpn = make_conn(placeboify, m, conn)

    # add a tag to the connection
    changed, vpn = v.tag_connection(m, conn, vpn['VpnConnectionId'], add={'Ansible-Test': 'VPN'})

    assert changed == True
    assert vpn['Tags'] == [{'Key': 'Ansible-Test', 'Value': 'VPN'}]

    # delete connection
    tear_down_conn(m, conn, vpn['VpnConnectionId'])


def test_tag_connection_remove_tags(placeboify, maybe_sleep):
    # get list of customer gateways and virtual private gateways
    cgw, vgw = get_dependencies()

    # create connection with a tag
    params = make_params(cgw[0], vgw[0], tags={'Ansible-Test': 'VPN'})
    m, conn = setup_mod_conn(placeboify, params)
    _, vpn = v.ensure_present(m, conn)

    # remove a tag from the connection
    changed, vpn = v.tag_connection(m, conn, vpn['VpnConnectionId'], add={}, remove={'Ansible-Test': 'VPN'})

    assert changed == True
    assert 'Tags' not in vpn

    # delete connection
    tear_down_conn(m, conn, vpn['VpnConnectionId'])
