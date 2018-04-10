# -*- coding: utf-8 -*-

# Copyright 2017 Dag Wieers <dag@wieers.com>
# Copyright 2017 Swetha Chunduri (@schunduri)

# This file is part of Ansible by Red Hat
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
    default: 443 (for https) and 80 (for http)
    type: int
  username:
    description:
    - The username to use for authentication.
    required: yes
    default: admin
    aliases: [ user ]
  password:
    description:
    - The password to use for authentication.
    required: yes
  private_key:
    description:
    - PEM formatted file that contains your private key to be used for signature-based authentication.
    - The name of the key (without extension) is used as the certificate name in ACI, unless C(certificate_name) is specified.
    aliases: [ cert_key ]
  certificate_name:
    description:
    - The X.509 certificate name attached to the APIC AAA user used for signature-based authentication.
    - It defaults to the C(private_key) basename, without extension.
    aliases: [ cert_name ]
    default: C(private_key) basename
  output_level:
    description:
    - Influence the output of this ACI module.
    - C(normal) means the standard output, incl. C(current) dict
    - C(info) means informational output, incl. C(previous), C(proposed) and C(sent) dicts
    - C(debug) means debugging output, incl. C(filter_string), C(method), C(response), C(status) and C(url) information
    choices: [ debug, info, normal ]
    default: normal
  timeout:
    description:
    - The socket level timeout in seconds.
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
    - This should only set to C(no) used on personally controlled sites using self-signed certificates.
    type: bool
    default: 'yes'
notes:
- By default, if an environment variable C(<protocol>_proxy) is set on
  the target host, requests will be sent through that proxy. This
  behaviour can be overridden by setting a variable for this task
  (see `setting the environment
  <http://docs.ansible.com/playbooks_environment.html>`_),
  or by using the C(use_proxy) option.
- HTTP redirects can redirect from HTTP to HTTPS so you should be sure that
  your proxy environment for both protocols is correct.
'''
