# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Dag Wieers (@dagwieers) <dag@wieers.com>
# Copyright: (c) 2017, Swetha Chunduri (@schunduri)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
  host:
    description:
    - IP Address or hostname of APIC resolvable by Ansible control host.
    type: str
    required: yes
    aliases: [ hostname ]
  port:
    description:
    - Port number to be used for REST connection.
    - The default value depends on parameter C(use_ssl).
    type: int
  username:
    description:
    - The username to use for authentication.
    type: str
    default: admin
    aliases: [ user ]
  password:
    description:
    - The password to use for authentication.
    - This option is mutual exclusive with C(private_key). If C(private_key) is provided too, it will be used instead.
    type: str
    required: yes
  private_key:
    description:
    - Either a PEM-formatted private key file or the private key content used for signature-based authentication.
    - This value also influences the default C(certificate_name) that is used.
    - This option is mutual exclusive with C(password). If C(password) is provided too, it will be ignored.
    type: str
    required: yes
    aliases: [ cert_key ]
  certificate_name:
    description:
    - The X.509 certificate name attached to the APIC AAA user used for signature-based authentication.
    - If a C(private_key) filename was provided, this defaults to the C(private_key) basename, without extension.
    - If PEM-formatted content was provided for C(private_key), this defaults to the C(username) value.
    type: str
    aliases: [ cert_name ]
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
seealso:
- ref: aci_guide
  description: Detailed information on how to manage your ACI infrastructure using Ansible.
- ref: aci_dev_guide
  description: Detailed guide on how to write your own Cisco ACI modules to contribute.
'''
