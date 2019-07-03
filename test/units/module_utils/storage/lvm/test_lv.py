import pytest
import sys
from mock import Mock

# We don't need to import gi and libblockdev, all calls can be mocked.
# This bypasses the imports
sys.modules['gi'] = Mock()
sys.modules['gi.repository'] = Mock()

from ansible.module_utils.storage.lvm import lv

RUN_DATA = (('vg_00', None, 'present', ['lv_01', 'lv_00'], 'exception'),
            ('vg_00', None, 'present', ['lv_00'], 'nothing'),
            ('vg_00', None, 'present', [], 'create'),
            ('vg_00', 'lv_00', 'absent', ['lv_00'], 'remove'),)


def test_generate_lv_name():
    name = lv.generate_lv_name(['lv_00', 'I was here. Fantomas', 'lv_01'])

    assert name == "lv_02"


@pytest.mark.parametrize("vgname, lvname, state, existing_lvs, expected_action",
                         ((d[0], d[1], d[2], d[3], d[4])
                          for d in RUN_DATA))
def test_run(vgname, lvname, state, existing_lvs, expected_action, monkeypatch):
    # This test fakes presence of lvm devices on the system using mock.
    # This is done by mocking all libblockdev calls.
    # We just need to make sure that the calls were (not) made.

    class DummyLv(object):
        def __init__(self, lvname):
            self.lv_name = lvname

    class DummyVg(object):
        name = 'vg_00'
        free = '50MiB'

    mock_existing_lvs = Mock(return_value=[DummyLv(x) for x in existing_lvs])

    mock_vg = Mock(return_value=DummyVg)

    mock_lvcreate = Mock(return_value=True)
    mock_lvremove = Mock(return_value=True)

    monkeypatch.setattr(lv.blockdev.lvm, "vginfo", mock_vg)

    monkeypatch.setattr(lv.blockdev, "switch_init_checks", lambda x: None)
    monkeypatch.setattr(lv.blockdev, "ensure_init", lambda: True)

    monkeypatch.setattr(lv.blockdev.lvm, "lvs", mock_existing_lvs)

    monkeypatch.setattr(lv, "lvcreate", mock_lvcreate)
    monkeypatch.setattr(lv, "lvremove", mock_lvremove)

    try:
        lv.run({"vg_name": vgname, "lv_name": lvname, "state": state})
    except ValueError:
        assert expected_action == "exception"

    if expected_action == "create":
        if lvname is None:
            lvname = lv.generate_lv_name(existing_lvs)
        mock_lvcreate.assert_called_with(lvname, vgname, DummyVg.free)

    elif expected_action == "remove":
        mock_lvremove.assert_called_with(lvname, vgname)

    elif expected_action == "nothing":
        mock_lvcreate.assert_not_called()
        mock_lvremove.assert_not_called()
