# (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
lookup: grafana_dashboard
author: Thierry Salle (@seuf)
version_added: "2.7"
short_description: list or search grafana dashboards
description:
  - This lookup returns a list of grafana dashboards with possibility to filter them by query.
options:
  grafana_url:
    description: url of grafana.
    env:
      - name: GRAFANA_URL
    default: http://127.0.0.1:3000
  grafana_api_key:
    description:
      - api key of grafana.
      - when C(grafana_api_key) is set, the options C(grafan_user), C(grafana_password) and C(grafana_org_id) are ignored.
      - Attention, please remove the two == at the end of the grafana_api_key
      - because ansible lookup plugins options are split on = (see example).
    env:
      - name: GRAFANA_API_KEY
  grafana_user:
    description: grafana authentication user.
    env:
      - name: GRAFANA_USER
    default: admin
  grafana_password:
    description:  grafana authentication password.
    env:
      - name: GRAFANA_PASSWORD
    default: admin
  grafana_org_id:
    description: grafana organisation id.
    env:
      - name: GRAFANA_ORG_ID
    default: 1
  search:
    description: optional filter for dashboard search.
    env:
      - name: GRAFANA_DASHBOARD_SEARCH
"""

EXAMPLES = """
- name: get project foo grafana dashboards
  set_fact:
    grafana_dashboards: "{{ lookup('grafana_dashboard', 'grafana_url=http://grafana.company.com grafana_user=admin grafana_password=admin search=foo') }}"

- name: get all grafana dashboards
  set_fact:
    grafana_dashboards: "{{ lookup('grafana_dashboard', 'grafana_url=http://grafana.company.com grafana_api_key=' ~ grafana_api_key|replace('==', '')) }}"
"""

import base64
import json
import os
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.urls import open_url
from ansible.module_utils._text import to_bytes, to_native
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.utils.display import Display

display = Display()


ANSIBLE_GRAFANA_URL = 'http://127.0.0.1:3000'
ANSIBLE_GRAFANA_API_KEY = None
ANSIBLE_GRAFANA_USER = 'admin'
ANSIBLE_GRAFANA_PASSWORD = 'admin'
ANSIBLE_GRAFANA_ORG_ID = 1
ANSIBLE_GRAFANA_DASHBOARD_SEARCH = None

if os.getenv('GRAFANA_URL') is not None:
    ANSIBLE_GRAFANA_URL = os.environ['GRAFANA_URL']

if os.getenv('GRAFANA_API_KEY') is not None:
    ANSIBLE_GRAFANA_API_KEY = os.environ['GRAFANA_API_KEY']

if os.getenv('GRAFANA_USER') is not None:
    ANSIBLE_GRAFANA_USER = os.environ['GRAFANA_USER']

if os.getenv('GRAFANA_PASSWORD') is not None:
    ANSIBLE_GRAFANA_PASSWORD = os.environ['GRAFANA_PASSWORD']

if os.getenv('GRAFANA_ORG_ID') is not None:
    ANSIBLE_GRAFANA_ORG_ID = os.environ['GRAFANA_ORG_ID']

if os.getenv('GRAFANA_DASHBOARD_SEARCH') is not None:
    ANSIBLE_GRAFANA_DASHBOARD_SEARCH = os.environ['GRAFANA_DASHBOARD_SEARCH']


class GrafanaAPIException(Exception):
    pass


class GrafanaAPI:
    def __init__(self, **kwargs):
        self.grafana_url = kwargs.get('grafana_url', ANSIBLE_GRAFANA_URL)
        self.grafana_api_key = kwargs.get('grafana_api_key', ANSIBLE_GRAFANA_API_KEY)
        self.grafana_user = kwargs.get('grafana_user', ANSIBLE_GRAFANA_USER)
        self.grafana_password = kwargs.get('grafana_password', ANSIBLE_GRAFANA_PASSWORD)
        self.grafana_org_id = kwargs.get('grafana_org_id', ANSIBLE_GRAFANA_ORG_ID)
        self.search = kwargs.get('search', ANSIBLE_GRAFANA_DASHBOARD_SEARCH)

    def grafana_switch_organisation(self, headers):
        try:
            r = open_url('%s/api/user/using/%s' % (self.grafana_url, self.grafana_org_id), headers=headers, method='POST')
        except HTTPError as e:
            raise GrafanaAPIException('Unable to switch to organization %s : %s' % (self.grafana_org_id, to_native(e)))
        if r.getcode() != 200:
            raise GrafanaAPIException('Unable to switch to organization %s : %s' % (self.grafana_org_id, str(r.getcode())))

    def grafana_headers(self):
        headers = {'content-type': 'application/json; charset=utf8'}
        if self.grafana_api_key:
            headers['Authorization'] = "Bearer %s==" % self.grafana_api_key
        else:
            auth = base64.b64encode(to_bytes('%s:%s' % (self.grafana_user, self.grafana_password)).replace('\n', ''))
            headers['Authorization'] = 'Basic %s' % auth
            self.grafana_switch_organisation(headers)

        return headers

    def grafana_list_dashboards(self):
        # define http headers
        headers = self.grafana_headers()

        dashboard_list = []
        try:
            if self.search:
                r = open_url('%s/api/search?query=%s' % (self.grafana_url, self.search), headers=headers, method='GET')
            else:
                r = open_url('%s/api/search/' % self.grafana_url, headers=headers, method='GET')
        except HTTPError as e:
            raise GrafanaAPIException('Unable to search dashboards : %s' % to_native(e))
        if r.getcode() == 200:
            try:
                dashboard_list = json.loads(r.read())
            except Exception as e:
                raise GrafanaAPIException('Unable to parse json list %s' % to_native(e))
        else:
            raise GrafanaAPIException('Unable to list grafana dashboards : %s' % str(r.getcode()))

        return dashboard_list


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        grafana_args = terms[0].split(' ')
        grafana_dict = {}
        ret = []

        for param in grafana_args:
            try:
                key, value = param.split('=')
            except ValueError:
                raise AnsibleError("grafana_dashboard lookup plugin needs key=value pairs, but received %s" % terms)
            grafana_dict[key] = value

        grafana = GrafanaAPI(**grafana_dict)

        ret = grafana.grafana_list_dashboards()

        return ret
