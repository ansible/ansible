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
import collections
from units.utils.amazon_placebo_fixtures import placeboify, maybe_sleep
from ansible.modules.cloud.amazon import aws_direct_connect_link_aggregation_group as lag_module
from ansible.module_utils.ec2 import get_aws_connection_info, boto3_conn


@pytest.fixture(scope="module")
def dependencies():

    # each LAG dict will contain the keys: module, connections, virtual_interfaces
    Dependencies = collections.namedtuple("Dependencies", ["lag_1", "lag_2"])
    lag_1 = dict()
    lag_2 = dict()

    vanilla_params = {"name": "ansible_lag_1",
                      "location": "EqSe2",
                      "num_connections": 1,
                      "min_links": 0,
                      "bandwidth": "1Gbps"}

    for lag in ("ansible_lag_1", "ansible_lag_2"):
        params = dict(vanilla_params)
        params["name"] = lag
        if lag == "ansible_lag_1":
            lag_1["module"] = FakeModule(**params)
        else:
            lag_2["module"] = FakeModule(**params)

    if os.getenv("PLACEBO_RECORD"):
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(lag_1["module"], boto3=True)
        client = boto3_conn(lag_1["module"], conn_type="client", resource="directconnect", region=region, endpoint=ec2_url, **aws_connect_kwargs)
        # See if link aggregation groups exist
        for name in ("ansible_lag_1", "ansible_lag_2"):
            lag_id = lag_module.create_lag(client, num_connections=1, location="EqSe2", bandwidth="1Gbps", name=name, connection_id=None)
            if name == "ansible_lag_1":
                lag_1["lag_id"] = lag_id
                lag_1["name"] = name
            else:
                lag_2["lag_id"] = lag_id
                lag_2["name"] = name
        yield Dependencies(lag_1=lag_1, lag_2=lag_2)
    else:
        lag_1.update(lag_id="dxlag-fgkk4dja", name="ansible_lag_1")
        lag_2.update(lag_id="dxlag-fgytkicv", name="ansible_lag_2")
        yield Dependencies(lag_1=lag_1, lag_2=lag_2)

    if os.getenv("PLACEBO_RECORD"):
        # clean up
        lag_module.ensure_absent(client, lag_1["lag_id"], lag_1["name"], True, True, True, 120)
        lag_module.ensure_absent(client, lag_2["lag_id"], lag_2["name"], True, True, True, 120)


class FakeModule(object):
    def __init__(self, **kwargs):
        self.params = kwargs

    def fail_json(self, *args, **kwargs):
        self.exit_args = args
        self.exit_kwargs = kwargs
        raise Exception("FAIL")

    def exit_json(self, *args, **kwargs):
        self.exit_args = args
        self.exit_kwargs = kwargs


def test_nonexistent_lag_status(placeboify, maybe_sleep):
    client = placeboify.client("directconnect")
    exists = lag_module.lag_exists(client=client,
                                   lag_id="doesntexist",
                                   lag_name="doesntexist",
                                   verify=True)
    assert not exists


def test_lag_status(placeboify, maybe_sleep, dependencies):
    client = placeboify.client("directconnect")
    status = lag_module.lag_status(client, lag_id=dependencies.lag_1.get("lag_id"))
    assert status.get("lagId") == dependencies.lag_1.get("lag_id")
    assert status.get("lagName") == "ansible_lag_1"


def test_lag_exists(placeboify, maybe_sleep, dependencies):
    client = placeboify.client("directconnect")
    exists = lag_module.lag_exists(client=client,
                                   lag_id=dependencies.lag_1.get("lag_id"),
                                   lag_name=None,
                                   verify=True)
    assert exists


def test_lag_exists_using_name(placeboify, maybe_sleep, dependencies):
    client = placeboify.client("directconnect")
    exists = lag_module.lag_exists(client=client,
                                   lag_id=None,
                                   lag_name=dependencies.lag_1.get("name"),
                                   verify=True)
    assert exists


def test_nonexistent_lag_does_not_exist(placeboify, maybe_sleep):
    client = placeboify.client("directconnect")
    exists = lag_module.lag_exists(client=client,
                                   lag_id="dxlag-XXXXXXXX",
                                   lag_name="doesntexist",
                                   verify=True)
    assert not exists


def test_lag_changed_true(placeboify, maybe_sleep, dependencies):
    client = placeboify.client("directconnect")
    status = lag_module.lag_status(client=client, lag_id=dependencies.lag_1.get("lag_id"))
    assert lag_module.lag_changed(status, "new_name", 1)


def test_lag_changed_true_no(placeboify, maybe_sleep, dependencies):
    client = placeboify.client("directconnect")
    status = lag_module.lag_status(client=client, lag_id=dependencies.lag_1.get("lag_id"))
    assert not lag_module.lag_changed(status, "ansible_lag_1", 0)


def test_update_lag(placeboify, maybe_sleep, dependencies):
    client = placeboify.client("directconnect")
    status_before = lag_module.lag_status(client=client, lag_id=dependencies.lag_2.get("lag_id"))
    lag_module.update_lag(client,
                          lag_id=dependencies.lag_2.get("lag_id"),
                          lag_name="ansible_lag_2_update",
                          min_links=0,
                          wait=False,
                          wait_timeout=0,
                          num_connections=1)
    status_after = lag_module.lag_status(client=client, lag_id=dependencies.lag_2.get("lag_id"))
    assert status_before != status_after

    # remove the lag name from the statuses and verify it was the only thing changed
    del status_before['lagName']
    del status_after['lagName']
    assert status_before == status_after


def test_delete_nonexistent_lag(placeboify, maybe_sleep):
    client = placeboify.client("directconnect")
    changed = lag_module.ensure_absent(client, "dxlag-XXXXXXXX", "doesntexist", True, True, True, 120)
    assert not changed


def test_delete_lag_with_connections_without_force_delete(placeboify, maybe_sleep, dependencies):
    client = placeboify.client("directconnect")
    with pytest.raises(Exception) as error_message:
        lag_module.ensure_absent(client, dependencies.lag_1.get("lag_id"), "ansible_lag_1", False, True, True, 120)
        assert "To force deletion of the LAG use delete_force: True" in error_message


def test_delete_lag_with_connections(placeboify, maybe_sleep, dependencies):
    client = placeboify.client("directconnect")
    changed = lag_module.ensure_absent(client, dependencies.lag_1.get("lag_id"), "ansible_lag_1", True, True, True, 120)
    assert changed
