import os
import unittest

from ansible.inventory import Inventory

class TestInventory(unittest.TestCase):

    def setUp(self):
        self.cwd = os.getcwd()
        self.test_dir = os.path.join(self.cwd, 'test')

        self.inventory_file = os.path.join(self.test_dir, 'simple_hosts')
        self.inventory_script = os.path.join(self.test_dir, 'inventory_api.py')

        os.chmod(self.inventory_script, 0755)

    def tearDown(self):
        os.chmod(self.inventory_script, 0644)

    ### Simple inventory format tests

    def simple_inventory(self):
        return Inventory( self.inventory_file )

    def script_inventory(self):
        return Inventory( self.inventory_script )

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

        assert vars == {}

    def test_simple_extra_vars(self):
        inventory = self.simple_inventory()
        vars = inventory.get_variables('thor', 'a=5')

        assert vars == {}

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

        assert vars == {"hammer":True}

    def test_script_extra_vars(self):
        inventory = self.script_inventory()
        vars = inventory.get_variables('thor', 'simple=yes')

        assert vars == {"hammer":True, "simple": "yes"}