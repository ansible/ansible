# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: k8s
    plugin_type: inventory
    author:
      - Chris Houseknecht <@chouseknecht>
      - Fabian von Feilitzsch <@fabianvf>

    short_description: Kubernetes (K8s) inventory source

    description:
      - Fetch containers and services for one or more clusters
      - Groups by cluster name, namespace, namespace_services, namespace_pods, and labels
      - Uses k8s.(yml|yaml) YAML configuration file to set parameter values.

    options:
      plugin:
         description: token that ensures this is a source file for the 'k8s' plugin.
         required: True
         choices: ['k8s']
      connections:
          description:
          - Optional list of cluster connection settings. If no connections are provided, the default
            I(~/.kube/config) and active context will be used, and objects will be returned for all namespaces
            the active user is authorized to access.
          name:
              description:
              - Optional name to assign to the cluster. If not provided, a name is constructed from the server
                and port.
          kubeconfig:
              description:
              - Path to an existing Kubernetes config file. If not provided, and no other connection
                options are provided, the OpenShift client will attempt to load the default
                configuration file from I(~/.kube/config.json). Can also be specified via K8S_AUTH_KUBECONFIG
                environment variable.
          context:
              description:
              - The name of a context found in the config file. Can also be specified via K8S_AUTH_CONTEXT environment
                variable.
          host:
              description:
              - Provide a URL for accessing the API. Can also be specified via K8S_AUTH_HOST environment variable.
          api_key:
              description:
              - Token used to authenticate with the API. Can also be specified via K8S_AUTH_API_KEY environment
                variable.
          username:
              description:
              - Provide a username for authenticating with the API. Can also be specified via K8S_AUTH_USERNAME
                environment variable.
          password:
              description:
              - Provide a password for authenticating with the API. Can also be specified via K8S_AUTH_PASSWORD
                environment variable.
          client_cert:
              description:
              - Path to a certificate used to authenticate with the API. Can also be specified via K8S_AUTH_CERT_FILE
                environment variable.
              aliases: [ cert_file ]
          client_key:
              description:
              - Path to a key file used to authenticate with the API. Can also be specified via K8S_AUTH_KEY_FILE
                environment variable.
              aliases: [ key_file ]
          ca_cert:
              description:
              - Path to a CA certificate used to authenticate with the API. Can also be specified via
                K8S_AUTH_SSL_CA_CERT environment variable.
              aliases: [ ssl_ca_cert ]
          validate_certs:
              description:
              - "Whether or not to verify the API server's SSL certificates. Can also be specified via
                K8S_AUTH_VERIFY_SSL environment variable."
              type: bool
              aliases: [ verify_ssl ]
          namespaces:
              description:
              - List of namespaces. If not specified, will fetch all containers for all namespaces user is authorized
                to access.

    requirements:
    - "python >= 2.7"
    - "openshift >= 0.6"
    - "PyYAML >= 3.11"
'''

EXAMPLES = '''
# File must be named k8s.yaml or k8s.yml

# Authenticate with token, and return all pods and services for all namespaces
plugin: k8s
connections:
  - host: https://192.168.64.4:8443
    token: xxxxxxxxxxxxxxxx
    validate_certs: false

# Use default config (~/.kube/config) file and active context, and return objects for a specific namespace
plugin: k8s
connections:
  - namespaces:
    - testing

# Use a custom config file, and a specific context.
plugin: k8s
connections:
  - kubeconfig: /path/to/config
    context: 'awx/192-168-64-4:8443/developer'
'''

import json

from ansible.errors import AnsibleError
from ansible.module_utils.k8s.common import K8sAnsibleMixin, HAS_K8S_MODULE_HELPER, k8s_import_exception
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable

try:
    from openshift.dynamic.exceptions import DynamicApiError
except ImportError:
    pass


def format_dynamic_api_exc(exc):
    if exc.body:
        if exc.headers and exc.headers.get('Content-Type') == 'application/json':
            message = json.loads(exc.body).get('message')
            if message:
                return message
        return exc.body
    else:
        return '%s Reason: %s' % (exc.status, exc.reason)


class K8sInventoryException(Exception):
    pass


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable, K8sAnsibleMixin):
    NAME = 'k8s'

    transport = 'kubectl'

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        cache_key = self._get_cache_prefix(path)
        config_data = self._read_config_data(path)
        self.setup(config_data, cache, cache_key)

    def setup(self, config_data, cache, cache_key):
        connections = config_data.get('connections')

        if not HAS_K8S_MODULE_HELPER:
            raise K8sInventoryException(
                "This module requires the OpenShift Python client. Try `pip install openshift`. Detail: {0}".format(k8s_import_exception)
            )

        source_data = None
        if cache and cache_key in self._cache:
            try:
                source_data = self._cache[cache_key]
            except KeyError:
                pass

        if not source_data:
            self.fetch_objects(connections)

    def fetch_objects(self, connections):

        if connections:
            if not isinstance(connections, list):
                raise K8sInventoryException("Expecting connections to be a list.")

            for connection in connections:
                if not isinstance(connection, dict):
                    raise K8sInventoryException("Expecting connection to be a dictionary.")
                client = self.get_api_client(**connection)
                name = connection.get('name', self.get_default_host_name(client.configuration.host))
                if connection.get('namespaces'):
                    namespaces = connection['namespaces']
                else:
                    namespaces = self.get_available_namespaces(client)
                for namespace in namespaces:
                    self.get_pods_for_namespace(client, name, namespace)
                    self.get_services_for_namespace(client, name, namespace)
        else:
            client = self.get_api_client()
            name = self.get_default_host_name(client.configuration.host)
            namespaces = self.get_available_namespaces(client)
            for namespace in namespaces:
                self.get_pods_for_namespace(client, name, namespace)
                self.get_services_for_namespace(client, name, namespace)

    @staticmethod
    def get_default_host_name(host):
        return host.replace('https://', '').replace('http://', '').replace('.', '-').replace(':', '_')

    def get_available_namespaces(self, client):
        v1_namespace = client.resources.get(api_version='v1', kind='Namespace')
        try:
            obj = v1_namespace.get()
        except DynamicApiError as exc:
            self.display.debug(exc)
            raise K8sInventoryException('Error fetching Namespace list: %s' % format_dynamic_api_exc(exc))
        return [namespace.metadata.name for namespace in obj.items]

    def get_pods_for_namespace(self, client, name, namespace):
        v1_pod = client.resources.get(api_version='v1', kind='Pod')
        try:
            obj = v1_pod.get(namespace=namespace)
        except DynamicApiError as exc:
            self.display.debug(exc)
            raise K8sInventoryException('Error fetching Pod list: %s' % format_dynamic_api_exc(exc))

        namespace_group = 'namespace_{0}'.format(namespace)
        namespace_pods_group = '{0}_pods'.format(namespace_group)

        self.inventory.add_group(name)
        self.inventory.add_group(namespace_group)
        self.inventory.add_child(name, namespace_group)
        self.inventory.add_group(namespace_pods_group)
        self.inventory.add_child(namespace_group, namespace_pods_group)

        for pod in obj.items:
            pod_name = pod.metadata.name
            pod_groups = []
            pod_annotations = {} if not pod.metadata.annotations else dict(pod.metadata.annotations)

            if pod.metadata.labels:
                # create a group for each label_value
                for key, value in pod.metadata.labels:
                    group_name = 'label_{0}_{1}'.format(key, value)
                    if group_name not in pod_groups:
                        pod_groups.append(group_name)
                    self.inventory.add_group(group_name)
                pod_labels = dict(pod.metadata.labels)
            else:
                pod_labels = {}

            if not pod.status.containerStatuses:
                continue

            for container in pod.status.containerStatuses:
                # add each pod_container to the namespace group, and to each label_value group
                container_name = '{0}_{1}'.format(pod.metadata.name, container.name)
                self.inventory.add_host(container_name)
                self.inventory.add_child(namespace_pods_group, container_name)
                if pod_groups:
                    for group in pod_groups:
                        self.inventory.add_child(group, container_name)

                # Add hostvars
                self.inventory.set_variable(container_name, 'object_type', 'pod')
                self.inventory.set_variable(container_name, 'labels', pod_labels)
                self.inventory.set_variable(container_name, 'annotations', pod_annotations)
                self.inventory.set_variable(container_name, 'cluster_name', pod.metadata.clusterName)
                self.inventory.set_variable(container_name, 'pod_node_name', pod.spec.nodeName)
                self.inventory.set_variable(container_name, 'pod_name', pod.spec.name)
                self.inventory.set_variable(container_name, 'pod_host_ip', pod.status.hostIP)
                self.inventory.set_variable(container_name, 'pod_phase', pod.status.phase)
                self.inventory.set_variable(container_name, 'pod_ip', pod.status.podIP)
                self.inventory.set_variable(container_name, 'pod_self_link', pod.metadata.selfLink)
                self.inventory.set_variable(container_name, 'pod_resource_version', pod.metadata.resourceVersion)
                self.inventory.set_variable(container_name, 'pod_uid', pod.metadata.uid)
                self.inventory.set_variable(container_name, 'container_name', container.image)
                self.inventory.set_variable(container_name, 'container_image', container.image)
                if container.state.running:
                    self.inventory.set_variable(container_name, 'container_state', 'Running')
                if container.state.terminated:
                    self.inventory.set_variable(container_name, 'container_state', 'Terminated')
                if container.state.waiting:
                    self.inventory.set_variable(container_name, 'container_state', 'Waiting')
                self.inventory.set_variable(container_name, 'container_ready', container.ready)
                self.inventory.set_variable(container_name, 'ansible_remote_tmp', '/tmp/')
                self.inventory.set_variable(container_name, 'ansible_connection', self.transport)
                self.inventory.set_variable(container_name, 'ansible_{0}_pod'.format(self.transport),
                                            pod_name)
                self.inventory.set_variable(container_name, 'ansible_{0}_container'.format(self.transport),
                                            container.name)
                self.inventory.set_variable(container_name, 'ansible_{0}_namespace'.format(self.transport),
                                            namespace)

    def get_services_for_namespace(self, client, name, namespace):
        v1_service = client.resources.get(api_version='v1', kind='Service')
        try:
            obj = v1_service.get(namespace=namespace)
        except DynamicApiError as exc:
            self.display.debug(exc)
            raise K8sInventoryException('Error fetching Service list: %s' % format_dynamic_api_exc(exc))

        namespace_group = 'namespace_{0}'.format(namespace)
        namespace_services_group = '{0}_services'.format(namespace_group)

        self.inventory.add_group(name)
        self.inventory.add_group(namespace_group)
        self.inventory.add_child(name, namespace_group)
        self.inventory.add_group(namespace_services_group)
        self.inventory.add_child(namespace_group, namespace_services_group)

        for service in obj.items:
            service_name = service.metadata.name
            service_labels = {} if not service.metadata.labels else dict(service.metadata.labels)
            service_annotations = {} if not service.metadata.annotations else dict(service.metadata.annotations)

            self.inventory.add_host(service_name)

            if service.metadata.labels:
                # create a group for each label_value
                for key, value in service.metadata.labels:
                    group_name = 'label_{0}_{1}'.format(key, value)
                    self.inventory.add_group(group_name)
                    self.inventory.add_child(group_name, service_name)

            try:
                self.inventory.add_child(namespace_services_group, service_name)
            except AnsibleError as e:
                raise

            ports = [{'name': port.name,
                      'port': port.port,
                      'protocol': port.protocol,
                      'targetPort': port.targetPort,
                      'nodePort': port.nodePort} for port in service.spec.ports or []]

            # add hostvars
            self.inventory.set_variable(service_name, 'object_type', 'service')
            self.inventory.set_variable(service_name, 'labels', service_labels)
            self.inventory.set_variable(service_name, 'annotations', service_annotations)
            self.inventory.set_variable(service_name, 'cluster_name', service.metadata.clusterName)
            self.inventory.set_variable(service_name, 'ports', ports)
            self.inventory.set_variable(service_name, 'type', service.spec.type)
            self.inventory.set_variable(service_name, 'self_link', service.metadata.selfLink)
            self.inventory.set_variable(service_name, 'resource_version', service.metadata.resourceVersion)
            self.inventory.set_variable(service_name, 'uid', service.metadata.uid)

            if service.spec.externalTrafficPolicy:
                self.inventory.set_variable(service_name, 'external_traffic_policy',
                                            service.spec.externalTrafficPolicy)
            if service.spec.externalIPs:
                self.inventory.set_variable(service_name, 'external_ips', service.spec.externalIPs)

            if service.spec.externalName:
                self.inventory.set_variable(service_name, 'external_name', service.spec.externalName)

            if service.spec.healthCheckNodePort:
                self.inventory.set_variable(service_name, 'health_check_node_port',
                                            service.spec.healthCheckNodePort)
            if service.spec.loadBalancerIP:
                self.inventory.set_variable(service_name, 'load_balancer_ip',
                                            service.spec.loadBalancerIP)
            if service.spec.selector:
                self.inventory.set_variable(service_name, 'selector', dict(service.spec.selector))

            if hasattr(service.status.loadBalancer, 'ingress') and service.status.loadBalancer.ingress:
                load_balancer = [{'hostname': ingress.hostname,
                                  'ip': ingress.ip} for ingress in service.status.loadBalancer.ingress]
                self.inventory.set_variable(service_name, 'load_balancer', load_balancer)
