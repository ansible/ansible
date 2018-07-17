#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Thierry Sallé (@seuf)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.1'
}

DOCUMENTATION = '''
---
module: grafana_dashboard
author:
  - Thierry Sallé (@tsalle)
version_added: "2.5"
short_description: Manage Grafana dashboards
description:
  - Create, update, delete, export Grafana dashboards via API.
options:
  grafana_url:
    description:
      - The Grafana URL.
    required: true
  grafana_user:
    description:
      - The Grafana API user.
    default: admin
  grafana_password:
    description:
      - The Grafana API password.
    default: admin
  grafana_api_key:
    description:
      - The Grafana API key.
      - If set, I(grafana_user) and I(grafana_password) will be ignored.
  org_id:
    description:
      - The Grafana Organisation ID where the dashboard will be imported / exported.
      - Not used when I(grafana_api_key) is set, because the grafana_api_key only belongs to one organisation..
    default: 1
  state:
    description:
      - State of the dashboard.
    required: true
    choices: [ absent, export, present ]
    default: present
  slug:
    description:
      - slug of the dashboard. It's the friendly url name of the dashboard.
      - When C(state) is C(present), this parameter can override the slug in the meta section of the json file.
      - If you want to import a json dashboard exported directly from the interface (not from the api),
        you have to specify the slug parameter because there is no meta section in the exported json.
  path:
    description:
      - The path to the json file containing the Grafana dashboard to import or export.
  overwrite:
    description:
      - Override existing dashboard when state is present.
    type: bool
    default: 'no'
  message:
    description:
      - Set a commit message for the version history.
      - Only used when C(state) is C(present).
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated.
      - This should only be used on personally controlled sites using self-signed certificates.
    type: bool
    default: 'yes'
'''

EXAMPLES = '''
- name: Import Grafana dashboard foo
  grafana_dashboard:
    grafana_url: http://grafana.company.com
    grafana_api_key: XXXXXXXXXXXX
    state: present
    message: Updated by ansible
    overwrite: yes
    path: /path/to/dashboards/foo.json

- name: Export dashboard
  grafana_dashboard:
    grafana_url: http://grafana.company.com
    grafana_api_key: XXXXXXXXXXXX
    state: export
    slug: foo
    path: /path/to/dashboards/foo.json
'''

RETURN = '''
---
slug:
  description: slug of the created / deleted / exported dashboard.
  returned: success
  type: string
  sample: foo
'''

import json
import base64

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_bytes

__metaclass__ = type


class GrafanaAPIException(Exception):
    pass


class GrafanaMalformedJson(Exception):
    pass


class GrafanaExportException(Exception):
    pass


def grafana_switch_organisation(module, grafana_url, org_id, headers):
    r, info = fetch_url(module, '%s/api/user/using/%s' % (grafana_url, org_id), headers=headers, method='POST')
    if info['status'] != 200:
        raise GrafanaAPIException('Unable to switch to organization %s : %s' % (org_id, info))


def grafana_dashboard_exists(module, grafana_url, slug, headers):
    dashboard_exists = False
    dashboard = {}
    r, info = fetch_url(module, '%s/api/dashboards/db/%s' % (grafana_url, slug), headers=headers, method='GET')
    if info['status'] == 200:
        dashboard_exists = True
        try:
            dashboard = json.loads(r.read())
        except Exception as e:
            raise GrafanaMalformedJson(e)
    elif info['status'] == 404:
        dashboard_exists = False
    else:
        raise GrafanaAPIException('Unable to get dashboard %s : %s' % (slug, info))

    return dashboard_exists, dashboard


def grafana_create_dashboard(module, data):

    # define data payload for grafana API
    try:
        with open(data['path'], 'r') as json_file:
            payload = json.load(json_file)
    except Exception as e:
        raise GrafanaMalformedJson("Can't load json file %s" % str(e))

    # define http header
    headers = {'content-type': 'application/json; charset=utf8'}
    if 'grafana_api_key' in data and data['grafana_api_key']:
        headers['Authorization'] = "Bearer %s" % data['grafana_api_key']
    else:
        auth = base64.b64encode(to_bytes('%s:%s' % (data['grafana_user'], data['grafana_password'])).replace('\n', ''))
        headers['Authorization'] = 'Basic %s' % auth
        grafana_switch_organisation(module, data['grafana_url'], data['org_id'], headers)

    if data.get('slug'):
        slug = data['slug']
    elif 'meta' in payload and 'slug' in payload['meta']:
        slug = payload['meta']['slug']
    else:
        raise GrafanaMalformedJson('No slug found in json')

    # test if dashboard already exists
    dashboard_exists, dashboard = grafana_dashboard_exists(module, data['grafana_url'], slug, headers=headers)

    result = {}
    if dashboard_exists is True:
        if dashboard == payload:
            # unchanged
            result['slug'] = data['slug']
            result['msg'] = "Dashboard %s unchanged." % data['slug']
            result['changed'] = False
        else:
            # update
            if 'overwrite' in data and data['overwrite']:
                payload['overwrite'] = True
            if 'message' in data and data['message']:
                payload['message'] = data['message']

            r, info = fetch_url(module, '%s/api/dashboards/db' % data['grafana_url'], data=json.dumps(payload), headers=headers, method='POST')
            if info['status'] == 200:
                result['slug'] = slug
                result['msg'] = "Dashboard %s updated" % slug
                result['changed'] = True
            else:
                body = json.loads(info['body'])
                raise GrafanaAPIException('Unable to update the dashboard %s : %s' % (slug, body['message']))
    else:
        # create
        if 'dashboard' not in payload:
            payload = {'dashboard': payload}
        r, info = fetch_url(module, '%s/api/dashboards/db' % data['grafana_url'], data=json.dumps(payload), headers=headers, method='POST')
        if info['status'] == 200:
            result['msg'] = "Dashboard %s created" % slug
            result['changed'] = True
            result['slug'] = slug
        else:
            raise GrafanaAPIException('Unable to create the new dashboard %s : %s - %s.' % (slug, info['status'], info))

    return result


def grafana_delete_dashboard(module, data):

    # define http headers
    headers = {'content-type': 'application/json'}
    if 'grafana_api_key' in data and data['grafana_api_key']:
        headers['Authorization'] = "Bearer %s" % data['grafana_api_key']
    else:
        auth = base64.b64encode(to_bytes('%s:%s' % (data['grafana_user'], data['grafana_password'])).replace('\n', ''))
        headers['Authorization'] = 'Basic %s' % auth
        grafana_switch_organisation(module, data['grafana_url'], data['org_id'], headers)

    # test if dashboard already exists
    dashboard_exists, dashboard = grafana_dashboard_exists(module, data['grafana_url'], data['slug'], headers=headers)

    result = {}
    if dashboard_exists is True:
        # delete
        r, info = fetch_url(module, '%s/api/dashboards/db/%s' % (data['grafana_url'], data['slug']), headers=headers, method='DELETE')
        if info['status'] == 200:
            result['msg'] = "Dashboard %s deleted" % data['slug']
            result['changed'] = True
            result['slug'] = data['slug']
        else:
            raise GrafanaAPIException('Unable to update the dashboard %s : %s' % (data['slug'], info))
    else:
        # dashboard does not exist, do nothing
        result = {'msg': "Dashboard %s does not exist." % data['slug'],
                  'changed': False,
                  'slug': data['slug']}

    return result


def grafana_export_dashboard(module, data):

    # define http headers
    headers = {'content-type': 'application/json'}
    if 'grafana_api_key' in data and data['grafana_api_key']:
        headers['Authorization'] = "Bearer %s" % data['grafana_api_key']
    else:
        auth = base64.b64encode(to_bytes('%s:%s' % (data['grafana_user'], data['grafana_password'])).replace('\n', ''))
        headers['Authorization'] = 'Basic %s' % auth
        grafana_switch_organisation(module, data['grafana_url'], data['org_id'], headers)

    # test if dashboard already exists
    dashboard_exists, dashboard = grafana_dashboard_exists(module, data['grafana_url'], data['slug'], headers=headers)

    if dashboard_exists is True:
        try:
            with open(data['path'], 'w') as f:
                f.write(json.dumps(dashboard))
        except Exception as e:
            raise GrafanaExportException("Can't write json file : %s" % str(e))
        result = {'msg': "Dashboard %s exported to %s" % (data['slug'], data['path']),
                  'slug': data['slug'],
                  'changed': True}
    else:
        result = {'msg': "Dashboard %s does not exist." % data['slug'],
                  'slug': data['slug'],
                  'changed': False}

    return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['present', 'absent', 'export'],
                       default='present'),
            grafana_url=dict(required=True),
            grafana_user=dict(default='admin'),
            grafana_password=dict(default='admin', no_log=True),
            grafana_api_key=dict(type='str', no_log=True),
            org_id=dict(default=1, type='int'),
            slug=dict(type='str'),
            path=dict(type='str'),
            overwrite=dict(type='bool', default=False),
            message=dict(type='str'),
            validate_certs=dict(type='bool', default=True)
        ),
        supports_check_mode=False,
        required_together=[['grafana_user', 'grafana_password', 'org_id']],
        mutually_exclusive=[['grafana_user', 'grafana_api_key']],
    )

    try:
        if module.params['state'] == 'present':
            result = grafana_create_dashboard(module, module.params)
        elif module.params['state'] == 'absent':
            result = grafana_delete_dashboard(module, module.params)
        else:
            result = grafana_export_dashboard(module, module.params)
    except GrafanaAPIException as e:
        module.fail_json(
            failed=True,
            msg="error : %s" % e
        )
        return
    except GrafanaMalformedJson as e:
        module.fail_json(
            failed=True,
            msg="error : json file does not contain a meta section with a slug parameter, or you did'nt specify the slug parameter"
        )
        return
    except GrafanaExportException as e:
        module.fail_json(
            failed=True,
            msg="error : json file cannot be written : %s" % str(e)
        )
        return

    module.exit_json(
        failed=False,
        **result
    )
    return

if __name__ == '__main__':
    main()
