#!/usr/bin/python
#
# Copyright 2017 Red Hat | Ansible
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.


from ansible.module_utils.k8s_common import K8SClient

from kubernetes.client.rest import ApiException
from kubernetes.client.models.v1_service_port import V1ServicePort


DOCUMENTATION = '''
---
module: k8s_service

short_description: Manage Kubernetes service objects

description:
  - Mange the lifecycle of a Kubernetes service object.

version_added: "2.3"

options:
  annotations:
    description:
      - Dict of arbitrary data stored in metadata, and not used to organize or categorize objects.
    required: false
  cluster_ip:
    description:
      - IP address of the service.
    required: false
  external_ips:
    description:
      - List of IP address for which nodes in the cluster will accept traffic for the service.
    required: false
  external_name:
    description:
      - External reference that kubedns or equivalent will return as a CNAME record for this service.
    required: false
  labels:
    description:
      - Map of string keys and values that can be used to organize and categorize (scope and select) objects.
  load_balancer_ip:
    description:
      - Only applies to C(type) I(LoadBalancer). Creates the load balancer with the specified IP address.
    required: false
  load_balancer_source_ranges:
    description:
      - List of IP addresses used to restrict traffic through the load balancer.
    required: false
  name:
    description:
      - Name of the service.
    required: true
  namespace:
    description:
      - The project or namespace to which the service is scoped.
    default: default
    required: false
  ports:
    description:
      - List of ports, where each port is a key, value map.
      - Valid keys include I(name), I(node_port), I(port), I(protocol), I(taraget_port)
    required: false
  replace:
    description:
      - Set to true to force the deletion and re-creation of an existing service.
    default: false
    required: false
  request_timeout:
    description:
      - Maximum time in seconds to wait when retrieving an existing service from the API.
    default: 10
    required: false
  selector:
    description:
      - Route service traffic to pods with label keys and values matching this selector.
    required: false
  session_affinity:
    description:
      - Enable session affinity.
    choices:
      - ClientIP
    required: false
  state:
    description:
      - Set to C(present) to ensure the service exists, and C(absent) to delete the service.
    choices:
      - present
      - absent
    default: present
    required: false
  type:
    description:
      - Specify the type of service.
    choices:
      - ClusterIP
      - ExternalName
      - LoadBalancer
      - NodePort
    default:
      - NodePort
    required: false

author:
  - "Ansible Core Team"

requirements:
  - kubernetes v1.0.0
'''

EXAMPLES = '''
- name: Remove service
    k8s_service:
      name: example
      state: absent

- name: Create example service
  k8s_service:
    name: example
    ports:
      - name: http-port
        port: 8888
        target_port: 8000
    selector:
      foo: bar
    state: present

- name: Patch example service
  k8s_service:
    name: example
    ports:
      - name: https-port
        port: 9000
        target_port: 9000
    selector:
      baz: pzazz
    state: present
'''

RETURN = '''
k8s_service:
  description: dict of the kubernetes configuration representing the service
  returned: success
  type: dictionary
  contains:
    api_version:
      description: API version number
      returned: success
      type: string
      sample: v1
    kind:
      description: The type of object.
      returned: success
      type: string
      sample: Service
    metadata:
      description: External and internal data about the service.
      returned: success
      type: complex
      contains:
        annotations:
          description:
            - Unstructured key value map stored with a resource that may be set by external tools to store and
            - retrieve arbitrary metadata.
          returned: success
          type: string
        cluster_name:
          description: The name of the cluster to which the object belongs.
          returned: success
          type: string
        creation_timestamp:
          description: The date and time when the object was created.
          returned: success
          type: string
        deletion_grace_period_seconds:
          description:
            - Number of seconds allowed for this object to gracefully terminate before it will be removed from the
            - system.
          returned: success
          type: int
        deletion_timestamp:
          description:
            - Number of seconds allowed for this object to gracefully terminate before it will be removed from the
            - system.
          returned: success
          type: string
    spec:
      description: The actual configuration of the service
      returned: success
      type: complex
      contains:
        cluster_ip:
          description: IP address of the service
          returned: success
          type: string
        external_i_ps:
          description:
            - List of IP addresses for which nodes in the cluster will also accept traffic for the service.
          returned: success
          type: list
        external_name:
          description:
            - External reference that kubedns or equivalent will return as a CNAME record for this service.
          returned: success
          type: string
        load_balancer_ip:
          description: If the service is a load balancer, it will get created with the specified IP.
          returned: success
          type: string
        load_balancer_source_ranges:
          description:
            - When the service is a load balancer, inbound traffic flow will be restricted to this set of IP
            - ranges.
          returned: success
          type: string
        ports:
          description: The list of ports exposed by this service.
          returned: success
          type: complex
        selector:
          description:
            - Key, value pairs used to determine which pods to route traffic to.
          returned: success
          type: complex
        session_affinity:
          description:
            - Contains either I(ClientIp) or I(None), indicating which form of session affinity is
            - active, if any.
          returned: success
          type: string
        type:
          description:
            - Determines how the Service is exposed. Valid options are I(ExternalName), I(ClusterIP), I(NodePort),
            - and I(LoadBalancer).
          returned: success
          type: string
'''


def create_service(module, kube):
    '''
    Create a new service.
    Assembles a k8s template from module params, and posts it to the API.
    :param module: Ansible module object
    :param kube: kubernetes client
    :param check_mode: bool
    :return: API response JSON
    '''

    template = {
        u'apiVersion': u'v1',
        u'kind': u'Service',
        u'metadata': {},
        u'spec': {}
    }

    template['metadata']['name'] = module.params['name']
    if module.params.get('labels'):
        template['metadata']['labels'] = module.params.get('labels')
    if module.params.get('annotations'):
        template['metadata']['annotations'] = module.params.get('annotations')
    if module.params.get('cluster_ip'):
        template['spec']['clusterIP'] = module.params.get('cluster_ip')
    if module.params.get('external_i_ps'):
        template['spec']['externalIPs'] = module.params.get('external_i_ps')
    if module.params.get('type'):
        template['spec']['type'] = module.params.get('type')
    if module.params.get('external_name'):
        template['spec']['externalName'] = module.params.get('external_name')
    if module.params.get('load_balancer_source_ranges'):
        template['spec']['loadBalancerSourceRanges'] = module.params.get('load_balancer_source_ranges')
    if module.params.get('ports'):
        template['spec']['ports'] = convert_port_names(module.params['ports'])
    if module.params.get('selector'):
        template['spec']['selector'] = module.params.get('selector')
    if module.params.get('session_affinity'):
        template['spec']['sessionAffinity'] = module.params.get('session_affinity')

    api_response = template
    if not module.check_mode:
        try:
            api_response = kube.create_namespaced_service(module.params['namespace'], template)
        except ApiException as exc:
            module.fail_json(msg="Exception when calling CoreV1Api->create_namespaced_service: {}".format(str(exc)))

    return api_response


def convert_port_names(ports):
    '''
    Convert parameter names to k8s template format
    :param ports: list
    :return: list
    '''
    template_ports = []
    for port in ports:
        template_port = {}
        if port.get('name'):
            template_port['name'] = port['name']
        if port.get('protocol'):
            template_port['protocol'] = port['protocol']
        if port.get('port'):
            template_port['port'] = port['port']
        if port.get('target_port'):
            template_port['targetPort'] = port['target_port']
        if port.get('node_port'):
            template_port['nodePort'] = port['node_port']
        template_ports.append(template_port)
    return template_ports


def remove_service(module, kube):
    '''
    Delete an existing service.
    :param module: Ansible module object
    :param kube: kubernetes client
    :param check_mode: bool
    :return: None
    '''

    name = module.params['name']
    namespace = module.params['namespace']

    if not module.check_mode:
        try:
            kube.delete_namespaced_service(name, namespace)
        except ApiException as exc:
            module.fail_json(msg="Exception when calling CoreV1Api->delete_namespaced_service: {}".format(str(exc)))


def patch_service(module, kube, service):
    '''
    Determine if an existing service is different than the requested service. Parameters of type list or object will
    update or add-to the matching service attributes, rather than replacing.

    Returns a bool indicating if a patch was required, and the template used to patch the existing service.
    :param module: Ansible module object
    :param kube: kubernetes client
    :param service: existing service object returned by the API
    :return: bool, dict
    '''
    annotations = module.params.get('annotations')
    cluster_ip = module.params.get('cluster_ip')
    external_ips = module.params.get('external_ips')
    external_name = module.params.get('external_name')
    labels = module.params.get('labels')
    load_balancer_ip = module.params.get('load_balancer_ip')
    load_balancer_source_ranges = module.params.get('load_balancer_source_ranges')
    ports = module.params.get('ports')
    selector = module.params.get('selector')
    service_type = module.params.get('type')
    session_affinity = module.params.get('session_affinity')
    patch = False
    changes = {}

    if annotations and annotations > service.metadata.annotations:
        service.metadata.annotations.update(annotations)
        changes['annotations'] = annotations
        patch = True
    if cluster_ip and cluster_ip != service.spec.cluster_ip:
        service.spec.cluster_ip = cluster_ip
        changes['cluster_ip'] = cluster_ip
        patch = True
    if external_ips and external_ips > service.spec.external_i_ps:
        service.spec.external_i_ps = list(set(service.spec.external_i_ps + external_ips))
        changes['external_i_ps'] = external_ips
        patch = True
    if external_name and external_name != service.spec.external_name:
        service.spec.external_name = external_name
        changes['external_name'] = external_name
        patch = True
    if labels and labels > service.metadata.labels:
        service.metadata.labels.update(labels)
        changes['labels'] = labels
        patch = True
    if load_balancer_ip and load_balancer_ip != service.spec.load_balancer_ip:
        service.spec.load_balancer_ip = load_balancer_ip
        changes['load_balancer_ip'] = load_balancer_ip
        patch = True
    if load_balancer_source_ranges and load_balancer_source_ranges > service.spec.load_balancer_source_ranges:
        service.spec.load_balancer_source_ranges = \
            list(set(service.spec.load_balancer_source_ranges + load_balancer_source_ranges))
        changes['load_balancer_source_ranges'] = load_balancer_source_ranges
        patch = True
    if ports:
        for port in ports:
            if not port_is_defined(port, service.spec.ports):
                service.spec.ports.append(V1ServicePort(name=port.get('name'),
                                                        node_port=port.get('node_port'),
                                                        port=port.get('port'),
                                                        protocol=port.get('protocol'),
                                                        target_port=port.get('target_port')))
                changes['ports'] = ports
                patch = True
    if selector and selector > service.spec.selector:
        service.spec.selector.update(selector)
        changes['selector'] = selector
        patch = True
    if service_type and service_type != service.spec.type:
        service.spec.type = service_type
        changes['type'] = service_type
        patch = True
    if session_affinity and session_affinity != service.spec.session_affinity:
        service.spec.session_affinity = session_affinity
        changes['session_affinity'] = session_affinity
        patch = True

    template = {}

    if patch:
        template['apiVersion'] = 'v1'
        template['kind'] = 'Service'
        template['metadata'] = {u'name': service.metadata.name,
                                u'namespace': service.metadata.namespace}
        template['spec'] = {u'type': service.spec.type}
        if service.metadata.annotations:
            template['metadata']['annotations'] = service.metadata.annotations
        if service.metadata.labels:
            template['metdata']['labels'] = service.metadata.labels
        if service.spec.cluster_ip:
            template['spec']['clusterIP'] = service.spec.cluster_ip
        if service.spec.external_i_ps:
            template['spec']['externalIPs'] = service.spec.external_i_ps
        if service.spec.external_name:
            template['spec']['externalName'] = service.spec.external_name
        if service.spec.load_balancer_ip:
            template['spec']['loadBalancerIP'] = service.spec.load_balancer_ip
        if service.spec.load_balancer_source_ranges:
            template['spec']['loadBalancerSourceRanges'] = service.spec.load_balancer_source_ranges
        if service.spec.ports:
            template['spec']['ports'] = convert_ports_to_template(service.spec.ports)
        if service.spec.selector:
            template['spec']['selector'] = service.spec.selector
        if service.spec.session_affinity:
            template['spec']['sessionAffinity'] = service.spec.session_affinity

        if not module.check_mode:
            try:
                api_response = kube.patch_namespaced_service(service.metadata.name,
                                                             service.metadata.namespace,
                                                             template)
                template = api_response
            except ApiException as exc:
                module.fail_json(msg="Exception when calling CoreV1Api->patch_namespaced_service: {}".format(str(exc)))

    return patch, template


def convert_ports_to_template(ports):
    '''
    Convert list port object to template list of port dicts
    :param ports: list
    :return: list
    '''
    template_ports = []
    for port in ports:
        template_port = {}
        if port.name:
            template_port['name'] = port.name
        if port.protocol:
            template_port['protocol'] = port.protocol
        if port.port:
            template_port['port'] = port.port
        if port.target_port:
            template_port['target_port'] = port.target_port
        if port.node_port:
            template_port['node_port'] = port.node_port
        template_ports.append(template_port)
    return template_ports


def port_is_defined(test_port, existing_ports):
    '''
    Test if a port is defined in an existing service.
    :param test_port: dict defining a port
    :param existing_ports: array of port objects from an existing service
    :return: bool
    '''
    port_dict = {u'name': test_port.get('name'),
                 u'node_port': test_port.get('node_port'),
                 u'port': test_port.get('port'),
                 u'protocol': test_port.get('protocol'),
                 u'target_port': test_port.get('target_port')}
    match = False
    for port in existing_ports:
        match = True
        for key in port_dict.keys():
            if port_dict[key] and port_dict[key] != getattr(port, key):
                match = False
        if match:
            break
    return match


def get_service_state(module, kube):
    '''
    Query the API for an existing service.
    :param module: Ansible module object
    :param kube: kubernetes client
    :return: API response JSON
    '''

    namespace = module.params['namespace']
    timeout_seconds = module.params['request_timeout']
    name = module.params['name']
    service = {}

    try:
        api_response = kube.list_namespaced_service(namespace,
                                                    timeout_seconds=timeout_seconds)
        for item in api_response.items:
            if item.metadata.name == name:
                service = item
                break

    except ApiException as exc:
        module.fail_json(msg="Exception when calling CoreV1Api->list_namespaced_service: {}".format(str(exc)))

    return service


def main():

    arg_spec = dict(
        annotations=dict(type='dict'),
        cluster_ip=dict(type='str'),
        external_ips=dict(type='list'),
        external_name=dict(type='str'),
        labels=dict(type='dict'),
        load_balancer_ip=dict(type='str'),
        load_balancer_source_ranges =dict(type='list'),
        name=dict(type='str', required=True),
        namespace=dict(type='str', default='default'),
        ports=dict(type='list'),
        replace=dict(type='bool', default=False),
        request_timeout=dict(type='int', default=10),
        selector=dict(type='dict'),
        session_affinity=dict(type='str', choices=['ClientIP']),
        state=dict(type='str',
                   choices=['present', 'absent'],
                   default='present'),
        type=dict(type='str',
                  choices=['ClusterIP', 'ExternalName', 'LoadBalancer', 'NodePort'],
                  default='NodePort'),
    )

    # Instantiate K8SClient with AnsibleModule params. By default kubernetes=True, which instantiates the Kubernetes
    #  client. Pass openshift=True, if you need the OpenShift client. The kuberenetes client is accessible as
    # .k8s_client, and OpenShft as .os_client.
    k8s = K8SClient(argument_spec=arg_spec)

    module = k8s.module
    kube = k8s.k8s_client

    state = module.params['state']
    replace = module.params['replace']
    service = get_service_state(module, kube)
    service_name = module.params['name']
    namespace = module.params['namespace']

    # The module will return the result dict. Specific information about the state of the service will be
    #  available as the Ansible fact 'k8s_service'.
    fact_key = "k8s_service"
    result = {u'msg': '',
              u'changed': False,
              u'ansible_facts': {}}

    if state == 'present':
        if not service:
            # Create a new service
            service = create_service(module, kube)
            result['msg'] = "Created service {0} in {1}".format(service_name, namespace)
            result['changed'] = True
            result['ansible_facts'][fact_key] = service if isinstance(service, dict) else service.to_dict()
        else:
            if replace:
                # Remove and re-create an existing service
                remove_service(module, kube)
                service = create_service(module, kube)
                result['msg'] = "Replaced service {0} in {1}".format(service_name, namespace)
                result['changed'] = True
                result['ansible_facts'][fact_key] = service if isinstance(service, dict) else service.to_dict()
            else:
                # Check if an existing service should be patched
                patched, service = patch_service(module, kube, service)
                if patched:
                    result['msg'] = "Patched service {0} in {1}".format(service_name, namespace)
                    result['changed'] = True
                result['ansible_facts'][fact_key] = service if isinstance(service, dict) else service.to_dict()
    elif state == 'absent':
        if service:
            # Delete an existing service
            remove_service(module, kube)
            result['msg'] = "Removed service {0} in {1}".format(service_name, namespace)
            result['changed'] = True
            result['ansible_facts'][fact_key] = {}

    module.exit_json(**result)


if __name__ == '__main__':
    main()
