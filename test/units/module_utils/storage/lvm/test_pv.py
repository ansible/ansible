import pytest
import sys
from mock import Mock

# We don't need to import gi and libblockdev, all calls can be mocked.
# This bypasses the imports
sys.modules['gi'] = Mock()
sys.modules['gi.repository'] = Mock()

from ansible.module_utils.storage.lvm import pv


PVCREATE_DATA = (('/dev/vdb', '/dev/vda', True),
                 ('/dev/vdb', '/dev/vdb', False))

PVREMOVE_DATA = (('/dev/vdb', '/dev/vda', False),
                 ('/dev/vdb', '/dev/vdb', True))

RUN_DATA = (('present', 'create'),
            ('absent', 'remove'))


@pytest.mark.parametrize("existing_device, device, run_create",
                         ((d[0], d[1], d[2])
                          for d in PVCREATE_DATA))
def test_pvcreate(existing_device, device, run_create, monkeypatch):

    class Dummy(object):
        pv_name = existing_device

    mock_pvs = Mock(return_value=[Dummy])
    mock_pvcreate = Mock()

    monkeypatch.setattr(pv.blockdev.lvm, "pvs", mock_pvs)

    monkeypatch.setattr(pv.blockdev.lvm, "pvcreate", mock_pvcreate)

    pv.pvcreate([device])

    if run_create:
        mock_pvcreate.assert_called_with(device)
    else:
        mock_pvcreate.assert_not_called()


@pytest.mark.parametrize("existing_device, device, run_remove",
                         ((d[0], d[1], d[2])
                          for d in PVREMOVE_DATA))
def test_pvremove(existing_device, device, run_remove, monkeypatch):

    class Dummy(object):
        pv_name = existing_device

    mock_pvs = Mock(return_value=[Dummy])
    mock_pvremove = Mock()

    monkeypatch.setattr(pv.blockdev.lvm, "pvs", mock_pvs)

    monkeypatch.setattr(pv.blockdev.lvm, "pvremove", mock_pvremove)

    pv.pvremove([device])

    if run_remove:
        mock_pvremove.assert_called_with(device)
    else:
        mock_pvremove.assert_not_called()


@pytest.mark.parametrize("state, expected_action",
                         ((d[0], d[1])
                          for d in RUN_DATA))
def test_run(state, expected_action, monkeypatch):
    # This test fakes presence of lvm devices on the system using mock.
    # This is done by mocking all libblockdev calls.
    # We just need to make sure that the calls were (not) made.

    class Dummy(object):
        pv_name = '/dev/vdb'

    mock_pvcreate = Mock(return_value=True)
    mock_pvremove = Mock(return_value=True)

    monkeypatch.setattr(pv.blockdev, "switch_init_checks", lambda x: None)
    monkeypatch.setattr(pv.blockdev, "ensure_init", lambda: True)
    monkeypatch.setattr(pv, "pvcreate", mock_pvcreate)
    monkeypatch.setattr(pv, "pvremove", mock_pvremove)

    pv.run({'state': state, 'devices': ['/dev/vdb']})

    if expected_action == "create":
        mock_pvcreate.assert_called_with(['/dev/vdb'])
    elif expected_action == "remove":
        mock_pvremove.assert_called_with(['/dev/vdb'])
    else:
        mock_pvcreate.assert_not_called()
        mock_pvremove.assert_not_called()
