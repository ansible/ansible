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
#


class ModuleDocFragment(object):

    DOCUMENTATION = '''
options:
  state:
    description:
    - Determines if an object should be created, patched, or deleted. When set to
      C(present), the object will be created, if it does not exist, or patched, if
      parameter values differ from the existing object's attributes, and deleted,
      if set to C(absent). A patch operation results in merging lists and updating
      dictionaries, with lists being merged into a unique set of values. If a list
      contains a dictionary with a I(name) or I(type) attribute, a strategic merge
      is performed, where individual elements with a matching I(name_) or I(type)
      are merged. To force the replacement of lists, set the I(force) option to C(True).
    default: present
    choices:
    - present
    - absent
  force:
    description:
    - If set to C(True), and I(state) is C(present), an existing object will be updated,
      and lists will be replaced, rather than merged.
    default: false
    type: bool
  resource_definition:
    description:
    - "Provide a valid YAML definition for an object when creating or updating. NOTE: I(kind), I(api_version), I(name),
      and I(namespace) will be overwritten by corresponding values found in the provided I(resource_definition)."
    aliases:
    - definition
    - inline
  src:
    description:
    - "Provide a path to a file containing a valid YAML definition of an object to be created or updated. Mutually
      exclusive with I(resource_definition). NOTE: I(kind), I(api_version), I(name), and I(namespace) will be
      overwritten by corresponding values found in the configuration read in from the I(src) file."
  api_version:
    description:
    - Use to specify the API version when deleting an object, or when creating an object, such as namespace or
      project, that only requires a I(name) attribute.
    aliases:
    - api
    - version
  kind:
    description:
    - Use to specify the object kind when deleting an object, or when creating an object, such as namespace or
      project, that only requires a I(name) attribute.
  name:
    description:
    - Use to specify an object name when deleting an object, or when creating an object, such as namespace or
      project, that only requires a name attribute.
  namespace:
    description:
    - Use to specify the namespace or project when deleting an object, or when creating an object, such as namespace
      or project, that only requires a I(name) attribute.
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
    - The name of a context found in the config file. Can also be specified via K8S_AUTH_CONTEXT environment variable.
  username:
    description:
    - Provide a username for authenticating with the API. Can also be specified via K8S_AUTH_USERNAME environment
      variable.
  password:
    description:
    - Provide a password for authenticating with the API. Can also be specified via K8S_AUTH_PASSWORD environment
      variable.
  cert_file:
    description:
    - Path to a certificate used to authenticate with the API. Can also be specified via K8S_AUTH_CERT_FILE environment
      variable.
  key_file:
    description:
    - Path to a key file used to authenticate with the API. Can also be specified via K8S_AUTH_HOST environment
      variable.
  ssl_ca_cert:
    description:
    - Path to a CA certificate used to authenticate with the API. Can also be specified via K8S_AUTH_SSL_CA_CERT
      environment variable.
  verify_ssl:
    description:
    - Whether or not to verify the API server's SSL certificates. Can also be specified via K8S_AUTH_VERIFY_SSL
      environment variable.
    type: bool

notes:
  - "To learn more about the OpenShift Python client, visit: https://github.com/openshift/openshift-restclient-python"
'''
