# Copyright: (c) 2018, Hewlett Packard Enterprise Development LP
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from ansible.module_utils import basic


def convert_to_binary_multiple(size_with_unit):
    if size_with_unit is None:
        return -1
    valid_units = ['MiB', 'GiB', 'TiB']
    valid_unit = False
    for unit in valid_units:
        if size_with_unit.strip().endswith(unit):
            valid_unit = True
            size = size_with_unit.split(unit)[0]
            if float(size) < 0:
                return -1
    if not valid_unit:
        raise ValueError("%s does not have a valid unit. The unit must be one of %s" % (size_with_unit, valid_units))

    size = size_with_unit.replace(" ", "").split('iB')[0]
    size_kib = basic.human_to_bytes(size)
    return int(size_kib / (1024 * 1024))


storage_system_spec = {
    "storage_system_ip": {
        "required": True,
        "type": "str"
    },
    "storage_system_username": {
        "required": True,
        "type": "str",
        "no_log": True
    },
    "storage_system_password": {
        "required": True,
        "type": "str",
        "no_log": True
    },
    "secure": {
        "type": "bool",
        "default": False
    }
}


def cpg_argument_spec():
    spec = {
        "state": {
            "required": True,
            "choices": ['present', 'absent'],
            "type": 'str'
        },
        "cpg_name": {
            "required": True,
            "type": "str"
        },
        "domain": {
            "type": "str"
        },
        "growth_increment": {
            "type": "str",
        },
        "growth_limit": {
            "type": "str",
        },
        "growth_warning": {
            "type": "str",
        },
        "raid_type": {
            "required": False,
            "type": "str",
            "choices": ['R0', 'R1', 'R5', 'R6']
        },
        "set_size": {
            "required": False,
            "type": "int"
        },
        "high_availability": {
            "type": "str",
            "choices": ['PORT', 'CAGE', 'MAG']
        },
        "disk_type": {
            "type": "str",
            "choices": ['FC', 'NL', 'SSD']
        }
    }
    spec.update(storage_system_spec)
    return spec
