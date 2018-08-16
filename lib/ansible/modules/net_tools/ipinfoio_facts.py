#!/usr/bin/python
#
# (c) 2016, Aleksei Kostiuk <unitoff@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ipinfoio_facts
short_description: "Retrieve IP geolocation facts of a host's IP address"
description:
  - "Gather IP geolocation facts of a host's IP address using ipinfo.io API"
version_added: "2.3"
author: "Aleksei Kostiuk (@akostyuk)"
options:
  timeout:
    description:
      - HTTP connection timeout in seconds
    required: false
    default: 10
  http_agent:
    description:
      - Set http user agent
    required: false
    default: "ansible-ipinfoio-module/0.0.1"
notes:
  - "Check http://ipinfo.io/ for more information"
'''

EXAMPLES = '''
# Retrieve geolocation data of a host's IP address
- name: get IP geolocation data
  ipinfoio_facts:
'''

RETURN = '''
ansible_facts:
  description: "Dictionary of ip geolocation facts for a host's IP address"
  returned: changed
  type: complex
  contains:
    ip:
      description: "Public IP address of a host"
      type: string
      sample: "8.8.8.8"
    hostname:
      description: Domain name
      type: string
      sample: "google-public-dns-a.google.com"
    country:
      description: ISO 3166-1 alpha-2 country code
      type: string
      sample: "US"
    region:
      description: State or province name
      type: string
      sample: "California"
    city:
      description: City name
      type: string
      sample: "Mountain View"
    loc:
      description: Latitude and Longitude of the location
      type: string
      sample: "37.3860,-122.0838"
    org:
      description: "organization's name"
      type: string
      sample: "AS3356 Level 3 Communications, Inc."
    postal:
      description: Postal code
      type: string
      sample: "94035"
'''
from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.urls import fetch_url


USER_AGENT = 'ansible-ipinfoio-module/0.0.1'


class IpinfoioFacts(object):

    def __init__(self, module):
        self.url = 'https://ipinfo.io/json'
        self.timeout = module.params.get('timeout')
        self.module = module

    def get_geo_data(self):
        response, info = fetch_url(self.module, self.url, force=True,  # NOQA
                                   timeout=self.timeout)
        try:
            info['status'] == 200
        except AssertionError:
            self.module.fail_json(msg='Could not get {} page, '
                                  'check for connectivity!'.format(self.url))
        else:
            try:
                content = response.read()
                result = self.module.from_json(content.decode('utf8'))
            except ValueError:
                self.module.fail_json(
                    msg='Failed to parse the ipinfo.io response: '
                    '{0} {1}'.format(self.url, content))
            else:
                return result


def main():
    module = AnsibleModule(  # NOQA
        argument_spec=dict(
            http_agent=dict(default=USER_AGENT),
            timeout=dict(type='int', default=10),
        ),
        supports_check_mode=True,
    )

    ipinfoio = IpinfoioFacts(module)
    ipinfoio_result = dict(
        changed=False, ansible_facts=ipinfoio.get_geo_data())
    module.exit_json(**ipinfoio_result)


if __name__ == '__main__':
    main()
