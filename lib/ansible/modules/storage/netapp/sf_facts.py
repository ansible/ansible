#!/usr/bin/python
# (c) 2017, NetApp, Inc
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
module: sf_facts

short_description: Report facts of a NetApp SolidFire cluster.
extends_documentation_fragment:
    - netapp.solidfire
version_added: '2.5'
author: Kevin Hulquest (@hulquest)
description:
- Report the facts of a SolidFire cluster..
- High level cluster, node, accounts, volume, virtual volume, snapshots, events, cluster faults, and version information, version information.

'''

EXAMPLES = """
---
    - name: Get cluster facts.
      sf_facts:
        hostname: "{{ solidfire_hostname }}"
        username: "{{ solidfire_username }}"
        password: "{{ solidfire_password }}"
"""

RETURN = """
msg:
    description: Gathered facts for Solidfire cluster.
    returned: always
    type: string
"""

import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

HAS_SF_SDK = netapp_utils.has_sf_sdk()


class SolidFireFacts(object):
    """
    Class to aggregate several SolidFire cluster API calls into an Ansible facts module.
    The API methods that are currently called and returned are:
    * GetClusterInfo
    * ListAllNodes
    * GetClusterSate
    * GetClusterVersionInfo
    * ListAccounts
    * ListDrives
    * ListVolumes
    * ListVirtualVolumes
    * ListSnapshots
    * ListClusterFaults
    """

    def __init__(self):
        self.state = {}
        self.cluster_config = {}
        self.version_info = {}
        self.facts = {}

        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
        )

        params = self.module.params

        if HAS_SF_SDK:
            self.sfe = netapp_utils.ElementFactory.create(params['hostname'], params['username'], params['password'],
                                                          print_ascii_art=False)
        else:
            self.module.fail_json(msg="Unable to import the SolidFire Python SDK")

        self.fact_metadata = self.make_metadata()

    def make_metadata(self):
        """Single place to add future API calls."""
        fact_metadata = {'cluster-info': {self.sfe.get_cluster_info: {}},
                         'node-info': {self.sfe.list_all_nodes: {}},
                         'state': {self.sfe.get_cluster_state: {'force': True}},
                         'version_info': {self.sfe.get_cluster_version_info: {}},
                         'accounts': {self.sfe.list_accounts: {}},
                         'drives': {self.sfe.list_drives: {}},
                         'volumes': {self.sfe.list_volumes: {}},
                         'virtual-volumes': {self.sfe.list_virtual_volumes: {}},
                         'snapshots': {self.sfe.list_snapshots: {}},
                         'cluster-faults': {self.sfe.list_cluster_faults: {}},
                         }
        return fact_metadata

    def fetch_fact(self, name, api):
        """Uniform way to add facts to our return structure."""
        from solidfire.common import ApiServerError
        try:
            method, args = api.popitem()
            data = method(**args)
            self.facts.update(data.to_json())
        except ApiServerError as sf_problem:
            if sf_problem.error_name and sf_problem.error_name == 'xFeatureNotEnabled':
                self.facts[name] = {}
                return
            self.module.fail_json(
                msg="Failed to obtain cluster fact [%s] from [%s]. Error [%s]" % (name, self.module.params['hostname'],
                                                                                  to_native(sf_problem)))
        except ApiServerError as problem:
            self.module.fail_json(msg=to_native(problem))

    def gather_facts(self):
        """Gather information from the cluster and return it to Ansible."""

        self.facts['mvip'] = self.module.params['hostname']
        """This is the cluster identifyer."""

        for key in self.fact_metadata.keys():
            self.fetch_fact(name=key, api=self.fact_metadata[key])

        result = dict(ansible_facts=self.facts, changed=False)
        self.module.exit_json(**result)


def main():
    facts = SolidFireFacts()
    facts.gather_facts()


if __name__ == '__main__':
    main()
