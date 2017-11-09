# 2016, James Turner <turnerjsm@gmail.com>
#This lookup plugin is used to find AWS service and or region subnet ranges.
#e.g:
# $ cat playbook.yml
# - name: Test Playbook
#   hosts: localhost
#   connection: local
#   gather_facts: no
#   vars:
#      contents: "{{ lookup('aws_ranges', region='ap-southeast-2', service='EC2', wantlist=True) }}"
#
#   tasks:
#
#      - debug: msg=" {% for addr in contents %} {{ addr }} {% endfor %}"
#
# $ ansible-playbook playbook.yml
#  [WARNING]: provided hosts list is empty, only localhost is available
#
#
# PLAY [Test Playbook] ***********************************************************
#
# TASK [debug] *******************************************************************
# ok: [localhost] => {
#     "msg": "  52.62.0.0/15  52.64.0.0/17  52.64.128.0/17  52.65.0.0/16  52.95.241.0/24  52.95.255.16/28  54.66.0.0/16  54.79.0.0/16  54.153.128.0/17  54.206.0.0/16  54.252.0.0/16  54.253.0.0/16 "
# }
#
# PLAY RECAP *********************************************************************
# localhost                  : ok=1    changed=0    unreachable=0    failed=0
#




from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

REQUESTS_INSTALLED = False

try:
    import requests
    REQUESTS_INSTALLED = True
except ImportError:
    REQUESTS_INSTALLED = False

class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):
        if not REQUESTS_INSTALLED:
            raise AnsibleError('Python Requests must be installed')
        amazon_url = 'https://ip-ranges.amazonaws.com/ip-ranges.json'
        result_list = []

        def find_prefixes(kwargs, amazon_url):
            try:
                amazon_response= requests.get(amazon_url).json()['prefixes']
            except Exception as e:
                raise AnsibleError("Encounted Exception while looking up Prefix dictionary: %s" % e)
            if 'region' in kwargs:
                region = kwargs['region']
                amazon_response = list(item for item in amazon_response if item['region']==region)
            if 'service' in kwargs:
                service = str.upper(kwargs['service'])
                amazon_response = list(item for item in amazon_response if item['service']== service)


            result_list = []
            for item in amazon_response:
                result_list.append(item['ip_prefix'])
            return result_list

        result_list = find_prefixes(kwargs,amazon_url)
        return result_list


