# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
import pytest

from ansible.modules.cloud.misc import virt_net

from units.compat import mock


virt_net.libvirt = None
virt_net.HAS_VIRT = True


class DummyNetwork():
    def __init__(self, name, isActive=True):
        self._name = name
        self._isActive = isActive

    def name(self):
        return self._name

    def isActive(self):
        return self._isActive


class DummyLibvirtConn():
    def __init__(self):
        self._network = [
            DummyNetwork("inactive_net", isActive=False),
            DummyNetwork("active_net", isActive=True)]

    def listNetworks(self):
        return [i.name() for i in self._network]

    def networkLookupByName(self, name):
        for i in self._network:
            if i.name() == name:
                return i

    def listDefinedNetworks(self):
        return []


class DummyLibvirt():
    VIR_ERR_NETWORK_EXIST = 'VIR_ERR_NETWORK_EXIST'

    @classmethod
    def open(cls, uri):
        return DummyLibvirtConn()

    class libvirtError(Exception):
        def __init__(self):
            self.error_code

        def get_error_code(self):
            return self.error_code


@pytest.fixture
def dummy_libvirt(monkeypatch):
    monkeypatch.setattr(virt_net, 'libvirt', DummyLibvirt)
    return DummyLibvirt


@pytest.fixture
def virt_net_obj(dummy_libvirt):
    return virt_net.VirtNetwork('qemu:///nowhere', mock.MagicMock())
