from ansible.plugins.vars import BaseVarsPlugin


class VarsModule(BaseVarsPlugin):
    REQUIRES_WHITELIST = False

    def get_vars(self, loader, path, entities):
        return {}
