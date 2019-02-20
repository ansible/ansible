# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
import mock
import libvirt


from ansible.modules.cloud.misc.virt_net import VirtNetwork


NET_XML = """
<network>
  <name>foo</name>
</network>
"""


class mocked_exception(libvirt.libvirtError):
    def __init__(self, code):
        self.err = [code]


def raise_network_exist(a):
    raise mocked_exception(libvirt.VIR_ERR_NETWORK_EXIST)


def test_virt_net_recreate():
    uri = 'test:///default'
    module = mock.MagicMock()
    virt_net = VirtNetwork(uri, module)
    virt_net.conn.create = raise_network_exist
    assert virt_net.create("default") is None


def test_virt_stop_ignore_inactive():
    uri = 'test:///default'
    module = mock.MagicMock()
    virt_net = VirtNetwork(uri, module)
    virt_net.conn.get_status = mock.Mock(return_value="inactive")
    virt_net.conn.destroy = mock.Mock()
    virt_net.stop("default")
    virt_net.conn.destroy.assert_not_called()


def test_virt_stop_active():
    uri = 'test:///default'
    module = mock.MagicMock()
    virt_net = VirtNetwork(uri, module)
    virt_net.conn.get_status = mock.Mock(return_value="active")
    virt_net.conn.destroy = mock.Mock()
    virt_net.stop("default")
    virt_net.conn.destroy.assert_called()
