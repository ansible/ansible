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

from ansible.module_utils.k8s.common import K8sAnsibleMixin, HAS_K8S_MODULE_HELPER

try:
    from ansible.errors import AnsibleError
except ImportError:
    AnsibleError = Exception

try:
    from openshift.dynamic.exceptions import DynamicApiError
except ImportError:
    pass


class K8sInventoryException(Exception):
    pass


class K8sInventoryHelper(K8sAnsibleMixin):
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
        client = self.get_api_client()

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
            raise K8sInventoryException('Error fetching Namespace list: {0}'.format(exc.message))
        return [namespace.metadata.name for namespace in obj.items]

    def get_pods_for_namespace(self, client, name, namespace):
        v1_pod = client.resources.get(api_version='v1', kind='Pod')
        try:
            obj = v1_pod.get(namespace=namespace)
        except DynamicApiError as exc:
            raise K8sInventoryException('Error fetching Pod list: {0}'.format(exc.message))

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
            pod_labels = {} if not pod.metadata.labels else pod.metadata.labels
            pod_annotations = {} if not pod.metadata.annotations else pod.metadata.annotations

            if pod.metadata.labels:
                pod_labels = pod.metadata.labels
                # create a group for each label_value
                for key, value in pod.metadata.labels:
                    group_name = 'label_{0}_{1}'.format(key, value)
                    if group_name not in pod_groups:
                        pod_groups.append(group_name)
                    self.inventory.add_group(group_name)

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
            raise K8sInventoryException('Error fetching Service list: {0}'.format(exc.message))

        namespace_group = 'namespace_{0}'.format(namespace)
        namespace_services_group = '{0}_services'.format(namespace_group)

        self.inventory.add_group(name)
        self.inventory.add_group(namespace_group)
        self.inventory.add_child(name, namespace_group)
        self.inventory.add_group(namespace_services_group)
        self.inventory.add_child(namespace_group, namespace_services_group)

        for service in obj.items:
            service_name = service.metadata.name
            service_labels = {} if not service.metadata.labels else service.metadata.labels
            service_annotations = {} if not service.metadata.annotations else service.metadata.annotations

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
                self.inventory.set_variable(service_name, 'selector', service.spec.selector)

            if hasattr(service.status.loadBalancer, 'ingress') and service.status.loadBalancer.ingress:
                load_balancer = [{'hostname': ingress.hostname,
                                  'ip': ingress.ip} for ingress in service.status.loadBalancer.ingress]
                self.inventory.set_variable(service_name, 'load_balancer', load_balancer)


class OpenShiftInventoryHelper(K8sInventoryHelper):
    helper = None
    transport = 'oc'

    def fetch_objects(self, connections):
        super(OpenShiftInventoryHelper, self).fetch_objects(connections)
        client = self.get_api_client()

        if connections:
            for connection in connections:
                client = self.get_api_client(**connection)
                name = connection.get('name', self.get_default_host_name(client.configuration.host))
                if connection.get('namespaces'):
                    namespaces = connection['namespaces']
                else:
                    namespaces = self.get_available_namespaces(client)
                for namespace in namespaces:
                    self.get_routes_for_namespace(client, name, namespace)
        else:
            name = self.get_default_host_name(client.configuration.host)
            namespaces = self.get_available_namespaces(client)
            for namespace in namespaces:
                self.get_routes_for_namespace(client, name, namespace)

    def get_routes_for_namespace(self, client, name, namespace):
        v1_route = client.resources.get(api_version='v1', kind='Route')
        try:
            obj = v1_route.get(namespace=namespace)
        except DynamicApiError as exc:
            raise K8sInventoryException('Error fetching Routes list: {0}'.format(exc.message))

        namespace_group = 'namespace_{0}'.format(namespace)
        namespace_routes_group = '{0}_routes'.format(namespace_group)

        self.inventory.add_group(name)
        self.inventory.add_group(namespace_group)
        self.inventory.add_child(name, namespace_group)
        self.inventory.add_group(namespace_routes_group)
        self.inventory.add_child(namespace_group, namespace_routes_group)
        for route in obj.items:
            route_name = route.metadata.name
            route_labels = {} if not route.metadata.labels else route.metadata.labels
            route_annotations = {} if not route.metadata.annotations else route.metadata.annotations

            self.inventory.add_host(route_name)

            if route.metadata.labels:
                # create a group for each label_value
                for key, value in route.metadata.labels:
                    group_name = 'label_{0}_{1}'.format(key, value)
                    self.inventory.add_group(group_name)
                    self.inventory.add_child(group_name, route_name)

            self.inventory.add_child(namespace_routes_group, route_name)

            # add hostvars
            self.inventory.set_variable(route_name, 'labels', route_labels)
            self.inventory.set_variable(route_name, 'annotations', route_annotations)
            self.inventory.set_variable(route_name, 'cluster_name', route.metadata.clusterName)
            self.inventory.set_variable(route_name, 'object_type', 'route')
            self.inventory.set_variable(route_name, 'self_link', route.metadata.selfLink)
            self.inventory.set_variable(route_name, 'resource_version', route.metadata.resourceVersion)
            self.inventory.set_variable(route_name, 'uid', route.metadata.uid)

            if route.spec.host:
                self.inventory.set_variable(route_name, 'host', route.spec.host)

            if route.spec.path:
                self.inventory.set_variable(route_name, 'path', route.spec.path)

            if hasattr(route.spec.port, 'targetPort') and route.spec.port.targetPort:
                self.inventory.set_variable(route_name, 'port', route.spec.port)
