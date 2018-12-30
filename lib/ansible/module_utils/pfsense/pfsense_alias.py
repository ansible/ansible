# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Orion Poplawski <orion@nwra.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pfsense.pfsense import PFSenseModule

ALIASES_ARGUMENT_SPEC = dict(
    name=dict(required=True, type='str'),
    type=dict(default='host', required=False, choices=['host', 'network', 'port', 'urltable']),
    state=dict(required=True, choices=['present', 'absent']),
    address=dict(default=None, required=False, type='str'),
    descr=dict(default=None, required=False, type='str'),
    detail=dict(default='', required=False, type='str'),
    updatefreq=dict(default=None, required=False, type='str'),
)

ALIASES_REQUIRED_IF = [["type", "urltable", ["updatefreq"]]]


class PFSenseAliasModule(object):
    """ module managing pfsense aliases """

    def __init__(self, module, pfsense=None):
        if pfsense is None:
            pfsense = PFSenseModule(module)
        self.module = module
        self.pfsense = pfsense
        self.aliases = self.pfsense.get_element('aliases')

        self.changed = False
        self.change_descr = ''

        self.diff = {}

        self.results = {}
        self.results['added'] = []
        self.results['deleted'] = []
        self.results['modified'] = []

    def _update(self):
        """ make the target pfsense reload aliases """
        return self.pfsense.phpshell('''require_once("filter.inc");
if (filter_configure() == 0) { clear_subsystem_dirty('aliases'); }''')

    def commit_changes(self):
        """ apply changes and exit module """
        stdout = ''
        stderr = ''
        if self.changed and not self.module.check_mode:
            self.pfsense.write_config(descr=self.change_descr)
            (rc, stdout, stderr) = self._update()

        diff = {}
        if 'after' in self.diff:
            diff['after'] = self.diff['after']
        if 'before' in self.diff:
            diff['before'] = self.diff['before']
        self.module.exit_json(stdout=stdout, stderr=stderr, changed=self.changed, diff=diff)

    def add(self, alias):
        """ add or update alias """
        alias_elt = self.pfsense.find_alias(alias['name'], alias['type'])
        self.diff['after'] = alias
        if alias_elt is None:
            alias_elt = self.pfsense.new_element('alias')
            self.pfsense.copy_dict_to_element(alias, alias_elt)
            self.aliases.append(alias_elt)

            changed = True
            self.results['added'].append(alias)
            self.diff['before'] = ''
            self.change_descr = 'ansible pfsense_alias added %s type %s' % (alias['name'], alias['type'])
        else:
            self.diff['before'] = self.pfsense.element_to_dict(alias_elt)
            changed = self.pfsense.copy_dict_to_element(alias, alias_elt)
            if changed:
                self.diff['after'] = self.pfsense.element_to_dict(alias_elt)
                self.results['modified'].append(self.pfsense.element_to_dict(alias_elt))
                self.change_descr = 'ansible pfsense_alias updated "%s" type %s' % (alias['name'], alias['type'])

        if changed:
            self.changed = changed

    def remove_alias_elt(self, alias_elt):
        """ delete alias_elt from xml """
        self.aliases.remove(alias_elt)
        self.changed = True
        self.results['deleted'] = self.pfsense.element_to_dict(alias_elt)
        self.diff['before'] = self.pfsense.element_to_dict(alias_elt)

    def remove(self, alias):
        """ delete alias """
        alias_elt = self.pfsense.find_alias(alias['name'], alias['type'])
        self.diff['after'] = ''
        self.diff['before'] = ''
        if alias_elt is not None:
            self.remove_alias_elt(alias_elt)
            self.change_descr = 'ansible pfsense_alias removed "%s"' % (alias['name'])

    @staticmethod
    def params_to_alias(params):
        """ return an alias dict from module params """
        alias = dict()
        alias['name'] = params['name']
        alias['type'] = params['type']
        if params['state'] == 'present':
            alias['address'] = params['address']
            alias['descr'] = params['descr']
            alias['detail'] = params['detail']
            if alias['type'] == 'urltable':
                alias['url'] = params['address']
                alias['updatefreq'] = params['updatefreq']

        return alias

    def run(self, params):
        """ process input params to add/update/delete an alias """
        alias = self.params_to_alias(params)

        state = params['state']
        if state == 'absent':
            self.remove(alias)
        elif state == 'present':
            self.add(alias)


def main():
    module = AnsibleModule(
        argument_spec=ALIASES_ARGUMENT_SPEC,
        required_if=ALIASES_REQUIRED_IF,
        supports_check_mode=True)

    pfalias = PFSenseAliasModule(module)

    pfalias.run(module.params)

    pfalias.commit_changes()


if __name__ == '__main__':
    main()
