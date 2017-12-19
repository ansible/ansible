
import json
import os
import re

from datetime import datetime

from ansible.errors import AnsibleError

try:
    from openshift.helper.kubernetes import KubernetesObjectHelper
    from openshift.helper.exceptions import KubernetesException
    HAS_K8S_MODULE_HELPER = True
except ImportError as exc:
    HAS_K8S_MODULE_HELPER = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


CONNECTION_ARGS = [
    'kubeconfig',
    'context',
    'host',
    'api_key',
    'username',
    'password',
    'verify_ssl',
    'ssl_ca_cert',
    'cert_file',
    'key_file',
]


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)


class KubernetesLookup(object):

    def __init__(self):

        if not HAS_K8S_MODULE_HELPER:
            raise AnsibleError(
                "The k8s lookup requires the OpenShift Python client. Try `pip install openshift`"
            )

        if not HAS_YAML:
            raise AnsibleError(
                "This module requires PyYAML. Try `pip install PyYAML`"
            )

        self.kind = None
        self.name = None
        self.namespace = None
        self.api_version = None
        self.src = None
        self.resource_version = None
        self.label_selector = None
        self.field_selector = None
        self.include_uninitialized = None
        self.helper = None
        self.connection = {}

    def run(self, terms, variables=None, **kwargs):

        self.kind = kwargs.get('kind')
        self.name = kwargs.get('name')
        self.namespace = kwargs.get('namespace')
        self.api_version = kwargs.get('api_version')
        self.src = kwargs.get('src')
        self.resource_version = kwargs.get('resource_version')
        self.label_selector = kwargs.get('label_selector')
        self.field_selector = kwargs.get('field_selector')
        self.include_uninitialized = kwargs.get('include_uninitialized', False)

        if self.src:
            defn = self.load_resource_definition()
            self.params_from_resource_definition(defn)

        if not self.api_version:
            raise AnsibleError(
                "Error: no API version specified. Use the 'api_version' parameter, or use the 'src' parameter to "
                "provide a path to a file containing a resource definition."
            )

        if not self.kind:
            raise AnsibleError(
                "Error: no Kind specified. Use the 'kind' parameter, or use the 'src' parameter to provide a path to "
                "a file containing a resource definition."
            )
        self.kind = self._to_snake(self.kind)
        self.helper = self.get_helper()

        for arg in CONNECTION_ARGS:
            self.connection[arg] = kwargs.get(arg)

        try:
            self.helper.set_client_config(**self.connection)
        except Exception as exc:
            raise AnsibleError(
                "Client authentication failed  with {0}".format(exc.message)
            )

        return self.list_objects()

    def get_helper(self):
        try:
            helper = KubernetesObjectHelper(api_version=self.api_version, kind=self.kind, debug=False)
            helper.get_model(self.api_version, self.kind)
        except KubernetesException as exc:
            raise AnsibleError("Error initializing OpenShift helper {0}".format(exc.message))
        return helper

    def load_resource_definition(self):
        """ Load the requested src path """
        path = os.path.normpath(self.src)
        if not os.path.exists(path):
            raise AnsibleError("Error accessing {0}. Does the file exist?".format(path))
        try:
            result = yaml.safe_load(open(path, 'r'))
        except (IOError, yaml.YAMLError) as exc:
            raise AnsibleError("Error loading resource_definition: {0}".format(exc))
        return result

    def params_from_resource_definition(self, defn):
        if defn.get('apiVersion'):
            self.api_version  = defn['apiVersion']
        if defn.get('kind'):
            self.kind = defn['kind']
        if defn.get('metadata', {}).get('labels'):
            self.label_selector = defn['metadata']['labels']
        if defn.get('metadata', {}).get('resourceVersion'):
            self.resource_version = defn['metadata']['resourceVersion']

    @staticmethod
    def _to_snake(name):
        """ Convert string from camel to snake """
        if not name:
            return name

        def replace(m):
            m = m.group(0)
            return m[0] + '_' + m[1:]

        p = r'[a-z][A-Z]|' \
            r'[A-Z]{2}[a-z]'
        result = re.sub(p, replace, name)
        return result.lower()

    def list_objects(self):
        method_name = 'list'
        method_name += '_namespaced_' if self.namespace else '_'
        method_name += self.kind

        # method_name += '_for_all_namespaces' if not self.namespace else ''

        try:
            method = self.helper.lookup_method(method_name=method_name)
        except KubernetesException:
            raise AnsibleError(
                "Error getting method {0} for API {1} and Kind {2}".format(method_name, self.api_version, self.kind)
            )

        params = {}
        if self.field_selector:
            params['field_selector'] = self.field_selector
        if self.name:
            if self.field_selector:
                params['field_selector']['name'] = self.name
            else:
                params['field_selector'] = {'name': self.name}
        if self.resource_version:
            params['resource_version'] = self.resource_version
        if self.label_selector:
            params['label_selector'] = self.label_selector
        params['include_uninitialized'] = self.include_uninitialized

        if self.namespace:
            try:
                result = method(self.namespace, **params)
            except KubernetesException as exc:
                raise AnsibleError(exc.message)
        else:
            try:
                result = method(**params)
            except KubernetesException as exc:
                raise AnsibleError(exc.message)

        response = {}
        if result is not None:
            # Convert Datetime objects to ISO format
            response = json.loads(json.dumps(result.to_dict(), cls=DateTimeEncoder))
            if 'items' in response:
                response['item_list'] = response.pop('items')

        return [response]
