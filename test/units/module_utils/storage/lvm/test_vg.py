import pytest
import sys
from mock import Mock

# We don't need to import gi and libblockdev, all calls can be mocked.
# This bypasses the imports
sys.modules['gi'] = Mock()
sys.modules['gi.repository'] = Mock()

from ansible.module_utils.storage.lvm import vg


RUN_DATA = (('vg_00', 'present', 'create'),
            ('vg_existing', 'absent', 'remove'))


def test_generate_vg_name():
    name = vg.generate_vg_name(['vg_00', 'I was here. Fantomas', 'vg_01'])

    assert name == "vg_02"


@pytest.mark.parametrize("vgname, state, expected_action",
                         ((d[0], d[1], d[2])
                          for d in RUN_DATA))
def test_run(vgname, state, expected_action, monkeypatch):
    # This test fakes presence of lvm devices on the system using mock.
    # This is done by mocking all libblockdev calls.
    # We just need to make sure that the calls were made.

    class DummyPvs(object):
        pv_name = '/dev/vdb'

    class DummyVgs(object):
        name = 'vg_existing'
    mock_pvs = Mock(return_value=[DummyPvs])
    mock_vgs = Mock(return_value=[DummyVgs])
    mock_vgcreate = Mock(return_value=True)
    mock_vgremove = Mock(return_value=True)

    monkeypatch.setattr(vg.blockdev, "switch_init_checks", lambda x: None)
    monkeypatch.setattr(vg.blockdev, "ensure_init", lambda: True)
    monkeypatch.setattr(vg, "get_existing_vgs", lambda x: ['vg_existing'])

    monkeypatch.setattr(vg.blockdev.lvm, "pvs", mock_pvs)
    monkeypatch.setattr(vg.blockdev.lvm, "vgs", mock_vgs)

    monkeypatch.setattr(vg.blockdev.lvm, "vgcreate", mock_vgcreate)
    monkeypatch.setattr(vg.blockdev.lvm, "vgremove", mock_vgremove)

    vg.run({'name': vgname, 'state': state, 'pvs': ['/dev/vdb']})

    if expected_action == "create":
        mock_vgcreate.assert_called_with(vgname, ['/dev/vdb'])
    elif expected_action == "remove":
        mock_vgremove.assert_called_with(vgname)
    else:
        mock_vgcreate.assert_not_called()
        mock_vgremove.assert_not_called()
