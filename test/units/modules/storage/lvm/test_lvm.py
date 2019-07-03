import pytest

from ansible.modules.storage.lvm import lvm

LVM_MODULE_DATA = (
    ({"devices": "/dev/vdb1", "state": 'present'}, True),)

EXCEPTION = 'exception'


def test_process_module_arguments():

    args = {}

    result = lvm.process_module_arguments(args)

    expected_result = {'devices': args.get('devices', None),
                       'state': args.get('state', None),
                       'pv': {'state': None},
                       'vg': {'state': None, 'name': None},
                       'lv': {'state': None, 'name': None}}

    assert result == expected_result


def test_pv_get_module_args():

    pv = lvm.PV_Layer()

    lvm.LVM_Layer.args['devices'] = ['device1', 'device2']
    pv.desired_state = 'present'

    result = pv.get_module_args('dummy')

    expected_result = {'state': 'present', 'devices': ['device1', 'device2']}

    assert result == expected_result


def test_vg_get_module_args():

    vg = lvm.VG_Layer()

    lvm.LVM_Layer.args['devices'] = ['device1', 'device2']
    lvm.LVM_Layer.args['vg'] = {'name': 'vg_name'}
    vg.desired_state = 'present'

    result = vg.get_module_args('dummy')

    expected_result = {'state': 'present', 'pvs': ['device1', 'device2'], 'name': 'vg_name'}

    assert result == expected_result


def test_lv_get_module_args():

    lv = lvm.LV_Layer()

    lvm.LVM_Layer.args['vg'] = {'name': 'vg_name'}
    lvm.LVM_Layer.args['lv'] = {'name': 'lv_name'}
    lv.desired_state = 'present'

    result = lv.get_module_args('dummy')

    expected_result = {'state': 'present', 'vg_name': 'vg_name', 'lv_name': 'lv_name'}

    assert result == expected_result


# state, pvstate, vgstate, lvstate, expected values list/EXCEPTION
DESIRED_STATES_DATA = (
    (None, None, None, [None, None, None]),
    (None, None, 'present', ['present', 'present', 'present']),
    (None, None, 'absent', [None, None, 'absent']),
    (None, 'present', None, ['present', 'present', None]),
    (None, 'present', 'present', ['present', 'present', 'present']),
    (None, 'present', 'absent', ['present', 'present', 'absent']),
    (None, 'absent', None, [None, 'absent', 'absent']),
    (None, 'absent', 'present', EXCEPTION),
    (None, 'absent', 'absent', [None, 'absent', 'absent']),

    ('present', None, None, ['present', None, None]),
    ('present', None, 'present', ['present', 'present', 'present']),
    ('present', None, 'absent', ['present', None, 'absent']),
    ('present', 'present', None, ['present', 'present', None]),
    ('present', 'present', 'present', ['present', 'present', 'present']),
    ('present', 'present', 'absent', ['present', 'present', 'absent']),
    ('present', 'absent', None, ['present', 'absent', 'absent']),
    ('present', 'absent', 'present', EXCEPTION),
    ('present', 'absent', 'absent', ['present', 'absent', 'absent']),

    ('absent', None, None, ['absent', 'absent', 'absent']),
    ('absent', None, 'present', EXCEPTION),
    ('absent', None, 'absent', ['absent', 'absent', 'absent']),
    ('absent', 'present', None, EXCEPTION),
    ('absent', 'present', 'present', EXCEPTION),
    ('absent', 'present', 'absent', EXCEPTION),
    ('absent', 'absent', None, ['absent', 'absent', 'absent']),
    ('absent', 'absent', 'present', EXCEPTION),
    ('absent', 'absent', 'absent', ['absent', 'absent', 'absent']))


@pytest.mark.parametrize("pvstate, vgstate, lvstate, expected_result",
                         ((d[0], d[1], d[2], d[3])
                          for d in DESIRED_STATES_DATA))
def test_resolve_desired_state(pvstate, vgstate, lvstate, expected_result):

    args = {'devices': None,
            'state': None,
            'pv': {'state': pvstate},
            'vg': {'state': vgstate, 'name': None},
            'lv': {'state': lvstate, 'name': None}}

    lvm.LVM_Layer.suggested_states = {}
    lvm.LVM_Layer.args = args

    layers = [
        lvm.PV_Layer(),
        lvm.VG_Layer(),
        lvm.LV_Layer()]

    try:
        for i in range(2):
            for layer in layers:
                layer.resolve_desired_state()
    except ValueError:
        assert expected_result == EXCEPTION
        return

    result = [x.desired_state for x in layers]

    assert result == expected_result
