        self._parent_groups_dict_cache = {}
        self._child_groups_dict_cache = {}
        self._child_groups_dict_cache = {}
        self._parent_groups_dict_cache = {}

    def get_child_groups_dict(self):

        if not self._child_groups_dict_cache:
            for (group_name, group) in iteritems(self.groups):
                self._child_groups_dict_cache[group_name] = [ g.name for g in group.child_groups ]

        return self._child_groups_dict_cache

    def get_parent_groups_dict(self):

        if not self._parent_groups_dict_cache:
            for (group_name, group) in iteritems(self.groups):
                self._parent_groups_dict_cache[group_name] = [ g.name for g in group.parent_groups ]

        return self._parent_groups_dict_cache
