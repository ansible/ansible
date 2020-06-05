#
# Copyright: (c) 2018, Red Hat | Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
    lookup: k8s
    version_added: "2.5"
    short_description: Query the K8s API

    description:
      - Uses the OpenShift Python client to fetch a specific object by name, all matching objects within a
        namespace, or all matching objects for all namespaces, as well as information about the cluster.
      - Provides access the full range of K8s APIs.
      - Enables authentication via config file, certificates, password or token.

    options:
      cluster_info:
        description:
        - Use to specify the type of cluster information you are attempting to retrieve. Will take priority
          over all the other options.
      api_version:
        description:
        - Use to specify the API version. If I(resource definition) is provided, the I(apiVersion) from the
          I(resource_definition) will override this option.
        default: v1
      kind:
        description:
        - Use to specify an object model. If I(resource definition) is provided, the I(kind) from a
          I(resource_definition) will override this option.
        required: true
      resource_name:
        description:
        - Fetch a specific object by name. If I(resource definition) is provided, the I(metadata.name) value
          from the I(resource_definition) will override this option.
      namespace:
        description:
        - Limit the objects returned to a specific namespace. If I(resource definition) is provided, the
          I(metadata.namespace) value from the I(resource_definition) will override this option.
      label_selector:
        description:
        - Additional labels to include in the query. Ignored when I(resource_name) is provided.
      field_selector:
        description:
        - Specific fields on which to query. Ignored when I(resource_name) is provided.
      resource_definition:
        description:
        - "Provide a YAML configuration for an object. NOTE: I(kind), I(api_version), I(resource_name),
          and I(namespace) will be overwritten by corresponding values found in the provided I(resource_definition)."
      src:
        description:
        - "Provide a path to a file containing a valid YAML definition of an object dated. Mutually
          exclusive with I(resource_definition). NOTE: I(kind), I(api_version), I(resource_name), and I(namespace)
          will be overwritten by corresponding values found in the configuration read in from the I(src) file."
        - Reads from the local file system. To read from the Ansible controller's file system, use the file lookup
          plugin or template lookup plugin, combined with the from_yaml filter, and pass the result to
          I(resource_definition). See Examples below.
      host:
        description:
        - Provide a URL for accessing the API. Can also be specified via K8S_AUTH_HOST environment variable.
      api_key:
        description:
        - Token used to authenticate with the API. Can also be specified via K8S_AUTH_API_KEY environment variable.
      kubeconfig:
        description:
        - Path to an existing Kubernetes config file. If not provided, and no other connection
          options are provided, the openshift client will attempt to load the default
          configuration file from I(~/.kube/config.json). Can also be specified via K8S_AUTH_KUBECONFIG environment
          variable.
      context:
        description:
        - The name of a context found in the config file. Can also be specified via K8S_AUTH_CONTEXT environment
          variable.
      username:
        description:
        - Provide a username for authenticating with the API. Can also be specified via K8S_AUTH_USERNAME environment
          variable.
      password:
        description:
        - Provide a password for authenticating with the API. Can also be specified via K8S_AUTH_PASSWORD environment
          variable.
      client_cert:
        description:
        - Path to a certificate used to authenticate with the API. Can also be specified via K8S_AUTH_CERT_FILE
          environment
          variable.
        aliases: [ cert_file ]
      client_key:
        description:
        - Path to a key file used to authenticate with the API. Can also be specified via K8S_AUTH_KEY_FILE environment
          variable.
        aliases: [ key_file ]
      ca_cert:
        description:
        - Path to a CA certificate used to authenticate with the API. Can also be specified via K8S_AUTH_SSL_CA_CERT
          environment variable.
        aliases: [ ssl_ca_cert ]
      validate_certs:
        description:
        - Whether or not to verify the API server's SSL certificates. Can also be specified via K8S_AUTH_VERIFY_SSL
          environment variable.
        type: bool
        aliases: [ verify_ssl ]

    requirements:
      - "python >= 2.7"
      - "openshift >= 0.6"
      - "PyYAML >= 3.11"

    notes:
      - "The OpenShift Python client wraps the K8s Python client, providing full access to
        all of the APIS and models available on both platforms. For API version details and
        additional information visit https://github.com/openshift/openshift-restclient-python"
"""

EXAMPLES = r"""
- name: Fetch a list of namespaces
  set_fact:
    projects: "{{ lookup('k8s', api_version='v1', kind='Namespace') }}"

- name: Fetch all deployments
  set_fact:
    deployments: "{{ lookup('k8s', kind='Deployment') }}"

- name: Fetch all deployments in a namespace
  set_fact:
    deployments: "{{ lookup('k8s', kind='Deployment', namespace='testing') }}"

- name: Fetch a specific deployment by name
  set_fact:
    deployments: "{{ lookup('k8s', kind='Deployment', namespace='testing', resource_name='elastic') }}"

- name: Fetch with label selector
  set_fact:
    service: "{{ lookup('k8s', kind='Service', label_selector='app=galaxy') }}"

# Use parameters from a YAML config

- name: Load config from the Ansible controller filesystem
  set_fact:
    config: "{{ lookup('file', 'service.yml') | from_yaml }}"

- name: Using the config (loaded from a file in prior task), fetch the latest version of the object
  set_fact:
    service: "{{ lookup('k8s', resource_definition=config) }}"

- name: Use a config from the local filesystem
  set_fact:
    service: "{{ lookup('k8s', src='service.yml') }}"
"""

RETURN = r"""
  _list:
    description:
      - One ore more object definitions returned from the API.
    type: complex
    contains:
      api_version:
        description: The versioned schema of this representation of an object.
        returned: success
        type: str
      kind:
        description: Represents the REST resource this object represents.
        returned: success
        type: str
      metadata:
        description: Standard object metadata. Includes name, namespace, annotations, labels, etc.
        returned: success
        type: complex
      spec:
        description: Specific attributes of the object. Will vary based on the I(api_version) and I(kind).
        returned: success
        type: complex
      status:
        description: Current status details for the object.
        returned: success
        type: complex
"""


from ansible.errors import AnsibleError
from ansible.module_utils.common._collections_compat import KeysView
from ansible.plugins.lookup import LookupBase

from ansible.module_utils.k8s.common import K8sAnsibleMixin

try:
    from openshift.dynamic import DynamicClient
    from openshift.dynamic.exceptions import NotFoundError
    HAS_K8S_MODULE_HELPER = True
    k8s_import_exception = None
except ImportError as e:
    HAS_K8S_MODULE_HELPER = False
    k8s_import_exception = e

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class KubernetesLookup(K8sAnsibleMixin):

    def __init__(self):

        if not HAS_K8S_MODULE_HELPER:
            raise Exception(
                "Requires the OpenShift Python client. Try `pip install openshift`. Detail: {0}".format(k8s_import_exception)
            )

        if not HAS_YAML:
            raise Exception(
                "Requires PyYAML. Try `pip install PyYAML`"
            )

        self.kind = None
        self.name = None
        self.namespace = None
        self.api_version = None
        self.label_selector = None
        self.field_selector = None
        self.include_uninitialized = None
        self.resource_definition = None
        self.helper = None
        self.connection = {}

    def fail(self, msg=None):
        raise AnsibleError(msg)

    def run(self, terms, variables=None, **kwargs):
        self.params = kwargs
        self.client = self.get_api_client()

        cluster_info = kwargs.get('cluster_info')
        if cluster_info == 'version':
            return [self.client.version]
        if cluster_info == 'api_groups':
            if isinstance(self.client.resources.api_groups, KeysView):
                return [list(self.client.resources.api_groups)]
            return [self.client.resources.api_groups]

        self.kind = kwargs.get('kind')
        self.name = kwargs.get('resource_name')
        self.namespace = kwargs.get('namespace')
        self.api_version = kwargs.get('api_version', 'v1')
        self.label_selector = kwargs.get('label_selector')
        self.field_selector = kwargs.get('field_selector')
        self.include_uninitialized = kwargs.get('include_uninitialized', False)

        resource_definition = kwargs.get('resource_definition')
        src = kwargs.get('src')
        if src:
            resource_definition = self.load_resource_definitions(src)[0]
        if resource_definition:
            self.kind = resource_definition.get('kind', self.kind)
            self.api_version = resource_definition.get('apiVersion', self.api_version)
            self.name = resource_definition.get('metadata', {}).get('name', self.name)
            self.namespace = resource_definition.get('metadata', {}).get('namespace', self.namespace)

        if not self.kind:
            raise AnsibleError(
                "Error: no Kind specified. Use the 'kind' parameter, or provide an object YAML configuration "
                "using the 'resource_definition' parameter."
            )

        resource = self.find_resource(self.kind, self.api_version, fail=True)
        try:
            k8s_obj = resource.get(name=self.name, namespace=self.namespace, label_selector=self.label_selector, field_selector=self.field_selector)
        except NotFoundError:
            return []

        if self.name:
            return [k8s_obj.to_dict()]

        return k8s_obj.to_dict().get('items')


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        return KubernetesLookup().run(terms, variables=variables, **kwargs)
