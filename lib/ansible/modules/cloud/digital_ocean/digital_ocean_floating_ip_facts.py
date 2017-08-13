#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: digital_ocean_floating_ip_facts
short_description: DigitalOcean Floating IPs facts
description:
     - Fetch DigitalOcean Floating IPs facts.
version_added: "2.4"
author: "Patrick Marques (@pmarques)"
options:
  oauth_token:
    description:
     - DigitalOcean OAuth token.
    required: true

notes:
  - Version 2 of DigitalOcean API is used.
requirements:
  - "python >= 2.6"
'''


EXAMPLES = '''
- name: "Gather facts about all Floating IPs"
  digital_ocean_floating_ip_facts:
  register: result

- name: "List of current floating ips"
  debug: var=result.floating_ips
'''


RETURN = '''
# Digital Ocean API info https://developers.digitalocean.com/documentation/v2/#floating-ips
floating_ips:
    description: a DigitalOcean Floating IP resource
    returned: success and no resource constraint
    type: list
    sample: [
      {
        "ip": "45.55.96.47",
        "droplet": null,
        "region": {
          "name": "New York 3",
          "slug": "nyc3",
          "sizes": [
            "512mb",
            "1gb",
            "2gb",
            "4gb",
            "8gb",
            "16gb",
            "32gb",
            "48gb",
            "64gb"
          ],
          "features": [
            "private_networking",
            "backups",
            "ipv6",
            "metadata"
          ],
          "available": true
        },
        "locked": false
      }
    ]
'''

import json
import os

from ansible.module_utils.basic import env_fallback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


class Response(object):

    def __init__(self, resp, info):
        self.body = None
        if resp:
            self.body = resp.read()
        self.info = info

    @property
    def json(self):
        if not self.body:
            if "body" in self.info:
                return json.loads(self.info["body"])
            return None
        try:
            return json.loads(self.body)
        except ValueError:
            return None

    @property
    def status_code(self):
        return self.info["status"]


class Rest(object):

    def __init__(self, module, headers):
        self.module = module
        self.headers = headers
        self.baseurl = 'https://api.digitalocean.com/v2'

    def _url_builder(self, path):
        if path[0] == '/':
            path = path[1:]
        return '%s/%s' % (self.baseurl, path)

    def send(self, method, path, data=None, headers=None):
        url = self._url_builder(path)
        data = self.module.jsonify(data)
        timeout = self.module.params['timeout']

        resp, info = fetch_url(self.module, url, data=data, headers=self.headers, method=method, timeout=timeout)

        # Exceptions in fetch_url may result in a status -1, the ensures a
        if info['status'] == -1:
            self.module.fail_json(msg=info['msg'])

        return Response(resp, info)

    def get(self, path, data=None, headers=None):
        return self.send('GET', path, data, headers)

    def put(self, path, data=None, headers=None):
        return self.send('PUT', path, data, headers)

    def post(self, path, data=None, headers=None):
        return self.send('POST', path, data, headers)

    def delete(self, path, data=None, headers=None):
        return self.send('DELETE', path, data, headers)


def core(module):
    api_token = module.params['oauth_token']

    rest = Rest(module, {'Authorization': 'Bearer {0}'.format(api_token),
                         'Content-type': 'application/json'})

    page = 1
    has_next = True
    floating_ips = []
    while has_next or 200 != status_code:
        response = rest.get("floating_ips?page={0}&per_page=20".format(page))
        status_code = response.status_code
        # stop if any error during pagination
        if 200 != status_code:
            break
        page = page + 1
        floating_ips.extend(response.json["floating_ips"])
        has_next = "pages" in response.json["links"] and "next" in response.json["links"]["pages"]

    if status_code == 200:
        module.exit_json(changed=False, floating_ips=floating_ips)
    else:
        module.fail_json(msg="Error fecthing facts [{0}: {1}]".format(
            status_code, response.json["message"]))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            oauth_token=dict(
                no_log=True,
                # Support environment variable for DigitalOcean OAuth Token
                fallback=(env_fallback, ['DO_API_TOKEN', 'DO_API_KEY', 'DO_OAUTH_TOKEN']),
                required=True,
            ),
            validate_certs=dict(type='bool', default=True),
            timeout=dict(type='int', default=30),
        ),
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
