import boto
import itertools
import sys
import unittest
import uuid

from exceptions import SystemExit
from moto import mock_ec2

from ansible.modules.core.cloud.amazon.ec2_snapshot import create_snapshot


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

        #self.existing_snapshot = ec2.create_snapshot(self.existing_volume.id)
        self.module = MockModule()

        self.snapshot_args = {'state': 'present',
                              'description': 'I am a monkey',
                              'device_name': 'jim'}

        self.ec2 = ec2

    def tearDown(self):
        super(EC2SnapshotTest, self).tearDown()
        self.mock.stop()

    def setupInstance(self):
        self.existing_instance = self.ec2.run_instances("fake ami").instances[0]
        self.existing_volume = self.ec2.create_volume(size=100, zone='us-east-1')

    def test_create_from_instance(self):
        self.setupInstance()
        with self.assertRaises(SystemExit) as context:
            create_snapshot(self.module,
                            self.ec2,
                            instance_id=self.existing_instance.id,
                            **self.snapshot_args)

        self.assertTrue(self.module.exit['changed'])
        self.assertIsNone(self.module.fail)
        self.assertEqual(0, context.exception.code)

    def test_create_from_instance_missing_name(self):

        with self.assertRaises(SystemExit) as context:
            del self.snapshot_args['device_name']
            create_snapshot(self.module,
                            self.ec2,
                            instance_id='no instance',
                            **self.snapshot_args)

        self.assertIsNotNone(self.module.fail)
        self.assertIsNone(self.module.exit)
        self.assertEqual(1, context.exception.code)

    def test_create_from_instance_missing_id(self):

        with self.assertRaises(SystemExit) as context:
            create_snapshot(self.module,
                            self.ec2,
                            **self.snapshot_args)

        self.assertIsNotNone(self.module.fail)
        self.assertIsNone(self.module.exit)
        self.assertEqual(1, context.exception.code)

    def test_wrong_number_of_ids(self):
        args = ['instance_id', 'snapshot_id', 'volume_id']
        arg_combos = list(itertools.combinations(args, 2))
        arg_combos.extend(itertools.combinations(args, 3))
        arg_combos.append([])

        for args in arg_combos:
            snapshot_args = {}
            for arg in args:
                snapshot_args[arg] = str(uuid.uuid4())
            snapshot_args.update(self.snapshot_args)
            with self.assertRaises(SystemExit) as context:
                create_snapshot(self.module,
                                self.ec2,
                                **snapshot_args)

            self.assertIsNotNone(self.module.fail)
            self.assertIsNone(self.module.exit)
            self.assertEqual(1, context.exception.code)










