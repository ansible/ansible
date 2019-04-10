# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = '''
    name: kubevirt
    plugin_type: inventory
    author:
      - KubeVirt Team (@kubevirt)

    version_added: "2.8"
    short_description: KubeVirt inventory source
    extends_documentation_fragment:
        - inventory_cache
        - constructed
    description:
      - Fetch running VirtualMachines for one or more namespaces.
      - Groups by namespace, namespace_vms  and labels.
      - Uses kubevirt.(yml|yaml) YAML configuration file to set parameter values.

    options:
      plugin:
        description: token that ensures this is a source file for the 'kubevirt' plugin.
        required: True
        choices: ['kubevirt']
        type: str
      host_format:
        description:
          - Specify the format of the host in the inventory group.
        default: "{namespace}-{name}-{uid}"
      connections:
          type: list
          description:
            - Optional list of cluster connection settings. If no connections are provided, the default
              I(~/.kube/config) and active context will be used, and objects will be returned for all namespaces
              the active user is authorized to access.
          suboptions:
            name:
                description:
                - Optional name to assign to the cluster. If not provided, a name is constructed from the server
                    and port.
                type: str
            kubeconfig:
                description:
                - Path to an existing Kubernetes config file. If not provided, and no other connection
                    options are provided, the OpenShift client will attempt to load the default
                    configuration file from I(~/.kube/config.json). Can also be specified via K8S_AUTH_KUBECONFIG
                    environment variable.
                type: str
            context:
                description:
                - The name of a context found in the config file. Can also be specified via K8S_AUTH_CONTEXT environment
                    variable.
                type: str
            host:
                description:
                - Provide a URL for accessing the API. Can also be specified via K8S_AUTH_HOST environment variable.
                type: str
            api_key:
                description:
                - Token used to authenticate with the API. Can also be specified via K8S_AUTH_API_KEY environment
                    variable.
                type: str
            username:
                description:
                - Provide a username for authenticating with the API. Can also be specified via K8S_AUTH_USERNAME
                    environment variable.
                type: str
            password:
                description:
                - Provide a password for authenticating with the API. Can also be specified via K8S_AUTH_PASSWORD
                    environment variable.
                type: str
            cert_file:
                description:
                - Path to a certificate used to authenticate with the API. Can also be specified via K8S_AUTH_CERT_FILE
                    environment variable.
                type: str
            key_file:
                description:
                - Path to a key file used to authenticate with the API. Can also be specified via K8S_AUTH_HOST
                    environment variable.
                type: str
            ssl_ca_cert:
                description:
                - Path to a CA certificate used to authenticate with the API. Can also be specified via
                    K8S_AUTH_SSL_CA_CERT environment variable.
                type: str
            verify_ssl:
                description:
                - "Whether or not to verify the API server's SSL certificates. Can also be specified via
                    K8S_AUTH_VERIFY_SSL environment variable."
                type: bool
            namespaces:
                description:
                - List of namespaces. If not specified, will fetch all virtual machines for all namespaces user is authorized
                    to access.
                type: list
            network_name:
                description:
                - In case of multiple network attached to virtual machine, define which interface should be returned as primary IP
                    address.
                type: str
            api_version:
                description:
                - "Specify the KubeVirt API version."
                type: str
            annotation_variable:
                description:
                - "Specify the name of the annotation which provides data, which should be used as inventory host variables."
                - "Note, that the value in ansible annotations should be json."
                type: str
                default: 'ansible'
    requirements:
    - "openshift >= 0.6"
    - "PyYAML >= 3.11"
'''

EXAMPLES = '''
# File must be named kubevirt.yaml or kubevirt.yml

# Authenticate with token, and return all virtual machines for all namespaces
plugin: kubevirt
connections:
 - host: https://kubevirt.io
   token: xxxxxxxxxxxxxxxx
   ssl_verify: false

# Use default config (~/.kube/config) file and active context, and return vms with interfaces
# connected to network myovsnetwork and from namespace vms
plugin: kubevirt
connections:
  - namespaces:
      - vms
    network_name: myovsnetwork
'''

import json

from ansible.plugins.inventory.k8s import K8sInventoryException, InventoryModule as K8sInventoryModule, format_dynamic_api_exc

try:
    from openshift.dynamic.exceptions import DynamicApiError
except ImportError:
    pass


API_VERSION = 'kubevirt.io/v1alpha3'


class InventoryModule(K8sInventoryModule):
    NAME = 'kubevirt'

    def setup(self, config_data, cache, cache_key):
        self.config_data = config_data
        super(InventoryModule, self).setup(config_data, cache, cache_key)

    def fetch_objects(self, connections):
        client = self.get_api_client()
        vm_format = self.config_data.get('host_format', '{namespace}-{name}-{uid}')

        if connections:
            for connection in connections:
                client = self.get_api_client(**connection)
                name = connection.get('name', self.get_default_host_name(client.configuration.host))
                if connection.get('namespaces'):
                    namespaces = connection['namespaces']
                else:
                    namespaces = self.get_available_namespaces(client)
                interface_name = connection.get('network_name')
                api_version = connection.get('api_version', API_VERSION)
                annotation_variable = connection.get('annotation_variable', 'ansible')
                for namespace in namespaces:
                    self.get_vms_for_namespace(client, name, namespace, vm_format, interface_name, api_version, annotation_variable)
        else:
            name = self.get_default_host_name(client.configuration.host)
            namespaces = self.get_available_namespaces(client)
            for namespace in namespaces:
                self.get_vms_for_namespace(client, name, namespace, vm_format, None, api_version, annotation_variable)

    def get_vms_for_namespace(self, client, name, namespace, name_format, interface_name=None, api_version=None, annotation_variable=None):
        v1_vm = client.resources.get(api_version=api_version, kind='VirtualMachineInstance')
        try:
            obj = v1_vm.get(namespace=namespace)
        except DynamicApiError as exc:
            self.display.debug(exc)
            raise K8sInventoryException('Error fetching Virtual Machines list: %s' % format_dynamic_api_exc(exc))

        namespace_group = 'namespace_{0}'.format(namespace)
        namespace_vms_group = '{0}_vms'.format(namespace_group)

        name = self._sanitize_group_name(name)
        namespace_group = self._sanitize_group_name(namespace_group)
        namespace_vms_group = self._sanitize_group_name(namespace_vms_group)
        self.inventory.add_group(name)
        self.inventory.add_group(namespace_group)
        self.inventory.add_child(name, namespace_group)
        self.inventory.add_group(namespace_vms_group)
        self.inventory.add_child(namespace_group, namespace_vms_group)
        for vm in obj.items:
            if not (vm.status and vm.status.interfaces):
                continue

            # Find interface by its name:
            if interface_name is None:
                interface = vm.status.interfaces[0]
            else:
                interface = next(
                    (i for i in vm.status.interfaces if i.name == interface_name),
                    None
                )

            # If interface is not found or IP address is not reported skip this VM:
            if interface is None or interface.ipAddress is None:
                continue

            vm_name = name_format.format(namespace=vm.metadata.namespace, name=vm.metadata.name, uid=vm.metadata.uid)
            vm_ip = interface.ipAddress
            vm_annotations = {} if not vm.metadata.annotations else dict(vm.metadata.annotations)

            self.inventory.add_host(vm_name)

            if vm.metadata.labels:
                # create a group for each label_value
                for key, value in vm.metadata.labels:
                    group_name = 'label_{0}_{1}'.format(key, value)
                    group_name = self._sanitize_group_name(group_name)
                    self.inventory.add_group(group_name)
                    self.inventory.add_child(group_name, vm_name)
                vm_labels = dict(vm.metadata.labels)
            else:
                vm_labels = {}

            self.inventory.add_child(namespace_vms_group, vm_name)

            # add hostvars
            self.inventory.set_variable(vm_name, 'ansible_host', vm_ip)
            self.inventory.set_variable(vm_name, 'labels', vm_labels)
            self.inventory.set_variable(vm_name, 'annotations', vm_annotations)
            self.inventory.set_variable(vm_name, 'object_type', 'vm')
            self.inventory.set_variable(vm_name, 'resource_version', vm.metadata.resourceVersion)
            self.inventory.set_variable(vm_name, 'uid', vm.metadata.uid)

            # Add all variables which are listed in 'ansible' annotation:
            annotations_data = json.loads(vm_annotations.get(annotation_variable, "{}"))
            for k, v in annotations_data.items():
                self.inventory.set_variable(vm_name, k, v)

    def verify_file(self, path):
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('kubevirt.yml', 'kubevirt.yaml')):
                return True
        return False
