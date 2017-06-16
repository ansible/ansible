#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2017, Kenneth D. Evensen <kevensen@redhat.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
author:
  - "Kenneth D. Evensen (@kevensen)"
description:
  - |-
      This module provides query capabilities against ManageIQ and the
      CloudForms Management Engine.
module: manageiq_query
options:
  host:
    description:
      - "The host for the ManageIQ API endpoint."
    required: false
    default: 127.0.0.1
  port:
    description:
      - "The port for the ManageIQ API endpoint."
    required: false
    default: 443
  ssl:
    description:
      - "Whether or not to use SSL/TLS"
    required: false
    default: yes
  url_username:
    description:
      - "The ManageIQ/CFME user name with which to query."
    required: true
  url_password:
    description:
      - "The ManageIQ/CFME user's password with which to query."
    required: true
  resource:
    description:
      - "The ManageIQ/CFME resource to query."
    required: true
  offset:
    description:
      - "0-based offset of first item to return."
    required: false
  limit:
    description:
      - "Number of items to return. If 0 is specified then the remaining
         items are returned."
    required: false
  filter:
    description:
      - "One or more filters to search on."
    required: false
  attributes:
    description:
      - "Which attributes in addition to id and href to return. If not
         specified then all attributes are returned"
    required: false
  expand:
    description:
      - "To expand the resources returned in the collection and not
         just the href."
    required: false
  sort_by:
    description:
      - "By which attribute(s) to sort the result."
    required: false
  sort_order:
    description:
      - "Order of the sort."
    choices:
      - ascending
      - decending
    default: ascending
    required: false



short_description: "Query ManageIQ and CFME Resources"
version_added: "2.4"

"""

EXAMPLES = """
- name:
  - |-
     Retrieve all users with the name Administrator and only show
     the name and userid
  manageiq_query:
    url_username: admin
    url_password: <<redacted>>
    resource: users
    validate_certs: no
    expand: resources
    filter: name=Administrator
    attributes:
      - name
      - userid

- name: List all users
  manageiq_query:
    url_username: admin
    url_password: <<redacted>>
    resource: users
    validate_certs: no
    expand: resources

"""

RETURN = '''
code:
  description: The HTTP status code for the query.
  returned: success
  type: int
count:
  description: The total number of resources for this resource type.
  returned: success
  type: int
name:
  description: The name of the resource being queried.
  returned: success
  type: string
resources:
  description:
  - |-
       If the code is 200, then this will be a JSON string with the response
       of ManageIQ.  If there was an error, this value will be the error
       message.
  returned: success
  type: string
subcount:
  description: The total number of resources returned.
  returned: success
  type: int
url:
  description: The URL to the requested resource.
  returned: success
  type: string


...
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils import urls
from ansible.module_utils.six.moves import urllib


def url(module):
    url = ''
    params = ['offset',
              'limit',
              'filter',
              'attributes',
              'expand',
              'sort_by',
              'sort_order']
    first_param = True

    if module.params['ssl']:
        url += 'https://'
    else:
        url += 'http://'

    url += module.params['host']
    url += ':'
    url += str(module.params['port'])
    url += '/api/'
    url += module.params['resource']
    url += '?'

    for param in params:
        if module.params[param] is not None:
            if not first_param:
                url += '&'

            if param in 'filter':
                url += param
                url += "[]="
                filter_param = module.params[param].split('=')
                url += filter_param[0]
                url += '='
                url += '\'' + urllib.parse.quote(filter_param[1]) + '\''
                first_param = False

            elif param in 'attributes' or param in 'sort_by':
                first_attr = True
                url += param
                url += '='
                for attr in module.params[param]:
                    if not first_attr:
                        url += ','
                    url += attr
                    first_attr = False
            else:
                url += param
                url += '='
                url += str(module.params[param])
                first_param = False

    module.log(msg="URL for Query is %s" % url)
    return url


def query(module, url):
    response, info = urls.fetch_url(url=url,
                                    module=module,
                                    method='get')
    module.log(msg="Code for Query is %s" % info['status'])
    if info['status'] >= 300:
            return info['body'], info['status']

    return module.from_json(response.read()), info['status']


def main():

    module = AnsibleModule(
        argument_spec=dict(
            host=dict(required=False, type='str', default='127.0.0.1'),
            port=dict(required=False, type='int', default=443),
            ssl=dict(required=False, type='bool', default='yes'),
            url_username=dict(required=True, type='str'),
            url_password=dict(required=True, type='str', no_log=True),
            resource=dict(required=True, type='str'),
            offset=dict(required=False, type='int'),
            limit=dict(required=False, type='int'),
            filter=dict(required=False, type='str'),
            attributes=dict(required=False, type='list'),
            expand=dict(required=False, type='str'),
            sort_by=dict(required=False, type='list'),
            sort_order=dict(required=False,
                            choices=['ascending', 'decending'],
                            default='ascending'),
            validate_certs=dict(required=False, type='bool', default='yes'),
            client_cert=dict(required=False, type='path'),
            client_key=dict(required=False, type='path')
        ),
        supports_check_mode=True,
        no_log=True
    )
    count = 0
    name = module.params['resource']
    body = None
    subcount = 0

    query_url = url(module)
    result, code = query(module, query_url)

    if isinstance(result, str):
        body = result
    else:
        count = result['count']
        name = result['name']
        body = result['resources']
        subcount = result['subcount']

    facts = {}
    facts['manageiq_query'] = {
        'code': code,
        'count': count,
        'name': name,
        'resources': body,
        'subcount': subcount,
        'url': query_url
    }

    module.exit_json(changed=False, ansible_facts=facts)

if __name__ == '__main__':
    main()
