# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from units.compat import mock


def test_virt_net_create_already_active(virt_net_obj, dummy_libvirt):
    virt_net_obj.conn.create = mock.Mock()
    assert virt_net_obj.create("active_net") is None
    virt_net_obj.conn.create.assert_not_called()


def test_virt_net_recreate(virt_net_obj, dummy_libvirt):
    virt_net_obj.conn.create = mock.Mock()
    dummy_libvirt.libvirtError.error_code = 'VIR_ERR_NETWORK_EXIST'
    virt_net_obj.conn.create.side_effect = dummy_libvirt.libvirtError
    assert virt_net_obj.create("active_net") is None


def test_virt_stop_ignore_inactive(virt_net_obj):
    virt_net_obj.conn.destroy = mock.Mock()
    virt_net_obj.stop('inactive_net')
    virt_net_obj.conn.destroy.assert_not_called()


def test_virt_stop_active(virt_net_obj, monkeypatch):
    virt_net_obj.conn.destroy = mock.Mock()
    virt_net_obj.stop('active_net')
    virt_net_obj.conn.destroy.assert_called_with('active_net')
