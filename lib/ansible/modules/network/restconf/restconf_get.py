#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: restconf_get
version_added: "2.8"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Fetch configuration/state data from RESTCONF enabled devices.
description:
    - RESTCONF is a standard mechanisms to allow web applications to access the
      configuration data and state data developed and standardized by
      the IETF. It is documented in RFC 8040.
    - This module allows the user to fetch configuration and state data from RESTCONF
      enabled devices.
options:
  path:
    description:
      - URI being used to execute API calls.
    required: true
  content:
    description:
      - The C(content) is a query parameter that controls how descendant nodes of the
        requested data nodes in C(path) will be processed in the reply. If value is
        I(config) return only configuration descendant data nodes of value in C(path).
        If value is I(nonconfig) return only non-configuration descendant data nodes
        of value in C(path). If value is I(all) return all descendant data nodes of
        value in C(path)
    required: false
    choices: ['config', 'nonconfig', 'all']
  output:
    description:
      - The output of response received.
    required: false
    default: json
    choices: ['json', 'xml']
"""

EXAMPLES = """
- name: get l3vpn services
  restconf_get:
      path: /config/ietf-l3vpn-svc:l3vpn-svc/vpn-services
"""

RETURN = """
response:
  description: A dictionary representing a JSON-formatted response
  returned: when the device response is valid JSON
  type: dict
  sample: |
        {
            "vpn-services": {
                "vpn-service": [
                    {
                        "customer-name": "red",
                        "vpn-id": "blue_vpn1",
                        "vpn-service-topology": "ietf-l3vpn-svc:any-to-any"
                    }
                ]
            }
        }

"""

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.network.restconf import restconf


def main():
    """entry point for module execution
    """
    argument_spec = dict(
        path=dict(required=True),
        content=dict(choices=['config', 'nonconfig', 'all']),
        output=dict(choices=['json', 'xml'], default='json'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    result = {'changed': False}

    try:
        response = restconf.get(module, **module.params)
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc), code=exc.code)

    result.update({
        'response': response,
    })

    module.exit_json(**result)


if __name__ == '__main__':
    main()
