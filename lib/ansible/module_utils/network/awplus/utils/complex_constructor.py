STATE = "state"
PRESENT = "present"
ABSENT = "absent"


def get_param_str(d, key):
    val = d.get(key)
    if val is True:
        return key.replace("_", "-")
    return val


def get_param(key, module, params):
    levels = key.split(".")
    if len(levels) == 1:
        return get_param_str(params, key)
    current = module.params
    for i, l in enumerate(levels):
        if i == len(levels) - 1:
            return get_param_str(current, levels[-1])
        current = current[l]


def construct_from_list(mapper_dict, module, params):
    mapper = mapper_dict[params[STATE]]
    cmd = ""
    for i, key in enumerate(mapper):
        cmd = cmd.strip()
        if i % 2 == 0:
            if key != "":
                cmd += " {}".format(key)
        else:
            val = get_param(key, module, params)
            if val is None:
                if key:
                    return None
                else:
                    continue
            elif val is False:
                continue
            elif val is True:
                cmd += " {}".format(key)
            else:
                cmd += " {}".format(val)
    return cmd


def _construct_commands(mapper_dict, module, params):
    commands = set()
    more_than_router = False

    for key, val in params.items():
        if val is None or mapper_dict is None:
            continue

        mapper = mapper_dict.get(key)
        if mapper is None:
            continue
        if key != "router":
            more_than_router = True
        result = None
        if isinstance(mapper, dict):
            if PRESENT in mapper:
                result = construct_from_list(mapper, module, val)
            else:
                commands.update(_construct_commands(mapper, module, val))
        elif callable(mapper):
            result = mapper(module)

        if result:
            commands.add(result.strip())

    if not commands and more_than_router:
        module.fail_json({"errors": ["No commands could be constructed."]})
    return commands


def construct_commands(module, key_to_command_map, first_map):
    commands = _construct_commands(key_to_command_map, module, module.params)
    first = first_map(module, commands)
    return first, commands


def arrange_commands(first, diff):
    commands = [first]

    for d in diff:
        commands.append(d)
    return commands


def get_commands(
    module, key_to_command_map, first_map, existing_first, existing
):
    constructed_ospf, constructed = construct_commands(
        module, key_to_command_map, first_map
    )

    intersection = constructed.intersection(existing)
    diff = constructed - existing

    dup_commands = []
    if len(intersection) == 0 and constructed_ospf == existing_first:
        dup_commands = [constructed_ospf]
    elif intersection:
        dup_commands = [i for i in intersection]
    if dup_commands:
        if module.check_mode:
            module.fail_json(
                {
                    "changed": False,
                    "msg": "The given commands already existed.",
                    "commands": dup_commands,
                }
            )

    if diff or constructed_ospf != existing_first:
        return arrange_commands(constructed_ospf, diff)
    return []
