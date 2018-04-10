#!/usr/bin/python

# Copyright: (c) 2016-2017, Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: oneview_enclosure_facts
short_description: Retrieve facts about one or more Enclosures
description:
    - Retrieve facts about one or more of the Enclosures from OneView.
version_added: "2.5"
requirements:
    - hpOneView >= 2.0.1
author:
    - Felipe Bulsoni (@fgbulsoni)
    - Thiago Miotto (@tmiotto)
    - Adriane Cardozo (@adriane-cardozo)
options:
    name:
      description:
        - Enclosure name.
    options:
      description:
        - "List with options to gather additional facts about an Enclosure and related resources.
          Options allowed: C(script), C(environmentalConfiguration), and C(utilization). For the option C(utilization),
          you can provide specific parameters."

extends_documentation_fragment:
    - oneview
    - oneview.factsparams
'''

EXAMPLES = '''
- name: Gather facts about all Enclosures
  oneview_enclosure_facts:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
  no_log: true
  delegate_to: localhost
- debug: var=enclosures

- name: Gather paginated, filtered and sorted facts about Enclosures
  oneview_enclosure_facts:
    params:
      start: 0
      count: 3
      sort: name:descending
      filter: status=OK
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
  no_log: true
  delegate_to: localhost
- debug: var=enclosures

- name: Gather facts about an Enclosure by name
  oneview_enclosure_facts:
    name: Enclosure-Name
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
  no_log: true
  delegate_to: localhost
- debug: var=enclosures

- name: Gather facts about an Enclosure by name with options
  oneview_enclosure_facts:
    name: Test-Enclosure
    options:
      - script                       # optional
      - environmentalConfiguration   # optional
      - utilization                  # optional
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
  no_log: true
  delegate_to: localhost
- debug: var=enclosures
- debug: var=enclosure_script
- debug: var=enclosure_environmental_configuration
- debug: var=enclosure_utilization

- name: "Gather facts about an Enclosure with temperature data at a resolution of one sample per day, between two
         specified dates"
  oneview_enclosure_facts:
    name: Test-Enclosure
    options:
      - utilization:                   # optional
          fields: AmbientTemperature
          filter:
            - startDate=2016-07-01T14:29:42.000Z
            - endDate=2017-07-01T03:29:42.000Z
          view: day
          refresh: false
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
  no_log: true
  delegate_to: localhost
- debug: var=enclosures
- debug: var=enclosure_utilization
'''

RETURN = '''
enclosures:
    description: Has all the OneView facts about the Enclosures.
    returned: Always, but can be null.
    type: dict

enclosure_script:
    description: Has all the OneView facts about the script of an Enclosure.
    returned: When requested, but can be null.
    type: string

enclosure_environmental_configuration:
    description: Has all the OneView facts about the environmental configuration of an Enclosure.
    returned: When requested, but can be null.
    type: dict

enclosure_utilization:
    description: Has all the OneView facts about the utilization of an Enclosure.
    returned: When requested, but can be null.
    type: dict
'''

from ansible.module_utils.oneview import OneViewModuleBase


class EnclosureFactsModule(OneViewModuleBase):
    argument_spec = dict(name=dict(type='str'), options=dict(type='list'), params=dict(type='dict'))

    def __init__(self):
        super(EnclosureFactsModule, self).__init__(additional_arg_spec=self.argument_spec)

    def execute_module(self):

        ansible_facts = {}

        if self.module.params['name']:
            enclosures = self._get_by_name(self.module.params['name'])

            if self.options and enclosures:
                ansible_facts = self._gather_optional_facts(self.options, enclosures[0])
        else:
            enclosures = self.oneview_client.enclosures.get_all(**self.facts_params)

        ansible_facts['enclosures'] = enclosures

        return dict(changed=False,
                    ansible_facts=ansible_facts)

    def _gather_optional_facts(self, options, enclosure):

        enclosure_client = self.oneview_client.enclosures
        ansible_facts = {}

        if options.get('script'):
            ansible_facts['enclosure_script'] = enclosure_client.get_script(enclosure['uri'])
        if options.get('environmentalConfiguration'):
            env_config = enclosure_client.get_environmental_configuration(enclosure['uri'])
            ansible_facts['enclosure_environmental_configuration'] = env_config
        if options.get('utilization'):
            ansible_facts['enclosure_utilization'] = self._get_utilization(enclosure, options['utilization'])

        return ansible_facts

    def _get_utilization(self, enclosure, params):
        fields = view = refresh = filter = ''

        if isinstance(params, dict):
            fields = params.get('fields')
            view = params.get('view')
            refresh = params.get('refresh')
            filter = params.get('filter')

        return self.oneview_client.enclosures.get_utilization(enclosure['uri'],
                                                              fields=fields,
                                                              filter=filter,
                                                              refresh=refresh,
                                                              view=view)

    def _get_by_name(self, name):
        return self.oneview_client.enclosures.get_by('name', name)


def main():
    EnclosureFactsModule().run()


if __name__ == '__main__':
    main()
