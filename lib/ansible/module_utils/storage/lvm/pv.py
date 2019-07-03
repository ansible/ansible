# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

HAS_GI = True
try:
    import gi
except ImportError:
    HAS_GI = False

if HAS_GI:
    gi.require_version("BlockDev", "2.0")
    from gi.repository import BlockDev as blockdev


def has_gi():
    return HAS_GI


def pvcreate(devices):
    ''' create Physical Volumes on given devices '''
    changed = False

    pv_names = [x.pv_name for x in blockdev.lvm.pvs()]

    for device in devices:
        if device not in pv_names:
            blockdev.lvm.pvcreate(device)
            changed = True

    return changed


def pvremove(devices):
    ''' remove Physical Volume from given devices '''
    changed = False

    pv_names = [x.pv_name for x in blockdev.lvm.pvs()]

    for device in devices:
        if device in pv_names:
            blockdev.lvm.pvremove(device)
            changed = True

    return changed


def run(params):
    # seed the result dict in the object
    result = dict(
        changed=False
    )

    # libblockdev initialization
    blockdev.switch_init_checks(False)
    if not blockdev.ensure_init():
        raise OSError("Failed to initialize libblockdev")

    if params["state"] == "present":
        # create PVs
        try:
            result["changed"] += pvcreate(params["devices"])
        except blockdev.LVMError as e:
            raise OSError("Could not create LVM PV: %s" % e)
    else:
        # remove PVs
        try:
            result["changed"] += pvremove(params["devices"])
        except blockdev.LVMError as e:
            raise OSError("Could not remove LVM PV: %s" % e)

    return result
