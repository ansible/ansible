# (c) 2015, Ensighten <infra@ensighten.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: credstash
    version_added: "2.0"
    short_description: retrieve secrets from Credstash on AWS
    requirements:
      - credstash (python library)
    description:
      - "Credstash is a small utility for managing secrets using AWS's KMS and DynamoDB: https://github.com/fugue/credstash"
    options:
      _terms:
        description: term or list of terms to lookup in the credit store
        type: list
        required: True
      table:
        description: name of the credstash table to query
        default: 'credential-store'
        required: True
      version:
        description: Credstash version
      region:
        description: AWS region
      profile_name:
        description: AWS profile to use for authentication
        env:
          - name: AWS_PROFILE
      aws_access_key_id:
        description: AWS access key ID
        env:
          - name: AWS_ACCESS_KEY_ID
      aws_secret_access_key:
        description: AWS access key
        env:
          - name: AWS_SECRET_ACCESS_KEY
      aws_session_token:
        description: AWS session token
        env:
          - name: AWS_SESSION_TOKEN
"""

EXAMPLES = """
- name: first use credstash to store your secrets
  shell: credstash put my-github-password secure123

- name: "Test credstash lookup plugin -- get my github password"
  debug: msg="Credstash lookup! {{ lookup('credstash', 'my-github-password') }}"

- name: "Test credstash lookup plugin -- get my other password from us-west-1"
  debug: msg="Credstash lookup! {{ lookup('credstash', 'my-other-password', region='us-west-1') }}"

- name: "Test credstash lookup plugin -- get the company's github password"
  debug: msg="Credstash lookup! {{ lookup('credstash', 'company-github-password', table='company-passwords') }}"

- name: Example play using the 'context' feature
  hosts: localhost
  vars:
    context:
      app: my_app
      environment: production
  tasks:

  - name: "Test credstash lookup plugin -- get the password with a context passed as a variable"
    debug: msg="{{ lookup('credstash', 'some-password', context=context) }}"

  - name: "Test credstash lookup plugin -- get the password with a context defined here"
    debug: msg="{{ lookup('credstash', 'some-password', context=dict(app='my_app', environment='production')) }}"
"""

RETURN = """
  _raw:
    description:
      - value(s) stored in Credstash
"""

import os

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

CREDSTASH_INSTALLED = False

try:
    import credstash
    CREDSTASH_INSTALLED = True
except ImportError:
    CREDSTASH_INSTALLED = False


class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):

        if not CREDSTASH_INSTALLED:
            raise AnsibleError('The credstash lookup plugin requires credstash to be installed.')

        ret = []
        for term in terms:
            try:
                version = kwargs.pop('version', '')
                region = kwargs.pop('region', None)
                table = kwargs.pop('table', 'credential-store')
                profile_name = kwargs.pop('profile_name', os.getenv('AWS_PROFILE', None))
                aws_access_key_id = kwargs.pop('aws_access_key_id', os.getenv('AWS_ACCESS_KEY_ID', None))
                aws_secret_access_key = kwargs.pop('aws_secret_access_key', os.getenv('AWS_SECRET_ACCESS_KEY', None))
                aws_session_token = kwargs.pop('aws_session_token', os.getenv('AWS_SESSION_TOKEN', None))
                kwargs_pass = {'profile_name': profile_name, 'aws_access_key_id': aws_access_key_id,
                               'aws_secret_access_key': aws_secret_access_key, 'aws_session_token': aws_session_token}
                val = credstash.getSecret(term, version, region, table, context=kwargs, **kwargs_pass)
            except credstash.ItemNotFound:
                raise AnsibleError('Key {0} not found'.format(term))
            except Exception as e:
                raise AnsibleError('Encountered exception while fetching {0}: {1}'.format(term, e.message))
            ret.append(val)

        return ret
