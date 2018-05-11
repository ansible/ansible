#
#  Copyright 2018 Red Hat | Ansible
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

from __future__ import absolute_import, division, print_function

from ansible.module_utils.six import iteritems

try:
    from openshift.helper.kubernetes import KubernetesObjectHelper
    from openshift.helper.openshift import OpenShiftObjectHelper
    from openshift.helper.exceptions import KubernetesException
    HAS_K8S_MODULE_HELPER = True
except ImportError as exc:
    HAS_K8S_MODULE_HELPER = False


class K8sInventoryException(Exception):
    pass


class K8sInventoryHelper(object):
    helper = None
    transport = 'kubectl'

    def setup(self, config_data, cache, cache_key):
        connections = config_data.get('connections')

        if not HAS_K8S_MODULE_HELPER:
            raise K8sInventoryException(
                "This module requires the OpenShift Python client. Try `pip install openshift`"
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
        self.helper = self.get_helper('v1', 'namespace_list')

        if connections:
            if not isinstance(connections, list):
                raise K8sInventoryException("Expecting connections to be a list.")

            for connection in connections:
                if not isinstance(connection, dict):
                    raise K8sInventoryException("Expecting connection to be a dictionary.")
                self.authenticate(connection)
                name = connection.get('name', self.get_default_host_name(self.helper.api_client.host))
                if connection.get('namespaces'):
                    namespaces = connections['namespaces']
                else:
                    namespaces = self.get_available_namespaces()
                for namespace in namespaces:
                    self.get_pods_for_namespace(name, namespace)
                    self.get_services_for_namespace(name, namespace)
        else:
            name = self.get_default_host_name(self.helper.api_client.host)
            namespaces = self.get_available_namespaces()
            for namespace in namespaces:
                self.get_pods_for_namespace(name, namespace)
                self.get_services_for_namespace(name, namespace)

    def authenticate(self, connection=None):
        auth_options = {}
        if connection:
            auth_args = ('host', 'api_key', 'kubeconfig', 'context', 'username', 'password',
                         'cert_file', 'key_file', 'ssl_ca_cert', 'verify_ssl')
            for key, value in iteritems(connection):
                if key in auth_args and value is not None:
                    auth_options[key] = value
        try:
            self.helper.set_client_config(**auth_options)
        except KubernetesException as exc:
            raise K8sInventoryException('Error connecting to the API: {0}'.format(exc.message))

    @staticmethod
    def get_default_host_name(host):
        return host.replace('https://', '').replace('http://', '').replace('.', '-').replace(':', '_')

    def get_helper(self, api_version, kind):
        try:
            helper = KubernetesObjectHelper(api_version=api_version, kind=kind, debug=False)
            helper.get_model(api_version, kind)
            return helper
        except KubernetesException as exc:
            raise K8sInventoryException('Error initializing object helper: {0}'.format(exc.message))

    def get_available_namespaces(self):
        try:
            obj = self.helper.get_object()
        except KubernetesObjectHelper as exc:
            raise K8sInventoryException('Error fetching Namespace list: {0}'.format(exc.message))
        return [namespace.metadata.name for namespace in obj.items]

    def get_pods_for_namespace(self, name, namespace):
        self.helper.set_model('v1', 'pod_list')
        try:
            obj = self.helper.get_object(namespace=namespace)
        except KubernetesException as exc:
            raise K8sInventoryException('Error fetching Pod list: {0}'.format(exc.message))

        namespace_pod_group = '{0}_pods'.format(namespace)

        self.inventory.add_group(name)
        self.inventory.add_group(namespace)
        self.inventory.add_child(name, namespace)
        self.inventory.add_group(namespace_pod_group)
        self.inventory.add_child(namespace, namespace_pod_group)
        for pod in obj.items:
            pod_name = pod.metadata.name
            pod_groups = []
            pod_labels = {} if not pod.metadata.labels else pod.metadata.labels
            pod_annotations = {} if not pod.metadata.annotations else pod.metadata.annotations

            if pod.metadata.labels:
                pod_labels = pod.metadata.labels
                # create a group for each label_value
                for key, value in iteritems(pod.metadata.labels):
                    group_name = '{0}_{1}'.format(key, value)
                    if group_name not in pod_groups:
                        pod_groups.append(group_name)
                    self.inventory.add_group(group_name)

            for container in pod.status.container_statuses:
                # add each pod_container to the namespace group, and to each label_value group
                container_name = '{0}_{1}'.format(pod.metadata.name, container.name)
                self.inventory.add_host(container_name)
                self.inventory.add_child(namespace_pod_group, container_name)
                if pod_groups:
                    for group in pod_groups:
                        self.inventory.add_child(group, container_name)

                # Add hostvars
                self.inventory.set_variable(container_name, 'object_type', 'pod')
                self.inventory.set_variable(container_name, 'labels', pod_labels)
                self.inventory.set_variable(container_name, 'annotations', pod_annotations)
                self.inventory.set_variable(container_name, 'cluster_name', pod.metadata.cluster_name)
                self.inventory.set_variable(container_name, 'pod_node_name', pod.spec.node_name)
                self.inventory.set_variable(container_name, 'pod_name', pod.spec.node_name)
                self.inventory.set_variable(container_name, 'pod_host_ip', pod.status.host_ip)
                self.inventory.set_variable(container_name, 'pod_phase', pod.status.phase)
                self.inventory.set_variable(container_name, 'pod_ip', pod.status.pod_ip)
                self.inventory.set_variable(container_name, 'pod_self_link', pod.metadata.self_link)
                self.inventory.set_variable(container_name, 'pod_resource_version', pod.metadata.resource_version)
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
                self.inventory.set_variable(container_name, 'ansible_connection', self.transport)
                self.inventory.set_variable(container_name, 'ansible_{0}_pod'.format(self.transport),
                                            pod_name)
                self.inventory.set_variable(container_name, 'ansible_{0}_container'.format(self.transport),
                                            container.name)

    def get_services_for_namespace(self, name, namespace):
        self.helper.set_model('v1', 'service_list')
        try:
            obj = self.helper.get_object(namespace=namespace)
        except KubernetesException as exc:
            raise K8sInventoryException('Error fetching Service list: {0}'.format(exc.message))

        namespace_service_group = '{0}_services'.format(namespace)

        self.inventory.add_group(name)
        self.inventory.add_group(namespace)
        self.inventory.add_child(name, namespace)
        self.inventory.add_group(namespace_service_group)
        self.inventory.add_child(namespace, namespace_service_group)
        for service in obj.items:
            service_name = service.metadata.name
            service_labels = {} if not service.metadata.labels else service.metadata.labels
            service_annotations = {} if not service.metadata.annotations else service.metadata.annotations

            self.inventory.add_host(service_name)

            if service.metadata.labels:
                # create a group for each label_value
                for key, value in iteritems(service.metadata.labels):
                    group_name = '{0}_{1}'.format(key, value)
                    self.inventory.add_group(group_name)
                    self.inventory.add_child(group_name, service_name)

            self.inventory.add_child(namespace_service_group, service_name)

            ports = [{'name': port.name,
                      'port': port.port,
                      'protocol': port.protocol,
                      'targetPort': port.target_port,
                      'nodePort': port.node_port} for port in service.spec.ports]

            # add hostvars
            self.inventory.set_variable(service_name, 'object_type', 'service')
            self.inventory.set_variable(service_name, 'labels', service_labels)
            self.inventory.set_variable(service_name, 'annotations', service_annotations)
            self.inventory.set_variable(service_name, 'cluster_name', service.metadata.cluster_name)
            self.inventory.set_variable(service_name, 'ports', ports)
            self.inventory.set_variable(service_name, 'type', service.spec.type)
            self.inventory.set_variable(service_name, 'self_link', service.metadata.self_link)
            self.inventory.set_variable(service_name, 'resource_version', service.metadata.resource_version)
            self.inventory.set_variable(service_name, 'uid', service.metadata.uid)

            if service.spec.external_traffic_policy:
                self.inventory.set_variable(service_name, 'external_traffic_policy',
                                            service.spec.external_traffic_policy)
            if hasattr(service.spec, 'external_ips') and service.spec.external_ips:
                self.inventory.set_variable(service_name, 'external_ips', service.spec.external_ips)

            if service.spec.external_name:
                self.inventory.set_variable(service_name, 'external_name', service.spec.external_name)

            if service.spec.health_check_node_port:
                self.inventory.set_variable(service_name, 'health_check_node_port',
                                            service.spec.health_check_node_port)
            if service.spec.load_balancer_ip:
                self.inventory.set_variable(service_name, 'load_balancer_ip',
                                            service.spec.load_balancer_ip)
            if service.spec.selector:
                self.inventory.set_variable(service_name, 'selector', service.spec.selector)

            if hasattr(service.status.load_balancer, 'ingress') and service.status.load_balancer.ingress:
                load_balancer = [{'hostname': ingress.hostname,
                                  'ip': ingress.ip} for ingress in service.status.load_balancer.ingress]
                self.inventory.set_variable(service_name, 'load_balancer', load_balancer)


class OpenShiftInventoryHelper(K8sInventoryHelper):
    helper = None
    transport = 'oc'

    def fetch_objects(self, connections):
        super(OpenShiftInventoryHelper, self).fetch_objects(connections)
        self.helper = self.get_helper('v1', 'namespace_list')

        if connections:
            for connection in connections:
                self.authenticate(connection)
                name = connection.get('name', self.get_default_host_name(self.helper.api_client.host))
                if connection.get('namespaces'):
                    namespaces = connection['namespaces']
                else:
                    namespaces = self.get_available_namespaces()
                for namespace in namespaces:
                    self.get_routes_for_namespace(name, namespace)
        else:
            name = self.get_default_host_name(self.helper.api_client.host)
            namespaces = self.get_available_namespaces()
            for namespace in namespaces:
                self.get_routes_for_namespace(name, namespace)

    def get_helper(self, api_version, kind):
        try:
            helper = OpenShiftObjectHelper(api_version=api_version, kind=kind, debug=False)
            helper.get_model(api_version, kind)
            return helper
        except KubernetesException as exc:
            raise K8sInventoryException('Error initializing object helper: {0}'.format(exc.message))

    def get_routes_for_namespace(self, name, namespace):
        self.helper.set_model('v1', 'route_list')
        try:
            obj = self.helper.get_object(namespace=namespace)
        except KubernetesException as exc:
            raise K8sInventoryException('Error fetching Routes list: {0}'.format(exc.message))

        namespace_routes_group = '{0}_routes'.format(namespace)

        self.inventory.add_group(name)
        self.inventory.add_group(namespace)
        self.inventory.add_child(name, namespace)
        self.inventory.add_group(namespace_routes_group)
        self.inventory.add_child(namespace, namespace_routes_group)
        for route in obj.items:
            route_name = route.metadata.name
            route_labels = {} if not route.metadata.labels else route.metadata.labels
            route_annotations = {} if not route.metadata.annotations else route.metadata.annotations

            self.inventory.add_host(route_name)

            if route.metadata.labels:
                # create a group for each label_value
                for key, value in iteritems(route.metadata.labels):
                    group_name = '{0}_{1}'.format(key, value)
                    self.inventory.add_group(group_name)
                    self.inventory.add_child(group_name, route_name)

            self.inventory.add_child(namespace_routes_group, route_name)

            # add hostvars
            self.inventory.set_variable(route_name, 'labels', route_labels)
            self.inventory.set_variable(route_name, 'annotations', route_annotations)
            self.inventory.set_variable(route_name, 'cluster_name', route.metadata.cluster_name)
            self.inventory.set_variable(route_name, 'object_type', 'route')
            self.inventory.set_variable(route_name, 'self_link', route.metadata.self_link)
            self.inventory.set_variable(route_name, 'resource_version', route.metadata.resource_version)
            self.inventory.set_variable(route_name, 'uid', route.metadata.uid)

            if route.spec.host:
                self.inventory.set_variable(route_name, 'host', route.spec.host)

            if route.spec.path:
                self.inventory.set_variable(route_name, 'path', route.spec.path)

            if hasattr(route.spec.port, 'target_port') and route.spec.port.target_port:
                self.inventory.set_variable(route_name, 'port', route.spec.port)
