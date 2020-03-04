from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest
from ansible.modules.crypto import luks_device
from units.compat.mock import patch
from ansible.module_utils import basic


class DummyModule(object):
    # module to mock AnsibleModule class
    def __init__(self):
        self.params = dict()

    def fail_json(self, msg=""):
        raise ValueError(msg)

    def get_bin_path(self, command, dummy):
        return command


# ===== Handler & CryptHandler methods tests =====

def test_generate_luks_name(monkeypatch):
    module = DummyModule()
    monkeypatch.setattr(luks_device.Handler, "_run_command",
                        lambda x, y: [0, "UUID", ""])
    crypt = luks_device.CryptHandler(module)
    assert crypt.generate_luks_name("/dev/dummy") == "luks-UUID"


def test_get_container_name_by_device(monkeypatch):
    module = DummyModule()
    monkeypatch.setattr(luks_device.Handler, "_run_command",
                        lambda x, y: [0, "crypt container_name", ""])
    crypt = luks_device.CryptHandler(module)
    assert crypt.get_container_name_by_device("/dev/dummy") == "container_name"


def test_get_container_device_by_name(monkeypatch):
    module = DummyModule()
    monkeypatch.setattr(luks_device.Handler, "_run_command",
                        lambda x, y: [0, "device:  /dev/luksdevice", ""])
    crypt = luks_device.CryptHandler(module)
    assert crypt.get_container_device_by_name("dummy") == "/dev/luksdevice"


def test_run_luks_remove(monkeypatch):
    def run_command_check(self, command):
        # check that wipefs command is actually called
        assert command[0] == "wipefs"
        return [0, "", ""]

    module = DummyModule()
    monkeypatch.setattr(luks_device.CryptHandler,
                        "get_container_name_by_device",
                        lambda x, y: None)
    monkeypatch.setattr(luks_device.Handler,
                        "_run_command",
                        run_command_check)
    crypt = luks_device.CryptHandler(module)
    crypt.run_luks_remove("dummy")


# ===== ConditionsHandler methods data and tests =====

# device, key, passphrase, state, is_luks, label, expected
LUKS_CREATE_DATA = (
    ("dummy", "key", None, "present", False, None, True),
    (None, "key", None, "present", False, None, False),
    (None, "key", None, "present", False, "labelName", True),
    ("dummy", None, None, "present", False, None, False),
    ("dummy", "key", None, "absent", False, None, False),
    ("dummy", "key", None, "opened", True, None, False),
    ("dummy", "key", None, "closed", True, None, False),
    ("dummy", "key", None, "present", True, None, False),
    ("dummy", None, "foo", "present", False, None, True),
    (None, None, "bar", "present", False, None, False),
    (None, None, "baz", "present", False, "labelName", True),
    ("dummy", None, None, "present", False, None, False),
    ("dummy", None, "quz", "absent", False, None, False),
    ("dummy", None, "qux", "opened", True, None, False),
    ("dummy", None, "quux", "closed", True, None, False),
    ("dummy", None, "corge", "present", True, None, False))

# device, state, is_luks, expected
LUKS_REMOVE_DATA = (
    ("dummy", "absent", True, True),
    (None, "absent", True, False),
    ("dummy", "present", True, False),
    ("dummy", "absent", False, False))

# device, key, passphrase, state, name, name_by_dev, expected
LUKS_OPEN_DATA = (
    ("dummy", "key", None, "present", "name", None, False),
    ("dummy", "key", None, "absent", "name", None, False),
    ("dummy", "key", None, "closed", "name", None, False),
    ("dummy", "key", None, "opened", "name", None, True),
    (None, "key", None, "opened", "name", None, False),
    ("dummy", None, None, "opened", "name", None, False),
    ("dummy", "key", None, "opened", "name", "name", False),
    ("dummy", "key", None, "opened", "beer", "name", "exception"),
    ("dummy", None, "foo", "present", "name", None, False),
    ("dummy", None, "bar", "absent", "name", None, False),
    ("dummy", None, "baz", "closed", "name", None, False),
    ("dummy", None, "qux", "opened", "name", None, True),
    (None, None, "quux", "opened", "name", None, False),
    ("dummy", None, None, "opened", "name", None, False),
    ("dummy", None, "quuz", "opened", "name", "name", False),
    ("dummy", None, "corge", "opened", "beer", "name", "exception"))

# device, dev_by_name, name, name_by_dev, state, label, expected
LUKS_CLOSE_DATA = (
    ("dummy", "dummy", "name", "name", "present", None, False),
    ("dummy", "dummy", "name", "name", "absent", None, False),
    ("dummy", "dummy", "name", "name", "opened", None, False),
    ("dummy", "dummy", "name", "name", "closed", None, True),
    (None, "dummy", "name", "name", "closed", None, True),
    ("dummy", "dummy", None, "name", "closed", None, True),
    (None, "dummy", None, "name", "closed", None, False))

# device, key, passphrase, new_key, new_passphrase, state, label, expected
LUKS_ADD_KEY_DATA = (
    ("dummy", "key", None, "new_key", None, "present", None, True),
    (None, "key", None, "new_key", None, "present", "labelName", True),
    (None, "key", None, "new_key", None, "present", None, False),
    ("dummy", None, None, "new_key", None, "present", None, False),
    ("dummy", "key", None, None, None, "present", None, False),
    ("dummy", "key", None, "new_key", None, "absent", None, "exception"),
    ("dummy", None, "pass", "new_key", None, "present", None, True),
    (None, None, "pass", "new_key", None, "present", "labelName", True),
    ("dummy", "key", None, None, "new_pass", "present", None, True),
    (None, "key", None, None, "new_pass", "present", "labelName", True),
    (None, "key", None, None, "new_pass", "present", None, False),
    ("dummy", None, None, None, "new_pass", "present", None, False),
    ("dummy", "key", None, None, None, "present", None, False),
    ("dummy", "key", None, None, "new_pass", "absent", None, "exception"),
    ("dummy", None, "pass", None, "new_pass", "present", None, True),
    (None, None, "pass", None, "new_pass", "present", "labelName", True))

# device, remove_key, remove_passphrase, state, label, expected
LUKS_REMOVE_KEY_DATA = (
    ("dummy", "key", None, "present", None, True),
    (None, "key", None, "present", None, False),
    (None, "key", None, "present", "labelName", True),
    ("dummy", None, None, "present", None, False),
    ("dummy", "key", None, "absent", None, "exception"),
    ("dummy", None, "foo", "present", None, True),
    (None, None, "foo", "present", None, False),
    (None, None, "foo", "present", "labelName", True),
    ("dummy", None, None, "present", None, False),
    ("dummy", None, "foo", "absent", None, "exception"))


@pytest.mark.parametrize("device, keyfile, passphrase, state, is_luks, " +
                         "label, expected",
                         ((d[0], d[1], d[2], d[3], d[4], d[5], d[6])
                          for d in LUKS_CREATE_DATA))
def test_luks_create(device, keyfile, passphrase, state, is_luks, label,
                     expected, monkeypatch):
    module = DummyModule()

    module.params["device"] = device
    module.params["keyfile"] = keyfile
    module.params["passphrase"] = passphrase
    module.params["state"] = state
    module.params["label"] = label

    monkeypatch.setattr(luks_device.CryptHandler, "is_luks",
                        lambda x, y: is_luks)
    crypt = luks_device.CryptHandler(module)
    if device is None:
        monkeypatch.setattr(luks_device.Handler, "get_device_by_label",
                            lambda x, y: [0, "/dev/dummy", ""])
    try:
        conditions = luks_device.ConditionsHandler(module, crypt)
        assert conditions.luks_create() == expected
    except ValueError:
        assert expected == "exception"


@pytest.mark.parametrize("device, state, is_luks, expected",
                         ((d[0], d[1], d[2], d[3])
                          for d in LUKS_REMOVE_DATA))
def test_luks_remove(device, state, is_luks, expected, monkeypatch):
    module = DummyModule()

    module.params["device"] = device
    module.params["state"] = state

    monkeypatch.setattr(luks_device.CryptHandler, "is_luks",
                        lambda x, y: is_luks)
    crypt = luks_device.CryptHandler(module)
    try:
        conditions = luks_device.ConditionsHandler(module, crypt)
        assert conditions.luks_remove() == expected
    except ValueError:
        assert expected == "exception"


@pytest.mark.parametrize("device, keyfile, passphrase, state, name, "
                         "name_by_dev, expected",
                         ((d[0], d[1], d[2], d[3], d[4], d[5], d[6])
                          for d in LUKS_OPEN_DATA))
def test_luks_open(device, keyfile, passphrase, state, name, name_by_dev,
                   expected, monkeypatch):
    module = DummyModule()
    module.params["device"] = device
    module.params["keyfile"] = keyfile
    module.params["passphrase"] = passphrase
    module.params["state"] = state
    module.params["name"] = name

    monkeypatch.setattr(luks_device.CryptHandler,
                        "get_container_name_by_device",
                        lambda x, y: name_by_dev)
    monkeypatch.setattr(luks_device.CryptHandler,
                        "get_container_device_by_name",
                        lambda x, y: device)
    monkeypatch.setattr(luks_device.Handler, "_run_command",
                        lambda x, y: [0, device, ""])
    crypt = luks_device.CryptHandler(module)
    try:
        conditions = luks_device.ConditionsHandler(module, crypt)
        assert conditions.luks_open() == expected
    except ValueError:
        assert expected == "exception"


@pytest.mark.parametrize("device, dev_by_name, name, name_by_dev, "
                         "state, label, expected",
                         ((d[0], d[1], d[2], d[3], d[4], d[5], d[6])
                          for d in LUKS_CLOSE_DATA))
def test_luks_close(device, dev_by_name, name, name_by_dev, state,
                    label, expected, monkeypatch):
    module = DummyModule()
    module.params["device"] = device
    module.params["name"] = name
    module.params["state"] = state
    module.params["label"] = label

    monkeypatch.setattr(luks_device.CryptHandler,
                        "get_container_name_by_device",
                        lambda x, y: name_by_dev)
    monkeypatch.setattr(luks_device.CryptHandler,
                        "get_container_device_by_name",
                        lambda x, y: dev_by_name)
    crypt = luks_device.CryptHandler(module)
    try:
        conditions = luks_device.ConditionsHandler(module, crypt)
        assert conditions.luks_close() == expected
    except ValueError:
        assert expected == "exception"


@pytest.mark.parametrize("device, keyfile, passphrase, new_keyfile, " +
                         "new_passphrase, state, label, expected",
                         ((d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7])
                          for d in LUKS_ADD_KEY_DATA))
def test_luks_add_key(device, keyfile, passphrase, new_keyfile, new_passphrase,
                      state, label, expected, monkeypatch):
    module = DummyModule()
    module.params["device"] = device
    module.params["keyfile"] = keyfile
    module.params["passphrase"] = passphrase
    module.params["new_keyfile"] = new_keyfile
    module.params["new_passphrase"] = new_passphrase
    module.params["state"] = state
    module.params["label"] = label

    monkeypatch.setattr(luks_device.Handler, "get_device_by_label",
                        lambda x, y: [0, "/dev/dummy", ""])

    try:
        conditions = luks_device.ConditionsHandler(module, module)
        assert conditions.luks_add_key() == expected
    except ValueError:
        assert expected == "exception"


@pytest.mark.parametrize("device, remove_keyfile, remove_passphrase, state, " +
                         "label, expected",
                         ((d[0], d[1], d[2], d[3], d[4], d[5])
                          for d in LUKS_REMOVE_KEY_DATA))
def test_luks_remove_key(device, remove_keyfile, remove_passphrase, state,
                         label, expected, monkeypatch):

    module = DummyModule()
    module.params["device"] = device
    module.params["remove_keyfile"] = remove_keyfile
    module.params["remove_passphrase"] = remove_passphrase
    module.params["state"] = state
    module.params["label"] = label

    monkeypatch.setattr(luks_device.Handler, "get_device_by_label",
                        lambda x, y: [0, "/dev/dummy", ""])
    monkeypatch.setattr(luks_device.Handler, "_run_command",
                        lambda x, y: [0, device, ""])

    crypt = luks_device.CryptHandler(module)
    try:
        conditions = luks_device.ConditionsHandler(module, crypt)
        assert conditions.luks_remove_key() == expected
    except ValueError:
        assert expected == "exception"
