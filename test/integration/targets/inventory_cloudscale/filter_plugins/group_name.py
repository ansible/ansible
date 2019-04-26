from ansible.inventory.group import to_safe_group_name


def safe_group_name(name):
    return to_safe_group_name(name)


class FilterModule(object):
    filter_map = {
        'safe_group_name': safe_group_name
    }

    def filters(self):
        return self.filter_map
