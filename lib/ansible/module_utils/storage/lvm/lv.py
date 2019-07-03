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


def lvcreate(lv_name, vg_name, size):
    blockdev.lvm.lvcreate(vg_name, lv_name, size)

    return True


def lvremove(lv_name, vg_name):
    blockdev.lvm.lvremove(vg_name, lv_name)

    return True


def generate_lv_name(forbidden_names):
    index = 0
    lv_name = "lv_%02d" % index

    while lv_name in forbidden_names:
        index += 1
        lv_name = "lv_%02d" % index

    return lv_name


def run(params):

    # seed the result dict in the object
    result = dict(
        changed=False
    )

    # libblockdev initialization
    blockdev.switch_init_checks(False)
    if not blockdev.ensure_init():
        raise OSError("Failed to initialize libblockdev")

    lv_name = params["lv_name"]
    result["lv_name"] = lv_name

    # There might be multiple LVs with same name on different VGs
    if (params["vg_name"] is None and params["state"] == "absent"):
        # Nothing to do, exit normally
        return(result)

    try:
        vg = blockdev.lvm.vginfo(params["vg_name"])
    except blockdev.LVMError as e:
        if params["state"] == "absent":
            # VG does not exist, hence LV neither, our job is done
            return(result)
        else:
            raise OSError(e)

    lv_names = [x.lv_name for x in blockdev.lvm.lvs(vg.name)]

    size = vg.free

    if params["state"] == "present":

        if lv_name is None:
            # No LV name was given. Use existing LV, if exactly one is present.
            # If none is present, generate new LV name. If multiple LVs are
            # present, fail.
            # This behavior is to preserve idempotency when no LV name is specified.

            if len(lv_names) == 0:
                lv_name = generate_lv_name(lv_names)
            elif len(lv_names) == 1:
                # Nothing to do. This will skip to the end.
                lv_name = lv_names[0]
            else:
                raise ValueError("Multiple LVs %s present on given VG. "
                                 "Could not decide "
                                 "which LV to use." % lv_names)
            result["lv_name"] = lv_name

        # check if LV with the same name does not already exist
        if lv_name not in lv_names:

            # create LV
            try:
                result["changed"] += lvcreate(lv_name,
                                              params["vg_name"],
                                              size)
            except blockdev.LVMError as e:
                raise OSError("Could not create LVM LV: %s" % e)

    else:
        if lv_name in lv_names:
            # remove LV
            try:
                result["changed"] += lvremove(lv_name,
                                              params["vg_name"])
            except blockdev.LVMError as e:
                raise OSError("Could not remove LVM LV: %s" % e)

    return result
