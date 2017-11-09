# (c) 2016 James Turner <turnerjsm@gmail.com>
# (c) 2017 Ansible Project
# This lookup plugin is used to find AWS service and or region subnet ranges.
# $ cat playbook.yml
# - name: Test Playbook
#   hosts: localhost
#   connection: local
#   gather_facts: no
#   vars:
#      contents: "{{ lookup('aws_ranges', region='ap-southeast-2', service='EC2', wantlist=True) }}"
#
#   tasks:
#      - debug: msg="{% for addr in contents %}{{ addr }} {% endfor %}"
#      - debug: msg="{{ lookup('aws_ranges', region='us-east-1', service='S3') }}"
#
# $ ansible-playbook playbook.yml
#  [WARNING]: provided hosts list is empty, only localhost is available
#
#
# PLAY [Test Playbook] ***********************************************************
#
# TASK [debug] *******************************************************************
# ok: [localhost] => {
#     "msg": "52.62.0.0/15  52.64.0.0/17  52.64.128.0/17  52.65.0.0/16  52.95.241.0/24  52.95.255.16/28  54.66.0.0/16  54.79.0.0/16  54.153.128.0/17  54.206.0.0/16  54.252.0.0/16  54.253.0.0/16 "
# }
#
# TASK [debug] *******************************************************************
# ok: [localhost] => {
#     "msg": "52.92.16.0/20,52.216.0.0/15,54.231.0.0/17"
# }
#
# PLAY RECAP *********************************************************************
# localhost                  : ok=1    changed=0    unreachable=0    failed=0
#


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
from six.moves import urllib

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):
        try:
            resp = urllib.request.urlopen('https://ip-ranges.amazonaws.com/ip-ranges.json')
            amazon_response = json.load(resp)['prefixes']
        except getattr(json.decoder, 'JSONDecodeError', ValueError) as e:
            # on Python 3+, json.decoder.JSONDecodeError is raised for bad
            # JSON. On 2.x it's a ValueError
            raise AnsibleError("Could not decode AWS IP ranges: %s" % e)
        except Exception as e:
            raise AnsibleError("Encountered Exception while looking up Prefix dictionary: %s" % e)

        if 'region' in kwargs:
            region = kwargs['region']
            amazon_response = (item for item in amazon_response if item['region'] == region)
        if 'service' in kwargs:
            service = str.upper(kwargs['service'])
            amazon_response = (item for item in amazon_response if item['service'] == service)

        return [item['ip_prefix'] for item in amazon_response]
