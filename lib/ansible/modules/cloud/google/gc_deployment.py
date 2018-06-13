#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Tomas Mazak <tomas@valec.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: gc_deployment
version_added: 2.7
short_description: Manage Google Cloud Deployment Manager deployments
description:
  - Create, update or delete Google Cloud Deployment Manager deployments. More information at
    U(https://cloud.google.com/deployment-manager/).
author:
  - Tomas Mazak (@tomas-mazak)
requirements:
  - PyYAML
  - google-api-python-client
options:
  name:
    description:
      - Name of the deployment (used as the unique identifier of the deployment within a project)
    required: true

  config:
    description:
      - YAML formatted manifest of the deployment.
        See U(https://cloud.google.com/deployment-manager/docs/configuration/syntax-reference) for details.
    default: ''

  state:
    description:
      - Desired state of the resource
    default: present
    choices: [present, absent]

  create_policy:
    description:
      - Deployment Manager create policy.
        See U(https://cloud.google.com/deployment-manager/docs/deployments/updating-deployments) for details.
    default: create_or_acquire
    choices: [acquire, create_or_acquire]

  delete_policy:
    description:
      - Deployment Manager delete policy.
        See U(https://cloud.google.com/deployment-manager/docs/deployments/updating-deployments) for details.
    default: delete
    choices: [abandon, delete]

  wait:
    description:
      - Whether to poll for the deployment operation to finish and report success/failure. By default,
        the module exits right after initiating the operation
    type: bool
    default: false

  wait_timeout:
    description:
      - If I(wait) is set, this specifies the maximum amount of time in seconds to wait before an error is returned.
    default: 300

  credentials_file:
    description:
      - Path to a Google service account credentials JSON file. If not specified, value from GCE_CREDENTIALS_FILE_PATH
        environment variable will be used.

  project_id:
    description:
      - Google Cloud project ID to use. If not specified, value from GCE_PROJECT environment variable will be used.
'''

EXAMPLES = '''
# Create a simple GCE machine with public IP
- gc_deployment:
    name: simple-vm
    config: |
      resources:
      - type: compute.v1.instance
        name: simple-vm
        properties:
          zone: europe-west2-a
          machineType: https://www.googleapis.com/compute/v1/projects/myproject/zones/europe-west2-a/machineTypes/f1-micro
          disks:
          - deviceName: boot
            type: PERSISTENT
            boot: true
            autoDelete: true
            initializeParams:
              sourceImage: https://www.googleapis.com/compute/v1/projects/debian-cloud/global/images/family/debian-9
          networkInterfaces:
          - network: https://www.googleapis.com/compute/v1/projects/myproject/global/networks/default
            accessConfigs:
            - name: External NAT
              type: ONE_TO_ONE_NAT

# Load config from Jinja template
# (Ansible Jinja temlate, Deployment Manager native templating is NOT supported)
- gc_deployment:
    name: kube-cluster
    config: "{{ lookup('template', 'kube-cluster.yml.j2') }}"

# Wait (max 1 minute) for the deployment to be applied before continuing
- gc_deployment:
    name: my-deployment
    config: "{{ my_deployment_config }}"
    wait: yes
    wait_timeout: 60
'''

RETURN = '''
msg:
  description: Brief report of what was done to achieve the desired state
  returned: always
  type: string
  sample: Deployment updated
'''

import os
import time

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    from apiclient.errors import HttpError
    from apiclient.discovery import build
    from google.oauth2 import service_account
    HAS_APICLIENT = True
except ImportError:
    HAS_APICLIENT = False

from ansible.module_utils.basic import AnsibleModule


class Deployment(object):

    class Error(Exception):
        def __init__(self, err):
            self.err = err

        def __str__(self):
            return '\n'.join(['%s(%s): %s' % (e.get('code', 'ERROR'), e.get('location', ''), e.get('message', ''))
                              for e in self.err['errors']])

    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.config = kwargs['config']
        self.create_policy = kwargs['create_policy'].upper()
        self.delete_policy = kwargs['delete_policy'].upper()
        self.credentials_file = kwargs['credentials_file'] or os.environ.get('GCE_CREDENTIALS_FILE_PATH', None)
        self.project_id = kwargs['project_id'] or os.environ.get('GCE_PROJECT', None)

        if self.credentials_file is None or self.project_id is None:
            raise RuntimeError('Project ID and credentials file must be provided, see ansible-doc for details.')

        credentials = service_account.Credentials.from_service_account_file(self.credentials_file)
        self._api = build('deploymentmanager', 'v2', credentials=credentials)

        self._obj = None
        self._manifest = None
        try:
            self._obj = self._api.deployments().get(
                project=self.project_id,
                deployment=self.name
            ).execute()
            manifest_link = self._obj['manifest'] if 'manifest' in self._obj else self._obj['update']['manifest']
            self._manifest = self._api.manifests().get(
                project=self.project_id,
                deployment=self.name,
                manifest=manifest_link.split('/')[-1]
            ).execute()
        except HttpError as ex:
            if ex.resp.status != 404:
                raise

    def _body(self):
        body = {
            'name': self.name,
            'target': {
                'config': {
                    'content': self.config,
                },
            },
        }
        if self._obj is not None and 'fingerprint' in self._obj:
            body['fingerprint'] = self._obj['fingerprint']
        return body

    def _wait(self, operation, timeout):
        if timeout is None:
            return
        deadline = time.time() + timeout
        while True:
            op = self._api.operations().get(
                project=self.project_id,
                operation=operation
            ).execute()
            if op['status'] == 'DONE':
                if 'error' in op:
                    raise self.Error(op['error'])
                return
            if time.time() > deadline:
                raise TimeoutError('Operation did not finish within %d s timeout' % timeout)
            time.sleep(1)

    def exists(self):
        return self._obj is not None

    def current_config(self):
        if self._manifest is None:
            return ''
        return self._manifest['config']['content']

    def new_config(self):
        return self.config

    def modified(self):
        current_dict = yaml.load(self.current_config())
        new_dict = yaml.load(self.new_config())
        return current_dict != new_dict

    def create(self, wait=None):
        operation = self._api.deployments().insert(
            project=self.project_id,
            body=self._body()
        ).execute()
        self._wait(operation['name'], wait)

    def update(self, wait=None):
        operation = self._api.deployments().update(
            project=self.project_id,
            deployment=self.name,
            body=self._body(),
            createPolicy=self.create_policy,
            deletePolicy=self.delete_policy
        ).execute()
        self._wait(operation['name'], wait)

    def delete(self, wait=None):
        operation = self._api.deployments().delete(
            project=self.project_id,
            deployment=self.name,
            deletePolicy=self.delete_policy
        ).execute()
        self._wait(operation['name'], wait)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            config=dict(type='str', default=''),
            create_policy=dict(type='str', default='create_or_acquire', choices=['acquire', 'create_or_acquire']),
            delete_policy=dict(type='str', default='delete', choices=['abandon', 'delete']),
            wait=dict(type='bool', default=False),
            wait_timeout=dict(type='int', default=300),
            credentials_file=dict(type='str'),
            project_id=dict(type='str'),
        ),
        supports_check_mode=True,
    )

    state = module.params.get('state')
    wait = module.params.get('wait_timeout') if module.params.get('wait') else None

    if not HAS_YAML:
        module.fail_json(
            msg='PyYAML is required. Use "pip install --upgrade PyYAML" to resolve.'
        )

    if not HAS_APICLIENT:
        module.fail_json(
            msg='Google API client 1.7+ required. Use "pip install --upgrade google-api-python-client" to resolve.'
        )

    try:
        deployment = Deployment(**module.params)

        if state == 'present':
            if not deployment.exists():
                if not module.check_mode:
                    deployment.create(wait)
                module.exit_json(msg="Deployment created", changed=True,
                                 diff=dict(before='', after=deployment.new_config()))
            elif deployment.modified():
                if not module.check_mode:
                    deployment.update(wait)
                module.exit_json(msg="Deployment updated", changed=True,
                                 diff=dict(before=deployment.current_config(), after=deployment.new_config()))
            else:
                module.exit_json(msg="Deployment not modified", changed=False)

        elif state == 'absent':
            if deployment.exists():
                if not module.check_mode:
                    deployment.delete(wait)
                module.exit_json(msg="Deployment deleted", changed=True,
                                 diff=dict(before=deployment.current_config(), after=''))
            else:
                module.exit_json(msg="Deployment does not exist", changed=False)
    except (OSError, RuntimeError, Deployment.Error, HttpError) as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
