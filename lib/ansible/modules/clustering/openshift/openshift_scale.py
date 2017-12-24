#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Chris Houseknecht <@chouseknecht>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

from ansible.module_utils.k8s.scale import OpenShiftAnsibleScaleModule

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
  - Similar to the `kubectl scale` command. Use to set the number of replicas for Deployment, ReplicatSet,
    Replication Controller, and Job objects. 

extends_documentation_fragment: kubernetes

options:
  replicas:
    description:
      - The desired number of replicas.
  current_replicas:
    description:
      - Only attempt to scale, if the number of existing replicas matches.
  resource_version:
    description:
      - Only attempt to scale, if the current object version matches.
  wait:
    description:
      - Wait for the scaling operation to complete.
    default: true
  wait_time:
    description:
      - Number of seconds to wait for the scaling operation to complete. If the number of available replicas is not
        reached within the allotted time, an error will result.
    default: 30

requirements:
    - "python >= 2.7"
    - "openshift >= 0.3"
    - "PyYAML >= 3.11"
'''

EXAMPLES = '''
- name: Scale deployment config up
  k8s_scale:
    api_version: v1
    kind: DeploymentConfig
    name: elastic
    namespace: myproject
    replicas: 3
    wait_time: 60

- name: Scale deployment config down
  k8s_scale:
    api_version: v1
    kind: DeploymentConfig
    name: elastic
    namespace: myproject
    replicas: 2

- name: Scale deployment config from src file without waiting
  k8s_scale:
    src: /myproject/elastic_deployment.yml
    replicas: 3
    wait: no

'''

RETURN = '''
result:
  description:
  - The patched object.
  returned: success
  type: dict
'''


def main():
    OpenShiftAnsibleScaleModule().execute_scale()


if __name__ == '__main__':
    main()