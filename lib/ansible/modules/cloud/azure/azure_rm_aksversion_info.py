#!/usr/bin/python
#
# Copyright (c) 2018 Yuwei Zhou, <yuwzho@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_aksversion_info

version_added: "2.9"

short_description: Get available kubernetes versions supported by Azure Kubernetes Service

description:
    - Get available kubernetes versions supported by Azure Kubernetes Service.

options:
    location:
        description:
            - Get the versions available for creating a managed Kubernetes cluster.
        required: true
    version:
        description:
            - Get the upgrade versions available for a managed Kubernetes cluster version.

extends_documentation_fragment:
    - azure

author:
    - Yuwei Zhou (@yuwzho)
'''

EXAMPLES = '''
    - name: Get available versions for AKS in location eastus
      azure_rm_aksversion_info:
        location: eastus
    - name: Get  available versions an AKS can be upgrade to
      azure_rm_aksversion_info:
        location: eastis
        version: 1.11.6
'''

RETURN = '''
azure_aks_versions:
    description: List of supported kubernetes versions.
    returned: always
    type: list
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.common import AzureHttpError
except Exception:
    # handled in azure_rm_common
    pass


class AzureRMAKSVersion(AzureRMModuleBase):

    def __init__(self):

        self.module_args = dict(
            location=dict(type='str', required=True),
            version=dict(type='str')
        )

        self.results = dict(
            changed=False,
            azure_aks_versions=[]
        )

        self.location = None
        self.version = None

        super(AzureRMAKSVersion, self).__init__(
            derived_arg_spec=self.module_args,
            supports_tags=False,
            facts_module=True
        )

    def exec_module(self, **kwargs):

        is_old_facts = self.module._name == 'azure_rm_aksversion_facts'
        if is_old_facts:
            self.module.deprecate("The 'azure_rm_aksversion_facts' module has been renamed to 'azure_rm_aksversion_info'", version='2.13')

        for key in self.module_args:
            setattr(self, key, kwargs[key])

        self.results['azure_aks_versions'] = self.get_all_versions(self.location, self.version)

        return self.results

    def get_all_versions(self, location, version):
        '''
        Get all kubernetes version supported by AKS
        :return: ordered version list
        '''
        try:
            result = dict()
            response = self.containerservice_client.container_services.list_orchestrators(self.location, resource_type='managedClusters')
            orchestrators = response.orchestrators
            for item in orchestrators:
                result[item.orchestrator_version] = [x.orchestrator_version for x in item.upgrades] if item.upgrades else []
            if version:
                return result.get(version) or []
            else:
                keys = list(result.keys())
                keys.sort()
                return keys
        except Exception as exc:
            self.fail('Error when getting AKS supported kubernetes version list for location {0} - {1}'.format(self.location, exc.message or str(exc)))


def main():
    """Main module execution code path"""

    AzureRMAKSVersion()


if __name__ == '__main__':
    main()
