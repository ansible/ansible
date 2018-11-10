# (c) 2018 Yunge Zhu, <yungez@microsoft.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
lookup: azure_service_principal_attribute

requirements:
  - azure-graphrbac

author:
  - Yunge Zhu <yungez@microsoft.com>

version_added: "2.7"

short_description: Look up Azure service principal attributes.

description:
  - Describes object id of your Azure service principal account.
options:
  azure_client_id:
    description: azure service principal client id.
  azure_secret:
    description: azure service principal secret
  azure_tenant:
    description: azure tenant
  azure_cloud_environment:
    description: azure cloud environment
"""

EXAMPLES = """
set_fact:
  object_id: "{{ lookup('azure_service_principal_attribute',
                         azure_client_id=azure_client_id,
                         azure_secret=azure_secret,
                         azure_tenant=azure_secret) }}"
"""

RETURN = """
_raw:
  description:
    Returns object id of service principal.
"""

from ansible.errors import AnsibleError
from ansible.plugins import AnsiblePlugin
from ansible.plugins.lookup import LookupBase
from ansible.module_utils._text import to_native

try:
    from azure.common.credentials import ServicePrincipalCredentials
    from azure.graphrbac import GraphRbacManagementClient
    from msrestazure import azure_cloud
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    raise AnsibleError(
        "The lookup azure_service_principal_attribute requires azure.graphrbac, msrest")


class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):

        self.set_options(direct=kwargs)

        credentials = {}
        credentials['azure_client_id'] = self.get_option('azure_client_id', None)
        credentials['azure_secret'] = self.get_option('azure_secret', None)
        credentials['azure_tenant'] = self.get_option('azure_tenant', 'common')

        if credentials['azure_client_id'] is None or credentials['azure_secret'] is None:
            raise AnsibleError("Must specify azure_client_id and azure_secret")

        _cloud_environment = azure_cloud.AZURE_PUBLIC_CLOUD
        if self.get_option('azure_cloud_environment', None) is not None:
            cloud_environment = azure_cloud.get_cloud_from_metadata_endpoint(credentials['azure_cloud_environment'])

        try:
            azure_credentials = ServicePrincipalCredentials(client_id=credentials['azure_client_id'],
                                                            secret=credentials['azure_secret'],
                                                            tenant=credentials['azure_tenant'],
                                                            resource=_cloud_environment.endpoints.active_directory_graph_resource_id)

            client = GraphRbacManagementClient(azure_credentials, credentials['azure_tenant'],
                                               base_url=_cloud_environment.endpoints.active_directory_graph_resource_id)

            response = list(client.service_principals.list(filter="appId eq '{0}'".format(credentials['azure_client_id'])))
            sp = response[0]

            return sp.object_id.split(',')
        except CloudError as ex:
            raise AnsibleError("Failed to get service principal object id: %s" % to_native(ex))
        return False
