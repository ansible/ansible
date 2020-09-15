# (c) 2015, Brian Coca <bcoca@ansible.com>
# (c) 2012-17 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
lookup: url
author: Brian Coca (@bcoca)
version_added: "1.9"
short_description: return contents from URL
description:
    - Returns the content of the URL requested to be used as data in play.
options:
  _terms:
    description: urls to query
  validate_certs:
    description: Flag to control SSL certificate validation
    type: boolean
    default: True
  split_lines:
    description: Flag to control if content is returned as a list of lines or as a single text blob
    type: boolean
    default: True
  use_proxy:
    description: Flag to control if the lookup will observe HTTP proxy environment variables when present.
    type: boolean
    default: True
  username:
    description: Username to use for HTTP authentication.
    type: string
    version_added: "2.8"
  password:
    description: Password to use for HTTP authentication.
    type: string
    version_added: "2.8"
  headers:
    description: HTTP request headers
    type: dictionary
    default: {}
    version_added: "2.9"
"""

EXAMPLES = """
- name: url lookup splits lines by default
  debug: msg="{{item}}"
  loop: "{{ lookup('url', 'https://github.com/gremlin.keys', wantlist=True) }}"

- name: display ip ranges
  debug: msg="{{ lookup('url', 'https://ip-ranges.amazonaws.com/ip-ranges.json', split_lines=False) }}"

- name: url lookup using authentication
  debug: msg="{{ lookup('url', 'https://some.private.site.com/file.txt', username='bob', password='hunter2') }}"

- name: url lookup using headers
  debug: msg="{{ lookup('url', 'https://some.private.site.com/api/service', headers={'header1':'value1', 'header2':'value2'} ) }}"
"""

RETURN = """
  _list:
    description: list of list of lines or content of url(s)
"""

from ansible.errors import AnsibleError
from ansible.module_utils.six.moves.urllib.error import HTTPError, URLError
from ansible.module_utils._text import to_text, to_native
from ansible.module_utils.urls import open_url, ConnectionError, SSLValidationError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

display = Display()


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        self.set_options(direct=kwargs)

        ret = []
        for term in terms:
            display.vvvv("url lookup connecting to %s" % term)
            try:
                response = open_url(term, validate_certs=self.get_option('validate_certs'),
                                    use_proxy=self.get_option('use_proxy'),
                                    url_username=self.get_option('username'),
                                    url_password=self.get_option('password'),
                                    headers=self.get_option('headers'))
            except HTTPError as e:
                raise AnsibleError("Received HTTP error for %s : %s" % (term, to_native(e)))
            except URLError as e:
                raise AnsibleError("Failed lookup url for %s : %s" % (term, to_native(e)))
            except SSLValidationError as e:
                raise AnsibleError("Error validating the server's certificate for %s: %s" % (term, to_native(e)))
            except ConnectionError as e:
                raise AnsibleError("Error connecting to %s: %s" % (term, to_native(e)))

            if self.get_option('split_lines'):
                for line in response.read().splitlines():
                    ret.append(to_text(line))
            else:
                ret.append(to_text(response.read()))
        return ret
