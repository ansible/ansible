#!/usr/bin/python
# (c) 2016, Flavio Percoco <flavio@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: helm
short_description: Manages Kubernetes packages with the Helm package manager
version_added: "2.4"
author: "Flavio Percoco (flaper87)"
description:
   - Install, upgrade, delete and list packages with the Helm package manage
requirements:
  - "pyhelm"
  - "grpcio"
options:
  host:
    description:
      - Tiller's server host
    required: false
    default: "localhost"
  port:
    description:
      - Tiller's server port
    required: false
    default: 44134
  namespace:
    description:
      - Kubernetes namespace where the chart should be installed
    required: false
    default: "default"
  name:
    description:
      - Release name to manage
    required: false
    default: null
  state:
    description:
      - Whether to install C(present), remove C(absent), or purge C(purged) a package.
    required: false
    choices: ['absent', 'purged', 'present']
    default: "installed"
  chart:
    description: |
      A map describing the chart to install. For example:
      chart:
        name: memcached
        version: 0.4.0
        source:
          type: repo
          location: https://kubernetes-charts.storage.googleapis.com
    required: false
    default: {}
  values:
    description:
      - A map of value options for the chart.
    required: false
    default: {}
  disable_hooks:
    description:
      - Whether to disable hooks during the uninstall process
    required: false
    default: false
'''

RETURN = ''' # '''

EXAMPLES = '''
- name: Install helm chart
  helm:
    host: localhost
    chart:
      name: memcached
      version: 0.4.0
      source:
        type: repo
        location: https://kubernetes-charts.storage.googleapis.com
    state: installed
    name: my-memcached
    namespace: default

- name: Uninstall helm chart
  helm:
    host: localhost
    state: absent
    name: my-memcached
'''

try:
    import grpc
    from pyhelm import tiller
    from pyhelm import chartbuilder
    HAS_PYHELM = True
except ImportError as exc:
    HAS_PYHELM = False

from ansible.module_utils.basic import AnsibleModule


def install(module, tserver):
    changed = False
    params = module.params
    name = params['name']
    values = params['values']
    chart = module.params['chart']
    namespace = module.params['namespace']

    chartb = chartbuilder.ChartBuilder(chart)
    try:
        tserver.install_release(chartb.get_helm_chart(), namespace,
                                dry_run=False, name=name,
                                values=values)
        changed = True
    except grpc._channel._Rendezvous as exc:
        if "already exists" not in str(exc):
            raise exc

    return dict(changed=changed)


def delete(module, tserver, purge=False):
    changed = False
    params = module.params

    if not module.params['name']:
        module.fail_json(msg='Missing required field name')

    name = module.params['name']
    disable_hooks = params['disable_hooks']

    try:
        tserver.uninstall_release(name, disable_hooks, purge)
        changed = True
    except grpc._channel._Rendezvous as exc:
        if 'not found' not in str(exc):
            raise exc

    return dict(changed=changed)


def main():
    """The main function."""
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', default='localhost'),
            port=dict(type='int', default=44134),
            name=dict(type='str', default=''),
            chart=dict(type='dict'),
            state=dict(
                choices=['absent', 'purged', 'present'],
                default='present'
            ),
            # Install options
            values=dict(type='dict'),
            namespace=dict(type='str', default='default'),

            # Uninstall options
            disable_hooks=dict(type='bool', default=False),
        ),
        supports_check_mode=True)

    if not HAS_PYHELM:
        module.fail_json(msg="Could not import the pyhelm python module. "
                         "Please install `pyhelm` package.")

    host = module.params['host']
    port = module.params['port']
    state = module.params['state']
    tserver = tiller.Tiller(host, port)

    if state == 'present':
        rst = install(module, tserver)

    if state in 'absent':
        rst = delete(module, tserver)

    if state in 'purged':
        rst = delete(module, tserver, True)

    module.exit_json(**rst)


if __name__ == '__main__':
    main()
