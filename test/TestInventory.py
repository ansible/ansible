import os
import unittest

from ansible.inventory import Inventory
from ansible.runner import Runner

class TestInventory(unittest.TestCase):

    def setUp(self):
        self.cwd = os.getcwd()
        self.test_dir = os.path.join(self.cwd, 'test')

        self.inventory_file = os.path.join(self.test_dir, 'simple_hosts')
        self.inventory_script = os.path.join(self.test_dir, 'inventory_api.py')
        self.inventory_yaml = os.path.join(self.test_dir, 'yaml_hosts')

        os.chmod(self.inventory_script, 0755)

    def tearDown(self):
        os.chmod(self.inventory_script, 0644)

    ### Simple inventory format tests

    def simple_inventory(self):
        return Inventory( self.inventory_file )

    def script_inventory(self):
        return Inventory( self.inventory_script )

    def yaml_inventory(self):
        return Inventory( self.inventory_yaml )

    def test_simple(self):
        inventory = self.simple_inventory()
        hosts = inventory.list_hosts()

        expected_hosts=['jupiter', 'saturn', 'zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']
        assert hosts == expected_hosts

    def test_simple_all(self):
        inventory = self.simple_inventory()
        hosts = inventory.list_hosts('all')

        expected_hosts=['jupiter', 'saturn', 'zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']
        assert hosts == expected_hosts

    def test_simple_norse(self):
        inventory = self.simple_inventory()
        hosts = inventory.list_hosts("norse")

        expected_hosts=['thor', 'odin', 'loki']
        assert hosts == expected_hosts

    def test_simple_ungrouped(self):
        inventory = self.simple_inventory()
        hosts = inventory.list_hosts("ungrouped")

        expected_hosts=['jupiter', 'saturn']
        assert hosts == expected_hosts

    def test_simple_combined(self):
        inventory = self.simple_inventory()
        hosts = inventory.list_hosts("norse:greek")

        expected_hosts=['zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']
        assert hosts == expected_hosts

    def test_simple_restrict(self):
        inventory = self.simple_inventory()

        restricted_hosts = ['hera', 'poseidon', 'thor']
        expected_hosts=['zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']

        inventory.restrict_to(restricted_hosts)
        hosts = inventory.list_hosts("norse:greek")

        assert hosts == restricted_hosts

        inventory.lift_restriction()
        hosts = inventory.list_hosts("norse:greek")

        assert hosts == expected_hosts

    def test_simple_vars(self):
        inventory = self.simple_inventory()
        vars = inventory.get_variables('thor')

        assert vars == {'group_names': ['norse']}

    def test_simple_port(self):
        inventory = self.simple_inventory()
        vars = inventory.get_variables('hera')

        assert vars == {'ansible_ssh_port': 3000, 'group_names': ['greek']}

    ### Inventory API tests

    def test_script(self):
        inventory = self.script_inventory()
        hosts = inventory.list_hosts()

        expected_hosts=['jupiter', 'saturn', 'zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']

        print "Expected: %s"%(expected_hosts)
        print "Got     : %s"%(hosts)
        assert sorted(hosts) == sorted(expected_hosts)

    def test_script_all(self):
        inventory = self.script_inventory()
        hosts = inventory.list_hosts('all')

        expected_hosts=['jupiter', 'saturn', 'zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']
        assert sorted(hosts) == sorted(expected_hosts)

    def test_script_norse(self):
        inventory = self.script_inventory()
        hosts = inventory.list_hosts("norse")

        expected_hosts=['thor', 'odin', 'loki']
        assert sorted(hosts) == sorted(expected_hosts)

    def test_script_combined(self):
        inventory = self.script_inventory()
        hosts = inventory.list_hosts("norse:greek")

        expected_hosts=['zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']
        assert sorted(hosts) == sorted(expected_hosts)

    def test_script_restrict(self):
        inventory = self.script_inventory()

        restricted_hosts = ['hera', 'poseidon', 'thor']
        expected_hosts=['zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']

        inventory.restrict_to(restricted_hosts)
        hosts = inventory.list_hosts("norse:greek")

        assert sorted(hosts) == sorted(restricted_hosts)

        inventory.lift_restriction()
        hosts = inventory.list_hosts("norse:greek")

        assert sorted(hosts) == sorted(expected_hosts)

    def test_script_vars(self):
        inventory = self.script_inventory()
        vars = inventory.get_variables('thor')

        assert vars == {"hammer":True, 'group_names': ['norse']}

    ### Tests for yaml inventory file

    def test_yaml(self):
        inventory = self.yaml_inventory()
        hosts = inventory.list_hosts()
        print hosts
        expected_hosts=['jupiter', 'saturn', 'zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']
        assert hosts == expected_hosts

    def test_yaml_all(self):
        inventory = self.yaml_inventory()
        hosts = inventory.list_hosts('all')

        expected_hosts=['jupiter', 'saturn', 'zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']
        assert hosts == expected_hosts

    def test_yaml_norse(self):
        inventory = self.yaml_inventory()
        hosts = inventory.list_hosts("norse")

        expected_hosts=['thor', 'odin', 'loki']
        assert hosts == expected_hosts

    def test_simple_ungrouped(self):
        inventory = self.yaml_inventory()
        hosts = inventory.list_hosts("ungrouped")

        expected_hosts=['jupiter']
        assert hosts == expected_hosts

    def test_yaml_combined(self):
        inventory = self.yaml_inventory()
        hosts = inventory.list_hosts("norse:greek")

        expected_hosts=['zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']
        assert hosts == expected_hosts

    def test_yaml_restrict(self):
        inventory = self.yaml_inventory()

        restricted_hosts = ['hera', 'poseidon', 'thor']
        expected_hosts=['zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']

        inventory.restrict_to(restricted_hosts)
        hosts = inventory.list_hosts("norse:greek")

        assert hosts == restricted_hosts

        inventory.lift_restriction()
        hosts = inventory.list_hosts("norse:greek")

        assert hosts == expected_hosts

    def test_yaml_vars(self):
        inventory = self.yaml_inventory()
        vars = inventory.get_variables('thor')

        assert vars == {"hammer":True, 'group_names': ['norse']}

    def test_yaml_change_vars(self):
        inventory = self.yaml_inventory()
        vars = inventory.get_variables('thor')

        vars["hammer"] = False

        vars = inventory.get_variables('thor')
        assert vars == {"hammer":True, 'group_names': ['norse']}

    def test_yaml_host_vars(self):
        inventory = self.yaml_inventory()
        vars = inventory.get_variables('saturn')

        assert vars == {"moon":"titan",
                        "moon2":"enceladus",
                        'group_names': ['multiple']}

    def test_yaml_port(self):
        inventory = self.yaml_inventory()
        vars = inventory.get_variables('hera')

        assert vars == {'ansible_ssh_port': 3000,
                        'ntp_server': 'olympus.example.com',
                        'group_names': ['greek']}

    def test_yaml_multiple_groups(self):
        inventory = self.yaml_inventory()
        vars = inventory.get_variables('odin')

        assert 'group_names' in vars
        assert sorted(vars['group_names']) == [ 'norse', 'ruler' ]

    ### Test Runner class method

    def test_class_method(self):
        hosts, groups = Runner.parse_hosts(self.inventory_file)

        expected_hosts = ['jupiter', 'saturn', 'zeus', 'hera', 'poseidon', 'thor', 'odin', 'loki']
        assert hosts == expected_hosts

        expected_groups= {
            'ungrouped': ['jupiter', 'saturn'],
            'greek': ['zeus', 'hera', 'poseidon'],
            'norse': ['thor', 'odin', 'loki']
        }
        assert groups == expected_groups

    def test_class_override(self):
        override_hosts = ['thor', 'odin']
        hosts, groups = Runner.parse_hosts(self.inventory_file, override_hosts)

        assert hosts == override_hosts

        assert groups == { 'ungrouped': override_hosts }
