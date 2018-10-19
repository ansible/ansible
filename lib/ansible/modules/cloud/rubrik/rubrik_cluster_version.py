#!/usr/bin/python
# (c) 2018 Rubrik, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
module: rubrik_cluster_version
short_description: Retrieves the software version of the Rubrik cluster.
description:
    - Retrieves the software version of the Rubrik cluster.
version_added: 2.8
author: Rubrik Ranger Team

extends_documentation_fragment:
    - rubrik_cdm
requirements: [rubrik_cdm]
'''

EXAMPLES = '''
- rubrik_cluster_version:
'''

RETURN = '''
version:
    description: The version of the Rubrik cluster.
    returned: success
    type: string
    sample: 4.1.3-2510
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.rubrik_cdm import sdk_validation, connect, load_provider_variables, rubrik_argument_spec


def main():
    """ Main entry point for Ansible module execution.
    """

    argument_spec = rubrik_argument_spec

    # Start Parameters
    argument_spec.update(
        dict(

        )
    )
    # End Parameters

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    sdk_present, rubrik_cdm = sdk_validation()

    if sdk_present is False:
        module.fail_json(msg="The Rubrik Python SDK is required for this module (pip install rubrik_cdm).")

    results = {}

    load_provider_variables(module)

    rubrik = connect(rubrik_cdm, module)
    if isinstance(rubrik, str):
        module.fail_json(msg=rubrik)

    results["version"] = rubrik.cluster_version()

    module.exit_json(**results)


if __name__ == '__main__':
    main()
