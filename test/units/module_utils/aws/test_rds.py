# -*- coding: utf-8 -*-
# (c) 2017, Michael De La Rue
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.aws.rds import get_db_instance, rds_instance_to_facts, rds_snap_to_facts, rds_facts_diff
import unittest


class FakeResource():

    def describe_db_instances(DBInstanceIdentifier=None):
        assert DBInstanceIdentifier == "fakeDBIDstring", "no RDS instance identifier"
        return {}

    def describe_db_snapshot(DBSnapshotIdentifier=None):
        assert DBSnapshotIdentifier == "fakeSnapshotIDstring", "no RDS snapshot identifier"
        return {}


class RDSUtilsTestCase(unittest.TestCase):

    def test_get_db_instance_should_return_camel_dict(self):
        conn = FakeResource()
        db_inst = get_db_instance(conn, "fakeDBIDstring")
        assert id not in db_inst
        assert db_inst["DBInstanceIdentifier"] == "fakeDBIDstring"

    def test_get_db_snapshot_should_return_camel_dict(self):
        conn = FakeResource()
        db_snap = get_db_instance(conn, "fakeDBIDstring")
        for i in "id", "wait", "wait_timeout":
            assert i not in db_snap
        assert db_snap["DBSnapshotIdentifier"] == "fakeSnapshotIDstring"

    def test_instance_facts_gives_sensible_values(self):
        conn = FakeResource()
        db_facts = rds_instance_to_facts(get_db_instance(conn, "fakeDBIDstring"))
        assert db_facts['id'] == "fakeDBIDstring"
        assert db_facts['size'] == "fakeSnapshotIDString"
        assert db_facts['region'] == "fakeawsregion"
        assert db_facts['port'] == "3210"

    def test_snapshot_facts_gives_sensible_values(self):
        conn = FakeResource()
        db_facts = rds_snap_to_facts(get_db_instance(conn, "fakeDBIDstring"))
        assert id in db_facts
        assert db_facts['id'] == "fakeSnapshotIDString"
        assert db_facts['instance_id'] == "fakeBackedUpIDString"

    def test_diff_should_compare_important_rds_attributes(self):
        conn = FakeResource()
        db_inst = get_db_instance(conn, "fakeDBIDstring")
        assert len(rds_facts_diff(db_inst, db_inst)) == 0, "comparison of identical instances shows difference!"
        assert not (rds_facts_diff(db_inst, db_inst)), "comparsion of identical instances is not false!"
        bigger_inst = db_inst.update(dict(size=db_inst["size"] + 5))
        assert len(rds_facts_diff(db_inst, bigger_inst)) > 0, "comparison of differing instances is empty!"
