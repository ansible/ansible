# (c) 2017 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.utils.amazon_placebo_fixtures import placeboify, maybe_sleep
from ansible.modules.cloud.amazon import aws_direct_connect_connection


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


# When rerecording these tests, create a stand alone connection with default values in us-west-2
# with the name ansible-test-connection and set connection_id to the appropriate value
connection_id = "dxcon-fgq9rgot"
connection_name = 'ansible-test-connection'


def test_connection_status(placeboify, maybe_sleep):
    client = placeboify.client('directconnect')
    status = aws_direct_connect_connection.connection_status(client, connection_id)['connection']
    assert status['connectionName'] == connection_name
    assert status['connectionId'] == connection_id


def test_connection_exists_by_id(placeboify, maybe_sleep):
    client = placeboify.client('directconnect')
    exists = aws_direct_connect_connection.connection_exists(client, connection_id)
    assert exists == connection_id


def test_connection_exists_by_name(placeboify, maybe_sleep):
    client = placeboify.client('directconnect')
    exists = aws_direct_connect_connection.connection_exists(client, None, connection_name)
    assert exists == connection_id


def test_connection_does_not_exist(placeboify, maybe_sleep):
    client = placeboify.client('directconnect')
    exists = aws_direct_connect_connection.connection_exists(client, 'dxcon-notthere')
    assert exists is False


def test_changed_properties(placeboify, maybe_sleep):
    client = placeboify.client('directconnect')
    status = aws_direct_connect_connection.connection_status(client, connection_id)['connection']
    location = "differentlocation"
    bandwidth = status['bandwidth']
    assert aws_direct_connect_connection.changed_properties(status, location, bandwidth) is True


def test_associations_are_not_updated(placeboify, maybe_sleep):
    client = placeboify.client('directconnect')
    status = aws_direct_connect_connection.connection_status(client, connection_id)['connection']
    lag_id = status.get('lagId')
    assert aws_direct_connect_connection.update_associations(client, status, connection_id, lag_id) is False


def test_create_and_delete(placeboify, maybe_sleep):
    client = placeboify.client('directconnect')
    created_conn = verify_create_works(placeboify, maybe_sleep, client)
    deleted_conn = verify_delete_works(placeboify, maybe_sleep, client, created_conn)


def verify_create_works(placeboify, maybe_sleep, client):
    created = aws_direct_connect_connection.create_connection(client=client,
                                                              location="EqSE2",
                                                              bandwidth="1Gbps",
                                                              name="ansible-test-2",
                                                              lag_id=None)
    assert created.startswith('dxcon')
    return created


def verify_delete_works(placeboify, maybe_sleep, client, conn_id):
    changed = aws_direct_connect_connection.ensure_absent(client, conn_id)
    assert changed is True
