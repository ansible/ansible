# -*- coding: utf-8 -*

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
    DOCUMENTATION = r'''
options:
  http_agent:
    description:
    - Set http user agent.
    default: ansible-httpget
  use_proxy:
    description:
    - if C(no), it will not use a proxy, even if one is defined in
      an environment variable on the target hosts.
    type: bool
    default: 'yes'
  validate_certs:
    description:
    - If C(no), SSL certificates will not be validated. This should only be used
      on personally controlled sites using self-signed certificates.
    - Prior to 1.9.2 the code defaulted to C(no).
    type: bool
    default: 'yes'
    version_added: '1.9.2'
  url_username:
    description:
    - The username for use in HTTP basic authentication.
    - This parameter can be used without C(url_password) for sites that allow empty passwords.
    version_added: '1.6'
  url_password:
    description:
    - The password for use in HTTP basic authentication.
    - If the C(url_username) parameter is not specified, the C(url_password) parameter will not be used.
    version_added: '1.6'
  force_basic_auth:
    description:
      - The library used by this module only sends authentication information when a webservice
        responds to an initial request with a 401 status. Since some basic auth services do not properly
        send a 401, logins will fail. This option forces the sending of the Basic authentication header
        upon initial request.
    type: bool
    default: "no"
    version_added: '2.0'
  client_cert:
    description:
    - PEM formatted certificate chain file to be used for SSL client
      authentication. This file can also include the key as well, and if
      the key is included, C(client_key) is not required.
    version_added: '2.4'
  client_key:
    description:
    - PEM formatted file that contains your private key to be used for SSL
      client authentication. If C(client_cert) contains both the certificate
      and key, this option is not required.
    version_added: '2.4'
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
