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

__metaclass__ = type
from ansible.compat.tests.mock import patch, call
from ansible.modules.system import parted as parted_module
from ansible.modules.system.parted import parse_partition_info
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase, set_module_args

# Example of output : parted -s -m /dev/sdb -- unit 'MB' print
parted_output1 = """
BYT;
/dev/sdb:286061MB:scsi:512:512:msdos:ATA TOSHIBA THNSFJ25:;
1:1.05MB:106MB:105MB:fat32::esp;
2:106MB:368MB:262MB:ext2::;
3:368MB:256061MB:255692MB:::;"""

# corresponding dictionary after parsing by parse_partition_info
parted_dict1 = {
    "generic": {
        "dev": "/dev/sdb",
        "size": 286061.0,
        "unit": "mb",
        "table": "msdos",
        "model": "ATA TOSHIBA THNSFJ25",
        "logical_block": 512,
        "physical_block": 512
    },
    "partitions": [{
        "num": 1,
        "begin": 1.05,
        "end": 106.0,
        "size": 105.0,
        "fstype": "fat32",
        "name": '',
        "flags": ["esp"],
        "unit": "mb"
    }, {
        "num": 2,
        "begin": 106.0,
        "end": 368.0,
        "size": 262.0,
        "fstype": "ext2",
        "name": '',
        "flags": [],
        "unit": "mb"
    }, {
        "num": 3,
        "begin": 368.0,
        "end": 256061.0,
        "size": 255692.0,
        "fstype": "",
        "name": '',
        "flags": [],
        "unit": "mb"
    }]
}

parted_output2 = """
BYT;
/dev/sdb:286061MB:scsi:512:512:msdos:ATA TOSHIBA THNSFJ25:;"""

# corresponding dictionary after parsing by parse_partition_info
parted_dict2 = {
    "generic": {
        "dev": "/dev/sdb",
        "size": 286061.0,
        "unit": "mb",
        "table": "msdos",
        "model": "ATA TOSHIBA THNSFJ25",
        "logical_block": 512,
        "physical_block": 512
    },
    "partitions": []
}


class TestParted(ModuleTestCase):
    def setUp(self):
        super(TestParted, self).setUp()

        self.module = parted_module
        self.mock_check_parted_label = (patch('ansible.modules.system.parted.check_parted_label', return_value=False))
        self.check_parted_label = self.mock_check_parted_label.start()

        self.mock_parted = (patch('ansible.modules.system.parted.parted'))
        self.parted = self.mock_parted.start()

        self.mock_run_command = (patch('ansible.module_utils.basic.AnsibleModule.run_command'))
        self.run_command = self.mock_run_command.start()

        self.mock_get_bin_path = (patch('ansible.module_utils.basic.AnsibleModule.get_bin_path'))
        self.get_bin_path = self.mock_get_bin_path.start()

    def tearDown(self):
        super(TestParted, self).tearDown()
        self.mock_run_command.stop()
        self.mock_get_bin_path.stop()
        self.mock_parted.stop()
        self.mock_check_parted_label.stop()

    def execute_module(self, failed=False, changed=False, script=None):
        if failed:
            result = self.failed()
            self.assertTrue(result['failed'], result)
        else:
            result = self.changed(changed)
            self.assertEqual(result['changed'], changed, result)

        if script:
            self.assertEqual(script, result['script'], result['script'])

        return result

    def failed(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            self.module.main()

        result = exc.exception.args[0]
        self.assertTrue(result['failed'], result)
        return result

    def changed(self, changed=False):
        with self.assertRaises(AnsibleExitJson) as exc:
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], changed, result)
        return result

    def test_parse_partition_info(self):
        """Test that the parse_partition_info returns the expected dictionary"""
        self.assertEqual(parse_partition_info(parted_output1, 'MB'), parted_dict1)
        self.assertEqual(parse_partition_info(parted_output2, 'MB'), parted_dict2)

    def test_partition_already_exists(self):
        set_module_args({
            'device': '/dev/sdb',
            'number': 1,
            'state': 'present',
        })
        with patch('ansible.modules.system.parted.get_device_info', return_value=parted_dict1):
            self.execute_module(changed=False)

    def test_create_new_partition(self):
        set_module_args({
            'device': '/dev/sdb',
            'number': 4,
            'state': 'present',
        })
        with patch('ansible.modules.system.parted.get_device_info', return_value=parted_dict1):
            self.execute_module(changed=True, script='unit KiB mkpart primary 0% 100%')

    def test_create_new_partition_1G(self):
        set_module_args({
            'device': '/dev/sdb',
            'number': 4,
            'state': 'present',
            'part_end': '1GiB',
        })
        with patch('ansible.modules.system.parted.get_device_info', return_value=parted_dict1):
            self.execute_module(changed=True, script='unit KiB mkpart primary 0% 1GiB')

    def test_remove_partition_number_1(self):
        set_module_args({
            'device': '/dev/sdb',
            'number': 1,
            'state': 'absent',
        })
        with patch('ansible.modules.system.parted.get_device_info', return_value=parted_dict1):
            self.execute_module(changed=True, script='rm 1')

    def test_change_flag(self):
        # Flags are set in a second run of parted().
        # Between the two runs, the partition dict is updated.
        # use checkmode here allow us to continue even if the dictionary is
        # not updated.
        set_module_args({
            'device': '/dev/sdb',
            'number': 3,
            'state': 'present',
            'flags': ['lvm', 'boot'],
            '_ansible_check_mode': True,
        })

        with patch('ansible.modules.system.parted.get_device_info', return_value=parted_dict1):
            self.parted.reset_mock()
            self.execute_module(changed=True)
            # When using multiple flags:
            # order of execution is non deterministic, because set() operations are used in
            # the current implementation.
            expected_calls_order1 = [call('unit KiB set 3 lvm on set 3 boot on ',
                                          '/dev/sdb', 'optimal')]
            expected_calls_order2 = [call('unit KiB set 3 boot on set 3 lvm on ',
                                          '/dev/sdb', 'optimal')]
            self.assertTrue(self.parted.mock_calls == expected_calls_order1 or
                            self.parted.mock_calls == expected_calls_order2)

    def test_create_new_primary_lvm_partition(self):
        # use check_mode, see previous test comment
        set_module_args({
            'device': '/dev/sdb',
            'number': 4,
            'flags': ["boot"],
            'state': 'present',
            'part_start': '257GiB',
            '_ansible_check_mode': True,
        })
        with patch('ansible.modules.system.parted.get_device_info', return_value=parted_dict1):
            self.execute_module(changed=True, script='unit KiB mkpart primary 257GiB 100% unit KiB set 4 boot on')

    def test_create_label_gpt(self):
        # Like previous test, current implementation use parted to create the partition and
        # then retrieve and update the dictionary. Use check_mode to force to continue even if
        # dictionary is not updated.
        set_module_args({
            'device': '/dev/sdb',
            'number': 1,
            'flags': ["lvm"],
            'label': 'gpt',
            'name': 'lvmpartition',
            'state': 'present',
            '_ansible_check_mode': True,
        })
        with patch('ansible.modules.system.parted.get_device_info', return_value=parted_dict2):
            self.execute_module(changed=True, script='unit KiB mklabel gpt mkpart primary 0% 100% unit KiB name 1 \'"lvmpartition"\' set 1 lvm on')
