# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.plugins.vars import BaseVarsPlugin


class VarsModule(BaseVarsPlugin):
    def get_vars(self, loader, path, entities):
        config_aliases = ['testns.testcoll.test_vars', 'testns.testcoll.redirect_vars']
        if (
            self.ansible_name != config_aliases[0] or
            self.ansible_aliases != config_aliases or
            any(not self.matches_name([name]) for name in config_aliases) or
            any(self.matches_name([name]) for name in ['test_vars', 'redirect_vars'])
        ):
            return {'failed': True}
        return {'collection_var': True}
