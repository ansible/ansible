import json
import os
import pytest
import sys

BASIC_INVENTORY = {
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


@pytest.fixture
def vmware_inventory():
    inventory_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'contrib', 'inventory'))

    sys.path.append(inventory_dir)

    try:
        import vmware_inventory
    except BaseException as ex:
        pytest.skip(ex)
    finally:
        sys.path.remove(inventory_dir)

    return vmware_inventory


def test_host_info_returns_single_host(vmware_inventory):
    vmw = vmware_inventory.VMWareInventory(load=False)
    vmw.inventory = BASIC_INVENTORY
    foo = vmw.get_host_info('foo')
    bar = vmw.get_host_info('bar')
    assert foo == {'hostname': 'foo'}
    assert bar == {'hostname': 'bar'}


def test_show_returns_serializable_data(vmware_inventory):
    fakeargs = FakeArgs()
    vmw = vmware_inventory.VMWareInventory(load=False)
    vmw.args = fakeargs
    vmw.inventory = BASIC_INVENTORY
    showdata = vmw.show()
    json.loads(showdata)


def test_show_list_returns_serializable_data(vmware_inventory):
    fakeargs = FakeArgs()
    vmw = vmware_inventory.VMWareInventory(load=False)
    vmw.args = fakeargs
    vmw.args.list = True
    vmw.inventory = BASIC_INVENTORY
    showdata = vmw.show()
    json.loads(showdata)


def test_show_list_returns_all_data(vmware_inventory):
    fakeargs = FakeArgs()
    vmw = vmware_inventory.VMWareInventory(load=False)
    vmw.args = fakeargs
    vmw.args.list = True
    vmw.inventory = BASIC_INVENTORY
    showdata = vmw.show()
    expected = json.dumps(BASIC_INVENTORY, indent=2)
    assert showdata == expected


def test_show_host_returns_serializable_data(vmware_inventory):
    fakeargs = FakeArgs()
    vmw = vmware_inventory.VMWareInventory(load=False)
    vmw.args = fakeargs
    vmw.args.host = 'foo'
    vmw.inventory = BASIC_INVENTORY
    showdata = vmw.show()
    json.loads(showdata)


def test_show_host_returns_just_host(vmware_inventory):
    fakeargs = FakeArgs()
    vmw = vmware_inventory.VMWareInventory(load=False)
    vmw.args = fakeargs
    vmw.args.list = False
    vmw.args.host = 'foo'
    vmw.inventory = BASIC_INVENTORY
    showdata = vmw.show()
    expected = BASIC_INVENTORY['_meta']['hostvars']['foo']
    expected = json.dumps(expected, indent=2)
    assert showdata == expected
