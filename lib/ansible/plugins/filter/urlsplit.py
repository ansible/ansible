# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import annotations

DOCUMENTATION = r'''
  name: urlsplit
  version_added: "2.4"
  short_description: get components from URL
  description:
    - Split a URL into its component parts.
  positional: _input, query
  options:
    _input:
      description: URL string to split.
      type: str
      required: true
    query:
      description: Specify a single component to return.
      type: str
      choices: ["fragment", "hostname", "netloc", "password",  "path",  "port",  "query", "scheme",  "username"]
'''

EXAMPLES = r'''

    parts: '{{ "http://user:password@www.acme.com:9000/dir/index.html?query=term#fragment" | urlsplit }}'
    # =>
    #   {
    #       "fragment": "fragment",
    #       "hostname": "www.acme.com",
    #       "netloc": "user:password@www.acme.com:9000",
    #       "password": "password",
    #       "path": "/dir/index.html",
    #       "port": 9000,
    #       "query": "query=term",
    #       "scheme": "http",
    #       "username": "user"
    #   }

    hostname: '{{ "http://user:password@www.acme.com:9000/dir/index.html?query=term#fragment" | urlsplit("hostname") }}'
    # => 'www.acme.com'

    query: '{{ "http://user:password@www.acme.com:9000/dir/index.html?query=term#fragment" | urlsplit("query") }}'
    # => 'query=term'

    path: '{{ "http://user:password@www.acme.com:9000/dir/index.html?query=term#fragment" | urlsplit("path") }}'
    # => '/dir/index.html'
'''

RETURN = r'''
  _value:
    description:
      - A dictionary with components as keyword and their value.
      - If O(query) is provided, a string or integer will be returned instead, depending on O(query).
    type: any
'''

from urllib.parse import urlsplit

from ansible.errors import AnsibleFilterError
from ansible.utils import helpers


def split_url(value, query='', alias='urlsplit'):

    results = helpers.object_to_dict(urlsplit(value), exclude=['count', 'index', 'geturl', 'encode'])

    # If a query is supplied, make sure it's valid then return the results.
    # If no option is supplied, return the entire dictionary.
    if query:
        if query not in results:
            raise AnsibleFilterError(alias + ': unknown URL component: %s' % query)
        return results[query]
    else:
        return results


# ---- Ansible filters ----
class FilterModule(object):
    ''' URI filter '''

    def filters(self):
        return {
            'urlsplit': split_url
        }
