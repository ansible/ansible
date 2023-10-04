from __future__ import annotations

DOCUMENTATION = '''
    vars: noop_vars_plugin
    short_description: Do NOT load host and group vars
    description: don't test loading host and group vars from a collection
    options:
      stage:
        default: all
        choices: ['all', 'inventory', 'task']
        type: str
        ini:
          - key: stage
            section: testns.testcol.noop_vars_plugin
        env:
          - name: ANSIBLE_VARS_PLUGIN_STAGE
    extends_documentation_fragment:
        - testns.testcol2.deprecation
'''

from ansible.plugins.vars import BaseVarsPlugin


class VarsModule(BaseVarsPlugin):

    def get_vars(self, loader, path, entities, cache=True):
        super(VarsModule, self).get_vars(loader, path, entities)
        return {'collection': 'yes', 'notreal': 'value'}
