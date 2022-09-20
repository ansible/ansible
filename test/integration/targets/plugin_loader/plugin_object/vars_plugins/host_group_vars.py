from ansible.plugins.vars import BaseVarsPlugin


class VarsModule(BaseVarsPlugin):
    REQUIRES_ENABLED = True

    def get_vars(self, loader, path, entities):
        if (
            self.ansible_name != 'host_group_vars' or
            self.ansible_aliases != ['host_group_vars'] or
            any(not self.matches_name([name]) for name in ['host_group_vars', 'ansible.legacy.host_group_vars']) or
            self.matches_name(['ansible.builtin.host_group_vars'])
        ):
            return {'failed': True}
        return {'legacy_var': True}
