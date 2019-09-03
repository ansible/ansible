#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Till Klampaeckel (@till)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.1'
}

DOCUMENTATION = '''
---
module: grafana_dashboard_download
author:
  - Till Klampaeckel (@till)
version_added: "2.10"
short_description: Download Grafana dashboards
description:
  - Download Grafana dashboards (from Grafana.com), so they can be used with grafana_dashboard.
options:
  id:
    description:
      - The dashboard ID.
    type: int
    required: true
    aliases: [ dashboard_id ]
  revision:
    description:
      - The dashboard revision.
    type: int
    required: true
    aliases: [ dashboard_revision ]
  state:
    description:
      - State of the dashboard.
    required: true
    choices: [ absent, present ]
    default: present
    type: str
  path:
    description:
      - The path where to store the json file containing the Grafana dashboard.
    type: path
  overwrite:
    description:
      - Override existing dashboard when state is present.
    type: bool
    default: 'no'
  url:
    description:
      - The Grafana URL — most likely grafana.com.
    required: true
    default: https://grafana.com/api
    aliases: [ grafana_url ]
    type: str
'''

EXAMPLES = '''
- hosts: localhost
  connection: local
  tasks:
    - name: Download a dashboard to /tmp/dashboards/10645.json
      grafana_dashboard_download:
        id: 10645
        revision: 1
        path: /tmp/dashboards

    - name: Delete a dashboard in /tmp/dashboards/10645.json
      grafana_dashboard_download:
        id: 10645
        state: absent
        path: /tmp/dashboards
'''

RETURN = '''
---
path:
  description: The complete path to the dashboard.
  returned: success
  type: str
  sample: /tmp/dashboards/10645.json
'''

import json
import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url, url_argument_spec
from ansible.module_utils._text import to_native

__metaclass__ = type


class GrafanaPathException(Exception):
    pass


class GrafanaAPIException(Exception):
    pass


def grafana_dashboard_file(path, id):
    return os.path.join(path, id, '.json')


def grafana_dashboard_exists(path, id):
    return os.path.isfile(grafana_dashboard_file(path, id))


def grafana_download_dashboard(module, data):
    grafana_url = data['grafana_url']
    id = data['id']
    revision = data['revision']

    dashboard_file = grafana_dashboard_file(data['path'], data['id'])

    result = {}

    if grafana_dashboard_exists(data['path'], id) and data['overwrite'] is False:
        result['msg'] = 'Dashboard %d already in path. Set overwrite to re-download.'
        result['path'] = dashboard_file
        result['changed'] = False
        return result

    # download dashboad
    r, info = fetch_url(module, '%s/api/dashboards/%d/revisions/%d/download' % (data['grafana_url'], id, revision), method='GET')
    body = json.loads(info['body'])
    if info['status'] != 200:
        raise GrafanaAPIException("Could not download dashboard %d at rev %d: %s" % (id, revision, body['message']))

    # save to file
    try:
        with open(dashboard_file, 'w') as handle:
            handle.write(body)
            handle.close()
    except Exception as e:
        raise GrafanaPathException("Can't write json file %s" % to_native(e))

    result['msg'] = 'Dashboard %d at revision %d saved' % (id, revision)
    result['path'] = dashboard_file
    result['changed'] = True

    return result


def grafana_delete_dashboard(module, data):
    path = data['path']
    id = data['id']

    # test if the dashboard file exists
    dashboard_exists, dashboard = grafana_dashboard_exists(module, path, id)

    dashboard_file = grafana_dashboard_file(path, id)

    if dashboard_exists is True:
        # delete
        os.remove(dashboard_file)
        result = {
            'msg': 'Dashboard removed',
            'path': dashboard_file,
            'changed': True,
        }
    else:
        # dashboard does not exist, do nothing
        result = {
            'msg': "Dashboard %d does not exist in '%s'." % (id, path),
            'path': dashboard_file,
            'changed': False,
        }

    return result


def main():
    argument_spec = dict()

    # remove unnecessary arguments
    argument_spec.update(
        state=dict(choices=['present', 'absent'], default='present'),
        url=dict(aliases=['grafana_url'], default='https://grafana.com/api'),
        id=dict(aliases=['dashboard_id'], type='int', required=True),
        revision=dict(aliases=['dashboard_revision'], type='int', required=True),
        path=dict(type='path', required=True),
        overwrite=dict(type='bool', default=False),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
        required_together=[['url_username', 'url_password']],
        mutually_exclusive=[['grafana_user', 'grafana_api_key']],
    )

    try:
        if os.path.isdir(module.params['path']) is False:
            raise GrafanaPathException("Path %s does not exists." % module.params['path'])

        if module.params['state'] == 'present':
            result = grafana_download_dashboard(module, module.params)
        else:
            result = grafana_delete_dashboard(module, module.params)
    except GrafanaAPIException as e:
        module.fail_json(
            failed=True,
            msg="error : %s" % to_native(e)
        )
        return
    except GrafanaPathException as e:
        module.fail_json(
            failed=True,
            msg="error : %s" % to_native(e)
        )

    module.exit_json(
        failed=False,
        **result
    )
    return


if __name__ == '__main__':
    main()
