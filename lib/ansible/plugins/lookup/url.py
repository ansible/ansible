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
  force:
    description: Whether or not to set "cache-control" header with value "no-cache"
    type: boolean
    version_added: "2.10"
    default: False
    vars:
        - name: ansible_lookup_url_force
    env:
        - name: ANSIBLE_LOOKUP_URL_FORCE
    ini:
        - section: url_lookup
          key: force
  timeout:
    description: How long to wait for the server to send data before giving up
    type: float
    version_added: "2.10"
    default: 10
    vars:
        - name: ansible_lookup_url_timeout
    env:
        - name: ANSIBLE_LOOKUP_URL_TIMEOUT
    ini:
        - section: url_lookup
          key: timeout
  http_agent:
    description: User-Agent to use in the request
    type: string
    version_added: "2.10"
    vars:
        - name: ansible_lookup_url_agent
    env:
        - name: ANSIBLE_LOOKUP_URL_AGENT
    ini:
        - section: url_lookup
          key: agent
  force_basic_auth:
    description: Force basic authentication
    type: boolean
    version_added: "2.10"
    default: False
    vars:
        - name: ansible_lookup_url_agent
    env:
        - name: ANSIBLE_LOOKUP_URL_AGENT
    ini:
        - section: url_lookup
          key: agent
  follow_redirects:
    description: String of urllib2, all/yes, safe, none to determine how redirects are followed, see RedirectHandlerFactory for more information
    type: string
    version_added: "2.10"
    default: 'urllib2'
    vars:
        - name: ansible_lookup_url_follow_redirects
    env:
        - name: ANSIBLE_LOOKUP_URL_FOLLOW_REDIRECTS
    ini:
        - section: url_lookup
          key: follow_redirects
  use_gssapi:
    description: Use GSSAPI handler of requests
    type: boolean
    version_added: "2.10"
    default: False
    vars:
        - name: ansible_lookup_url_use_gssapi
    env:
        - name: ANSIBLE_LOOKUP_URL_USE_GSSAPI
    ini:
        - section: url_lookup
          key: use_gssapi
  unix_socket:
    description: String of file system path to unix socket file to use when establishing connection to the provided url
    type: string
    version_added: "2.10"
    vars:
        - name: ansible_lookup_url_unix_socket
    env:
        - name: ANSIBLE_LOOKUP_URL_UNIX_SOCKET
    ini:
        - section: url_lookup
          key: unix_socket
  ca_path:
    description: String of file system path to CA cert bundle to use
    type: string
    version_added: "2.10"
    vars:
        - name: ansible_lookup_url_ca_path
    env:
        - name: ANSIBLE_LOOKUP_URL_CA_PATH
    ini:
        - section: url_lookup
          key: ca_path
  unredirected_headers:
    description: A list of headers to not attach on a redirected request
    type: list
    version_added: "2.10"
    vars:
        - name: ansible_lookup_url_unredir_headers
    env:
        - name: ANSIBLE_LOOKUP_URL_UNREDIR_HEADERS
    ini:
        - section: url_lookup
          key: unredirected_headers
"""

EXAMPLES = """
- name: url lookup splits lines by default
  debug: msg="{{item}}"
  loop: "{{ lookup('url', 'https://github.com/gremlin.keys', wantlist=True) }}"

- name: display ip ranges
  debug: msg="{{ lookup('url', 'https://ip-ranges.amazonaws.com/ip-ranges.json', split_lines=False) }}"

- name: url lookup using authentication
  debug: msg="{{ lookup('url', 'https://some.private.site.com/file.txt', username='bob', password='hunter2') }}"

- name: url lookup using basic authentication
  debug: msg="{{ lookup('url', 'https://some.private.site.com/file.txt', username='bob', password='hunter2', force_basic_auth='True') }}"

- name: url lookup using headers
  debug: msg="{{ lookup('url', 'https://some.private.site.com/api/service', headers={'header1':'value1', 'header2':'value2'} ) }}"
"""

RETURN = """
  _list:
    description: list of list of lines or content of url(s)
    type: list
    elements: str
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

        self.set_options(var_options=variables, direct=kwargs)

        ret = []
        for term in terms:
            display.vvvv("url lookup connecting to %s" % term)
            try:
                response = open_url(term, validate_certs=self.get_option('validate_certs'),
                                    use_proxy=self.get_option('use_proxy'),
                                    url_username=self.get_option('username'),
                                    url_password=self.get_option('password'),
                                    headers=self.get_option('headers'),
                                    force=self.get_option('force'),
                                    timeout=self.get_option('timeout'),
                                    http_agent=self.get_option('http_agent'),
                                    force_basic_auth=self.get_option('force_basic_auth'),
                                    follow_redirects=self.get_option('follow_redirects'),
                                    use_gssapi=self.get_option('use_gssapi'),
                                    unix_socket=self.get_option('unix_socket'),
                                    ca_path=self.get_option('ca_path'),
                                    unredirected_headers=self.get_option('unredirected_headers'))
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
