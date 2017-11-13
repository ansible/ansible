#!/usr/bin/python

# Copyright: (c) 2016-2017, Hewlett Packard Enterprise Development LP
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: oneview_managed_san_facts
short_description: Retrieve facts about the OneView Managed SANs
description:
    - Retrieve facts about the OneView Managed SANs.
version_added: "2.5"
requirements:
    - "hpOneView >= 3.0.0"
author:
    - Alex Monteiro (@aalexmonteiro)
    - Madhav Bharadwaj (@madhav-bharadwaj)
    - Priyanka Sood (@soodpr)
    - Ricardo Galeno (@ricardogpsf)
options:
    name:
      description:
        - Name of the Managed SAN.
    options:
      description:
        - "List with options to gather additional facts about Managed SAN.
          Options allowed:
          C(endpoints) gets the list of endpoints in the SAN identified by name.
          C(wwn) gets the list of Managed SANs associated with an informed WWN C(locate)."
    params:
      description:
        - List of params to delimit, filter and sort the list of resources.
        - "params allowed:
           C(start): The first item to return, using 0-based indexing.
           C(count): The number of resources to return.
           C(query): A general query string to narrow the list of resources returned.
           C(sort): The sort order of the returned data set."

extends_documentation_fragment:
    - oneview
'''

EXAMPLES = '''
- name: Gather facts about all Managed SANs
  oneview_managed_san_facts:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
  no_log: true
  delegate_to: localhost

- debug: var=managed_sans

- name: Gather paginated, filtered and sorted facts about Managed SANs
  oneview_managed_san_facts:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
    params:
      count: 3
      query: imported eq true
      start: 0
      sort: name:ascending
  no_log: true
  delegate_to: localhost

- debug: var=managed_sans

- name: Gather facts about a Managed SAN by name
  oneview_managed_san_facts:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
    name: "SAN1_0"
  no_log: true
  delegate_to: localhost

- debug: var=managed_sans

- name: Gather facts about the endpoints in the SAN identified by name
  oneview_managed_san_facts:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
    name: "SAN1_0"
    options:
      - endpoints
  no_log: true
  delegate_to: localhost

- debug: var=managed_sans
- debug: var=managed_san_endpoints

- name: Gather facts about Managed SANs for an associated WWN
  oneview_managed_san_facts:
    hostname: 172.16.101.48
    username: administrator
    password: my_password
    api_version: 500
    options:
      - wwn:
         locate: "20:00:4A:2B:21:E0:00:01"
  no_log: true
  delegate_to: localhost

- debug: var=wwn_associated_sans
'''

RETURN = '''
managed_sans:
    description: The list of Managed SANs.
    returned: Always, but can be null.
    type: list

managed_san_endpoints:
    description: The list of endpoints in the SAN identified by name.
    returned: When requested, but can be null.
    type: dict

wwn_associated_sans:
    description: The list of associations between provided WWNs and the SANs.
    returned: When requested, but can be null.
    type: dict
'''

from ansible.module_utils.oneview import OneViewModuleBase


class ManagedSanFactsModule(OneViewModuleBase):
    argument_spec = dict(
        name=dict(type='str'),
        options=dict(type='list'),
        params=dict(type='dict')
    )

    def __init__(self):
        super(ManagedSanFactsModule, self).__init__(additional_arg_spec=self.argument_spec)

        self.resource_client = self.oneview_client.managed_sans

    def execute_module(self):
        facts = dict()

        name = self.module.params['name']

        if name:
            facts['managed_sans'] = [self.resource_client.get_by_name(name)]

            if facts['managed_sans'] and 'endpoints' in self.options:
                managed_san = facts['managed_sans'][0]
                if managed_san:
                    environmental_configuration = self.resource_client.get_endpoints(managed_san['uri'])
                    facts['managed_san_endpoints'] = environmental_configuration

        else:
            facts['managed_sans'] = self.resource_client.get_all(**self.facts_params)

        if self.options:
            if self.options.get('wwn'):
                wwn = self.__get_sub_options(self.options['wwn'])
                facts['wwn_associated_sans'] = self.resource_client.get_wwn(wwn['locate'])

        return dict(changed=False, ansible_facts=facts)

    def __get_sub_options(self, option):
        return option if isinstance(option, dict) else {}


def main():
    ManagedSanFactsModule().run()


if __name__ == '__main__':
    main()
