# Copyright (c) 2017 Tim Rightnour <thegarbledone@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    author:
        - Tim Rightnour (@garbled1)
    lookup: snow
    version_added: "2.5"
    short_description: get info from Service-Now
    description:
        - Retrieves data from a Service-Now instance
    options:
        _terms:
            description: The list of queries to search Service-Now for
            type: list
            elements: string
            required: True
        instance:
            description: The Service-Now instance to connect to
            required: True
        username:
            description: The username to login to Service-Now as
            reqired: True
        password:
            description: The password to use for username
            required: True
        table:
            description: The table to query in Service-Now
            required: True
        result_fields:
            description: A list of fields to return in the results
            default: [] (all fields)
            type: list
            required: False
        lookup_field:
            description: The field to compare each term against
            required: False
            default: "number"
'''

EXAMPLES = '''
  vars:
    snow_context:
      table: incident
      instance: dev18962
      username: ansible_test
      password: my_password
      result_fields: [number]
  tasks:

    - name: Example of with_snow using record numbers and context
      debug:
        var: item
        verbosity: 0
      with_snow:
        - context: "{{snow_context}}"
        - INC0000055
        - INC0000054

    - name: check for incident numbered INC0000055
      debug: msg={{ lookup("snow", "INC0000055", context=snow_context) }}

    - name: Find all records in the incident table that are on hold, full variable definition
      debug: msg={{ lookup("snow", "2", instance='dev18962', username='ansible_test',
                           password='my_password', table='incident', lookup_field='state', result_fields=['sys_id']) }}
'''

RETURN = '''
    _raw:
        description:
            - list of values associated with queries
            - if result_fields is not restricted to one field, will return
              a list of dicts
        type: list
'''

import os

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

# Pull in pysnow
HAS_PYSNOW = False
try:
    import pysnow
    HAS_PYSNOW = True

except ImportError:
    pass

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


def snow_get(key, instance=None, username=None, password=None, table=None, lookup_field=None, result_fields=None):
    if not HAS_PYSNOW:
        raise AnsibleError("Service-Now lookup requires pysnow to be installed")
    value = []
    if instance is None:
        raise AnsibleError("Service-Now: No instance specified")
    if username is None:
        raise AnsibleError("Service-Now: No username specified")
    if password is None:
        raise AnsibleError("Service-Now: No password specified")
    if table is None:
        raise AnsibleError("Service-Now: No table specified")
    if lookup_field is None:
        raise AnsibleError("Service-Now: No lookup_field specified")

    try:
        conn = pysnow.Client(instance=instance, user=username, password=password)
    except Exception as detail:
        raise AnsibleError("Could not connect to ServiceNow: {0}".format(str(detail)))
    try:
        record = conn.query(table=table, query={lookup_field: key})
        for res in record.get_multiple(fields=result_fields):
            if len(result_fields) == 1:
                # we have single field results, make a simpler list
                value.append(res[result_fields[0]])
            else:
                value.append(res)

    except pysnow.exceptions.NoResults:
        return ['ENOENT']
    except Exception as detail:
        raise AnsibleError("Unknown failure in query record: {0}".format(str(detail)))

    return value


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        display.vvvv("Terms: %s" % str(terms))
        ret = []
        ctx = {}

        instance = kwargs.pop('instance', None)
        username = kwargs.pop('username', None)
        password = kwargs.pop('password', None)
        table = kwargs.pop('table', None)
        lookup_field = kwargs.pop('lookup_field', 'number')
        result_fields = kwargs.pop('result_fields', [])
        ctx = kwargs.get('context', {})

        for term in terms:
            if isinstance(term, dict):
                ctx = term.get('context', {})

        if ctx != {}:
            instance = ctx.pop('instance', None)
            username = ctx.pop('username', None)
            password = ctx.pop('password', None)
            table = ctx.pop('table', None)
            lookup_field = ctx.pop('lookup_field', 'number')
            result_fields = ctx.pop('result_fields', [])

        for term in terms:
            if not isinstance(term, dict):
                value = snow_get(term, instance=instance, username=username,
                                 password=password, table=table,
                                 lookup_field=lookup_field, result_fields=result_fields)
                ret.append(value)

        return ret
