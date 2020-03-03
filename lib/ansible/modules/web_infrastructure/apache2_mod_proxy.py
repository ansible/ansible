#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Olivier Boukili <boukili.olivier@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: apache2_mod_proxy
author: Olivier Boukili (@oboukili)
version_added: "2.2"
short_description: Set and/or get members' attributes of an Apache httpd 2.4 mod_proxy balancer pool
description:
  - Set and/or get members' attributes of an Apache httpd 2.4 mod_proxy balancer
    pool, using HTTP POST and GET requests. The httpd mod_proxy balancer-member
    status page has to be enabled and accessible, as this module relies on parsing
    this page. This module supports ansible check_mode, and requires BeautifulSoup
    python module.
options:
  balancer_url_suffix:
    description:
      - Suffix of the balancer pool url required to access the balancer pool
        status page (e.g. balancer_vhost[:port]/balancer_url_suffix).
    default: /balancer-manager/
  balancer_vhost:
    description:
      - (ipv4|ipv6|fqdn):port of the Apache httpd 2.4 mod_proxy balancer pool.
    required: true
  balancer_name:
     description:
       - name of the balancer to use if this vhost as more than one balancer
  balancer_member:
    description:
      - (ipv4|ipv6|fqdn) of the balancer member to get or to set attributes to.
        Port number is autodetected and should not be specified here.
        If undefined, apache2_mod_proxy module will return a members list of
        dictionaries of all the current balancer pool members' attributes.
  state:
    description:
      - Desired state of the member host.
        (absent|disabled),drained,hot_standby,ignore_errors can be
        simultaneously invoked by separating them with a comma (e.g. state=drained,ignore_errors).
    choices: ["present", "absent", "enabled", "disabled", "drained", "hot_standby", "ignore_errors","lf:<number>"]
  tls:
    description:
      - Use https to access balancer management page.
    type: bool
    default: 'no'
  validate_certs:
    description:
      - Validate ssl/tls certificates.
    type: bool
    default: 'yes'
'''

EXAMPLES = '''
# Get all current balancer pool members' attributes:
- apache2_mod_proxy:
    balancer_vhost: 10.0.0.2

# Get a specific member's attributes:
- apache2_mod_proxy:
    balancer_vhost: myws.mydomain.org
    balancer_suffix: /lb/
    balancer_host: node1.myws.mydomain.org

# Enable all balancer pool members:
- apache2_mod_proxy:
    balancer_vhost: '{{ myloadbalancer_host }}'
  register: result
- apache2_mod_proxy:
    balancer_vhost: '{{ myloadbalancer_host }}'
    balancer_member: '{{ item.host }}'
    state: present
  with_items: '{{ result.members }}'

# Gracefully disable a member from a loadbalancer node:
- apache2_mod_proxy:
    balancer_vhost: '{{ vhost_host }}'
    balancer_member: '{{ member.host }}'
    state: drained
  delegate_to: myloadbalancernode
- wait_for:
    host: '{{ member.host }}'
    port: '{{ member.port }}'
    state: drained
  delegate_to: myloadbalancernode
- apache2_mod_proxy:
    balancer_vhost: '{{ vhost_host }}'
    balancer_member: '{{ member.host }}'
    state: absent
  delegate_to: myloadbalancernode
'''

RETURN = '''
member:
    description: specific balancer member information dictionary, returned when apache2_mod_proxy module is invoked with balancer_member parameter.
    type: dict
    returned: success
    sample:
      {"attributes":
            {"Busy": "0",
            "Elected": "42",
            "Factor": "1",
            "From": "136K",
            "Load": "0",
            "Route": null,
            "RouteRedir": null,
            "Set": "0",
            "Status": "Init Ok ",
            "To": " 47K",
            "Worker URL": null
        },
        "balancer_url": "http://10.10.0.2/balancer-manager/",
        "host": "10.10.0.20",
        "management_url": "http://10.10.0.2/lb/?b=mywsbalancer&w=http://10.10.0.20:8080/ws&nonce=8925436c-79c6-4841-8936-e7d13b79239b",
        "path": "/ws",
        "port": 8080,
        "protocol": "http",
        "status": {
            "disabled": false,
            "drained": false,
            "hot_standby": false,
            "ignore_errors": false
        }
      }
members:
    description: list of member (defined above) dictionaries, returned when apache2_mod_proxy is invoked with no balancer_member and state args.
    returned: success
    type: list
    sample:
      [{"attributes": {
            "Busy": "0",
            "Elected": "42",
            "Factor": "1",
            "From": "136K",
            "Load": "0",
            "Route": null,
            "RouteRedir": null,
            "Set": "0",
            "Status": "Init Ok ",
            "To": " 47K",
            "Worker URL": null
        },
        "balancer_url": "http://10.10.0.2/balancer-manager/",
        "host": "10.10.0.20",
        "management_url": "http://10.10.0.2/lb/?b=mywsbalancer&w=http://10.10.0.20:8080/ws&nonce=8925436c-79c6-4841-8936-e7d13b79239b",
        "path": "/ws",
        "port": 8080,
        "protocol": "http",
        "status": {
            "disabled": false,
            "drained": false,
            "hot_standby": false,
            "ignore_errors": false
        }
        },
        {"attributes": {
            "Busy": "0",
            "Elected": "42",
            "Factor": "1",
            "From": "136K",
            "Load": "0",
            "Route": null,
            "RouteRedir": null,
            "Set": "0",
            "Status": "Init Ok ",
            "To": " 47K",
            "Worker URL": null
        },
        "balancer_url": "http://10.10.0.2/balancer-manager/",
        "host": "10.10.0.21",
        "management_url": "http://10.10.0.2/lb/?b=mywsbalancer&w=http://10.10.0.21:8080/ws&nonce=8925436c-79c6-4841-8936-e7d13b79239b",
        "path": "/ws",
        "port": 8080,
        "protocol": "http",
        "status": {
            "disabled": false,
            "drained": false,
            "hot_standby": false,
            "ignore_errors": false}
        }
      ]
'''

import re
import traceback

BEAUTIFUL_SOUP_IMP_ERR = None
try:
    from bs4 import BeautifulSoup
except ImportError:
    BEAUTIFUL_SOUP_IMP_ERR = traceback.format_exc()
    HAS_BEAUTIFULSOUP = False
else:
    HAS_BEAUTIFULSOUP = True

# balancer member attributes extraction regexp:
EXPRESSION = r"(b=([\w\.\-]+)&w=(https?|ajp|wss?|ftp|[sf]cgi)://([\w\.\-]+):?(\d*)([/\w\.\-]*)&?[\w\-\=]*)"
# Apache2 server version extraction regexp:
APACHE_VERSION_EXPRESSION = r"SERVER VERSION: APACHE/([\d.]+)"


def regexp_extraction(string, _regexp, groups=1):
    """ Returns the capture group (default=1) specified in the regexp, applied to the string """
    regexp_search = re.search(string=str(string), pattern=str(_regexp))
    if regexp_search:
        if regexp_search.group(groups) != '':
            return str(regexp_search.group(groups))
    return None


class BalancerMember(object):
    """ Apache 2.4 mod_proxy LB balancer member.
    attributes:
        read-only:
            host -> member host (string),
            management_url -> member management url (string),
            protocol -> member protocol (string)
            port -> member port (string),
            path -> member location (string),
            balancer_url -> url of this member's parent balancer (string),
            attributes -> whole member attributes (dictionary)
            module -> ansible module instance (AnsibleModule object).
        writable:
            status -> status of the member (dictionary)
    """

    def __init__(self, management_url, balancer_url, module):
        self.host = regexp_extraction(management_url, str(EXPRESSION), 4)
        self.management_url = str(management_url)
        self.protocol = regexp_extraction(management_url, EXPRESSION, 3)
        self.port = regexp_extraction(management_url, EXPRESSION, 5)
        self.path = regexp_extraction(management_url, EXPRESSION, 6)
        self.balancer_url = str(balancer_url)
        self.module = module

    def get_member_attributes(self):
        """ Returns a dictionary of a balancer member's attributes."""

        balancer_member_page = fetch_url(self.module, self.management_url, headers={'referer': self.management_url})

        if balancer_member_page[1]['status'] != 200:
            self.module.fail_json(msg="Could not get balancer_member_page, check for connectivity! " + balancer_member_page[1])
        else:
            try:
                soup = BeautifulSoup(balancer_member_page[0],features="html.parser")
            except TypeError:
                self.module.fail_json(msg="Cannot parse balancer_member_page HTML! " + str(soup))
            else:
                subsoup = soup.findAll('table')[1].findAll('tr')
                keys = subsoup[0].findAll('th')
                for valuesset in subsoup[1::1]:
                    if re.search(self.host, str(valuesset)):
                        values = valuesset.findAll('td')
                        return dict((keys[x].string, values[x].string) for x in range(0, len(keys)))

    def get_member_status(self):
        """ Returns a dictionary of a balancer member's status attributes."""
        status_mapping = {'disabled': 'Dis',
                          'drained': 'Drn',
                          'hot_standby': 'Stby',
                          'ignore_errors': 'Ign'}
        status = {'lf': float(self.attributes['Factor'])}
        actual_status = str(self.attributes['Status'])
        for mode in status_mapping.keys():
            if re.search(pattern=status_mapping[mode], string=actual_status):
                status[mode] = True
            else:
                status[mode] = False
        return status

    def set_member_status(self, values):
        """ Sets a balancer member's status attributes amongst pre-mapped values."""
        values_mapping = {'disabled': '&w_status_D',
                          'drained': '&w_status_N',
                          'hot_standby': '&w_status_H',
                          'ignore_errors': '&w_status_I',
                          'lf': '&w_lf'}

        request_body = regexp_extraction(self.management_url, EXPRESSION, 1)
        for k in values.keys():
            v=''
            if k=='lf':
                v=str(float(values[k]))
            elif values[k]:
                v='1'
            else:
                v='0'
            request_body = request_body + str(values_mapping[k]) + '='+v

        response = fetch_url(self.module, self.management_url, data=str(request_body), headers={'referer': self.management_url})
        if response[1]['status'] != 200:
            self.module.fail_json(msg="Could not set the member status! " + self.host + " " + response[1]['status'])

    attributes = property(get_member_attributes)
    status = property(get_member_status, set_member_status)


class Balancer(object):
    """ Apache httpd 2.4 mod_proxy balancer object"""

    def __init__(self, host, suffix, name, module, members=None, tls=False):
        self.name=name
        if tls:
            self.base_url = str(str('https://') + str(host))
            self.url = str(str('https://') + str(host) + str(suffix))
        else:
            self.base_url = str(str('http://') + str(host))
            self.url = str(str('http://') + str(host) + str(suffix))
        self.module = module
        self.page = self.fetch_balancer_page()
        if members is None:
            self._members = []

    def fetch_balancer_page(self):
        """ Returns the balancer management html page as a string for later parsing."""
        page = fetch_url(self.module, str(self.url))
        if page[1]['status'] != 200:
            self.module.fail_json(msg="Could not get balancer page! HTTP status response: " + str(page[1]['status']))
        else:
            content = page[0].read()
            apache_version = regexp_extraction(content.upper(), APACHE_VERSION_EXPRESSION, 1)
            if apache_version:
                if not re.search(pattern=r"2\.4\.[\d]*", string=apache_version):
                    self.module.fail_json(msg="This module only acts on an Apache2 2.4+ instance, current Apache2 version: " + str(apache_version))
                return content
            else:
                self.module.fail_json(msg="Could not get the Apache server version from the balancer-manager")

    def get_balancer_members(self):
        """ Returns members of the balancer as a generator object for later iteration."""
        try:
            soup = BeautifulSoup(self.page, features="html.parser")
        except TypeError:
            self.module.fail_json(msg="Cannot parse balancer page HTML! " + str(self.page))
        else:
            h3s=soup.find_all('h3')
            if self.name is None:
                if len(h3s)>1:
                    self.module.fail_json(msg="More than one balancer, balancer_name required")
                return self.parse_balancer(h3s[0])
            else:
                for tag in h3s:
                    if tag.a.contents[0] != 'balancer://'+self.name:
                        continue
                    return self.parse_balancer(tag)
                self.module.fail_json(msg="balancer '"+self.name+"' not found")
    def parse_balancer(self, h3):
        table=h3.find_next_siblings('table', limit=2)
        for element in table[1].findAll('a'):
            balancer_member_suffix = str(element.get('href'))
            if not balancer_member_suffix:
                self.module.fail_json(msg="Argument 'balancer_member_suffix' is empty!")
            else:
                yield BalancerMember(str(self.base_url + balancer_member_suffix), str(self.url), self.module)

    members = property(get_balancer_members)


def main():
    """ Initiates module."""
    module = AnsibleModule(
        argument_spec=dict(
            balancer_vhost=dict(required=True, default=None, type='str'),
            balancer_url_suffix=dict(default="/balancer-manager", type='str'),
            balancer_name=dict(default=None, type='str'),
            balancer_member=dict(type='str', aliases=['member_host']),
            state=dict(type='str'),
            tls=dict(default=False, type='bool'),
            validate_certs=dict(default=True, type='bool')
        ),
        supports_check_mode=True
    )

    if HAS_BEAUTIFULSOUP is False:
        module.fail_json(msg=missing_required_lib('BeautifulSoup'), exception=BEAUTIFUL_SOUP_IMP_ERR)

    member_status = {}
    p=re.compile('(present|absent|enabled|disabled|drained|hot_standby|ignore_errors|lf)(?::([^,]+))?')
    if module.params['state'] is not None:
        states = module.params['state'].split(',')
        for _state in states:
            m=p.match(_state)
            if m:
                s=m.group(1)
                v=m.group(2)
                if v==None:
                    v=True
                if s=='enabled' or s=='present':
                    s='disabled'
                    v=False
                elif s=='absent':
                    s='disabled'
                member_status[s]=v
            else:
                module.fail_json(
                    msg="State can only take values amongst 'lf:<number>', 'present', 'absent', 'enabled', 'disabled', 'drained', 'hot_standby', 'ignore_errors' found: '"+_state+"'"
                )
    else:
        states = ['None']

    mybalancer = Balancer(module.params['balancer_vhost'],
                          module.params['balancer_url_suffix'],
                          module.params['balancer_name'],
                          module=module,
                          tls=module.params['tls'])

    if module.params['balancer_member'] is None:
        json_output_list = []
        for member in mybalancer.members:
            json_output_list.append({
                "host": member.host,
                "status": member.status,
                "protocol": member.protocol,
                "port": member.port,
                "path": member.path,
                "attributes": member.attributes,
                "management_url": member.management_url,
                "balancer_url": member.balancer_url
            })
        module.exit_json(
            changed=False,
            members=json_output_list
        )
    else:
        changed = False

        for member in mybalancer.members:
            if str(member.host) == str(module.params['balancer_member']):
                if module.params['state'] is not None:
                    member_status_before = member.status
                    if not module.check_mode:
                        member_status_after = member.status = member_status
                    else:
                        member_status_after = member_status
                    if member_status_before != member_status_after:
                        changed = True
                module.exit_json(
                    changed=changed,
                    member= {
                        "host": member.host,
                        "status": member.status,
                        "protocol": member.protocol,
                        "port": member.port,
                        "path": member.path,
                        "attributes": member.attributes,
                        "management_url": member.management_url,
                        "balancer_url": member.balancer_url
                    })
        module.fail_json(msg=str(module.params['balancer_member']) + ' is not a member of the balancer ' + str(module.params['balancer_vhost']) + '!')


from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.urls import fetch_url
if __name__ == '__main__':
    main()
