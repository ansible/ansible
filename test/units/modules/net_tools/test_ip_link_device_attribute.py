# Copyright (c) 2019 George Shuklin
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import pytest
from units.compat import mock
from ansible.modules.net_tools import ip_link_device_attribute


IF1 = '2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP mode DEFAULT group default qlen 1000\\    link/ether 00:23:54:84:d1:7a brd ff:ff:ff:ff:ff:ff link-netnsid 0'  # noqa
IF1_data = {
    "address": '00:23:54:84:d1:7a',
    "alias": None,
    "arp": True,
    "broadcast": 'ff:ff:ff:ff:ff:ff',
    "group": 'default',
    "mtu": 1500,
    "multicast": True,
    "name": 'eth0',
    "promisc": False,
    "txqueuelen": 1000,
    "state": 'up'
}


IF2 = '6: veth3@veth2: <BROADCAST,NOARP,PROMISC,M-DOWN> mtu 8000 qdisc noop master ovs-system state DOWN mode DEFAULT group 42 qlen 1\\    link/ether 3e:bf:a6:f0:6c:fb brd 0a:0a:0a:0a:0a:0a\\    alias for_test'  # noqa
IF2_data = {
    "address": '3e:bf:a6:f0:6c:fb',
    "alias": 'for_test',
    "arp": False,
    "broadcast": '0a:0a:0a:0a:0a:0a',
    "group": '42',
    "mtu": 8000,
    "multicast": False,
    "name": 'veth3',
    "promisc": True,
    "txqueuelen": 1,
    "state": 'down'
}
IF3 = '118: vcan9: <NOARP> mtu 72 qdisc noop state DOWN mode DEFAULT group default qlen 1000\\    link/can \\    alias foo'  # noqa
IF3_data = {
    "address": None,
    "alias": 'foo',
    "arp": False,
    "broadcast": None,
    "group": 'default',
    "mtu": 72,
    "multicast": False,
    "name": 'vcan9',
    "promisc": False,
    "txqueuelen": 1000,
    "state": 'down'
}


@pytest.fixture(scope='function')
def eth0():
    '''Example of parsed interface'''
    return IF1_data


class FailJsonException(Exception):
    pass


@pytest.fixture(scope='function')
def module():
    module = mock.MagicMock()
    module.params = {}
    for knob in ip_link_device_attribute.Link.knob_cmds.keys():
        module.params[knob] = None
    for param in ip_link_device_attribute.Link.params_list:
        module.params[param] = None
    module.check_mode = False
    module.fail_json.side_effect = FailJsonException("fail_json was called")
    return module


@pytest.fixture(scope='function')
def Zlink():
    ''' Link class with mocked _exec'''
    with mock.patch.object(ip_link_device_attribute.Link, '_exec'):
        yield ip_link_device_attribute.Link


@pytest.fixture(scope='function')
def elink(module):
    ''' Link object with trivial initialization'''
    module.params["name"] = True
    link = ip_link_device_attribute.Link(module)
    return link


@pytest.mark.parametrize('input,output', [
    (
        IF1,
        {
            'name': 'eth0',
            'mtu': 1500,
            'group': 'default',
            'txqueuelen': 1000,
            'multicast': True,
            'state': 'up',
            'arp': True,
            'promisc': False,
            'address': '00:23:54:84:d1:7a',
            'broadcast': 'ff:ff:ff:ff:ff:ff',
            'alias': None
        }
    ),
    (
        IF2,
        IF2_data,
    ),
    (
        IF3,
        IF3_data,
    )
])
def test_parse_interface_good_cases(elink, input, output):
    assert elink._parse_interface(input) == output


@pytest.mark.parametrize("input,output", [
    ('\n', []),
    ('', []),
    (
        '\n'.join([IF1, IF2]),
        [
            IF1_data,
            IF2_data
        ]
    )
])
def test_get_interfaces_info_good_parsing(Zlink, module, input, output):
    Zlink._exec.return_value = input
    module.params['name'] = 'eth0'
    assert list(Zlink(module)._get_interfaces_info(None)) == output


def test_get_interfaces_info_check_calling_args_group(Zlink, module):
    module.params['group_id'] = 'test_group'
    link = Zlink(module)
    list(link._get_interfaces_info(None))
    link._exec.assert_called_once_with(
        None, ['ip', '-o', 'link', 'show', 'group', 'test_group'], False
    )


def test_get_interfaces_info_check_calling_args_name(Zlink, module):
    module.params['name'] = 'eth0'
    link = Zlink(module)
    list(link._get_interfaces_info(None))
    link._exec.assert_called_once_with(
        None, ['ip', '-o', 'link', 'show', 'dev', 'eth0'], False
    )


def test_is_changes_needed_for_interface_no_changes(eth0, module):
    module.params['name'] = 'eth0'
    link = ip_link_device_attribute.Link(module)
    assert link._is_changes_needed_for_interface(eth0) is False


@pytest.mark.parametrize("change_attr", [
    'address',
    'alias',
    'arp',
    'broadcast',
    'group',
    'mtu',
    'multicast',
    'promisc',
    'txqueuelen',
    'state'
])
def test_is_changes_needed_for_interface_one_param(eth0, module, change_attr):
    module.params['name'] = 'eth0'
    module.params[change_attr] = 'need_change'
    link = ip_link_device_attribute.Link(module)
    assert link._is_changes_needed_for_interface(eth0) is True


@pytest.mark.parametrize("change_attr", ['address', 'broadcast'])
def test_is_changes_needed_for_interface_no_l2(eth0, module, change_attr):
    module.params['name'] = 'eth0'
    eth0["address"] = None
    eth0["broadcast"] = None
    module.params[change_attr] = 'need_change'
    link = ip_link_device_attribute.Link(module)
    with pytest.raises(FailJsonException):
        link._is_changes_needed_for_interface(eth0)


@pytest.mark.parametrize('knob, knob_value, command', [
    ('state', 'up', 'ip link set dev eth0 up'),
    ('state', 'down', 'ip link set dev eth0 down'),
    ('mtu', 1500, 'ip link set dev eth0 mtu 1500'),
    ('arp', True, 'ip link set dev eth0 arp on'),
    ('arp', False, 'ip link set dev eth0 arp off'),
    ('multicast', False, 'ip link set dev eth0 multicast off'),
    ('multicast', True, 'ip link set dev eth0 multicast on'),
    ('promisc', True, 'ip link set dev eth0 promisc on'),
    ('promisc', False, 'ip link set dev eth0 promisc off'),
    ('broadcast', 'FA:FA:FA:FA:FA:FA', 'ip link set dev eth0 broadcast fa:fa:fa:fa:fa:fa'),  # noqa
    ('address', 'BB:BB:BB:BB:BB:BB', 'ip link set dev eth0 address bb:bb:bb:bb:bb:bb'),  # noqa
    ('group', 3, 'ip link set dev eth0 group 3'),
    ('group', 'bar', 'ip link set dev eth0 group bar'),
    ('alias', 'foobar', 'ip link set dev eth0 alias foobar'),
    ('txqueuelen', 2, 'ip link set dev eth0 txqueuelen 2'),
])
def test_apply_change_good(Zlink, module, knob, knob_value, command):
    module.params['name'] = 'eth0'
    module.params[knob] = knob_value
    link = Zlink(module)
    link._apply_changes()
    Zlink._exec.assert_called_once_with(None, command.split())


def test_apply_change_uses_group_id(Zlink, module):
    module.params['group_id'] = '42'
    module.params['mtu'] = 1500
    link = Zlink(module)
    link._apply_changes()
    command = 'ip link set group 42 mtu 1500'
    Zlink._exec.assert_called_once_with(None, command.split())


def test_apply_change_uses_namespace(Zlink, module):
    module.params['name'] = 'eth0'
    module.params['mtu'] = 1500
    module.params['namespace'] = 'test'
    link = Zlink(module)
    link._apply_changes()
    command = 'ip link set dev eth0 mtu 1500'
    Zlink._exec.assert_called_with('test', command.split())


@pytest.mark.parametrize('input, output', [
    ([], set()),
    ([IF1_data], set(['eth0'])),
    ([IF1_data, IF2_data], set(['eth0', 'veth3']))
])
def test_get_iface_set_good(Zlink, module, input, output):
    module.params['name'] = 'eth0'
    link = Zlink(module)
    with mock.patch.object(link, '_get_interfaces_info') as mock_info:
        mock_info.return_value = input
        assert link._get_iface_set('dosntmatter') == output


@pytest.mark.parametrize('src, dst, status', [
    (set([]), set(['eth0']), False),
    (set(['eth0']), set([]), True),
    (set(['eth0']), set(['eth1']), True),
])
def test_netns_need_to_move_good(Zlink, module, src, dst, status):
    module.params['name'] = 'eth0'
    module.params['netns'] = 'foo'
    link = Zlink(module)
    with mock.patch.object(link, '_get_iface_set') as mock_iface_set:
        mock_iface_set.side_effect = [src, dst]
        assert link._netns_need_to_move() is status


@pytest.mark.parametrize('src, dst', [
    (set([]), set([])),
    (set(['eth0']), set(['eth0'])),
])
def test_netns_need_to_move_bad(Zlink, module, src, dst):
    module.params['name'] = 'eth0'
    module.params['netns'] = 'foo'
    link = Zlink(module)
    with mock.patch.object(link, '_get_iface_set') as mock_iface_set:
        mock_iface_set.side_effect = [src, dst]
        with pytest.raises(FailJsonException):
            raise Exception(link._netns_need_to_move())
