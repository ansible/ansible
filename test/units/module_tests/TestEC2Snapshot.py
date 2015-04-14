import boto
import datetime
import itertools
import sys
import unittest
import uuid

from exceptions import SystemExit
from moto import mock_ec2

from ansible.modules.core.cloud.amazon.ec2_snapshot import create_snapshot, \
    _get_most_recent_snapshot


class MockModule(object):
    def __init__(self):
        self.fail = None
        self.exit = None

    def fail_json(self, **kwargs):
        self.fail = kwargs
        sys.exit(1)

    def exit_json(self, **kwargs):
        self.exit = kwargs
        sys.exit(0)


class EC2SnapshotTest(unittest.TestCase):
    def setUp(self):
        super(EC2SnapshotTest, self).setUp()
        self.mock = mock_ec2()
        self.mock.start()
        ec2 = boto.connect_ec2("FAKE", "FAKE")

        self.module = MockModule()

        self.snapshot_args = dict(state='present', description='I am a monkey')

        self.ec2 = ec2

    def tearDown(self):
        super(EC2SnapshotTest, self).tearDown()
        self.mock.stop()

    def setup_instance(self):
        self.existing_instance = self.ec2.run_instances("fake ami").instances[0]
        self.existing_volume = self.ec2.create_volume(size=100,
                                                      zone='us-east-1')

    def assert_fail(self, context):
        self.assertIsNotNone(self.module.fail)
        self.assertIsNone(self.module.exit)
        self.assertEqual(1, context.exception.code)

    def assert_changed(self, context):
        self._assert_success(context, changed=True)

    def assert_unchanged(self, context):
        self._assert_success(context, changed=False)

    def _assert_success(self, context, changed):
        if changed:
            self.assertTrue(self.module.exit['changed'])
        else:
            if 'changed' in self.module.exit:
                self.assertFalse(self.module.exit['changed'])
        self.assertIsNone(self.module.fail)
        self.assertEqual(0, context.exception.code)

    def create_ec2_snapshot(self):
        volume = self.ec2.create_volume(10, 'us-east-1')
        snapshot = self.ec2.create_snapshot(volume.id, 'meh')
        return snapshot

    def test_create_from_instance(self):
        self.setup_instance()
        self.snapshot_args['device_name'] = 'jim'
        with self.assertRaises(SystemExit) as context:
            create_snapshot(self.module, self.ec2,
                            instance_id=self.existing_instance.id,
                            **self.snapshot_args)

        self.assert_changed(context)

    def test_create_from_instance_no_volumes(self):
        self.snapshot_args['device_name'] = 'jim'
        self.existing_instance = self.ec2.run_instances("fake ami").instances[0]
        with self.assertRaises(SystemExit) as context:
            create_snapshot(self.module, self.ec2,
                            instance_id=self.existing_instance.id,
                            **self.snapshot_args)

        self.assert_fail(context)

    def test_create_from_instance_missing_name(self):
        with self.assertRaises(SystemExit) as context:
            create_snapshot(self.module, self.ec2, instance_id='no instance',
                            **self.snapshot_args)

        self.assert_fail(context)

    def test_create_from_instance_missing_id(self):

        with self.assertRaises(SystemExit) as context:
            create_snapshot(self.module, self.ec2, device_name='jim',
                            **self.snapshot_args)

        self.assert_fail(context)

    def test_wrong_number_of_ids(self):
        args = ['instance_id', 'snapshot_id', 'volume_id']
        arg_combos = list(itertools.combinations(args, 2))
        arg_combos.extend(itertools.combinations(args, 3))
        arg_combos.append([])

        for args in arg_combos:
            case_args = {}
            for arg in args:
                case_args[arg] = str(uuid.uuid4())
            case_args.update(self.snapshot_args)
            with self.assertRaises(SystemExit) as context:
                create_snapshot(self.module, self.ec2, **case_args)

            self.assert_fail(context)

    def test_create_from_volume(self):
        volume = self.ec2.create_volume(10, 'us-east-1')
        with self.assertRaises(SystemExit) as context:
            create_snapshot(self.module, self.ec2, volume_id=volume.id,
                            **self.snapshot_args)

        self.assert_changed(context)

    def test_create_from_missing_volume(self):
        with self.assertRaises(SystemExit) as context:
            create_snapshot(self.module, self.ec2, volume_id=uuid.uuid4(),
                            **self.snapshot_args)

        self.assert_fail(context)

    def test_delete_snapshot(self):

        snapshot = self.create_ec2_snapshot()
        self.assertEqual(1, len(self.ec2.get_all_snapshots()))

        self.snapshot_args['state'] = 'absent'

        with self.assertRaises(SystemExit) as context:
            create_snapshot(self.module, self.ec2, snapshot_id=snapshot.id,
                            **self.snapshot_args)

        self.assert_changed(context)
        self.assertEqual(0, len(self.ec2.get_all_snapshots()))

    def test_delete_missing_snapshot(self):
        self.snapshot_args['state'] = 'absent'

        with self.assertRaises(SystemExit) as context:
            create_snapshot(self.module, self.ec2,
                            snapshot_id=str(uuid.uuid4()), **self.snapshot_args)

        self.assert_unchanged(context)

    # def test_last_snapshot_min_age(self):
    # snapshot = self.create_ec2_snapshot()
    #
    #     with self.assertRaises(SystemExit) as context:
    #         create_snapshot(self.module,
    #                         self.ec2,
    #                         volume_id=snapshot.volume_id,
    #                         snapshot_max_age=0.00000001,
    #                         **self.snapshot_args)
    #
    #     self.assert_changed(context)

    def test_get_most_recent_snapshot(self):

        snap_1 = self.create_ec2_snapshot()
        snap_2 = self.create_ec2_snapshot()

        snaps = [snap_1, snap_2]

        # moto doesn't set the time
        for snap in snaps:
            snap.start_time = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z')

        found_snap = _get_most_recent_snapshot(snaps)
        self.assertEqual(snap_1, found_snap)

        found_snap = _get_most_recent_snapshot(snaps, max_snapshot_age_secs=1,
                                               now=datetime.datetime.utcnow() + datetime.timedelta(
                                                   seconds=2))
        self.assertEqual(None, found_snap)










