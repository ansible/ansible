# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Dag Wieers (@dagwieers) <dag@wieers.com>
# Copyright: (c) 2017, Swetha Chunduri (@schunduri)

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Standard files documentation fragment
    DOCUMENTATION = '''
options:
  host:
    description:
    - IP Address or hostname of APIC resolvable by Ansible control host.
    required: yes
    aliases: [ hostname ]
  port:
    description:
    - Port number to be used for REST connection.
    - The default value depends on parameter `use_ssl`.
  username:
    description:
    - The username to use for authentication.
    default: admin
    aliases: [ user ]
  password:
    description:
    - The password to use for authentication.
    - This option is mutual exclusive with C(private_key). If C(private_key) is provided too, it will be used instead.
    required: yes
  private_key:
    description:
    - PEM formatted file that contains your private key to be used for signature-based authentication.
    - The name of the key (without extension) is used as the certificate name in ACI, unless C(certificate_name) is specified.
    - This option is mutual exclusive with C(password). If C(password) is provided too, it will be ignored.
    required: yes
    aliases: [ cert_key ]
  certificate_name:
    description:
    - The X.509 certificate name attached to the APIC AAA user used for signature-based authentication.
    - It defaults to the C(private_key) basename, without extension.
    aliases: [ cert_name ]
  output_level:
    description:
    - Influence the output of this ACI module.
    - C(normal) means the standard output, incl. C(current) dict
    - C(info) adds informational output, incl. C(previous), C(proposed) and C(sent) dicts
    - C(debug) adds debugging output, incl. C(filter_string), C(method), C(response), C(status) and C(url) information
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
    default: 'yes'
  use_ssl:
    description:
    - If C(no), an HTTP connection will be used instead of the default HTTPS connection.
    type: bool
    default: 'yes'
  validate_certs:
    description:
    - If C(no), SSL certificates will not be validated.
    - This should only set to C(no) when used on personally controlled sites using self-signed certificates.
    type: bool
    default: 'yes'
notes:
- Please read the :ref:`aci_guide` for more detailed information on how to manage your ACI infrastructure using Ansible.
'''
