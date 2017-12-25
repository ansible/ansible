#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Chris Houseknecht <@chouseknecht>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function


__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''

module: openshift_scale

short_description: Set a new size for a Deployment, ReplicaSet, Replication Controller, or Job.

version_added: "2.5"

author: "Chris Houseknecht (@chouseknecht)"

description:
  - Similar to the oc scale command. Use to set the number of replicas for a Deployment, ReplicatSet,
    or Replication Controller, or the parallelism attribute of a Job. Supports check mode.

extends_documentation_fragment:
  - k8s_name_options
  - k8s_auth_options
  - k8s_resource_options
  - k8s_scale_options

requirements:
    - "python >= 2.7"
    - "openshift >= 0.3"
    - "PyYAML >= 3.11"
'''

EXAMPLES = '''
- name: Scale deployment config up
  openshift_scale:
    api_version: v1
    kind: DeploymentConfig
    name: elastic
    namespace: myproject
    replicas: 3
    wait_time: 60

- name: Scale deployment config down
  openshift_scale:
    api_version: v1
    kind: DeploymentConfig
    name: elastic
    namespace: myproject
    replicas: 2

- name: Scale deployment config from src file without waiting
  openshift_scale:
    src: /myproject/elastic_deployment.yml
    replicas: 3
    wait: no
'''

RETURN = '''
result:
  description:
  - If a change was made, will be set to the patched object. Otherwise, will be set to the existing object.
  returned: success
  type: dict
'''

EXAMPLES = '''
- name: Scale deployment config up
  openshift_scale:
    api_version: v1
    kind: DeploymentConfig
    name: elastic
    namespace: myproject
    replicas: 3

- name: Scale deployment to 2 when current replicas is 3
  openshift_scale:
    api_version: v1
    kind: DeploymentConfig
    name: elastic
    namespace: myproject
    current_replicas: 3
    replicas: 2

- name: Scale current replicas when resource version matches
  openshift_scale:
    api_version: v1
    kind: DeploymentConfig
    name: elastic
    namespace: myproject
    resource_version: '31245'
    replicas: 3

# To use an API with '/' in the name, you will need
- name: Increase the parallelism for a job
  openshift_scale:
    api_version: batch/v1
    kind: job
    name: pi-with-timeout
    namespace: testing
    replicas: 2

- name: Scale deployment config from src file without waiting
  openshift_scale:
    src: /myproject/elastic_deployment.yml
    replicas: 3
    wait: no

'''

RETURN = '''
result:
  description:
  - If a change was made, will return the patched object, otherwise returns the existing object.
  returned: success
  type: dict
'''

from ansible.module_utils.k8s.scale import OpenShiftAnsibleScaleModule


def main():
    OpenShiftAnsibleScaleModule().execute_module()


if __name__ == '__main__':
    main()
