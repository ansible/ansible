#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Tim Rightnour <thegarbledone@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: snow_record_find
short_description: Search for multiple records from ServiceNow
version_added: "2.9"
description:
    - Gets multiple records from a specified table from ServiceNow based on a query dictionary.
options:
    table:
      description:
      - Table to query for records.
      type: str
      required: false
      default: incident
    query:
      description:
      - Dict to query for records.
      type: dict
      required: true
    max_records:
      description:
      - Maximum number of records to return.
      type: int
      required: false
      default: 20
    order_by:
      description:
      - Field to sort the results on.
      - Can prefix with "-" or "+" to change descending or ascending sort order.
      type: str
      default: "-created_on"
      required: false
    return_fields:
      description:
      - Fields of the record to return in the json.
      - By default, all fields will be returned.
      type: list
      required: false
requirements:
    - python pysnow (pysnow)
author:
    - Tim Rightnour (@garbled1)
extends_documentation_fragment: service_now.documentation
'''

EXAMPLES = '''
- name: Search for incident assigned to group, return specific fields
  snow_record_find:
    username: ansible_test
    password: my_password
    instance: dev99999
    table: incident
    query:
      assignment_group: d625dccec0a8016700a222a0f7900d06
    return_fields:
      - number
      - opened_at

- name: Using OAuth, search for incident assigned to group, return specific fields
  snow_record_find:
    username: ansible_test
    password: my_password
    client_id: "1234567890abcdef1234567890abcdef"
    client_secret: "Password1!"
    instance: dev99999
    table: incident
    query:
      assignment_group: d625dccec0a8016700a222a0f7900d06
    return_fields:
      - number
      - opened_at

- name: Find open standard changes with my template
  snow_record_find:
    username: ansible_test
    password: my_password
    instance: dev99999
    table: change_request
    query:
      AND:
        equals:
          active: "True"
          type: "standard"
          u_change_stage: "80"
        contains:
          u_template: "MY-Template"
    return_fields:
      - sys_id
      - number
      - sys_created_on
      - sys_updated_on
      - u_template
      - active
      - type
      - u_change_stage
      - sys_created_by
      - description
      - short_description
'''

RETURN = '''
record:
    description: The full contents of the matching ServiceNow records as a list of records.
    type: dict
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.service_now import ServiceNowClient
from ansible.module_utils._text import to_native

try:
    # This is being managed by ServiceNowClient
    import pysnow
except ImportError:
    pass


class BuildQuery(object):
    '''
    This is a BuildQuery manipulation class that constructs
    a pysnow.QueryBuilder object based on data input.
    '''

    def __init__(self, module):
        self.module = module
        self.logic_operators = ["AND", "OR", "NQ"]
        self.condition_operator = {
            'equals': self._condition_closure,
            'not_equals': self._condition_closure,
            'contains': self._condition_closure,
            'not_contains': self._condition_closure,
            'starts_with': self._condition_closure,
            'ends_with': self._condition_closure,
            'greater_than': self._condition_closure,
            'less_than': self._condition_closure,
        }
        self.accepted_cond_ops = self.condition_operator.keys()
        self.append_operator = False
        self.simple_query = True
        self.data = module.params['query']

    def _condition_closure(self, cond, query_field, query_value):
        self.qb.field(query_field)
        getattr(self.qb, cond)(query_value)

    def _iterate_fields(self, data, logic_op, cond_op):
        if isinstance(data, dict):
            for query_field, query_value in data.items():
                if self.append_operator:
                    getattr(self.qb, logic_op)()
                self.condition_operator[cond_op](cond_op, query_field, query_value)
                self.append_operator = True
        else:
            self.module.fail_json(msg='Query is not in a supported format')

    def _iterate_conditions(self, data, logic_op):
        if isinstance(data, dict):
            for cond_op, fields in data.items():
                if (cond_op in self.accepted_cond_ops):
                    self._iterate_fields(fields, logic_op, cond_op)
                else:
                    self.module.fail_json(msg='Supported conditions: {0}'.format(str(self.condition_operator.keys())))
        else:
            self.module.fail_json(msg='Supported conditions: {0}'.format(str(self.condition_operator.keys())))

    def _iterate_operators(self, data):
        if isinstance(data, dict):
            for logic_op, cond_op in data.items():
                if (logic_op in self.logic_operators):
                    self.simple_query = False
                    self._iterate_conditions(cond_op, logic_op)
                elif self.simple_query:
                    self.condition_operator['equals']('equals', logic_op, cond_op)
                    break
                else:
                    self.module.fail_json(msg='Query is not in a supported format')
        else:
            self.module.fail_json(msg='Supported operators: {0}'.format(str(self.logic_operators)))

    def build_query(self):
        self.qb = pysnow.QueryBuilder()
        self._iterate_operators(self.data)
        return (self.qb)


def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = ServiceNowClient.snow_argument_spec()
    module_args.update(
        table=dict(type='str', required=False, default='incident'),
        query=dict(type='dict', required=True),
        max_records=dict(default=20, type='int', required=False),
        order_by=dict(default='-created_on', type='str', required=False),
        return_fields=dict(default=None, type='list', required=False)
    )
    module_required_together = [
        ['client_id', 'client_secret']
    ]

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_together=module_required_together
    )

    # Connect to ServiceNow
    service_now_client = ServiceNowClient(module)
    service_now_client.login()
    conn = service_now_client.conn

    params = module.params
    instance = params['instance']
    table = params['table']
    query = params['query']
    max_records = params['max_records']
    return_fields = params['return_fields']

    result = dict(
        changed=False,
        instance=instance,
        table=table,
        query=query,
        max_records=max_records,
        return_fields=return_fields
    )

    # Do the lookup
    try:
        bq = BuildQuery(module)
        qb = bq.build_query()
        record = conn.query(table=module.params['table'],
                            query=qb)
        if module.params['return_fields'] is not None:
            res = record.get_multiple(fields=module.params['return_fields'],
                                      limit=module.params['max_records'],
                                      order_by=[module.params['order_by']])
        else:
            res = record.get_multiple(limit=module.params['max_records'],
                                      order_by=[module.params['order_by']])
    except Exception as detail:
        module.fail_json(msg='Failed to find record: {0}'.format(to_native(detail)), **result)

    try:
        result['record'] = list(res)
    except pysnow.exceptions.NoResults:
        result['record'] = []

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
