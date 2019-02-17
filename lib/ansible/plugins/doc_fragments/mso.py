# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
  host:
    description:
    - IP Address or hostname of the ACI Multi Site Orchestrator host.
    type: str
    required: yes
    aliases: [ hostname ]
  port:
    description:
    - Port number to be used for the REST connection.
    - The default value depends on parameter `use_ssl`.
    type: int
  username:
    description:
    - The username to use for authentication.
    type: str
    default: admin
  password:
    description:
    - The password to use for authentication.
    - This option is mutual exclusive with C(private_key). If C(private_key) is provided too, it will be used instead.
    type: str
    required: yes
  output_level:
    description:
    - Influence the output of this ACI module.
    - C(normal) means the standard output, incl. C(current) dict
    - C(info) adds informational output, incl. C(previous), C(proposed) and C(sent) dicts
    - C(debug) adds debugging output, incl. C(filter_string), C(method), C(response), C(status) and C(url) information
    type: str
    choices: [ debug, info, normal ]
    default: normal
  timeout:
    description:
    - The socket level timeout in seconds.
    type: int
    default: 30
  use_proxy:
    description:
      - If C(no), it will not use a proxy, even if one is defined in an environment variable on the target hosts.
    type: bool
    default: yes
  use_ssl:
    description:
    - If C(no), an HTTP connection will be used instead of the default HTTPS connection.
    type: bool
    default: yes
  validate_certs:
    description:
    - If C(no), SSL certificates will not be validated.
    - This should only set to C(no) when used on personally controlled sites using self-signed certificates.
    type: bool
    default: yes
requirements:
- Multi Site Orchestrator v2.1 or newer
notes:
- Please read the :ref:`aci_guide` for more detailed information on how to manage your ACI infrastructure using Ansible.
- This module was written to support ACI Multi Site Orchestrator v2.1 or newer. Some or all functionality may not work on earlier versions.
'''
