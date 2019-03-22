#!/usr/bin/env python

# Copyright (c) 2016, Hugh Ma <hugh.ma@flextronics.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

# Stacki inventory script
# Configure stacki.yml with proper auth information and place in the following:
#  - ../inventory/stacki.yml
#  - /etc/stacki/stacki.yml
#  - /etc/ansible/stacki.yml
# The stacki.yml file can contain entries for authentication information
# regarding the Stacki front-end node.
#
# use_hostnames uses hostname rather than interface ip as connection
#
#

"""
Example Usage:
    List Stacki Nodes
    $ ./stack.py --list


Example Configuration:
---
stacki:
  auth:
    stacki_user: admin
    stacki_password: abc12345678910
    stacki_endpoint: http://192.168.200.50/stack
use_hostnames: false
"""

import argparse
import os
import sys
import yaml
from distutils.version import StrictVersion

import json

try:
    import requests
except Exception:
    sys.exit('requests package is required for this inventory script')


CONFIG_FILES = ['/etc/stacki/stacki.yml', '/etc/ansible/stacki.yml']


def stack_auth(params):
    endpoint = params['stacki_endpoint']
    auth_creds = {'USERNAME': params['stacki_user'],
                  'PASSWORD': params['stacki_password']}

    client = requests.session()
    client.get(endpoint)

    init_csrf = client.cookies['csrftoken']

    header = {'csrftoken': init_csrf, 'X-CSRFToken': init_csrf,
              'Content-type': 'application/x-www-form-urlencoded'}

    login_endpoint = endpoint + "/login"

    login_req = client.post(login_endpoint, data=auth_creds, headers=header)

    csrftoken = login_req.cookies['csrftoken']
    sessionid = login_req.cookies['sessionid']

    auth_creds.update(CSRFTOKEN=csrftoken, SESSIONID=sessionid)

    return client, auth_creds


def stack_build_header(auth_creds):
    header = {'csrftoken': auth_creds['CSRFTOKEN'],
              'X-CSRFToken': auth_creds['CSRFTOKEN'],
              'sessionid': auth_creds['SESSIONID'],
              'Content-type': 'application/json'}

    return header


def stack_host_list(endpoint, header, client):

    stack_r = client.post(endpoint, data=json.dumps({"cmd": "list host"}),
                          headers=header)
    return json.loads(stack_r.json())


def stack_net_list(endpoint, header, client):

    stack_r = client.post(endpoint, data=json.dumps({"cmd": "list host interface"}),
                          headers=header)
    return json.loads(stack_r.json())


def format_meta(hostdata, intfdata, config):
    use_hostnames = config['use_hostnames']
    meta = dict(all=dict(hosts=list()),
                frontends=dict(hosts=list()),
                backends=dict(hosts=list()),
                _meta=dict(hostvars=dict()))

    # Iterate through list of dicts of hosts and remove
    # environment key as it causes conflicts
    for host in hostdata:
        del host['environment']
        meta['_meta']['hostvars'][host['host']] = host
        meta['_meta']['hostvars'][host['host']]['interfaces'] = list()

    # @bbyhuy to improve readability in next iteration

    for intf in intfdata:
        if intf['host'] in meta['_meta']['hostvars']:
            meta['_meta']['hostvars'][intf['host']]['interfaces'].append(intf)
            if intf['default'] is True:
                meta['_meta']['hostvars'][intf['host']]['ansible_host'] = intf['ip']
                if not use_hostnames:
                    meta['all']['hosts'].append(intf['ip'])
                    if meta['_meta']['hostvars'][intf['host']]['appliance'] != 'frontend':
                        meta['backends']['hosts'].append(intf['ip'])
                    else:
                        meta['frontends']['hosts'].append(intf['ip'])
                else:
                    meta['all']['hosts'].append(intf['host'])
                    if meta['_meta']['hostvars'][intf['host']]['appliance'] != 'frontend':
                        meta['backends']['hosts'].append(intf['host'])
                    else:
                        meta['frontends']['hosts'].append(intf['host'])
    return meta


def parse_args():
    parser = argparse.ArgumentParser(description='Stacki Inventory Module')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true',
                       help='List active hosts')
    group.add_argument('--host', help='List details about the specific host')

    return parser.parse_args()


def main():
    args = parse_args()

    if StrictVersion(requests.__version__) < StrictVersion("2.4.3"):
        sys.exit('requests>=2.4.3 is required for this inventory script')

    try:
        config_files = CONFIG_FILES
        config_files.append(os.path.dirname(os.path.realpath(__file__)) + '/stacki.yml')
        config = None
        for cfg_file in config_files:
            if os.path.isfile(cfg_file):
                stream = open(cfg_file, 'r')
                config = yaml.safe_load(stream)
                break
        if not config:
            sys.stderr.write("No config file found at {0}\n".format(config_files))
            sys.exit(1)
        client, auth_creds = stack_auth(config['stacki']['auth'])
        header = stack_build_header(auth_creds)
        host_list = stack_host_list(config['stacki']['auth']['stacki_endpoint'], header, client)
        intf_list = stack_net_list(config['stacki']['auth']['stacki_endpoint'], header, client)
        final_meta = format_meta(host_list, intf_list, config)
        print(json.dumps(final_meta, indent=4))
    except Exception as e:
        sys.stderr.write('%s\n' % e.message)
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
