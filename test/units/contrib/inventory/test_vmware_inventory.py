import json
import os
import pickle
import unittest
import sys
from nose.plugins.skip import SkipTest


try:
    from pyVmomi import vim, vmodl
except ImportError:
    raise SkipTest("test_vmware_inventory.py requires the python module 'pyVmomi'")

try:
    from vmware_inventory import VMWareInventory
except ImportError:
    raise SkipTest("test_vmware_inventory.py requires the python module 'vmware_inventory'")

# contrib's dirstruct doesn't contain __init__.py files
checkout_path = os.path.dirname(__file__)
checkout_path = checkout_path.replace('/test/units/contrib/inventory', '')
inventory_dir = os.path.join(checkout_path, 'contrib', 'inventory')
sys.path.append(os.path.abspath(inventory_dir))

# cleanup so that nose's path is not polluted with other inv scripts
sys.path.remove(os.path.abspath(inventory_dir))

BASICINVENTORY = {
    'all': {
        'hosts': ['foo', 'bar']
    },
    '_meta': {
        'hostvars': {
            'foo': {'hostname': 'foo'},
            'bar': {'hostname': 'bar'}
        }
    }
}


class FakeArgs(object):
    debug = False
    write_dumpfile = None
    load_dumpfile = None
    host = False
    list = True


class TestVMWareInventory(unittest.TestCase):

    def test_host_info_returns_single_host(self):
        vmw = VMWareInventory(load=False)
        vmw.inventory = BASICINVENTORY
        foo = vmw.get_host_info('foo')
        bar = vmw.get_host_info('bar')
        assert foo == {'hostname': 'foo'}
        assert bar == {'hostname': 'bar'}

    def test_show_returns_serializable_data(self):
        fakeargs = FakeArgs()
        vmw = VMWareInventory(load=False)
        vmw.args = fakeargs
        vmw.inventory = BASICINVENTORY
        showdata = vmw.show()
        serializable = False

        try:
            json.loads(showdata)
            serializable = True
        except:
            pass
        assert serializable
        # import epdb; epdb.st()

    def test_show_list_returns_serializable_data(self):
        fakeargs = FakeArgs()
        vmw = VMWareInventory(load=False)
        vmw.args = fakeargs
        vmw.args.list = True
        vmw.inventory = BASICINVENTORY
        showdata = vmw.show()
        serializable = False

        try:
            json.loads(showdata)
            serializable = True
        except:
            pass
        assert serializable
        # import epdb; epdb.st()

    def test_show_list_returns_all_data(self):
        fakeargs = FakeArgs()
        vmw = VMWareInventory(load=False)
        vmw.args = fakeargs
        vmw.args.list = True
        vmw.inventory = BASICINVENTORY
        showdata = vmw.show()
        expected = json.dumps(BASICINVENTORY, indent=2)
        assert showdata == expected

    def test_show_host_returns_serializable_data(self):
        fakeargs = FakeArgs()
        vmw = VMWareInventory(load=False)
        vmw.args = fakeargs
        vmw.args.host = 'foo'
        vmw.inventory = BASICINVENTORY
        showdata = vmw.show()
        serializable = False

        try:
            json.loads(showdata)
            serializable = True
        except:
            pass
        assert serializable
        # import epdb; epdb.st()

    def test_show_host_returns_just_host(self):
        fakeargs = FakeArgs()
        vmw = VMWareInventory(load=False)
        vmw.args = fakeargs
        vmw.args.list = False
        vmw.args.host = 'foo'
        vmw.inventory = BASICINVENTORY
        showdata = vmw.show()
        expected = BASICINVENTORY['_meta']['hostvars']['foo']
        expected = json.dumps(expected, indent=2)
        # import epdb; epdb.st()
        assert showdata == expected
