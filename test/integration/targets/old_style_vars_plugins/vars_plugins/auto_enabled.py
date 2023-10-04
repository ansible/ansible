from __future__ import annotations

from ansible.plugins.vars import BaseVarsPlugin


class VarsModule(BaseVarsPlugin):
    REQUIRES_ENABLED = False

    def get_vars(self, loader, path, entities):
        return {'explicitly_auto_enabled': True}
