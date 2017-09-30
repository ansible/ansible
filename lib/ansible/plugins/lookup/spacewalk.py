# Copyright (c) 2017 Tim Rightnour <thegarbledone@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import os

from ansible.plugins.lookup import LookupBase
from ansible.errors import AnsibleError
from ansible.module_utils.six.moves import xmlrpc_client

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

DOCUMENTATION = '''
    author:
        - Tim Rightnour (@garbled1)
    lookup: spacewalk
    version_added: "2.5"
    short_description: get info from spacewalk/Satellite 5
    description:
        - Retrieves data from a spacewalk/Satellite 5 server
        - Searches for a hostname, or partial hostname in spacewalk.
        - Can return the spacewalk hostname, ip, system ID, or full record.
    options:
        _terms:
            description: Hostnames to lookup
            type: list
            elements: string
            required: True
        saturl:
            description: The URL of the spacwalk server API
            required: true
        username:
            description: The username to connect to spacewalk server API as
            reqired: True
        password:
            description: The password to use for username
            required: True
        result_fields:
            description: A list of fields to return in the results
            default: [name]
            type: list
            choices: ['name', 'hostname', 'last_checkin', 'ip', 'hw_description',
                      'hw_device_id', 'hw_vendor_id', 'hw_driver', 'id']
        lookup_field:
            description: The field to compare each term against
            default: "hostname"
            choices: ['name', 'hostname', 'ip', 'hw_device_id', 'hw_vendor_id', 'hw_driver', 'id']
'''

EXAMPLES = '''
  vars:
    sat_context:
      saturl: http://sat/rpc/api
      username: satuser
      password: my_password
      result_fields: [id]
  tasks:

    - name: Example of with_spacewalk using hostnames and context
      debug:
        var: item
        verbosity: 0
      with_spacewalk:
        - context: "{{sat_context}}"
        - dbnode1
        - web02

    - name: check for a host named joe01 with context
      debug: msg={{ lookup("spacewalk", "joe01", context=sat_context) }}

    - name: Find all servers whose ip contains 10.1.5., full variable definition
      debug: msg={{ lookup("spacewalk", "10.1.5", saturl='http://sat/rpc/api',
                           username='satuser', password='my_password',
                           lookup_field='ip', result_fields=['name']) }}
'''

RETURN = '''
    _raw:
        description:
            - list of values associated with queries
            - if result_fields is not restricted to one field, will return
              a list of dicts
        type: list
'''


def spacewalk_connect(saturl=None, password=None, user=None):
    sw_conn = dict()
    if password is None or saturl is None or user is None:
        raise AnsibleError('password, saturl and user are required values')
    try:
        sw_conn['client'] = xmlrpc_client.Server(saturl)
        sw_conn['session'] = sw_conn['client'].auth.login(user, password)
    except Exception as e:
        raise AnsibleError('Unable to login to spacwalk/satellite server: {}'.format(str(e)))

    return sw_conn


def spacewalk_search(term, sw=None, result_fields=None, lookup_field='hostname'):
    value = []

    valid_result = ['name', 'hostname', 'last_checkin', 'id', 'ip', 'hw_description',
                    'hw_device_id', 'hw_vendor_id', 'hw_driver']

    if sw is None:
        raise AnsibleError("Could not connect to spacewalk/satellite")

    if result_fields is None:
        result_fields = ['name']

    for rf in result_fields:
        if rf not in valid_result:
            raise AnsibleError("{0} is not a valid result field, use one of {1}".format(rf, str(valid_result)))

    # first, figure out what our lookup is
    if lookup_field == 'hw_description':
        systems = sw['client'].system.search.deviceDescription(sw['session'], term)
    elif lookup_field == 'hw_driver':
        systems = sw['client'].system.search.deviceDriver(sw['session'], term)
    elif lookup_field == 'hw_device_id':
        systems = sw['client'].system.search.deviceId(sw['session'], term)
    elif lookup_field == 'hw_vendor_id':
        systems = sw['client'].system.search.deviceVendorId(sw['session'], term)
    elif lookup_field == 'hostname':
        systems = sw['client'].system.search.hostname(sw['session'], term)
    elif lookup_field == 'ip':
        systems = sw['client'].system.search.ip(sw['session'], term)
    elif lookup_field == 'name' or lookup_field == 'description':
        systems = sw['client'].system.search.nameAndDescription(sw['session'], term)
    elif lookup_field == 'id':
        systems = sw['client'].system.search.uuid(sw['session'], term)
    else:
        raise AnsibleError("Invalid lookup_field : {0}".format(str(lookup_field)))

    if len(systems) < 1:
        return ['ENOENT']

    for sys in systems:
        # if we have a single result, make a simple list
        if len(result_fields) == 1:
            res = sys.get(result_fields[0])
            value.append(res)
        elif not result_fields:
            value.append(sys)
        else:
            # dict of per-system values requested
            sysval = dict()
            for rf in result_fields:
                res = sys.get(rf)
                sysval[rf] = res
            value.append(sysval)

    return value


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        display.vvvv("Terms: %s" % str(terms))
        ret = []
        ctx = {}

        saturl = kwargs.pop('saturl', None)
        username = kwargs.pop('username', None)
        password = kwargs.pop('password', None)
        lookup_field = kwargs.pop('lookup_field', 'hostname')
        result_fields = kwargs.pop('result_fields', ['name'])
        ctx = kwargs.get('context', {})

        for term in terms:
            if isinstance(term, dict):
                ctx = term.get('context', {})

        if ctx != {}:
            saturl = ctx.pop('saturl', None)
            username = ctx.pop('username', None)
            password = ctx.pop('password', None)
            lookup_field = ctx.pop('lookup_field', 'hostname')
            result_fields = ctx.pop('result_fields', ['name'])

        sw_conn = spacewalk_connect(saturl=str(saturl), password=str(password), user=str(username))

        for term in terms:
            if not isinstance(term, dict):
                value = spacewalk_search(str(term), sw=sw_conn, result_fields=result_fields, lookup_field=lookup_field)
                ret.append(value)

        sw_conn['client'].auth.logout(sw_conn['session'])

        return ret
