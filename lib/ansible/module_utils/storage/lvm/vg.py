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


def generate_vg_name(forbidden_names):
    ''' Automatically generates a name for a VG (e.g: 'vg_05'). Avoids using
        any name in forbidden_names.
    '''

    index = 0
    vg_name = "vg_%02d" % index

    while vg_name in forbidden_names:
        index += 1
        vg_name = "vg_%02d" % index

    return vg_name


def get_existing_vgs(pvs):
    ''' return list of existing Volume Groups (VGs)
        located on given Physical Volumes (PVs) list
    '''

    existing_pvs = [pv.pv_name for pv in blockdev.lvm.pvs()]
    existing_vgs = []
    for pv in pvs:
        if pv not in existing_pvs:
            continue
        existing_vg = blockdev.lvm.pvinfo(pv).vg_name
        if existing_vg is not None:
            existing_vgs.append(existing_vg)
    return existing_vgs


def run(params):
    # seed the result dict in the object
    result = dict(
        changed=False,
        vg_name=""
    )

    # libblockdev initialization
    blockdev.switch_init_checks(False)
    if not blockdev.ensure_init():
        raise OSError("Failed to initialize libblockdev")

    existing_pvs = [pv.pv_name for pv in blockdev.lvm.pvs()]

    vg_name = params["name"]
    result["vg_name"] = vg_name

    vg_names = [x.name for x in blockdev.lvm.vgs()]
    if params["state"] == "present":
        # create VG if it isn't present on the system

        # check if all required arguments are present
        if params["pvs"] is None:
            raise ValueError("LVM VG creation requires 'pvs' "
                             "option to be specified")

        if not(set(params["pvs"]) <= set(existing_pvs)):
            # given pvs have to be subset of all existing pvs -
            # alas they are not
            raise ValueError("LVM VG creation requires all "
                             "given 'pvs' to exist")

        if vg_name is None:
            # No VG name was given. Use existing VG, if exactly one is present.
            # If none is present, generate new VG name. If multiple VGs are
            # present, fail.
            # This behavior is to preserve idempotency when no VG name is specified.

            existing_vgs = get_existing_vgs(params["pvs"])

            if len(existing_vgs) == 0:
                vg_name = generate_vg_name(vg_names)
            elif len(existing_vgs) == 1:
                # Nothing to do. This will skip to the end.
                vg_name = existing_vgs[0]
            else:
                raise OSError("Multiple VGs %s present on given PVs. "
                              "Could not decide "
                              "which VG to use." % existing_vgs)

            result["vg_name"] = vg_name

        # check if VG with the same name does not already exist
        if vg_name not in vg_names:
            # create VG
            try:
                result["changed"] += blockdev.lvm.vgcreate(vg_name,
                                                           params["pvs"])
            except blockdev.LVMError as e:
                raise OSError("Could not create LVM VG: %s" % e)
    else:
        # remove VG if it is present on the system

        if vg_name is None:
            # remove any VG present on pvs
            existing_vgs = get_existing_vgs(params["pvs"])
            for vg in existing_vgs:
                try:
                    result["changed"] += blockdev.lvm.vgremove(vg)
                except blockdev.LVMError as e:
                    raise OSError("Could not remove LVM VG: %s" % e)

        elif vg_name in vg_names:
            # remove given VG
            try:
                result["changed"] += blockdev.lvm.vgremove(vg_name)
            except blockdev.LVMError as e:
                raise OSError("Could not remove LVM VG: %s" % e)

    return result
